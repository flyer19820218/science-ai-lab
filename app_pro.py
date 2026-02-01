import streamlit as st
import google.generativeai as genai
import os
import asyncio
import edge_tts
import io
import re
from PIL import Image

# --- 1. 頁面配置 ---
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
    </style>
    """, unsafe_allow_html=True)

# --- 2. 語音生成引擎 ---
async def generate_voice(text):
    communicate = edge_tts.Communicate(text, "zh-TW-YunxiNeural", rate="-5%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- 3. 快速 API 指南 ---
st.title("🔬 理化 AI 手搖飲實驗室")

st.markdown("""
<div class="guide-box">
    <b>各位同學好！請快速取得你的 AI 通行證：</b><br><br>
    1. 點擊 <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a> 並登入。<br>
    2. 點擊 <b>Create API key</b>，勾選兩次同意後按產生。<br>
    3. 複製金鑰，回到這裡貼上。
</div>
""", unsafe_allow_html=True)

user_key = st.text_input("🔑 在這裡貼上你的 API 通行證：", type="password")

if user_key:
    try:
        genai.configure(api_key=user_key)
        st.success("✅ 通行證驗證成功！")
    except:
        st.error("金鑰有誤，請檢查。")

st.divider()

# --- 4. 學生問答區 ---
st.subheader("💬 學生提問區：拍照或打字問問題")
col_q, col_i = st.columns([1, 1])
with col_q:
    student_q = st.text_input("輸入理化問題：")
with col_i:
    uploaded_file = st.file_uploader("📷 拍照上傳題目截圖：", type=["jpg", "png", "jpeg"])

if (student_q or uploaded_file) and user_key:
    with st.spinner("👨‍🏫 AI 老師思考中..."):
        try:
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            prompt = ["資深男理化老師。化學式如 $$H_2O$$ 必須使用 LaTeX 格式。"]
            if uploaded_file: prompt.append(Image.open(uploaded_file))
            if student_q: prompt.append(f"問題：{student_q}")
            res = model.generate_content(prompt)
            st.info(f"老師解釋：\n\n{res.text}")
        except Exception as e:
            st.error(f"連線失敗：{e}")

st.divider()

# --- 5. 單元選擇與動態教學 ---
st.subheader("🥤 自主學習區：選擇你想上的課")

# 單元與頁碼映射表
unit_map = {
    "1-1 原子量與分子量 (p.25)": 25,
    "1-2 莫耳數觀念 (p.27)": 27,
    "1-3 化學計量 (p.30)": 30,
    "2-1 質量守恆定律 (p.35)": 35,
    "2-2 化學反應式 (p.38)": 38
}

selected_unit = st.selectbox("📖 請選擇學習單元：", list(unit_map.keys()))
target_page = unit_map[selected_unit]

if st.button(f"🚀 啟動【{selected_unit}】互動教學"):
    if not user_key:
        st.warning("請先輸入通行證。")
    else:
        file_path = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        if os.path.exists(file_path):
            with st.spinner("🥤 AI 老師正在準備講義與珍奶中..."):
                try:
                    sample_file = genai.upload_file(path=file_path)
                    model = genai.GenerativeModel('models/gemini-2.5-flash')
                    
                    # 提示詞：要求同時產生課程內容與一道隨機練習題
                    prompt_text = [
                        sample_file,
                        f"你是有 20 年資歷的男理化老師。請針對講義第 {target_page} 頁教學。"
                        "1. 開場說：各位同學好！歡迎來到理化教室。今天老師感冒沙啞，但我們還是要來聊聊這一頁。"
                        "2. 使用手搖飲珍珠情境解釋這一頁的科學原理。3. 所有的化學式與公式必須嚴格使用 LaTeX 格式。"
                        "4. 在教學結束後，請加上分隔線 '---QUIZ---'，並針對本頁出一道『隨堂挑戰題』(含選項) 與正確答案。"
                        "5. 最後提醒多喝溫水。"
                    ]
                    
                    response = model.generate_content(prompt_text)
                    full_text = response.text
                    
                    # 拆分教學內容與練習題
                    parts = full_text.split("---QUIZ---")
                    teaching_content = parts[0]
                    quiz_content = parts[1] if len(parts) > 1 else "（今日無隨堂練習）"
                    
                    # 顯示內容
                    st.markdown(teaching_content)
                    
                    # 生成並播放語音 (只唸教學內容)
                    clean_text = teaching_content.replace('$', '').replace('*', '').replace('#', '').replace('\n', ' ')
                    audio_bytes = asyncio.run(generate_voice(clean_text))
                    st.audio(audio_bytes, format="audio/mp3")
                    
                    # 顯示隨機練習題
                    st.success("📝 **隨堂挑戰題**")
                    st.markdown(quiz_content)
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"連線出錯：{e}")
        else:
            st.error("找不到講義檔案。")