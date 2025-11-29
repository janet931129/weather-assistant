import streamlit as st
import requests
import google.generativeai as genai
import pandas as pd

# === Streamlit 基本設定 ===
st.set_page_config(page_title="👩‍💼即時氣象主播 Demo", layout="centered")
st.title("👩‍💼即時氣象主播 Demo")
st.caption("CWA 全台天氣資料與 Gemini LLM 整合")

# === API Key 設定 ===
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


# === UI 主流程 ===
if st.button("📡 取得全台天氣資料"):
    with st.spinner("正在抓取 CWA 天氣資料..."):
        data = fetch_all_weather()

    if isinstance(data, dict) and "error" in data:
        st.error(data["error"])

    else:
        # ----整理資料----
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

                    if name == "Wx":  # 天氣描述
                        if val:
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

        # ----❶ Gemini 摘要放在 caption 下方 + 對話框----
        with st.spinner("Gemini 正在生成摘要..."):
            summary = call_gemini(df.to_dict(orient="records"))

        st.subheader("🤖 Gemini 溫柔摘要（AI 對話框）")
        with st.chat_message("assistant"):
            st.write(summary)

        # ----❷ 下拉式選單顯示單一城市天氣----
        st.subheader("📍 查詢城市天氣")
        city = st.selectbox("選擇城市", df["城市"].tolist())

        info = details[city]
        st.info(
            f"**{city} 今日天氣**\n\n"
            f"🌡 **最低溫:** {info['最低溫']}°C\n"
            f"🔥 **最高溫:** {info['最高溫']}°C\n"
            f"☁️ **天氣狀況:** {info['天氣描述']}"
        )
