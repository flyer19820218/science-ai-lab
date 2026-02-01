import streamlit as st
import google.generativeai as genai
import os

# --- 1. 頁面配置 (維持清爽翩翩體) ---
st.set_page_config(page_title="20年理化魂：AI 互動實驗室", layout="wide")

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
    </style>
    """, unsafe_allow_html=True)

# --- 2. 學生 API 金鑰引導 ---
st.title("🔬 20年理化魂：AI 互動實驗室")
st.markdown("""
    ### 🔑 學生通行證領取處
    各位同學，請先跟著步驟領取你的「數位通行證」：
    1. 點擊 **[👉 取得自己的 Gemini API Key](https://aistudio.google.com/app/apikey)**。
    2. 點擊 "Create API key in new project" 並複製。
    3. 將代碼貼在下方輸入框，就能啟動 AI 老師囉！
""")

user_key = st.text_input("請輸入你的 API 通行證：", type="password")

if user_key:
    try:
        # 使用老師指定的最新型號
        genai.configure(api_key=user_key)
        st.success("✅ 驗證成功！實驗設備已啟動。")
    except:
        st.error("⚠️ 金鑰有誤，請檢查後重新貼上。")
else:
    st.info("💡 尚未輸入通行證，請先完成上方步驟。")

st.divider()

# --- 3. 學生提問區 ---
st.subheader("💬 理化概念快問快答")
student_q = st.text_input("對剛才上課內容有疑問嗎？直接問：", placeholder="例如：1 莫耳到底有多少個原子？")

if student_q and user_key:
    with st.spinner("AI 老師正在組織易懂的答案..."):
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            prompt_q = f"你是資深理化老師。請回答學生：'{student_q}'。要求：1. 開場說『各位同學好』。2. 術語後加註中文。3. 解說要讓國二學生也聽懂。"
            res = model.generate_content(prompt_q)
            st.info(f"👨‍🏫 **老師解釋：**\n\n{res.text}")
        except Exception as e:
            st.error(f"連線出錯：{e}")

st.divider()

# --- 4. 莫耳數魔王挑戰 ---
st.subheader("🍎 莫耳數 $n = m/M$ 攻略")
if st.button("🚀 啟動互動教學 (讀取 Ph_Ch_finals 講義)"):
    if not user_key:
        st.warning("請先輸入通行證。")
    else:
        # --- 相對路徑讀取 Ph_Ch_finals.pdf ---
        base_path = os.path.dirname(__file__)
        file_path = os.path.join(base_path, "..", "data", "Ph_Ch_finals.pdf")
        
        if os.path.exists(file_path):
            with st.spinner("老師正在為大家翻閱講義..."):
                try:
                    sample_file = genai.upload_file(path=file_path)
                    model = genai.GenerativeModel('gemini-2.0-flash')
                    
                    main_prompt = [
                        sample_file,
                        "你是有 20 年資歷的理化老師。請根據講義第 27 頁，對學生進行教學。"
                        "要求：1. 開場說：『各位同學好！今天老師身體微恙，聲音有點沙啞，但我們會一起攻克最難的莫耳數...』"
                        "2. 使用『買蘋果』的比喻解釋公式 n = m / M。"
                        "3. 所有的英文術語（如 Mole, Mass）必須加註中文。"
                        "4. 最後提醒大家：『老師雖然感冒了，但會陪著大家學習，你們也要多喝水、多休息喔！』"
                    ]
                    
                    response = model.generate_content(main_prompt)
                    st.markdown(response.text)
                    st.balloons()
                except Exception as e:
                    st.error(f"生成失敗：{e}")
        else:
            # 報錯時顯示路徑，方便老師在 GitHub Desktop 確認
            st.error(f"找不到講義 Ph_Ch_finals.pdf！目前偵測路徑：{file_path}。請確認 GitHub 上的檔案名稱大小寫完全一致。")