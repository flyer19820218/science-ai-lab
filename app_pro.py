import streamlit as st
import google.generativeai as genai
import os

# --- 1. 頁面配置 (維持老師喜愛的清爽翩翩體) ---
st.set_page_config(page_title="理化 AI 互動實驗室", layout="wide")

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

# --- 2. 手動金鑰輸入 ---
st.title("🔬 20年理化魂：AI 互動實驗室")
user_key = st.text_input("🔑 請輸入您的 Gemini API Key：", type="password")

if user_key:
    genai.configure(api_key=user_key)
else:
    st.info("💡 請先輸入金鑰以啟動系統。")

st.divider()

# --- 3. 學生提問區 ---
st.subheader("💬 學生提問區")
student_q = st.text_input("學生問：", placeholder="例如：什麼是分子量？")

if student_q and user_key:
    with st.spinner("AI 老師正在思考中文解釋..."):
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt_q = f"你是理化老師。請回答學生：'{student_q}'。要求：1. 語氣溫暖。2. 術語後加註中文。3. 解說極其簡單。"
            res = model.generate_content(prompt_q)
            st.info(f"👨‍🏫 **老師解釋：**\n\n{res.text}")
        except Exception as e:
            st.error(f"連線出錯：{e}")

st.divider()

# --- 4. 備課教材生成 (修正路徑 Bug) ---
st.subheader("🍎 莫耳數「買蘋果」教學導讀")
if st.button("🚀 讀取講義並生成教學導讀"):
    if not user_key:
        st.warning("請先輸入金鑰。")
    else:
        # --- 核心修正：自動偵測檔案位置 ---
        # 抓取目前程式碼所在的路徑，再往上找 data 資料夾
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 雲端路徑修正：通常 data 會在 src 的上一層或同一層
        file_path = os.path.join(current_dir, "..", "data", "ph_ch_finals.pdf")
        
        # 如果找不到，再試試看同級路徑 (適應不同的部署結構)
        if not os.path.exists(file_path):
            file_path = os.path.join(current_dir, "data", "ph_ch_finals.pdf")

        if os.path.exists(file_path):
            with st.spinner("正在為您研讀講義..."):
                try:
                    sample_file = genai.upload_file(path=file_path)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    main_prompt = [
                        sample_file,
                        "你是有 20 年資歷的理化老師。請根據講義第 27 頁，用『買蘋果』解釋 n = m / M。"
                        "要求：1. 全文繁中。 2. 物理符號與英文術語必須加註中文。 3. 最後給感冒中的老師一句暖心的鼓勵。"
                    ]
                    response = model.generate_content(main_prompt)
                    st.markdown(response.text)
                    st.balloons()
                except Exception as e:
                    st.error(f"生成失敗：{e}")
        else:
            # 這裡顯示相對路徑，方便除錯
            st.error(f"找不到檔案！偵測路徑為：{file_path}\n請確認 data 資料夾已上傳至 GitHub。")