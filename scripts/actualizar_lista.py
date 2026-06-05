# -*- coding: utf-8 -*-
"""
Lista Curada — actualización automática semanal.

Recorre el universo CANDIDATES, consulta el Worker (Yahoo) por cada uno,
calcula los 5 estados del Semáforo de Calidad + score, y selecciona el
Top 20 con una regla fija (5/5 primero por menor P/E, luego 4/5).

Escribe <repo>/lista_top20.json con metadatos de fecha. La página
lista.html lo lee con fetch() al abrir.

Pensado para correr en GitHub Actions (cron semanal) sin intervención.
Si la corrida sale mal (Yahoo caído, pocos resultados), aborta con código !=0
y NO pisa el JSON anterior, conservando la última lista buena.
"""
import json, os, sys, time, urllib.request, urllib.parse
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8")

WORKER = "https://yahoo-proxy.webmaster-c89.workers.dev/"
# El código va como secret del repo (SEMAFORO_CODE). Fallback para correr local.
CODE = os.environ.get("SEMAFORO_CODE", "SEMAFORONYSE2026")

# Carpeta raíz del repo = carpeta padre de /scripts
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(REPO_ROOT, "lista_top20.json")

# Cuántas empresas mostrar y umbrales de seguridad
TOP_N = 20
MIN_FETCH_OK = 25     # si se obtienen menos de 25 de 50, la corrida no es confiable
MIN_QUALIFY = 12      # si quedan menos de 12 aptas (>=4/5), no publicamos

CANDIDATES = [
    "AAPL","MSFT","GOOGL","META","NVDA","V","MA","KO","PEP","JNJ",
    "PG","HD","MCD","ABBV","LLY","UNH","COST","WMT","ADBE","ORCL",
    "AVGO","TXN","QCOM","NKE","CAT","HON","LMT","CVX","XOM","ABT",
    "TMO","ACN","CSCO","MRK","AMGN","CL","AXP","LOW","UPS","DIS",
    "TGT","IBM","PM","MO","BLK","GS","CMCSA","INTU","NOW","ISRG"
]

MESES_ES = ["enero","febrero","marzo","abril","mayo","junio","julio",
            "agosto","septiembre","octubre","noviembre","diciembre"]


def num(o):
    if o is None: return None
    if isinstance(o, (int, float)): return float(o)
    if isinstance(o, dict) and "raw" in o:
        try: return float(o["raw"])
        except Exception: return None
    return None


def fetch(tkr):
    url = WORKER + "?" + urllib.parse.urlencode({"symbol": tkr, "k": CODE})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def evaluate(m):
    pe, roe, mar = m["pe"], m["roe"], m["margin"]
    de, fcf = m["debt"], m["fcf"]
    def s_pe(v):
        if v is None or v > 500 or v < 0: return "warn"
        return "ok" if v <= 25 else ("warn" if v <= 30 else "fail")
    def s_roe(v): return "warn" if v is None else ("ok" if v >= 15 else ("warn" if v >= 12 else "fail"))
    def s_mar(v): return "warn" if v is None else ("ok" if v >= 10 else ("warn" if v >= 7 else "fail"))
    def s_de(v):  return "warn" if v is None else ("ok" if v <= 100 else ("warn" if v <= 120 else "fail"))
    def s_fcf(v): return "warn" if v is None else ("ok" if v > 0 else "fail")
    states = [s_pe(pe), s_roe(roe), s_mar(mar), s_de(de), s_fcf(fcf)]
    return states, states.count("ok")


def main():
    results, errors = [], 0
    for t in CANDIDATES:
        try:
            j = fetch(t)
            r = j["quoteSummary"]["result"][0]
            sd = r.get("summaryDetail", {}); fd = r.get("financialData", {})
            ks = r.get("defaultKeyStatistics", {}); pr = r.get("price", {}); ap = r.get("assetProfile", {})
            m = {
                "ticker": t,
                "name": pr.get("longName") or pr.get("shortName") or t,
                "sector": ap.get("sector", ""),
                "pe": num(sd.get("trailingPE")) if num(sd.get("trailingPE")) is not None else num(ks.get("trailingPE")),
                "roe": (num(fd.get("returnOnEquity")) * 100) if num(fd.get("returnOnEquity")) is not None else None,
                "margin": (num(fd.get("profitMargins")) * 100) if num(fd.get("profitMargins")) is not None else None,
                "debt": num(fd.get("debtToEquity")),
                "fcf": num(fd.get("freeCashflow")),
                "div": (num(sd.get("dividendYield")) * 100) if num(sd.get("dividendYield")) is not None else None,
            }
            m["states"], m["score"] = evaluate(m)
            results.append(m)
            pe_s = f"{m['pe']:.1f}" if m['pe'] is not None else "N/D"
            print(f"{t:6} {m['score']}/5  PE={pe_s:>6}  {m['name'][:30]}")
        except Exception as e:
            errors += 1
            print(f"{t:6} ERROR {e}")
        time.sleep(0.4)

    print(f"\nObtenidas {len(results)}/{len(CANDIDATES)} (errores: {errors})")

    # --- Guard de confiabilidad: no publicar corridas malas ---
    if len(results) < MIN_FETCH_OK:
        print(f"ABORT: solo {len(results)} resultados (<{MIN_FETCH_OK}). No se publica; se conserva la última lista.")
        sys.exit(1)

    # --- Selección automática del Top 20 ---
    qualify = [m for m in results if m["score"] >= 4]
    qualify.sort(key=lambda x: (-x["score"], x["pe"] if x["pe"] is not None else 999))
    if len(qualify) < MIN_QUALIFY:
        print(f"ABORT: solo {len(qualify)} aptas (>=4/5, <{MIN_QUALIFY}). No se publica.")
        sys.exit(1)
    top = qualify[:TOP_N]

    now = datetime.now(timezone.utc)
    payload = {
        "updated_iso": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_label": f"{now.day} de {MESES_ES[now.month - 1]} de {now.year}",
        "updated_month": f"{MESES_ES[now.month - 1]} {now.year}",
        "count": len(top),
        "count_5": sum(1 for m in top if m["score"] == 5),
        "universe": len(CANDIDATES),
        "companies": top,
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"\nOK → {OUT_PATH}")
    print(f"Top {len(top)} | 5/5: {payload['count_5']} | actualizado {payload['updated_label']}")


if __name__ == "__main__":
    main()
