import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="SupplierDash",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────
# COLUMN NAME CONSTANTS  ← edit here only if your Excel uses other names
# ─────────────────────────────────────────────────────────────────
COL_SUPPLIER = "Supplier_Name"
COL_COUNTRY = "Country"
COL_CATEGORY = "Category"
COL_DELIVERY = "Delivery_Performance_%"
COL_LEADTIME = "Lead_Time_Days"
COL_QUALITY = "Quality_Score_%"
COL_COMPLAINT = "Complaint_Rate_%"
COL_PRICE_DEV = "Price_Deviation_%"
COL_SCORE = "Overall_Score"       # optional — calculated if missing
COL_STATUS = "Status"             # optional
COL_ANOMALY = "Anomaly_Flag"      # optional
COL_ID = "Supplier_ID"            # optional
COL_SPEND = "Spend"               # optional
COL_NOTES = "Notes"               # optional

REQUIRED_COLS = [
    COL_SUPPLIER, COL_COUNTRY, COL_CATEGORY,
    COL_DELIVERY, COL_LEADTIME, COL_QUALITY,
    COL_COMPLAINT, COL_PRICE_DEV,
]

# ─────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.stApp { background:#0d1117 !important; color:#e6edf3; }
.block-container { padding: 16px 22px 24px 22px !important; max-width: 100% !important; }
#MainMenu, footer, header { visibility: hidden; }

