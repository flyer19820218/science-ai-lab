import streamlit as st
import google.generativeai as genai
import os

# --- 1. 頁面風格 (翩翩體與清爽風格) ---
st.set_page_config(page_title="20年理化魂：AI 手搖飲實驗室", layout="wide")

st.markdown("""
    <style>
    /* 強制字體與黑字 */
    html, body, [class*="css"], .stMarkdown, p, h1, h2, h3, span, label, li {
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', 'KaiTi', sans-serif !important;
    }
    /* 您最愛的淡藍色按鈕 */
    .stButton>button {
        background-color: #e3f2fd !important;
        color: #000000 !important;
        border: 1px solid #bbdefb !important;
        border-radius: 8px;
        font-weight: bold;
    }
    /* 修正亂碼：使用乾淨的背景盒 */
    .guide-box {
        background-color: #f1f8e9;
        padding: 20px;
        border-radius: 12px;
        border: 2px dashed #8bc34a;
        margin: 10px 0;
    }
    </style>
    
    <script>
    function speak(text) {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel(); 
            const msg = new SpeechSynthesisUtterance();
            msg.text = text;
            msg.lang = 'zh-TW';
            msg.rate = 0.85; 
            window.speechSynthesis.speak(msg);
        }
    }
    </script>
    """, unsafe_allow_html=True)

# --- 2. 學生 API 通行證：保姆級教學 (解決亂碼問題) ---
st.title("🔬 20年理化魂：AI 手搖飲實驗室")

st.subheader("🔑 學生領取「數位通行證」教學")
st.markdown(f"""
    <div class="guide-box">
        <b>各位同學好！請依照這三個步驟開啟你的 AI 助教：</b><br><br>
        1. 點擊開啟：<a href="https://aistudio.google.com/app/apikey" target="_blank">👉 Google AI Studio (領取金鑰)</a><br>
        2. 點擊藍色按鈕 <b>"Create API key in new project"</b> 並複製那串代碼。<br>
        3. 將代碼貼在下方的輸入框中，按下 Enter 即可。
    </div>
""", unsafe_allow_html=True)

user_key = st.text_input("在這裡貼上你的 API 通行證：", type="password")

if user_key:
    try:
        # 使用老師指定的最新型號 2.5
        genai.configure(api_key=user_key)
        st.success("✅ 通行證驗證成功！正在啟動 Gemini 2.5 Flash 老師...")
    except:
        st.error("⚠️ 通行證有誤，請確認是否完整複製。")
else:
    st.info("💡 請先完成上方教學取得金鑰。")

st.divider()

# --- 3. 手搖飲情境教學 (由 Gemini 2.5 講述) ---
st.subheader("🥤 莫耳數攻略：珍珠奶茶計算法")
if st.button("🚀 啟動互動教學 (讀取 Ph_Ch_finals 講義)"):
    if not user_key:
        st.warning("請先輸入通行證。")
    else:
        # 雲端路徑精準修正 (相對路徑 + 大小寫)
        base_path = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        
        if os.path.exists(base_path):
            with st.spinner("AI 老師正在調製珍奶中..."):
                try:
                    sample_file = genai.upload_file(path=base_path)
                    model = genai.GenerativeModel('models/gemini-2.5-flash')
                    
                    prompt = [
                        sample_file,
                        "你是有 20 年資歷的理化老師。請根據講義第 27 頁對國二學生教學。"
                        "1. 開場說：『各位同學好！今天老師身體微恙，但為了你們最愛的手搖飲，我們來聊聊莫耳數...』"
                        "2. 使用『珍珠奶茶的珍珠量』解釋公式 n = m / M。n 是杯數，m 是珍珠總重，M 是一杯珍珠的重量。"
                        "3. 所有的物理符號與英文術語必須加註中文。內容要幽默、貼近學生生活。"
                        "4. 最後提醒：『老師會陪著大家，你們也要多喝溫水，要注意身體喔！』"
                    ]
                    
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                    
                    # 語音按鈕
                    speech_text = response.text.replace('$', '').replace('*', '').replace('#', '')
                    st.components.v1.html(f"""
                        <button onclick="parent.speak('{speech_text}')" style="
                            background-color: #4CAF50; color: white; padding: 12px 24px; 
                            border: none; border-radius: 10px; cursor: pointer; font-size: 16px; font-weight: bold;">
                            🔊 聽 AI 老師講課 (自然語音)
                        </button>
                    """, height=70)
                    st.balloons()
                except Exception as e:
                    st.error(f"生成失敗：{e}")
        else:
            st.error(f"找不到講義檔案！目前路徑：{base_path}")

st.divider()

# --- 4. 階段性引導練習 ---
st.subheader("📝 隨堂挑戰：看看你懂了嗎？")
if 'quiz_step' not in st.session_state:
    st.session_state.quiz_step = 0

if st.session_state.quiz_step == 0:
    st.info("🥤 第一關：珍珠杯數題")
    st.write("老師出題：一杯大杯珍奶的珍珠重 50g ($M$)，現在店長給了你 350g 的珍珠 ($m$)，請問總共可以裝成幾杯珍奶 ($n$)？")
    ans1 = st.text_input("你的答案：", key="a1")
    if st.button("送出珍奶解答"):
        if ans1 == "7":
            st.success("太強了！ $n = 350 / 50 = 7$ 杯。概念完全正確！")
            st.session_state.quiz_step = 1
            st.rerun()
        else: st.error("再算算看，『總重量』除以『每一杯的重量』喔！")

elif st.session_state.quiz_step == 1:
    st.info("🧪 第二關：理化魔王題")
    st.write("老師出題：二氧化碳 (CO₂) 的分子量 ($M$) 是 44。如果你現在有 88g 的二氧化碳 ($m$)，請問這有多少莫耳 ($n$)？")
    ans2 = st.text_input("你的答案：", key="a2")
    if st.button("送出理化解答"):
        if ans2 == "2":
            st.balloons()
            st.success("超級優秀！ $88 / 44 = 2$ 莫耳。你已經學會莫耳數的精髓了！")
            if st.button("重新練習"):
                st.session_state.quiz_step = 0
                st.rerun()
        else: st.error("想想看，跟剛才算珍奶杯數的方法一模一樣喔！")