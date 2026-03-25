from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Semáforo NYSE", page_icon="🚦", layout="wide")

API_BASE_URL = "https://www.alphavantage.co/query"
TIMEOUT_SECONDS = 20


@dataclass
class MetricResult:
    indicador: str
    valor: str
    referencia: str
    estado: str
    explicacion: str


def _to_float(value: Any) -> float | None:
    if value in (None, "None", "", "-"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_percent(decimal_value: float | None) -> str:
    if decimal_value is None:
        return "N/D"
    return f"{decimal_value * 100:.2f}%"


def _format_ratio(value: float | None, suffix: str = "") -> str:
    if value is None:
        return "N/D"
    return f"{value:.2f}{suffix}"


@st.cache_data(ttl=60 * 60 * 12)
def fetch_alpha_overview(symbol: str, api_key: str) -> dict[str, Any]:
    response = requests.get(
        API_BASE_URL,
        params={"function": "OVERVIEW", "symbol": symbol, "apikey": api_key},
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=60 * 60 * 12)
def fetch_alpha_cash_flow(symbol: str, api_key: str) -> dict[str, Any]:
    response = requests.get(
        API_BASE_URL,
        params={"function": "CASH_FLOW", "symbol": symbol, "apikey": api_key},
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def build_metric_results(overview: dict[str, Any], cash_flow: dict[str, Any]) -> list[MetricResult]:
    pe = _to_float(overview.get("PERatio"))
    roe = _to_float(overview.get("ReturnOnEquityTTM"))
    margin = _to_float(overview.get("ProfitMargin"))
    debt_equity = _to_float(overview.get("DebtToEquityRatio"))
    div_yield = _to_float(overview.get("DividendYield"))

    fcf_value = None
    annual_reports = cash_flow.get("annualReports") or []
    if annual_reports:
        latest = annual_reports[0]
        operating_cf = _to_float(latest.get("operatingCashflow"))
        capex = _to_float(latest.get("capitalExpenditures"))
        if operating_cf is not None and capex is not None:
            fcf_value = operating_cf - capex

    metrics = [
        MetricResult(
            indicador="Trailing P/E",
            valor=_format_ratio(pe, "x"),
            referencia="10x–25x suele considerarse rango razonable en analistas value/growth mixto.",
            estado="🟢 OK" if pe is not None and 10 <= pe <= 25 else "🟡 Revisar",
            explicacion="Más bajo puede indicar infravaloración o riesgo; más alto exige mayor crecimiento.",
        ),
        MetricResult(
            indicador="ROE",
            valor=_format_percent(roe),
            referencia=">= 15% suele reflejar buena rentabilidad sobre patrimonio.",
            estado="🟢 OK" if roe is not None and roe >= 0.15 else "🟡 Revisar",
            explicacion="ROE alto y sostenible es preferible a un pico puntual.",
        ),
        MetricResult(
            indicador="Profit Margin",
            valor=_format_percent(margin),
            referencia=">= 10% se considera saludable en muchos sectores.",
            estado="🟢 OK" if margin is not None and margin >= 0.10 else "🟡 Revisar",
            explicacion="Comparar siempre contra pares del mismo sector.",
        ),
        MetricResult(
            indicador="Debt to Equity",
            valor=_format_ratio(debt_equity),
            referencia="<= 1.5 suele interpretarse como apalancamiento manejable.",
            estado="🟢 OK" if debt_equity is not None and debt_equity <= 1.5 else "🟡 Revisar",
            explicacion="Sectores intensivos en capital pueden tolerar niveles más altos.",
        ),
        MetricResult(
            indicador="Free Cash Flow",
            valor=(f"${fcf_value:,.0f}" if fcf_value is not None else "N/D"),
            referencia="> 0 de forma consistente: negocio con capacidad real de generar caja.",
            estado="🟢 OK" if fcf_value is not None and fcf_value > 0 else "🟡 Revisar",
            explicacion="Calculado como Operating Cash Flow - Capital Expenditures (último anual).",
        ),
        MetricResult(
            indicador="Div. Yield (%)",
            valor=_format_percent(div_yield),
            referencia=">= 2% suele ser atractivo para perfil de renta (según sector).",
            estado="🟢 OK" if div_yield is not None and div_yield >= 0.02 else "🟡 Revisar",
            explicacion="Un yield muy alto puede ser señal de riesgo si no es sostenible.",
        ),
    ]
    return metrics


def build_verification_links(symbol: str) -> list[tuple[str, str, str]]:
    return [
        (
            "Alpha Vantage Overview (métricas de PE/ROE/Margen/Deuda/Div)",
            f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey=demo",
            "Reemplaza 'demo' por tu API key para ver exactamente los campos usados.",
        ),
        (
            "Alpha Vantage Cash Flow (base para Free Cash Flow)",
            f"https://www.alphavantage.co/query?function=CASH_FLOW&symbol={symbol}&apikey=demo",
            "En annualReports[0], calcula: operatingCashflow - capitalExpenditures.",
        ),
        (
            "SEC EDGAR (fuente primaria)",
            f"https://www.sec.gov/edgar/search/#/q={symbol}",
            "Valida estados financieros oficiales 10-K/10-Q cuando quieras auditoría manual.",
        ),
    ]


def main() -> None:
    st.title("🚦 Semáforo NYSE")
    st.caption("Evaluación fundamental de 6 indicadores con referencias de uso común en análisis financiero.")

    with st.sidebar:
        st.subheader("Configuración")
        api_key = st.text_input(
            "Alpha Vantage API Key",
            type="password",
            value=st.secrets.get("ALPHA_VANTAGE_API_KEY", ""),
            help="Sin servicios pagos. Usa la API gratuita de Alpha Vantage.",
        ).strip()
        symbol = st.text_input("Ticker NYSE", value="IBM").upper().strip()
        run = st.button("Analizar", type="primary")

    if not run:
        st.info("Ingresa API key + ticker y haz clic en **Analizar**.")
        return

    if not api_key:
        st.error("Debes ingresar tu API key de Alpha Vantage.")
        return

    with st.spinner(f"Consultando datos para {symbol}..."):
        try:
            overview = fetch_alpha_overview(symbol, api_key)
            cash_flow = fetch_alpha_cash_flow(symbol, api_key)
        except requests.HTTPError as exc:
            st.error(f"Error HTTP al consultar Alpha Vantage: {exc}")
            return
        except requests.RequestException as exc:
            st.error(f"Error de conexión: {exc}")
            return

    if "Symbol" not in overview:
        possible_note = overview.get("Note") or overview.get("Information") or "Ticker inválido o límite de API alcanzado."
        st.error(f"No se pudo obtener OVERVIEW para {symbol}. Detalle: {possible_note}")
        return

    company_name = overview.get("Name", symbol)
    exchange = overview.get("Exchange", "N/D")
    sector = overview.get("Sector", "N/D")

    st.subheader(f"Reporte: {company_name} ({symbol})")
    st.write(f"**Exchange:** {exchange} | **Sector:** {sector}")

    metrics = build_metric_results(overview, cash_flow)
    df = pd.DataFrame([m.__dict__ for m in metrics])
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("### Referencias usadas en la columna 'Referencia'")
    st.markdown(
        "Estas referencias son **umbrales generales** usados frecuentemente por analistas fundamentales. "
        "Siempre conviene compararlas con el promedio del sector y la etapa del ciclo económico."
    )

    st.markdown("### Verificación de datos (links directos)")
    for title, url, howto in build_verification_links(symbol):
        st.markdown(f"- [{title}]({url})  ")
        st.caption(f"Cómo verificar: {howto}")

    st.divider()
    st.caption(
        "Nota de transparencia: los datos se obtienen de Alpha Vantage (free tier). "
        "Para validación de máxima confianza, contrasta con reportes 10-K/10-Q en SEC EDGAR."
    )


if __name__ == "__main__":
    main()
