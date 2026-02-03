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

# --- 1. 介面配置 (極簡白晝協議：為老師與學生設計的清晰視覺) ---
st.set_page_config(page_title="理化 AI 雞排珍奶實驗室", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    html, body, [class*="css"], .stMarkdown, p, span, label, li {
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', sans-serif !important;
    }
    div[data-testid="stTextInput"] input, div[data-baseweb="select"] {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid #000000 !important;
    }
    div.stButton > button {
        background-color: #e3f2fd !important; 
        color: #000000 !important;
        border: 2px solid #01579b !important;
        border-radius: 12px !important;
        height: 3.5rem !important;
        width: 100% !important;
    }
    .katex { color: #000000 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心語音引擎 (曉臻 HsiaoChen：會說數學公式的助教) ---
async def generate_voice_base64(text):
    # 【公式轉譯協議】：將符號中性化，防止曉臻唸出「斜線」
    clean_text = re.sub(r'\$+', '', text)
    clean_text = clean_text.replace('/', '除以').replace('*', '乘以').replace('=', '等於')
    clean_text = clean_text.replace('\\%', '百分之').replace('%', '百分之')
    
    # 召喚曉臻 (HsiaoChenNeural)
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_data += chunk["data"]
    
    b64 = base64.b64encode(audio_data).decode()
    return f'<audio controls style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

# --- 3. 圖片提取功能 ---
def get_pdf_page_image(pdf_path, page_index):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_index)
    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)) 
    img_data = pix.tobytes("png")
    doc.close()
    return img_data

# --- 4. 72 頁熱血標題地圖 (完整保留) ---
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

# --- 5. Session 初始化 ---
if 'audio_html' not in st.session_state: st.session_state.audio_html = None

# --- 6. 介面主體 ---
st.title("🥤 理化 AI 雞排珍奶實驗室 (助教版)")
user_key = st.text_input("🔑 請輸入通行證 (API KEY)：", type="password")

st.divider()

# --- 7. 五大門派選單 ---
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

# --- 8. 點火發射區 ---
if st.button(f"🚀 啟動【第 {target_page} 頁】真理導讀"):
    if not user_key:
        st.warning("請先輸入金鑰。")
    else:
        genai.configure(api_key=user_key)
        path_finals = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        with st.spinner("正在調製波霸奶茶..."):
            try:
                # A. 顯示講義截圖
                page_img = get_pdf_page_image(path_finals, target_page - 1)
                st.image(page_img, caption=f"講義：{page_titles[target_page]}", use_column_width=True)
                
                # B. 上傳並分析
                file_obj = genai.upload_file(path=path_finals)
                model = genai.GenerativeModel('models/gemini-2.5-flash')
                
                # C. 🎯 API 核心 6 項提示 (精確切齊，絕不突出)
                prompt_content = [file_obj, f"""你是理化 AI 助教。詳細講解講義第 {target_page} 頁內容。
使用雞排配大杯珍奶解釋。
【語音優化 6 項指令】：
1. 公式顯示用 LaTeX。但口播台詞嚴禁出現「/」、「斜線」或「Slash」。
2. 看到 n=m/M，台詞必須寫成：「莫耳數等於質量除以分子量」。
3. 嚴禁反問使用者任何問題。
4. 看到符號請直接稱呼物理意義（如 n 叫莫耳數，m 叫質量）。
5. 口吻必須熱血且充滿科學狂熱。
6. 結尾帥氣大喊：「這就是理化的真理！」"""]

                # D. 生成劇本與語音
                res = model.generate_content(prompt_content)
                st.markdown(res.text)
                st.session_state.audio_html = asyncio.run(generate_voice_base64(res.text))
                st.balloons()
            except Exception as e:
                st.error(f"實驗異常：{e}")

# --- 9. 語音播放區 ---
if st.session_state.audio_html:
    st.markdown("---")
    st.info("🔊 **曉臻老師導讀中**：")
    st.markdown(st.session_state.audio_html, unsafe_allow_html=True)