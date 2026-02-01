import streamlit as st
import google.generativeai as genai
import os
import asyncio
import edge_tts
import io
from PIL import Image

# --- 1. 頁面配置 (翩翩體與全黑文字) ---
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

# --- 2. 核心男聲引擎 (YunxiNeural) ---
async def generate_voice(text):
    communicate = edge_tts.Communicate(text, "zh-TW-YunxiNeural", rate="-5%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- 3. 學生 API 通行證：快速申請版 ---
st.title("🔬 理化 AI 手搖飲實驗室")

st.markdown("""
<div class="guide-box">
    <b>各位同學好！請快速取得你的 AI 通行證：</b><br><br>
    步驟 1：點擊 <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a> 並登入。<br>
    步驟 2：點擊 <b>Create API key</b>，勾選兩次同意後按產生。<br>
    步驟 3：複製金鑰，回到這裡貼上。
</div>
""", unsafe_allow_html=True)

user_key = st.text_input("🔑 在這裡貼上你的 API 通行證：", type="password")

if user_key:
    try:
        genai.configure(api_key=user_key)
        st.success("✅ 通行證驗證成功！")
    except:
        st.error("❌ 金鑰格式錯誤，請檢查。")

st.divider()

# --- 4. 學生問答區 ---
st.subheader("💬 學生提問區：拍照或打字問問題")
col1, col2 = st.columns([1, 1])
with col1:
    student_q = st.text_input("輸入你想問的理化問題：")
with col2:
    uploaded_file = st.file_uploader("📷 拍照上傳題目截圖：", type=["jpg", "png", "jpeg"])

if (student_q or uploaded_file) and user_key:
    with st.spinner("👨‍🏫 AI 老師思考中..."):
        try:
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            prompt = ["資深男理化老師。化學式如 $$H_2O$$ 必須使用 LaTeX 格式。解說要簡單。"]
            if uploaded_file: prompt.append(Image.open(uploaded_file))
            if student_q: prompt.append(f"問題內容：{student_q}")
            res = model.generate_content(prompt)
            st.info(f"👨‍🏫 老師解釋：\n\n{res.text}")
        except Exception as e:
            st.error(f"連線失敗：{e}")

st.divider()

# --- 5. 動態分頁教學區 ---
st.subheader("🥤 自主學習區：翻開講義學單元")

# 讓學生輸入頁碼
target_page = st.number_input("📖 請輸入你想學習的講義頁碼 (例如: 27)：", min_value=1, max_value=100, value=27)

if st.button("🚀 啟動該頁面互動教學"):
    if not user_key:
        st.warning("請先輸入通行證。")
    else:
        file_path = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        if os.path.exists(file_path):
            with st.spinner(f"🥤 AI 老師正在翻閱第 {target_page} 頁講義並準備珍奶中..."):
                try:
                    sample_file = genai.upload_file(path=file_path)
                    model = genai.GenerativeModel('models/gemini-2.5-flash')
                    
                    # 動態提示詞：根據輸入頁碼調整
                    prompt_text = [
                        sample_file,
                        f"你是有 20 年資歷的男理化老師。請針對講義第 {target_page} 頁的內容進行教學。"
                        "1. 開場說：各位同學好！今天老師感冒沙啞，我們來看看這一頁的重點。"
                        "2. 請完整整理出這一頁的關鍵概念與例題內容。"
                        "3. 盡可能使用『珍珠奶茶』的情境或比喻來解釋科學原理（例如莫耳數公式 $n = m / M$）。"
                        "4. 所有的化學式與公式必須嚴格使用 LaTeX 格式（如 $$CO_2$$, $$n = \\frac{m}{M}$$）。"
                        "5. 最後溫馨提醒學生多喝溫水，注意健康。"
                    ]
                    
                    response = model.generate_content(prompt_text)
                    st.markdown(response.text)
                    
                    # 生成音訊
                    clean_text = response.text.replace('$', '').replace('*', '').replace('#', '').replace('\n', ' ')
                    audio_bytes = asyncio.run(generate_voice(clean_text))
                    
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3")
                        st.balloons()
                except Exception as e:
                    st.error(f"連線出錯：{e}")
        else:
            st.error("找不到講義 Ph_Ch_finals.pdf，請確認 data 資料夾。")

st.divider()

# --- 6. 隨堂挑戰 (作為基礎示範) ---
st.subheader("📝 莫耳數魔王挑戰 (基礎觀測)")
st.write("二氧化碳 ($$CO_2$$) 分子量 ($$M$$) 是 44。如果有 88g 的二氧化碳 ($$m$$)，是多少莫耳 ($$n$$)？")
ans = st.text_input("你的答案：", key="q1")
if st.button("送出挑戰答案"):
    if ans == "2":
        st.success("🎯 優秀！ $$n = \\frac{88}{44} = 2$$ 莫耳。")
    else:
        st.error("再想一下喔，總重除以分子量！")