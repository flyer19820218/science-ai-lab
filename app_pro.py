import streamlit as st
import google.generativeai as genai
import os
import asyncio
import edge_tts
import re
import base64
from PIL import Image

# --- 零件檢查：防止雲端崩潰 ---
try:
    import fitz
except ImportError:
    st.error("❌ 偵測到零件缺失！請確保 GitHub 中有 requirements.txt 並包含 pymupdf。")
    st.stop()

# --- 1. 頁面配置 (白晝協議 + 行動端完全防溢位) ---
st.set_page_config(page_title="理化 AI 雞排珍奶實驗室", layout="wide")

st.markdown("""
    <style>
    /* A. 全域白晝協議：強制背景與文字顏色 */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stToolbar"], .stMain {
        background-color: #ffffff !important;
    }
    html, body, [class*="css"], .stMarkdown, p, span, label, li {
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', 'Heiti TC', 'Microsoft JhengHei', sans-serif !important;
    }

    /* B. 行動端防溢位優化：移除欄位限制，確保不滿出來 */
    [data-testid="stAppViewBlockContainer"] {
        padding: 1.5rem 1rem !important;
    }
    h1 { font-size: calc(1.5rem + 1vw) !important; text-align: center; }

    /* C. 提問區組件優化：解決「黑底黑字」與「輸入框溢位」 */
    div[data-testid="stTextInput"] input {
        background-color: #ffffff !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        border: 2px solid #000000 !important;
    }

    /* D. 拍照截圖區：強力中文化與空間校準 */
    [data-testid="stFileUploader"] section {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px dashed #000000 !important;
        padding: 10px !important;
    }
    [data-testid="stFileUploader"] button {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #000000 !important;
    }
    /* 暴力替換 Browse files 文字 */
    [data-testid="stFileUploader"] button div span { font-size: 0 !important; }
    [data-testid="stFileUploader"] button div span::before {
        content: "瀏覽檔案" !important;
        font-size: 1rem !important;
        color: #000000 !important;
    }

    /* E. 黃色導覽框鎖定 */
    .guide-box {
        background-color: #fff9c4 !important;
        color: #000000 !important;
        padding: 15px;
        border-radius: 12px;
        border: 2px solid #fbc02d;
        margin-bottom: 20px;
    }

    /* F. 按鈕行動優化 */
    div.stButton > button {
        background-color: #e3f2fd !important; 
        color: #000000 !important;
        border: 2px solid #01579b !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        width: 100% !important;
        height: 3.5rem !important;
    }

    /* G. LaTeX 公式與下拉選單鎖定 */
    .katex { color: #000000 !important; }
    div[data-baseweb="select"], div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心助教語音 (iPad 專用 Base64 強效方案) ---
async def generate_voice_base64(text):
    clean_text = re.sub(r'\$+', '', text).replace('\\%', '百分之').replace('%', '百分之')
    communicate = edge_tts.Communicate(clean_text, "zh-TW-YunxiNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_data += chunk["data"]
    b64 = base64.b64encode(audio_data).decode()
    return f'<audio controls style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

# --- 3. 雲端截圖功能 ---
def get_pdf_page_image(pdf_path, page_index):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_index)
    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)) 
    img_data = pix.tobytes("png")
    doc.close()
    return img_data

# --- 4. 72 頁熱血中二標題 (完整保留，一字不漏) ---
page_titles = {
    1: "【禁忌儀式：科學方法】", 2: "【因果變律：實驗安全】", 3: "【平衡律：測量與天平】", 4: "【煉金基礎：密度奧義】",
    5: "【煉金呼吸：大氣製備】", 6: "【本質界線：純物與混合】", 7: "【提純程序：過濾蒸發】", 8: "【溶解契約：飽和極限】",
    9: "【濃度鎖鍊：百分率之理】", 10: "【極限視界：百萬分點】", 11: "【介質低語：波動傳遞】", 12: "【聲速律法：溫度震盪】",
    13: "【迴聲空間：測距奧義】", 14: "【聽覺統治：樂音要素】", 15: "【感官外視界：超聲應用】", 16: "【虛空直線：光傳定律】",
    17: "【鏡像世界：反射與虛實】", 18: "【歪曲維度：折射與視深】", 19: "【光之焦點：透鏡奧義】", 20: "【散出虛無：凹透色散】",
    21: "【視覺修正：眼球構造】", 22: "【穿透熱能：熱傳導】", 23: "【能量流轉：對流輻射】", 24: "【因果天平：比熱計算】",
    25: "【微觀平衡：原子構造】", 26: "【地圖導覽：元素週期】", 27: "【終極天平：質量莫耳】", 28: "【絕對計數：常數契約】",
    29: "【變遷權杖：反應速率】", 30: "【因果殺陣：氧化還原】", 31: "【離子覺醒：解離電解】", 32: "【烈焰交鋒：酸鹼試煉】",
    33: "【色澤密碼：pH指示劑】", 34: "【聖戰餘韻：中和鹽類】", 35: "【結晶真理：日常鹽類】", 36: "【禁斷界線：有機起源】",
    37: "【奔流結構：烴類性質】", 38: "【香氣連鎖：酯化奧義】", 39: "【長鏈囚籠：聚物塑膠】", 40: "【界面生死：皂化活性】",
    41: "【平衡結界：力之要素】", 42: "【彈性律法：虎克比例】", 43: "【運動終焉：摩擦力學】", 44: "【重壓深淵：壓力的定義】",
    45: "【液態威壓：液壓規律】", 46: "【真空挑戰：大氣壓力】", 47: "【排水奧義：浮力秘術】", 48: "【時空座標：位移路徑】",
    49: "【動態規律：速度速率】", 50: "【加速度覺醒：等加速】", 51: "【第一律法：慣性定律】", 52: "【絕對方程：F=ma】",
    53: "【宿命反擊：作用反作】", 54: "【圓周輪迴：引力向心】", 55: "【時空軌跡：功與功率】", 56: "【位能幻化：重力能量】",
    57: "【永恆總量：力能守恆】", 58: "【力矩平衡：槓桿原理】", 59: "【機械魔法：滑輪應用】", 60: "【省力契約：斜面輪軸】",
    61: "【庫倫禁令：靜電感應】", 62: "【電勢之戰：電流電壓】", 63: "【電阻枷鎖：歐姆定律】", 64: "【瓦特之翼：電功功率】",
    65: "【焦耳毀滅：家用安全】", 66: "【無形指向：磁場磁極】", 67: "【靈魂契約：鋅銅電池】", 68: "【強制異變：電鍍祕術】",
    69: "【磁魂覺醒：右手定則】", 70: "【勞倫茲怒：開掌定則】", 71: "【旋轉輪迴：直流電動機】", 72: "【發電機覺醒：冷次定律】"
}

# --- 5. 初始化 Session ---
if 'audio_html' not in st.session_state: st.session_state.audio_html = None

# --- 6. 通行證申請教學 ---
st.title("🥤 理化 AI 雞排珍奶實驗室 (助教版)")
st.markdown("""<div class="guide-box"><b>📖 快速指南：</b>點擊 <a href="https://aistudio.google.com/app/apikey" target="_blank">AI Studio</a> 取得金鑰，<b>務必勾選兩次同意</b>後貼回下方。</div>""", unsafe_allow_html=True)
user_key = st.text_input("🔑 通行證：", type="password")

st.divider()

# --- 7. 學生提問區 (移除欄位，防止溢位) ---
st.subheader("💬 提問專區")
student_q = st.text_input("打字問助教：", placeholder="例如：莫耳數怎麼算？")
uploaded_file = st.file_uploader("拍下題目截圖：", type=["jpg", "png", "jpeg"])

if (student_q or uploaded_file) and user_key:
    with st.spinner("正在調製波霸奶茶..."):
        try:
            genai.configure(api_key=user_key)
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            # 修正提問邏輯，防止錯誤
            parts = ["你是資深理化 AI 助教。用雞排配大杯珍奶解釋。公式使用 LaTeX。"]
            if uploaded_file: parts.append(Image.open(uploaded_file))
            if student_q: parts.append(student_q)
            res = model.generate_content(parts)
            st.info(f"💡 助教解答：\n\n{res.text}")
        except Exception as e: st.error(f"思考失敗：{e}")

st.divider()

# --- 8. 五大門派雙選單 ---
st.subheader("📖 翻開講義學習")
parts_list = ["【第一門：物質初探】", "【二：能量流轉】", "【三：微觀審判】", "【四：力學秘術】", "【五：旋轉輪迴】"]
part_choice = st.selectbox("第一步：選擇大章節", parts_list)

if "一" in part_choice: r = range(1, 16)
elif "二" in part_choice: r = range(16, 27)
elif "三" in part_choice: r = range(27, 41)
elif "四" in part_choice: r = range(41, 55)
else: r = range(55, 73)

options = [f"第 {p} 頁：{page_titles.get(p, '單元重點')}" for p in r]
selected_page_str = st.selectbox("第二步：精確單元名稱", options)
target_page = int(re.search(r"第 (\d+) 頁", selected_page_str).group(1))

if st.button(f"🚀 啟動【第 {target_page} 頁】導讀"):
    if not user_key:
        st.warning("請先輸入金鑰。")
    else:
        genai.configure(api_key=user_key)
        path_finals = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        with st.spinner("正在調製波霸奶茶..."):
            try:
                page_img = get_pdf_page_image(path_finals, target_page - 1)
                st.image(page_img, caption=f"講義：{page_titles[target_page]}", use_column_width=True)
                file_obj = genai.upload_file(path=path_finals)
                model = genai.GenerativeModel('models/gemini-2.5-flash')
                prompt = [file_obj, f"你是理化 AI 助教。詳細講解講義第 {target_page} 頁。用雞排配大杯珍奶開場。公式必須 LaTeX。不准出測驗。"]
                res = model.generate_content(prompt)
                st.markdown(res.text)
                st.session_state.audio_html = asyncio.run(generate_voice_base64(res.text))
                st.balloons()
            except Exception as e: st.error(f"導讀失敗：{e}")

if st.session_state.audio_html:
    st.markdown("---")
    st.info("🔊 **平板提醒**：點擊下方播放鈕聽導讀。")
    st.markdown(st.session_state.audio_html, unsafe_allow_html=True)