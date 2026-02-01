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
        padding: 25px;
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

# --- 2. 語音生成函數 (質感男聲：Yunxi) ---
async def generate_male_voice(text):
    # 使用 Microsoft Edge 的穩定男聲：Yunxi
    communicate = edge_tts.Communicate(text, "zh-TW-YunxiNeural", rate="-5%")
    temp_file = "output.mp3"
    await communicate.save(temp_file)
    return temp_file

# --- 3. 學生 API 通行證：還原保姆級 6 步指南 ---
st.title("🔬 理化 AI 手搖飲實驗室")

st.markdown("""
<div class="guide-container">
    <h3 style='margin-top:0;'>各位小朋友好！請跟著以下步驟取得你的 AI 通行證：</h3>
    1. 點擊連結開啟網頁：<a href="https://aistudio.google.com/app/apikey" target="_blank">👉 Google AI Studio (金鑰申請處)</a><br>
    2. 如果看到登入畫面，請用你的 <b>Google 帳號</b>登入。<br>
    3. 點擊畫面左側或中間的藍色按鈕 <b>"Create API key"</b>。<br>
    4. 選擇 <b>"Create API key in new project"</b>。<br>
    5. 看到一串像密碼的英文數字，點擊 <b>"Copy"</b> 複製起來。<br>
    6. 回到本網頁，把代碼貼在下方的輸入框中，按下 Enter 即可。
</div>
""", unsafe_allow_html=True)

user_key = st.text_input("🔑 在這裡貼上你的 API 通行證：", type="password")

if user_key:
    try:
        genai.configure(api_key=user_key)
        st.success("✅ 通行證已就緒！使用的模型：Gemini 2.5 Flash")
    except:
        st.error("⚠️ 金鑰格式錯誤，請重新複製貼上。")

st.divider()

# --- 4. 學生問問題專區 (恢復最重要功能) ---
st.subheader("💬 學生提問區：有問題直接問 AI 老師")
student_q = st.text_input("輸入你想問的理化問題：", placeholder="例如：為什麼原子量沒有單位？")

if student_q and user_key:
    with st.spinner("AI 老師正在思考答案..."):
        try:
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            prompt_q = f"你是資深男理化老師。請回答學生：'{student_q}'。1. 開場說『各位同學好』。2. 術語後加註中文。3. 解說要超級簡單。"
            res = model.generate_content(prompt_q)
            st.info(f"👨‍🏫 **老師解釋：**\n\n{res.text}")
        except Exception as e:
            st.error(f"連線出錯：{e}")

st.divider()

# --- 5. 手搖飲教學 (含題目、男聲、進度條) ---
st.subheader("🥤 莫耳數攻略：手搖飲珍珠量法")

if st.button("🚀 啟動互動教學 (含男聲講述與進度條)"):
    if not user_key:
        st.warning("請先輸入通行證。")
    else:
        file_path = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        if os.path.exists(file_path):
            with st.spinner("正在為大家翻閱講義並錄製男聲語音..."):
                try:
                    sample_file = genai.upload_file(path=file_path)
                    model = genai.GenerativeModel('models/gemini-2.5-flash')
                    
                    prompt = [
                        sample_file,
                        "你是有 20 年資歷的男理化老師。請根據講義第 27 頁教學。"
                        "1. 開場必須是：『各位同學好！歡迎來到理化教室。今天老師身體微恙，聲音有點沙啞，但為了你們最愛的珍奶，我們來聊聊莫耳數...』"
                        "2. **重要**：請在內容中完整列出講義中的例題題目，方便學生邊聽邊看。"
                        "3. 使用『珍珠奶茶珍珠量』解釋公式 n = m / M。n 杯數，m 珍珠總重，M 每杯重量。"
                        "4. 最後提醒：『老師會陪著大家學習，你們也要多喝溫水，要注意身體喔！』"
                    ]
                    
                    response = model.generate_content(prompt)
                    teaching_text = response.text
                    st.markdown(teaching_text)
                    
                    # 生成並播放語音 (男聲 + 進度條)
                    clean_text = teaching_text.replace('$', '').replace('*', '').replace('#', '')
                    audio_file = asyncio.run(generate_male_voice(clean_text))
                    
                    with open(audio_file, "rb") as f:
                        audio_bytes = f.read()
                    
                    st.audio(audio_bytes, format="audio/mp3")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"實驗失敗：{e}")
        else:
            st.error(f"找不到講義 Ph_Ch_finals.pdf，目前路徑：{file_path}")

st.divider()

# --- 6. 階段性互動練習 ---
st.subheader("📝 隨堂挑戰：你懂了嗎？")
if 'quiz_step' not in st.session_state:
    st.session_state.quiz_step = 0

if st.session_state.quiz_step == 0:
    st.write("🥤 **第一關：珍珠杯數題**")
    st.write("老師出題：一杯珍奶的珍珠重 50g ($M$)，現在有 400g 的珍珠 ($m$)，請問可以裝成幾杯 ($n$)？")
    ans1 = st.text_input("你的答案：", key="a1")
    if st.button("送出解答"):
        if ans1 == "8":
            st.success("太強了！ $n = 400 / 50 = 8$ 杯。")
            st.session_state.quiz_step = 1
            st.rerun()
        else: st.error("再算算看喔！用總量除以每杯量。")

elif st.session_state.quiz_step == 1:
    st.write("🧪 **第二關：理化魔王題**")
    st.write("老師出題：氧氣 ($O_2$) 分子量 ($M$) 是 32。如果你有 96g 的氧氣 ($m$)，是多少莫耳 ($n$)？")
    ans2 = st.text_input("你的答案：", key="a2")
    if st.button("確認結果"):
        if ans2 == "3":
            st.balloons()
            st.success("超級優秀！ $96 / 32 = 3$ 莫耳。你掌握莫耳數了！")
            if st.button("重新練習"):
                st.session_state.quiz_step = 0
                st.rerun()
        else: st.error("想想看，跟算珍奶杯數方法一模一樣喔！")