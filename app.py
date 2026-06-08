from __future__ import annotations

import hashlib
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="SupplierDash",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

COL_SUPPLIER = "Supplier_Name"
COL_COUNTRY = "Country"
COL_CATEGORY = "Category"
COL_DELIVERY = "Delivery_Performance_%"
COL_LEADTIME = "Lead_Time_Days"
COL_QUALITY = "Quality_Score_%"
COL_COMPLAINT = "Complaint_Rate_%"
COL_PRICE_DEV = "Price_Deviation_%"
COL_SCORE = "Overall_Score"
COL_STATUS = "Status"
COL_ANOMALY = "Anomaly_Flag"
COL_ID = "Supplier_ID"
COL_SPEND = "Spend"
COL_NOTES = "Notes"

REQUIRED_COLS = [
    COL_SUPPLIER,
    COL_COUNTRY,
    COL_CATEGORY,
    COL_DELIVERY,
    COL_LEADTIME,
    COL_QUALITY,
    COL_COMPLAINT,
    COL_PRICE_DEV,
]

DEFAULT_SETTINGS = {
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

CFG_PREFIX = "cfg_"

# ── Init session state ────────────────────────────────────────────────────────
for _k, _v in DEFAULT_SETTINGS.items():
    if f"{CFG_PREFIX}{_k}" not in st.session_state:
        st.session_state[f"{CFG_PREFIX}{_k}"] = _v

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

html, body, [class*="css"] { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; }
.stApp { background: #0d1117 !important; color: #e6edf3 !important; }
.block-container { padding: 1rem 1.35rem 2rem 1.35rem !important; max-width: 100% !important; }
#MainMenu, footer { visibility: hidden !important; }

header[data-testid="stHeader"] {
    visibility: visible !important;
    background: transparent !important;
    height: 2.75rem !important;
}

div[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    z-index: 999999 !important;
    cursor: pointer !important;
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 9px !important;
}

div[data-testid="collapsedControl"] * { cursor: pointer !important; }

section[data-testid="stSidebar"] {
    background: #161b22 !important;
    border-right: 1px solid #30363d !important;
}

section[data-testid="stSidebar"] > div { padding: 0.8rem 0.75rem !important; }
section[data-testid="stSidebar"] * { color: #c9d1d9 !important; }

.logo-box {
    font-size: 1.05rem;
    font-weight: 900;
    color: #e6edf3;
    padding: 0.55rem 0.35rem 0.95rem 0.35rem;
    border-bottom: 1px solid #30363d;
    margin-bottom: 0.85rem;
}

.side-title {
    font-size: 0.68rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #8b949e !important;
    font-weight: 900;
    margin: 1rem 0.35rem 0.35rem 0.35rem;
}

div[role="radiogroup"] label {
    background: transparent !important;
    border-radius: 8px !important;
    padding: 0.5rem 0.6rem !important;
    margin: 0.05rem 0 !important;
    cursor: pointer !important;
}

div[role="radiogroup"] label:hover { background: #21262d !important; }
div[role="radiogroup"] label[data-baseweb="radio"] > div:first-child { display: none !important; }
div[role="radiogroup"] label p { font-size: 0.86rem !important; font-weight: 700 !important; }
div[role="radiogroup"] * { cursor: pointer !important; }

.stSelectbox, .stSelectbox *, div[data-baseweb="select"], div[data-baseweb="select"] * {
    cursor: pointer !important;
}

div[data-baseweb="select"] input,
input[aria-autocomplete="list"] {
    cursor: pointer !important;
    caret-color: transparent !important;
    user-select: none !important;
}

.stTextInput input, .stTextInput input * {
    cursor: text !important;
    caret-color: auto !important;
    user-select: text !important;
}

.stSelectbox label,
.stTextInput label,
.stFileUploader label,
.stRadio label,
.stSlider label,
.stCheckbox label,
.stNumberInput label {
    color: #8b949e !important;
    font-size: 0.78rem !important;
    font-weight: 750 !important;
}

div[data-baseweb="select"] > div,
.stTextInput input,
.stNumberInput input {
    background: #21262d !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    border-radius: 9px !important;
}

.stSlider div[data-baseweb="slider"] div { background-color: #30363d !important; }
.stSlider div[data-baseweb="slider"] div[style*="width"] { background-color: #f0f6fc !important; }

.stSlider div[role="slider"] {
    background-color: #f0f6fc !important;
    border: 2px solid #f0f6fc !important;
    box-shadow: 0 0 0 2px #30363d !important;
}

.stButton > button {
    background: #1f3a5f !important;
    border: 1px solid #388bfd !important;
    color: #58a6ff !important;
    border-radius: 9px !important;
    font-weight: 800 !important;
}

.top-bar {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 1rem 1.1rem;
    margin-bottom: 0.9rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.8rem;
    flex-wrap: wrap;
}

.top-title {
    font-size: 1.35rem;
    font-weight: 900;
    color: #e6edf3;
}

.top-sub {
    font-size: 0.82rem;
    color: #8b949e;
    margin-top: 0.15rem;
}

.metric-grid {
    display: grid;
    grid-template-columns: repeat(7, minmax(140px, 1fr));
    gap: 0.65rem;
    margin-bottom: 0.75rem;
}

@media (max-width: 1600px) {
    .metric-grid { grid-template-columns: repeat(4, minmax(160px, 1fr)); }
}

@media (max-width: 900px) {
    .metric-grid { grid-template-columns: repeat(1, minmax(160px, 1fr)); }
}

.kpi-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 1rem 1.1rem;
    display: flex;
    align-items: center;
    gap: 0.85rem;
    min-height: 92px;
}

.kpi-icon {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.15rem;
    flex-shrink: 0;
}

.kpi-label { font-size: 0.76rem; color: #8b949e; font-weight: 700; }
.kpi-value { font-size: 1.55rem; font-weight: 900; color: #e6edf3; line-height: 1.12; }
.kpi-good { font-size: 0.74rem; color: #3fb950; font-weight: 850; }
.kpi-bad { font-size: 0.74rem; color: #f85149; font-weight: 850; }
.kpi-muted { font-size: 0.72rem; color: #6e7681; }

.kpi-selected-name {
    font-size: 0.68rem;
    color: #58a6ff;
    font-weight: 800;
    margin-top: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 120px;
}

.s-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 1rem 1.1rem;
    height: 100%;
    overflow: hidden;
}

.s-card-title {
    font-size: 0.96rem;
    font-weight: 900;
    color: #e6edf3;
    margin-bottom: 0.8rem;
}

.status-active,
.status-risk,
.status-high {
    padding: 0.15rem 0.55rem;
    border-radius: 16px;
    font-size: 0.72rem;
    font-weight: 850;
    display: inline-block;
}

.status-active {
    background: rgba(63,185,80,.12);
    color: #3fb950;
    border: 1px solid rgba(63,185,80,.35);
}

.status-risk {
    background: rgba(210,153,34,.12);
    color: #d29922;
    border: 1px solid rgba(210,153,34,.35);
}

.status-high {
    background: rgba(248,81,73,.12);
    color: #f85149;
    border: 1px solid rgba(248,81,73,.35);
}

.alert-row { border-bottom: 1px solid #21262d; padding: 0.65rem 0; }
.alert-row:last-child { border-bottom: none; }
.alert-name { font-size: 0.86rem; font-weight: 850; color: #e6edf3; }
.alert-desc { font-size: 0.76rem; color: #8b949e; margin-top: 0.15rem; }

.alert-badge-high,
.alert-badge-med {
    padding: 0.13rem 0.45rem;
    border-radius: 12px;
    font-size: 0.68rem;
    font-weight: 900;
}

.alert-badge-high {
    background: rgba(248,81,73,.12);
    color: #f85149;
    border: 1px solid rgba(248,81,73,.35);
}

.alert-badge-med {
    background: rgba(210,153,34,.12);
    color: #d29922;
    border: 1px solid rgba(210,153,34,.35);
}

.profile-avatar {
    width: 48px;
    height: 48px;
    border-radius: 14px;
    background: linear-gradient(135deg, #1f6feb, #58a6ff);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 900;
}

.stDataFrame { border-radius: 10px !important; overflow: hidden !important; }

div[data-testid="stDataFrame"] {
    border: 1px solid #30363d !important;
    border-radius: 10px !important;
}
</style>
""",
    unsafe_allow_html=True,
)


# ── Config helpers ────────────────────────────────────────────────────────────
def cfg_key(setting_key: str) -> str:
    return f"{CFG_PREFIX}{setting_key}"


def cfg_get(setting_key: str):
    return st.session_state[cfg_key(setting_key)]


def cfg_set(setting_key: str, value) -> None:
    st.session_state[cfg_key(setting_key)] = value


def get_rules() -> dict:
    return {
        "delivery_target": float(cfg_get("delivery_target")),
        "quality_target": float(cfg_get("quality_target")),
        "leadtime_limit": float(cfg_get("leadtime_limit")),
        "complaint_limit": float(cfg_get("complaint_limit")),
        "price_dev_tolerance": float(cfg_get("price_dev_tolerance")),
        "anomaly_sensitivity": str(cfg_get("anomaly_sensitivity")),
    }


def get_effective_rules() -> dict:
    rules = get_rules()
    sensitivity = rules["anomaly_sensitivity"]

    delivery_target = rules["delivery_target"]
    quality_target = rules["quality_target"]
    leadtime_limit = rules["leadtime_limit"]
    complaint_limit = rules["complaint_limit"]
    price_dev_tolerance = rules["price_dev_tolerance"]

    if sensitivity == "Low":
        delivery_threshold = max(0.0, delivery_target - 5.0)
        quality_threshold = max(0.0, quality_target - 3.0)
        leadtime_threshold = leadtime_limit + 3.0
        complaint_threshold = complaint_limit + 0.5
        price_threshold = price_dev_tolerance + 1.0
    elif sensitivity == "High":
        delivery_threshold = min(100.0, delivery_target + 1.0)
        quality_threshold = min(100.0, quality_target + 1.0)
        leadtime_threshold = max(0.1, leadtime_limit - 2.0)
        complaint_threshold = max(0.1, complaint_limit - 0.2)
        price_threshold = max(0.1, price_dev_tolerance - 0.3)
    else:
        delivery_threshold = delivery_target
        quality_threshold = quality_target
        leadtime_threshold = leadtime_limit
        complaint_threshold = complaint_limit
        price_threshold = price_dev_tolerance

    return {
        **rules,
        "delivery_threshold": delivery_threshold,
        "quality_threshold": quality_threshold,
        "leadtime_threshold": leadtime_threshold,
        "complaint_threshold": complaint_threshold,
        "price_threshold": price_threshold,
    }


# ── RULES is computed fresh every run (not module-level constant) ─────────────
RULES = get_effective_rules()


def clean_cols(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip() for c in df.columns]
    return df


def find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    normalized = {str(c).strip().lower(): c for c in df.columns}
    for candidate in candidates:
        if candidate.lower() in normalized:
            return normalized[candidate.lower()]
    return None


def to_num(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def calc_score(row: pd.Series) -> float:
    score = 100.0

    if pd.notna(row.get(COL_DELIVERY)) and row[COL_DELIVERY] < float(RULES["delivery_target"]):
        score -= (float(RULES["delivery_target"]) - row[COL_DELIVERY]) * 1.8

    if pd.notna(row.get(COL_LEADTIME)) and row[COL_LEADTIME] > float(RULES["leadtime_limit"]):
        score -= (row[COL_LEADTIME] - float(RULES["leadtime_limit"])) * 2.0

    if pd.notna(row.get(COL_QUALITY)) and row[COL_QUALITY] < float(RULES["quality_target"]):
        score -= (float(RULES["quality_target"]) - row[COL_QUALITY]) * 2.5

    if pd.notna(row.get(COL_COMPLAINT)) and row[COL_COMPLAINT] > float(RULES["complaint_limit"]):
        score -= (row[COL_COMPLAINT] - float(RULES["complaint_limit"])) * 8.0

    if pd.notna(row.get(COL_PRICE_DEV)) and abs(row[COL_PRICE_DEV]) > float(RULES["price_dev_tolerance"]):
        score -= (abs(row[COL_PRICE_DEV]) - float(RULES["price_dev_tolerance"])) * 3.5

    return max(round(score, 1), 0.0)


def risk_label(score: float) -> str:
    if score >= 90:
        return "Low"
    if score >= 75:
        return "Medium"
    return "High"


def status_text_from_risk(risk: str) -> str:
    return {
        "Low": "Green / Good",
        "Medium": "Yellow / Monitor",
        "High": "Red / High Risk",
    }.get(str(risk), "Green / Good")


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


def country_flag(country: str) -> str:
    flags = {
        "austria": "🇦🇹",
        "china": "🇨🇳",
        "czech republic": "🇨🇿",
        "czechia": "🇨🇿",
        "france": "🇫🇷",
        "germany": "🇩🇪",
        "india": "🇮🇳",
        "italy": "🇮🇹",
        "mexico": "🇲🇽",
        "netherlands": "🇳🇱",
        "poland": "🇵🇱",
        "spain": "🇪🇸",
        "turkey": "🇹🇷",
        "usa": "🇺🇸",
        "united states": "🇺🇸",
        "united states of america": "🇺🇸",
        "uk": "🇬🇧",
        "united kingdom": "🇬🇧",
        "vietnam": "🇻🇳",
    }
    text = str(country).strip()
    return flags.get(text.lower(), "🏳️")


def country_with_flag(country: str) -> str:
    text = str(country).strip()
    if bool(cfg_get("show_country_flags")):
        return f"{country_flag(text)} {text}"
    return text


def price_signal(value: float) -> str:
    if pd.isna(value):
        return "—"
    if value > 0:
        return f"🔴 ▲ +{value:.2f}%"
    if value < 0:
        return f"🟢 ▼ {value:.2f}%"
    return "🟢 ● 0.00%"


def stable_trend(base_value: float, name: str, points: int = 12, spread: float = 3.2) -> list[float]:
    seed_text = str(name).encode("utf-8")
    seed = int(hashlib.md5(seed_text).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    steps = rng.normal(0, spread / 4, points).cumsum()
    centered = steps - steps.mean()
    trend = np.clip(float(base_value) + centered, 0, 100)
    return [round(float(v), 1) for v in trend]


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


def issue_text(row: pd.Series) -> str:
    issues = []

    if pd.notna(row.get("Delivery")) and row["Delivery"] < float(RULES["delivery_threshold"]):
        issues.append(f"Delivery below threshold ({row['Delivery']:.1f}%)")

    if pd.notna(row.get("Quality")) and row["Quality"] < float(RULES["quality_threshold"]):
        issues.append(f"Quality below threshold ({row['Quality']:.1f}%)")

    if pd.notna(row.get("LeadTime")) and row["LeadTime"] > float(RULES["leadtime_threshold"]):
        issues.append(f"Lead time above threshold ({row['LeadTime']:.1f} days)")

    if pd.notna(row.get("Complaint")) and row["Complaint"] > float(RULES["complaint_threshold"]):
        issues.append(f"Complaint rate high ({row['Complaint']:.2f}%)")

    if pd.notna(row.get("PriceDev")) and abs(row["PriceDev"]) > float(RULES["price_threshold"]):
        issues.append(f"Price deviation outside tolerance ({row['PriceDev']:+.2f}%)")

    return " · ".join(issues) if issues else "No critical KPI issue"


@st.cache_data(show_spinner=False)
def load_excel(uploaded_file) -> pd.DataFrame:
    return clean_cols(pd.read_excel(uploaded_file))


with st.sidebar:
    st.markdown('<div class="logo-box">📦 SupplierDash</div>', unsafe_allow_html=True)

    page_options = [
        "🏠 Overview",
        "👥 Suppliers",
        "📈 Performance",
        "⚠️ Anomalies",
        "🔔 Alerts",
        "🏅 Scorecards",
        "💰 Spend Analysis",
        "📂 Category Insights",
        "🌍 Country Insights",
        "📊 Trends",
        "📄 Contracts",
        "✅ Assessments",
        "📁 Documents",
        "⚙️ Settings",
        "👤 Users & Roles",
    ]

    st.markdown('<div class="side-title">Navigation</div>', unsafe_allow_html=True)
    page = st.radio("Navigation", page_options, index=0, label_visibility="collapsed", key="page_nav")


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
    st.caption("Upload your supplier KPI Excel file. Filters, charts, settings, tables, and selected supplier profile update automatically.")


def render_settings(raw_data: pd.DataFrame | None = None, clean_data: pd.DataFrame | None = None) -> None:
    st.markdown('<div class="s-card"><div class="s-card-title">⚙️ Dashboard Settings</div>', unsafe_allow_html=True)
    st.caption("These settings control KPI cards, anomaly detection, risk scoring, profile colors, and supplier table display.")

    s1, s2 = st.columns(2)

    with s1:
        st.markdown("#### KPI Targets")
        new_delivery_target = st.slider(
            "Delivery target (%)",
            50.0,
            100.0,
            value=float(cfg_get("delivery_target")),
            step=0.5,
            key="w_delivery_target",
        )
        new_quality_target = st.slider(
            "Quality target (%)",
            50.0,
            100.0,
            value=float(cfg_get("quality_target")),
            step=0.5,
            key="w_quality_target",
        )
        new_leadtime_limit = st.slider(
            "Lead time limit (days)",
            1.0,
            60.0,
            value=float(cfg_get("leadtime_limit")),
            step=0.5,
            key="w_leadtime_limit",
        )
        new_complaint_limit = st.slider(
            "Complaint rate limit (%)",
            0.0,
            20.0,
            value=float(cfg_get("complaint_limit")),
            step=0.1,
            key="w_complaint_limit",
        )
        new_price_dev_tolerance = st.slider(
            "Price deviation tolerance (+/- %)",
            0.0,
            25.0,
            value=float(cfg_get("price_dev_tolerance")),
            step=0.1,
            key="w_price_dev_tolerance",
        )

    with s2:
        st.markdown("#### Anomaly & Display")

        sensitivity_options = ["Low", "Medium", "High"]
        current_sensitivity = str(cfg_get("anomaly_sensitivity"))
        sensitivity_index = sensitivity_options.index(current_sensitivity) if current_sensitivity in sensitivity_options else 1

        new_anomaly_sensitivity = st.selectbox(
            "Anomaly sensitivity",
            sensitivity_options,
            index=sensitivity_index,
            key="w_anomaly_sensitivity",
            help="Low = fewer alerts, Medium = normal rules, High = stricter alerts.",
        )

        new_top_supplier_rows = st.slider(
            "Top supplier table rows",
            5,
            50,
            value=int(cfg_get("top_supplier_rows")),
            step=1,
            key="w_top_supplier_rows",
        )

        new_show_country_flags = st.checkbox(
            "Show country flags",
            value=bool(cfg_get("show_country_flags")),
            key="w_show_country_flags",
        )

        new_show_delivery_trend = st.checkbox(
            "Show delivery trend line in Top Suppliers",
            value=bool(cfg_get("show_delivery_trend")),
            key="w_show_delivery_trend",
        )

    # Write widget values back to cfg_ store AFTER widgets are rendered
    cfg_set("delivery_target", new_delivery_target)
    cfg_set("quality_target", new_quality_target)
    cfg_set("leadtime_limit", new_leadtime_limit)
    cfg_set("complaint_limit", new_complaint_limit)
    cfg_set("price_dev_tolerance", new_price_dev_tolerance)
    cfg_set("anomaly_sensitivity", new_anomaly_sensitivity)
    cfg_set("top_supplier_rows", new_top_supplier_rows)
    cfg_set("show_country_flags", new_show_country_flags)
    cfg_set("show_delivery_trend", new_show_delivery_trend)

    effective = get_effective_rules()

    st.markdown("#### Effective Anomaly Thresholds")
    threshold_df = pd.DataFrame(
        {
            "Rule": [
                "Delivery alert if below",
                "Quality alert if below",
                "Lead time alert if above",
                "Complaint rate alert if above",
                "Price deviation alert if outside",
            ],
            "Effective Threshold": [
                f"{effective['delivery_threshold']:.1f}%",
                f"{effective['quality_threshold']:.1f}%",
                f"{effective['leadtime_threshold']:.1f} days",
                f"{effective['complaint_threshold']:.2f}%",
                f"±{effective['price_threshold']:.2f}%",
            ],
        }
    )
    st.dataframe(threshold_df, use_container_width=True, hide_index=True)

    st.markdown("#### Data Quality Overview")

    if raw_data is None:
        st.info("Upload an Excel file to see data quality checks here.")
    else:
        duplicate_rows = int(raw_data.duplicated().sum())
        missing_values = int(raw_data.isna().sum().sum())
        total_rows = len(raw_data)
        total_columns = len(raw_data.columns)
        valid_rows = len(clean_data) if clean_data is not None else 0

        dq1, dq2, dq3, dq4 = st.columns(4)
        dq1.metric("Uploaded Rows", f"{total_rows}")
        dq2.metric("Valid Rows Used", f"{valid_rows}")
        dq3.metric("Columns Detected", f"{total_columns}")
        dq4.metric("Missing Values", f"{missing_values}")

        st.caption(f"Duplicate full rows detected: {duplicate_rows}")

        detected_columns = pd.DataFrame({"Detected Columns": raw_data.columns.astype(str).tolist()})
        st.dataframe(detected_columns, use_container_width=True, hide_index=True, height=240)

    st.markdown("</div>", unsafe_allow_html=True)


if uploaded_file is None:
    if page == "⚙️ Settings":
        render_settings()
        st.stop()

    st.markdown(
        """
<div class="s-card" style="max-width:650px;margin:55px auto;text-align:center;">
  <div style="font-size:3rem;margin-bottom:12px;">📂</div>
  <div style="font-size:1.2rem;font-weight:900;color:#e6edf3;margin-bottom:8px;">Upload your supplier data</div>
  <div style="font-size:.88rem;color:#8b949e;line-height:1.55;">
    Expected columns: <b>Supplier_Name, Country, Category, Delivery_Performance_%, Lead_Time_Days,<br>
    Quality_Score_%, Complaint_Rate_%, Price_Deviation_%</b>.<br>
    Optional columns: Supplier_ID, Status, Anomaly_Flag, Overall_Score, Spend, Notes.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.stop()


raw = load_excel(uploaded_file)

AUTO_MAP = {
    COL_SUPPLIER: ["supplier_name", "supplier", "supplier name", "name", "lieferant"],
    COL_COUNTRY: ["country", "land", "country_name"],
    COL_CATEGORY: ["category", "kategorie", "material", "type", "material_group"],
    COL_DELIVERY: ["delivery_performance_%", "delivery_performance", "delivery %", "on_time_delivery", "liefertreue", "delivery_%"],
    COL_LEADTIME: ["lead_time_days", "lead_time", "lead time", "lieferzeit", "leadtime"],
    COL_QUALITY: ["quality_score_%", "quality_score", "quality %", "qualitätsrate", "quality_%", "quality"],
    COL_COMPLAINT: ["complaint_rate_%", "complaint_rate", "complaint rate", "reklamationsquote", "complaints_%"],
    COL_PRICE_DEV: ["price_deviation_%", "price_deviation", "price deviation", "preisabweichung", "price_dev"],
    COL_SCORE: ["overall_score", "overall score", "score", "gesamtscore"],
    COL_STATUS: ["status", "supplier_status", "supplier status", "risk_status"],
    COL_ANOMALY: ["anomaly_flag", "anomaly", "anomalieflag", "is_anomaly"],
    COL_ID: ["supplier_id", "supplier id", "id", "lieferant_id"],
    COL_SPEND: ["spend", "spend_under_management", "annual_spend", "total_spend", "purchase_value", "value", "spend amount"],
    COL_NOTES: ["notes", "comment", "comments", "remark", "remarks"],
}

col_map = {internal: find_col(raw, candidates) for internal, candidates in AUTO_MAP.items()}
missing = [col for col in REQUIRED_COLS if col_map.get(col) is None]

if missing:
    st.error(
        "Required columns were not found. Missing: "
        + ", ".join(missing)
        + "\n\nColumns found in your file: "
        + ", ".join([str(c) for c in raw.columns])
    )
    st.stop()

rename_map = {actual: internal for internal, actual in col_map.items() if actual is not None}
df = raw.rename(columns=rename_map).copy()

df = to_num(df, [COL_DELIVERY, COL_LEADTIME, COL_QUALITY, COL_COMPLAINT, COL_PRICE_DEV, COL_SCORE, COL_SPEND])
df = df.dropna(subset=REQUIRED_COLS).copy()

if df.empty:
    st.error("The file was loaded, but after cleaning there are no valid supplier rows. Please check your numeric KPI columns.")
    st.stop()

if COL_ID not in df.columns:
    df[COL_ID] = [f"S{i + 1:03d}" for i in range(len(df))]

if COL_SPEND not in df.columns:
    df[COL_SPEND] = np.nan

df[COL_SCORE] = df.apply(calc_score, axis=1)
df["_risk"] = df[COL_SCORE].apply(risk_label)
df[COL_STATUS] = df["_risk"].apply(status_text_from_risk)


def count_anomalies(row: pd.Series) -> int:
    count = 0
    count += int(pd.notna(row[COL_DELIVERY]) and row[COL_DELIVERY] < float(RULES["delivery_threshold"]))
    count += int(pd.notna(row[COL_LEADTIME]) and row[COL_LEADTIME] > float(RULES["leadtime_threshold"]))
    count += int(pd.notna(row[COL_QUALITY]) and row[COL_QUALITY] < float(RULES["quality_threshold"]))
    count += int(pd.notna(row[COL_COMPLAINT]) and row[COL_COMPLAINT] > float(RULES["complaint_threshold"]))
    count += int(pd.notna(row[COL_PRICE_DEV]) and abs(row[COL_PRICE_DEV]) > float(RULES["price_threshold"]))
    return count


df["_anomaly"] = df.apply(count_anomalies, axis=1)

agg_dict = {
    "Supplier_ID": (COL_ID, "first"),
    "Country": (COL_COUNTRY, "first"),
    "Category": (COL_CATEGORY, "first"),
    "Delivery": (COL_DELIVERY, "mean"),
    "LeadTime": (COL_LEADTIME, "mean"),
    "Quality": (COL_QUALITY, "mean"),
    "Complaint": (COL_COMPLAINT, "mean"),
    "PriceDev": (COL_PRICE_DEV, "mean"),
    "Score": (COL_SCORE, "mean"),
    "Spend": (COL_SPEND, "sum"),
    "Anomalies": ("_anomaly", "sum"),
    "Status": (COL_STATUS, "first"),
    "Risk": ("_risk", "first"),
}

if COL_NOTES in df.columns:
    agg_dict["Notes"] = (COL_NOTES, "first")

agg = (
    df.groupby(COL_SUPPLIER, as_index=False)
    .agg(**agg_dict)
    .sort_values("Score", ascending=False)
    .reset_index(drop=True)
)

for numeric_col in ["Delivery", "LeadTime", "Quality", "Complaint", "PriceDev", "Score", "Spend"]:
    if numeric_col in agg.columns:
        agg[numeric_col] = pd.to_numeric(agg[numeric_col], errors="coerce").round(2)


if page == "⚙️ Settings":
    # Handle reset at module level BEFORE rendering settings
    reset_pressed = st.button("↻ Reset all settings to default", key="module_reset_btn")
    if reset_pressed:
        for k, v in DEFAULT_SETTINGS.items():
            st.session_state[cfg_key(k)] = v
        st.rerun()
    
    render_settings(raw_data=raw, clean_data=df)
    st.markdown(
        '<div style="text-align:center;color:#6e7681;font-size:.75rem;padding:24px 0 8px;">SupplierDash · Interactive KPI Monitoring · Powered by Streamlit</div>',
        unsafe_allow_html=True,
    )
    st.stop()


f1, f2, f3, f4, f5 = st.columns([1.35, 1.35, 1.28, 1.28, 2.15])

with f1:
    country_options = ["All Countries"] + sorted(agg["Country"].dropna().astype(str).unique().tolist())
    sel_country = st.selectbox("Country", country_options, key="filter_country")

with f2:
    category_options = ["All Categories"] + sorted(agg["Category"].dropna().astype(str).unique().tolist())
    sel_category = st.selectbox("Category", category_options, key="filter_category")

with f3:
    status_options = ["All Statuses"] + sorted(agg["Status"].dropna().astype(str).unique().tolist())
    sel_status = st.selectbox("Supplier Status", status_options, key="filter_status")

with f4:
    risk_options = ["All Risk Levels", "Low", "Medium", "High"]
    sel_risk = st.selectbox("Risk Level", risk_options, key="filter_risk")

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
    query = search_q.strip().lower()
    filt = filt[filt[COL_SUPPLIER].astype(str).str.lower().str.contains(query, na=False)]

filt = filt.reset_index(drop=True)

if filt.empty:
    st.warning("No suppliers match the selected filters. Change filters or clear the search box.")
    st.stop()

supplier_names = filt[COL_SUPPLIER].astype(str).tolist()

if "selected_supplier" not in st.session_state or st.session_state["selected_supplier"] not in supplier_names:
    st.session_state["selected_supplier"] = supplier_names[0]

# ── Determine currently selected supplier for KPI bar ────────────────────────
_current_selected = st.session_state.get("selected_supplier", supplier_names[0])
if _current_selected not in supplier_names:
    _current_selected = supplier_names[0]

_sel_row = filt[filt[COL_SUPPLIER].astype(str) == _current_selected].iloc[0]

avg_delivery = filt["Delivery"].mean()
avg_lead = filt["LeadTime"].mean()
avg_quality = filt["Quality"].mean()
avg_complaint = filt["Complaint"].mean()
active_suppliers = len(filt)
anomaly_alerts = int(filt["Anomalies"].sum())

# Selected supplier KPIs for the last card
_sel_score = float(_sel_row["Score"])
_sel_color = score_color(_sel_score)
_sel_name_short = str(_current_selected)[:18] + ("…" if len(str(_current_selected)) > 18 else "")

st.markdown(
    f"""
<div class="metric-grid">
  <div class="kpi-card">
    <div class="kpi-icon" style="background:rgba(56,139,253,.12);">🚚</div>
    <div>
      <div class="kpi-label">On-Time Delivery %</div>
      <div class="kpi-value">{avg_delivery:.1f}%</div>
      <div class="{'kpi-good' if avg_delivery >= float(RULES['delivery_target']) else 'kpi-bad'}">{'▲ meets' if avg_delivery >= float(RULES['delivery_target']) else '▼ below'} {float(RULES['delivery_target']):.1f}% target</div>
    </div>
  </div>

  <div class="kpi-card">
    <div class="kpi-icon" style="background:rgba(163,113,247,.12);">⏱️</div>
    <div>
      <div class="kpi-label">Avg Lead Time</div>
      <div class="kpi-value">{avg_lead:.1f}d</div>
      <div class="{'kpi-good' if avg_lead <= float(RULES['leadtime_limit']) else 'kpi-bad'}">{'▼ within' if avg_lead <= float(RULES['leadtime_limit']) else '▲ above'} {float(RULES['leadtime_limit']):.1f}d target</div>
    </div>
  </div>

  <div class="kpi-card">
    <div class="kpi-icon" style="background:rgba(63,185,80,.12);">🛡️</div>
    <div>
      <div class="kpi-label">Quality Score</div>
      <div class="kpi-value">{avg_quality:.1f}%</div>
      <div class="{'kpi-good' if avg_quality >= float(RULES['quality_target']) else 'kpi-bad'}">{'▲ meets' if avg_quality >= float(RULES['quality_target']) else '▼ below'} {float(RULES['quality_target']):.1f}% target</div>
    </div>
  </div>

  <div class="kpi-card">
    <div class="kpi-icon" style="background:rgba(248,81,73,.12);">⚠️</div>
    <div>
      <div class="kpi-label">Complaint Rate</div>
      <div class="kpi-value">{avg_complaint:.2f}%</div>
      <div class="{'kpi-good' if avg_complaint <= float(RULES['complaint_limit']) else 'kpi-bad'}">{'▼ within' if avg_complaint <= float(RULES['complaint_limit']) else '▲ above'} {float(RULES['complaint_limit']):.1f}% limit</div>
    </div>
  </div>

  <div class="kpi-card">
    <div class="kpi-icon" style="background:rgba(56,139,253,.12);">👥</div>
    <div>
      <div class="kpi-label">Active Suppliers</div>
      <div class="kpi-value">{active_suppliers}</div>
      <div class="kpi-muted">in current filter</div>
    </div>
  </div>

  <div class="kpi-card">
    <div class="kpi-icon" style="background:rgba(210,153,34,.12);">🔔</div>
    <div>
      <div class="kpi-label">Anomaly Alerts</div>
      <div class="kpi-value">{anomaly_alerts}</div>
      <div class="{'kpi-bad' if anomaly_alerts > 0 else 'kpi-good'}">{'requires attention' if anomaly_alerts > 0 else 'all clear'}</div>
    </div>
  </div>

  <div class="kpi-card">
    <div class="kpi-icon" style="background:rgba(88,166,255,.10);">🔍</div>
    <div>
      <div class="kpi-label">Selected Supplier</div>
      <div class="kpi-value" style="font-size:1.1rem;color:{_sel_color};">{_sel_score:.0f}<span style="font-size:.85rem;color:#8b949e;">/100</span></div>
      <div class="kpi-selected-name" title="{_current_selected}">{_sel_name_short}</div>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)


def render_supplier_selector() -> pd.Series:
    selected = st.selectbox(
        "Click to view supplier profile →",
        supplier_names,
        index=supplier_names.index(st.session_state["selected_supplier"])
        if st.session_state["selected_supplier"] in supplier_names
        else 0,
        key="selected_supplier",
    )
    return filt[filt[COL_SUPPLIER].astype(str) == selected].iloc[0]


def render_supplier_profile(row: pd.Series) -> None:
    color = score_color(float(row["Score"]))
    price_color = "#f85149" if row["PriceDev"] > 0 else "#3fb950"

    st.markdown(
        f"""
<div class="s-card">
  <div class="s-card-title">Selected Supplier</div>

  <div style="display:flex;gap:12px;align-items:center;margin-bottom:14px;">
    <div class="profile-avatar">{initials(row[COL_SUPPLIER])}</div>
    <div>
      <div style="font-weight:900;font-size:1rem;color:#e6edf3;">{row[COL_SUPPLIER]}</div>
      <div style="font-size:.78rem;color:#8b949e;">{row['Category']} · {country_with_flag(row['Country'])}</div>
      <div style="margin-top:5px;">{status_html(row['Status'])}</div>
    </div>
  </div>

  <div style="font-size:.75rem;color:#8b949e;">Overall Score</div>
  <div style="font-size:2.15rem;font-weight:900;color:{color};">
    {row['Score']:.0f}<span style="font-size:1rem;color:#8b949e;">/100</span>
  </div>

  <div style="height:8px;background:#21262d;border-radius:8px;overflow:hidden;margin:6px 0 16px 0;">
    <div style="height:8px;width:{max(min(float(row['Score']), 100), 0)}%;background:{color};"></div>
  </div>

  <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;">
    <div><div class="kpi-label">Delivery</div><div style="font-weight:900;color:{'#3fb950' if row['Delivery'] >= float(RULES['delivery_target']) else '#f85149'};">{row['Delivery']:.1f}%</div></div>
    <div><div class="kpi-label">Quality</div><div style="font-weight:900;color:{'#3fb950' if row['Quality'] >= float(RULES['quality_target']) else '#f85149'};">{row['Quality']:.1f}%</div></div>
    <div><div class="kpi-label">Lead Time</div><div style="font-weight:900;color:{'#3fb950' if row['LeadTime'] <= float(RULES['leadtime_limit']) else '#f85149'};">{row['LeadTime']:.1f}d</div></div>
    <div><div class="kpi-label">Complaints</div><div style="font-weight:900;color:{'#3fb950' if row['Complaint'] <= float(RULES['complaint_limit']) else '#f85149'};">{row['Complaint']:.2f}%</div></div>
    <div><div class="kpi-label">Price Dev</div><div style="font-weight:900;color:{price_color};">{row['PriceDev']:+.2f}%</div></div>
    <div><div class="kpi-label">Anomalies</div><div style="font-weight:900;color:#e6edf3;">{int(row['Anomalies'])}</div></div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_top_table(data: pd.DataFrame, rows: int | None = None) -> None:
    if rows is None:
        rows = int(cfg_get("top_supplier_rows"))

    table_df = data[
        [
            COL_SUPPLIER,
            "Category",
            "Country",
            "Delivery",
            "Quality",
            "LeadTime",
            "Complaint",
            "PriceDev",
            "Status",
            "Risk",
            "Score",
        ]
    ].copy()

    table_df = table_df.sort_values("Score", ascending=False).head(rows).reset_index(drop=True)
    table_df["Country"] = table_df["Country"].apply(country_with_flag)
    table_df["Price Signal"] = table_df["PriceDev"].apply(price_signal)

    display_cols = [
        COL_SUPPLIER,
        "Category",
        "Country",
        "Delivery",
        "Quality",
        "LeadTime",
        "Complaint",
        "Price Signal",
        "Status",
        "Risk",
        "Score",
    ]

    if bool(cfg_get("show_delivery_trend")):
        table_df["Delivery Trend"] = table_df.apply(
            lambda row: stable_trend(row["Delivery"], row[COL_SUPPLIER]),
            axis=1,
        )
        display_cols.insert(4, "Delivery Trend")

    display_df = table_df[display_cols].copy()

    display_df = display_df.rename(
        columns={
            COL_SUPPLIER: "Supplier",
            "Delivery": "Delivery %",
            "Quality": "Quality %",
            "LeadTime": "Lead Time",
            "Complaint": "Complaint %",
            "Price Signal": "Price Dev %",
        }
    )

    column_config = {
        "Supplier": st.column_config.TextColumn("Supplier", width="medium"),
        "Category": st.column_config.TextColumn("Category", width="medium"),
        "Country": st.column_config.TextColumn("Country", width="medium"),
        "Delivery %": st.column_config.ProgressColumn(
            "Delivery %",
            format="%.1f%%",
            min_value=0,
            max_value=100,
            width="medium",
        ),
        "Quality %": st.column_config.ProgressColumn(
            "Quality %",
            format="%.1f%%",
            min_value=0,
            max_value=100,
            width="medium",
        ),
        "Lead Time": st.column_config.NumberColumn(
            "Lead Time",
            format="%.1f d",
            width="small",
        ),
        "Complaint %": st.column_config.NumberColumn(
            "Complaint %",
            format="%.2f%%",
            width="small",
        ),
        "Price Dev %": st.column_config.TextColumn("Price Dev %", width="small"),
        "Status": st.column_config.TextColumn("Status", width="medium"),
        "Risk": st.column_config.TextColumn("Risk", width="small"),
        "Score": st.column_config.ProgressColumn(
            "Score",
            format="%.1f",
            min_value=0,
            max_value=100,
            width="medium",
        ),
    }

    if bool(cfg_get("show_delivery_trend")):
        column_config["Delivery Trend"] = st.column_config.LineChartColumn(
            "Delivery Trend",
            y_min=0,
            y_max=100,
            width="medium",
        )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=460,
        column_config=column_config,
    )


def render_overview() -> None:
    left, right = st.columns([3.1, 1.1])

    with left:
        st.markdown('<div class="s-card"><div class="s-card-title">📈 Supplier Performance Trend — Delivery vs Quality</div>', unsafe_allow_html=True)

        trend = filt.sort_values("Score", ascending=False).head(15)

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=trend[COL_SUPPLIER],
                y=trend["Delivery"],
                mode="lines+markers",
                name="On-Time Delivery %",
                line=dict(color="#388bfd", width=2),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=trend[COL_SUPPLIER],
                y=trend["Quality"],
                mode="lines+markers",
                name="Quality Score %",
                line=dict(color="#3fb950", width=2),
            )
        )
        fig.add_hline(y=float(RULES["delivery_target"]), line_dash="dash", line_color="rgba(56,139,253,.45)", annotation_text="Delivery target")
        fig.add_hline(y=float(RULES["quality_target"]), line_dash="dash", line_color="rgba(63,185,80,.45)", annotation_text="Quality target")
        theme = plotly_theme(300)
        theme["xaxis"]["title"] = "Supplier"
        theme["yaxis"]["title"] = "Score (%)"
        fig.update_layout(**theme, xaxis_tickangle=-35)

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
        st.markdown("</div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)

        with c1:
            st.markdown('<div class="s-card"><div class="s-card-title">📦 Score by Category</div>', unsafe_allow_html=True)
            category_scores = filt.groupby("Category", as_index=False)["Score"].mean().sort_values("Score")
            fig_cat = px.bar(
                category_scores,
                x="Score",
                y="Category",
                orientation="h",
                color="Score",
                color_continuous_scale="Blues",
                range_color=[50, 100],
                labels={"Score": "Avg Overall Score", "Category": "Category"},
            )
            fig_cat.update_layout(**plotly_theme(260), coloraxis_showscale=False)
            st.plotly_chart(fig_cat, use_container_width=True, config={"displayModeBar": True})
            st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="s-card"><div class="s-card-title">🌍 Supplier Count by Country</div>', unsafe_allow_html=True)
            country_counts = filt["Country"].value_counts().reset_index()
            country_counts.columns = ["Country", "Count"]
            country_counts["Country"] = country_counts["Country"].apply(country_with_flag)
            fig_country = px.pie(country_counts.head(10), names="Country", values="Count", hole=0.55)
            fig_country.update_layout(**plotly_theme(260), showlegend=True)
            st.plotly_chart(fig_country, use_container_width=True, config={"displayModeBar": True})
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="s-card"><div class="s-card-title">🏆 Top Suppliers</div>', unsafe_allow_html=True)
        render_supplier_selector()
        render_top_table(filt)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        selected = filt[filt[COL_SUPPLIER].astype(str) == st.session_state["selected_supplier"]].iloc[0]

        st.markdown('<div class="s-card"><div class="s-card-title">⚠️ Anomaly Detection</div>', unsafe_allow_html=True)
        anomalies = filt[filt["Anomalies"] > 0].sort_values("Score").head(6)

        if anomalies.empty:
            st.success("No anomalies detected in current filters.")
        else:
            for _, anomaly in anomalies.iterrows():
                badge_class = "alert-badge-high" if anomaly["Score"] < 75 else "alert-badge-med"
                level = "High" if anomaly["Score"] < 75 else "Medium"

                st.markdown(
                    f"""
<div class="alert-row">
  <div style="display:flex;gap:8px;align-items:center;justify-content:space-between;">
    <span class="alert-name">{anomaly[COL_SUPPLIER]}</span><span class="{badge_class}">{level}</span>
  </div>
  <div class="alert-desc">{issue_text(anomaly)}</div>
  <div class="kpi-muted">{anomaly["Category"]} · {country_with_flag(anomaly["Country"])}</div>
</div>
""",
                    unsafe_allow_html=True,
                )

        st.markdown("</div>", unsafe_allow_html=True)
        render_supplier_profile(selected)


def render_suppliers() -> None:
    left, right = st.columns([2.45, 1])

    with left:
        st.markdown('<div class="s-card"><div class="s-card-title">👥 Supplier Directory</div>', unsafe_allow_html=True)
        selected_row = render_supplier_selector()
        render_top_table(filt, rows=25)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        render_supplier_profile(selected_row)


def render_performance() -> None:
    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="s-card"><div class="s-card-title">🎯 Delivery Reliability vs Quality Score</div>', unsafe_allow_html=True)
        fig = px.scatter(
            filt,
            x="Delivery",
            y="Quality",
            size="Score",
            color="Risk",
            hover_name=COL_SUPPLIER,
            size_max=28,
            color_discrete_map={"Low": "#3fb950", "Medium": "#d29922", "High": "#f85149"},
            labels={"Delivery": "On-Time Delivery (%)", "Quality": "Quality Score (%)"},
        )
        fig.add_vline(x=float(RULES["delivery_target"]), line_dash="dash", line_color="rgba(255,255,255,.25)")
        fig.add_hline(y=float(RULES["quality_target"]), line_dash="dash", line_color="rgba(255,255,255,.25)")
        theme = plotly_theme(380)
        theme["xaxis"]["title"] = "On-Time Delivery (%)"
        theme["yaxis"]["title"] = "Quality Score (%)"
        fig.update_layout(**theme)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="s-card"><div class="s-card-title">⏱️ Lead Time vs Complaint Rate</div>', unsafe_allow_html=True)
        fig = px.scatter(
            filt,
            x="LeadTime",
            y="Complaint",
            size="Score",
            color="Risk",
            hover_name=COL_SUPPLIER,
            size_max=28,
            color_discrete_map={"Low": "#3fb950", "Medium": "#d29922", "High": "#f85149"},
            labels={"LeadTime": "Lead Time (Days)", "Complaint": "Complaint Rate (%)"},
        )
        fig.add_vline(x=float(RULES["leadtime_limit"]), line_dash="dash", line_color="rgba(255,255,255,.25)")
        fig.add_hline(y=float(RULES["complaint_limit"]), line_dash="dash", line_color="rgba(255,255,255,.25)")
        theme = plotly_theme(380)
        theme["xaxis"]["title"] = "Lead Time (Days)"
        theme["yaxis"]["title"] = "Complaint Rate (%)"
        fig.update_layout(**theme)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
        st.markdown("</div>", unsafe_allow_html=True)


def render_anomalies() -> None:
    st.markdown('<div class="s-card"><div class="s-card-title">⚠️ Anomaly Management</div>', unsafe_allow_html=True)

    anomalies = filt[filt["Anomalies"] > 0].sort_values(["Score", "Anomalies"], ascending=[True, False]).copy()

    if anomalies.empty:
        st.success("No anomaly found in the current filter.")
    else:
        anomalies["Issue"] = anomalies.apply(issue_text, axis=1)
        show = anomalies[
            [
                COL_SUPPLIER,
                "Category",
                "Country",
                "Delivery",
                "LeadTime",
                "Quality",
                "Complaint",
                "PriceDev",
                "Risk",
                "Score",
                "Issue",
            ]
        ].copy()

        show["Country"] = show["Country"].apply(country_with_flag)
        show["PriceDev"] = show["PriceDev"].apply(price_signal)

        show = show.rename(
            columns={
                COL_SUPPLIER: "Supplier",
                "Delivery": "Delivery %",
                "LeadTime": "Lead Time",
                "Quality": "Quality %",
                "Complaint": "Complaint %",
                "PriceDev": "Price Dev %",
            }
        )

        st.dataframe(show, use_container_width=True, hide_index=True, height=500)

    st.markdown("</div>", unsafe_allow_html=True)


def render_scorecards() -> None:
    st.markdown('<div class="s-card"><div class="s-card-title">🏅 Supplier Scorecards</div>', unsafe_allow_html=True)

    scorecard = filt[
        [
            COL_SUPPLIER,
            "Category",
            "Country",
            "Delivery",
            "Quality",
            "LeadTime",
            "Complaint",
            "PriceDev",
            "Anomalies",
            "Risk",
            "Score",
        ]
    ].sort_values("Score", ascending=False).copy()

    scorecard["Country"] = scorecard["Country"].apply(country_with_flag)
    scorecard["PriceDev"] = scorecard["PriceDev"].apply(price_signal)

    scorecard = scorecard.rename(
        columns={
            COL_SUPPLIER: "Supplier",
            "Delivery": "Delivery %",
            "Quality": "Quality %",
            "LeadTime": "Lead Time",
            "Complaint": "Complaint %",
            "PriceDev": "Price Dev %",
        }
    )

    st.dataframe(scorecard, use_container_width=True, hide_index=True, height=500)
    st.markdown("</div>", unsafe_allow_html=True)


def render_spend_analysis() -> None:
    st.markdown('<div class="s-card"><div class="s-card-title">💰 Spend Analysis</div>', unsafe_allow_html=True)

    if not filt["Spend"].notna().any() or filt["Spend"].sum(skipna=True) <= 0:
        st.info("No Spend column was found in your Excel file. Add Spend / Annual_Spend / Total_Spend to activate real spend charts.")
        fallback = filt.groupby("Category", as_index=False)["Score"].mean().sort_values("Score", ascending=False)
        fig = px.bar(fallback, x="Category", y="Score", color="Score", color_continuous_scale="Blues",
                     labels={"Category": "Category", "Score": "Avg Overall Score"})
    else:
        spend = filt.groupby("Category", as_index=False)["Spend"].sum().sort_values("Spend", ascending=False)
        fig = px.bar(spend, x="Category", y="Spend", color="Spend", color_continuous_scale="Blues",
                     labels={"Category": "Category", "Spend": "Total Spend"})

    fig.update_layout(**plotly_theme(420))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
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
    )

    category = category.round(2).sort_values("Avg_Score", ascending=False)
    st.dataframe(category, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)


def render_country_insights() -> None:
    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="s-card"><div class="s-card-title">🌍 Suppliers by Country</div>', unsafe_allow_html=True)

        country = (
            filt.groupby("Country", as_index=False)
            .agg(
                Suppliers=(COL_SUPPLIER, "count"),
                Avg_Score=("Score", "mean"),
                Alerts=("Anomalies", "sum"),
            )
            .round(2)
            .sort_values("Suppliers", ascending=False)
        )

        country["Country"] = country["Country"].apply(country_with_flag)
        st.dataframe(country, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="s-card"><div class="s-card-title">🌍 Country Score Chart</div>', unsafe_allow_html=True)

        country_score = filt.groupby("Country", as_index=False)["Score"].mean().sort_values("Score", ascending=False)
        country_score["Country"] = country_score["Country"].apply(country_with_flag)

        fig = px.bar(
            country_score,
            x="Country",
            y="Score",
            color="Score",
            color_continuous_scale="Blues",
            range_color=[50, 100],
            labels={"Country": "Country", "Score": "Avg Overall Score"},
        )

        fig.update_layout(**plotly_theme(360), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
        st.markdown("</div>", unsafe_allow_html=True)


def render_trends() -> None:
    st.markdown('<div class="s-card"><div class="s-card-title">📊 KPI Trends / Ranking</div>', unsafe_allow_html=True)

    metric = st.selectbox(
        "Choose KPI",
        ["Score", "Delivery", "Quality", "LeadTime", "Complaint", "PriceDev"],
        key="trend_metric",
    )

    axis_labels = {
        "Score": "Overall Score",
        "Delivery": "On-Time Delivery (%)",
        "Quality": "Quality Score (%)",
        "LeadTime": "Lead Time (Days)",
        "Complaint": "Complaint Rate (%)",
        "PriceDev": "Price Deviation (%)",
    }

    ascending = metric in ["LeadTime", "Complaint", "PriceDev"]
    trend = filt.sort_values(metric, ascending=ascending).head(20)

    fig = px.line(
        trend,
        x=COL_SUPPLIER,
        y=metric,
        markers=True,
        hover_data=["Category", "Country", "Risk", "Score"],
        labels={COL_SUPPLIER: "Supplier", metric: axis_labels.get(metric, metric)},
    )

    theme = plotly_theme(430)
    theme["xaxis"]["title"] = "Supplier"
    theme["yaxis"]["title"] = axis_labels.get(metric, metric)
    fig.update_layout(**theme, xaxis_tickangle=-35)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    st.markdown("</div>", unsafe_allow_html=True)


def render_placeholder(title: str, text: str) -> None:
    st.markdown(
        f'<div class="s-card"><div class="s-card-title">{title}</div><div style="color:#8b949e;line-height:1.6;">{text}</div></div>',
        unsafe_allow_html=True,
    )


if page == "🏠 Overview":
    render_overview()
elif page == "👥 Suppliers":
    render_suppliers()
elif page == "📈 Performance":
    render_performance()
elif page == "⚠️ Anomalies":
    render_anomalies()
elif page == "🔔 Alerts":
    render_anomalies()
elif page == "🏅 Scorecards":
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
    render_placeholder(
        "📄 Contracts",
        "Contract management placeholder. Add contract expiry, contract value, owner, renewal date, and SLA columns later to make this section fully data-driven.",
    )
elif page == "✅ Assessments":
    render_scorecards()
elif page == "📁 Documents":
    render_placeholder(
        "📁 Documents",
        "Document management placeholder for supplier certificates, quality documents, compliance files, and audit reports.",
    )
elif page == "👤 Users & Roles":
    render_placeholder(
        "👤 Users & Roles",
        "Users & Roles placeholder. This Streamlit demo can later be connected to authentication and role-based permissions.",
    )

st.markdown(
    '<div style="text-align:center;color:#6e7681;font-size:.75rem;padding:24px 0 8px;">SupplierDash · Interactive KPI Monitoring · Powered by Streamlit</div>',
    unsafe_allow_html=True,
)
