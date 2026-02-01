import streamlit as st
import google.generativeai as genai
import os
import asyncio
import edge_tts
import io
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
    audio { width: 100%; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心男聲引擎 (穩定版 YunxiNeural) ---
async def generate_voice_bytes(text):
    # 移除符號避免語音亂唸
    clean_text = text.replace('$', '').replace('*', '').replace('#', '').replace('\n', ' ')
    communicate = edge_tts.Communicate(clean_text, "zh-TW-YunxiNeural", rate="-5%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- 3. 學生快速指南 (打勾兩次版) ---
st.title("理化 AI 手搖飲實驗室")

st.markdown("""
<div class="guide-box">
    <b>各位同學好！請照著以下步驟取得你的 AI 通行證：</b><br><br>
    1. 點擊連結：<a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a> 並登入。<br>
    2. 點擊 <b>Create API key</b>，勾選兩次同意條款後按產生。<br>
    3. 複製那串金鑰代碼，回到這裡貼上。
</div>
""", unsafe_allow_html=True)

user_key = st.text_input("在這裡貼上你的 API 通行證：", type="password")

if user_key:
    try:
        genai.configure(api_key=user_key)
        st.success("通行證驗證成功！")
    except:
        st.error("金鑰有誤，請檢查。")

st.divider()

# --- 4. 學生問答區 ---
st.subheader("學生提問區：拍照或打字問問題")
col1, col2 = st.columns([1, 1])
with col1:
    student_q = st.text_input("輸入你想問的問題：")
with col2:
    uploaded_file = st.file_uploader("拍照上傳題目截圖：", type=["jpg", "png", "jpeg"])

if (student_q or uploaded_file) and user_key:
    with st.spinner("AI 老師思考中..."):
        try:
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            prompt = ["你是資深男理化老師。化學式如 $$H_2O, CO_2$$ 必須使用 LaTeX 格式。"]
            parts = prompt + ([Image.open(uploaded_file)] if uploaded_file else []) + ([f"問題：{student_q}"] if student_q else [])
            res = model.generate_content(parts)
            st.info(f"老師解釋：\n\n{res.text}")
        except Exception as e:
            st.error(f"連線失敗：{e}")

st.divider()

# --- 5. 講義全單元隨選 (補齊 48-70 頁) ---
st.subheader("自主學習區：選擇你想上的單元")

unit_map = {
    "序章：禁忌的儀式與因果變律 (p.1-2)": 1,
    "1-1：測量與天平的平衡律 (p.3)": 3,
    "1-2：煉金基礎：物質的密度 (p.4)": 4,
    "1-3：煉金呼吸：大氣製備 (p.5)": 5,
    "1-5：溶解度與濃度的契約 (p.8)": 8,
    "2-1：波動的低語與聲速律法 (p.11)": 11,
    "3-2：折射定律與透鏡成像奧義 (p.18)": 18,
    "4-1：熱傳導與比熱的試煉 (p.22)": 22,
    "5-1：原子構造與離子契約 (p.25)": 25,
    "6-1：質量守恆與莫耳數計數 (p.27)": 27,
    "7-1：解離說與 pH 值的規律 (p.31)": 31,
    "8-2：酯化反應與聚合物之魂 (p.37)": 37,
    "9-2：摩擦力與帕斯卡的壓力 (p.43)": 43,
    "9-3：大氣壓力與浮力秘術 (p.46)": 46,
    "10-1：時間的流逝：直線運動 (p.48-51)": 48,
    "10-2：速度與加速度的追逐 (p.52-55)": 52,
    "11-1：牛頓三大運動定律 (p.56-60)": 56,
    "11-2：圓周運動與萬有引力 (p.61-63)": 61,
    "12-1：功與能的轉換守恆 (p.64-67)": 64,
    "12-2：槓桿原理與簡單機械 (p.68-70)": 68,
    "末章：直流電動機與旋轉輪迴 (p.71)": 71
}

selected_unit = st.selectbox("請選擇學習單元：", list(unit_map.keys()))
target_page = unit_map[selected_unit]

if st.button(f"啟動【{selected_unit}】教學內容"):
    if not user_key:
        st.warning("請先輸入通行證。")
    else:
        file_path = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        if os.path.exists(file_path):
            with st.spinner(f"正在準備第 {target_page} 頁教學與珍奶中..."):
                try:
                    sample_file = genai.upload_file(path=file_path)
                    model = genai.GenerativeModel('models/gemini-2.5-flash')
                    
                    prompt_text = [
                        sample_file,
                        f"你是有 20 年資歷的男理化老師。請針對講義第 {target_page} 頁教學。"
                        "1. 開場說：各位同學好！今天老師感冒沙啞，但我們還是要來聊聊這一章。"
                        "2. 使用手搖飲珍珠情境解釋原理。化學式與公式必須嚴格使用 LaTeX 格式（如 $CO_2$, $n = \\frac{m}{M}$）。"
                        "3. 教學後務必加上標籤 '---QUIZ---' 並出一題有選項的隨機測驗題與答案。"
                        "4. 提醒多喝溫水。"
                    ]
                    
                    response = model.generate_content(prompt_text)
                    full_text = response.text
                    
                    # 拆分內容與測驗
                    parts = full_text.split("---QUIZ---")
                    st.markdown(parts[0])
                    
                    # 語音生成
                    audio_bytes = asyncio.run(generate_voice_bytes(parts[0]))
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3")
                    
                    # 顯示測驗
                    if len(parts) > 1:
                        st.success("隨堂隨機挑戰題")
                        st.markdown(parts[1])
                    
                    st.balloons()
                except Exception as e:
                    st.error(f"連線出錯：{e}")
        else:
            st.error("找不到講義檔案。")