section[data-testid="stSidebar"] {
    background:#161b22 !important;
    border-right:1px solid #30363d;
}
section[data-testid="stSidebar"] * { color:#c9d1d9 !important; }
section[data-testid="stSidebar"] > div { padding: 14px 12px !important; }

.logo-box {
    font-size:1.05rem; font-weight:800; color:#e6edf3;
    padding:8px 6px 16px 6px; border-bottom:1px solid #30363d; margin-bottom:14px;
}
.side-title {
    font-size:0.70rem; letter-spacing:.08em; text-transform:uppercase;
    color:#8b949e; font-weight:800; margin:16px 6px 6px 6px;
}

/* Streamlit radio styled like sidebar nav */
div[role="radiogroup"] label {
    background:transparent !important;
    border-radius:8px !important;
    padding:8px 10px !important;
    margin:2px 0 !important;
}
div[role="radiogroup"] label:hover { background:#21262d !important; }
div[role="radiogroup"] label[data-baseweb="radio"] > div:first-child { display:none !important; }
div[role="radiogroup"] label p { font-size:0.86rem !important; font-weight:650 !important; }

.top-bar {
    background:#161b22; border:1px solid #30363d; border-radius:12px;
    padding:16px 18px; margin-bottom:14px;
    display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap;
}
.top-title { font-size:1.35rem; font-weight:850; color:#e6edf3; }
.top-sub { font-size:0.82rem; color:#8b949e; margin-top:2px; }

.kpi-card {
    background:#161b22; border:1px solid #30363d; border-radius:12px;
    padding:16px 18px; display:flex; align-items:center; gap:14px; min-height:94px;
}
.kpi-icon {
    width:44px; height:44px; border-radius:12px; display:flex;
    align-items:center; justify-content:center; font-size:1.15rem; flex-shrink:0;
}
.kpi-label { font-size:0.76rem; color:#8b949e; font-weight:650; }
.kpi-value { font-size:1.55rem; font-weight:850; color:#e6edf3; line-height:1.15; }
.kpi-good { font-size:0.74rem; color:#3fb950; font-weight:800; }
.kpi-bad { font-size:0.74rem; color:#f85149; font-weight:800; }
.kpi-muted { font-size:0.72rem; color:#6e7681; }

.s-card {
    background:#161b22; border:1px solid #30363d; border-radius:12px;
    padding:16px 18px; height:100%; overflow:hidden;
}
.s-card-title { font-size:0.96rem; font-weight:850; color:#e6edf3; margin-bottom:12px; }

.metric-grid { display:grid; grid-template-columns:repeat(6, minmax(150px,1fr)); gap:10px; margin-bottom:12px; }
@media (max-width: 1400px) { .metric-grid { grid-template-columns:repeat(3, 1fr); } }
@media (max-width: 900px) { .metric-grid { grid-template-columns:repeat(1, 1fr); } }

.status-active { background:rgba(63,185,80,.12); color:#3fb950; border:1px solid rgba(63,185,80,.35); padding:3px 9px; border-radius:16px; font-size:.72rem; font-weight:800; }
.status-risk { background:rgba(210,153,34,.12); color:#d29922; border:1px solid rgba(210,153,34,.35); padding:3px 9px; border-radius:16px; font-size:.72rem; font-weight:800; }
.status-high { background:rgba(248,81,73,.12); color:#f85149; border:1px solid rgba(248,81,73,.35); padding:3px 9px; border-radius:16px; font-size:.72rem; font-weight:800; }

.alert-row { border-bottom:1px solid #21262d; padding:10px 0; }
.alert-row:last-child { border-bottom:none; }
.alert-name { font-size:.86rem; font-weight:800; color:#e6edf3; }
.alert-desc { font-size:.76rem; color:#8b949e; margin-top:2px; }
.alert-badge-high { background:rgba(248,81,73,.12); color:#f85149; border:1px solid rgba(248,81,73,.35); padding:2px 7px; border-radius:12px; font-size:.68rem; font-weight:850; }
.alert-badge-med { background:rgba(210,153,34,.12); color:#d29922; border:1px solid rgba(210,153,34,.35); padding:2px 7px; border-radius:12px; font-size:.68rem; font-weight:850; }

.profile-avatar {
    width:48px; height:48px; border-radius:14px; background:linear-gradient(135deg,#1f6feb,#58a6ff);
    display:flex; align-items:center; justify-content:center; color:white; font-weight:900;
}

.stSelectbox label, .stTextInput label, .stFileUploader label, .stRadio label {
    color:#8b949e !important; font-size:0.78rem !important; font-weight:700 !important;
}
div[data-baseweb="select"] > div, .stTextInput input {
    background:#21262d !important; border:1px solid #30363d !important; color:#e6edf3 !important; border-radius:9px !important;
}
.stButton > button {
    background:#1f3a5f !important; border:1px solid #388bfd !important; color:#58a6ff !important;
    border-radius:9px !important; font-weight:800 !important;
}
.stDataFrame { border-radius:10px !important; overflow:hidden !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────
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
    if pd.notna(row.get(COL_DELIVERY)) and row[COL_DELIVERY] < 95:
        score -= (95 - row[COL_DELIVERY]) * 1.8
    if pd.notna(row.get(COL_LEADTIME)) and row[COL_LEADTIME] > 10:
        score -= (row[COL_LEADTIME] - 10) * 2.0
    if pd.notna(row.get(COL_QUALITY)) and row[COL_QUALITY] < 97:
        score -= (97 - row[COL_QUALITY]) * 2.5
    if pd.notna(row.get(COL_COMPLAINT)) and row[COL_COMPLAINT] > 1.0:
        score -= (row[COL_COMPLAINT] - 1.0) * 8.0
    if pd.notna(row.get(COL_PRICE_DEV)) and abs(row[COL_PRICE_DEV]) > 1.0:
        score -= (abs(row[COL_PRICE_DEV]) - 1.0) * 3.5
    return max(round(score, 1), 0.0)


def risk_label(score: float) -> str:
    if score >= 90:
        return "Low"
    if score >= 75:
        return "Medium"
    return "High"


def initials(name: str) -> str:
    text = str(name).strip()
    if not text:
        return "?"
    parts = text.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return text[:2].upper()


def status_html(status: str) -> str:
    s = str(status).lower()
    if "high" in s:
        return '<span class="status-high">High Risk</span>'
    if "risk" in s or "monitor" in s or "medium" in s or "yellow" in s:
        return '<span class="status-risk">At Risk</span>'
    return '<span class="status-active">Active</span>'


def score_color(score: float) -> str:
    if score >= 90:
        return "#3fb950"
    if score >= 75:
        return "#d29922"
    return "#f85149"


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
    if pd.notna(row.get("Delivery")) and row["Delivery"] < 95:
        issues.append(f"Delivery below target ({row['Delivery']:.1f}%)")
    if pd.notna(row.get("Quality")) and row["Quality"] < 97:
        issues.append(f"Quality below target ({row['Quality']:.1f}%)")
    if pd.notna(row.get("LeadTime")) and row["LeadTime"] > 10:
        issues.append(f"Lead time above target ({row['LeadTime']:.1f} days)")
    if pd.notna(row.get("Complaint")) and row["Complaint"] > 1:
        issues.append(f"Complaint rate high ({row['Complaint']:.2f}%)")
    if pd.notna(row.get("PriceDev")) and abs(row["PriceDev"]) > 1:
        issues.append(f"Price deviation outside tolerance ({row['PriceDev']:+.2f}%)")
    return " · ".join(issues) if issues else "No critical KPI issue"


@st.cache_data(show_spinner=False)
def load_excel(uploaded_file) -> pd.DataFrame:
    return clean_cols(pd.read_excel(uploaded_file))


# ─────────────────────────────────────────────────────────────────
# SIDEBAR — NOW REAL INTERACTIVE NAVIGATION
# ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="logo-box">📦 SupplierDash</div>', unsafe_allow_html=True)
    st.markdown('<div class="side-title">Monitoring</div>', unsafe_allow_html=True)
    page_monitor = ["🏠 Overview", "👥 Suppliers", "📈 Performance", "⚠️ Anomalies", "🔔 Alerts", "🏅 Scorecards"]
    st.markdown('<div class="side-title">Analytics</div>', unsafe_allow_html=True)
    page_analytics = ["💰 Spend Analysis", "📂 Category Insights", "🌍 Country Insights", "📊 Trends"]
    st.markdown('<div class="side-title">Management</div>', unsafe_allow_html=True)
    page_manage = ["📄 Contracts", "✅ Assessments", "📁 Documents"]
    st.markdown('<div class="side-title">Configuration</div>', unsafe_allow_html=True)
    page_config = ["⚙️ Settings", "👤 Users & Roles"]

    all_pages = page_monitor + page_analytics + page_manage + page_config
    page = st.radio("Navigation", all_pages, index=0, label_visibility="collapsed", key="page_nav")

# ─────────────────────────────────────────────────────────────────
# HEADER + UPLOAD
# ─────────────────────────────────────────────────────────────────
now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
st.markdown(f"""
<div class="top-bar">
  <div>
    <div class="top-title">Supplier Performance Dashboard</div>
    <div class="top-sub">Real-time supplier KPI monitoring &amp; anomaly detection</div>
  </div>
  <div style="font-size:.78rem;color:#8b949e;">🕐 {now_str}</div>
</div>
""", unsafe_allow_html=True)

upload_col, note_col = st.columns([1.5, 4.5])
with upload_col:
    uploaded_file = st.file_uploader("Upload supplier Excel", type=["xlsx", "xls"], label_visibility="collapsed")
with note_col:
    st.caption("Upload your supplier KPI Excel file. The dashboard will update automatically when you change filters or select a supplier.")

if uploaded_file is None:
    st.markdown("""
    <div class="s-card" style="max-width:620px;margin:55px auto;text-align:center;">
      <div style="font-size:3rem;margin-bottom:12px;">📂</div>
      <div style="font-size:1.2rem;font-weight:850;color:#e6edf3;margin-bottom:8px;">Upload your supplier data</div>
      <div style="font-size:.88rem;color:#8b949e;line-height:1.55;">
        Expected columns: <b>Supplier_Name, Country, Category, Delivery_Performance_%, Lead_Time_Days,<br>
        Quality_Score_%, Complaint_Rate_%, Price_Deviation_%</b>.<br>
        Optional columns: Supplier_ID, Status, Anomaly_Flag, Overall_Score, Spend, Notes.
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────────────────────────
# LOAD, MAP, VALIDATE
# ─────────────────────────────────────────────────────────────────
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
    COL_SPEND: ["spend", "spend_under_management", "annual_spend", "total_spend", "purchase_value", "value"],
    COL_NOTES: ["notes", "comment", "comments", "remark", "remarks"],
}

col_map = {internal: find_col(raw, candidates) for internal, candidates in AUTO_MAP.items()}
missing = [col for col in REQUIRED_COLS if col_map.get(col) is None]
if missing:
    st.error(
        "Required columns were not found. Missing: " + ", ".join(missing) +
        "\n\nColumns found in your file: " + ", ".join([str(c) for c in raw.columns])
    )
    st.stop()

rename_map = {actual: internal for internal, actual in col_map.items() if actual is not None}
df = raw.rename(columns=rename_map).copy()

df = to_num(df, [COL_DELIVERY, COL_LEADTIME, COL_QUALITY, COL_COMPLAINT, COL_PRICE_DEV, COL_SCORE, COL_SPEND])
df = df.dropna(subset=REQUIRED_COLS).copy()

if df.empty:
    st.error("The file was loaded, but after cleaning there are no valid supplier rows. Please check numeric KPI columns.")
    st.stop()

if COL_ID not in df.columns:
    df[COL_ID] = [f"S{i + 1:03d}" for i in range(len(df))]

if COL_SCORE not in df.columns or df[COL_SCORE].isna().all():
    df[COL_SCORE] = df.apply(calc_score, axis=1)
else:
    df[COL_SCORE] = df[COL_SCORE].fillna(df.apply(calc_score, axis=1))

if COL_SPEND not in df.columns:
    df[COL_SPEND] = np.nan

df["_risk"] = df[COL_SCORE].apply(risk_label)

if COL_STATUS not in df.columns:
    df[COL_STATUS] = df["_risk"].map({"Low": "Active", "Medium": "At Risk", "High": "High Risk"})
else:
    df[COL_STATUS] = df[COL_STATUS].fillna(df["_risk"].map({"Low": "Active", "Medium": "At Risk", "High": "High Risk"}))

if COL_ANOMALY in df.columns:
    def normalize_anomaly(value) -> int:
        if pd.isna(value):
            return 0
        return 1 if str(value).strip().lower() in {"yes", "ja", "y", "true", "1", "critical", "kritisch"} else 0
    df["_anomaly"] = df[COL_ANOMALY].apply(normalize_anomaly)
else:
    def count_anomalies(row: pd.Series) -> int:
        count = 0
        count += int(pd.notna(row[COL_DELIVERY]) and row[COL_DELIVERY] < 95)
        count += int(pd.notna(row[COL_LEADTIME]) and row[COL_LEADTIME] > 10)
        count += int(pd.notna(row[COL_QUALITY]) and row[COL_QUALITY] < 97)
        count += int(pd.notna(row[COL_COMPLAINT]) and row[COL_COMPLAINT] > 1.0)
        count += int(pd.notna(row[COL_PRICE_DEV]) and abs(row[COL_PRICE_DEV]) > 1.0)
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

for col in ["Delivery", "LeadTime", "Quality", "Complaint", "PriceDev", "Score", "Spend"]:
    if col in agg.columns:
        agg[col] = pd.to_numeric(agg[col], errors="coerce").round(2)

# ─────────────────────────────────────────────────────────────────
# FILTERS — INTERACTIVE
# ─────────────────────────────────────────────────────────────────
f1, f2, f3, f4, f5 = st.columns([1.4, 1.4, 1.3, 1.3, 2.0])
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

# ─────────────────────────────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────────────────────────────
avg_delivery = filt["Delivery"].mean()
avg_lead = filt["LeadTime"].mean()
avg_quality = filt["Quality"].mean()
avg_complaint = filt["Complaint"].mean()
active_suppliers = len(filt)
anomaly_alerts = int(filt["Anomalies"].sum())
spend_total = filt["Spend"].sum(skipna=True) if filt["Spend"].notna().any() else np.nan

spend_text = f"€{spend_total:,.0f}" if pd.notna(spend_total) and spend_total > 0 else "N/A"

st.markdown(f"""
<div class="metric-grid">
  <div class="kpi-card"><div class="kpi-icon" style="background:rgba(56,139,253,.12);">🚚</div><div><div class="kpi-label">On-Time Delivery %</div><div class="kpi-value">{avg_delivery:.1f}%</div><div class="{'kpi-good' if avg_delivery >= 95 else 'kpi-bad'}">{'▲ meets' if avg_delivery >= 95 else '▼ below'} 95% target</div></div></div>
  <div class="kpi-card"><div class="kpi-icon" style="background:rgba(163,113,247,.12);">⏱️</div><div><div class="kpi-label">Avg Lead Time</div><div class="kpi-value">{avg_lead:.1f}d</div><div class="{'kpi-good' if avg_lead <= 10 else 'kpi-bad'}">{'▼ within' if avg_lead <= 10 else '▲ above'} 10d target</div></div></div>
  <div class="kpi-card"><div class="kpi-icon" style="background:rgba(63,185,80,.12);">🛡️</div><div><div class="kpi-label">Quality Score</div><div class="kpi-value">{avg_quality:.1f}%</div><div class="{'kpi-good' if avg_quality >= 97 else 'kpi-bad'}">{'▲ meets' if avg_quality >= 97 else '▼ below'} 97% target</div></div></div>
  <div class="kpi-card"><div class="kpi-icon" style="background:rgba(248,81,73,.12);">⚠️</div><div><div class="kpi-label">Complaint Rate</div><div class="kpi-value">{avg_complaint:.2f}%</div><div class="{'kpi-good' if avg_complaint <= 1 else 'kpi-bad'}">{'▼ within' if avg_complaint <= 1 else '▲ above'} 1% limit</div></div></div>
  <div class="kpi-card"><div class="kpi-icon" style="background:rgba(56,139,253,.12);">👥</div><div><div class="kpi-label">Active Suppliers</div><div class="kpi-value">{active_suppliers}</div><div class="kpi-muted">in current filter</div></div></div>
  <div class="kpi-card"><div class="kpi-icon" style="background:rgba(210,153,34,.12);">🔔</div><div><div class="kpi-label">Anomaly Alerts</div><div class="kpi-value">{anomaly_alerts}</div><div class="{'kpi-bad' if anomaly_alerts > 0 else 'kpi-good'}">{'requires attention' if anomaly_alerts > 0 else 'all clear'}</div></div></div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# SHARED COMPONENTS
# ─────────────────────────────────────────────────────────────────
def render_supplier_selector() -> pd.Series:
    selected = st.selectbox(
        "Click to view supplier profile →",
        supplier_names,
        index=supplier_names.index(st.session_state["selected_supplier"]) if st.session_state["selected_supplier"] in supplier_names else 0,
        key="selected_supplier",
    )
    return filt[filt[COL_SUPPLIER].astype(str) == selected].iloc[0]


def render_supplier_profile(row: pd.Series) -> None:
    color = score_color(float(row["Score"]))
    st.markdown(f"""
    <div class="s-card">
      <div class="s-card-title">Selected Supplier</div>
      <div style="display:flex;gap:12px;align-items:center;margin-bottom:14px;">
        <div class="profile-avatar">{initials(row[COL_SUPPLIER])}</div>
        <div>
          <div style="font-weight:850;font-size:1rem;color:#e6edf3;">{row[COL_SUPPLIER]}</div>
          <div style="font-size:.78rem;color:#8b949e;">{row['Category']} · {row['Country']}</div>
          <div style="margin-top:5px;">{status_html(row['Status'])}</div>
        </div>
      </div>
      <div style="font-size:.75rem;color:#8b949e;">Overall Score</div>
      <div style="font-size:2.15rem;font-weight:900;color:{color};">{row['Score']:.0f}<span style="font-size:1rem;color:#8b949e;">/100</span></div>
      <div style="height:8px;background:#21262d;border-radius:8px;overflow:hidden;margin:6px 0 16px 0;">
        <div style="height:8px;width:{max(min(float(row['Score']), 100), 0)}%;background:{color};"></div>
      </div>
      <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;">
        <div><div class="kpi-label">Delivery</div><div style="font-weight:850;color:{'#3fb950' if row['Delivery'] >= 95 else '#f85149'};">{row['Delivery']:.1f}%</div></div>
        <div><div class="kpi-label">Quality</div><div style="font-weight:850;color:{'#3fb950' if row['Quality'] >= 97 else '#f85149'};">{row['Quality']:.1f}%</div></div>
        <div><div class="kpi-label">Lead Time</div><div style="font-weight:850;color:{'#3fb950' if row['LeadTime'] <= 10 else '#f85149'};">{row['LeadTime']:.1f}d</div></div>
        <div><div class="kpi-label">Complaints</div><div style="font-weight:850;color:{'#3fb950' if row['Complaint'] <= 1 else '#f85149'};">{row['Complaint']:.2f}%</div></div>
        <div><div class="kpi-label">Price Dev</div><div style="font-weight:850;color:{'#3fb950' if abs(row['PriceDev']) <= 1 else '#f85149'};">{row['PriceDev']:+.2f}%</div></div>
        <div><div class="kpi-label">Anomalies</div><div style="font-weight:850;color:#e6edf3;">{int(row['Anomalies'])}</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_top_table(data: pd.DataFrame, rows: int = 12) -> None:
    table_df = data[[COL_SUPPLIER, "Category", "Country", "Delivery", "Quality", "LeadTime", "Complaint", "PriceDev", "Status", "Risk", "Score"]].copy()
    table_df = table_df.sort_values("Score", ascending=False).head(rows)
    table_df.columns = ["Supplier", "Category", "Country", "Delivery %", "Quality %", "Lead Time", "Complaint %", "Price Dev %", "Status", "Risk", "Score"]
    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        height=min(440, 40 + 35 * len(table_df)),
        column_config={
            "Delivery %": st.column_config.ProgressColumn("Delivery %", min_value=0, max_value=100, format="%.1f%%"),
            "Quality %": st.column_config.ProgressColumn("Quality %", min_value=0, max_value=100, format="%.1f%%"),
            "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%.1f"),
            "Lead Time": st.column_config.NumberColumn("Lead Time", format="%.1f d"),
            "Complaint %": st.column_config.NumberColumn("Complaint %", format="%.2f%%"),
            "Price Dev %": st.column_config.NumberColumn("Price Dev %", format="%+.2f%%"),
        },
    )


def render_overview() -> None:
    left, right = st.columns([3.1, 1.1])
    with left:
        st.markdown('<div class="s-card"><div class="s-card-title">📈 Supplier Performance Trend — Delivery vs Quality</div>', unsafe_allow_html=True)
        trend = filt.sort_values("Score", ascending=False).head(15)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=trend[COL_SUPPLIER], y=trend["Delivery"], mode="lines+markers", name="On-Time Delivery %", line=dict(color="#388bfd", width=2)))
        fig.add_trace(go.Scatter(x=trend[COL_SUPPLIER], y=trend["Quality"], mode="lines+markers", name="Quality Score %", line=dict(color="#3fb950", width=2)))
        fig.add_hline(y=95, line_dash="dash", line_color="rgba(56,139,253,.45)", annotation_text="95% target")
        fig.add_hline(y=97, line_dash="dash", line_color="rgba(63,185,80,.45)", annotation_text="97% target")
        fig.update_layout(**plotly_theme(300), xaxis_tickangle=-35)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
        st.markdown('</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="s-card"><div class="s-card-title">📦 Score by Category</div>', unsafe_allow_html=True)
            cat = filt.groupby("Category", as_index=False)["Score"].mean().sort_values("Score")
            fig = px.bar(cat, x="Score", y="Category", orientation="h", color="Score", color_continuous_scale="Blues", range_color=[50, 100])
            fig.update_layout(**plotly_theme(260), coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="s-card"><div class="s-card-title">🌍 Supplier Count by Country</div>', unsafe_allow_html=True)
            country = filt["Country"].value_counts().reset_index()
            country.columns = ["Country", "Count"]
            fig = px.pie(country.head(10), names="Country", values="Count", hole=0.55)
            fig.update_layout(**plotly_theme(260), showlegend=True)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="s-card"><div class="s-card-title">🏆 Top Suppliers</div>', unsafe_allow_html=True)
        row = render_supplier_selector()
        render_top_table(filt)
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        row = filt[filt[COL_SUPPLIER].astype(str) == st.session_state["selected_supplier"]].iloc[0]
        st.markdown('<div class="s-card"><div class="s-card-title">⚠️ Anomaly Detection</div>', unsafe_allow_html=True)
        anomalies = filt[filt["Anomalies"] > 0].sort_values("Score").head(6)
        if anomalies.empty:
            st.success("No anomalies detected in current filters.")
        else:
            for _, a in anomalies.iterrows():
                badge = "alert-badge-high" if a["Score"] < 75 else "alert-badge-med"
                level = "High" if a["Score"] < 75 else "Medium"
                st.markdown(f"""
                <div class="alert-row">
                  <div style="display:flex;gap:8px;align-items:center;justify-content:space-between;">
                    <span class="alert-name">{a[COL_SUPPLIER]}</span><span class="{badge}">{level}</span>
                  </div>
                  <div class="alert-desc">{issue_text(a)}</div>
                  <div class="kpi-muted">{a['Category']} · {a['Country']}</div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        render_supplier_profile(row)


def render_suppliers() -> None:
    left, right = st.columns([2.4, 1])
    with left:
        st.markdown('<div class="s-card"><div class="s-card-title">👥 Supplier Directory</div>', unsafe_allow_html=True)
        selected_row = render_supplier_selector()
        render_top_table(filt, rows=25)
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        render_supplier_profile(selected_row)


def render_performance() -> None:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="s-card"><div class="s-card-title">🎯 Delivery Reliability vs Quality Score</div>', unsafe_allow_html=True)
        fig = px.scatter(filt, x="Delivery", y="Quality", size="Score", color="Risk", hover_name=COL_SUPPLIER, size_max=28, color_discrete_map={"Low": "#3fb950", "Medium": "#d29922", "High": "#f85149"})
        fig.add_vline(x=95, line_dash="dash", line_color="rgba(255,255,255,.25)")
        fig.add_hline(y=97, line_dash="dash", line_color="rgba(255,255,255,.25)")
        fig.update_layout(**plotly_theme(380), xaxis_title="Delivery %", yaxis_title="Quality %")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="s-card"><div class="s-card-title">⏱️ Lead Time vs Complaint Rate</div>', unsafe_allow_html=True)
        fig = px.scatter(filt, x="LeadTime", y="Complaint", size="Score", color="Risk", hover_name=COL_SUPPLIER, size_max=28, color_discrete_map={"Low": "#3fb950", "Medium": "#d29922", "High": "#f85149"})
        fig.add_vline(x=10, line_dash="dash", line_color="rgba(255,255,255,.25)")
        fig.add_hline(y=1, line_dash="dash", line_color="rgba(255,255,255,.25)")
        fig.update_layout(**plotly_theme(380), xaxis_title="Lead Time Days", yaxis_title="Complaint Rate %")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
        st.markdown('</div>', unsafe_allow_html=True)


def render_anomalies() -> None:
    st.markdown('<div class="s-card"><div class="s-card-title">⚠️ Anomaly Management</div>', unsafe_allow_html=True)
    anomalies = filt[filt["Anomalies"] > 0].sort_values(["Risk", "Score"], ascending=[True, True]).copy()
    if anomalies.empty:
        st.success("No anomaly found in the current filter.")
    else:
        anomalies["Issue"] = anomalies.apply(issue_text, axis=1)
        show = anomalies[[COL_SUPPLIER, "Category", "Country", "Delivery", "LeadTime", "Quality", "Complaint", "PriceDev", "Risk", "Score", "Issue"]]
        st.dataframe(show, use_container_width=True, hide_index=True, height=460)
    st.markdown('</div>', unsafe_allow_html=True)


def render_scorecards() -> None:
    st.markdown('<div class="s-card"><div class="s-card-title">🏅 Supplier Scorecards</div>', unsafe_allow_html=True)
    scorecard = filt[[COL_SUPPLIER, "Delivery", "Quality", "LeadTime", "Complaint", "PriceDev", "Anomalies", "Risk", "Score"]].sort_values("Score", ascending=False)
    st.dataframe(
        scorecard,
        use_container_width=True,
        hide_index=True,
        height=500,
        column_config={
            "Delivery": st.column_config.ProgressColumn("Delivery", min_value=0, max_value=100, format="%.1f%%"),
            "Quality": st.column_config.ProgressColumn("Quality", min_value=0, max_value=100, format="%.1f%%"),
            "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%.1f"),
        },
    )
    st.markdown('</div>', unsafe_allow_html=True)


def render_spend_analysis() -> None:
    st.markdown('<div class="s-card"><div class="s-card-title">💰 Spend Analysis</div>', unsafe_allow_html=True)
    if not filt["Spend"].notna().any() or filt["Spend"].sum() <= 0:
        st.info("No Spend column was found in your Excel file. Add a Spend / Annual_Spend / Total_Spend column to activate spend charts.")
        fallback = filt.groupby("Category", as_index=False)["Score"].mean().sort_values("Score", ascending=False)
        fig = px.bar(fallback, x="Category", y="Score", color="Score", color_continuous_scale="Blues")
    else:
        spend = filt.groupby("Category", as_index=False)["Spend"].sum().sort_values("Spend", ascending=False)
        fig = px.bar(spend, x="Category", y="Spend", color="Spend", color_continuous_scale="Blues")
    fig.update_layout(**plotly_theme(420))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    st.markdown('</div>', unsafe_allow_html=True)


def render_category_insights() -> None:
    st.markdown('<div class="s-card"><div class="s-card-title">📂 Category Insights</div>', unsafe_allow_html=True)
    category = filt.groupby("Category", as_index=False).agg(Suppliers=(COL_SUPPLIER, "count"), Avg_Score=("Score", "mean"), Avg_Delivery=("Delivery", "mean"), Avg_Quality=("Quality", "mean"), Avg_Lead_Time=("LeadTime", "mean"), Alerts=("Anomalies", "sum"))
    category = category.round(2).sort_values("Avg_Score", ascending=False)
    st.dataframe(category, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_country_insights() -> None:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="s-card"><div class="s-card-title">🌍 Suppliers by Country</div>', unsafe_allow_html=True)
        country = filt.groupby("Country", as_index=False).agg(Suppliers=(COL_SUPPLIER, "count"), Avg_Score=("Score", "mean"), Alerts=("Anomalies", "sum")).round(2).sort_values("Suppliers", ascending=False)
        st.dataframe(country, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="s-card"><div class="s-card-title">🌍 Country Score Chart</div>', unsafe_allow_html=True)
        country = filt.groupby("Country", as_index=False)["Score"].mean().sort_values("Score", ascending=False)
        fig = px.bar(country, x="Country", y="Score", color="Score", color_continuous_scale="Blues", range_color=[50, 100])
        fig.update_layout(**plotly_theme(360), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
        st.markdown('</div>', unsafe_allow_html=True)


def render_trends() -> None:
    st.markdown('<div class="s-card"><div class="s-card-title">📊 KPI Trends / Ranking</div>', unsafe_allow_html=True)
    metric = st.selectbox("Choose KPI", ["Score", "Delivery", "Quality", "LeadTime", "Complaint", "PriceDev"], key="trend_metric")
    trend = filt.sort_values(metric, ascending=(metric in ["LeadTime", "Complaint", "PriceDev"])).head(20)
    fig = px.line(trend, x=COL_SUPPLIER, y=metric, markers=True, hover_data=["Category", "Country", "Risk", "Score"])
    fig.update_layout(**plotly_theme(430), xaxis_tickangle=-35)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    st.markdown('</div>', unsafe_allow_html=True)


def render_placeholder(title: str, text: str) -> None:
    st.markdown(f'<div class="s-card"><div class="s-card-title">{title}</div><div style="color:#8b949e;line-height:1.6;">{text}</div></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# PAGE ROUTING
# ─────────────────────────────────────────────────────────────────
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
    render_placeholder("📄 Contracts", "This section is connected to supplier risk context. Add contract expiry, contract value, owner, and renewal date columns later to make this page fully data-driven.")
elif page == "✅ Assessments":
    render_scorecards()
elif page == "📁 Documents":
    render_placeholder("📁 Documents", "Document management placeholder: supplier certificates, quality documents, compliance files, and audit reports can be connected here later.")
elif page == "⚙️ Settings":
    render_placeholder("⚙️ Settings", "Settings placeholder: targets are currently fixed at Delivery ≥ 95%, Quality ≥ 97%, Lead Time ≤ 10 days, Complaint Rate ≤ 1%, and Price Deviation within ±1%.")
elif page == "👤 Users & Roles":
    render_placeholder("👤 Users & Roles", "Users & Roles placeholder: this demo app runs locally/Streamlit Cloud. Role-based permissions can be added later if the app is connected to authentication.")

st.markdown("""
<div style="text-align:center;color:#6e7681;font-size:.75rem;padding:24px 0 8px;">
SupplierDash · Interactive KPI Monitoring · Powered by Streamlit
</div>
""", unsafe_allow_html=True)
