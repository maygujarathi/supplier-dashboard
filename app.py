"""SupplierDash — Supplier Performance & Risk Dashboard.

Fixes vs previous version:
- Settings reset no longer crashes (uses on_click callback; widget keys are
  never written after widget instantiation).
- Widget keys ARE the config (no value=/key= conflict, no shadow cfg_ store).
- Rules are computed fresh every run, after session state is settled.
- Column detection is order-independent and fuzzy (handles spaces, %, _, case,
  German names). Manual column mapper appears if auto-detection fails.
- Numeric columns are cleaned (€, %, commas, spaces) before coercion, and a
  data-quality report tells you exactly which columns/rows had bad values
  instead of silently dropping rows.
- Delivery % is derived from On_Time_Shipments / Total_Shipments if missing.
- Extra dataset columns supported: Region, Supplier_Tier, ESG_Score,
  Anomaly_Flag, Last_Audit_Date, Spend, Notes.
"""

from __future__ import annotations

import io
import re
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════
# Page config
# ══════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="SupplierDash",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════
# Internal column names
# ══════════════════════════════════════════════════════════════════════════
COL_SUPPLIER = "Supplier_Name"
COL_COUNTRY = "Country"
COL_REGION = "Region"
COL_CATEGORY = "Category"
COL_TIER = "Supplier_Tier"
COL_DELIVERY = "Delivery_Performance_%"
COL_LEADTIME = "Lead_Time_Days"
COL_QUALITY = "Quality_Score_%"
COL_COMPLAINT = "Complaint_Rate_%"
COL_PRICE_DEV = "Price_Deviation_%"
COL_ESG = "ESG_Score"
COL_SCORE = "Overall_Score"
COL_STATUS = "Status"
COL_ANOMALY = "Anomaly_Flag"
COL_ID = "Supplier_ID"
COL_SPEND = "Spend"
COL_NOTES = "Notes"
COL_AUDIT = "Last_Audit_Date"
COL_TOTAL_SHIP = "Total_Shipments"
COL_ONTIME_SHIP = "On_Time_Shipments"
COL_DATE = "Period_Date"  # optional time column for real time trends

REQUIRED_COLS = [COL_SUPPLIER, COL_COUNTRY, COL_CATEGORY, COL_DELIVERY,
                 COL_LEADTIME, COL_QUALITY, COL_COMPLAINT, COL_PRICE_DEV]
NUMERIC_COLS = [COL_DELIVERY, COL_LEADTIME, COL_QUALITY, COL_COMPLAINT,
                COL_PRICE_DEV, COL_ESG, COL_SCORE, COL_SPEND,
                COL_TOTAL_SHIP, COL_ONTIME_SHIP]

# Synonyms for fuzzy auto-detection (normalized: lowercase, alphanumeric only)
AUTO_MAP: dict[str, list[str]] = {
    COL_SUPPLIER: ["suppliername", "supplier", "name", "lieferant", "vendor", "vendorname"],
    COL_COUNTRY: ["country", "land", "countryname"],
    COL_REGION: ["region", "area", "zone"],
    COL_CATEGORY: ["category", "kategorie", "material", "materialgroup", "commodity"],
    COL_TIER: ["suppliertier", "tier", "classification", "supplierclass"],
    COL_DELIVERY: ["deliveryperformance", "delivery", "ontimedelivery", "otd",
                   "liefertreue", "deliveryrate", "ontimedeliveryrate"],
    COL_LEADTIME: ["leadtimedays", "leadtime", "lieferzeit", "avgleadtime"],
    COL_QUALITY: ["qualityscore", "quality", "qualitatsrate", "qualityrate", "qualitaet"],
    COL_COMPLAINT: ["complaintrate", "complaints", "reklamationsquote", "defectrate", "claimrate"],
    COL_PRICE_DEV: ["pricedeviation", "pricedev", "preisabweichung", "pricevariance"],
    COL_ESG: ["esgscore", "esg", "sustainabilityscore"],
    COL_SCORE: ["overallscore", "score", "gesamtscore", "totalscore"],
    COL_STATUS: ["status", "supplierstatus", "riskstatus"],
    COL_ANOMALY: ["anomalyflag", "anomaly", "isanomaly", "anomalieflag"],
    COL_ID: ["supplierid", "id", "lieferantid", "vendorid"],
    COL_SPEND: ["spend", "annualspend", "totalspend", "purchasevalue", "spendundermanagement", "value"],
    COL_NOTES: ["notes", "comment", "comments", "remark", "remarks", "sourcenote"],
    COL_AUDIT: ["lastauditdate", "auditdate", "lastaudit"],
    COL_TOTAL_SHIP: ["totalshipments", "shipments", "totaldeliveries"],
    COL_ONTIME_SHIP: ["ontimeshipments", "ontimedeliveries"],
    COL_DATE: ["date", "month", "period", "reportingdate", "reportdate",
               "snapshotdate", "kpidate", "datum", "monat", "periodend", "week"],
}

# ══════════════════════════════════════════════════════════════════════════
# Settings — single source of truth lives in st.session_state under these
# keys. Widgets use the SAME keys (no value= param, so no conflicts).
# ══════════════════════════════════════════════════════════════════════════
DEFAULT_SETTINGS: dict[str, object] = {
    "delivery_target": 95.0,
    "quality_target": 97.0,
    "leadtime_limit": 10.0,
    "complaint_limit": 1.0,
    "price_dev_tolerance": 1.0,
    "anomaly_sensitivity": "Medium",
    "top_supplier_rows": 14,
    "show_country_flags": True,
    "show_delivery_trend": True,
}

for _k, _v in DEFAULT_SETTINGS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


def reset_settings() -> None:
    """Reset all settings. Runs as an on_click CALLBACK, which executes
    BEFORE the next script run — so writing widget keys here is legal and
    can never raise StreamlitAPIException."""
    for k, v in DEFAULT_SETTINGS.items():
        st.session_state[k] = v


def get_effective_rules() -> dict:
    """Compute thresholds fresh from current session state."""
    s = st.session_state
    rules = {
        "delivery_target": float(s["delivery_target"]),
        "quality_target": float(s["quality_target"]),
        "leadtime_limit": float(s["leadtime_limit"]),
        "complaint_limit": float(s["complaint_limit"]),
        "price_dev_tolerance": float(s["price_dev_tolerance"]),
        "anomaly_sensitivity": str(s["anomaly_sensitivity"]),
    }
    sens = rules["anomaly_sensitivity"]
    if sens == "Low":
        rules.update(
            delivery_threshold=max(0.0, rules["delivery_target"] - 5.0),
            quality_threshold=max(0.0, rules["quality_target"] - 3.0),
            leadtime_threshold=rules["leadtime_limit"] + 3.0,
            complaint_threshold=rules["complaint_limit"] + 0.5,
            price_threshold=rules["price_dev_tolerance"] + 1.0,
        )
    elif sens == "High":
        rules.update(
            delivery_threshold=min(100.0, rules["delivery_target"] + 1.0),
            quality_threshold=min(100.0, rules["quality_target"] + 1.0),
            leadtime_threshold=max(0.1, rules["leadtime_limit"] - 2.0),
            complaint_threshold=max(0.1, rules["complaint_limit"] - 0.2),
            price_threshold=max(0.1, rules["price_dev_tolerance"] - 0.3),
        )
    else:
        rules.update(
            delivery_threshold=rules["delivery_target"],
            quality_threshold=rules["quality_target"],
            leadtime_threshold=rules["leadtime_limit"],
            complaint_threshold=rules["complaint_limit"],
            price_threshold=rules["price_dev_tolerance"],
        )
    return rules


