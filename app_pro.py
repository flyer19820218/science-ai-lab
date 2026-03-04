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
    st.error("❌ 零件缺失！請確保已安裝 pymupdf。")
    st.stop()

# ==========================================
# 🧠 核心大腦：曉臻老師專屬 Prompt 腳本設定區
# ==========================================
# 您可以隨時在這裡修改曉臻的上課風格、四段式內容，以及發音修正。

PROMPT_TEMPLATE = """
你是「理化實驗室」的專屬導讀助教曉臻。你熱愛馬拉松（半馬 PB 92 分），語速穩定、語調溫和，充滿科學熱情。
請針對這份講義的【第 {target_page} 頁】進行教學導讀。

【視覺與聽覺雙軌協議】（嚴格執行）
請將你的回答分為兩個部分，並用標籤隔開：
1. 【視覺內容】：畫面上給學生看的 Markdown 解答。排版清晰，重點字可加粗。所有的數學與化學公式必須嚴格使用 LaTeX 包覆（如 $$n = \\frac{{m}}{{M}}$$ 或 $2H_2O_2 \\rightarrow 2H_2O + O_2$）。
2. 【聽覺劇本】：曉臻要唸出來的隱藏劇本。
   - 劇本長度必須與視覺內容相等甚至更長，細節要多。
   - 【特殊發音修正】：劇本中「嚴禁」出現數學符號與英文代號。看到 1ppm 必須寫成「百萬分之一」；看到 n=m/M 必須寫成「莫耳數等於質量除以分子量」；遇到 M 必須唸作「體積莫耳濃度」；遇到雙氧水化學式請直接寫「雙氧水」。
   - 解釋「莫耳」概念時，請優先使用「手搖飲珍珠」的邏輯來比喻。

【教學產線四大流程】（請在視覺與聽覺中都呈現這四個段落的對應內容）
(1) 10秒課前熱身：隨機產出 30 秒運動健康或賽事內容（如 NBA、棒球經典賽、拉筋、剛跑完步的心得），並提到「現炸大雞排」配「波霸奶茶」舒緩學生壓力。劇本開頭必喊：『各位同學，請翻到第 {target_page} 頁。』
(2) 重點整理詳細解析：用自然段落解釋畫面上的核心觀念與圖表。拒絕唸出圖片的排版描述（如顏色、字體、背景）。
(3) 題目講解：若頁面中有練習題，請詳細講解。若難度較高，請啟動「分段配速解說」，引導學生將前面概念與習題串連，確保每個同學都能跟上這場科學馬拉松。若無題目則總結觀念。
(4) 常考重點與易錯提醒：點出大考常考重點，以及學長姐最常犯的錯誤（避坑指南）。結尾必含句：「開課前拉拉筋，老師跑完馬拉松才來的，大家加油！」或「熱身一下上完課老師就要去慢跑囉」。
"""

# ==========================================
# 🎨 1. 頁面配置 (蘋果/平板雙模適配：深度白晝協議)
# ==========================================
st.set_page_config(page_title="理化 AI 雞排珍奶實驗室", layout="wide")

