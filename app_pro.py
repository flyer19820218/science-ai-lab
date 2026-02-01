import streamlit as st
import google.generativeai as genai
import os
import asyncio
import edge_tts
import io
from PIL import Image

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
        border-radius: 12px;
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
    audio { width: 100%; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 穩定版男聲生成引擎 (Yunxi) ---
async def generate_voice(text):
    # 使用 Microsoft Yunxi 沉穩男聲，語速調慢 5% 更有老師感
    communicate = edge_tts.Communicate(text, "zh-TW-YunxiNeural", rate="-5%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- 3. 學生 API 通行證：保姆級 6 步教學 ---
st.title("🔬 理化 AI 手搖飲實驗室")

with st.expander("各位小朋友好！點此查看『取得通行證』詳細步驟", expanded=True):
    st.markdown("""
    <div class="guide-container">
        <b>請跟著以下步驟取得你的 AI 通行證：</b><br><br>
        1. 點擊連結開啟網頁：<a href="https://aistudio.google.com/app/apikey" target="_blank">👉 Google AI Studio (金鑰申請處)</a><br>
        2. <b>重要：請務必使用個人 Gmail 帳號登入</b> (學校帳號可能無法使用)。<br>
        3. 點擊畫面上的藍色按鈕 <b>"Create API key"</b>。<br>
        4. 選擇 <b>"Create API key in new project"</b>。<br>
        5. 看到密碼般的英文數字，點擊 <b>"Copy"</b> 複製起來。<br>
        6. 回到本網頁，把代碼貼在下方的輸入框中，按下 Enter。
    </div>
    """, unsafe_allow_html=True)

user_key = st.text_input("🔑 在這裡貼上你的 API 通行證：", type="password")

if user_key:
    try:
        genai.configure(api_key=user_key)
        st.success("✅ 通行證已就緒！使用模型：Gemini 2.5 Flash")
    except:
        st.error("⚠️ 金鑰格式錯誤，請重新複製貼上。")

st.divider()

# --- 4. 學生問問題專區 (支援拍照提問) ---
st.subheader("💬 學生提問區：拍照或打字問 AI 老師")
col_text, col_img = st.columns([1, 1])

with col_text:
    student_q = st.text_input("輸入問題：", placeholder="例如：原子量是什麼？")
with col_img:
    uploaded_image = st.file_uploader("或是拍照上傳題目：", type=["jpg", "png", "jpeg"])

if (student_q or uploaded_image) and user_key:
    with st.spinner("AI 老師正在思考答案..."):
        try:
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            prompt_parts = ["你是資深男理化老師。1.開場說『各位同學好』。2.術語加註中文。3.解說要簡單好懂。"]
            if uploaded_image:
                prompt_parts.append(Image.open(uploaded_image))
            if student_q:
                prompt_parts.append(f"問題內容：{student_q}")
                
            res = model.generate_content(prompt_parts)
            st.info(f"👨‍🏫 **老師解釋：**\n\n{res.text}")
        except Exception as e:
            if "429" in str(e):
                st.error("🚫 流量爆了！請等 1 分鐘讓 AI 老師喘口氣再問喔。")
            else: st.error(f"連線出錯：{e}")

st.divider()

# --- 5. 手搖飲教學與進度條男聲 ---
st.subheader("🥤 莫耳數攻略：珍珠奶茶計算法")

if st.button("🚀 啟動互動教學 (含男聲講述與進度條)"):
    if not user_key:
        st.warning("請先輸入通行證。")
    else:
        file_path = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        if os.path.exists(file_path):
            with st.spinner("AI 老師正在調製大杯珍奶中..."):
                try:
                    sample_file = genai.upload_file(path=file_path)
                    model = genai.GenerativeModel('models/gemini-2.5-flash')
                    
                    prompt = [
                        sample_file,
                        "你是有 20 年資歷的男理化老師。請根據講義第 27 頁教學。"
                        "1. 開場說：『各位同學好！歡迎來到理化教室。今天老師感冒聲音沙啞，但為了你們最愛的珍奶，我們來聊聊莫耳數...』"
                        "2. 完整列出講義中的例題題目內容，方便學生邊聽邊看。"
                        "3. 使用珍珠奶茶珍珠量解釋 n = m / M。n 杯數，m 珍珠總重，M 每杯重量。"
                        "4. 術語後加註中文。最後提醒多喝溫水。"
                    ]
                    
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                    
                    # 語音生成
                    clean_text = response.text.replace('$', '').replace('*', '').replace('#', '').replace('\n', ' ')
                    audio_bytes = asyncio.run(generate_voice(clean_text))
                    st.audio(audio_bytes, format="audio/mp3")
                    st.caption("💡 國三小朋友可以拉動進度條重聽，或調整播放速度。")
                    st.balloons()
                except Exception as e:
                    if "429" in str(e):
                        st.error("🚫 流量達到免費版上限！請等待 1 分鐘後再點一次。")
                    else: st.error(f"語音生成失敗：{e}")
        else:
            st.error("找不到講義 Ph_Ch_finals.pdf。")

st.divider()

# --- 6. 階段性互動練習 ---
st.subheader("📝 隨堂挑戰：你懂了嗎？")
if 'quiz_step' not in st.session_state:
    st.session_state.quiz_step = 0

if st.session_state.quiz_step == 0:
    st.write("🥤 **第一關：珍珠杯數題**")
    st.write("老師出題：一杯珍奶的珍珠重 50g ($M$)，現在店長給你 400g 的珍珠 ($m$)，可以裝成幾杯 ($n$)？")
    ans1 = st.text_input("你的答案：", key="a1")
    if st.button("送出解答"):
        if ans1 == "8":
            st.success("答對了！ $n = 400 / 50 = 8$ 杯。")
            st.session_state.quiz_step = 1
            st.rerun()
        else: st.error("再算算看喔！總量除以每杯量。")

elif st.session_state.quiz_step == 1:
    st.write("🧪 **第二關：理化魔王題**")
    st.write("二氧化碳 ($CO_2$) 的分子量 ($M$) 是 44。如果你有 88g 的二氧化碳 ($m$)，是多少莫耳 ($n$)？")
    ans2 = st.text_input("你的答案：", key="a2")
    if st.button("確認結果"):
        if ans2 == "2":
            st.balloons(); st.success("優秀！你掌握精髓了！")
            if st.button("重新練習"):
                st.session_state.quiz_step = 0; st.rerun()