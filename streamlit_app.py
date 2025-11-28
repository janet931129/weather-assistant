import streamlit as st
import requests
import google.generativeai as genai

st.set_page_config(page_title="天氣預報小助理 Demo", layout="centered")

st.title("☀️ 天氣預報小助理 Demo")
st.caption("CWA 一般天氣預報資料 + Gemini LLM 智慧摘要")

CWA_KEY = st.secrets.get("CWA_API_KEY")
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY")

# === CWA Weather API ===
def fetch_weather():
    if not CWA_KEY:
        return {"error": "❌ CWA API key 未設定"}

    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
    params = {"Authorization": CWA_KEY, "locationName": "臺北市"}

    try:
        resp = requests.get(url, params=params, timeout=10, verify=False)
        resp.raise_for_status()
        data = resp.json()

        if data.get("success") != "true":
            return {"error": "❌ CWA 回傳資料錯誤"}

        return data["records"]["location"][0]

    except Exception as e:
        return {"error": f"API 錯誤: {e}"}


# === Gemini Summary ===
def call_gemini(weather):
    if not GEMINI_KEY:
        return "❌ Gemini API Key 未設定"

    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-pro")

    try:
        prompt = f"""
你是一位溫柔親切的小助理，請以簡單、安撫、體貼的語氣摘要臺北市未來 36 小時天氣：

{weather}

請用條列式摘要並補上一句關心的提醒，例如「記得帶傘喔！」或「注意溫度變化」。"""

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"Gemini 錯誤：{e}"


# === UI ===
if st.button("🌤 取得天氣預報 + Gemini 摘要"):
    with st.spinner("正在取得最新天氣資料..."):
        weather_data = fetch_weather()

    st.subheader("📄 來自 CWA 的天氣預報（整理後）")
    st.write(weather_data)

    if "error" not in weather_data:
        with st.spinner("Gemini 正在生成摘要..."):
            summary = call_gemini(weather_data)

        st.subheader("🤖 Gemini 溫柔摘要")
        st.write(summary)
