import streamlit as st
import google.generativeai as genai
import os
import asyncio
import edge_tts
import io
from PIL import Image

# --- 1. 頁面配置 (翩翩體與全黑文字) ---
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

# --- 2. 強化音訊引擎 (解決聲音消失問題) ---
async def generate_voice_bytes(text):
    # 使用雲端男聲 Yunxi
    communicate = edge_tts.Communicate(text, "zh-TW-YunxiNeural", rate="-5%")
    audio_stream = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_stream.write(chunk["data"])
    audio_stream.seek(0)
    return audio_stream.read()

# --- 3. 學生 API 指南 (老師發現的勾選兩次版) ---
st.title("🔬 理化 AI 手搖飲實驗室")

st.markdown("""
<div class="guide-box">
    <b>各位同學好！請快速取得你的 AI 通行證：</b><br><br>
    步驟 1：點擊開啟 <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a> 並登入。<br>
    步驟 2：點擊 <b>Create API key</b>，<b>勾選兩次同意條款</b>後按下產生。<br>
    步驟 3：複製那串代碼，回到這裡貼上。
</div>
""", unsafe_allow_html=True)

user_key = st.text_input("🔑 在這裡貼上你的 API 通行證：", type="password")

if user_key:
    try:
        genai.configure(api_key=user_key)
        st.success("✅ 通行證驗證成功！正在連接 Gemini 2.5 Flash 老師...")
    except:
        st.error("❌ 金鑰有誤，請重新檢查。")

st.divider()

# --- 4. 學生問答區 ---
st.subheader("💬 學生提問區：拍照或打字問問題")
col_q, col_up = st.columns([1, 1])
with col_q:
    student_q = st.text_input("輸入你想問的理化問題：")
with col_up:
    uploaded_image = st.file_uploader("📷 拍照上傳題目截圖：", type=["jpg", "png", "jpeg"])

if (student_q or uploaded_image) and user_key:
    with st.spinner("👨‍🏫 AI 老師正在思考答案..."):
        try:
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            prompt = ["你是資深男理化老師。化學式如 $CO_2$ 與公式如 $n=m/M$ 必須使用 LaTeX 格式。"]
            if uploaded_image: prompt.append(Image.open(uploaded_image))
            if student_q: prompt.append(f"問題內容：{student_q}")
            res = model.generate_content(prompt)
            st.info(f"👨‍🏫 老師解釋：\n\n{res.text}")
        except Exception as e:
            st.error(f"連寫失敗：{e}")

st.divider()

# --- 5. 自主學習區：單元選單 (Pull Bar) ---
st.subheader("🥤 自主學習區：你想上哪一課？")

# 根據講義內容整理的正確單元對照表
unit_map = {
    "序章：實驗安全與科學方法 (p.1-2)": 1,
    "1-1：測量、誤差與天平使用 (p.3)": 3,
    "1-2：物質的特徵：密度 (p.4)": 4,
    "1-3：大氣製備：氮、氧、二氧化碳 (p.5)": 5,
    "1-4：純物質與混合物、過濾 (p.6-7)": 6,
    "1-5：溶解度與百分率濃度 (p.8-10)": 8,
    "2-1：波動傳遞與聲速律法 (p.11-13)": 11,
    "2-2：樂音三要素與超聲波 (p.14-15)": 14,
    "3-1：光的傳播、反射與針孔成像 (p.16-17)": 16,
    "3-2：折射定律與透鏡成像奧義 (p.18-21)": 18,
    "4-1：熱傳導、潛熱與比熱 (p.22-24)": 22,
    "5-1：原子構造與離子契約 (p.25-26)": 25,
    "6-1：質量守恆與莫耳數計數 (p.27-28)": 27,
    "6-2：反應速率與氧化還原殺陣 (p.29-30)": 29,
    "7-1：解離說、酸鹼特性與pH值 (p.31-33)": 31,
    "7-2：酸鹼中和與生活鹽類 (p.34-35)": 34,
    "8-1：有機化合物與乾餾 (p.36)": 36,
    "8-2：烴類、酯化與聚合物 (p.37-39)": 37,
    "8-3：皂化反應與界面活性劑 (p.40)": 40,
    "9-1：力之三要素與虎克定律 (p.41-42)": 41,
    "9-2：摩擦力、壓力與帕斯卡 (p.43-45)": 43,
    "9-3：大氣壓力與浮力秘術 (p.46-47)": 46,
    "進階：直流電動機與電磁感應 (p.71)": 71
}

selected_unit = st.selectbox("📖 請選擇你想學習的章節單元：", list(unit_map.keys()))
target_page = unit_map[selected_unit]

if st.button(f"🚀 啟動【{selected_unit}】互動教學"):
    if not user_key:
        st.warning("請先輸入通行證。")
    else:
        file_path = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        if os.path.exists(file_path):
            with st.spinner(f"🥤 AI 老師正在調製大杯珍奶並翻閱第 {target_page} 頁..."):
                try:
                    sample_file = genai.upload_file(path=file_path)
                    model = genai.GenerativeModel('models/gemini-2.5-flash')
                    
                    # 提示詞鎖定：莫耳數珍珠情境 + LaTeX
                    prompt_text = [
                        sample_file,
                        f"你是資深男理化老師。請針對講義第 {target_page} 頁內容教學。"
                        "1. 開場說：各位同學好！今天老師感冒聲音沙啞。我們來看看這一章。"
                        "2. 務必完整列出講義中的例題內容。"
                        "3. 盡量使用手搖飲珍珠情境解釋原理。化學式與公式必須嚴格使用 LaTeX 格式（如 $CO_2$, $n=m/M$）。"
                        "4. 課程結束後加上分隔線 '---QUIZ---'，並根據本頁出一道『隨機練習題』(含選項) 與答案。"
                        "5. 最後提醒多喝溫水，注意身體。"
                    ]
                    
                    response = model.generate_content(prompt_text)
                    full_text = response.text
                    
                    # 分解內容與測驗
                    parts = full_text.split("---QUIZ---")
                    st.markdown(parts[0])
                    
                    # 音訊生成
                    clean_text = parts[0].replace('$', '').replace('*', '').replace('#', '').replace('\n', ' ')
                    audio_data = asyncio.run(generate_voice_bytes(clean_text))
                    
                    if audio_data:
                        st.audio(audio_data, format="audio/mp3")
                    
                    # 顯示練習題
                    if len(parts) > 1:
                        st.success("📝 **隨堂隨機挑戰題**")
                        st.markdown(parts[1])
                    
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"連線出錯：{e}。請稍後再試。")
        else:
            st.error("找不到講義檔案。")