st.markdown("""
    <style>
    /* 全局白底黑字鎖定 */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .stMain {
        background-color: #ffffff !important;
    }
    html, body, .stMarkdown, p, span, label, li {
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', 'PingFang TC', sans-serif !important;
        font-size: calc(1rem + 0.3vw) !important;
    }

    /* 蘋果手機/平板 Selectbox 黑底與反黑修正 */
    div[data-baseweb="popover"], div[data-baseweb="listbox"], ul[role="listbox"], li[role="option"] {
        background-color: #ffffff !important; color: #000000 !important;
    }
    div[data-testid="stTextInput"] input, div[data-baseweb="select"], div[data-baseweb="select"] > div {
        background-color: #ffffff !important; color: #000000 !important;
        -webkit-text-fill-color: #000000 !important; border: 2px solid #000000 !important;
    }

    /* 📸 照片區中文化與配色修正 */
    [data-testid="stFileUploader"] section { background-color: #ffffff !important; border: 2px dashed #01579b !important; }
    [data-testid="stFileUploader"] button { background-color: #e3f2fd !important; color: #000000 !important; border: 1px solid #01579b !important; }
    [data-testid="stFileUploader"] button div span { font-size: 0 !important; }
    [data-testid="stFileUploader"] button div span::before { content: "瀏覽檔案 (選取題目)" !important; font-size: 1rem !important; color: #000000 !important; }

    /* 按鈕適配 */
    div.stButton > button {
        background-color: #e3f2fd !important; color: #000000 !important;
        border: 2px solid #01579b !important; border-radius: 12px !important;
        width: 100% !important; height: 3.5rem !important;
    }
    .guide-box { border: 2px dashed #01579b; padding: 1.2rem; border-radius: 12px; background-color: #f0f8ff; color: #000000; }
    .katex { color: #000000 !important; }

    /* 強制暗色模式失效 */
    @media (prefers-color-scheme: dark) {
        .stApp, div[data-testid="stTextInput"] input, [data-testid="stFileUploader"] section {
            background-color: #ffffff !important; color: #000000 !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 🎙️ 2. 曉臻語音引擎 (純化播音)
# ==========================================
async def generate_voice_base64(text):
    # 清除 Markdown 與特殊符號，確保只唸中文字與標點
    clean_text = re.sub(r'[^\w\u4e00-\u9fff\d，。！？「」、：]', '', text)
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": audio_data += chunk["data"]
    b64 = base64.b64encode(audio_data).decode()
    return f'<audio controls autoplay style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

# ==========================================
# 🖼️ 3. 圖片處理功能
# ==========================================
def get_pdf_page_image(pdf_path, page_index):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_index)
    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)) 
    img_data = pix.tobytes("png")
    doc.close()
    return img_data

# ==========================================
# 📚 4. 72 頁熱血標題字典 (不變)
# ==========================================
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

if 'audio_html' not in st.session_state: st.session_state.audio_html = None
if 'qa_audio_html' not in st.session_state: st.session_state.qa_audio_html = None

# ==========================================
# 🔑 5. UI 與 API 驗證
# ==========================================
st.title("🚀 理化 AI 雞排珍奶實驗室 (曉臻助教版)")
st.markdown("""
<div class="guide-box">
    <b>📖 學生快速通行指南：</b><br>
    1. 前往 <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a>。<br>
    2. 點擊 <b>Create API key</b> 產出專屬通行證。<br>
    3. 貼回下方「通行證」欄位按 Enter 啟動反應爐。
</div>
""", unsafe_allow_html=True)
user_key = st.text_input("🔑 通行證輸入區：", type="password")
st.divider()

# ==========================================
# 💬 6. 學生問答區 (同樣套用雙軌與熱身風格)
# ==========================================
st.subheader("💬 學生問問題區")
student_q = st.text_input("打字問曉臻：", placeholder="例如：1ppm 是什麼意思？")
uploaded_file = st.file_uploader("📸 照片區：", type=["jpg", "png", "jpeg"])

if (student_q or uploaded_file) and user_key:
    with st.spinner("曉臻正在分析問題..."):
        try:
            genai.configure(api_key=user_key)
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            
            # 問答區專用 Prompt
            prompt_qa = f"""{PROMPT_TEMPLATE}
            
            這是學生的提問內容，請依照上述【四段式產出】與【雙軌協議】為他解答：
            學生的問題：{student_q}
            """
            
            parts = [prompt_qa]
            if uploaded_file: parts.append(Image.open(uploaded_file))
            res = model.generate_content(parts)
            
            full_qa = res.text
            display_qa = full_qa.split("【聽覺劇本】")[0].replace("【視覺內容】", "").strip()
            voice_qa = full_qa.split("【聽覺劇本】")[-1].strip() if "【聽覺劇本】" in full_qa else display_qa
            
            st.info(f"💡 曉臻解答：\n\n{display_qa}")
            st.session_state.qa_audio_html = asyncio.run(generate_voice_base64(voice_qa))
        except Exception as e: st.error(f"思考失敗：{e}")

if st.session_state.qa_audio_html:
    st.markdown(st.session_state.qa_audio_html, unsafe_allow_html=True)
st.divider()

# ==========================================
# 📖 7. 課程選單與導讀啟動
# ==========================================
st.subheader("📖 啟動導讀：選擇單元")
parts_list = ["【第一門：物質初探】", "【二：能量流轉】", "【三：微觀審判】", "【四：力學秘術】", "【五：旋轉輪迴】"]
part_choice = st.selectbox("大章節", parts_list)
r = range(1, 16) if "一" in part_choice else range(16, 27) if "二" in part_choice else range(27, 41) if "三" in part_choice else range(41, 55) if "四" in part_choice else range(55, 73)
options = [f"第 {p} 頁：{page_titles.get(p, '單元')} " for p in r]
selected_page_str = st.selectbox("精確單元名稱", options)
target_page = int(re.search(r"第 (\d+) 頁", selected_page_str).group(1))

if st.button(f"🚀 啟動【第 {target_page} 頁】真理導讀"):
    if not user_key: st.warning("請先輸入金鑰。")
    else:
        genai.configure(api_key=user_key)
        path_finals = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        with st.spinner("曉臻正在備課調製珍奶..."):
            try:
                page_img = get_pdf_page_image(path_finals, target_page - 1)
                st.image(page_img, use_column_width=True)
                file_obj = genai.upload_file(path=path_finals)
                model = genai.GenerativeModel('models/gemini-2.5-flash')
                
                # 直接注入剛剛寫好的核心 PROMPT_TEMPLATE
                final_prompt = PROMPT_TEMPLATE.format(target_page=target_page)
                
                res = model.generate_content([file_obj, final_prompt])
                full_lecture = res.text
                
                # 雙軌切割
                display_lecture = full_lecture.split("【聽覺劇本】")[0].replace("【視覺內容】", "").strip()
                voice_lecture = full_lecture.split("【聽覺劇本】")[-1].strip() if "【聽覺劇本】" in full_lecture else display_lecture
                
                st.markdown(display_lecture)
                st.session_state.audio_html = asyncio.run(generate_voice_base64(voice_lecture))
                st.balloons()
            except Exception as e: st.error(f"異常：{e}")

if st.session_state.audio_html:
    st.markdown("---")
    st.info("🔊 **曉臻正在口播真理...**")
    st.markdown(st.session_state.audio_html, unsafe_allow_html=True)
