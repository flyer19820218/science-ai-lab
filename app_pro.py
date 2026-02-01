import streamlit as st
import google.generativeai as genai
import os
import asyncio
import edge_tts
import fitz  # 雲端自動加載，免本機安裝
import re
import base64
from PIL import Image

# --- 1. 頁面配置 (全黑翩翩體、適應平板) ---
st.set_page_config(page_title="理化 AI 雞排珍奶實驗室", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="css"], .stMarkdown, p, h1, h2, h3, span, label, li {
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', 'KaiTi', sans-serif !important;
    }
    .guide-box {
        background-color: #fff9c4;
        padding: 15px;
        border-radius: 12px;
        border: 2px solid #fbc02d;
        margin-bottom: 20px;
    }
    .stButton>button {
        background-color: #e3f2fd !important;
        border-radius: 8px;
        font-weight: bold;
        width: 100%;
        height: 50px;
        font-size: 1.2rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心助教語音 (iPad 專用強效 Base64 方案) ---
async def generate_voice_base64(text):
    # 移除 LaTeX 與特殊字符，將 % 唸成「百分之」
    clean_text = re.sub(r'\$+', '', text)
    clean_text = clean_text.replace('\\%', '百分之').replace('%', '百分之')
    clean_text = clean_text.replace('*', '').replace('#', '').replace('\n', ' ')
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    # 轉為 Base64 字串，徹底解決 iPad 報錯問題
    b64 = base64.b64encode(audio_data).decode()
    return f'<audio controls autoplay style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'

# --- 3. 雲端截圖功能 ---
def get_pdf_page_image(pdf_path, page_index):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_index)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # 高清渲染
    img_data = pix.tobytes("png")
    doc.close()
    return img_data

# --- 4. 72 頁熱血中二標題 (不偷懶全開版) ---
page_titles = {
    1: "【禁忌的儀式：科學方法與變因】", 2: "【因果變律：實驗安全規範】", 3: "【平衡律：測量與天平操作】", 4: "【煉金基礎：物質密度奧義】",
    5: "【煉金呼吸：大氣製備禁咒】", 6: "【本質界線：純粹靈魂與混沌】", 7: "【提純程序：過濾與蒸發陣法】", 8: "【溶解契約：飽和溶液的極限】",
    9: "【濃度鎖鍊：質量百分率之理】", 10: "【極限視界：百萬分點 ppm】", 11: "【介質低語：波動與能量傳遞】", 12: "【聲速律法：溫度與震盪】",
    13: "【迴聲空間：距離測量奧義】", 14: "【聽覺統治：樂音三要素】", 15: "【感官外視界：超聲波應用】", 16: "【虛空直線：光的傳播定律】",
    17: "【鏡像世界：反射與虛實界線】", 18: "【歪曲維度：折射與視深現象】", 19: "【光之焦點：凸透鏡成像奧義】", 20: "【散出虛無：凹透鏡與彩虹色散】",
    21: "【視覺修正：眼球與光學儀器】", 22: "【穿透熱能：熱傳導的試煉】", 23: "【能量流轉：對流與輻射禁咒】", 24: "【因果天平：比熱與熱量計算】",
    25: "【微觀平衡：原子構造之謎】", 26: "【地圖導覽：元素週期律】", 27: "【終極天平：質量守恆與莫耳數】", 28: "【絕對計數：阿佛加德羅契約】",
    29: "【變遷權杖：化學反應速率】", 30: "【因果殺陣：氧化還原爭戰】", 31: "【離子覺醒：解離說與電解質】", 32: "【烈焰交鋒：酸鹼性質與試煉】",
    33: "【色澤密碼：pH值與指示劑】", 34: "【聖戰餘韻：酸鹼中和與鹽類】", 35: "【結晶真理：生活中常見鹽類】", 36: "【禁斷界線：有機化合物起源】",
    37: "【奔流結構：烴類與化石燃料】", 38: "【香氣連鎖：酯化反應奧義】", 39: "【長鏈囚籠：聚合物與塑膠】", 40: "【界面生死鬥：皂化與界面活性】",
    41: "【平衡結界：力之三要素與合力】", 42: "【彈性律法：虎克與比例契約】", 43: "【運動終焉：摩擦力與正向力】", 44: "【重壓深淵：壓力的定義與帕斯卡】",
    45: "【液態威壓：連通管與液壓規律】", 46: "【真空挑戰：托里切利與大氣壓力】", 47: "【排水奧義：阿基米德浮力秘術】", 48: "【時空座標：位置、位移與路徑】",
    49: "【動態規律：速度與速率之別】", 50: "【加速度覺醒：等加速度運動】", 51: "【第一律法：慣性與牛頓之魂】", 52: "【絕對方程式：F=ma 的力量】",
    53: "【宿命反擊：作用與反作用力】", 54: "【圓周輪迴：向心力與萬有引力】", 55: "【時空軌跡：功與功率的獻祭】", 56: "【位能幻化：重力場下的能量】",
    57: "【永恆總量：力學能守恆定律】", 58: "【力矩平衡：槓桿原理的支點】", 59: "【機械魔法：滑輪與定滑輪】", 60: "【省力契約：斜面、螺旋與輪軸】",
    61: "【庫倫禁令：靜電感應與引力】", 62: "【電勢之戰：電流、電壓與伏特】", 63: "【電阻枷鎖：歐姆定律的秩序】", 64: "【瓦特之翼：電功與瞬時能量】",
    65: "【焦耳毀滅：家用電路與安全】", 66: "【無形指向：磁場線與磁極】", 67: "【靈魂契約：鋅銅電池奧義】", 68: "【強制異變：電鍍祕術之理】",
    69: "【磁魂覺醒：安培右手定則】", 70: "【勞倫茲之怒：右手開掌定則】", 71: "【旋轉輪迴：直流電動機契約】", 72: "【發電機覺醒：法拉第感應與冷次】"
}

