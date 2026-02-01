import streamlit as st
import google.generativeai as genai
import os
import asyncio
import edge_tts
import io
from PIL import Image

# --- 1. 頁面配置 (回歸最穩定字體) ---
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
    audio { width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 強化版男聲引擎 (使用 io 緩存) ---
async def generate_voice(text):
    communicate = edge_tts.Communicate(text, "zh-TW-YunxiNeural", rate="-5%")
    audio_stream = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_stream.write(chunk["data"])
    audio_stream.seek(0)
    return audio_stream.read()

# --- 3. 學生 API 通行證：快速申請版 (打勾兩次即可) ---
st.title("理化 AI 手搖飲實驗室")

st.markdown("""
<div class="guide-box">
    <b>各位同學好！請快速取得你的 AI 通行證：</b><br><br>
    步驟 1：點擊 <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a> 並登入個人帳號。<br>
    步驟 2：點擊 <b>Create API key</b>，勾選兩次同意條款後按產生。<br>
    步驟 3：點擊 <b>Copy</b> 複製代碼，回到這裡貼上。
</div>
""", unsafe_allow_html=True)

user_key = st.text_input("🔑 在這裡貼上你的 API 通行證：", type="password")

if user_key:
    try:
        genai.configure(api_key=user_key)
        st.success("✅ 通行證驗證成功！")
    except:
        st.error("金鑰格式錯誤，請檢查。")

st.divider()

# --- 4. 學生問答專區 ---
st.subheader("學生提問區：拍照或打字問 AI 老師")
col1, col2 = st.columns([1, 1])
with col1:
    student_q = st.text_input("輸入理化問題：", placeholder="例如：什麼是分子量？")
with col2:
    uploaded_file = st.file_uploader("拍照上傳題目：", type=["jpg", "png", "jpeg"])

if (student_q or uploaded_file) and user_key:
    with st.spinner("AI 老師正在思考答案..."):
        try:
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            prompt = ["你是資深男理化老師。1.開場說各位同學好。2.術語加註中文。3.解說要簡單。"]
            if uploaded_file: prompt.append(Image.open(uploaded_file))
            if student_q: prompt.append(f"問題：{student_q}")
            res = model.generate_content(prompt)
            st.info(f"老師解釋：\n\n{res.text}")
        except Exception as e:
            st.error(f"連線失敗：{e}")

st.divider()

# --- 5. 手搖飲教學與男聲播放器 (強化緩存版) ---
st.subheader("🥤 莫耳數攻略：珍珠奶茶計算法")

if st.button("🚀 啟動互動教學內容 (含男聲與進度條)"):
    if not user_key:
        st.warning("請先輸入通行證。")
    else:
        file_path = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        if os.path.exists(file_path):
            with st.spinner("🥤 AI 老師正在調製大杯珍奶中..."):
                try:
                    sample_file = genai.upload_file(path=file_path)
                    model = genai.GenerativeModel('models/gemini-2.5-flash')
                    prompt_text = [
                        sample_file,
                        "你是有 20 年資歷的男理化老師。請根據講義第 27 頁教學。"
                        "1. 開場說：各位同學好！今天老師感冒聲音沙啞，但為了你們最愛的珍奶，我們來聊聊莫耳數。"
                        "2. 完整列出講義中的例題題目內容。3. 使用珍珠奶茶珍珠量解釋 n = m / M。"
                        "4. 最後提醒多喝溫水，注意身體健康。"
                    ]
                    response = model.generate_content(prompt_text)
                    st.markdown(response.text)
                    
                    # 強化版語音生成
                    clean_text = response.text.replace('$', '').replace('*', '').replace('#', '').replace('\n', ' ')
                    audio_data = asyncio.run(generate_voice(clean_text))
                    
                    if audio_data:
                        st.audio(audio_data, format="audio/mp3")
                        st.caption("💡 學生可以拉動上方進度條重聽，或調整播放速度。")
                        st.balloons()
                except Exception as e:
                    st.error(f"語音生成失敗，請再試一次：{e}")
        else:
            st.error("找不到講義檔案。")

st.divider()

# --- 6. 階段性闖關練習 ---
st.subheader("隨堂挑戰：你懂了嗎？")
if 'quiz_step' not in st.session_state: st.session_state.quiz_step = 0

if st.session_state.quiz_step == 0:
    st.write("第一題：珍珠杯數挑戰")
    st.write("老師出題：一杯珍奶的珍珠重 50g (M)，現在給你 400g 的珍珠 (m)，請問可以裝成幾杯珍奶 (n)？")
    ans1 = st.text_input("你的答案：", key="a1")
    if st.button("送出解答"):
        if ans1 == "8":
            st.success("🎯 答對了！ n = 400 / 50 = 8 杯。")
            st.session_state.quiz_step = 1; st.rerun()
        else: st.error("再算算看喔！")

elif st.session_state.quiz_step == 1:
    st.write("第二題：理化魔王實戰")
    st.write("二氧化碳 (CO2) 的分子量 (M) 是 44。如果你有 88g 的二氧化碳 (m)，是多少莫耳 (n)？")
    ans2 = st.text_input("你的答案：", key="a2")
    if st.button("確認挑戰結果"):
        if ans2 == "2":
            st.balloons(); st.success("🌟 超級優秀！ 88 / 44 = 2 莫耳。")
            if st.button("重新練習"): st.session_state.quiz_step = 0; st.rerun()