# ══════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
html, body, [class*="css"] { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; }
.stApp { background: #0d1117 !important; color: #e6edf3 !important; }
.block-container { padding: 1rem 1.35rem 2rem 1.35rem !important; max-width: 100% !important; }
#MainMenu, footer { visibility: hidden !important; }
header[data-testid="stHeader"] { visibility: visible !important; background: transparent !important; height: 2.75rem !important; }
div[data-testid="collapsedControl"] { display:flex !important; visibility:visible !important; opacity:1 !important;
    z-index:999999 !important; cursor:pointer !important; background:#161b22 !important;
    border:1px solid #30363d !important; border-radius:9px !important; }
div[data-testid="collapsedControl"] * { cursor:pointer !important; }
section[data-testid="stSidebar"] { background:#161b22 !important; border-right:1px solid #30363d !important; }
section[data-testid="stSidebar"] > div { padding:0.8rem 0.75rem !important; }
section[data-testid="stSidebar"] * { color:#c9d1d9 !important; }
.logo-box { font-size:1.05rem; font-weight:900; color:#e6edf3; padding:.55rem .35rem .95rem .35rem;
    border-bottom:1px solid #30363d; margin-bottom:.85rem; }
.side-title { font-size:.68rem; letter-spacing:.08em; text-transform:uppercase; color:#8b949e !important;
    font-weight:900; margin:1rem .35rem .35rem .35rem; }
div[role="radiogroup"] label { background:transparent !important; border-radius:8px !important;
    padding:.5rem .6rem !important; margin:.05rem 0 !important; cursor:pointer !important; }
div[role="radiogroup"] label:hover { background:#21262d !important; }
div[role="radiogroup"] label[data-baseweb="radio"] > div:first-child { display:none !important; }
div[role="radiogroup"] label p { font-size:.86rem !important; font-weight:700 !important; }
div[role="radiogroup"] * { cursor:pointer !important; }
.stSelectbox, .stSelectbox *, div[data-baseweb="select"], div[data-baseweb="select"] * { cursor:pointer !important; }
div[data-baseweb="select"] input, input[aria-autocomplete="list"] { cursor:pointer !important;
    caret-color:transparent !important; user-select:none !important; }
.stTextInput input { cursor:text !important; caret-color:auto !important; user-select:text !important; }
.stSelectbox label,.stTextInput label,.stFileUploader label,.stRadio label,.stSlider label,
.stCheckbox label,.stNumberInput label { color:#8b949e !important; font-size:.78rem !important; font-weight:750 !important; }
div[data-baseweb="select"] > div,.stTextInput input,.stNumberInput input { background:#21262d !important;
    border:1px solid #30363d !important; color:#e6edf3 !important; border-radius:9px !important; }
.stSlider div[data-baseweb="slider"] div { background-color:#30363d !important; }
.stSlider div[data-baseweb="slider"] div[style*="width"] { background-color:#f0f6fc !important; }
.stSlider div[role="slider"] { background-color:#f0f6fc !important; border:2px solid #f0f6fc !important;
    box-shadow:0 0 0 2px #30363d !important; }
.stButton > button { background:#1f3a5f !important; border:1px solid #388bfd !important; color:#58a6ff !important;
    border-radius:9px !important; font-weight:800 !important; }
.stDownloadButton > button { background:#1f3a5f !important; border:1px solid #388bfd !important;
    color:#58a6ff !important; border-radius:9px !important; font-weight:800 !important; }
.top-bar { background:#161b22; border:1px solid #30363d; border-radius:12px; padding:1rem 1.1rem;
    margin-bottom:.9rem; display:flex; justify-content:space-between; align-items:center; gap:.8rem; flex-wrap:wrap; }
.top-title { font-size:1.35rem; font-weight:900; color:#e6edf3; }
.top-sub { font-size:.82rem; color:#8b949e; margin-top:.15rem; }
.metric-grid { display:grid; grid-template-columns:repeat(7,minmax(140px,1fr)); gap:.65rem; margin-bottom:.75rem; }
@media (max-width:1600px){ .metric-grid{ grid-template-columns:repeat(4,minmax(160px,1fr)); } }
@media (max-width:900px){ .metric-grid{ grid-template-columns:repeat(1,minmax(160px,1fr)); } }
.kpi-card { background:#161b22; border:1px solid #30363d; border-radius:12px; padding:1rem 1.1rem;
    display:flex; align-items:center; gap:.85rem; min-height:92px; }
.kpi-icon { width:44px; height:44px; border-radius:12px; display:flex; align-items:center;
    justify-content:center; font-size:1.15rem; flex-shrink:0; }
.kpi-label { font-size:.76rem; color:#8b949e; font-weight:700; }
.kpi-value { font-size:1.55rem; font-weight:900; color:#e6edf3; line-height:1.12; }
.kpi-good { font-size:.74rem; color:#3fb950; font-weight:850; }
.kpi-bad { font-size:.74rem; color:#f85149; font-weight:850; }
.kpi-muted { font-size:.72rem; color:#6e7681; }
.kpi-selected-name { font-size:.68rem; color:#58a6ff; font-weight:800; margin-top:2px; white-space:nowrap;
    overflow:hidden; text-overflow:ellipsis; max-width:120px; }
.s-card { background:#161b22; border:1px solid #30363d; border-radius:12px; padding:1rem 1.1rem;
    height:100%; overflow:hidden; }
.s-card-title { font-size:.96rem; font-weight:900; color:#e6edf3; margin-bottom:.8rem; }
.status-active,.status-risk,.status-high { padding:.15rem .55rem; border-radius:16px; font-size:.72rem;
    font-weight:850; display:inline-block; }
.status-active { background:rgba(63,185,80,.12); color:#3fb950; border:1px solid rgba(63,185,80,.35); }
.status-risk { background:rgba(210,153,34,.12); color:#d29922; border:1px solid rgba(210,153,34,.35); }
.status-high { background:rgba(248,81,73,.12); color:#f85149; border:1px solid rgba(248,81,73,.35); }
.alert-row { border-bottom:1px solid #21262d; padding:.65rem 0; }
.alert-row:last-child { border-bottom:none; }
.alert-name { font-size:.86rem; font-weight:850; color:#e6edf3; }
.alert-desc { font-size:.76rem; color:#8b949e; margin-top:.15rem; }
.alert-badge-high,.alert-badge-med { padding:.13rem .45rem; border-radius:12px; font-size:.68rem; font-weight:900; }
.alert-badge-high { background:rgba(248,81,73,.12); color:#f85149; border:1px solid rgba(248,81,73,.35); }
.alert-badge-med { background:rgba(210,153,34,.12); color:#d29922; border:1px solid rgba(210,153,34,.35); }
.chip-row { margin-top:.35rem; display:flex; flex-wrap:wrap; gap:4px; }
.kpi-chip { padding:.12rem .5rem; border-radius:8px; font-size:.7rem; font-weight:800; white-space:nowrap;
    background:rgba(248,81,73,.10); color:#f85149; border:1px solid rgba(248,81,73,.30); }
.kpi-chip.amber { background:rgba(210,153,34,.10); color:#d29922; border-color:rgba(210,153,34,.30); }
.chip-legend { font-size:.66rem; color:#6e7681; margin-bottom:.5rem; line-height:1.5; }
.profile-avatar { width:48px; height:48px; border-radius:14px; background:linear-gradient(135deg,#1f6feb,#58a6ff);
    display:flex; align-items:center; justify-content:center; color:white; font-weight:900; }
.stDataFrame { border-radius:10px !important; overflow:hidden !important; }
div[data-testid="stDataFrame"] { border:1px solid #30363d !important; border-radius:10px !important; }
</style>
""",
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════
def normalize_name(name: str) -> str:
    """'Delivery_Performance_%' / 'delivery performance %' -> 'deliveryperformance'."""
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def auto_detect_columns(df: pd.DataFrame) -> dict[str, str | None]:
    """Map internal column names to actual file columns, order-independent."""
    norm_to_actual: dict[str, str] = {}
    for col in df.columns:
        norm_to_actual.setdefault(normalize_name(col), col)

    result: dict[str, str | None] = {}
    used: set[str] = set()
    for internal, candidates in AUTO_MAP.items():
        found = None
        # exact normalized match first
        for cand in candidates:
            actual = norm_to_actual.get(cand)
            if actual is not None and actual not in used:
                found = actual
                break
        # fallback: candidate contained in column name (e.g. 'avgleadtimedays')
        if found is None:
            for cand in candidates:
                for norm, actual in norm_to_actual.items():
                    if actual not in used and cand in norm and len(cand) >= 5:
                        found = actual
                        break
                if found:
                    break
        result[internal] = found
        if found:
            used.add(found)
    return result


def clean_numeric(series: pd.Series) -> pd.Series:
    """Coerce to numeric; strips €, $, %, thousands separators, spaces."""
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(float)
    cleaned = (
        series.astype(str)
        .str.strip()
        .str.replace(r"[€$%\s]", "", regex=True)
        .str.replace(",", "", regex=False)  # thousands separators (1,537,000)
    )
    return pd.to_numeric(cleaned, errors="coerce")


def calc_score(row: pd.Series, rules: dict) -> float:
    """Graded score: gentle 'excellence' deductions apply always (so two suppliers
    above target still differ), hard penalties apply when a KPI breaches its target.
    A perfect supplier (100% delivery, 100% quality, 0d lead, 0% complaints,
    0% price deviation) scores 100; everyone else scores below it."""
    score = 100.0

    # ── Gentle excellence deductions (always active) ──
    if pd.notna(row.get(COL_DELIVERY)):
        score -= max(0.0, 100.0 - row[COL_DELIVERY]) * 0.4
    if pd.notna(row.get(COL_QUALITY)):
        score -= max(0.0, 100.0 - row[COL_QUALITY]) * 0.5
    if pd.notna(row.get(COL_LEADTIME)):
        score -= max(0.0, row[COL_LEADTIME]) * 0.15
    if pd.notna(row.get(COL_COMPLAINT)):
        score -= max(0.0, row[COL_COMPLAINT]) * 1.0
    if pd.notna(row.get(COL_PRICE_DEV)):
        score -= abs(row[COL_PRICE_DEV]) * 0.4

    # ── Hard penalties (only when target is breached) ──
    if pd.notna(row.get(COL_DELIVERY)) and row[COL_DELIVERY] < rules["delivery_target"]:
        score -= (rules["delivery_target"] - row[COL_DELIVERY]) * 1.5
    if pd.notna(row.get(COL_LEADTIME)) and row[COL_LEADTIME] > rules["leadtime_limit"]:
        score -= (row[COL_LEADTIME] - rules["leadtime_limit"]) * 1.8
    if pd.notna(row.get(COL_QUALITY)) and row[COL_QUALITY] < rules["quality_target"]:
        score -= (rules["quality_target"] - row[COL_QUALITY]) * 2.0
    if pd.notna(row.get(COL_COMPLAINT)) and row[COL_COMPLAINT] > rules["complaint_limit"]:
        score -= (row[COL_COMPLAINT] - rules["complaint_limit"]) * 6.0
    if pd.notna(row.get(COL_PRICE_DEV)) and abs(row[COL_PRICE_DEV]) > rules["price_dev_tolerance"]:
        score -= (abs(row[COL_PRICE_DEV]) - rules["price_dev_tolerance"]) * 3.0

    return float(np.clip(round(score, 1), 0.0, 100.0))


def risk_label(score: float) -> str:
    if score >= 90:
        return "Low"
    if score >= 75:
        return "Medium"
    return "High"


def status_text_from_risk(risk: str) -> str:
    return {"Low": "Green / Good", "Medium": "Yellow / Monitor", "High": "Red / High Risk"}.get(str(risk), "Green / Good")


def initials(name: str) -> str:
    text = str(name).strip()
    if not text:
        return "?"
    parts = text.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return text[:2].upper()


def status_html(status: str) -> str:
    text = str(status).lower()
    if "high" in text or "red" in text:
        return '<span class="status-high">High Risk</span>'
    if "risk" in text or "monitor" in text or "medium" in text or "yellow" in text:
        return '<span class="status-risk">At Risk</span>'
    return '<span class="status-active">Active</span>'


def score_color(score: float) -> str:
    if score >= 90:
        return "#3fb950"
    if score >= 75:
        return "#d29922"
    return "#f85149"


FLAGS = {
    "austria": "🇦🇹", "china": "🇨🇳", "czech republic": "🇨🇿", "czechia": "🇨🇿",
    "france": "🇫🇷", "germany": "🇩🇪", "india": "🇮🇳", "italy": "🇮🇹",
    "mexico": "🇲🇽", "netherlands": "🇳🇱", "poland": "🇵🇱", "spain": "🇪🇸",
    "turkey": "🇹🇷", "usa": "🇺🇸", "united states": "🇺🇸",
    "united states of america": "🇺🇸", "uk": "🇬🇧", "united kingdom": "🇬🇧",
    "vietnam": "🇻🇳", "japan": "🇯🇵", "south korea": "🇰🇷", "switzerland": "🇨🇭",
    "sweden": "🇸🇪", "hungary": "🇭🇺", "portugal": "🇵🇹", "romania": "🇷🇴",
    "slovakia": "🇸🇰", "brazil": "🇧🇷", "canada": "🇨🇦",
}


def country_with_flag(country: str) -> str:
    text = str(country).strip()
    if bool(st.session_state["show_country_flags"]):
        return f"{FLAGS.get(text.lower(), '🏳️')} {text}"
    return text


def price_signal(value: float) -> str:
    if pd.isna(value):
        return "—"
    if value > 0:
        return f"🔴 ▲ +{value:.2f}%"
    if value < 0:
        return f"🟢 ▼ {value:.2f}%"
    return "🟢 ● 0.00%"


def fmt_spend(value: float) -> str:
    if pd.isna(value) or value <= 0:
        return "—"
    if value >= 1_000_000:
        return f"€{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"€{value / 1_000:.0f}k"
    return f"€{value:.0f}"


def plotly_theme(height: int = 280) -> dict:
    return {
        "height": height,
        "plot_bgcolor": "rgba(0,0,0,0)",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": "#c9d1d9", "size": 11},
        "margin": {"t": 25, "b": 35, "l": 35, "r": 15},
        "xaxis": {"gridcolor": "#21262d", "linecolor": "#30363d", "zerolinecolor": "#30363d"},
        "yaxis": {"gridcolor": "#21262d", "linecolor": "#30363d", "zerolinecolor": "#30363d"},
        "legend": {"font": {"color": "#c9d1d9", "size": 10}},
    }


def issue_text(row: pd.Series, rules: dict) -> str:
    issues = []
    if pd.notna(row.get("Delivery")) and row["Delivery"] < rules["delivery_threshold"]:
        issues.append(f"Delivery below threshold ({row['Delivery']:.1f}%)")
    if pd.notna(row.get("Quality")) and row["Quality"] < rules["quality_threshold"]:
        issues.append(f"Quality below threshold ({row['Quality']:.1f}%)")
    if pd.notna(row.get("LeadTime")) and row["LeadTime"] > rules["leadtime_threshold"]:
        issues.append(f"Lead time above threshold ({row['LeadTime']:.1f} days)")
    if pd.notna(row.get("Complaint")) and row["Complaint"] > rules["complaint_threshold"]:
        issues.append(f"Complaint rate high ({row['Complaint']:.2f}%)")
    if pd.notna(row.get("PriceDev")) and abs(row["PriceDev"]) > rules["price_threshold"]:
        issues.append(f"Price deviation outside tolerance ({row['PriceDev']:+.2f}%)")
    return " · ".join(issues) if issues else "No critical KPI issue"


def issue_chips(row: pd.Series, rules: dict) -> str:
    """Compact, scannable chips — one per breached KPI — instead of sentences."""
    chips = []
    if pd.notna(row.get("Delivery")) and row["Delivery"] < rules["delivery_threshold"]:
        sev = "" if row["Delivery"] < rules["delivery_threshold"] - 5 else " amber"
        chips.append(f'<span class="kpi-chip{sev}" title="Delivery below {rules["delivery_threshold"]:.0f}% threshold">🚚 {row["Delivery"]:.1f}%</span>')
    if pd.notna(row.get("Quality")) and row["Quality"] < rules["quality_threshold"]:
        sev = "" if row["Quality"] < rules["quality_threshold"] - 5 else " amber"
        chips.append(f'<span class="kpi-chip{sev}" title="Quality below {rules["quality_threshold"]:.0f}% threshold">🛡️ {row["Quality"]:.1f}%</span>')
    if pd.notna(row.get("LeadTime")) and row["LeadTime"] > rules["leadtime_threshold"]:
        sev = "" if row["LeadTime"] > rules["leadtime_threshold"] + 5 else " amber"
        chips.append(f'<span class="kpi-chip{sev}" title="Lead time above {rules["leadtime_threshold"]:.0f}d threshold">⏱️ {row["LeadTime"]:.0f}d</span>')
    if pd.notna(row.get("Complaint")) and row["Complaint"] > rules["complaint_threshold"]:
        sev = "" if row["Complaint"] > rules["complaint_threshold"] * 3 else " amber"
        chips.append(f'<span class="kpi-chip{sev}" title="Complaint rate above {rules["complaint_threshold"]:.1f}% limit">📣 {row["Complaint"]:.1f}%</span>')
    if pd.notna(row.get("PriceDev")) and abs(row["PriceDev"]) > rules["price_threshold"]:
        sev = "" if abs(row["PriceDev"]) > rules["price_threshold"] * 5 else " amber"
        chips.append(f'<span class="kpi-chip{sev}" title="Price deviation outside ±{rules["price_threshold"]:.1f}% tolerance">💶 {row["PriceDev"]:+.1f}%</span>')
    return '<div class="chip-row">' + "".join(chips) + "</div>" if chips else ""


@st.cache_data(show_spinner=False)
def load_excel(file_bytes: bytes) -> pd.DataFrame:
    df = pd.read_excel(io.BytesIO(file_bytes))
    df.columns = [str(c).strip() for c in df.columns]
    return df


# ══════════════════════════════════════════════════════════════════════════
# Sidebar
# ══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="logo-box">📦 SupplierDash</div>', unsafe_allow_html=True)
    page_options = [
        "🏠 Overview", "👥 Suppliers", "📈 Performance", "⚠️ Anomalies", "🔔 Alerts",
        "🏅 Scorecards", "💰 Spend Analysis", "📂 Category Insights", "🌍 Country Insights",
        "📊 Trends", "📄 Contracts", "✅ Assessments", "📁 Documents", "⚙️ Settings", "👤 Users & Roles",
    ]
    st.markdown('<div class="side-title">Navigation</div>', unsafe_allow_html=True)
    page = st.radio("Navigation", page_options, label_visibility="collapsed", key="page_nav")

# ══════════════════════════════════════════════════════════════════════════
# Top bar + uploader
# ══════════════════════════════════════════════════════════════════════════
now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
st.markdown(
    f"""
<div class="top-bar">
  <div>
    <div class="top-title">Supplier Performance Dashboard</div>
    <div class="top-sub">Real-time supplier KPI monitoring &amp; anomaly detection</div>
  </div>
  <div style="font-size:.78rem;color:#8b949e;">🕐 {now_str}</div>
</div>
""",
    unsafe_allow_html=True,
)

upload_col, note_col = st.columns([1.4, 4.8])
with upload_col:
    uploaded_file = st.file_uploader("Upload supplier Excel", type=["xlsx", "xls"], label_visibility="collapsed")
with note_col:
    st.caption(
        "Upload your supplier KPI Excel file — columns can be in **any order** and use flexible names. "
        "If a required column isn't auto-detected you can map it manually."
    )


# ══════════════════════════════════════════════════════════════════════════
# Settings page (works with or without data)
# ══════════════════════════════════════════════════════════════════════════
def render_settings(raw_data: pd.DataFrame | None = None,
                    clean_data: pd.DataFrame | None = None,
                    quality_report: list[str] | None = None) -> None:
    st.markdown('<div class="s-card"><div class="s-card-title">⚙️ Dashboard Settings</div>', unsafe_allow_html=True)
    st.caption("These settings control KPI cards, anomaly detection, risk scoring, and supplier table display. "
               "They apply instantly across all pages.")

    s1, s2 = st.columns(2)
    with s1:
        st.markdown("#### KPI Targets")
        # NOTE: no value= param — the session-state key IS the value.
        st.slider("Delivery target (%)", 50.0, 100.0, step=0.5, key="delivery_target")
        st.slider("Quality target (%)", 50.0, 100.0, step=0.5, key="quality_target")
        st.slider("Lead time limit (days)", 1.0, 60.0, step=0.5, key="leadtime_limit")
        st.slider("Complaint rate limit (%)", 0.0, 20.0, step=0.1, key="complaint_limit")
        st.slider("Price deviation tolerance (+/- %)", 0.0, 25.0, step=0.1, key="price_dev_tolerance")

    with s2:
        st.markdown("#### Anomaly & Display")
        st.selectbox("Anomaly sensitivity", ["Low", "Medium", "High"], key="anomaly_sensitivity",
                     help="Low = fewer alerts · Medium = normal rules · High = stricter alerts.")
        st.slider("Top supplier table rows", 5, 50, step=1, key="top_supplier_rows")
        st.checkbox("Show country flags", key="show_country_flags")
        st.checkbox("Show delivery trend sparkline in tables", key="show_delivery_trend",
                    help="Only visible when your Excel contains a Date/Month column with multiple snapshots per supplier.")

        st.markdown("#### Reset")
        # on_click callback => runs before next rerun => safe to write widget keys
        st.button("Reset all settings to default", on_click=reset_settings)

    effective = get_effective_rules()
    st.markdown("#### Effective Anomaly Thresholds")
    threshold_df = pd.DataFrame({
        "Rule": [
            "Delivery alert if below", "Quality alert if below", "Lead time alert if above",
            "Complaint rate alert if above", "Price deviation alert if outside",
        ],
        "Effective Threshold": [
            f"{effective['delivery_threshold']:.1f}%",
            f"{effective['quality_threshold']:.1f}%",
            f"{effective['leadtime_threshold']:.1f} days",
            f"{effective['complaint_threshold']:.2f}%",
            f"±{effective['price_threshold']:.2f}%",
        ],
    })
    st.dataframe(threshold_df, width="stretch", hide_index=True)

    st.markdown("#### Data Quality Overview")
    if raw_data is None:
        st.info("Upload an Excel file to see data quality checks here.")
    else:
        dq1, dq2, dq3, dq4 = st.columns(4)
        dq1.metric("Uploaded Rows", f"{len(raw_data)}")
        dq2.metric("Valid Rows Used", f"{len(clean_data) if clean_data is not None else 0}")
        dq3.metric("Columns Detected", f"{len(raw_data.columns)}")
        dq4.metric("Missing Values", f"{int(raw_data.isna().sum().sum())}")
        st.caption(f"Duplicate full rows detected: {int(raw_data.duplicated().sum())}")
        if quality_report:
            for msg in quality_report:
                st.warning(msg)
        detected = pd.DataFrame({"Detected Columns": raw_data.columns.astype(str).tolist()})
        st.dataframe(detected, width="stretch", hide_index=True, height=240)

    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# No file uploaded
# ══════════════════════════════════════════════════════════════════════════
if uploaded_file is None:
    if page == "⚙️ Settings":
        render_settings()
        st.stop()
    st.markdown(
        """
<div class="s-card" style="max-width:680px;margin:55px auto;text-align:center;">
  <div style="font-size:3rem;margin-bottom:12px;">📂</div>
  <div style="font-size:1.2rem;font-weight:900;color:#e6edf3;margin-bottom:8px;">Upload your supplier data</div>
  <div style="font-size:.88rem;color:#8b949e;line-height:1.55;">
    Required (any order, flexible names): <b>Supplier Name, Country, Category, Delivery Performance %,
    Lead Time Days, Quality Score %, Complaint Rate %, Price Deviation %</b>.<br><br>
    Optional: Supplier ID, Region, Supplier Tier, Spend, ESG Score, Status, Anomaly Flag,
    Total / On-Time Shipments, Last Audit Date, Notes.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.stop()


# ══════════════════════════════════════════════════════════════════════════
# Load + column detection + manual mapping fallback
# ══════════════════════════════════════════════════════════════════════════
raw = load_excel(uploaded_file.getvalue())

if raw.empty:
    st.error("The Excel file is empty — no rows were found.")
    st.stop()

col_map = auto_detect_columns(raw)
missing_required = [c for c in REQUIRED_COLS if col_map.get(c) is None]

# Delivery % can be derived from shipments if missing
can_derive_delivery = (
    COL_DELIVERY in missing_required
    and col_map.get(COL_TOTAL_SHIP) is not None
    and col_map.get(COL_ONTIME_SHIP) is not None
)
if can_derive_delivery:
    missing_required = [c for c in missing_required if c != COL_DELIVERY]

if missing_required:
    st.warning(
        "Some required columns could not be auto-detected: **"
        + ", ".join(missing_required)
        + "**. Map them manually below."
    )
    with st.expander("🔧 Manual Column Mapping", expanded=True):
        file_cols = ["— not present —"] + raw.columns.astype(str).tolist()
        for internal in REQUIRED_COLS:
            current = col_map.get(internal)
            idx = file_cols.index(current) if current in file_cols else 0
            choice = st.selectbox(
                f"Column for **{internal}**", file_cols, index=idx, key=f"map_{internal}",
            )
            col_map[internal] = None if choice == "— not present —" else choice

    still_missing = [c for c in REQUIRED_COLS if col_map.get(c) is None
                     and not (c == COL_DELIVERY and can_derive_delivery)]
    if still_missing:
        st.error("Still missing: " + ", ".join(still_missing)
                 + ". The dashboard cannot run without these columns.")
        st.stop()

# Rename to internal names
rename_map = {actual: internal for internal, actual in col_map.items() if actual is not None}
df = raw.rename(columns=rename_map).copy()

# ── Numeric cleaning with validation report ───────────────────────────────
quality_report: list[str] = []
for col in NUMERIC_COLS:
    if col in df.columns:
        before_nonnull = df[col].notna().sum()
        df[col] = clean_numeric(df[col])
        invalid = int(before_nonnull - df[col].notna().sum())
        if invalid > 0:
            quality_report.append(
                f"Column **{col}**: {invalid} value(s) were text/invalid and could not be "
                f"converted to numbers (e.g. words in a number column). These rows were affected."
            )
        # text column accidentally mapped to a numeric KPI?
        if col in REQUIRED_COLS and df[col].notna().sum() < max(1, len(df) * 0.5):
            st.error(
                f"Column mapped to **{col}** contains mostly non-numeric data — it looks like a "
                f"text column was mapped to a numeric KPI. Please check your file or the manual mapping."
            )
            st.stop()

# Derive delivery from shipments if needed
if COL_DELIVERY not in df.columns and can_derive_delivery:
    with np.errstate(divide="ignore", invalid="ignore"):
        df[COL_DELIVERY] = (df[COL_ONTIME_SHIP] / df[COL_TOTAL_SHIP] * 100).round(1)
    quality_report.append("Delivery_Performance_% was derived from On_Time_Shipments / Total_Shipments.")

rows_before = len(df)
df = df.dropna(subset=[c for c in REQUIRED_COLS if c in df.columns]).copy()
dropped = rows_before - len(df)
if dropped > 0:
    quality_report.append(f"{dropped} row(s) were dropped because required KPI values were missing or invalid.")

if df.empty:
    st.error("After cleaning, no valid supplier rows remain. Check the numeric KPI columns in your file.")
    st.stop()

# Optional columns / fallbacks
if COL_ID not in df.columns:
    df[COL_ID] = [f"S{i + 1:03d}" for i in range(len(df))]
if COL_SPEND not in df.columns:
    df[COL_SPEND] = np.nan
if COL_REGION not in df.columns:
    df[COL_REGION] = "—"
if COL_TIER not in df.columns:
    df[COL_TIER] = "—"
if COL_ESG not in df.columns:
    df[COL_ESG] = np.nan
if COL_AUDIT in df.columns:
    df[COL_AUDIT] = pd.to_datetime(df[COL_AUDIT], errors="coerce")
if COL_DATE in df.columns:
    df[COL_DATE] = pd.to_datetime(df[COL_DATE], errors="coerce")

# A real time trend is only possible when the file contains a date/month column
# with at least 2 distinct periods (i.e. multiple snapshots per supplier).
HAS_TIME = (
    COL_DATE in df.columns
    and df[COL_DATE].notna().sum() > 0
    and df[COL_DATE].dt.to_period("M").nunique() >= 2
)

# Per-supplier monthly delivery series for the table sparkline (REAL data only —
# no synthetic trends; the sparkline column is hidden when there is no time data).
DELIVERY_TREND_MAP: dict[str, list[float]] = {}
if HAS_TIME:
    _t = df.dropna(subset=[COL_DATE, COL_DELIVERY]).copy()
    _t["_m"] = _t[COL_DATE].dt.to_period("M").dt.to_timestamp()
    _series = _t.groupby([_t[COL_SUPPLIER].astype(str), "_m"])[COL_DELIVERY].mean().sort_index()
    DELIVERY_TREND_MAP = {
        name: [round(float(v), 1) for v in grp.values]
        for name, grp in _series.groupby(level=0)
    }

# ── Scoring + anomalies (rules computed fresh, AFTER settings state) ──────
RULES = get_effective_rules()

df[COL_SCORE] = df.apply(lambda r: calc_score(r, RULES), axis=1)
df["_risk"] = df[COL_SCORE].apply(risk_label)
df[COL_STATUS] = df["_risk"].apply(status_text_from_risk)


def count_anomalies(row: pd.Series) -> int:
    n = 0
    n += int(pd.notna(row[COL_DELIVERY]) and row[COL_DELIVERY] < RULES["delivery_threshold"])
    n += int(pd.notna(row[COL_LEADTIME]) and row[COL_LEADTIME] > RULES["leadtime_threshold"])
    n += int(pd.notna(row[COL_QUALITY]) and row[COL_QUALITY] < RULES["quality_threshold"])
    n += int(pd.notna(row[COL_COMPLAINT]) and row[COL_COMPLAINT] > RULES["complaint_threshold"])
    n += int(pd.notna(row[COL_PRICE_DEV]) and abs(row[COL_PRICE_DEV]) > RULES["price_threshold"])
    return n


df["_anomaly"] = df.apply(count_anomalies, axis=1)

agg_dict: dict = {
    "Supplier_ID": (COL_ID, "first"),
    "Country": (COL_COUNTRY, "first"),
    "Region": (COL_REGION, "first"),
    "Category": (COL_CATEGORY, "first"),
    "Tier": (COL_TIER, "first"),
    "Delivery": (COL_DELIVERY, "mean"),
    "LeadTime": (COL_LEADTIME, "mean"),
    "Quality": (COL_QUALITY, "mean"),
    "Complaint": (COL_COMPLAINT, "mean"),
    "PriceDev": (COL_PRICE_DEV, "mean"),
    "ESG": (COL_ESG, "mean"),
    "Score": (COL_SCORE, "mean"),
    "Spend": (COL_SPEND, "sum"),
    "Anomalies": ("_anomaly", "sum"),
    "Status": (COL_STATUS, "first"),
    "Risk": ("_risk", "first"),
}
if COL_NOTES in df.columns:
    agg_dict["Notes"] = (COL_NOTES, "first")
if COL_AUDIT in df.columns:
    agg_dict["LastAudit"] = (COL_AUDIT, "max")

agg = (
    df.groupby(COL_SUPPLIER, as_index=False)
    .agg(**agg_dict)
    .sort_values("Score", ascending=False)
    .reset_index(drop=True)
)
for nc in ["Delivery", "LeadTime", "Quality", "Complaint", "PriceDev", "ESG", "Score", "Spend"]:
    if nc in agg.columns:
        agg[nc] = pd.to_numeric(agg[nc], errors="coerce").round(2)

HAS_SPEND = agg["Spend"].notna().any() and agg["Spend"].sum(skipna=True) > 0

# ── Settings page (with data context) ─────────────────────────────────────
if page == "⚙️ Settings":
    render_settings(raw_data=raw, clean_data=df, quality_report=quality_report)
    st.markdown(
        '<div style="text-align:center;color:#6e7681;font-size:.75rem;padding:24px 0 8px;">'
        'SupplierDash · Interactive KPI Monitoring · Powered by Streamlit</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# Show data quality warnings once (non-blocking) on other pages
if quality_report:
    with st.expander(f"⚠️ Data quality notes ({len(quality_report)})", expanded=False):
        for msg in quality_report:
            st.warning(msg)

# ══════════════════════════════════════════════════════════════════════════
# Filters
# ══════════════════════════════════════════════════════════════════════════
f1, f2, f3, f4, f5 = st.columns([1.35, 1.35, 1.28, 1.28, 2.15])
with f1:
    sel_country = st.selectbox(
        "Country", ["All Countries"] + sorted(agg["Country"].dropna().astype(str).unique().tolist()),
        key="filter_country")
with f2:
    sel_category = st.selectbox(
        "Category", ["All Categories"] + sorted(agg["Category"].dropna().astype(str).unique().tolist()),
        key="filter_category")
with f3:
    sel_status = st.selectbox(
        "Supplier Status", ["All Statuses"] + sorted(agg["Status"].dropna().astype(str).unique().tolist()),
        key="filter_status")
with f4:
    sel_risk = st.selectbox("Risk Level", ["All Risk Levels", "Low", "Medium", "High"], key="filter_risk")
with f5:
    search_q = st.text_input("🔍 Search suppliers...", placeholder="Search suppliers...", key="filter_search")

filt = agg.copy()
if sel_country != "All Countries":
    filt = filt[filt["Country"].astype(str) == sel_country]
if sel_category != "All Categories":
    filt = filt[filt["Category"].astype(str) == sel_category]
if sel_status != "All Statuses":
    filt = filt[filt["Status"].astype(str) == sel_status]
if sel_risk != "All Risk Levels":
    filt = filt[filt["Risk"] == sel_risk]
if search_q.strip():
    q = search_q.strip().lower()
    filt = filt[filt[COL_SUPPLIER].astype(str).str.lower().str.contains(q, na=False)]
filt = filt.reset_index(drop=True)

if filt.empty:
    st.warning("No suppliers match the selected filters. Change filters or clear the search box.")
    st.stop()

supplier_names = filt[COL_SUPPLIER].astype(str).tolist()
if "selected_supplier" not in st.session_state or st.session_state["selected_supplier"] not in supplier_names:
    st.session_state["selected_supplier"] = supplier_names[0]

_current_selected = st.session_state["selected_supplier"]
_sel_row = filt[filt[COL_SUPPLIER].astype(str) == _current_selected].iloc[0]

# ══════════════════════════════════════════════════════════════════════════
# KPI bar
# ══════════════════════════════════════════════════════════════════════════
avg_delivery = filt["Delivery"].mean()
avg_lead = filt["LeadTime"].mean()
avg_quality = filt["Quality"].mean()
avg_complaint = filt["Complaint"].mean()
active_suppliers = len(filt)
anomaly_breaches = int(filt["Anomalies"].sum())
flagged_suppliers = int((filt["Anomalies"] > 0).sum())
_sel_score = float(_sel_row["Score"])
_sel_color = score_color(_sel_score)
_sel_name_short = str(_current_selected)[:18] + ("…" if len(str(_current_selected)) > 18 else "")

st.markdown(
    f"""
<div class="metric-grid">
  <div class="kpi-card">
    <div class="kpi-icon" style="background:rgba(56,139,253,.12);">🚚</div>
    <div><div class="kpi-label">On-Time Delivery %</div><div class="kpi-value">{avg_delivery:.1f}%</div>
    <div class="{'kpi-good' if avg_delivery >= RULES['delivery_target'] else 'kpi-bad'}">{'▲ meets' if avg_delivery >= RULES['delivery_target'] else '▼ below'} {RULES['delivery_target']:.1f}% target</div></div>
  </div>
  <div class="kpi-card">
    <div class="kpi-icon" style="background:rgba(163,113,247,.12);">⏱️</div>
    <div><div class="kpi-label">Avg Lead Time</div><div class="kpi-value">{avg_lead:.1f}d</div>
    <div class="{'kpi-good' if avg_lead <= RULES['leadtime_limit'] else 'kpi-bad'}">{'▼ within' if avg_lead <= RULES['leadtime_limit'] else '▲ above'} {RULES['leadtime_limit']:.1f}d target</div></div>
  </div>
  <div class="kpi-card">
    <div class="kpi-icon" style="background:rgba(63,185,80,.12);">🛡️</div>
    <div><div class="kpi-label">Quality Score</div><div class="kpi-value">{avg_quality:.1f}%</div>
    <div class="{'kpi-good' if avg_quality >= RULES['quality_target'] else 'kpi-bad'}">{'▲ meets' if avg_quality >= RULES['quality_target'] else '▼ below'} {RULES['quality_target']:.1f}% target</div></div>
  </div>
  <div class="kpi-card">
    <div class="kpi-icon" style="background:rgba(248,81,73,.12);">⚠️</div>
    <div><div class="kpi-label">Complaint Rate</div><div class="kpi-value">{avg_complaint:.2f}%</div>
    <div class="{'kpi-good' if avg_complaint <= RULES['complaint_limit'] else 'kpi-bad'}">{'▼ within' if avg_complaint <= RULES['complaint_limit'] else '▲ above'} {RULES['complaint_limit']:.1f}% limit</div></div>
  </div>
  <div class="kpi-card">
    <div class="kpi-icon" style="background:rgba(56,139,253,.12);">👥</div>
    <div><div class="kpi-label">Active Suppliers</div><div class="kpi-value">{active_suppliers}</div>
    <div class="kpi-muted">in current filter</div></div>
  </div>
  <div class="kpi-card">
    <div class="kpi-icon" style="background:rgba(210,153,34,.12);">🔔</div>
    <div><div class="kpi-label">Suppliers Flagged</div><div class="kpi-value">{flagged_suppliers}</div>
    <div class="{'kpi-bad' if flagged_suppliers > 0 else 'kpi-good'}">{f'{anomaly_breaches} KPI breaches' if flagged_suppliers > 0 else 'all clear'}</div></div>
  </div>
  <div class="kpi-card">
    <div class="kpi-icon" style="background:rgba(88,166,255,.10);">🔍</div>
    <div><div class="kpi-label">Selected Supplier</div>
    <div class="kpi-value" style="font-size:1.1rem;color:{_sel_color};">{_sel_score:.0f}<span style="font-size:.85rem;color:#8b949e;">/100</span></div>
    <div class="kpi-selected-name" title="{_current_selected}">{_sel_name_short}</div></div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════════════════════════
# Shared render blocks
# ══════════════════════════════════════════════════════════════════════════
def render_supplier_selector() -> pd.Series:
    selected = st.selectbox(
        "View supplier profile ↓", supplier_names,
        index=supplier_names.index(st.session_state["selected_supplier"]),
        key="selected_supplier",
    )
    return filt[filt[COL_SUPPLIER].astype(str) == selected].iloc[0]


def render_supplier_profile(row: pd.Series) -> None:
    color = score_color(float(row["Score"]))
    price_color = "#f85149" if row["PriceDev"] > 0 else "#3fb950"
    esg_html = ""
    if pd.notna(row.get("ESG")):
        esg_html = f'<div><div class="kpi-label">ESG Score</div><div style="font-weight:900;color:#58a6ff;">{row["ESG"]:.1f}</div></div>'
    spend_html = ""
    if HAS_SPEND and pd.notna(row.get("Spend")) and row["Spend"] > 0:
        spend_html = f'<div><div class="kpi-label">Spend</div><div style="font-weight:900;color:#e6edf3;">{fmt_spend(row["Spend"])}</div></div>'
    audit_html = ""
    if "LastAudit" in row.index and pd.notna(row.get("LastAudit")):
        audit_html = f'<div style="margin-top:12px;font-size:.74rem;color:#8b949e;">🗓️ Last audit: {pd.Timestamp(row["LastAudit"]).strftime("%d.%m.%Y")}</div>'
    tier = str(row.get("Tier", "—"))
    tier_txt = f" · {tier}" if tier not in ("—", "nan", "") else ""

    st.markdown(
        f"""
<div class="s-card">
  <div class="s-card-title">Selected Supplier</div>
  <div style="display:flex;gap:12px;align-items:center;margin-bottom:14px;">
    <div class="profile-avatar">{initials(row[COL_SUPPLIER])}</div>
    <div>
      <div style="font-weight:900;font-size:1rem;color:#e6edf3;">{row[COL_SUPPLIER]}</div>
      <div style="font-size:.78rem;color:#8b949e;">{row['Category']} · {country_with_flag(row['Country'])}{tier_txt}</div>
      <div style="margin-top:5px;">{status_html(row['Status'])}</div>
    </div>
  </div>
  <div style="font-size:.75rem;color:#8b949e;">Overall Score</div>
  <div style="font-size:2.15rem;font-weight:900;color:{color};">{row['Score']:.0f}<span style="font-size:1rem;color:#8b949e;">/100</span></div>
  <div style="height:8px;background:#21262d;border-radius:8px;overflow:hidden;margin:6px 0 16px 0;">
    <div style="height:8px;width:{max(min(float(row['Score']), 100), 0)}%;background:{color};"></div>
  </div>
  <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;">
    <div><div class="kpi-label">Delivery</div><div style="font-weight:900;color:{'#3fb950' if row['Delivery'] >= RULES['delivery_target'] else '#f85149'};">{row['Delivery']:.1f}%</div></div>
    <div><div class="kpi-label">Quality</div><div style="font-weight:900;color:{'#3fb950' if row['Quality'] >= RULES['quality_target'] else '#f85149'};">{row['Quality']:.1f}%</div></div>
    <div><div class="kpi-label">Lead Time</div><div style="font-weight:900;color:{'#3fb950' if row['LeadTime'] <= RULES['leadtime_limit'] else '#f85149'};">{row['LeadTime']:.1f}d</div></div>
    <div><div class="kpi-label">Complaints</div><div style="font-weight:900;color:{'#3fb950' if row['Complaint'] <= RULES['complaint_limit'] else '#f85149'};">{row['Complaint']:.2f}%</div></div>
    <div><div class="kpi-label">Price Dev</div><div style="font-weight:900;color:{price_color};">{row['PriceDev']:+.2f}%</div></div>
    <div><div class="kpi-label">Anomalies</div><div style="font-weight:900;color:#e6edf3;">{int(row['Anomalies'])}</div></div>
    {esg_html}{spend_html}
  </div>
  {audit_html}
</div>
""",
        unsafe_allow_html=True,
    )


def render_top_table(data: pd.DataFrame, rows: int | None = None) -> None:
    if rows is None:
        rows = int(st.session_state["top_supplier_rows"])

    table_df = data.sort_values("Score", ascending=False).head(rows).reset_index(drop=True).copy()
    table_df["CountryDisp"] = table_df["Country"].apply(country_with_flag)
    table_df["Price Signal"] = table_df["PriceDev"].apply(price_signal)

    display_cols = [COL_SUPPLIER, "Category", "CountryDisp", "Delivery", "Quality",
                    "LeadTime", "Complaint", "Price Signal", "Status", "Risk", "Score"]

    show_trend = bool(st.session_state["show_delivery_trend"]) and HAS_TIME
    if show_trend:
        table_df["Delivery Trend"] = table_df[COL_SUPPLIER].map(
            lambda n: DELIVERY_TREND_MAP.get(str(n), []))
        display_cols.insert(4, "Delivery Trend")

    display_df = table_df[display_cols].rename(columns={
        COL_SUPPLIER: "Supplier", "CountryDisp": "Country", "Delivery": "Delivery %",
        "Quality": "Quality %", "LeadTime": "Lead Time", "Complaint": "Complaint %",
        "Price Signal": "Price Dev %",
    })

    column_config = {
        "Supplier": st.column_config.TextColumn("Supplier", width="medium"),
        "Category": st.column_config.TextColumn("Category", width="medium"),
        "Country": st.column_config.TextColumn("Country", width="medium"),
        "Delivery %": st.column_config.ProgressColumn("Delivery %", format="%.1f%%", min_value=0, max_value=100, width="medium"),
        "Quality %": st.column_config.ProgressColumn("Quality %", format="%.1f%%", min_value=0, max_value=100, width="medium"),
        "Lead Time": st.column_config.NumberColumn("Lead Time", format="%.1f d", width="small"),
        "Complaint %": st.column_config.NumberColumn("Complaint %", format="%.2f%%", width="small"),
        "Price Dev %": st.column_config.TextColumn("Price Dev %", width="small"),
        "Status": st.column_config.TextColumn("Status", width="medium"),
        "Risk": st.column_config.TextColumn("Risk", width="small"),
        "Score": st.column_config.ProgressColumn("Score", format="%.1f", min_value=0, max_value=100, width="medium"),
    }
    if show_trend:
        column_config["Delivery Trend"] = st.column_config.LineChartColumn("Delivery Trend", y_min=0, y_max=100, width="medium")

    st.dataframe(display_df, width="stretch", hide_index=True, height=460, column_config=column_config)


# ══════════════════════════════════════════════════════════════════════════
# Pages
# ══════════════════════════════════════════════════════════════════════════
def render_overview() -> None:
    left, right = st.columns([3.1, 1.1])
    with left:
        if HAS_TIME:
            st.markdown('<div class="s-card"><div class="s-card-title">📈 KPI Trend Over Time — Delivery vs Quality</div>', unsafe_allow_html=True)
            dft = df[df[COL_SUPPLIER].astype(str).isin(supplier_names)].copy()
            dft["_month"] = dft[COL_DATE].dt.to_period("M").dt.to_timestamp()
            ts = dft.groupby("_month", as_index=False).agg(
                Delivery=(COL_DELIVERY, "mean"), Quality=(COL_QUALITY, "mean"))
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ts["_month"], y=ts["Delivery"], mode="lines+markers",
                                     name="On-Time Delivery %", line=dict(color="#388bfd", width=2)))
            fig.add_trace(go.Scatter(x=ts["_month"], y=ts["Quality"], mode="lines+markers",
                                     name="Quality Score %", line=dict(color="#3fb950", width=2)))
            x_title = "Month"
        else:
            st.markdown('<div class="s-card"><div class="s-card-title">📊 Delivery vs Quality — Supplier Comparison (Top 15 by Score)</div>', unsafe_allow_html=True)
            trend = filt.sort_values("Score", ascending=False).head(15)
            fig = go.Figure()
            fig.add_trace(go.Bar(x=trend[COL_SUPPLIER], y=trend["Delivery"], name="On-Time Delivery %",
                                 marker_color="#388bfd", opacity=0.85))
            fig.add_trace(go.Scatter(x=trend[COL_SUPPLIER], y=trend["Quality"], mode="lines+markers",
                                     name="Quality Score %", line=dict(color="#3fb950", width=2)))
            x_title = "Supplier"
        fig.add_hline(y=RULES["delivery_target"], line_dash="dash", line_color="rgba(56,139,253,.45)", annotation_text="Delivery target")
        fig.add_hline(y=RULES["quality_target"], line_dash="dash", line_color="rgba(63,185,80,.45)", annotation_text="Quality target")
        theme = plotly_theme(300)
        theme["xaxis"]["title"] = x_title
        theme["yaxis"]["title"] = "Score (%)"
        fig.update_layout(**theme, xaxis_tickangle=-35 if not HAS_TIME else 0,
                          barmode="group", yaxis_range=[None, 102])
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": True})
        if not HAS_TIME:
            st.caption("💡 This is a supplier comparison, not a time trend — your file has one snapshot per supplier. "
                       "Add a **Date / Month** column with multiple rows per supplier and this chart automatically becomes a real KPI-over-time trend.")
        st.markdown("</div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="s-card"><div class="s-card-title">📦 Score by Category</div>', unsafe_allow_html=True)
            cat = filt.groupby("Category", as_index=False)["Score"].mean().sort_values("Score")
            fig_cat = px.bar(cat, x="Score", y="Category", orientation="h", color="Score",
                             color_continuous_scale="Blues", range_color=[50, 100],
                             labels={"Score": "Avg Overall Score", "Category": "Category"})
            fig_cat.update_layout(**plotly_theme(260), coloraxis_showscale=False)
            st.plotly_chart(fig_cat, width="stretch", config={"displayModeBar": True})
            st.markdown("</div>", unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="s-card"><div class="s-card-title">🌍 Supplier Count by Country</div>', unsafe_allow_html=True)
            cc = filt["Country"].value_counts().reset_index()
            cc.columns = ["Country", "Count"]
            cc["Country"] = cc["Country"].apply(country_with_flag)
            fig_country = px.pie(cc.head(10), names="Country", values="Count", hole=0.55)
            fig_country.update_layout(**plotly_theme(260), showlegend=True)
            st.plotly_chart(fig_country, width="stretch", config={"displayModeBar": True})
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="s-card"><div class="s-card-title">🏆 Top Suppliers</div>', unsafe_allow_html=True)
        render_top_table(filt)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        # Selector sits directly above the profile card it controls
        selected_row = render_supplier_selector()
        render_supplier_profile(selected_row)

        st.markdown('<div class="s-card" style="margin-top:.8rem;"><div class="s-card-title">⚠️ Anomaly Detection</div>', unsafe_allow_html=True)
        anomalies = filt[filt["Anomalies"] > 0].sort_values("Score").head(8)
        if anomalies.empty:
            st.success("No anomalies detected in current filters.")
        else:
            st.markdown('<div class="chip-legend">🚚 Delivery · 🛡️ Quality · ⏱️ Lead time · 📣 Complaints · 💶 Price dev</div>', unsafe_allow_html=True)
            for _, a in anomalies.iterrows():
                badge = "alert-badge-high" if a["Score"] < 75 else "alert-badge-med"
                level = "High" if a["Score"] < 75 else "Medium"
                st.markdown(
                    f"""
<div class="alert-row">
  <div style="display:flex;gap:8px;align-items:center;justify-content:space-between;">
    <span class="alert-name">{a[COL_SUPPLIER]}</span><span class="{badge}">{level}</span>
  </div>
  {issue_chips(a, RULES)}
  <div class="kpi-muted" style="margin-top:.3rem;">{a["Category"]} · {country_with_flag(a["Country"])} · Score {a["Score"]:.0f}</div>
</div>
""",
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)


def render_suppliers() -> None:
    left, right = st.columns([2.45, 1])
    with right:
        selected_row = render_supplier_selector()
        render_supplier_profile(selected_row)
    with left:
        st.markdown('<div class="s-card"><div class="s-card-title">👥 Supplier Directory</div>', unsafe_allow_html=True)
        render_top_table(filt, rows=25)
        csv = filt.drop(columns=[c for c in ["Notes"] if c in filt.columns]).to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download filtered suppliers (CSV)", csv,
                           file_name="suppliers_filtered.csv", mime="text/csv")
        st.markdown("</div>", unsafe_allow_html=True)


def render_performance() -> None:
    c1, c2 = st.columns(2)
    risk_colors = {"Low": "#3fb950", "Medium": "#d29922", "High": "#f85149"}
    with c1:
        st.markdown('<div class="s-card"><div class="s-card-title">🎯 Delivery Reliability vs Quality Score</div>', unsafe_allow_html=True)
        fig = px.scatter(filt, x="Delivery", y="Quality", size="Score", color="Risk",
                         hover_name=COL_SUPPLIER, size_max=28, color_discrete_map=risk_colors,
                         labels={"Delivery": "On-Time Delivery (%)", "Quality": "Quality Score (%)"})
        fig.add_vline(x=RULES["delivery_target"], line_dash="dash", line_color="rgba(255,255,255,.25)")
        fig.add_hline(y=RULES["quality_target"], line_dash="dash", line_color="rgba(255,255,255,.25)")
        theme = plotly_theme(380)
        theme["xaxis"]["title"] = "On-Time Delivery (%)"
        theme["yaxis"]["title"] = "Quality Score (%)"
        fig.update_layout(**theme)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": True})
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="s-card"><div class="s-card-title">⏱️ Lead Time vs Complaint Rate</div>', unsafe_allow_html=True)
        fig = px.scatter(filt, x="LeadTime", y="Complaint", size="Score", color="Risk",
                         hover_name=COL_SUPPLIER, size_max=28, color_discrete_map=risk_colors,
                         labels={"LeadTime": "Lead Time (Days)", "Complaint": "Complaint Rate (%)"})
        fig.add_vline(x=RULES["leadtime_limit"], line_dash="dash", line_color="rgba(255,255,255,.25)")
        fig.add_hline(y=RULES["complaint_limit"], line_dash="dash", line_color="rgba(255,255,255,.25)")
        theme = plotly_theme(380)
        theme["xaxis"]["title"] = "Lead Time (Days)"
        theme["yaxis"]["title"] = "Complaint Rate (%)"
        fig.update_layout(**theme)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": True})
        st.markdown("</div>", unsafe_allow_html=True)


def render_anomalies() -> None:
    st.markdown('<div class="s-card"><div class="s-card-title">⚠️ Anomaly Management</div>', unsafe_allow_html=True)
    anomalies = filt[filt["Anomalies"] > 0].sort_values(["Score", "Anomalies"], ascending=[True, False]).copy()
    if anomalies.empty:
        st.success("No anomaly found in the current filter.")
    else:
        anomalies["Issue"] = anomalies.apply(lambda r: issue_text(r, RULES), axis=1)
        show = anomalies[[COL_SUPPLIER, "Category", "Country", "Delivery", "LeadTime",
                          "Quality", "Complaint", "PriceDev", "Risk", "Score", "Issue"]].copy()
        show["Country"] = show["Country"].apply(country_with_flag)
        show["PriceDev"] = show["PriceDev"].apply(price_signal)
        show = show.rename(columns={COL_SUPPLIER: "Supplier", "Delivery": "Delivery %",
                                    "LeadTime": "Lead Time", "Quality": "Quality %",
                                    "Complaint": "Complaint %", "PriceDev": "Price Dev %"})
        st.dataframe(show, width="stretch", hide_index=True, height=500)
    st.markdown("</div>", unsafe_allow_html=True)


def render_scorecards() -> None:
    st.markdown('<div class="s-card"><div class="s-card-title">🏅 Supplier Scorecards</div>', unsafe_allow_html=True)
    cols = [COL_SUPPLIER, "Category", "Country", "Tier", "Delivery", "Quality",
            "LeadTime", "Complaint", "PriceDev", "ESG", "Anomalies", "Risk", "Score"]
    sc = filt[[c for c in cols if c in filt.columns]].sort_values("Score", ascending=False).copy()
    sc["Country"] = sc["Country"].apply(country_with_flag)
    sc["PriceDev"] = sc["PriceDev"].apply(price_signal)
    if HAS_SPEND:
        sc["Spend"] = filt.sort_values("Score", ascending=False)["Spend"].apply(fmt_spend).values
    sc = sc.rename(columns={COL_SUPPLIER: "Supplier", "Delivery": "Delivery %", "Quality": "Quality %",
                            "LeadTime": "Lead Time", "Complaint": "Complaint %", "PriceDev": "Price Dev %"})
    st.dataframe(sc, width="stretch", hide_index=True, height=500)
    st.markdown("</div>", unsafe_allow_html=True)


def render_spend_analysis() -> None:
    st.markdown('<div class="s-card"><div class="s-card-title">💰 Spend Analysis</div>', unsafe_allow_html=True)
    if not HAS_SPEND:
        st.info("No Spend column was found in your Excel file. Add Spend / Annual_Spend / Total_Spend to activate real spend charts.")
        fallback = filt.groupby("Category", as_index=False)["Score"].mean().sort_values("Score", ascending=False)
        fig = px.bar(fallback, x="Category", y="Score", color="Score", color_continuous_scale="Blues",
                     labels={"Category": "Category", "Score": "Avg Overall Score"})
        fig.update_layout(**plotly_theme(420))
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": True})
    else:
        c1, c2 = st.columns(2)
        with c1:
            spend_cat = filt.groupby("Category", as_index=False)["Spend"].sum().sort_values("Spend", ascending=False)
            fig = px.bar(spend_cat, x="Category", y="Spend", color="Spend", color_continuous_scale="Blues",
                         labels={"Category": "Category", "Spend": "Total Spend (€)"})
            fig.update_layout(**plotly_theme(380))
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": True})
        with c2:
            top_spend = filt.nlargest(12, "Spend")[[COL_SUPPLIER, "Spend", "Score", "Risk"]]
            fig2 = px.bar(top_spend.sort_values("Spend"), x="Spend", y=COL_SUPPLIER, orientation="h",
                          color="Risk", color_discrete_map={"Low": "#3fb950", "Medium": "#d29922", "High": "#f85149"},
                          labels={"Spend": "Spend (€)", COL_SUPPLIER: "Supplier"})
            fig2.update_layout(**plotly_theme(380))
            st.plotly_chart(fig2, width="stretch", config={"displayModeBar": True})
        st.caption("Right chart: highest-spend suppliers colored by risk — high spend + high risk = priority for action.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_category_insights() -> None:
    st.markdown('<div class="s-card"><div class="s-card-title">📂 Category Insights</div>', unsafe_allow_html=True)
    category = filt.groupby("Category", as_index=False).agg(
        Suppliers=(COL_SUPPLIER, "count"),
        Avg_Score=("Score", "mean"),
        Avg_Delivery=("Delivery", "mean"),
        Avg_Quality=("Quality", "mean"),
        Avg_Lead_Time=("LeadTime", "mean"),
        Alerts=("Anomalies", "sum"),
    ).round(2).sort_values("Avg_Score", ascending=False)
    st.dataframe(category, width="stretch", hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_country_insights() -> None:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="s-card"><div class="s-card-title">🌍 Suppliers by Country</div>', unsafe_allow_html=True)
        country = (filt.groupby("Country", as_index=False)
                   .agg(Suppliers=(COL_SUPPLIER, "count"), Avg_Score=("Score", "mean"), Alerts=("Anomalies", "sum"))
                   .round(2).sort_values("Suppliers", ascending=False))
        country["Country"] = country["Country"].apply(country_with_flag)
        st.dataframe(country, width="stretch", hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="s-card"><div class="s-card-title">🌍 Country Score Chart</div>', unsafe_allow_html=True)
        cs = filt.groupby("Country", as_index=False)["Score"].mean().sort_values("Score", ascending=False)
        cs["Country"] = cs["Country"].apply(country_with_flag)
        fig = px.bar(cs, x="Country", y="Score", color="Score", color_continuous_scale="Blues",
                     range_color=[50, 100], labels={"Country": "Country", "Score": "Avg Overall Score"})
        fig.update_layout(**plotly_theme(360), coloraxis_showscale=False)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": True})
        st.markdown("</div>", unsafe_allow_html=True)


def render_trends() -> None:
    st.markdown('<div class="s-card"><div class="s-card-title">📊 KPI Trends / Ranking</div>', unsafe_allow_html=True)
    metric = st.selectbox("Choose KPI", ["Score", "Delivery", "Quality", "LeadTime", "Complaint", "PriceDev"],
                          key="trend_metric")
    axis_labels = {"Score": "Overall Score", "Delivery": "On-Time Delivery (%)",
                   "Quality": "Quality Score (%)", "LeadTime": "Lead Time (Days)",
                   "Complaint": "Complaint Rate (%)", "PriceDev": "Price Deviation (%)"}
    ascending = metric in ["LeadTime", "Complaint", "PriceDev"]
    trend = filt.sort_values(metric, ascending=ascending).head(20)
    fig = px.line(trend, x=COL_SUPPLIER, y=metric, markers=True,
                  hover_data=["Category", "Country", "Risk", "Score"],
                  labels={COL_SUPPLIER: "Supplier", metric: axis_labels.get(metric, metric)})
    theme = plotly_theme(430)
    theme["xaxis"]["title"] = "Supplier"
    theme["yaxis"]["title"] = axis_labels.get(metric, metric)
    fig.update_layout(**theme, xaxis_tickangle=-35)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": True})
    st.markdown("</div>", unsafe_allow_html=True)


def render_placeholder(title: str, text: str) -> None:
    st.markdown(
        f'<div class="s-card"><div class="s-card-title">{title}</div><div style="color:#8b949e;line-height:1.6;">{text}</div></div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════
# Router
# ══════════════════════════════════════════════════════════════════════════
if page == "🏠 Overview":
    render_overview()
elif page == "👥 Suppliers":
    render_suppliers()
elif page == "📈 Performance":
    render_performance()
elif page in ("⚠️ Anomalies", "🔔 Alerts"):
    render_anomalies()
elif page in ("🏅 Scorecards", "✅ Assessments"):
    render_scorecards()
elif page == "💰 Spend Analysis":
    render_spend_analysis()
elif page == "📂 Category Insights":
    render_category_insights()
elif page == "🌍 Country Insights":
    render_country_insights()
elif page == "📊 Trends":
    render_trends()
elif page == "📄 Contracts":
    render_placeholder("📄 Contracts",
                       "Contract management placeholder. Add contract expiry, contract value, owner, renewal date, and SLA columns later to make this section fully data-driven.")
elif page == "📁 Documents":
    render_placeholder("📁 Documents",
                       "Document management placeholder for supplier certificates, quality documents, compliance files, and audit reports.")
elif page == "👤 Users & Roles":
    render_placeholder("👤 Users & Roles",
                       "Users & Roles placeholder. This Streamlit demo can later be connected to authentication and role-based permissions.")

st.markdown(
    '<div style="text-align:center;color:#6e7681;font-size:.75rem;padding:24px 0 8px;">'
    'SupplierDash · Interactive KPI Monitoring · Powered by Streamlit</div>',
    unsafe_allow_html=True,
)