# --- 5. 初始化 Session ---
if 'audio_html' not in st.session_state: st.session_state.audio_html = None

# --- 6. 通行證指南 ---
st.title("🥤 理化 AI 雞排珍奶實驗室 (助教版)")
st.markdown("""
<div class="guide-box">
    <b>📖 學生快速通行指南：</b><br>
    1. 點擊連結：<a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a> 並登入。<br>
    2. 點擊 <b>Create API key</b>，<b>務必勾選兩次同意條款</b>後按產生。<br>
    3. 複製金鑰，貼回下方「通行證」欄位即可啟動。
</div>
""", unsafe_allow_html=True)

user_key = st.text_input("🔑 通行證輸入區：", type="password")
st.divider()

# --- 7. 學生提問區 ---
st.subheader("💬 學生提問專區：拍照或打字問問題")
col_q, col_up = st.columns([1, 1])
with col_q: student_q = st.text_input("輸入問題：", placeholder="例如：什麼是比熱？")
with col_up: uploaded_file = st.file_uploader("拍照上傳：", type=["jpg", "png", "jpeg"])

if (student_q or uploaded_file) and user_key:
    with st.spinner("正在調製波霸奶茶並思考答案..."):
        try:
            genai.configure(api_key=user_key)
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            prompt_parts = ["你是資深理化 AI 助教。請用雞排配大杯珍奶解釋。公式使用 LaTeX。"]
            if uploaded_file: prompt_parts.append(Image.open(uploaded_file))
            if student_q: prompt_parts.append(f"學生問題：{student_q}")
            res = model.generate_content(prompt_parts)
            st.info(f"💡 助教解答：\n\n{res.text}")
        except Exception as e: st.error(f"思考失敗：{e}")

st.divider()

# --- 8. 五大門派雙選單 (72 頁全開) ---
st.subheader("📖 真理之書：選擇學習單元")
parts_list = ["【第一門：物質初探】", "【二：能量流轉】", "【三：微觀審判】", "【四：力學秘術】", "【五：旋轉輪迴】"]
part_choice = st.selectbox("第一步：選擇大章節", parts_list)

if "第一門" in part_choice: r = range(1, 16)
elif "二" in part_choice: r = range(16, 27)
elif "三" in part_choice: r = range(27, 41)
elif "四" in part_choice: r = range(41, 55)
else: r = range(55, 73)

options = [f"第 {p} 頁：{page_titles.get(p, '單元重點')}" for p in r]
selected_page_str = st.selectbox("第二步：選擇精確單元名稱 (不跳頁)", options)
target_page = int(re.search(r"第 (\d+) 頁", selected_page_str).group(1))

if st.button(f"🚀 啟動【第 {target_page} 頁】圖文導讀"):
    if not user_key:
        st.warning("請先輸入通行證。")
    else:
        genai.configure(api_key=user_key)
        path_finals = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        with st.spinner("正在調製波霸奶茶..."):
            try:
                # 1. 雲端截圖
                page_img = get_pdf_page_image(path_finals, target_page - 1)
                st.image(page_img, caption=f"講義第 {target_page} 頁：{page_titles[target_page]}", use_column_width=True)
                
                # 2. AI 講解 (講義優先)
                file_obj = genai.upload_file(path=path_finals)
                model = genai.GenerativeModel('models/gemini-2.5-flash')
                prompt = [
                    file_obj,
                    f"你是資深理化 AI 助教。1. 請針對講義第 {target_page} 頁內容進行精確導讀。"
                    f"2. **【核心任務】**：優先詳細講解該頁面上的所有『例題』與計算步驟。"
                    "3. 開場白請生活化，提到『雞排配大杯珍奶』。說各位同學好！今天助教感冒沙啞。"
                    "4. 公式如 $n=m/M$ 與化學式必須使用 LaTeX。絕對不准出測驗題。"
                ]
                res = model.generate_content(prompt)
                st.markdown(res.text)
                
                # 3. iPad 專用 Base64 音訊播放
                st.session_state.audio_html = asyncio.run(generate_voice_base64(res.text))
                st.balloons()
            except Exception as e: st.error(f"導讀失敗：{e}")

# --- 9. iPad 音訊手動解鎖區 ---
if st.session_state.audio_html:
    st.markdown("---")
    st.info("🔊 **平板教學提醒**：請點擊下方播放鈕，聽取 AI 助教導讀內容。")
    st.markdown(st.session_state.audio_html, unsafe_allow_html=True)