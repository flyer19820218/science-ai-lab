import streamlit as st
import google.generativeai as genai
import os
import asyncio
import edge_tts
import fitz  # 雲端自動加載，免本機安裝
import re
from PIL import Image

# --- 1. 頁面配置 (全黑文字、翩翩體、適應平板) ---
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
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心助教語音 (HsiaoChen 穩定版) ---
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

# --- 3. 雲端截圖功能 ---
def get_pdf_page_image(pdf_path, page_index):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_index)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # 高清截圖
    img_data = pix.tobytes("png")
    doc.close()
    return img_data

# --- 4. 講義 72 頁完整目錄 (對齊講義內容) ---
page_titles = {
    1: "科學方法與變因判斷", 2: "實驗室安全規範", 3: "測量與天平操作", 4: "物質特徵：密度奧義",
    5: "大氣製備：氮、氧、二氧化碳", 6: "純物質與混合物", 7: "粗鹽精製：過濾與蒸發", 8: "溶解度與飽和溶液",
    9: "重量百分率濃度", 10: "百萬分點 (ppm)", 11: "波動與介質傳遞", 12: "聲速與溫度關係",
    13: "迴聲測距與反射", 14: "樂音三要素", 15: "超聲波與應用", 16: "光的傳播與針孔成像",
    17: "反射定律與平面鏡", 18: "折射定律與視深", 19: "凸透鏡成像規維", 20: "凹透鏡與色散",
    21: "眼球構造與矯正", 22: "熱量的流轉：熱傳導", 23: "熱對流與熱輻射", 24: "比熱與熱量計算",
    25: "原子構造與離子契約", 26: "元素週期表導覽", 27: "質量守恆與莫耳數", 28: "莫耳絕對計數",
    29: "化學反應速率", 30: "氧化還原反應", 31: "解離說與電解質", 32: "酸與鹼的特性",
    33: "pH 值與指示劑", 34: "酸鹼中和反應", 35: "生活常見鹽類", 36: "有機化合物簡介",
    37: "烴類的性質", 38: "酯化反應", 39: "聚合物與塑膠", 40: "皂化反應與清潔劑",
    41: "力之三要素", 42: "虎克定律", 43: "摩擦力原理", 44: "壓力的定義與單位",
    45: "液體壓力與連通管", 46: "大氣壓力測試", 47: "阿基米德浮力原理", 48: "位置、位移與路徑長",
    49: "速度與速率", 50: "加速度運動", 51: "牛頓第一定律 (慣性)", 52: "牛頓第二定律 (F=ma)",
    53: "牛頓第三定律", 54: "萬有引力與圓周運動", 55: "功與功率", 56: "位能與動能",
    57: "力學能守恆", 58: "槓桿原理與力矩", 59: "滑輪的應用", 60: "斜面與螺旋、輪軸",
    61: "靜電感應", 62: "電流與電壓", 63: "歐姆定律與電阻", 64: "電功與電功率",
    65: "家用電器安全", 66: "磁場與磁力線", 67: "鋅銅電池原理", 68: "電鍍實驗",
    69: "安培右手定則", 70: "右手開掌定則", 71: "直流電動機原理", 72: "法拉第感應與發電機"
}

# --- 5. 初始化 Session ---
if 'audio_data' not in st.session_state: st.session_state.audio_data = None
if 'quiz_data' not in st.session_state: st.session_state.quiz_data = None

# --- 6. 通行證申請教學 ---
st.title("🥤 理化 AI 雞排珍奶實驗室 (助教版)")
st.markdown("""
<div class="guide-box">
    <b>📖 學生快速通行指南：</b><br>
    1. 點擊連結：<a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a> 並登入。<br>
    2. 點擊 <b>Create API key</b>，<b>務必勾選兩次同意條款</b>後按產生。<br>
    3. 複製金鑰，貼回下方即可解鎖大杯珍奶課程。
</div>
""", unsafe_allow_html=True)

