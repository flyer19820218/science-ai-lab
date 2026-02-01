import streamlit as st
import google.generativeai as genai
import os
import asyncio
import edge_tts
import io

# --- 1. 頁面配置 (翩翩體與 RWD) ---
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
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 穩定版男聲生成 (直接輸出 Byte 避免讀取錯誤) ---
async def get_audio_data(text):
    # 使用老師指定的雲端男聲：Yunxi
    communicate = edge_tts.Communicate(text, "zh-TW-YunxiNeural", rate="-5%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- 3. 學生 API 指南 ---
st.title("🔬 理化 AI 手搖飲實驗室")

with st.expander("各位小朋友好！點此看『取得通行證』詳細步驟", expanded=False):
    st.markdown("""
    <div class="guide-box">
        1. 點擊：<a href="https://aistudio.google.com/app/apikey" target="_blank">👉 Google AI Studio</a><br>
        2. <b>請使用個人 Gmail 帳號登入</b>。<br>
        3. 點擊按鈕 <b>"Create API key"</b>。<br>
        4. 選擇 <b>"Create API key in new project"</b>。<br>
        5. 點擊 <b>"Copy"</b> 複製代碼。<br>
        6. 回到本網頁，把代碼貼在下方輸入框。
    </div>
    """, unsafe_allow_html=True)

user_key = st.text_input("🔑 在這裡貼上你的 API 通行證：", type="password")

if user_key:
    try:
        genai.configure(api_key=user_key)
        st.success("✅ 通行證驗證成功！")
    except:
        st.error("⚠️ 金鑰有誤。")

st.divider()

# --- 4. 學生問答專區 ---
st.subheader("💬 學生提問區")
student_q = st.text_input("輸入問題：", placeholder="例如：什麼是原子量？")
if student_q and user_key:
    with st.spinner("AI 老師思考中..."):
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        res = model.generate_content(f"你是資深理化老師，回答學生：{student_q}。術語加註中文。")
        st.info(res.text)

st.divider()

# --- 5. 手搖飲教學 (含題目、男聲、進度條) ---
st.subheader("🥤 莫耳數攻略：珍珠奶茶計算法")

if st.button("🚀 啟動互動教學 (含男聲講述)"):
    if not user_key:
        st.warning("請先輸入通行證。")
    else:
        file_path = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        if os.path.exists(file_path):
            with st.spinner("正在讀取講義並錄製語音..."):
                try:
                    sample_file = genai.upload_file(path=file_path)
                    model = genai.GenerativeModel('models/gemini-2.5-flash')
                    
                    # 老師要求：把講義題目寫進來，用男聲導讀
                    prompt = [
                        sample_file,
                        "你是有 20 年資歷的男理化老師。請根據講義第 27 頁教學。"
                        "1. 開場說：『各位同學好！我是你們的理化助教。今天老師感冒聲音沙啞，但我們還是要來攻克莫耳數...』"
                        "2. **重要**：請在內容中完整呈現講義中的例題題目，並逐字引導學生。 3. 使用珍珠奶茶比喻解釋 n = m/M。"
                        "4. 最後提醒大家多喝水，注意身體健康。"
                    ]
                    
                    response = model.generate_content(prompt)
                    teaching_text = response.text
                    st.markdown(teaching_text)
                    
                    # 語音生成與進度條
                    clean_text = teaching_text.replace('$', '').replace('*', '').replace('#', '')
                    audio_bytes = asyncio.run(get_audio_data(clean_text))
                    
                    # 顯示進度條播放器
                    st.audio(audio_bytes, format="audio/mp3")
                    st.caption("💡 學生可以拉動上方進度條重聽，或點擊右側調整播放速度。")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"語音生成失敗：{e}")
        else:
            st.error("找不到講義 Ph_Ch_finals.pdf，請確認 data 資料夾。")