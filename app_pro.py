import streamlit as st
import google.generativeai as genai
import os

# --- 1. 頁面配置 (翩翩體與清爽風格) ---
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
    .practice-box {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #2196f3;
    }
    </style>
    
    <script>
    function speak(text) {
        const msg = new SpeechSynthesisUtterance();
        msg.text = text;
        msg.lang = 'zh-TW';
        msg.rate = 0.9; // 稍微慢一點，像老師上課
        window.speechSynthesis.speak(msg);
    }
    </script>
    """, unsafe_allow_html=True)

# --- 2. 學生通行證 ---
st.title("🔬 20年理化魂：AI 手搖飲實驗室")
st.markdown("### 🔑 學生通行證：[👉 點此領取金鑰](https://aistudio.google.com/app/apikey)")

user_key = st.text_input("貼上你的 API 通行證：", type="password")

if user_key:
    genai.configure(api_key=user_key)
    st.success("✅ 實驗設備已啟動！")
else:
    st.info("💡 請先輸入金鑰。")

st.divider()

# --- 3. 手搖飲情境教學區 ---
st.subheader("🍎 莫耳數魔王：手搖飲攻略法")
if st.button("🚀 聽老師講『手搖飲與莫耳數』"):
    if not user_key:
        st.warning("請先輸入金鑰。")
    else:
        file_path = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        if os.path.exists(file_path):
            with st.spinner("AI 老師正在準備珍珠奶茶..."):
                try:
                    sample_file = genai.upload_file(path=file_path)
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    
                    # 老師要求的：手搖飲情境 + 溫暖開場
                    main_prompt = [
                        sample_file,
                        "你是有 20 年資歷的理化老師。請根據講義第 27 頁教學。"
                        "要求：1. 開場說：『各位同學好！今天老師感冒聲音沙啞，但為了你們想喝的手搖飲，我們來聊聊莫耳數...』"
                        "2. 使用『買手搖飲珍珠量』的比喻解釋 n = m / M。n 是杯數，m 是珍珠總重量，M 是一杯珍珠的重量。"
                        "3. 所有的英文術語必須加註中文。內容要幽默好懂。"
                        "4. 最後提醒大家：『老師會陪著大家學習，你們也要注意身體喔！』"
                    ]
                    
                    response = model.generate_content(main_prompt)
                    st.session_state['teaching_content'] = response.text
                    st.markdown(response.text)
                    
                    # 語音按鈕 (使用 JS)
                    text_for_speech = response.text.replace('$', '').replace('*', '')
                    st.components.v1.html(f"""
                        <button onclick="parent.speak('{text_for_speech}')" style="
                            background-color: #4CAF50; color: white; padding: 10px 20px; 
                            border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">
                            🔊 聽 AI 老師唸給你聽
                        </button>
                    """, height=50)
                    st.balloons()
                except Exception as e:
                    st.error(f"生成失敗：{e}")
        else:
            st.error("找不到講義 Ph_Ch_finals.pdf。")

st.divider()

# --- 4. 階段性引導練習區 ---
st.subheader("📝 互動練習：看看你懂了嗎？")
if 'step' not in st.session_state:
    st.session_state.step = 0

if st.session_state.step == 0:
    st.write("老師出題：如果一杯大杯珍奶的珍珠重 50g (M)，現在桌上有 200g 的珍珠 (m)，請問可以裝幾杯 (n)？")
    ans = st.text_input("請輸入你的答案（純數字）：")
    if st.button("送出答案"):
        if ans == "4":
            st.success("太強了！答對了。公式就是 n = 200 / 50 = 4 杯。")
            st.session_state.step = 1
            st.rerun()
        else:
            st.error("再想想看，總重量除以每一杯的重量喔！")

elif st.session_state.step == 1:
    st.markdown("""
        <div class="practice-box">
        🎉 <b>進階挑戰！</b><br>
        現在有一瓶水的分子量 (M) 是 18，如果老師手上有 36g 的水 (m)，請問這瓶水有多少莫耳 (n)？
        </div>
    """, unsafe_allow_html=True)
    ans2 = st.text_input("請輸入你的答案：")
    if st.button("確認挑戰結果"):
        if ans2 == "2":
            st.balloons()
            st.success("沒錯！36 / 18 = 2 莫耳。你已經掌握莫耳數的精髓了！")
            if st.button("重頭練習"):
                st.session_state.step = 0
                st.rerun()
        else:
            st.error("想想看，手搖飲的杯數怎麼算，莫耳數就怎麼算！")