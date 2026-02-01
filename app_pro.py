import streamlit as st
import google.generativeai as genai
import os
import asyncio
import edge_tts
import fitz  # 雲端自動加載，免本機安裝
import re
from PIL import Image

# --- 1. 頁面配置 (全黑文字、翩翩體、平板優化) ---
st.set_page_config(page_title="理化 AI 雞排珍奶實驗室", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="css"], .stMarkdown, p, h1, h2, h3, span, label, li {
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', 'KaiTi', sans-serif !important;
    }
    .guide-box {
        background-color: #fff9c4;
        padding: 15px;
        border-radius: 12px;
        border: 2px solid #fbc02d;
        margin-bottom: 20px;
    }
    .stButton>button {
        background-color: #e3f2fd !important;
        border-radius: 8px;
        font-weight: bold;
        width: 100%;
        height: 50px;
        font-size: 1.2rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心助教語音 (解決平板靜音版) ---
async def generate_voice(text):
    clean_text = re.sub(r'\$+', '', text)
    clean_text = clean_text.replace('\\%', '百分之').replace('%', '百分之')
    clean_text = clean_text.replace('*', '').replace('#', '').replace('\n', ' ')
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- 3. 雲端截圖功能 (直接讀取 PDF 頁面) ---
def get_pdf_page_image(pdf_path, page_index):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_index)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # 高清
    img_data = pix.tobytes("png")
    doc.close()
    return img_data

# --- 4. 講義目錄 (對應您的 72 頁熱血標題) ---
page_titles = {
    1: "科學方法與變因判斷", 2: "實驗安全規範", 27: "莫耳靈魂的絕對計數",
    71: "直流電動機：旋轉輪迴", 72: "法拉第發電機：能量覺醒"
}

# --- 5. 初始化 Session ---
if 'audio_data' not in st.session_state: st.session_state.audio_data = None
if 'quiz_data' not in st.session_state: st.session_state.quiz_data = None

st.title("🥤 理化 AI 雞排珍奶實驗室")
st.markdown("""<div class="guide-box"><b>各位同學好！我是導讀老師。</b><br>請輸入金鑰，我們邊吃雞排邊學理化！</div>""", unsafe_allow_html=True)

user_key = st.text_input("🔑 通行證：", type="password")
st.divider()

# --- 6. 五大門派雙選單 (全頁面不跳頁) ---
parts_list = ["【一：物質初探】", "【二：能量流轉】", "【三：微觀審判】", "【四：力學秘術】", "【五：旋轉輪迴】"]
part_choice = st.selectbox("第一步：選擇大單元", parts_list)

if "一" in part_choice: r = range(1, 16)
elif "二" in part_choice: r = range(16, 27)
elif "三" in part_choice: r = range(27, 41)
elif "四" in part_choice: r = range(41, 55)
else: r = range(55, 73)

options = [f"第 {p} 頁：{page_titles.get(p, '單元詳解')}" for p in r]
selected_page_str = st.selectbox("第二步：選擇精確頁碼", options)
target_page = int(re.search(r"第 (\d+) 頁", selected_page_str).group(1))

if st.button(f"🚀 啟動第 {target_page} 頁【雞排珍奶】導讀"):
    if not user_key:
        st.warning("請先輸入金鑰。")
    else:
        genai.configure(api_key=user_key)
        path_finals = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        path_bank = os.path.join(os.getcwd(), "data", "Huikao_Bank.pdf")
        
        # 顯示調製文字
        with st.spinner("正在調製波霸奶茶..."):
            try:
                # 1. 雲端截圖顯示
                page_img = get_pdf_page_image(path_finals, target_page - 1)
                st.image(page_img, caption=f"講義第 {target_page} 頁內容", use_column_width=True)
                
                # 2. AI 教學邏輯
                files = [genai.upload_file(path=path_finals)]
                if os.path.exists(path_bank): files.append(genai.upload_file(path=path_bank))
                
                model = genai.GenerativeModel('models/gemini-2.5-flash')
                prompt = files + [
                    f"你是有 20 年資歷的理化老師。1. 請針對第一個檔案第 {target_page} 頁詳細教學。"
                    f"2. **【講義優先】**：必須先完整講解講義圖片中的所有例題與重點。"
                    "3. 開場白請生活化，提到『雞排配大杯珍奶』。說各位同學好！今天老師感冒沙啞。"
                    "4. 公式如 $n=m/M$ 必須使用 LaTeX。5. 結尾用標籤 '[QUIZ_DATA]' 並從檔案二搜尋 1 題相關長敘述會考題。"
                ]
                res = model.generate_content(prompt)
                parts = res.text.split("[QUIZ_DATA]")
                st.markdown(parts[0])
                
                # 3. 語音處理
                st.session_state.audio_data = asyncio.run(generate_voice(parts[0]))
                if len(parts) > 1: st.session_state.quiz_data = parts[1]
                st.balloons()
            except Exception as e:
                st.error(f"連線失敗：{e}")

# --- 7. 平板音訊手動播放 ---
if st.session_state.audio_data:
    st.info("🔊 **平板教學提醒**：請點擊播放鈕聽導讀。")
    st.audio(st.session_state.audio_data, format="audio/mp3")

# --- 8. 隨堂測驗 (會考長敘述題) ---
if st.session_state.quiz_data:
    st.divider()
    st.subheader("📝 歷屆會考真題挑戰")
    st.markdown(st.session_state.quiz_data.split("正確")[0])
    ans = st.radio("你的選擇：", ["A", "B", "C", "D"], key="q_ans")
    if st.button("送出解答"):
        correct = re.search(r"正確[選項|字母][：:\s]*([A-D])", st.session_state.quiz_data).group(1)
        hint = re.search(r"提示[：:\s]*(.*)", st.session_state.quiz_data).group(1)
        if ans == correct: st.success("🎯 答對了！這就是會考重點。")
        else: st.error(f"❌ 老師小提示：{hint}")