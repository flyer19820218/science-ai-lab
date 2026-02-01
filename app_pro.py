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

# --- 2. 核心女聲引擎 (HsiaoChen 穩定版) ---
async def generate_voice(text):
    # 移除 LaTeX 符號避免語音唸出程式碼
    clean_text = re.sub(r'\$+', '', text)
    clean_text = clean_text.replace('*', '').replace('#', '').replace('\n', ' ')
    # 換成穩定女聲：zh-TW-HsiaoChenNeural
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- 3. 學生快速指南 (簡化版) ---
st.title("🔬 理化 AI 手搖飲實驗室")

st.markdown("""
<div class="guide-box">
    <b>各位同學好！請快速取得你的 AI 通行證：</b><br><br>
    1. 點擊 <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a> 並登入。<br>
    2. 點擊 <b>Create API key</b>，勾選兩次同意後按產生。<br>
    3. 複製金鑰，回到這裡貼上按 Enter。
</div>
""", unsafe_allow_html=True)

user_key = st.text_input("🔑 在這裡貼上你的通行證：", type="password")

if user_key:
    try:
        genai.configure(api_key=user_key)
        st.success("✅ 通行證驗證成功！")
    except:
        st.error("❌ 金鑰格式錯誤。")

st.divider()

# --- 4. 學生問答區 ---
st.subheader("💬 學生提問區：拍照或打字問問題")
col_q, col_up = st.columns([1, 1])
with col_q:
    student_q = st.text_input("輸入問題：", placeholder="例如：什麼是分子量？")
with col_up:
    uploaded_image = st.file_uploader("📷 拍照上傳題目：", type=["jpg", "png", "jpeg"])

if (student_q or uploaded_image) and user_key:
    with st.spinner("👩‍🏫 AI 老師正在思考答案..."):
        try:
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            prompt = ["你是資深理化老師。化學式如 $CO_2$ 與公式如 $n=m/M$ 必須使用 LaTeX 格式。"]
            parts = prompt + ([Image.open(uploaded_image)] if uploaded_image else []) + ([f"問題：{student_q}"] if student_q else [])
            res = model.generate_content(parts)
            st.info(f"👩‍🏫 老師解釋：\n\n{res.text}")
        except Exception as e:
            st.error(f"連線失敗：{e}")

st.divider()

# --- 5. 講義頁碼導讀區 (回歸指定頁碼) ---
st.subheader("🥤 自主學習區：翻開講義指定頁面")

target_page = st.number_input("📖 請輸入你想學習的講義頁碼 (1-71)：", min_value=1, max_value=71, value=27)

if st.button(f"🚀 啟動第 {target_page} 頁互動教學"):
    if not user_key:
        st.warning("請先輸入通行證。")
    else:
        file_path = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        if os.path.exists(file_path):
            with st.spinner(f"正在翻閱第 {target_page} 頁並調製大杯珍奶中..."):
                try:
                    sample_file = genai.upload_file(path=file_path)
                    model = genai.GenerativeModel('models/gemini-2.5-flash')
                    
                    # 強化隨機練習題的提示詞
                    prompt_text = [
                        sample_file,
                        f"你是有 20 年資歷的理化老師。請針對講義第 {target_page} 頁教學。"
                        "1. 開場說：各位同學好！今天老師感冒聲音沙啞，我們來看看這一頁。2. 完整列出該頁例題。 "
                        "3. 使用珍珠奶茶比喻解釋原理。4. 化學式與公式必須嚴格使用 LaTeX 格式（如 $CO_2$, $n = \\frac{m}{M}$）。"
                        "5. 教學結束後，請加上分隔線 '[QUIZ_START]'，並根據本頁內容出一道選擇題與答案。6. 提醒多喝溫水。"
                    ]
                    
                    response = model.generate_content(prompt_text)
                    full_text = response.text
                    
                    # 拆分內容與練習題
                    parts = full_text.split("[QUIZ_START]")
                    st.markdown(parts[0])
                    
                    # 語音生成 (HsiaoChen 女聲)
                    audio_bytes = asyncio.run(generate_voice(parts[0]))
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3")
                    
                    # 顯示練習題
                    if len(parts) > 1:
                        st.success("📝 **隨堂隨機挑戰**")
                        st.markdown(parts[1])
                    
                    st.balloons()
                except Exception as e:
                    st.error(f"連線出錯：{e}")
        else:
            st.error("找不到講義檔案。")