user_key = st.text_input("🔑 通行證輸入區：", type="password")
st.divider()

# --- 7. 五大門派雙選單 (修正顯示邏輯) ---
st.subheader("📖 選擇學習單元")
parts_list = ["【第一門：物質初探】", "【二：能量流轉】", "【三：微觀審判】", "【四：力學秘術】", "【五：旋轉輪迴】"]
part_choice = st.selectbox("第一步：選擇大章節", parts_list)

if "第一門" in part_choice: r = range(1, 16)
elif "二" in part_choice: r = range(16, 27)
elif "三" in part_choice: r = range(27, 41)
elif "四" in part_choice: r = range(41, 55)
else: r = range(55, 73)

options = [f"第 {p} 頁：{page_titles.get(p, '單元內容')}" for p in r]
selected_page_str = st.selectbox("第二步：選擇精確單元名稱", options)
target_page = int(re.search(r"第 (\d+) 頁", selected_page_str).group(1))

if st.button(f"🚀 啟動【第 {target_page} 頁】圖文導讀"):
    if not user_key:
        st.warning("請先輸入通行證。")
    else:
        genai.configure(api_key=user_key)
        path_finals = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        path_bank = os.path.join(os.getcwd(), "data", "Huikao_Bank.pdf")
        
        with st.spinner("正在調製波霸奶茶..."):
            try:
                # 1. 雲端截圖顯示
                page_img = get_pdf_page_image(path_finals, target_page - 1)
                st.image(page_img, caption=f"講義第 {target_page} 頁內容截圖", use_column_width=True)
                
                # 2. AI 教學邏輯
                files = [genai.upload_file(path=path_finals)]
                if os.path.exists(path_bank): files.append(genai.upload_file(path=path_bank))
                
                model = genai.GenerativeModel('models/gemini-2.5-flash')
                prompt = files + [
                    f"你是有 20 年資歷的理化 AI 助教。1. 請針對第一個檔案第 {target_page} 頁詳細教學。"
                    "2. **【講義優先】**：必須先完整講解講義圖片中的所有例題與計算步驟。"
                    "3. 開場白請生活化，提到『雞排配大杯珍奶』的小確幸。說各位同學好！今天助教感冒沙啞。"
                    "4. 公式如 $$n=m/M$$ 與百分比 $$V\\%$$ 必須使用 LaTeX。"
                    "5. 講解完後用標籤 '[QUIZ_DATA]'。從檔案二搜尋 1 題相關長敘述會考題，附上選項、正確字母與引導提示。"
                ]
                res = model.generate_content(prompt)
                parts = res.text.split("[QUIZ_DATA]")
                st.markdown(parts[0])
                
                st.session_state.audio_data = asyncio.run(generate_voice(parts[0]))
                if len(parts) > 1: st.session_state.quiz_data = parts[1]
                st.balloons()
            except Exception as e:
                st.error(f"連線失敗：{e}")

# --- 8. 平板音訊手動播放 ---
if st.session_state.audio_data:
    st.info("🔊 **平板教學提醒**：請點擊播放鈕，聽助教導讀。")
    st.audio(st.session_state.audio_data, format="audio/mp3")

# --- 9. 隨堂挑戰 (會考長敘述題) ---
if st.session_state.quiz_data:
    st.divider()
    st.subheader("📝 歷屆會考真題挑戰")
    st.markdown(st.session_state.quiz_data.split("正確")[0])
    ans = st.radio("你的選擇：", ["A", "B", "C", "D"], key="q_ans")
    if st.button("送出解答"):
        correct = re.search(r"正確[選項|字母][：:\s]*([A-D])", st.session_state.quiz_data).group(1)
        hint = re.search(r"提示[：:\s]*(.*)", st.session_state.quiz_data).group(1)
        if ans == correct: st.success("🎯 答對了！這就是會考重點。")
        else: st.error(f"❌ AI 助教小提示：{hint}")