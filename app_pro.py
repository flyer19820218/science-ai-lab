import streamlit as st
import google.generativeai as genai
import os
import asyncio
import edge_tts
import io
import re
from PIL import Image

# --- 1. 頁面配置 (翩翩體、全黑文字) ---
st.set_page_config(page_title="理化 AI 手搖飲實驗室", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="css"], .stMarkdown, p, h1, h2, h3, span, label, li {
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', 'KaiTi', sans-serif !important;
    }
    .guide-box {
        background-color: #f1f8e9;
        padding: 20px;
        border-radius: 12px;
        border: 2px dashed #8bc34a;
        margin-bottom: 20px;
    }
    .stButton>button {
        background-color: #e3f2fd !important;
        border-radius: 8px;
        font-weight: bold;
        width: 100%;
        height: 50px;
    }
    audio { width: 100%; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 穩定版助教語音 (HsiaoChen) ---
async def generate_voice(text):
    # 移除 LaTeX 符號與特殊字符，確保語音平順
    clean_text = re.sub(r'\$+', '', text)
    clean_text = clean_text.replace('\\%', '百分之').replace('%', '百分之')
    clean_text = clean_text.replace('*', '').replace('#', '').replace('\n', ' ')
    
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- 3. 初始化 Session (確保練習題不會因為網頁刷新消失) ---
if 'active_quiz' not in st.session_state:
    st.session_state.active_quiz = None

# --- 4. 學生 API 指南 (打勾兩次版) ---
st.title("🔬 理化 AI 手搖飲實驗室")

st.markdown("""
<div class="guide-box">
    <b>各位同學好！請照著以下步驟取得你的 AI 通行證：</b><br><br>
    1. 點擊 <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a> 並登入。<br>
    2. 點擊 <b>Create API key</b>，<b>勾選兩次同意條款</b>後按產生。<br>
    3. 複製金鑰，回到這裡貼上按 Enter。
</div>
""", unsafe_allow_html=True)

user_key = st.text_input("🔑 在這裡貼上你的通行證：", type="password")

if user_key:
    try:
        genai.configure(api_key=user_key)
        st.success("✅ 通行證驗證成功！正在連接 HsiaoChen 老師...")
    except:
        st.error("❌ 金鑰錯誤，請重新複製。")

st.divider()

# --- 5. 講義頁碼導讀區 ---
st.subheader("🥤 自主學習區：翻開講義指定頁面")

target_page = st.number_input("📖 請輸入講義頁碼 (1-71)：", min_value=1, max_value=71, value=1)

if st.button(f"🚀 啟動第 {target_page} 頁精確教學"):
    if not user_key:
        st.warning("請先輸入通行證。")
    else:
        file_path = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        if os.path.exists(file_path):
            with st.spinner(f"正在嚴格讀取第 {target_page} 頁並調製大杯珍奶..."):
                try:
                    sample_file = genai.upload_file(path=file_path)
                    model = genai.GenerativeModel('models/gemini-2.5-flash')
                    
                    # 提示詞下死命令：絕對服從 PDF
                    prompt_text = [
                        sample_file,
                        f"你是有 20 年資歷的理化老師。請嚴格根據講義第 {target_page} 頁內容進行教學。"
                        "1. 教學內容必須完全對齊講義數據與題目，不得自行編造。"
                        "2. 使用手搖飲珍珠情境解釋原理。化學式如 $CO_2$ 與公式如 $n = m / M$ 必須使用 LaTeX 格式。"
                        "3. 關於百分比濃度，請寫成 $$V\\% = \\left( \\frac{\\text{溶質體積}}{\\text{溶液體積}} \\right) \\times 100\\%$$。注意百分比符號要加轉義 \\%。"
                        "4. 結尾請用標籤 '[QUIZ_DATA]' 包裹以下內容：題目、選項A、選項B、選項C、選項D、正確字母、給學生的引導提示。"
                        "5. 最後提醒多喝溫水。"
                    ]
                    
                    response = model.generate_content(prompt_text)
                    full_text = response.text
                    
                    # 拆分內容與練習題數據
                    parts = full_text.split("[QUIZ_DATA]")
                    teaching_txt = parts[0]
                    st.markdown(teaching_txt)
                    
                    # 語音播放
                    audio_bytes = asyncio.run(generate_voice(teaching_txt))
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3")
                    
                    # 儲存題目數據
                    if len(parts) > 1:
                        st.session_state.active_quiz = parts[1]
                    
                    st.balloons()
                except Exception as e:
                    st.error(f"連線失敗：{e}")
        else:
            st.error("找不到講義檔案。")

# --- 6. 引導式問答界面 ---
if st.session_state.active_quiz:
    st.divider()
    st.subheader("📝 隨堂挑戰：引導式腦力激盪")
    
    quiz_raw = st.session_state.active_quiz
    # 提取題目與選項 (排除正確答案字母以免劇透)
    quiz_display = quiz_raw.split("正確")[0]
    st.markdown(quiz_display)
    
    student_choice = st.radio("你的解答是：", ["A", "B", "C", "D"], key="active_user_q")
    
    if st.button("送出解答"):
        # 從 raw 數據中抓取正確答案與引導提示
        correct_match = re.search(r"正確[選項|字母][：:\s]*([A-D])", quiz_raw)
        hint_match = re.search(r"引導提示[：:\s]*(.*)", quiz_raw)
        
        correct_ans = correct_match.group(1).strip() if correct_match else "A"
        hint_txt = hint_match.group(1).strip() if hint_match else "再想一下這頁的關鍵原理喔！"
        
        if student_choice == correct_ans:
            st.success(f"🎯 答對了！就是 {student_choice}。你的邏輯非常正確！")
        else:
            st.error(f"❌ 哎呀，再想想看！ HsiaoChen 老師的小提示：{hint_txt}")