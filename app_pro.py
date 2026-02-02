import streamlit as st
import google.generativeai as genai
import os
import asyncio
import edge_tts
import fitz  # 雲端自動截圖
import re
import base64
from PIL import Image

# --- 1. 頁面配置 (全能適配 + 白晝協議 + 手機優化) ---
st.set_page_config(page_title="理化 AI 珍珠莫耳研究室", layout="wide")

st.markdown("""
    <style>
    /* A. 全域白晝鎖定：強制背景與文字顏色 */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stToolbar"], .stMain {
        background-color: #ffffff !important;
    }
    html, body, [class*="css"], .stMarkdown, p, span, label, li {
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', 'Heiti TC', 'Microsoft JhengHei', sans-serif !important;
    }

    /* B. 手機排版優化：邊距與字體自動縮放 */
    [data-testid="stAppViewBlockContainer"] {
        padding: 1.5rem 1rem !important;
    }
    h1 { font-size: calc(1.5rem + 1.5vw) !important; text-align: center; }
    h3 { font-size: calc(1.1rem + 0.5vw) !important; }

    /* C. 深度組件修正：打字提問區與下拉選單 */
    div[data-testid="stTextInput"] input, div[data-baseweb="select"], div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        border: 2px solid #000000 !important;
    }

    /* D. 拍照截圖區：白底黑字 + 按鈕中文化 */
    [data-testid="stFileUploader"] section {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px dashed #000000 !important;
    }
    [data-testid="stFileUploader"] button {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #000000 !important;
    }
    [data-testid="stFileUploader"] button div span { font-size: 0 !important; }
    [data-testid="stFileUploader"] button div span::before {
        content: "瀏覽檔案" !important;
        font-size: 1rem !important;
        color: #000000 !important;
    }

    /* E. 理化專屬藍色導覽框 */
    .guide-box {
        background-color: #e3f2fd !important;
        color: #000000 !important;
        padding: 15px;
        border-radius: 12px;
        border: 2px solid #2196f3;
        margin-bottom: 20px;
    }

    /* F. 按鈕行動優化：手機上 100% 寬度方便點擊 */
    div.stButton > button {
        background-color: #e8eaf6 !important; 
        color: #000000 !important;
        border: 2px solid #1a237e !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        width: 100% !important;
        height: 3.5rem !important;
    }

    /* G. LaTeX 公式鎖定 */
    .katex { color: #000000 !important; }

    /* H. 針對手機深色模式的最後覆蓋 */
    @media (prefers-color-scheme: dark) {
        .stApp, div[data-testid="stTextInput"] input, section[data-testid="stFileUploader"], [data-testid="stFileUploader"] button {
            background-color: #ffffff !important;
            color: #000000 !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心助教語音 (iPad 專用 Base64) ---
async def generate_voice_base64(text):
    clean_text = re.sub(r'\$+', '', text).replace('\\%', '百分之').replace('%', '百分之')
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-3%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_data += chunk["data"]
    b64 = base64.b64encode(audio_data).decode()
    return f'<audio controls autoplay style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

# --- 3. 雲端截圖功能 ---
def get_pdf_page_image(pdf_path, page_index):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_index)
    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
    img_data = pix.tobytes("png")
    doc.close()
    return img_data

# --- 4. 理化 26 頁【珍珠莫耳全標題】 (完全校準) ---
page_titles = {
    1: "【物質的質量：原子量與分子量的真理】", 
    2: "【靈魂的度量衡：莫耳數 $n = m / M$ 的契約】", 
    3: "【化學的配方：反應式與係數的平衡律法】",
    4: "【質量的守恆：拉瓦節的物質不滅律法】", 
    5: "【能量的火花：吸熱與放熱反應的溫差】", 
    6: "【光陰的化身：反應速率與碰撞學說】",
    7: "【門檻的試煉：活化能與催化劑的秘密】", 
    8: "【平衡的博弈：勒沙特列原理與動態穩定】", 
    9: "【酸鹼的洗禮：$pH$ 值與水的離子積】",
    10: "【中和的藝術：酸鹼滴定與鹽類的生成】", 
    11: "【電子的長征：氧化還原與電位差的真相】", 
    12: "【伏特的禮物：電池、電解與電鍍律法】",
    13: "【有機的叢林：碳氫化合物與官能基之網】", 
    14: "【聚合物的意志：塑膠、纖維與天然橡膠】", 
    15: "【光的折射：透鏡成像與視力的矯正】",
    16: "【彩虹的密碼：光學色散與光譜的覺醒】", 
    17: "【聲波的共振：頻率、響度與音色的律法】", 
    18: "【熱量的傳遞：比熱、熱平衡與狀態改變】",
    19: "【靜電的審判：庫倫定律與電場的呼喚】", 
    20: "【歐姆的防線：電阻、電壓與電流的守恆】", 
    21: "【磁力的羅盤：電流磁效應與法拉第定律】",
    22: "【動能的狂飆：牛頓三大運動定律】", 
    23: "【位能的平衡：機械能守恆與槓桿原理】", 
    24: "【原子核的深處：放射性元素與核反應】",
    25: "【流體的壓力：帕斯卡原理與浮力律法】", 
    26: "【終極真理：科學探究與素養模擬考】"
}

# --- 5. 初始化 Session ---
if 'audio_html' not in st.session_state: st.session_state.audio_html = None

# --- 6. 介面呈現 ---
st.title("⚛️ 理化 AI 珍珠莫耳研究室 (助教版)")
st.markdown("""
<div class="guide-box">
    <b>📖 學生快速通行指南：</b><br>
    1. 點擊連結：<a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a> 並登入。<br>
    2. 複製那一串英文金鑰，貼回下方「通行證」欄位按 Enter 啟動助教。
</div>
""", unsafe_allow_html=True)

user_key = st.text_input("🔑 通行證輸入區：", type="password")
st.divider()

# --- 7. 提問區 ---
st.subheader("💬 理化真理提問區")
col_q, col_up = st.columns([1, 1])
with col_q: student_q = st.text_input("打字問助教：", placeholder="例如：為什麼 $n=m/M$？")
with col_up: uploaded_file = st.file_uploader("拍照詢問：", type=["jpg", "png", "jpeg"])

if (student_q or uploaded_file) and user_key:
    with st.spinner("正在調製珍珠奶茶..."):
        try:
            genai.configure(api_key=user_key)
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            parts = ["你是資深理化 AI 助教。請用珍珠奶茶 $n=m/M$ 解釋。公式必須使用 LaTeX。"]
            if uploaded_file: parts.append(Image.open(uploaded_file))
            if student_q: parts.append(student_q)
            res = model.generate_content(parts)
            st.info(f"💡 助教解答：\n\n{res.text}")
        except Exception as e: st.error(f"數據分析失敗：{e}")

st.divider()

# --- 8. 選單 ---
st.subheader("📖 翻開真理之書：選擇學習單元")
parts_list = ["【一：物質與能量】", "【二：反應與平衡】", "【三：有機與電學】", "【四：力學與光聲】"]
part_choice = st.selectbox("第一步：選擇大章節", parts_list)

if "一" in part_choice: r = range(1, 8)
elif "二" in part_choice: r = range(8, 14)
elif "三" in part_choice: r = range(14, 21)
else: r = range(21, 27)

options = [f"第 {p} 頁：{page_titles.get(p, '單元內容')}" for p in r]
selected_page_str = st.selectbox("第二步：精確單元名稱", options)
target_page = int(re.search(r"第 (\d+) 頁", selected_page_str).group(1))

# --- 9. 導讀按鈕 ---
if st.button(f"🚀 啟動【第 {target_page} 頁】圖文導讀"):
    if not user_key:
        st.warning("請先輸入金鑰。")
    else:
        genai.configure(api_key=user_key)
        path_finals = os.path.join(os.getcwd(), "data", "Physicsforfinals.pdf")
        with st.spinner("正在調製波霸奶茶..."):
            try:
                page_img = get_pdf_page_image(path_finals, target_page - 1)
                st.image(page_img, caption=f"講義：{page_titles[target_page]}", use_column_width=True)
                
                file_obj = genai.upload_file(path=path_finals)
                model = genai.GenerativeModel('models/gemini-2.5-flash')
                prompt = [
                    file_obj, 
                    f"你是資深理化 AI 助教。1. 請導讀第 {target_page} 頁內容。"
                    "2. 開場提雞排配大杯珍奶。說各位同學好！今天助教感冒沙啞。"
                    "3. 公式必須使用 LaTeX。不准出練習題。"
                ]
                res = model.generate_content(prompt)
                st.markdown(res.text)
                st.session_state.audio_html = asyncio.run(generate_voice_base64(res.text))
                st.balloons()
            except Exception as e: st.error(f"導讀失敗：{e}")

if st.session_state.audio_html:
    st.markdown("---")
    st.info("🔊 **提醒**：請點擊播放鈕聽助教導讀。")
    st.markdown(st.session_state.audio_html, unsafe_allow_html=True)