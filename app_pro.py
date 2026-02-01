import streamlit as st
import google.generativeai as genai
import os

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

# --- 2. 學生 API 通行證指南 ---
st.title("🔬 理化 AI 手搖飲實驗室")

with st.container():
    st.markdown("""
    <div class="guide-container">
        <h3 style='margin-top:0;'>各位小朋友好！請跟著以下步驟取得你的 AI 通行證：</h3>
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
        st.success("✅ 通行證驗證成功！")
    except:
        st.error("⚠️ 通 honey 證格式錯誤。")
else:
    st.info("💡 學生請先依照上方 6 個步驟取得通行證喔。")

st.divider()

# --- 3. 學生問問題專區 ---
st.subheader("💬 學生提問區")
student_q = st.text_input("輸入你想問的理化問題：", placeholder="例如：什麼是原子量？")

if student_q and user_key:
    with st.spinner("AI 老師正在思考答案..."):
        try:
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            prompt_q = f"你是資深的理化老師。請回答學生：'{student_q}'。1. 開場說『各位同學好』。2. 術語後加註中文。3. 解說要超級簡單。"
            res = model.generate_content(prompt_q)
            st.info(f"👨‍🏫 **老師解釋：**\n\n{res.text}")
        except Exception as e:
            st.error(f"連線出錯：{e}")

st.divider()

# --- 4. 手搖飲情境教學 (平版語音強化版) ---
st.subheader("🥤 莫耳數攻略：珍珠奶茶計算法")
if st.button("🚀 啟動互動教學"):
    if not user_key:
        st.warning("請先輸入通行證。")
    else:
        file_path = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        if os.path.exists(file_path):
            with st.spinner("老師正在翻閱講義..."):
                try:
                    sample_file = genai.upload_file(path=file_path)
                    model = genai.GenerativeModel('models/gemini-2.5-flash')
                    prompt = [
                        sample_file,
                        "你是資深的理化老師。請根據講義第 27 頁教學。1. 開場說：『各位同學好！今天老師聲音沙啞，但我們要來聊聊莫耳數...』"
                        "2. 使用『手搖飲珍珠量』解釋 n = m / M。3. 術語加註中文。4. 最後提醒大家多喝溫水。"
                    ]
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                    
                    # --- 平版專用語音按鈕組件 ---
                    # 清理 LaTeX 和 Markdown 標籤，避免 AI 唸出亂碼
                    clean_text = response.text.replace('$', '').replace('*', '').replace('#', '').replace('\n', ' ')
                    
                    st.components.v1.html(f"""
                        <div style="text-align: center; margin-top: 20px;">
                            <button id="speakBtn" style="
                                background-color: #4CAF50; color: white; padding: 18px; 
                                border: none; border-radius: 12px; cursor: pointer; font-size: 20px; width: 90%; font-weight: bold;
                                box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                                🔊 點我聽 AI 老師講課
                            </button>
                        </div>
                        <script>
                        const btn = document.getElementById('speakBtn');
                        btn.addEventListener('click', () => {{
                            if ('speechSynthesis' in window) {{
                                window.speechSynthesis.cancel(); // 停止之前的
                                const msg = new SpeechSynthesisUtterance("{clean_text}");
                                msg.lang = 'zh-TW';
                                msg.rate = 0.9;
                                window.speechSynthesis.speak(msg);
                                
                                // iOS 補償機制：如果沒聲音，嘗試 resume
                                window.speechSynthesis.resume();
                            }} else {{
                                alert("你的平版不支援語音功能喔！");
                            }}
                        }});
                        </script>
                    """, height=100)
                    st.balloons()
                except Exception as e:
                    st.error(f"生成失敗：{e}")
        else:
            st.error("找不到講義檔案。")

st.divider()

# --- 5. 階段性互動練習 ---
st.subheader("📝 隨堂挑戰")
if 'quiz_step' not in st.session_state:
    st.session_state.quiz_step = 0

if st.session_state.quiz_step == 0:
    st.write("🥤 **第一關：珍珠杯數題**")
    st.write("老師出題：一杯珍奶的珍珠重 50g ($M$)，你買了 400g 的珍珠 ($m$)，可以裝成幾杯 ($n$)？")
    ans1 = st.text_input("答案：", key="a1")
    if st.button("送出解答"):
        if ans1 == "8":
            st.success("答對了！")
            st.session_state.quiz_step = 1
            st.rerun()
        else: st.error("再算算看！")

elif st.session_state.quiz_step == 1:
    st.write("🧪 **第二關：理化魔王題**")
    st.write("老師出題：氧氣 ($O_2$) 分子量 ($M$) 是 32。如果有 64g 的氧氣 ($m$)，是多少莫耳 ($n$)？")
    ans2 = st.text_input("答案：", key="a2")
    if st.button("確認結果"):
        if ans2 == "2":
            st.balloons()
            st.success("優秀！")
            if st.button("重新練習"):
                st.session_state.quiz_step = 0
                st.rerun()