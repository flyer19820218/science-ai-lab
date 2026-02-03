import streamlit as st
import google.generativeai as genai
import os
import asyncio
import edge_tts
import re
import base64
from PIL import Image

# --- 零件檢查 ---
try:
    import fitz
except ImportError:
    st.error("❌ 偵測到零件缺失！請確保環境中已安裝 pymupdf。")
    st.stop()

# --- 1. 頁面配置 (蘋果手機全適配：白晝協議 + 翩翩體) ---
st.set_page_config(page_title="理化 AI 雞排珍奶實驗室", layout="wide")

st.markdown("""
    <style>
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stToolbar"], .stMain {
        background-color: #ffffff !important;
    }
    html, body, .stMarkdown, p, span, label, li {
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', sans-serif !important;
    }
    div[data-baseweb="popover"], div[data-baseweb="listbox"], ul[role="listbox"], li[role="option"] {
        background-color: #ffffff !important; color: #000000 !important;
    }
    div[data-testid="stTextInput"] input, div[data-baseweb="select"], div[data-baseweb="select"] > div {
        background-color: #ffffff !important; color: #000000 !important;
        -webkit-text-fill-color: #000000 !important; border: 2px solid #000000 !important;
    }
    div.stButton > button {
        background-color: #e3f2fd !important; color: #000000 !important;
        border: 2px solid #01579b !important; border-radius: 12px !important;
        width: 100% !important; height: 3.5rem !important;
    }
    .guide-box { border: 2px dashed #01579b; padding: 1.5rem; border-radius: 12px; background-color: #f0f8ff; color: #000000; }
    .katex { color: #000000 !important; }
    @media (prefers-color-scheme: dark) {
        .stApp, div[data-testid="stTextInput"] input, [data-testid="stFileUploader"] section {
            background-color: #ffffff !important; color: #000000 !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 曉臻語音引擎 (純淨播音模式) ---
async def generate_voice_base64(text):
    # 只保留中文字與基本標點，徹底清除所有代碼殘留
    clean_text = re.sub(r'[^\w\u4e00-\u9fff\d，。！？「」]', '', text)
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_data += chunk["data"]
    b64 = base64.b64encode(audio_data).decode()
    return f'<audio controls autoplay style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

# --- 3. 圖片提取 ---
def get_pdf_page_image(pdf_path, page_index):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_index)
    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)) 
    img_data = pix.tobytes("png")
    doc.close()
    return img_data

# --- 4. 72 頁熱血標題 (完整保留) ---
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

# --- 5. 初始化 ---
if 'audio_html' not in st.session_state: st.session_state.audio_html = None

# --- 6. API 通行指南 ---
st.title("🚀 理化 AI 雞排珍奶實驗室 (曉臻助教版)")
st.markdown("""<div class="guide-box"><b>📖 學生快速通行指南：</b><br>1. 前往 <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a> 獲取金鑰。<br>2. 貼回下方並按 Enter，開啟曉臻助教的沉浸式教學。</div>""", unsafe_allow_html=True)
user_key = st.text_input("🔑 通行證輸入區：", type="password")
st.divider()

# --- 7. 學生問問題區 ---
st.subheader("💬 學生問問題區")
student_q = st.text_input("打字問曉臻：", placeholder="例如：比熱怎麼算？")
uploaded_file = st.file_uploader("📸 照片區：", type=["jpg", "png", "jpeg"])

if (student_q or uploaded_file) and user_key:
    with st.spinner("正在調製波霸奶茶..."):
        try:
            genai.configure(api_key=user_key)
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            parts = ["你是助教曉臻。用雞排配珍奶解釋。公式使用 LaTeX。"]
            if uploaded_file: parts.append(Image.open(uploaded_file))
            if student_q: parts.append(student_q)
            res = model.generate_content(parts)
            st.info(f"💡 曉臻解答：\n\n{res.text}")
        except Exception as e: st.error(f"思考失敗：{e}")

st.divider()

# --- 8. 五大門派選單 ---
parts_list = ["【第一門：物質初探】", "【二：能量流轉】", "【三：微觀審判】", "【四：力學秘術】", "【五：旋轉輪迴】"]
part_choice = st.selectbox("大章節", parts_list)
r = range(1, 16) if "一" in part_choice else range(16, 27) if "二" in part_choice else range(27, 41) if "三" in part_choice else range(41, 55) if "四" in part_choice else range(55, 73)
options = [f"第 {p} 頁：{page_titles.get(p, '單元')}" for p in r]
selected_page_str = st.selectbox("精確單元名稱", options)
target_page = int(re.search(r"第 (\d+) 頁", selected_page_str).group(1))

# --- 9. 啟動導讀 (雙軌：聲畫分離協定) ---
if st.button(f"🚀 啟動【第 {target_page} 頁】沉浸式導讀"):
    if not user_key: st.warning("請先輸入金鑰。")
    else:
        genai.configure(api_key=user_key)
        path_finals = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        with st.spinner("曉臻正在純化劇本..."):
            try:
                page_img = get_pdf_page_image(path_finals, target_page - 1)
                st.image(page_img, use_column_width=True)
                file_obj = genai.upload_file(path=path_finals)
                model = genai.GenerativeModel('models/gemini-2.5-flash')
                
                # --- 🎯 雙軌 Prompt：將視覺與聽覺完全拆分 ---
                prompt_content = [file_obj, f"""你是資深理化助教曉臻。講解第 {target_page} 頁。

請將回答嚴格分為兩部分，並用標籤分隔：
【視覺內容】：給學生看著講義聽課用的 Markdown 筆記。公式請用 LaTeX 寫得漂亮。
【聽覺劇本】：曉臻要唸出來的口語。請將所有公式轉換為老師上課唸的中文字。

聽覺劇本 6 指令：
1. 嚴禁出現符號、斜線或 LaTeX。
2. n=m/M 唸作「莫耳數等於質量除以分子量」。
3. 語氣熱血狂熱，像馬斯克在上課。
4. 絕對不准反問學生問題。
5. 變數一律稱呼物理意義（如 n 是莫耳數）。
6. 結尾大喊：「這就是理化的真理！」"""]

                res = model.generate_content(prompt_content)
                full_text = res.text
                
                # 執行雙軌拆分
                display_part = full_text.split("【聽覺劇本】")[0].replace("【視覺內容】", "").strip()
                audio_part = full_text.split("【聽覺劇本】")[-1].strip() if "【聽覺劇本】" in full_text else display_part
                
                # 畫面上只顯示【視覺內容】
                st.markdown(display_part)
                # 曉臻只唸【聽覺劇本】，且文字不顯示在畫面上
                st.session_state.audio_html = asyncio.run(generate_voice_base64(audio_part))
                st.balloons()
            except Exception as e: st.error(f"異常：{e}")

if st.session_state.audio_html:
    st.markdown("---")
    st.info("🔊 **曉臻助教正在口播真理...**")
    st.markdown(st.session_state.audio_html, unsafe_allow_html=True)