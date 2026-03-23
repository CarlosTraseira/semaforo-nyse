import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

st.set_page_config(page_title="Semáforo NYSE Pro", page_icon="🚦")

# --- CARGA SEGURA DE LLAVES ---
# Accedemos a los nombres exactos que pusiste en tus Secrets
gemini_key = st.secrets["GEMINI_API_KEY"]
av_key = st.secrets["AV_API_KEY"]

if gemini_key and av_key:
    # Configurar Gemini
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    st.title("🚦 Semáforo de Calidad NYSE")
    st.markdown("Datos oficiales de Alpha Vantage + Análisis con IA Gemini.")

    ticker = st.text_input("Ticker de la empresa (ej: BP, AAPL, MSFT):", "BP").upper()

    if st.button("Analizar"):
        with st.spinner('Consultando terminal financiera...'):
            try:
                # 1. Obtener datos de Alpha Vantage
                url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={av_key}'
                response = requests.get(url)
                data = response.json()

                if "Symbol" not in data:
                    st.error("No se encontraron datos. Verifica el Ticker o el límite de la API.")
                else:
                    # 2. Extracción de Ratios (Convertimos de texto a número)
                    # Usamos .get con valor por defecto '0' para evitar errores
                    pe = float(data.get('TrailingPE', 0) if data.get('TrailingPE') != 'None' else 0)
                    roe = float(data.get('ReturnOnEquityTTM', 0) if data.get('ReturnOnEquityTTM') != 'None' else 0) * 100
                    margin = float(data.get('ProfitMargin', 0) if data.get('ProfitMargin') != 'None' else 0) * 100
                    div = float(data.get('DividendYield', 0) if data.get('DividendYield') != 'None' else 0) * 100

                    # 3. Mostrar Tabla de Métricas Reales
                    st.subheader(f"Métricas Auditadas para {ticker}")
                    res_df = pd.DataFrame({
                        "Indicador": ["P/E Ratio", "ROE (%)", "Profit Margin (%)", "Dividend Yield (%)"],
                        "Valor": [f"{pe:.2f}x", f"{roe:.2f}%", f"{margin:.2f}%", f"{div:.2f}%"],
                        "Estado": ["Normal" if pe < 30 else "Elevado", "Excelente" if roe > 15 else "Bajo", "Saludable" if margin > 10 else "Bajo", "Informativo"]
                    })
                    st.table(res_df)

                    # 4. Análisis con IA Gemini
                    prompt = f"""Actúa como experto financiero. Analiza estos datos reales de {ticker}:
                    - P/E Ratio: {pe:.2f}
                    - ROE: {roe:.2f}%
                    - Margen de Beneficio: {margin:.2f}%
                    Da un veredicto de 'Semáforo' (Verde, Amarillo o Rojo) y justifica con 3 puntos clave."""
                    
                    # Generar respuesta
                    ai_response = model.generate_content(prompt)
                    st.subheader("🧠 Veredicto de la IA")
                    st.write(ai_response.text)

            except Exception as e:
                st.error(f"Error técnico: {e}")
else:
    st.warning("⚠️ Asegúrate de configurar GEMINI_API_KEY y AV_API_KEY en los Secrets de Streamlit.")
