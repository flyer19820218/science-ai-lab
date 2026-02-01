import streamlit as st
import google.generativeai as genai
import os
import asyncio
import edge_tts
import io
import re
from PIL import Image

# --- 1. 頁面配置 (全黑文字、翩翩體、符合平板寬度) ---
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
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心助教語音 (HsiaoChen 穩定版) ---
async def generate_voice(text):
    # 清理 LaTeX 以免語音亂唸
    clean_text = re.sub(r'\$+', '', text)
    clean_text = clean_text.replace('\\%', '百分之').replace('%', '百分之')
    clean_text = clean_text.replace('*', '').replace('#', '').replace('\n', ' ')
    communicate = edge_tts.Communicate(clean_text, "zh-TW-HsiaoChenNeural", rate="-2%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- 3. 初始化 Session State ---
if 'api_ready' not in st.session_state: st.session_state.api_ready = False
if 'quiz_data' not in st.session_state: st.session_state.quiz_data = None
if 'audio_data' not in st.session_state: st.session_state.audio_data = None

# --- 4. 講義標題對照表 (1-72 頁) ---
page_titles = {
    1: "【探索的起點⸺禁忌的儀式與因果變律】", 2: "實驗室安全與科學方法", 3: "測量、誤差與天平使用", 4: "物質的特徵：密度★",
    5: "【大氣的禁咒：氮氧交織的煉金呼吸】", 6: "【本質的界線：純粹靈魂與混沌物質】", 7: "【真理的提純：粗鹽精製的精粹程序】",
    8: "【深淵的極限：靈魂容器的溶解度律法】", 9: "【濃縮的真理：質量守恆下的百分比鎖鍊】", 10: "【微影的低語：百萬分點下的極限視界】",
    11: "【振盪的初源：介質與能量的傳遞契約】", 12: "【大氣的音階：溫標下的聲速律法】", 13: "【命運的折返：迴聲空間的距離測量】",
    14: "【頻率的律法：樂音三要素的聽覺統治】", 15: "【波形的靈魂：超聲波與感官外的視界】", 16: "【穿梭虛空的直線：光的傳播與陰影法則】",
    17: "【鏡像的平回世界：反射定律與虛實界線】", 18: "【歪曲的維度：折射定律下的視錯覺】", 19: "【匯聚的光之焦點：凸透鏡的成像奧義】",
    20: "【散出的虛無：凹透鏡與色散的彩虹】", 21: "【視覺的修正：眼球構造與光學儀器】", 22: "【能量的流轉：穿透虛空的熱傳導陣法】",
    23: "【物質的幻化：熔點與沸點間的潛熱禁咒】", 24: "【熱能的刻印：熱量、比熱與因果天平】", 25: "【微觀的平衡：原子核外的離子契約】",
    26: "元素週期表：文字導覽地圖", 27: "【等價的轉化：質量守恆的終極天平】", 28: "【數量的意志：莫耳靈魂的絕對計數】",
    29: "【混沌的變遷：反應速率的四大權杖】", 30: "【奪氧的爭戰：氧化還原的因果殺陣】", 31: "【離子的覺醒：解離與電解質的導電規律】",
    32: "【酸與鹼的烈焰：腐蝕與化學性質的交鋒】", 33: "【萬物的量尺：pH值與指示劑的色澤密碼】", 34: "【中和的聖戰：水分子生成的熱能覺醒】",
    35: "【鹽類的餘韻：碳酸鹽與生活中的結晶真理】", 36: "【碳魂的起源：有機與無機的禁斷界線】", 37: "【烴類的奔流：化石燃料與鏈狀結構的鏈鎖】",
    38: "【酯化的香氣：醇、酸與分子間的連鎖反應】", 39: "【長鏈的囚籠：聚合物的結構與塑膠的神話】", 40: "【垢淨的代價：皂化反應與界面的生死鬥】",
    41: "【重力的牽引：力之三要素與平衡結界】", 42: "【彈性的契约：虎克與比例的絕對律法】", 43: "【阻力的纏繞：摩擦力與運動的終焉】",
    44: "【接觸的真相：帕斯卡與重壓的深淵】", 45: "【液態的威壓：連通管與深海的壓強律法】", 46: "【大氣的重量：馬德堡與托里切利的真空挑戰】",
    47: "【浮空的秘術：阿基米德與排水的奧義】", 48: "【時空的軌跡：位置、位移與路徑長的座標】", 49: "【瞬移的節奏：速度、速率與圖形的動態規律】",
    50: "【疾速的覺醒：加速度與等加速的絕對變化】", 51: "【萬物的固執：慣性與第一動態律法】", 52: "【力與質量的共鳴：加速度的絕對方程式】",
    53: "【因果的反擊：作用與反作用的宿命】", 54: "【圓周的輪迴：向心力與萬有引力的禁錮】", 55: "【能量的獻祭：功與功率的時空軌跡】",
    56: "【位能與動能的幻化：重力場下的能量覺醒】", 57: "【永恆的總量：能量守恆與力學能轉換】", 58: "【支點的支撐：槓桿原理與力矩的平衡】",
    59: "【鏈條的鏈鎖：定滑輪與動滑輪的機械魔法】", 60: "【坡道的延展：斜面與輪軸的省力契約】", 61: "【琥珀的囚籠：靜電感應與庫倫引力的禁斷律法】",
    62: "【電荷的奔流：安培與伏特的電勢之戰】", 63: "【阻絕的屏障：歐姆定律與電阻的物質枷鎖】", 64: "【能量的獻祭：電功與瓦特之翼的瞬時爆發】",
    65: "【凡間的雷霆：家用電路與焦耳熱的毀滅秩序】", 66: "【兩極的宿命：磁場線與北極星的無形指向】", 67: "【鋅銅電池：靈魂契約】",
    68: "【電鍍：強制異變的祕術】", 69: "【螺旋的感應：安培右手定則與電磁之魂】", 70: "【偏向的力場：右手開掌定則與勞倫茲的怒】",
    71: "【旋轉的輪迴：直流電動機與能量轉化的契約】", 72: "【虛空的湧現：法拉第冷次定律與發電機的覺醒】"
}

# --- 5. 學生快速指南 ---
st.title("🔬 理化 AI 手搖飲實驗室 (全球旗艦版)")
st.markdown("""
<div class="guide-box">
    <b>各位同學好！請取得 AI 通行證：</b><br>
    點擊 <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio</a> 登入後，點擊 <b>Create API key</b>，勾選兩次同意並產生，再貼回下方。
</div>
""", unsafe_allow_html=True)

user_key = st.text_input("🔑 在這裡貼上你的通行證：", type="password")
if user_key:
    try:
        genai.configure(api_key=user_key)
        st.session_state.api_ready = True
        st.success("✅ 通行證驗證成功！")
    except:
        st.error("❌ 金鑰格式錯誤。")

st.divider()

# --- 6. 五大部分雙階層選單 ---
st.subheader("🥤 自主學習區：選擇單元章門")

part_choice = st.selectbox("第一步：選擇大章門", [
    "【第一門：物質的密語】 (p.1-15)", "【第二門：時空的震盪】 (p.16-26)",
    "【第三門：微觀的審判】 (p.27-40)", "【第四門：重壓的試煉】 (p.41-54)",
    "【第五門：因果的追逐】 (p.55-72)"
])

# 映射邏輯
range_map = {"一": range(1, 16), "二": range(16, 27), "三": range(27, 41), "四": range(41, 55), "五": range(55, 73)}
current_range = range_map[part_choice[1]]
options = [f"第 {p} 頁：{page_titles[p]}" for p in current_range]
selected_page_str = st.selectbox("第二步：選擇精確單元頁碼", options)
target_page = int(re.search(r"第 (\d+) 頁", selected_page_str).group(1))

if st.button(f"🚀 啟動【第 {target_page} 頁】導讀與會考真題"):
    if not st.session_state.api_ready:
        st.warning("請先輸入通行證。")
    else:
        path_finals = os.path.join(os.getcwd(), "data", "Ph_Ch_finals.pdf")
        path_bank = os.path.join(os.path.join(os.getcwd(), "data", "Huikao_Bank.pdf"))
        
        if os.path.exists(path_finals):
            with st.spinner(f"正在連動講義與十年題庫中..."):
                try:
                    files_to_upload = [genai.upload_file(path=path_finals)]
                    if os.path.exists(path_bank):
                        files_to_upload.append(genai.upload_file(path=path_bank))
                    
                    model = genai.GenerativeModel('models/gemini-2.5-flash')
                    
                    # 雙檔聯動指令
                    prompt_text = files_to_upload + [
                        f"你是有 20 年資歷的理化老師。1. 根據第一個檔案第 {target_page} 頁進行精確教學。"
                        "2. 使用手搖飲珍珠情境，公式與化學式必須嚴格使用 LaTeX。"
                        "3. 如果有第二個檔案（題庫），請從中搜尋 1-2 題與該單元相關的『歷屆會考真題』。"
                        "4. 結尾用標籤 '[QUIZ_DATA]' 分隔，包含題目、選項、正確字母、引導提示。"
                        "5. 最後提醒多喝溫水。"
                    ]
                    
                    response = model.generate_content(prompt_text)
                    full_text = response.text
                    
                    parts = full_text.split("[QUIZ_DATA]")
                    st.markdown(parts[0])
                    
                    # 準備音訊 (不自動播放，供手動點擊)
                    st.session_state.audio_data = asyncio.run(generate_voice(parts[0]))
                    if len(parts) > 1: st.session_state.quiz_data = parts[1]
                    st.balloons()
                except Exception as e:
                    st.error(f"連線失敗：{e}")
        else:
            st.error("找不到核心講義檔案。")

# --- 7. 手機/平板音訊解鎖區 ---
if st.session_state.audio_data:
    st.info("💡 小朋友請點擊下方播放鈕，聽老師講解：")
    st.audio(st.session_state.audio_data, format="audio/mp3")

# --- 8. 歷屆會考真題互動區 ---
if st.session_state.quiz_data:
    st.divider()
    st.subheader("📝 歷屆會考挑戰題 (引導式問答)")
    quiz_raw = st.session_state.quiz_data
    st.markdown(quiz_raw.split("正確")[0])
    
    student_ans = st.radio("你的解答：", ["A", "B", "C", "D"], key="active_q")
    
    if st.button("送出解答"):
        correct_match = re.search(r"正確[選項|字母][：:\s]*([A-D])", quiz_raw)
        hint_match = re.search(r"提示[：:\s]*(.*)", quiz_raw)
        correct_ans = correct_match.group(1).strip() if correct_match else "A"
        hint_txt = hint_match.group(1).strip() if hint_match else "再想一下這頁的重點喔！"
        
        if student_ans == correct_ans:
            st.success(f"🎯 答對了！這題就是會考考過的重點。")
        else:
            st.error(f"❌ 哎呀，再想想！老師的小提示：{hint_txt}")