import streamlit as st
import requests
import google.generativeai as genai
import certifi
import pandas as pd

# === Streamlit 基本設定 ===
st.set_page_config(page_title="🌥️ 多雲 + API-first Demo", layout="centered")
st.title("🌥️ 多雲 + API-first Demo")
st.caption("CWA 全台天氣資料 + Gemini LLM 整合")

# === API Key 設定 ===
CWA_KEY = "CWA-FCEEAE83-A00B-455B-BD97-208C11A9E5F3"   # 中央氣象署 API Key
GEMINI_KEY = "AIzaSyDJ0Opfq__BMivJ7u3uergg4UeYid03wys" # Google Gemini API Key

# === 取得所有城市天氣預報 ===
def fetch_all_weather():
    if not CWA_KEY:
        return {"error": "❌ CWA API Key 未設定"}

    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
    params = {
        "Authorization": CWA_KEY
    }

    try:
        resp = requests.get(url, params=params, timeout=10, verify=False)
        resp.raise_for_status()
        data = resp.json()

        locations = data.get("records", {}).get("location", [])
        if not locations:
            return {"error": "⚠️ 沒有資料"}

        return locations
    except Exception as e:
        return {"error": f"API 錯誤: {e}"}

# === Gemini 生成摘要 ===
def call_gemini(text):
    if not GEMINI_KEY:
        return "❌ Gemini API Key 未設定"

    genai.configure(api_key=GEMINI_KEY)

    prompt = f"""請用溫柔、親切的語氣摘要以下天氣資訊，並加上一句溫和的問候：

{text}"""

    try:
        model = genai.GenerativeModel("gemini-2.5-pro")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Gemini 錯誤：{e}"

# === Streamlit UI ===
if st.button("📡 取得全台天氣 + Gemini 摘要"):
    with st.spinner("正在抓取 CWA 天氣資料..."):
        data = fetch_all_weather()

    if isinstance(data, dict) and "error" in data:
        st.error(data["error"])
    else:
        # 整理成表格
        rows = []
        for loc in data:
            location = loc.get("locationName", "")
            weather_elements = loc.get("weatherElement", [])
            row = {"城市": location}
            for element in weather_elements:
                name = element.get("elementName")
                times = element.get("time", [])
                if times:
                    row[name] = times[0].get("parameter", {}).get("parameterName")
            rows.append(row)

        df = pd.DataFrame(rows)
        st.subheader("📊 全台天氣整理表格")
        st.dataframe(df)

        # Gemini 摘要
        with st.spinner("Gemini 正在生成摘要..."):
            summary = call_gemini(df.to_dict(orient="records"))

        st.subheader("🤖 Gemini 溫柔摘要")
        st.write(summary)
