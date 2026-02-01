import streamlit as st
import google.generativeai as genai
import os

# --- 1. 頁面配置 (維持老師最愛的風格) ---
st.set_page_config(page_title="理化 AI 互動實驗室", layout="wide")

# 強制黑字與翩翩體
st.markdown("""
    <style>
    html, body, [class*="css"], .stMarkdown, p, h1, h2, h3, span, label, li {
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', 'KaiTi', sans-serif !important;
    }
    /* 您喜歡的淡藍色按鈕 */
    .stButton>button {
        background-color: #e3f2fd !important;
        color: #000000 !important;
        border: 1px solid #bbdefb !important;
        border-radius: 8px;
        font-weight: bold;
    }
    /* 輸入框樣式 */
    .stTextInput input {
        background-color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 頁面標題與金鑰輸入 (每人填自己的) ---
st.title("🔬 AI 互動實驗室")

# 將金鑰輸入放在顯眼的最上方
user_key = st.text_input("🔑 請輸入您的 Gemini API Key 以啟動系統：", type="password", help="每位使用者請輸入自己的金鑰，系統不會儲存您的資訊。")

if user_key:
    try:
        genai.configure(api_key=user_key)
        st.success("✅ 金鑰驗證成功！老師，準備好開始上課了嗎？")
    except Exception as e:
        st.error(f"⚠️ 金鑰似乎有點問題，請檢查後重新輸入。")
else:
    st.info("💡 尚未偵測到金鑰。請在上方輸入框貼上您的 API Key 以解鎖 AI 助教功能。")

st.divider()

# --- 3. 學生提問區 (中文加註) ---
st.subheader("💬 學生提問區")
st.write("這是一個適合程度不一學生的互動空間，AI 會自動為英文術語加上中文註解。")

student_q = st.text_input("學生問：", placeholder="例如：什麼是分子量？", key="input_q")

if student_q:
    if not user_key:
        st.warning("請先在上方輸入金鑰，AI 老師才能回答喔！")
    else:
        with st.spinner("AI 老師正在組織易懂的中文解釋..."):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                # 強化 Prompt：術語加註中文
                prompt_q = f"你是資深理化老師。請回答學生問題：'{student_q}'。要求：1. 語氣溫暖。2. 術語後方必須括號標註中文註解。3. 內容要讓程度不好的學生也能聽懂。"
                res = model.generate_content(prompt_q)
                st.info(f"👨‍🏫 **老師解釋：**\n\n{res.text}")
            except Exception as e:
                st.error(f"連線出現小意外：{e}")

st.divider()

# --- 4. 備課教材生成 (買蘋果比喻) ---
st.subheader("🍎 莫耳數「買蘋果」教學導讀")
if st.button("🚀 讀取講義並生成教學導讀"):
    if not user_key:
        st.warning("請先輸入金鑰再進行備課。")
    else:
        # 使用 Mac Mini M2 的正確路徑
        file_path = "/Users/luyenchun/Documents/GitHub/Science-AI-Tutor/data/ph_ch_finals.pdf"
        
        if os.path.exists(file_path):
            with st.spinner("正在為您精心研讀講義..."):
                try:
                    sample_file = genai.upload_file(path=file_path)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    main_prompt = [
                        sample_file,
                        "你是有 20 年資歷的理化老師。請根據講義第 27 頁，用『買蘋果』解釋莫耳數公式 n = m / M。"
                        "要求：1. 全文繁體中文。2. 所有的物理/化學符號與英文術語必須附上中文解釋。"
                        "3. 內容要非常簡單。4. 最後給感冒中的老師一句暖心的關懷。"
                    ]
                    
                    response = model.generate_content(main_prompt)
                    st.markdown(response.text)
                    st.balloons()
                except Exception as e:
                    st.error(f"備課失敗，請確認檔案與金鑰權限：{e}")
        else:
            st.error(f"找不到 PDF 檔案，請檢查路徑：{file_path}")