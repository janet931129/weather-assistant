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
        return {"error": "CWA API Key 未設定"}

    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
    params = {"Authorization": CWA_KEY, "locationName": "臺北市", "limit": 1}

    try:
        resp = requests.get(url, params=params, timeout=10, verify=False)
        resp.raise_for_status()
        data = resp.json()

        records = data.get("records", {}).get("locations", [])
        if not records:
            return {"error": "沒有資料"}

        locations = records[0].get("location", [])
        if not locations:
            return {"error": "沒有資料"}

        return locations[0]  # 取最新一筆資料

    except Exception as e:
        return {"error": str(e)}


# === Gemini LLM 生成摘要 ===
def call_gemini(text):
    if not GEMINI_KEY:
        return "Gemini API Key 未設定"

    genai.configure(api_key=GEMINI_KEY)

    try:
        model = "models/text-bison-001"
