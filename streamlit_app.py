import streamlit as st
import requests
import google.generativeai as genai
import pandas as pd

# === Streamlit 基本設定 ===
st.set_page_config(page_title="🌞 全台天氣資訊 DashBoard", layout="centered")
st.title("🌞 全台天氣資訊 DashBoard")
st.caption("CWA 全台天氣資料與 Gemini LLM 整合")

# === API Key 設定 ===
CWA_KEY = st.secrets["CWA_API_KEY"]
GEMINI_KEY = st.secrets["GEMINI_API_KEY"]

# === 取得所有城市天氣預報 ===
def fetch_all_weather():
    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
    params = {"Authorization": CWA_KEY}
    try:
        resp = requests.get(url, params=params, timeout=10, verify=False)
        resp.raise_for_status()
        data = resp.json()
        return data.get("records", {}).get("location", [])
    except Exception as e:
        return {"error": f"API 錯誤: {e}"}

# === Gemini 生成摘要 ===
def call_gemini(text):
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-2.5-pro")
    prompt = f"""請用溫柔、親切的語氣摘要以下天氣資訊，並加上一句溫和的問候：\n\n{text}"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Gemini 錯誤：{e}"

# === 主流程 - 預先載入資料 ===
with st.spinner("正在抓取中央氣象署天氣資料…"):
    data = fetch_all_weather()

if isinstance(data, dict) and "error" in data:
    st.error(data["error"])
    st.stop()

# === 整理為資料表 + 詳細字典 ===
rows = []
details = {}

for loc in data:
    location = loc.get("locationName", "")
    weather_elements = loc.get("weatherElement", [])

    min_temps = []
    max_temps = []
    wx_list = []

    for element in weather_elements:
        name = element.get("elementName")
        times = element.get("time", [])

        for t in times:
            val = t.get("parameter", {}).get("parameterName")

            if name == "Wx" and val:
                wx_list.append(val)

            if val and val.isdigit():
                val = int(val)
                if name == "MinT":
                    min_temps.append(val)
                elif name == "MaxT":
                    max_temps.append(val)

    rows.append({
        "城市": location,
        "最低溫": min(min_temps) if min_temps else None,
        "最高溫": max(max_temps) if max_temps else None
    })

    details[location] = {
        "最低溫": min(min_temps) if min_temps else None,
        "最高溫": max(max_temps) if max_temps else None,
        "天氣描述": wx_list[0] if wx_list else "N/A"
    }

df = pd.DataFrame(rows)

# === 城市下拉選單（永遠顯示） ===
st.subheader("查詢城市天氣")

city = st.selectbox("選擇城市", df["城市"].tolist())
info = details[city]

st.info(
    f"🔥 最高溫: {info['最高溫']}°C\n"
    f"❄️ 最低溫: {info['最低溫']}°C\n"
    f"☁️ 天氣狀況: {info['天氣描述']}"
)

# === 按鈕：生成 Gemini 摘要（放在下拉選單後面） ===
if st.button("👩‍💼即時氣象主播（生成摘要）"):
    with st.spinner("Gemini 正在生成摘要…"):
        summary = call_gemini(df.to_dict(orient="records"))

    # === 白色、有框、有陰影的摘要卡片 ===
    st.markdown(
        f"""
        <div style="
            background-color: white;
            padding: 20px;
            margin-top: 15px;
            border-radius: 10px;
            border: 1px solid #DDD;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            ">
            <p style="font-size:16px; line-height:1.6;">
                {summary}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
