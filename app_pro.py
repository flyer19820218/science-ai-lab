import streamlit as st
import google.generativeai as genai
import os
import asyncio
import edge_tts
import io
import re
from PIL import Image

# --- 1. 頁面配置 (全黑文字、翩翩體、適應平板) ---
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
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心助教語音 (HsiaoChen 穩定版) ---
async def generate_voice(text):
    # 移除 LaTeX 符號，確保語音平順
    clean_text = re.sub(r'\$+', '', text)
    clean_text = clean_text.replace('\\%', '百分之').replace('%', '百分之')
    clean_text = clean_text.replace('*', '').replace('#', '').replace('\n', ' ')
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- 3. 講義 72 頁完整目錄 (不偷懶全開版) ---
page_titles = {
    1: "科學方法與變因判斷", 2: "實驗室安全規範", 3: "測量與天平操作", 4: "物質特徵：密度",
    5: "大氣製備：氮、氧、二氧化碳", 6: "純物質與混合物", 7: "粗鹽精製：過濾與蒸發", 8: "溶解度與飽和溶液",
    9: "重量百分率濃度", 10: "百萬分點 (ppm)", 11: "波動與介質傳遞", 12: "聲速與溫度關係",
    13: "迴聲測距與反射", 14: "樂音三要素", 15: "超聲波與應用", 16: "光的傳播與針孔成像",
    17: "反射定律與平面鏡", 18: "折射定律與視深", 19: "凸透鏡成像規律", 20: "凹透鏡與色散",
    21: "眼球構造與矯正", 22: "熱量的流轉：熱傳導", 23: "熱對流與熱輻射", 24: "比熱與熱量計算",
    25: "原子構造與離子", 26: "元素週期表導覽", 27: "質量守恆與莫耳數", 28: "莫耳絕對計數",
    29: "化學反應速率", 30: "氧化還原反應", 31: "解離說與電解質", 32: "酸與鹼的特性",
    33: "pH 值與指示劑", 34: "酸鹼中和反應", 35: "常見鹽類", 36: "有機化合物簡介",
    37: "烴類的性質", 38: "酯化反應", 39: "聚合物與塑膠", 40: "皂化反應與清潔劑",
    41: "力之三要素", 42: "虎克定律", 43: "摩擦力", 44: "壓力的定義",
    45: "液體壓力與連通管", 46: "大氣壓力測試", 47: "阿基米德浮力原理", 48: "位移與路徑長",
    49: "速度與速率", 50: "加速度運動", 51: "牛頓第一定律", 52: "牛頓第二定律 (F=ma)",
    53: "牛頓第三定律", 54: "萬有引力與圓周運動", 55: "功與功率", 56: "位能與動能",
    57: "力學能守恆", 58: "槓桿原理與力矩", 59: "滑輪的應用", 60: "斜面與機械",
    61: "靜電感應", 62: "電流與電壓", 63: "歐姆定律", 64: "電功與電功率",
    65: "家用電器安全", 66: "磁場與磁力線", 67: "鋅銅電池原理", 68: "電鍍實驗",
    69: "安培右手定則", 70: "右手開掌定則", 71: "直流電動機原理", 72: "法拉第感應與發電機"
}

# --- 4. 初始化 Session ---
if 'audio_data' not in st.session_state: st.session_state.audio_data = None
if 'quiz_data' not in st.session_state: st.session_state.quiz_data = None

# --- 5. 快速 API 指南 ---
st.title("🥤 理化 AI 雞排珍奶實驗室")
st.markdown("""
<div class="guide-box">
    <b>各位同學好！我是 HsiaoChen 老師。</b><br>
    點擊 <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a> 登入，點擊 <b>Create API key</b>，勾選兩次同意並貼回下方即可。
</div>
""", unsafe_allow_html=True)

user_key = st.text_input("🔑 在這裡貼上你的通行證：", type="password")
st.divider()

# --- 6. 五大部分雙階層選單 ---
st.subheader("📖 真理之書：選擇單元章門")

