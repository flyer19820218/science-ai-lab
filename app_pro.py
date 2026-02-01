import streamlit as st
import google.generativeai as genai
import os
import asyncio
import edge_tts
import io
import re
from PIL import Image

# --- 1. 頁面配置 (全黑文字、翩翩體) ---
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

# --- 2. 核心女聲引擎 (HsiaoChen) ---
async def generate_voice(text):
    # 移除 LaTeX 符號與轉義字符，確保語音平順
    clean_text = re.sub(r'\$+', '', text)
    clean_text = clean_text.replace('\\%', '百分之').replace('%', '百分之')
    clean_text = clean_text.replace('*', '').replace('#', '').replace('\n', ' ')
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- 3. 學生 API 指南 ---
st.title("🔬 理化 AI 手搖飲實驗室")

st.markdown("""
<div class="guide-box">
    <b>各位同學好！請快速取得你的 AI 通行證：</b><br><br>
    1. 點擊 <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a> 並登入。<br>
    2. 點擊 <b>Create API key</b>，勾選兩次同意後按產生。<br>
    3. 複製金鑰，回到這裡貼上按 Enter。
</div>
""", unsafe_allow_html=True)

user_key = st.text_input("在這裡貼上你的通行證：", type="password")

if user_key:
    try:
        genai.configure(api_key=user_key)
        st.success("✅ 通行證驗證成功！")
    except:
        st.error("❌ 金鑰格式錯誤。")

st.divider()

# --- 4. 初始化 Session State ---
if 'current_quiz' not in st.session_state:
    st.session_state.current_quiz = None

# --- 5. 學生問答專區 ---
st.subheader("💬 學生提問區：拍照或打字問問題")
col_q, col_up = st.columns([1, 1])
with col_q:
    student_q = st.text_input("輸入問題：", placeholder="例如：什麼是原子量？")
with col_up:
    uploaded_image = st.file_uploader("📷 拍照上傳題目：", type=["jpg", "png", "jpeg"])

if (student_q or uploaded_image) and user_key:
    with st.spinner("👩‍🏫 AI 老師正在思考答案..."):
        try:
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            prompt = ["你是資深理化老師。化學式如 $CO_2$ 與公式必須嚴格使用 LaTeX 格式。"]
            parts = prompt + ([Image.open(uploaded_image)] if uploaded_image else []) + ([f"問題：{student_q}"] if student_q else [])
            res = model.generate_content(parts)
            st.info(f"👩‍🏫 老師解釋：\n\n{res.text}")
        except Exception as e:
            st.error(f"連線失敗：{e}")

st.divider()

# --- 6. 講義頁碼導讀與引導式練習 ---
st.subheader("🥤 自主學習區：翻開講義指定頁面")

target_page = st.number_input("請輸入講義頁碼 (1-71)：", min_value=1, max_value=71, value=27)

if st.button(f"🚀 啟動第 {target_page} 頁教學"):
    if not user_key:
        st.warning("請先輸入通行證。")
    else:
        file_path = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        if os.path.exists(file_path):
            with st.spinner(f"正在準備第 {target_page} 頁教學中..."):
                try:
                    sample_file = genai.upload_file(path=file_path)
                    model = genai.GenerativeModel('models/gemini-2.5-flash')
                    
                    # 強化邏輯：要求 AI 先自檢答案
                    prompt_text = [
                        sample_file,
                        f"你是有 20 年資歷的理化老師。請針對講義第 {target_page} 頁教學。"
                        "1. 開場說：各位同學好！今天老師感冒沙啞，我們來看看這一頁。2. 完整列出該頁例題。 "
                        "3. 使用珍珠奶茶情境解釋原理。公式如 $$n = \\frac{m}{M}$$ 必須使用 LaTeX 格式。"
                        "4. 百分比符號必須轉義為 \\%（例如 V\\%）。"
                        "5. 重點：課程結束後，請精準使用標籤 '[QUIZ_DATA]' 包裹：題目、選項、正確字母、一個引導提示。"
                        "請務必再次檢查『正確字母』是否與題目邏輯相符，不要給錯答案。"
                    ]
                    
                    response = model.generate_content(prompt_text)
                    full_text = response.text
                    
                    content_parts = full_text.split("[QUIZ_DATA]")
                    teaching_txt = content_parts[0]
                    st.markdown(teaching_txt)
                    
                    audio_bytes = asyncio.run(generate_voice(teaching_txt))
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3")
                    
                    if len(content_parts) > 1:
                        st.session_state.current_quiz = content_parts[1]
                    
                    st.balloons()
                except Exception as e:
                    st.error(f"連線出錯：{e}")
        else:
            st.error("找不到講義檔案。")

# --- 7. 顯示引導式練習界面 ---
if st.session_state.current_quiz:
    st.divider()
    st.subheader("📝 隨堂挑戰")
    
    quiz_raw = st.session_state.current_quiz
    st.info("請根據剛才的教學內容，選出正確答案：")
    
    # 清理題目顯示
    q_display = quiz_raw.split("正確")[0]
    st.markdown(q_display)
    
    student_ans = st.radio("你的選擇：", ["A", "B", "C", "D"], key="quiz_radio")
    
    if st.button("送出解答"):
        # 尋找正確答案字母
        match = re.search(r"[正確選項|正確字母][：:\s]*([A-D])", quiz_raw)
        hint_match = re.search(r"引導提示[：:\s]*(.*)", quiz_raw)
        
        correct_letter = match.group(1).strip() if match else "A"
        hint_text = hint_match.group(1).strip() if hint_match else "再想一下頁面中的關鍵公式喔！"
        
        if student_ans == correct_letter:
            st.success(f"🎯 太棒了！答案正是 {student_ans}。你掌握了這一頁的精髓！")
        else:
            st.error(f"❌ 不對喔！ HsiaoChen 老師的小提醒：{hint_text}")