import streamlit as st
import google.generativeai as genai
import os
import asyncio
import edge_tts
import base64

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
        color: #000000 !important;
        border: 1px solid #bbdefb !important;
        border-radius: 8px;
        font-weight: bold;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 語音生成函數 (高質感男聲 + 進度條支持) ---
async def generate_male_voice(text):
    # 使用 Microsoft Edge 的雲端男聲：Yunxi
    communicate = edge_tts.Communicate(text, "zh-TW-YunxiNeural", rate="-5%")
    temp_file = "output.mp3"
    await communicate.save(temp_file)
    return temp_file

# --- 3. 學生 API 通行證指南 ---
st.title("🔬 理化 AI 手寫教學實驗室")

with st.expander("🆘 學生請點此查看『如何取得通行證』詳細步驟", expanded=False):
    st.markdown("""
    <div class="guide-container">
        1. 點擊：<a href="https://aistudio.google.com/app/apikey" target="_blank">👉 Google AI Studio</a><br>
        2. <b>請使用個人 Gmail 帳號登入</b>。<br>
        3. 點擊藍色按鈕 <b>"Create API key"</b>。<br>
        4. 選擇 <b>"Create API key in new project"</b>。<br>
        5. 點擊 <b>"Copy"</b> 複製代碼。<br>
        6. 回到本網頁，把代碼貼在下方輸入框。
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

# --- 4. 學生提問區 ---
st.subheader("💬 學生隨機提問")
student_q = st.text_input("輸入你想問的理化問題：")
if student_q and user_key:
    with st.spinner("AI 老師正在思考..."):
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        res = model.generate_content(f"你是資深理化老師，請回答：{student_q}。開場說『各位同學好』，術語加註中文。")
        st.info(res.text)

st.divider()

# --- 5. 手搖飲教學 (含題目、男聲、進度條) ---
st.subheader("🥤 莫耳數攻略：手搖飲珍珠量法")

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
                    
                    # 老師要求的：要把題目寫進來，且用男聲引導
                    prompt = [
                        sample_file,
                        "你是有 20 年資歷的男理化老師。請根據講義第 27 頁教學。"
                        "1. 開場說：『各位同學好！我是你們的理化助教。今天老師聲音沙啞，但為了你們最愛的珍奶，我們來聊聊莫耳數...』"
                        "2. **重要**：請在內容中完整列出講義中的例題題目，並引導學生閱讀。"
                        "3. 使用『珍珠奶茶珍珠量』解釋 n = m / M。n 是杯數，m 是珍珠總重，M 是一杯珍珠的重量。"
                        "4. 英文術語後加註中文。最後提醒多喝溫水。"
                    ]
                    
                    response = model.generate_content(prompt)
                    teaching_text = response.text
                    
                    # 顯示文字內容 (讓學生可以讀題)
                    st.markdown(teaching_text)
                    
                    # 生成並播放語音 (男聲 + 進度條)
                    clean_text = teaching_text.replace('$', '').replace('*', '').replace('#', '')
                    audio_file = asyncio.run(generate_male_voice(clean_text))
                    
                    with open(audio_file, "rb") as f:
                        audio_bytes = f.read()
                    
                    st.audio(audio_bytes, format="audio/mp3")
                    st.caption("💡 點擊上方播放器右側的三個點，可以調整播放速度喔！")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"實驗失敗：{e}")
        else:
            st.error("找不到講義檔案。")

st.divider()

# --- 6. 階段性互動練習 ---
st.subheader("📝 隨堂小挑戰")
if 'quiz_step' not in st.session_state:
    st.session_state.quiz_step = 0

if st.session_state.quiz_step == 0:
    st.write("🥤 **第一題：珍珠杯數題** (打好基礎)")
    st.write("一杯珍奶的珍珠重 50g ($M$)，現在有 500g 的珍珠 ($m$)，可以裝成幾杯 ($n$)？")
    ans1 = st.text_input("你的答案：", key="a1")
    if st.button("送出解答"):
        if ans1 == "10":
            st.success("答對了！ $n = 500 / 50 = 10$ 杯。")
            st.session_state.quiz_step = 1
            st.rerun()
        else: st.error("再算算看喔！")

elif st.session_state.quiz_step == 1:
    st.write("🧪 **第二題：莫耳數實戰**")
    st.write("二氧化碳 ($CO_2$) 的分子量 ($M$) 是 44。如果你有 176g 的二氧化碳 ($m$)，是多少莫耳 ($n$)？")
    ans2 = st.text_input("你的答案：", key="a2")
    if st.button("確認結果"):
        if ans2 == "4":
            st.balloons()
            st.success("超級優秀！ $176 / 44 = 4$ 莫耳。")
            if st.button("重新練習"):
                st.session_state.quiz_step = 0
                st.rerun()