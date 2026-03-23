import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

try:
    gemini_key = st.secrets["GEMINI_API_KEY"]
    fmp_key = st.secrets["FMP_API_KEY"]

    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    st.title("🚦 Semáforo NYSE (Modo FMP 250)")
    ticker = st.text_input("Ticker:", "BP").upper().strip()

    if st.button("Analizar"):
        with st.spinner('Consultando FMP...'):
            # 1. Obtener P/E y Dividendos del Quote
            url_quote = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={fmp_key}"
            data_quote = requests.get(url_quote).json()

            # 2. Obtener ROE y Márgenes de Ratios TTM
            url_ratios = f"https://financialmodelingprep.com/api/v3/ratios-ttm/{ticker}?apikey={fmp_key}"
            data_ratios = requests.get(url_ratios).json()

            if not data_quote or not data_ratios:
                st.error("No se encontraron datos. Revisa el ticker o la API Key.")
            else:
                q = data_quote[0]
                r = data_ratios[0]

                pe = q.get('pe', 0)
                roe = r.get('returnOnEquityTTM', 0) * 100
                margin = r.get('netProfitMarginTTM', 0) * 100

                st.subheader(f"Auditoría: {ticker}")
                st.table(pd.DataFrame({
                    "Métrica": ["P/E Ratio", "ROE (%)", "Margen (%)"],
                    "Valor": [f"{pe:.2f}x", f"{roe:.2f}%", f"{margin:.2f}%"]
                }))

                # IA
                prompt = f"Analiza {ticker}: PE {pe:.2f}, ROE {roe:.2f}%, Margen {margin:.2f}%. Da veredicto semáforo."
                response = model.generate_content(prompt)
                st.subheader("🧠 Veredicto de la IA")
                st.write(response.text)

except Exception as e:
    st.error(f"Error: {e}")
