import streamlit as st
import google.generativeai as genai
import os
import asyncio
import edge_tts
import io
from PIL import Image

# --- 1. 頁面配置 (全黑字體與翩翩體) ---
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
    audio { width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 強化版男聲引擎 (修正語音中斷問題) ---
async def generate_voice(text):
    # 使用沉穩男聲 Yunxi
    communicate = edge_tts.Communicate(text, "zh-TW-YunxiNeural", rate="-5%")
    audio_stream = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_stream.write(chunk["data"])
    audio_stream.seek(0)
    return audio_stream.read()

# --- 3. 學生 API 指南 (簡化版) ---
st.title("理化 AI 手搖飲實驗室")

st.markdown("""
<div class="guide-box">
    <b>各位同學好！請照著以下步驟取得你的 AI 通行證：</b><br><br>
    1. 點擊連結：<a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a> 並登入個人帳號。<br>
    2. 點擊 <b>Create API key</b>，<b>勾選兩次同意條款</b>後按產生。<br>
    3. 複製那串金鑰代碼，回到這裡貼上。
</div>
""", unsafe_allow_html=True)

user_key = st.text_input("🔑 在這裡貼上你的 API 通行證：", type="password")

if user_key:
    try:
        genai.configure(api_key=user_key)
        st.success("✅ 通行證驗證成功！")
    except:
        st.error("金鑰有誤，請檢查。")

st.divider()

# --- 4. 學生問答專區 ---
st.subheader("💬 學生提問區：拍照或打字問問題")
col_q, col_i = st.columns([1, 1])
with col_q:
    student_q = st.text_input("輸入你想問的問題：")
with col_i:
    uploaded_file = st.file_uploader("📷 拍照上傳題目截圖：", type=["jpg", "png", "jpeg"])

if (student_q or uploaded_file) and user_key:
    with st.spinner("AI 老師思考中..."):
        try:
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            prompt = ["資深男理化老師。所有的化學式如 $$H_2O, CO_2$$ 必須使用 LaTeX 格式。解說要簡單好懂。"]
            if uploaded_file: prompt.append(Image.open(uploaded_file))
            if student_q: prompt.append(f"問題：{student_q}")
            res = model.generate_content(prompt)
            st.info(f"👨‍🏫 老師解釋：\n\n{res.text}")
        except Exception as e:
            st.error(f"連線失敗：{e}")

st.divider()

# --- 5. 單元選擇與動態教學 ---
st.subheader("🥤 自主學習區：選擇你想上的課")

# 70頁講義的大單元索引表
unit_map = {
    "第一章：基本測量與物質組成 (p.1-20)": 1,
    "第二章：原子結構與週期表 (p.21-35)": 21,
    "第三章：化學反應與莫耳數 (p.36-50)": 36,
    "第四章：氧化還原 (p.51-70)": 51
}

selected_unit = st.selectbox("📖 請選擇學習單元範圍：", list(unit_map.keys()))
start_page = unit_map[selected_unit]

if st.button(f"🚀 啟動【{selected_unit}】互動教學"):
    if not user_key:
        st.warning("請先輸入通行證。")
    else:
        file_path = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        if os.path.exists(file_path):
            with st.spinner("🥤 AI 老師正在準備講義與珍奶中..."):
                try:
                    sample_file = genai.upload_file(path=file_path)
                    model = genai.GenerativeModel('models/gemini-2.5-flash')
                    
                    # 提示詞優化：鎖定內容與 LaTeX
                    prompt_text = [
                        sample_file,
                        f"你是有 20 年資歷的男理化老師。請針對講義第 {start_page} 頁開始的單元教學。"
                        "1. 開場說：各位同學好！今天老師感冒沙啞，但我們還是要來聊聊這一章。"
                        "2. 使用珍珠奶茶情境解釋科學原理。3. 化學式與公式必須嚴格使用 LaTeX 格式。"
                        "4. 課程最後請加上標籤 '---練習題---'，並出一道選擇題（含選項）與正確答案。"
                        "5. 提醒多喝溫水。"
                    ]
                    
                    response = model.generate_content(prompt_text)
                    full_text = response.text
                    
                    # 分解內容
                    parts = full_text.split("---練習題---")
                    st.markdown(parts[0])
                    
                    # 生成語音 (使用 asyncio 解決中斷問題)
                    clean_text = parts[0].replace('$', '').replace('*', '').replace('#', '').replace('\n', ' ')
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    audio_bytes = loop.run_until_complete(generate_voice(clean_text))
                    
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3")
                    
                    # 顯示測驗
                    if len(parts) > 1:
                        st.success("📝 **隨堂挑戰題**")
                        st.markdown(parts[1])
                    
                    st.balloons()
                except Exception as e:
                    if "429" in str(e): st.error("🚫 流量爆了！請等一分鐘後再試。")
                    else: st.error(f"連線失敗：{e}")
        else:
            st.error("找不到講義檔案。")