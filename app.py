import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

# --- CARGA DE LLAVES DESDE SECRETS ---
gemini_key = st.secrets.get("GEMINI_API_KEY")
av_key = st.secrets.get("AV_API_KEY")

if gemini_key and av_key:
    # Configurar IA
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    st.title("🚦 Semáforo de Calidad NYSE")
    st.markdown("Datos oficiales de Alpha Vantage + Análisis Gemini.")

    ticker = st.text_input("Ticker (ej: BP, AAPL, MSFT):", "BP").upper()

    if st.button("Analizar"):
        with st.spinner('Auditando activos...'):
            try:
                # 1. Llamada a Alpha Vantage
                url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={av_key}'
                data = requests.get(url).json()

                if "Symbol" not in data:
                    st.error("Límite de API alcanzado o Ticker inválido. Alpha Vantage permite 25 consultas/día.")
                else:
                    # 2. Extracción de Ratios Reales
                    pe = float(data.get('TrailingPE', 0))
                    roe = float(data.get('ReturnOnEquityTTM', 0)) * 100
                    margin = float(data.get('ProfitMargin', 0)) * 100
                    div = float(data.get('DividendYield', 0)) * 100

                    # 3. Tabla de Resultados
                    st.subheader(f"Métricas Reales para {ticker}")
                    res_df = pd.DataFrame({
                        "Indicador": ["P/E Ratio", "ROE (%)", "Profit Margin (%)", "Dividend Yield (%)"],
                        "Valor": [f"{pe:.2f}x", f"{roe:.2f}%", f"{margin:.2f}%", f"{div:.2f}%"],
                        "Estado": ["OK" if pe < 30 else "Alto", "OK" if roe > 15 else "Bajo", "OK" if margin > 10 else "Bajo", "N/A"]
                    })
                    st.table(res_df)

                    # 4. Análisis IA
                    prompt = f"Analiza: Ticker {ticker}, P/E {pe}, ROE {roe}%, Margen {margin}%. Da un veredicto Semáforo y 3 puntos clave."
                    response = model.generate_content(prompt)
                    st.subheader("🧠 Veredicto de la IA")
                    st.write(response.text)

            except Exception as e:
                st.error(f"Error en el proceso: {e}")
else:
    st.error("⚠️ Error: No se detectan las API Keys en los Secrets de Streamlit.")
