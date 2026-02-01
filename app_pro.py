import streamlit as st
import google.generativeai as genai
import os
import asyncio
import edge_tts
import re
from PIL import Image

# --- 1. 頁面配置 (全黑文字、翩翩體) ---
st.set_page_config(page_title="理化 AI 手搖飲實驗室", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="css"], .stMarkdown, p, h1, h2, h3, span, label, li {
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', 'KaiTi', sans-serif !important;
    }
    .guide-box {
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
        height: 50px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 穩定版語音引擎 (Yunxi 男聲) ---
async def save_voice(text, filename="speech.mp3"):
    # 移除 LaTeX 符號避免 AI 唸出亂碼
    clean_text = re.sub(r'\$+', '', text)
    clean_text = clean_text.replace('*', '').replace('#', '').replace('\n', ' ')
    communicate = edge_tts.Communicate(clean_text, "zh-TW-YunxiNeural", rate="-5%")
    await communicate.save(filename)

# --- 3. 學生快速指南 (打勾兩次版) ---
st.title("🔬 理化 AI 手搖飲實驗室")

st.markdown("""
<div class="guide-box">
    <b>各位同學好！請快速取得你的 AI 通行證：</b><br><br>
    步驟 1：開啟 <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a> 並登入。<br>
    步驟 2：點擊 <b>Create API key</b>，<b>勾選兩次同意條款</b>後按產生。<br>
    步驟 3：複製金鑰，回到這裡貼上按 Enter。
</div>
""", unsafe_allow_html=True)

user_key = st.text_input("🔑 通行證貼在這裡：", type="password")

if user_key:
    try:
        genai.configure(api_key=user_key)
        st.success("✅ 通行證驗證成功！")
    except:
        st.error("金鑰有誤，請檢查。")

st.divider()

# --- 4. 學生問答區 ---
st.subheader("💬 學生提問區：拍照或打字問問題")
col_q, col_up = st.columns([1, 1])
with col_q:
    student_q = st.text_input("輸入問題：")
with col_up:
    uploaded_image = st.file_uploader("📷 拍照上傳題目：", type=["jpg", "png", "jpeg"])

if (student_q or uploaded_image) and user_key:
    with st.spinner("👨‍🏫 AI 老師正在思考答案..."):
        try:
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            prompt = ["資深男理化老師。化學式如 $$H_2O, CO_2$$ 與公式必須嚴格使用 LaTeX 格式。"]
            parts = prompt + ([Image.open(uploaded_image)] if uploaded_image else []) + ([f"問題：{student_q}"] if student_q else [])
            res = model.generate_content(parts)
            st.info(f"👨‍🏫 老師解釋：\n\n{res.text}")
        except Exception as e:
            st.error(f"連線失敗：{e}")

st.divider()

# --- 5. 講義單元隨選 (完全對齊 PDF 單元名稱) ---
st.subheader("🥤 自主學習區：翻開你的理化密笈")

unit_map = {
    "序章：禁忌的儀式與因果的變律 (p.1-2)": 1,
    "1-1：測量與天平的平衡律 (p.3)": 3,
    "1-2：煉金基礎：物質的密度 (p.4)": 4,
    "1-3：煉金呼吸：氮、氧、二氧化碳 (p.5)": 5,
    "2-1：波動的低語與聲速律法 (p.11)": 11,
    "3-2：折射定律與透鏡成像奧義 (p.18)": 18,
    "6-1：質量守恆與莫耳數計數 (p.27)": 27,
    "7-1：解離說與 pH 值的契約 (p.31)": 31,
    "8-2：酯化反應與聚合物之魂 (p.37)": 37,
    "9-3：大氣壓力與浮力秘術 (p.46)": 46,
    "末章：直流電動機與旋轉輪迴 (p.71)": 71
}

selected_unit = st.selectbox("📖 請選擇單元：", list(unit_map.keys()))
target_page = unit_map[selected_unit]

if st.button(f"🚀 啟動【{selected_unit}】教學"):
    if not user_key:
        st.warning("請先輸入通行證。")
    else:
        file_path = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        if os.path.exists(file_path):
            with st.spinner(f"正在翻閱第 {target_page} 頁並調製大杯珍奶..."):
                try:
                    sample_file = genai.upload_file(path=file_path)
                    model = genai.GenerativeModel('models/gemini-2.5-flash')
                    
                    # 提示詞下死命令
                    prompt_text = [
                        sample_file,
                        f"你是有 20 年資歷的男理化老師。請針對講義第 {target_page} 頁教學。"
                        "1. 開場說：各位同學好！今天老師感冒沙啞，我們來看看這一章。"
                        "2. 使用珍珠奶茶情境解釋科學原理。化學式如 $$CO_2$$ 與公式如 $$n = \\frac{m}{M}$$ 必須使用 LaTeX。"
                        "3. 教學後請加上分隔線 '---QUIZ---' 並出一題有選項的隨機測驗題與答案。"
                        "4. 提醒多喝溫水。"
                    ]
                    
                    response = model.generate_content(prompt_text)
                    full_text = response.text
                    
                    # 拆分內容與練習題
                    parts = full_text.split("---QUIZ---")
                    st.markdown(parts[0])
                    
                    # 語音生成 (存成檔案再播放)
                    asyncio.run(save_voice(parts[0], "temp_voice.mp3"))
                    if os.path.exists("temp_voice.mp3"):
                        st.audio("temp_voice.mp3")
                    
                    # 隨機練習題
                    if len(parts) > 1:
                        st.success("📝 **隨堂隨機挑戰**")
                        st.markdown(parts[1])
                    
                    st.balloons()
                except Exception as e:
                    st.error(f"連線出錯：{e}")
        else:
            st.error("找不到講義 Ph_Ch_finals.pdf，請確認 data 資料夾。")