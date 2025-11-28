import streamlit as st
import requests
import google.generativeai as genai
import certifi
import pandas as pd

st.set_page_config(page_title="🌥️ 多雲 + API-first Demo", layout="centered")
st.title("🌥️ 多雲 + API-first Demo")
st.caption("CWA 全台天氣資料 + Gemini LLM 整合")

CWA_KEY = "CWA-FCEEAE83-A00B-455B-BD97-208C11A9E5F3"
GEMINI_KEY = "AIzaSyDJ0Opfq__BMivJ7u3uergg4UeYid03wys"

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
    prompt = f"""請用溫柔、親切的語氣摘要以下天氣資訊，並加上一句溫和的問候：

{text}"""
    try:
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
        rows = []
        for loc in data:
            location = loc.get("locationName", "")
            weather_elements = loc.get("weatherElement", [])

            # 先抓所有 MinT / MaxT 數值
            min_temps = []
            max_temps = []
            for element in weather_elements:
                name = element.get("elementName")
                times = element.get("time", [])
                for t in times:
                    val = t.get("parameter", {}).get("parameterName")
                    if val and val.isdigit():
                        val = int(val)
                        if name == "MinT":
                            min_temps.append(val)
                        elif name == "MaxT":
                            max_temps.append(val)

            row = {
                "城市": location,
                "最低溫": min(min_temps) if min_temps else None,
                "最高溫": max(max_temps) if max_temps else None
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        st.subheader("📊 全台各城市最低 / 最高溫度")
        st.dataframe(df)

        # Gemini 摘要
        with st.spinner("Gemini 正在生成摘要..."):
            summary = call_gemini(df.to_dict(orient="records"))

        st.subheader("🤖 Gemini 溫柔摘要")
        st.write(summary)
