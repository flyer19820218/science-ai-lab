import streamlit as st
import google.generativeai as genai
import os
import asyncio
import edge_tts
import io
from PIL import Image

# --- 1. 頁面配置 (翩翩體與自適應) ---
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
        height: 48px;
    }
    audio { width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心語音引擎 (穩定男聲 + 緩存機制) ---
# 加入緩存，同樣的文字不會重複呼叫微軟服務
@st.cache_data(show_spinner=False)
def get_voice_sync(text):
    async def _generate():
        communicate = edge_tts.Communicate(text, "zh-TW-YunxiNeural", rate="-5%")
        data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                data += chunk["data"]
        return data
    return asyncio.run(_generate())

# --- 3. 學生 API 指南 (保留經典 6 步教學) ---
st.title("🔬 理化 AI 手搖飲實驗室")

with st.expander("各位小朋友好！點此查看『如何取得通行證』詳細步驟", expanded=True):
    st.markdown("""
    <div class="guide-box">
        <b>請跟著以下步驟取得你的 AI 通行證：</b><br><br>
        1. 點擊連結開啟網頁：<a href="https://aistudio.google.com/app/apikey" target="_blank">👉 Google AI Studio</a><br>
        2. <b>重要：請務必使用個人 Gmail 帳號登入</b>。<br>
        3. 點擊畫面上的藍色按鈕 <b>"Create API key"</b>。<br>
        4. 選擇 <b>"Create API key in new project"</b>。<br>
        5. 看到金鑰代碼後，點擊 <b>"Copy"</b> 複製起來。<br>
        6. 回到本網頁，把代碼貼在下方的輸入框中，按下 Enter。
    </div>
    """, unsafe_allow_html=True)

user_key = st.text_input("🔑 在這裡貼上你的 API 通行證：", type="password")

if user_key:
    try:
        genai.configure(api_key=user_key)
        st.success("✅ 通行證驗證成功！")
    except:
        st.error("⚠️ 金鑰有誤，請檢查。")

st.divider()

# --- 4. 學生問答區 ---
st.subheader("💬 學生提問區：拍照或打字問 AI 老師")
student_q = st.text_input("輸入你想問的問題：", placeholder="例如：為什麼原子量沒有單位？")
uploaded_file = st.file_uploader("或是拍照上傳題目截圖：", type=["jpg", "png", "jpeg"])

if (student_q or uploaded_file) and user_key:
    with st.spinner("AI 老師思考中..."):
        try:
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            prompt = ["你是資深男理化老師。1.開場說『各位同學好』。2.術語加註中文。3.解說要簡單。"]
            if uploaded_file: prompt.append(Image.open(uploaded_file))
            if student_q: prompt.append(f"問題：{student_q}")
            res = model.generate_content(prompt)
            st.info(f"👨‍🏫 **老師解釋：**\n\n{res.text}")
        except Exception as e:
            if "429" in str(e): st.error("🚫 流量爆了！請等一分鐘再問。")
            else: st.error(f"連線失敗：{e}")

st.divider()

# --- 5. 手搖飲教學與男聲播放器 (校準提示語) ---
st.subheader("🥤 莫耳數攻略：珍珠奶茶計算法")

if st.button("🚀 啟動互動教學 (含男聲講述與進度條)"):
    if not user_key:
        st.warning("請先輸入通行證。")
    else:
        pdf_path = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        if os.path.exists(pdf_path):
            # 老師要求的提示語：調製大杯珍奶
            with st.spinner("AI 老師正在調製大杯珍奶中..."):
                try:
                    gemini_file = genai.upload_file(path=pdf_path)
                    model = genai.GenerativeModel('models/gemini-2.5-flash')
                    prompt_text = [
                        gemini_file,
                        "你是有 20 年資歷的男理化老師。請根據講義第 27 頁教學。"
                        "1. 開場說：『各位同學好！歡迎來到理化教室。今天老師聲音沙啞，但為了你們最愛的珍奶，我們來聊聊莫耳數...』"
                        "2. 務必完整列出講義中的例題題目內容。"
                        "3. 使用珍珠奶茶珍珠量解釋公式 n = m / M。最後提醒多喝溫水。"
                    ]
                    response = model.generate_content(prompt_text)
                    st.markdown(response.text)
                    
                    # 語音生成 (清除標籤)
                    clean_text = response.text.replace('$', '').replace('*', '').replace('#', '').replace('\n', ' ')
                    audio_bytes = get_voice_sync(clean_text)
                    
                    st.audio(audio_bytes, format="audio/mp3")
                    st.caption("💡 國三同學可拉動進度條重聽。")
                    st.balloons()
                except Exception as e:
                    if "429" in str(e): st.error("🚫 流量上限！請等 1 分鐘後再點。")
                    else: st.error(f"語音生成出錯：{e}")
        else:
            st.error("找不到講義檔案。")