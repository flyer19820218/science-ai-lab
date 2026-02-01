import streamlit as st
import google.generativeai as genai
import os

# --- 1. 頁面風格 (翩翩體與互動式樣式) ---
st.set_page_config(page_title="20年理化魂：AI 手搖飲實驗室", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="css"], .stMarkdown, p, h1, h2, h3, span, label, li {
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', 'KaiTi', sans-serif !important;
    }
    .stButton>button {
        background-color: #e3f2fd !important;
        color: #000000 !important;
        border: 1px solid #bbdefb !important;
        border-radius: 8px;
        font-weight: bold;
    }
    .tutorial-box {
        background-color: #f1f8e9;
        padding: 20px;
        border-radius: 10px;
        border: 2px dashed #8bc34a;
        margin-bottom: 20px;
    }
    </style>
    
    <script>
    function speak(text) {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel(); // 先停止之前的聲音
            const msg = new SpeechSynthesisUtterance();
            msg.text = text;
            msg.lang = 'zh-TW';
            msg.rate = 0.85; 
            window.speechSynthesis.speak(msg);
        }
    }
    </script>
    """, unsafe_allow_html=True)

# --- 2. 學生 API 通行證：保姆級教學 ---
st.title("🔬 20年理化魂：AI 手搖飲實驗室")

with st.expander("🆘 第一次來？點我查看『如何取得通行證』教學", expanded=True):
    st.markdown("""
    <div class="tutorial-box">
    <b>各位同學好！請跟著以下步驟取得你的 AI 通行證：</b><br>
    1. 點擊連結開啟網頁：<a href="https://aistudio.google.com/app/apikey" target="_blank">👉 Google AI Studio (金鑰申請處)</a><br>
    2. 如果看到登入畫面，請用你的 <b>Google 帳號</b>登入。<br>
    3. 點擊畫面左側或中間的藍色按鈕 <b>"Create API key"</b>。<br>
    4. 選擇 <b>"Create API key in new project"</b>。<br>
    5. 看到一串像密碼的英文數字，點擊 <b>"Copy"</b> 複製起來。<br>
    6. 回到本網頁，把代碼貼在下方的輸入框中。
    </div>
    """, unsafe_allow_html=True)

user_key = st.text_input("🔑 在這裡貼上你的 API 通行證：", type="password")

if user_key:
    try:
        genai.configure(api_key=user_key)
        st.success("✅ 通行證驗證成功！正在連接 Gemini 2.5 Flash 老師...")
    except:
        st.error("⚠️ 通行證好像貼錯了，請重新複製一次喔。")
else:
    st.info("💡 請先完成上方的教學步驟，貼上通行證後即可解鎖。")

st.divider()

# --- 3. 手搖飲情境教學區 (TTS 語音版) ---
st.subheader("🥤 莫耳數攻略：手搖飲珍珠量法")
if st.button("🚀 啟動互動教學 (由 Gemini 2.5 講述)"):
    if not user_key:
        st.warning("請先輸入通行證。")
    else:
        file_path = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        if os.path.exists(file_path):
            with st.spinner("AI 老師正在調製大杯珍奶..."):
                try:
                    sample_file = genai.upload_file(path=file_path)
                    model = genai.GenerativeModel('models/gemini-2.5-flash')
                    
                    prompt = [
                        sample_file,
                        "你是有 20 年資歷的理化老師。請根據講義第 27 頁教學。"
                        "1. 開場說：『各位同學好！今天老師感冒聲音沙啞，但為了你們最愛的手搖飲，我們來聊聊莫耳數...』"
                        "2. 使用『買手搖飲珍珠量』解釋公式 n = m / M。n 是杯數，m 是珍珠總重，M 是一杯珍珠的重量。"
                        "3. 所有的物理符號與英文術語必須加註中文。內容要幽默好懂。"
                        "4. 最後提醒大家：『老師會陪著大家，你們也要多喝水，不要跟老師一樣感冒喔！』"
                    ]
                    
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                    
                    # 語音按鈕
                    speech_text = response.text.replace('$', '').replace('*', '').replace('#', '')
                    st.components.v1.html(f"""
                        <button onclick="parent.speak('{speech_text}')" style="
                            background-color: #4CAF50; color: white; padding: 12px 24px; 
                            border: none; border-radius: 10px; cursor: pointer; font-size: 16px; font-weight: bold;">
                            🔊 聽 AI 老師講課 (台灣腔)
                        </button>
                    """, height=70)
                    st.balloons()
                except Exception as e:
                    st.error(f"生成失敗：{e}")
        else:
            st.error("找不到講義 Ph_Ch_finals.pdf，請確認檔案位置。")

st.divider()

# --- 4. 階段性互動練習 ---
st.subheader("📝 隨堂小測驗：你懂了嗎？")
if 'step' not in st.session_state:
    st.session_state.step = 0

if st.session_state.step == 0:
    st.info("🥤 第一關：珍奶基礎題")
    st.write("老師出題：一杯珍奶的珍珠重 50g ($M$)，你現在買了 300g 的珍珠 ($m$)，請問總共可以裝成幾杯珍奶 ($n$)？")
    ans1 = st.text_input("你的答案：", key="q1")
    if st.button("送出珍奶解答"):
        if ans1 == "6":
            st.success("太厲害了！ $n = 300 / 50 = 6$ 杯。概念完全正確！")
            st.session_state.step = 1
            st.rerun()
        else:
            st.error("再算算看，用『總重量』除以『每一杯的重量』喔！")

elif st.session_state.step == 1:
    st.info("🧪 第二關：化學實戰題")
    st.write("老師出題：氧氣的分子量 ($M$) 是 32。如果你現在有 64g 的氧氣 ($m$)，請問這有多少莫耳 ($n$)？")
    ans2 = st.text_input("你的答案：", key="q2")
    if st.button("送出化學解答"):
        if ans2 == "2":
            st.balloons()
            st.success("超級優秀！ $64 / 32 = 2$ 莫耳。你已經學會莫耳數的精髓了！")
            if st.button("重新練習"):
                st.session_state.step = 0
                st.rerun()
        else:
            st.error("想想看，跟剛才算珍奶杯數的方法一模一樣喔！")