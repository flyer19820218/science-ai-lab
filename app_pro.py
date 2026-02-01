import streamlit as st
import google.generativeai as genai
import os
import asyncio
import edge_tts
import io

# --- 1. 頁面配置 (RWD 與 翩翩體) ---
st.set_page_config(page_title="理化 AI 手搖飲實驗室", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="css"], .stMarkdown, p, h1, h2, h3, span, label, li {
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', 'KaiTi', sans-serif !important;
    }
    .guide-container {
        background-color: #f1f8e9;
        padding: 20px;
        border-radius: 15px;
        border: 2px dashed #8bc34a;
        margin-bottom: 20px;
    }
    .stButton>button {
        background-color: #e3f2fd !important;
        border-radius: 8px;
        font-weight: bold;
        width: 100%;
        height: 45px;
    }
    /* 讓播放器在手機上也能滿版 */
    audio { width: 100%; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 穩定版男聲引擎 (非同步轉同步) ---
async def generate_voice_bytes(text):
    # 使用沉穩男聲 Yunxi，語速稍微放慢 -5% 更有老師感
    communicate = edge_tts.Communicate(text, "zh-TW-YunxiNeural", rate="-5%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- 3. 學生 API 通行證：保姆級 6 步教學 ---
st.title("🔬 理化 AI 手搖飲實驗室")

with st.container():
    st.markdown("""
    <div class="guide-container">
        <h3 style='margin-top:0;'>各位小朋友好！請跟著以下步驟取得你的 AI 通行證：</h3>
        1. 點擊連結開啟網頁：<a href="https://aistudio.google.com/app/apikey" target="_blank">👉 Google AI Studio (金鑰申請處)</a><br>
        2. <b>重要：請務必使用個人 Gmail 帳號登入</b> (學校帳號可能無法使用)。<br>
        3. 點擊畫面上的藍色按鈕 <b>"Create API key"</b>。<br>
        4. 選擇 <b>"Create API key in new project"</b>。<br>
        5. 看到一串代碼後，點擊 <b>"Copy"</b> 複製起來。<br>
        6. 回到本網頁，把代碼貼在下方的輸入框中，按下 Enter。
    </div>
    """, unsafe_allow_html=True)

user_key = st.text_input("🔑 在這裡貼上你的 API 通行證：", type="password")

if user_key:
    try:
        genai.configure(api_key=user_key)
        st.success("✅ 通行證已就緒！使用的模型：Gemini 2.5 Flash")
    except:
        st.error("⚠️ 金鑰錯誤，請重新複製。")

st.divider()

# --- 4. 學生問問題專區 ---
st.subheader("💬 學生提問區：有問題直接問 AI 老師")
student_q = st.text_input("輸入你想問的理化問題：", placeholder="例如：什麼是分子量？")

if student_q and user_key:
    with st.spinner("AI 老師正在思考答案..."):
        try:
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            prompt_q = f"你是資深男理化老師。請回答學生：'{student_q}'。1. 開場說『各位同學好』。2. 術語後加註中文。3. 解說要簡單好懂。"
            res = model.generate_content(prompt_q)
            st.info(f"👨‍🏫 **老師解釋：**\n\n{res.text}")
        except Exception as e:
            st.error(f"連線出錯：{e}")

st.divider()

# --- 5. 手搖飲教學 (含題目、男聲、進度條) ---
st.subheader("🥤 莫耳數攻略：珍珠奶茶計算法")

if st.button("🚀 啟動互動教學 (含男聲講述與進度條)"):
    if not user_key:
        st.warning("請先輸入通行證。")
    else:
        file_path = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        if os.path.exists(file_path):
            with st.spinner("正在為大家翻閱最新講義並錄製語音..."):
                try:
                    sample_file = genai.upload_file(path=file_path)
                    model = genai.GenerativeModel('models/gemini-2.5-flash')
                    
                    # 提示詞優化：包含題目與情境
                    prompt = [
                        sample_file,
                        "你是有 20 年資歷的男理化老師。請根據講義第 27 頁教學。"
                        "1. 開場說：『各位同學好！歡迎來到理化教室。今天老師感冒聲音沙啞，但我們要來聊聊莫耳數...』"
                        "2. **重要**：請在內容中完整呈現講義中的例題題目內容，方便學生邊聽邊看。"
                        "3. 使用珍珠奶茶比喻解釋 n = m / M。n 是杯數，m 是珍珠總重，M 是一杯珍珠的重量。"
                        "4. 英文術語後加註中文。最後提醒多喝溫水，注意身體健康。"
                    ]
                    
                    response = model.generate_content(prompt)
                    teaching_text = response.text
                    st.markdown(teaching_text)
                    
                    # 語音生成 (男聲 + 穩定進度條)
                    # 清理特殊字符，避免 AI 唸出亂碼
                    clean_text = teaching_text.replace('$', '').replace('*', '').replace('#', '').replace('\n', ' ')
                    audio_data = asyncio.run(generate_voice_bytes(clean_text))
                    
                    # 使用 st.audio 播放位元流，會自動出現進度條
                    st.audio(audio_data, format="audio/mp3")
                    st.caption("💡 學生可以拉動上方進度條重聽，或調整播放速度。")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"語音生成失敗，請再點一次：{e}")
        else:
            st.error("找不到講義 Ph_Ch_finals.pdf，請確認 data 資料夾。")

st.divider()

# --- 6. 階段性互動練習 ---
st.subheader("📝 隨堂挑戰：你懂了嗎？")
if 'quiz_step' not in st.session_state:
    st.session_state.quiz_step = 0

if st.session_state.quiz_step == 0:
    st.write("🥤 **第一關：珍珠杯數題**")
    st.write("老師出題：一杯珍奶的珍珠重 50g ($M$)，現在店長給你 500g 的珍珠 ($m$)，請問總共可以裝成幾杯珍奶 ($n$)？")
    ans1 = st.text_input("你的答案：", key="a1")
    if st.button("送出解答"):
        if ans1 == "10":
            st.success("答對了！ $n = 500 / 50 = 10$ 杯。")
            st.session_state.quiz_step = 1
            st.rerun()
        else: st.error("再算算看喔！")

elif st.session_state.quiz_step == 1:
    st.write("🧪 **第二關：理化魔王題**")
    st.write("老師出題：二氧化碳 ($CO_2$) 的分子量 ($M$) 是 44。如果你現在有 88g 的二氧化碳 ($m$)，請問這是多少莫耳 ($n$)？")
    ans2 = st.text_input("你的答案：", key="a2")
    if st.button("確認挑戰結果"):
        if ans2 == "2":
            st.balloons()
            st.success("超級優秀！ $88 / 44 = 2$ 莫耳。你掌握精髓了！")
            if st.button("重新練習"):
                st.session_state.quiz_step = 0
                st.rerun()