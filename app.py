import streamlit as st
import google.generativeai as genai
import pandas as pd
import requests

# 1. Configuración de página
st.set_page_config(page_title="Semáforo NYSE Alpha Pro", page_icon="🚦")

# --- CARGA SEGURA DE SECRETOS ---
try:
    gemini_key = st.secrets["GEMINI_API_KEY"].strip().replace('"', '').replace("'", "")
    alpha_key = st.secrets["ALPHA_VANTAGE_KEY"].strip().replace('"', '').replace("'", "")
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error en Secrets: {e}")
    st.stop()

# --- FUNCIÓN CON CACHÉ (Ahorra 25 créditos diarios) ---
@st.cache_data(ttl=86400)
def obtener_datos_alpha(ticker):
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={alpha_key}"
    response = requests.get(url)
    return response.json()

st.title("🚦 Semáforo NYSE Pro")
st.markdown("### Auditoría de 6 Puntos Clave")

ticker = st.text_input("Ticker de la empresa:", "B").upper().strip()

if st.button("Analizar"):
    with st.spinner(f'Analizando {ticker}...'):
        data = obtener_datos_alpha(ticker)

        if not data or "Symbol" not in data:
            st.error("❌ No se encontraron datos. Verifica el Ticker o el límite de la API.")
        else:
            # --- EXTRACCIÓN DE TUS 6 DATOS ESPECÍFICOS ---
            nombre = data.get('Name', ticker)
            
            # 1. Trailing PE
            pe = float(data.get('PERatio', 0)) if data.get('PERatio') != 'None' else 0
            # 2. Return on Equity (ROE)
            roe = float(data.get('ReturnOnEquityTTM', 0)) * 100 if data.get('ReturnOnEquityTTM') != 'None' else 0
            # 3. Profit Margins
            margin = float(data.get('ProfitMargin', 0)) * 100 if data.get('ProfitMargin') != 'None' else 0
            # 4. Debt to Equity
            debt = float(data.get('DebtToEquityRatio', 0)) if data.get('DebtToEquityRatio') != 'None' else 0
            # 5. Free Cash Flow (Aprox. mediante Operating Cash Flow en Overview)
            # Nota: Alpha Vantage Overview no da FCF directo, usamos Operating Cash Flow como referencia de liquidez
            fcf = data.get('OperatingCashFlowTTM', "N/A")
            # 6. Dividend Yield
            div = float(data.get('DividendYield', 0)) * 100 if data.get('DividendYield') != 'None' else 0

            st.subheader(f"Auditoría Técnica: {nombre}")

            # --- CONSTRUCCIÓN DE LA TABLA COMPLETA ---
            metrics_data = {
                "Indicador": ["P/E Ratio", "ROE (%)", "Margen (%)", "Deuda/Equity", "Cash Flow (Op)", "Div. Yield (%)"],
                "Valor": [f"{pe:.2f}x", f"{roe:.2f}%", f"{margin:.2f}%", f"{debt:.2f}", f"{fcf}", f"{div:.2f}%"],
                "Referencia": ["Bajo 20x", "Sobre 15%", "Sobre 10%", "Bajo 1.5", "Positivo", "Sobre 2%"],
                "Estado": [
                    "🟢 Atractivo" if 0 < pe < 20 else "🔴 Caro",
                    "🟢 Saludable" if roe > 15 else "🟡 Bajo",
                    "🟢 Eficiente" if margin > 10 else "🔴 Ajustado",
                    "🟢 Bajo Riesgo" if debt < 1.5 else "🔴 Endeudado",
                    "🟢 Liquidez" if fcf != "N/A" else "⚪ N/A",
                    "🟢 Paga" if div > 0 else "⚪ Sin Div."
                ]
            }

            df = pd.DataFrame(metrics_data)
            st.table(df)

            # --- VERDICTO IA ---
            st.subheader("🧠 Veredicto de la IA")
            prompt = f"""
            Analiza {nombre} ({ticker}) con estos 6 datos:
            PE:{pe}, ROE:{roe}%, Margen:{margin}%, Deuda/Eq:{debt}, CashFlow:{fcf}, Dividend:{div}%.
            Da un veredicto de inversión muy breve.
            """
            
            try:
                res_ia = model.generate_content(prompt)
                st.success(res_ia.text)
            except:
                st.info("💡 Datos cargados. La IA está saturada pero puedes ver la tabla arriba.")

st.divider()
st.caption("Memoria activa: Esta consulta no consumirá más créditos por las próximas 24 horas.")
