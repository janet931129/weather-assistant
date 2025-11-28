# weather_app.py
import streamlit as st
import requests
import google.generativeai as genai

st.set_page_config(page_title="天氣通知小助理 Demo", layout="centered")
st.title("🌞 天氣通知小助理 Demo")
st.caption("CWA 天氣資訊 結合 Gemini LLM")

CWA_KEY = st.secrets.get("CWA_API_KEY")
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY")

# === 取得最新天氣預報 ===
def fetch_latest_weather():
    if not CWA_KEY:
        return {"error": "❌ CWA API Key 未設定"}

    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
    params = {
        "Authorization": CWA_KEY,
        "locationName": "臺北市",
        "limit": 1
    }

    try:
        resp = requests.get(url, params=params, timeout=10)  # 關閉 SSL 驗證
        resp.raise_for_status()
        data = resp.json()

        locations = data.get("records", {}).get("locations", [])
        if not locations:
            return {"error": "⚠️ 沒有資料"}

        return locations[0]
    except Exception as e:
        return {"error": f"API 錯誤: {e}"}

# === Gemini 生成摘要 ===
def call_gemini(text):
    if not GEMINI_KEY:
        return "❌ Gemini API Key 未設定"

    genai.configure(api_key=GEMINI_KEY)

    try:
        model = "models/text-bison-001"
        prompt = f"""請用溫柔、親切的語氣摘要以下天氣資訊：

{text}"""
        response = genai.generate_text(model=model, prompt=prompt)
        return response.text
    except Exception as e:
        return f"Gemini 錯誤：{e}"

# === Streamlit UI ===
if st.button("📡 取得最新天氣 + Gemini 摘要"):
    with st.spinner("正在抓取 CWA 天氣資料..."):
        data = fetch_latest_weather()

    st.subheader("📄 最新天氣原始資料（整理後）")
    st.write(data)

    if "error" not in data:
        # 整理重點欄位
        location = data.get("locationName", "")
        weather_elements = data.get("weatherElement", [])
        clean_text = {}
        for element in weather_elements:
            name = element.get("elementName")
            times = element.get("time", [])
            if times:
                clean_text[name] = times[0].get("parameter", {}).get("parameterName")

        with st.spinner("Gemini 正在生成摘要..."):
            summary = call_gemini(clean_text)

        st.subheader("🤖 Gemini 溫柔摘要")
        st.write(summary)
