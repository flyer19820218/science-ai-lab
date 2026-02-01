import streamlit as st
import google.generativeai as genai
import os

# --- 1. 頁面配置 (RWD 自適應優化) ---
st.set_page_config(page_title="理化 AI 手搖飲實驗室", layout="wide")

st.markdown("""
    <style>
    /* 1. 基礎字體與顏色 */
    html, body, [class*="css"], .stMarkdown, p, h1, h2, h3, span, label, li {
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', 'KaiTi', sans-serif !important;
    }

    /* 2. 響應式容器優化：在手機上自動調整間距 */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem 1rem !important;
        }
        .guide-container {
            padding: 15px !important;
        }
        h1 { font-size: 1.8rem !important; }
        h3 { font-size: 1.2rem !important; }
    }

    /* 3. 保姆級指南框 */
    .guide-container {
        background-color: #f1f8e9;
        padding: 25px;
        border-radius: 15px;
        border: 2px dashed #8bc34a;
        margin-bottom: 20px;
    }

    /* 4. 手機版按鈕加強 */
    .stButton>button {
        background-color: #e3f2fd !important;
        color: #000000 !important;
        border: 1px solid #bbdefb !important;
        border-radius: 8px;
        font-weight: bold;
        width: 100%; /* 在小螢幕上按鈕自動撐滿，好點擊 */
    }
    </style>
    
    <script>
    function speak(text) {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
            const msg = new SpeechSynthesisUtterance();
            msg.text = text;
            msg.lang = 'zh-TW';
            msg.rate = 0.9; 
            window.speechSynthesis.speak(msg);
        }
    }
    </script>
    """, unsafe_allow_html=True)

# --- 2. 學生 API 通行證：保姆級 6 步教學 ---
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
        st.success("✅ 通行證驗證成功！正在啟動 Gemini 2.5 Flash 老師...")
    except:
        st.error("⚠️ 通行證格式有誤，請回 Google AI Studio 重新複製。")
else:
    st.info("💡 學生請先完成上方的 6 個步驟取得通行證。")

st.divider()

# --- 3. 手搖飲情境教學 ---
st.subheader("🥤 莫耳數攻略：珍珠奶茶計算法")
if st.button("🚀 啟動互動教學"):
    if not user_key:
        st.warning("請先輸入通行證。")
    else:
        base_path = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        if os.path.exists(base_path):
            with st.spinner("AI 老師正在調製大杯珍奶中..."):
                try:
                    sample_file = genai.upload_file(path=base_path)
                    model = genai.GenerativeModel('models/gemini-2.5-flash')
                    
                    prompt = [
                        sample_file,
                        "你是資深的理化老師。請根據講義第 27 頁對國二學生教學。"
                        "1. 開場說：『各位同學好！歡迎來到手搖飲實驗室。今天老師聲音沙啞，但為了你們最愛的珍奶，我們來聊聊莫耳數...』"
                        "2. 使用『珍珠奶茶的珍珠量』解釋公式 n = m / M。n 是杯數，m 是珍珠總重，M 是一杯珍珠的重量。"
                        "3. 物理符號與英文術語必須加註中文。內容要幽默好懂。"
                        "4. 最後提醒：『老師會一直陪著大家，你們也要注意身體，不要跟老師一樣感冒囉！』"
                    ]
                    
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                    
                    # 語音按鈕
                    speech_text = response.text.replace('$', '').replace('*', '').replace('#', '')
                    st.components.v1.html(f"""
                        <div style="text-align: center;">
                            <button onclick="parent.speak('{speech_text}')" style="
                                background-color: #4CAF50; color: white; padding: 15px 30px; 
                                border: none; border-radius: 10px; cursor: pointer; font-size: 18px; font-weight: bold; width: 80%;">
                                🔊 點我聽 AI 老師講課
                            </button>
                        </div>
                    """, height=80)
                    st.balloons()
                except Exception as e:
                    st.error(f"生成失敗：{e}")
        else:
            st.error("找不到講義 Ph_Ch_finals.pdf。")

st.divider()

# --- 4. 階段性互動練習 ---
st.subheader("📝 隨堂挑戰：你懂了嗎？")
if 'quiz_step' not in st.session_state:
    st.session_state.quiz_step = 0

# 使用容器讓內容更整齊
with st.container():
    if st.session_state.quiz_step == 0:
        st.write("🥤 **第一關：珍珠杯數題**")
        st.write("老師出題：一杯珍奶的珍珠重 50g ($M$)，你現在買了 300g 的珍珠 ($m$)，請問總共可以裝成幾杯珍奶 ($n$)？")
        ans1 = st.text_input("你的答案：", key="a1")
        if st.button("送出解答"):
            if ans1 == "6":
                st.success("太強了！ $n = 300 / 50 = 6$ 杯。")
                st.session_state.quiz_step = 1
                st.rerun()
            else: st.error("再算算看，用『總重量』除以『每一杯的重量』喔！")

    elif st.session_state.quiz_step == 1:
        st.write("🧪 **第二關：理化魔王題**")
        st.write("老師出題：氧氣 ($O_2$) 的分子量 ($M$) 是 32。如果你現在有 96g 的氧氣 ($m$)，請問這有多少莫耳 ($n$)？")
        ans2 = st.text_input("你的答案：", key="a2")
        if st.button("確認挑戰結果"):
            if ans2 == "3":
                st.balloons()
                st.success("超級優秀！ $96 / 32 = 3$ 莫耳。你已經完全掌握了！")
                if st.button("重新挑戰"):
                    st.session_state.quiz_step = 0
                    st.rerun()
            else: st.error("想想看，跟算珍奶杯數的方法完全一樣喔！")