import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

# 1. Configuración de la página
st.set_page_config(page_title="Semáforo NYSE Alpha", page_icon="🚦")

# --- CARGA SEGURA DE SECRETOS ---
try:
    # ALPHA_VANTAGE_KEY reemplaza a la de FMP
    gemini_key = st.secrets["GEMINI_API_KEY"].strip().replace('"', '').replace("'", "")
    alpha_key = st.secrets["ALPHA_VANTAGE_KEY"].strip().replace('"', '').replace("'", "")
    
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error en los Secrets: {e}")
    st.stop()

# 2. Interfaz de usuario
st.title("🚦 Semáforo NYSE (Alpha Edition)")
st.markdown("### Datos: Alpha Vantage | Cerebro: Gemini IA")

ticker = st.text_input("Introduce el Ticker (ej: AAPL, MSFT, TSLA):", "AAPL").upper().strip()

if st.button("Analizar"):
    with st.spinner(f'Obteniendo datos de Alpha Vantage para {ticker}...'):
        # Endpoint de Alpha Vantage para métricas generales (OVERVIEW)
        url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={alpha_key}"
        
        try:
            response = requests.get(url)
            data = response.json()

            if not data or "Symbol" not in data:
                st.error("❌ No se encontraron datos. Verifica el Ticker o tu API Key de Alpha Vantage.")
                if "Note" in data:
                    st.warning("Has alcanzado el límite de la versión gratuita de Alpha Vantage (5 consultas por minuto).")
            else:
                # Extraemos datos de Alpha Vantage
                nombre = data.get('Name', ticker)
                sector = data.get('Sector', 'N/A')
                pe = float(data.get('PERatio', 0)) if data.get('PERatio') != 'None' else 0
                roe = float(data.get('ReturnOnEquityTTM', 0)) * 100 if data.get('ReturnOnEquityTTM') != 'None' else 0
                dividend = data.get('DividendYield', '0')
                
                # --- MOSTRAR RESULTADOS ---
                st.subheader(f"Auditoría: {nombre}")
                
                # Lógica de semáforo para la tabla
                def get_status(val):
                    if val <= 0: return "⚪ N/A"
                    return "🟢 Atractivo" if val < 20 else "🟡 Elevado" if val < 35 else "🔴 Muy Caro"

                df = pd.DataFrame({
                    "Métrica": ["P/E Ratio", "ROE (%)", "Dividend Yield"],
                    "Valor": [f"{pe:.2f}x", f"{roe:.2f}%", f"{dividend}"],
                    "Estado": [get_status(pe), "🟢 Saludable" if roe > 15 else "🟡 Normal", "-"]
                })
                st.table(df)

                # --- ANÁLISIS DE IA ---
                st.subheader("🧠 Veredicto de la IA")
                prompt = f"Analiza la empresa {nombre} ({ticker}) del sector {sector}. Tiene un PE de {pe:.2f} y un ROE de {roe:.2f}%. Da un veredicto de inversión corto tipo semáforo."
                
                try:
                    resultado_ia = model.generate_content(prompt)
                    st.success(resultado_ia.text)
                except:
                    st.warning("La IA no pudo procesar el análisis, pero los datos están listos.")

        except Exception as e:
            st.error(f"Error de conexión: {e}")

st.divider()
st.caption("Alpha Vantage permite 25 consultas diarias en su plan gratuito.")
