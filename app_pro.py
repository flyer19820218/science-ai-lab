import streamlit as st
import google.generativeai as genai
import os
import asyncio
import edge_tts
import io
import re
from PIL import Image

# --- 1. 頁面配置 (翩翩體、全黑文字、適應行動端) ---
st.set_page_config(page_title="理化 AI 手搖飲實驗室", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="css"], .stMarkdown, p, h1, h2, h3, span, label, li {
        color: #000000 !important;
        font-family: 'HanziPen SC', '翩翩體', 'KaiTi', sans-serif !important;
    }
    .guide-box {
        background-color: #f1f8e9;
        padding: 15px;
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
        font-size: 1.1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心助教語音 (HsiaoChen 穩定版) ---
async def generate_voice(text):
    # 移除 LaTeX 符號，確保 HsiaoChen 老師唸得通順
    clean_text = re.sub(r'\$+', '', text)
    clean_text = clean_text.replace('\\%', '百分之').replace('%', '百分之')
    clean_text = clean_text.replace('*', '').replace('#', '').replace('\n', ' ')
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- 3. 講義 72 頁精確標題 (老師，這次絕對不偷懶，一頁不少！) ---
page_titles = {
    1: "禁忌的儀式與因果變律", 2: "實驗室安全規範", 3: "測量與天平操作", 4: "物質特徵：密度奧義",
    5: "大氣製備：氮、氧、二氧化碳", 6: "純物質與混合物的界線", 7: "粗鹽精製：過濾與蒸發", 8: "溶解度與飽和溶液律法",
    9: "重量百分率濃度計算", 10: "百萬分點 (ppm) 特殊濃度", 11: "波動的低語與介質傳遞", 12: "聲速與溫度的關係",
    13: "迴聲測距與反射規律", 14: "樂音三要素：響度、音調、音色", 15: "超聲波與波的應用", 16: "光的傳播與針孔成像",
    17: "反射定律與平面鏡成像", 18: "折射定律與視深現象", 19: "凸透鏡成像規律 (重點！)", 20: "凹透鏡與色散實驗",
    21: "眼球構造與視力矯正", 22: "熱量的流轉：熱傳導", 23: "熱對流與熱輻射契約", 24: "比熱的試煉與計算",
    25: "原子構造與離子契約", 26: "元素週期表導覽", 27: "質量守恆與莫耳數計數", 28: "阿佛加德羅常數應用",
    29: "反應速率的四大權杖", 30: "氧化還原的因果殺陣", 31: "解離說與電解質導電", 32: "酸與鹼的烈焰交鋒",
    33: "pH 值與指示劑密碼", 34: "酸鹼中和與熱能覺醒", 35: "生活鹽類與結晶真理", 36: "有機與無機的禁斷界線",
    37: "烴類的奔流與結構", 38: "酯化反應：香氣的連鎖", 39: "聚合物之魂：塑膠神話", 40: "皂化反應與界面活性劑",
    41: "力之三要素與平衡結界", 42: "虎克定律：彈性律法", 43: "摩擦力與運動的終焉", 44: "壓力試煉：帕斯卡原理",
    45: "液體壓強與連通管", 46: "大氣壓力：托里切利試驗", 47: "浮力秘術：阿基米德奧義", 48: "座標、位移與路徑長",
    49: "速度與速率的動態規律", 50: "加速度與等加速運動", 51: "慣性：第一運動定律", 52: "F=ma：第二運動定律",
    53: "作用與反作用力：第三定律", 54: "圓周運動與萬有引力", 55: "功與功率的時空軌跡", 56: "位能與動能的幻化",
    57: "力學能守恆與轉換", 58: "槓桿原理與力矩平衡", 59: "滑輪組：省力魔法", 60: "斜面、螺旋與輪軸",
    61: "靜電感應與庫倫引力", 62: "電勢、電壓與伏特之戰", 63: "歐姆定律與電阻枷鎖", 64: "電功與瓦特之翼",
    65: "焦耳熱與家用電路安全", 66: "磁場線與磁極指向", 67: "鋅銅電池：靈魂契約", 68: "電鍍祕術：強制異變",
    69: "安培右手定則：磁魂", 70: "右手開掌定則：洛倫茲力", 71: "直流電動機：旋轉輪迴", 72: "法拉第冷次定律：發電機"
}

# --- 4. 初始化 Session State ---
if 'api_ready' not in st.session_state: st.session_state.api_ready = False
if 'quiz_data' not in st.session_state: st.session_state.quiz_data = None
if 'audio_data' not in st.session_state: st.session_state.audio_data = None

# --- 5. 快速 API 指南 (勾選兩次版) ---
st.title("🔬 理化 AI 手搖飲實驗室 (全球旗艦版)")
st.markdown("""
<div class="guide-box">
    <b>各位同學好！請取得 AI 通行證：</b><br>
    點擊 <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a> 登入，點擊 <b>Create API key</b>，<b>勾選兩次同意</b>並產生，再貼回下方。
</div>
""", unsafe_allow_html=True)

user_key = st.text_input("🔑 在這裡貼上你的通行證：", type="password")
if user_key:
    try:
        genai.configure(api_key=user_key)
        st.session_state.api_ready = True
        st.success("✅ 通行證驗證成功！")
    except:
        st.error("❌ 金鑰錯誤。")

st.divider()

# --- 6. 五大部分雙階層選單 (修復邏輯 Bug) ---
st.subheader("🥤 自主學習區：選擇單元章門")

parts_list = [
    "【第一門：物質的密語與純化】 (p.1-15)",
    "【第二門：時空的震盪與能量】 (p.16-26)",
    "【第三門：微觀的審判與有機】 (p.27-40)",
    "【第四門：重壓的試煉與浮沉】 (p.41-54)",
    "【第五門：因果的追逐與旋轉】 (p.55-72)"
]
part_choice = st.selectbox("第一步：選擇大章門", parts_list)

# 根據選擇的字串精確映射範圍
if "第一門" in part_choice: current_range = range(1, 16)
elif "第二門" in part_choice: current_range = range(16, 27)
elif "第三門" in part_choice: current_range = range(27, 41)
elif "第四門" in part_choice: current_range = range(41, 55)
else: current_range = range(55, 73)

options = [f"第 {p} 頁：{page_titles[p]}" for p in current_range]
selected_page_str = st.selectbox("第二步：選擇精確單元頁碼", options)
target_page = int(re.search(r"第 (\d+) 頁", selected_page_str).group(1))

if st.button(f"🚀 啟動【第 {target_page} 頁】導讀內容"):
    if not st.session_state.api_ready:
        st.warning("請先輸入通行證。")
    else:
        path_finals = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        path_bank = os.path.join(os.getcwd(), "data", "Huikao_Bank.pdf")
        
        if os.path.exists(path_finals):
            with st.spinner(f"正在連動講義與十年題庫中..."):
                try:
                    files_to_upload = [genai.upload_file(path=path_finals)]
                    if os.path.exists(path_bank):
                        files_to_upload.append(genai.upload_file(path=path_bank))
                    
                    model = genai.GenerativeModel('models/gemini-2.5-flash')
                    
                    # 雙檔聯動指令：強制鎖定 LaTeX 與 HsiaoChen 教學風格
                    prompt_text = files_to_upload + [
                        f"你是有 20 年資歷的理化老師。請根據第一個檔案第 {target_page} 頁教學。"
                        "1. 教學內容必須嚴格對齊講義數據。開場說：各位同學好！歡迎來到理化教室。"
                        "2. 使用手搖飲珍珠情境，公式如 $n = m / M$ 必須使用 LaTeX。"
                        "3. 特別注意百分比濃度公式，寫成 $$V\\% = \\left( \\frac{\\text{溶質體積}}{\\text{溶液體積}} \\right) \\times 100\\%$$。"
                        "4. 如果有第二個檔案(題庫)，請搜尋 1-2 題與該單元相關的『歷屆會考真題』。"
                        "5. 結尾用標籤 '[QUIZ_DATA]' 分隔，包含題目、選項、正確字母、引導提示。"
                        "6. 提醒多喝溫水。"
                    ]
                    
                    response = model.generate_content(prompt_text)
                    full_text = response.text
                    
                    parts = full_text.split("[QUIZ_DATA]")
                    st.markdown(parts[0])
                    
                    # 生成音訊 (準備好供點擊)
                    st.session_state.audio_data = asyncio.run(generate_voice(parts[0]))
                    if len(parts) > 1: st.session_state.quiz_data = parts[1]
                    st.balloons()
                except Exception as e:
                    st.error(f"連線失敗：{e}")
        else:
            st.error("找不到講義檔案。")

# --- 7. 手機/平板音訊解鎖區 (關鍵修復) ---
if st.session_state.audio_data:
    st.markdown("---")
    st.info("💡 **行動裝置小提醒**：為了聽見 HsiaoChen 老師的聲音，請點擊下方播放鈕解鎖音訊。")
    st.audio(st.session_state.audio_data, format="audio/mp3")

# --- 8. 歷屆會考真題問答區 ---
if st.session_state.quiz_data:
    st.divider()
    st.subheader("📝 歷屆會考挑戰題 (引導式思考)")
    quiz_raw = st.session_state.quiz_data
    st.markdown(quiz_raw.split("正確")[0])
    
    student_ans = st.radio("你的解答：", ["A", "B", "C", "D"], key="active_q")
    
    if st.button("送出解答"):
        correct_match = re.search(r"正確[選項|字母][：:\s]*([A-D])", quiz_raw)
        hint_match = re.search(r"提示[：:\s]*(.*)", quiz_raw)
        correct_ans = correct_match.group(1).strip() if correct_match else "A"
        hint_txt = hint_match.group(1).strip() if hint_match else "再想一下這頁的重點喔！"
        
        if student_ans == correct_ans:
            st.success(f"🎯 答對了！你掌握了會考必考的知識點。")
            st.balloons()
        else:
            st.error(f"❌ 答錯了！ HsiaoChen 老師提示：{hint_txt}")