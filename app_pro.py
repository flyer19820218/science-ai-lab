import streamlit as st
import google.generativeai as genai
import os

# --- 1. 頁面配置 (維持老師最愛的風格) ---
st.set_page_config(page_title="理化魂：AI 互動實驗室", layout="wide")

# 強制黑字與翩翩體
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
    ### 🔑 學生登入區
    各位同學，在使用 AI 助教前，請先取得你自己的「數位通行證」：
    1. 點擊 **[取得 Gemini API Key](https://aistudio.google.com/app/apikey)** (需登入 Google 帳號)。
    2. 點擊 "Create API key in new project"。
    3. 將那一串代碼貼在下方輸入框。
""")

user_key = st.text_input("貼上你的 API Key：", type="password")

if user_key:
    try:
        genai.configure(api_key=user_key)
        st.success("✅ 驗證成功！實驗室設備已啟動。")
    except:
        st.error("⚠️ 金鑰無效，請重新檢查。")
else:
    st.info("💡 尚未偵測到金鑰，請先完成上方步驟。")

st.divider()

# --- 3. 學生提問區 (中文加註) ---
st.subheader("💬 理化問題快問快答")
student_q = st.text_input("有什麼不懂的概念？直接問老師：", placeholder="例如：為什麼原子量沒有單位？")

if student_q and user_key:
    with st.spinner("AI 老師正在組織易懂的答案..."):
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt_q = f"你是資深理化老師。請回答學生問題：'{student_q}'。要求：1. 開場要說『各位同學好』。2. 術語後方必須括號標註中文註解。3. 舉例要生活化。"
            res = model.generate_content(prompt_q)
            st.info(f"👨‍🏫 **AI 老師回覆：**\n\n{res.text}")
        except Exception as e:
            st.error(f"連線出錯：{e}")

st.divider()

# --- 4. 莫耳數魔王挑戰 (買蘋果比喻) ---
st.subheader("🍎 莫耳數 $n = m/M$ 攻略")
if st.button("🚀 啟動互動教學 (讀取 Ph_Ch_finals.pdf)"):
    if not user_key:
        st.warning("請先輸入金鑰。")
    else:
        # 相對路徑讀取 Ph_Ch_finals.pdf
        base_path = os.path.dirname(__file__)
        file_path = os.path.join(base_path, "..", "data", "Ph_Ch_finals.pdf")
        
        if os.path.exists(file_path):
            with st.spinner("AI 老師正在翻閱講義..."):
                try:
                    sample_file = genai.upload_file(path=file_path)
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    
                    # 針對學生的最終 Prompt
                    main_prompt = [
                        sample_file,
                        "你是有 20 年資歷的理化老師。請根據講義第 27 頁，對學生進行教學。"
                        "要求：1. 開場必須是：『各位同學好，歡迎來到理化教室！今天老師聲音有點沙啞，但我們要來攻克最難的莫耳數...』"
                        "2. 使用『買蘋果』的比喻解釋公式 n = m / M。"
                        "3. 所有的英文術語（如 Mole, Mass）必須加註中文。"
                        "4. 內容要幽默好懂，適合國二學生。"
                        "5. 最後要提醒學生：『老師雖然感冒了，但還是會陪著大家一起學習，大家也要注意身體喔！』"
                    ]
                    
                    response = model.generate_content(main_prompt)
                    st.markdown(response.text)
                    st.balloons()
                except Exception as e:
                    st.error(f"生成失敗：{e}")
        else:
            st.error(f"找不到講義 Ph_Ch_finals.pdf，請確認檔案已上傳至 data 資料夾。")