parts_list = [
    "【第一門：物質初探】 (p.1-15)", "【第二門：能量流轉】 (p.16-26)",
    "【第三門：微觀審判】 (p.27-40)", "【第四門：力學秘術】 (p.41-54)",
    "【第五門：旋轉輪迴】 (p.55-72)"
]
part_choice = st.selectbox("第一步：選擇大單元", parts_list)

# 精確映射
if "第一門" in part_choice: current_range = range(1, 16)
elif "第二門" in part_choice: current_range = range(16, 27)
elif "第三門" in part_choice: current_range = range(27, 41)
elif "第四門" in part_choice: current_range = range(41, 55)
else: current_range = range(55, 73)

options = [f"第 {p} 頁：{page_titles.get(p, '內容詳解')}" for p in current_range]
selected_page_str = st.selectbox("第二步：選擇精確頁碼", options)
target_page = int(re.search(r"第 (\d+) 頁", selected_page_str).group(1))

if st.button(f"🚀 啟動【第 {target_page} 頁】導讀與會考真題"):
    if not user_key:
        st.warning("請先輸入通行證。")
    else:
        genai.configure(api_key=user_key)
        path_finals = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        path_bank = os.path.join(os.getcwd(), "data", "Huikao_Bank.pdf")
        
        with st.spinner("正在調製波霸奶茶..."):
            try:
                files = [genai.upload_file(path=path_finals)]
                if os.path.exists(path_bank): files.append(genai.upload_file(path=path_bank))
                
                model = genai.GenerativeModel('models/gemini-2.5-flash')
                prompt = files + [
                    f"你是有 20 年資歷的男理化老師。請根據第一個檔案第 {target_page} 頁教學。"
                    "1. 開場請務必生活化，提到『雞排配大杯珍奶』的小確幸。說各位同學好！今天老師感冒沙啞。"
                    "2. 嚴格根據講義內容。公式如 $$n = m / M$$ 與百分比 $$V\\%$$ 必須使用 LaTeX。"
                    "3. 關於莫耳數，請使用珍珠奶茶的珍珠量來比喻說明。"
                    "4. 教學結束後加標籤 '[QUIZ_DATA]'。請從題庫(第二個檔案)中搜尋 1-2 題與單元相關的『歷屆會考真題』。"
                    "   * 優先選擇『題目長、敘述多』的經典考題。"
                    "   * 若題目含圖，請用文字精確還原圖意描述。"
                    "   * 包含：題目、選項、正確字母、引導提示。"
                ]
                response = model.generate_content(prompt)
                parts = response.text.split("[QUIZ_DATA]")
                st.markdown(parts[0])
                
                # 音訊處理 (平板手動播放)
                st.session_state.audio_data = asyncio.run(generate_voice(parts[0]))
                if len(parts) > 1: st.session_state.quiz_data = parts[1]
                st.balloons()
            except Exception as e:
                st.error(f"連線失敗：{e}")

# --- 7. 平板/手機聲音解鎖區 ---
if st.session_state.audio_data:
    st.info("💡 **小朋友請點擊下方播放鈕**，HsiaoChen 老師就會開始導讀。")
    st.audio(st.session_state.audio_data, format="audio/mp3")

# --- 8. 歷屆會考真題挑戰 ---
if st.session_state.quiz_data:
    st.divider()
    st.subheader("📝 歷屆會考挑戰題")
    quiz_raw = st.session_state.quiz_data
    st.markdown(quiz_raw.split("正確")[0])
    ans = st.radio("你的解答：", ["A", "B", "C", "D"], key="active_q")
    if st.button("送出解答"):
        correct = re.search(r"正確[選項|字母][：:\s]*([A-D])", quiz_raw).group(1)
        hint = re.search(r"提示[：:\s]*(.*)", quiz_raw).group(1)
        if ans == correct: st.success("🎯 答對了！這題就是會考的重點。")
        else: st.error(f"❌ 哎呀，再想想！ HsiaoChen 老師的小提示：{hint}")