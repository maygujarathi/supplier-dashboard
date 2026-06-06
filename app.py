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
# COLUMN NAME CONSTANTS  ← edit here if your Excel uses other names
# ─────────────────────────────────────────────────────────────────
COL_SUPPLIER   = "Supplier_Name"
COL_COUNTRY    = "Country"
COL_CATEGORY   = "Category"
COL_DELIVERY   = "Delivery_Performance_%"
COL_LEADTIME   = "Lead_Time_Days"
COL_QUALITY    = "Quality_Score_%"
COL_COMPLAINT  = "Complaint_Rate_%"
COL_PRICE_DEV  = "Price_Deviation_%"
COL_SCORE      = "Overall_Score"       # optional — calculated if missing
COL_STATUS     = "Status"              # optional
COL_ANOMALY    = "Anomaly_Flag"        # optional
COL_ID         = "Supplier_ID"         # optional

REQUIRED_COLS  = [COL_SUPPLIER, COL_COUNTRY, COL_CATEGORY,
                  COL_DELIVERY, COL_LEADTIME, COL_QUALITY,
                  COL_COMPLAINT, COL_PRICE_DEV]

# ─────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

*, body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; }

/* ── app background ── */
.stApp { background: #0d1117 !important; color: #e6edf3; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── hide default streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── sidebar ── */
section[data-testid="stSidebar"] {
    background: #161b22 !important;
    border-right: 1px solid #30363d;
    min-width: 200px !important; max-width: 200px !important;
}
section[data-testid="stSidebar"] > div { padding: 0 !important; }
section[data-testid="stSidebar"] * { color: #c9d1d9 !important; }

/* ── custom scrollbar ── */
::-webkit-scrollbar { width:6px; height:6px; }
::-webkit-scrollbar-track { background:#161b22; }
::-webkit-scrollbar-thumb { background:#30363d; border-radius:3px; }

/* ── nav items ── */
.nav-logo {
    padding: 18px 16px 12px;
    font-size: 1rem; font-weight: 700; color: #58a6ff !important;
    border-bottom: 1px solid #30363d; margin-bottom: 8px;
    display:flex; align-items:center; gap:8px;
}
.nav-section {
    font-size: 0.68rem; font-weight: 600; color: #6e7681 !important;
    text-transform: uppercase; letter-spacing: .08em;
    padding: 14px 16px 4px;
}
.nav-item {
    padding: 8px 16px; border-radius: 6px; margin: 1px 8px;
    font-size: 0.85rem; font-weight: 500; cursor: pointer;
    display:flex; align-items:center; gap:8px; color: #8b949e !important;
    transition: background .15s;
}
.nav-item:hover { background: #21262d; color: #c9d1d9 !important; }
.nav-item.active {
    background: #1f3a5f; color: #58a6ff !important;
    font-weight: 600;
}
.nav-badge {
    margin-left:auto; background:#da3633; color:#fff !important;
    border-radius:10px; font-size:0.7rem; font-weight:700;
    padding:1px 6px; min-width:18px; text-align:center;
}

/* ── top header bar ── */
.top-bar {
    background: #161b22;
    border-bottom: 1px solid #30363d;
    padding: 14px 24px;
    display:flex; align-items:center; justify-content:space-between;
    flex-wrap: wrap; gap: 10px;
}
.top-bar-title { font-size:1.35rem; font-weight:800; color:#e6edf3; }
.top-bar-sub   { font-size:0.78rem; color:#8b949e; margin-top:1px; }

/* ── filter bar ── */
.filter-bar {
    background: #161b22;
    border-bottom: 1px solid #30363d;
    padding: 10px 24px;
    display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
}

/* ── kpi card ── */
.kpi-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 16px 18px;
    display:flex; align-items:center; gap:14px;
}
.kpi-icon {
    width:42px; height:42px; border-radius:10px;
    display:flex; align-items:center; justify-content:center;
    font-size:1.2rem; flex-shrink:0;
}
.kpi-label  { font-size:0.75rem; color:#8b949e; font-weight:500; margin-bottom:2px; }
.kpi-value  { font-size:1.5rem; font-weight:800; color:#e6edf3; line-height:1.15; }
.kpi-delta-pos { font-size:0.75rem; color:#3fb950; font-weight:600; }
.kpi-delta-neg { font-size:0.75rem; color:#f85149; font-weight:600; }
.kpi-period { font-size:0.7rem; color:#6e7681; }

/* ── section card ── */
.s-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 18px 20px;
    height: 100%;
}
.s-card-title { font-size:0.9rem; font-weight:700; color:#e6edf3; margin-bottom:14px; }

/* ── anomaly items ── */
.anomaly-item {
    display:flex; align-items:flex-start; gap:10px;
    padding: 10px 0; border-bottom:1px solid #21262d;
}
.anomaly-item:last-child { border-bottom: none; }
.a-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; margin-top:5px; }
.a-name  { font-size:0.85rem; font-weight:600; color:#e6edf3; }
.a-desc  { font-size:0.75rem; color:#8b949e; }
.a-time  { font-size:0.7rem; color:#6e7681; margin-left:auto; white-space:nowrap; }
.a-badge {
    font-size:0.68rem; font-weight:700; padding:2px 7px;
    border-radius:10px; white-space:nowrap;
}
.a-high   { background:rgba(248,81,73,0.15); color:#f85149; border:1px solid rgba(248,81,73,0.3); }
.a-medium { background:rgba(210,153,34,0.15); color:#d29922; border:1px solid rgba(210,153,34,0.3); }

/* ── supplier profile panel ── */
.profile-panel {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 18px 20px;
}
.profile-avatar {
    width:44px; height:44px; border-radius:10px;
    background:linear-gradient(135deg,#1f3a5f,#388bfd);
    display:flex; align-items:center; justify-content:center;
    font-size:1.1rem; font-weight:800; color:#58a6ff;
    flex-shrink:0;
}
.p-score-big { font-size:2rem; font-weight:800; color:#e6edf3; }
.p-score-max { font-size:1rem; color:#8b949e; font-weight:500; }
.p-kpi-label { font-size:0.72rem; color:#8b949e; margin-bottom:2px; }
.p-kpi-value { font-size:1rem; font-weight:700; color:#e6edf3; }

/* ── status badges ── */
.st-active   { background:rgba(63,185,80,0.1);  color:#3fb950; border:1px solid rgba(63,185,80,0.3);  border-radius:20px; padding:3px 10px; font-size:0.75rem; font-weight:600; }
.st-atrisk   { background:rgba(210,153,34,0.1); color:#d29922; border:1px solid rgba(210,153,34,0.3); border-radius:20px; padding:3px 10px; font-size:0.75rem; font-weight:600; }
.st-highrisk { background:rgba(248,81,73,0.1);  color:#f85149; border:1px solid rgba(248,81,73,0.3);  border-radius:20px; padding:3px 10px; font-size:0.75rem; font-weight:600; }

/* ── table styling ── */
.stDataFrame { border-radius: 8px; overflow: hidden; }
div[data-testid="stDataFrame"] { border-radius:8px; }

/* ── streamlit widget overrides ── */
div[data-baseweb="select"] > div {
    background:#21262d !important; border-color:#30363d !important;
    color:#c9d1d9 !important; border-radius:8px !important;
    font-size:0.83rem !important;
}
.stSelectbox label { font-size:0.78rem !important; color:#8b949e !important; }

div[data-testid="stMetric"] {
    background:#21262d; border:1px solid #30363d;
    border-radius:8px; padding:12px 14px;
}
div[data-testid="stMetric"] label { color:#8b949e !important; font-size:0.78rem !important; }
div[data-testid="stMetric"] [data-testid="metric-container"] > div:nth-child(2) {
    color:#58a6ff !important; font-weight:800 !important;
}

.stTabs [data-baseweb="tab-list"] {
    background:transparent; border-bottom:1px solid #30363d; gap:4px;
}
.stTabs [data-baseweb="tab"] {
    background:transparent; color:#8b949e; font-weight:600;
    font-size:0.85rem; padding:8px 16px; border:none; border-radius:6px 6px 0 0;
}
.stTabs [aria-selected="true"] {
    background:rgba(88,166,255,0.1) !important;
    color:#58a6ff !important; border-bottom:2px solid #388bfd !important;
}
.stButton > button {
    background:#1f3a5f; border:1px solid #388bfd; color:#58a6ff;
    border-radius:8px; font-weight:600; font-size:0.82rem;
    padding:6px 16px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────
def clean_cols(df):
    df.columns = [str(c).strip() for c in df.columns]
    return df

def to_num(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def calc_score(row):
    s = 100.0
    if pd.notna(row.get(COL_DELIVERY))  and row[COL_DELIVERY]  < 95:  s -= (95  - row[COL_DELIVERY])  * 1.8
    if pd.notna(row.get(COL_LEADTIME))  and row[COL_LEADTIME]  > 10:  s -= (row[COL_LEADTIME] - 10)   * 2.0
    if pd.notna(row.get(COL_QUALITY))   and row[COL_QUALITY]   < 97:  s -= (97  - row[COL_QUALITY])   * 2.5
    if pd.notna(row.get(COL_COMPLAINT)) and row[COL_COMPLAINT] > 1.0: s -= (row[COL_COMPLAINT] - 1.0) * 8
    if pd.notna(row.get(COL_PRICE_DEV)) and abs(row[COL_PRICE_DEV]) > 1.0: s -= (abs(row[COL_PRICE_DEV])-1.0)*3.5
    return max(round(s,1), 0)

def risk_label(score):
    return "Low" if score >= 90 else "Medium" if score >= 75 else "High"

def status_badge_html(status):
    s = str(status).lower()
    if "high" in s: return f'<span class="st-highrisk">High Risk</span>'
    if "risk" in s or "monitor" in s or "medium" in s: return f'<span class="st-atrisk">At Risk</span>'
    return f'<span class="st-active">Active</span>'

def sparkline(values, color="#3fb950", width=80, height=30):
    """Tiny inline SVG sparkline."""
    if not values or len(values) < 2:
        return ""
    lo, hi = min(values), max(values)
    rng = hi - lo if hi != lo else 1
    pts = []
    for i, v in enumerate(values):
        x = i / (len(values)-1) * width
        y = height - ((v - lo) / rng) * (height - 4) - 2
        pts.append(f"{x:.1f},{y:.1f}")
    path = " ".join(pts)
    return (f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            f'xmlns="http://www.w3.org/2000/svg">'
            f'<polyline points="{path}" fill="none" stroke="{color}" stroke-width="1.8" '
            f'stroke-linejoin="round" stroke-linecap="round"/></svg>')

def plotly_theme():
    return dict(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8b949e", size=11),
        margin=dict(t=10, b=30, l=40, r=10),
        xaxis=dict(gridcolor="#21262d", linecolor="#30363d"),
        yaxis=dict(gridcolor="#21262d", linecolor="#30363d"),
    )

def initials(name):
    parts = str(name).split()
    return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else parts[0][1])).upper()

# ─────────────────────────────────────────────────────────────────
# SIDEBAR  — nav only, no column mapping
# ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
<div class="nav-logo">📦 SupplierDash</div>

<div class="nav-section">Monitoring</div>
<div class="nav-item active">🏠 Overview</div>
<div class="nav-item">👥 Suppliers</div>
<div class="nav-item">📈 Performance</div>
<div class="nav-item">⚠️ Anomalies <span class="nav-badge" id="anomaly-count">–</span></div>
<div class="nav-item">🔔 Alerts <span class="nav-badge">8</span></div>
<div class="nav-item">🏅 Scorecards</div>

<div class="nav-section">Analytics</div>
<div class="nav-item">💰 Spend Analysis</div>
<div class="nav-item">📂 Category Insights</div>
<div class="nav-item">🌍 Country Insights</div>
<div class="nav-item">📊 Trends</div>

<div class="nav-section">Management</div>
<div class="nav-item">📄 Contracts</div>
<div class="nav-item">✅ Assessments</div>
<div class="nav-item">📁 Documents</div>

<div class="nav-section">Configuration</div>
<div class="nav-item">⚙️ Settings</div>
<div class="nav-item">👤 Users & Roles</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# TOP HEADER BAR
# ─────────────────────────────────────────────────────────────────
now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
st.markdown(f"""
<div class="top-bar">
    <div>
        <div class="top-bar-title">Supplier Performance Dashboard</div>
        <div class="top-bar-sub">Real-time supplier KPI monitoring &amp; anomaly detection</div>
    </div>
    <div style="color:#6e7681;font-size:0.78rem;">🕐 {now_str}</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# FILE UPLOAD  (compact, in filter bar)
# ─────────────────────────────────────────────────────────────────
with st.container():
    fb_col, *_ = st.columns([2, 5])
    with fb_col:
        uploaded_file = st.file_uploader("", type=["xlsx","xls"], label_visibility="collapsed")

if uploaded_file is None:
    st.markdown("""
<div style="margin:60px auto;max-width:480px;text-align:center;color:#8b949e;">
    <div style="font-size:3rem;margin-bottom:16px;">📂</div>
    <div style="font-size:1.1rem;font-weight:600;color:#e6edf3;margin-bottom:8px;">Upload your supplier data</div>
    <div style="font-size:0.88rem;">Use the file picker above to load an Excel (.xlsx) file.<br>
    Expected columns: <code>Supplier_Name, Country, Category,<br>
    Delivery_Performance_%, Lead_Time_Days, Quality_Score_%,<br>
    Complaint_Rate_%, Price_Deviation_%</code></div>
</div>""", unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────────────────────────
# LOAD & VALIDATE DATA
# ─────────────────────────────────────────────────────────────────
raw = clean_cols(pd.read_excel(uploaded_file))

# Auto-detect column names (case-insensitive fuzzy match)
def find_col(df, candidates):
    low = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in low:
            return low[cand.lower()]
    return None

AUTO_MAP = {
    COL_SUPPLIER:  ["supplier_name","supplier","name","lieferant"],
    COL_COUNTRY:   ["country","land","country_name"],
    COL_CATEGORY:  ["category","material","kategorie","type","material_group"],
    COL_DELIVERY:  ["delivery_performance_%","delivery_performance","on_time_delivery","liefertreue","delivery_%"],
    COL_LEADTIME:  ["lead_time_days","lead_time","lieferzeit","leadtime"],
    COL_QUALITY:   ["quality_score_%","quality_score","qualitätsrate","quality_%","quality"],
    COL_COMPLAINT: ["complaint_rate_%","complaint_rate","reklamationsquote","complaints_%"],
    COL_PRICE_DEV: ["price_deviation_%","price_deviation","preisabweichung","price_dev"],
    COL_SCORE:     ["overall_score","score","gesamtscore"],
    COL_STATUS:    ["status","supplier_status"],
    COL_ANOMALY:   ["anomaly_flag","anomaly","anomalieflag"],
    COL_ID:        ["supplier_id","id","lieferant_id"],
}

col_map = {}   # internal_name → actual df column
for internal, candidates in AUTO_MAP.items():
    found = find_col(raw, candidates)
    col_map[internal] = found  # may be None

missing = [k for k in REQUIRED_COLS if col_map.get(k) is None]
if missing:
    st.error(f"⚠️ Could not find these required columns in your file: **{', '.join(missing)}**\n\n"
             f"Your file has: `{', '.join(raw.columns.tolist())}`")
    st.stop()

# Build clean df with standardised column names
rename = {v: k for k, v in col_map.items() if v is not None}
df = raw.rename(columns=rename).copy()

num_cols = [COL_DELIVERY, COL_LEADTIME, COL_QUALITY, COL_COMPLAINT, COL_PRICE_DEV, COL_SCORE]
df = to_num(df, num_cols)
df = df.dropna(subset=REQUIRED_COLS)

if COL_ID not in df.columns:
    df[COL_ID] = [f"S{i+1:04d}" for i in range(len(df))]

if COL_SCORE not in df.columns or df[COL_SCORE].isna().all():
    df[COL_SCORE] = df.apply(calc_score, axis=1)

df["_risk"] = df[COL_SCORE].apply(risk_label)

if COL_STATUS not in df.columns:
    df[COL_STATUS] = df["_risk"].map({"Low":"Active","Medium":"At Risk","High":"High Risk"})

# anomaly count
if COL_ANOMALY in df.columns:
    def _norm(v):
        if pd.isna(v): return 0
        return 1 if str(v).strip().lower() in {"yes","ja","y","true","1","kritisch"} else 0
    df["_anomaly"] = df[COL_ANOMALY].apply(_norm)
else:
    def _count_anom(row):
        c = 0
        if pd.notna(row.get(COL_DELIVERY))  and row[COL_DELIVERY]  < 95:  c+=1
        if pd.notna(row.get(COL_LEADTIME))  and row[COL_LEADTIME]  > 10:  c+=1
        if pd.notna(row.get(COL_QUALITY))   and row[COL_QUALITY]   < 97:  c+=1
        if pd.notna(row.get(COL_COMPLAINT)) and row[COL_COMPLAINT] > 1.0: c+=1
        if pd.notna(row.get(COL_PRICE_DEV)) and abs(row[COL_PRICE_DEV]) > 1.0: c+=1
        return c
    df["_anomaly"] = df.apply(_count_anom, axis=1)

# aggregate per supplier
agg = df.groupby(COL_SUPPLIER, as_index=False).agg(
    Supplier_ID   = (COL_ID,        "first"),
    Country       = (COL_COUNTRY,   "first"),
    Category      = (COL_CATEGORY,  "first"),
    Delivery      = (COL_DELIVERY,  "mean"),
    LeadTime      = (COL_LEADTIME,  "mean"),
    Quality       = (COL_QUALITY,   "mean"),
    Complaint     = (COL_COMPLAINT, "mean"),
    PriceDev      = (COL_PRICE_DEV, "mean"),
    Score         = (COL_SCORE,     "mean"),
    Anomalies     = ("_anomaly",    "sum"),
    Status        = (COL_STATUS,    "first"),
    Risk          = ("_risk",       "first"),
).sort_values("Score", ascending=False).reset_index(drop=True)
agg["Score"] = agg["Score"].round(1)

# ─────────────────────────────────────────────────────────────────
# FILTER BAR  (top-level filters, always visible)
# ─────────────────────────────────────────────────────────────────
st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
fc1, fc2, fc3, fc4, fc5 = st.columns([1.4, 1.4, 1.3, 1.3, 2.6])

with fc1:
    countries = ["All Countries"] + sorted(agg["Country"].dropna().unique().tolist())
    sel_country = st.selectbox("Country", countries, key="f_country")
with fc2:
    categories = ["All Categories"] + sorted(agg["Category"].dropna().unique().tolist())
    sel_cat = st.selectbox("Category", categories, key="f_cat")
with fc3:
    statuses = ["Active", "All Statuses"]
    sel_status = st.selectbox("Supplier Status", statuses, key="f_status")
with fc4:
    risk_opts = ["All Risk Levels", "Low", "Medium", "High"]
    sel_risk = st.selectbox("Risk Level", risk_opts, key="f_risk")
with fc5:
    search_q = st.text_input("🔍 Search suppliers…", key="f_search", placeholder="Search suppliers…")

# Apply filters
filt = agg.copy()
if sel_country != "All Countries": filt = filt[filt["Country"] == sel_country]
if sel_cat != "All Categories":    filt = filt[filt["Category"] == sel_cat]
if sel_status == "Active":         filt = filt[filt["Status"].str.lower().str.contains("active")]
if sel_risk != "All Risk Levels":  filt = filt[filt["Risk"] == sel_risk]
if search_q:                       filt = filt[filt[COL_SUPPLIER].str.lower().str.contains(search_q.lower(), na=False)]
filt = filt.reset_index(drop=True)

# selected supplier for profile panel
if "sel_supplier" not in st.session_state or st.session_state["sel_supplier"] not in filt[COL_SUPPLIER].values:
    st.session_state["sel_supplier"] = filt[COL_SUPPLIER].iloc[0] if len(filt) else None

sel_row = filt[filt[COL_SUPPLIER] == st.session_state["sel_supplier"]].iloc[0] if st.session_state["sel_supplier"] in filt[COL_SUPPLIER].values else (filt.iloc[0] if len(filt) else None)

st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)

if len(filt) == 0:
    st.warning("No suppliers match the selected filters.")
    st.stop()

# ─────────────────────────────────────────────────────────────────
# KPI CARDS  (6 across)
# ─────────────────────────────────────────────────────────────────
avg_del  = filt["Delivery"].mean()
avg_lt   = filt["LeadTime"].mean()
avg_q    = filt["Quality"].mean()
avg_cmp  = filt["Complaint"].mean()
n_sup    = len(filt)
n_anom   = int(filt["Anomalies"].sum())

kpi_html = f"""
<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:10px;padding:0 0 12px 0;">

  <div class="kpi-card">
    <div class="kpi-icon" style="background:rgba(56,139,253,0.12);">🚚</div>
    <div>
      <div class="kpi-label">On-Time Delivery %</div>
      <div class="kpi-value">{avg_del:.1f}%</div>
      <div class="kpi-delta-{'pos' if avg_del>=95 else 'neg'}">{'▲' if avg_del>=95 else '▼'} vs 95% target</div>
    </div>
  </div>

  <div class="kpi-card">
    <div class="kpi-icon" style="background:rgba(163,113,247,0.12);">⏱</div>
    <div>
      <div class="kpi-label">Avg Lead Time</div>
      <div class="kpi-value">{avg_lt:.1f}d</div>
      <div class="kpi-delta-{'neg' if avg_lt>10 else 'pos'}">{'▲ above' if avg_lt>10 else '▼ within'} 10d target</div>
    </div>
  </div>

  <div class="kpi-card">
    <div class="kpi-icon" style="background:rgba(63,185,80,0.12);">🛡</div>
    <div>
      <div class="kpi-label">Quality Score</div>
      <div class="kpi-value">{avg_q:.1f}%</div>
      <div class="kpi-delta-{'pos' if avg_q>=97 else 'neg'}">{'▲' if avg_q>=97 else '▼'} vs 97% target</div>
    </div>
  </div>

  <div class="kpi-card">
    <div class="kpi-icon" style="background:rgba(248,81,73,0.12);">⚠️</div>
    <div>
      <div class="kpi-label">Complaint Rate</div>
      <div class="kpi-value">{avg_cmp:.2f}%</div>
      <div class="kpi-delta-{'neg' if avg_cmp>1 else 'pos'}">{'▲ above' if avg_cmp>1 else '▼ within'} 1% limit</div>
    </div>
  </div>

  <div class="kpi-card">
    <div class="kpi-icon" style="background:rgba(56,139,253,0.12);">👥</div>
    <div>
      <div class="kpi-label">Active Suppliers</div>
      <div class="kpi-value">{n_sup}</div>
      <div class="kpi-period">in current filter</div>
    </div>
  </div>

  <div class="kpi-card">
    <div class="kpi-icon" style="background:rgba(210,153,34,0.12);">🔔</div>
    <div>
      <div class="kpi-label">Anomaly Alerts</div>
      <div class="kpi-value">{n_anom}</div>
      <div class="kpi-delta-{'neg' if n_anom>0 else 'pos'}">{'⚡ requires attention' if n_anom>0 else '✓ all clear'}</div>
    </div>
  </div>

</div>
"""
st.markdown(kpi_html, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# MAIN CONTENT GRID
# ─────────────────────────────────────────────────────────────────
left_col, right_col = st.columns([3.2, 1.0])

with left_col:
    # ── Performance Trend chart (Delivery vs Quality) ──────────
    st.markdown('<div class="s-card">', unsafe_allow_html=True)
    st.markdown('<div class="s-card-title">📈 Supplier Performance Trend — Delivery vs Quality</div>', unsafe_allow_html=True)

    trend_df = filt[[COL_SUPPLIER, "Delivery", "Quality", "Score"]].copy()
    trend_df = trend_df.sort_values("Score", ascending=False).head(15)
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=trend_df[COL_SUPPLIER], y=trend_df["Delivery"],
        mode="lines+markers", name="On-Time Delivery %",
        line=dict(color="#388bfd", width=2), marker=dict(size=5),
    ))
    fig_trend.add_trace(go.Scatter(
        x=trend_df[COL_SUPPLIER], y=trend_df["Quality"],
        mode="lines+markers", name="Quality Score %",
        line=dict(color="#3fb950", width=2), marker=dict(size=5),
    ))
    fig_trend.add_hline(y=95, line_dash="dash", line_color="rgba(56,139,253,0.4)", annotation_text="95% target")
    fig_trend.add_hline(y=97, line_dash="dash", line_color="rgba(63,185,80,0.4)",  annotation_text="97% target")
    fig_trend.update_layout(
        **plotly_theme(),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(color="#8b949e", size=10)),
        xaxis_tickangle=-35, height=220,
        margin=dict(t=30, b=60, l=40, r=10),
    )
    st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)

    # ── Two charts side by side ─────────────────────────────────
    ch1, ch2 = st.columns(2)
    with ch1:
        st.markdown('<div class="s-card">', unsafe_allow_html=True)
        st.markdown('<div class="s-card-title">📦 Score by Category</div>', unsafe_allow_html=True)
        cat_df = filt.groupby("Category")["Score"].mean().reset_index().sort_values("Score", ascending=True)
        fig_cat = px.bar(cat_df, y="Category", x="Score", orientation="h",
                         color="Score", color_continuous_scale="Blues",
                         range_color=[50, 100])
        fig_cat.update_traces(marker_line_width=0)
        fig_cat.update_layout(**plotly_theme(), height=200, showlegend=False,
                              coloraxis_showscale=False, margin=dict(t=5,b=10,l=5,r=10))
        st.plotly_chart(fig_cat, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    with ch2:
        st.markdown('<div class="s-card">', unsafe_allow_html=True)
        st.markdown('<div class="s-card-title">🌍 Supplier Count by Country</div>', unsafe_allow_html=True)
        ctry_df = filt["Country"].value_counts().reset_index()
        ctry_df.columns = ["Country","Count"]
        fig_ctry = px.pie(ctry_df.head(8), names="Country", values="Count", hole=0.55,
                          color_discrete_sequence=px.colors.qualitative.Set2)
        fig_ctry.update_traces(textinfo="percent+label", textfont_size=10)
        fig_ctry.update_layout(**plotly_theme(), height=200, showlegend=False,
                               margin=dict(t=5, b=5, l=5, r=5))
        st.plotly_chart(fig_ctry, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)

    # ── Top Suppliers table ─────────────────────────────────────
    st.markdown('<div class="s-card">', unsafe_allow_html=True)
    st.markdown('<div class="s-card-title">🏆 Top Suppliers</div>', unsafe_allow_html=True)

    table_df = filt[[COL_SUPPLIER, "Category", "Country",
                     "Delivery", "Quality", "PriceDev", "Status", "Score"]].copy()
    table_df.columns = ["Supplier", "Category", "Country",
                        "Delivery %", "Quality %", "Price Dev %", "Status", "Score"]
    table_df = table_df.head(10)
    table_df["Delivery %"] = table_df["Delivery %"].round(1)
    table_df["Quality %"]  = table_df["Quality %"].round(1)
    table_df["Price Dev %"]= table_df["Price Dev %"].round(2)

    # clickable supplier selection
    click_col, _ = st.columns([3, 1])
    with click_col:
        sel_in_table = st.selectbox(
            "Click to view supplier profile →",
            filt[COL_SUPPLIER].tolist(),
            index=filt[COL_SUPPLIER].tolist().index(st.session_state["sel_supplier"])
                  if st.session_state["sel_supplier"] in filt[COL_SUPPLIER].values else 0,
            key="sel_supplier",
            label_visibility="visible",
        )

    st.dataframe(
        table_df.style
            .background_gradient(subset=["Score"], cmap="RdYlGn", vmin=50, vmax=100)
            .format({"Delivery %":"{:.1f}","Quality %":"{:.1f}","Price Dev %":"{:+.2f}","Score":"{:.1f}"}),
        use_container_width=True, hide_index=True, height=320,
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# RIGHT PANEL — Anomalies + Supplier Profile
# ─────────────────────────────────────────────────────────────────
with right_col:

    # ── Anomaly Alerts ─────────────────────────────────────────
    st.markdown('<div class="s-card" style="margin-bottom:10px;">', unsafe_allow_html=True)
    st.markdown(f'<div class="s-card-title">⚠️ Anomaly Detection <span style="background:#da3633;color:#fff;border-radius:10px;padding:2px 7px;font-size:0.72rem;font-weight:700;margin-left:6px;">{n_anom}</span></div>', unsafe_allow_html=True)

    anomaly_sups = filt[filt["Anomalies"] > 0].sort_values("Score").head(5)
    if len(anomaly_sups) == 0:
        st.markdown('<div style="color:#3fb950;font-size:0.85rem;padding:8px 0;">✅ No anomalies detected</div>', unsafe_allow_html=True)
    else:
        items = ""
        for _, row in anomaly_sups.iterrows():
            sev   = "high" if row["Score"] < 75 else "medium"
            badge = f'<span class="a-badge a-{sev}">{"High" if sev=="high" else "Medium"}</span>'
            # determine worst KPI
            issues = []
            if pd.notna(row["Delivery"])  and row["Delivery"]  < 95:  issues.append(f"Delivery at {row['Delivery']:.0f}%")
            if pd.notna(row["Quality"])   and row["Quality"]   < 97:  issues.append(f"Quality at {row['Quality']:.0f}%")
            if pd.notna(row["LeadTime"])  and row["LeadTime"]  > 10:  issues.append(f"Lead time {row['LeadTime']:.0f}d")
            if pd.notna(row["Complaint"]) and row["Complaint"] > 1.0: issues.append(f"Complaints {row['Complaint']:.1f}%")
            desc = issues[0] if issues else "Multiple KPI issues"
            items += f"""
<div class="anomaly-item">
  <div>
    <div style="display:flex;align-items:center;gap:6px;margin-bottom:3px;">
      <span class="a-name">{row[COL_SUPPLIER]}</span>{badge}
    </div>
    <div class="a-desc">{desc}</div>
    <div class="kpi-period">{row['Category']} · {row['Country']}</div>
  </div>
</div>"""
        st.markdown(items, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Selected Supplier Profile ───────────────────────────────
    if sel_row is not None:
        score   = sel_row["Score"]
        s_color = "#3fb950" if score >= 90 else "#d29922" if score >= 75 else "#f85149"
        init    = initials(sel_row[COL_SUPPLIER])

        del_c  = "#3fb950" if sel_row["Delivery"] >= 95  else "#f85149"
        q_c    = "#3fb950" if sel_row["Quality"]  >= 97  else "#f85149"
        lt_c   = "#3fb950" if sel_row["LeadTime"] <= 10  else "#f85149"
        cmp_c  = "#3fb950" if sel_row["Complaint"]<= 1.0 else "#f85149"
        pd_c   = "#3fb950" if abs(sel_row["PriceDev"]) <= 1.0 else "#f85149"

        st.markdown(f"""
<div class="profile-panel">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
    <div class="profile-avatar">{init}</div>
    <div>
      <div style="font-size:0.92rem;font-weight:700;color:#e6edf3;">{sel_row[COL_SUPPLIER]}</div>
      <div style="font-size:0.75rem;color:#8b949e;">{sel_row['Category']} · {sel_row['Country']}</div>
      <div style="margin-top:3px;">{status_badge_html(sel_row['Status'])}</div>
    </div>
  </div>

  <div style="margin-bottom:14px;">
    <div style="color:#8b949e;font-size:0.72rem;margin-bottom:2px;">Overall Score</div>
    <div>
      <span class="p-score-big" style="color:{s_color};">{score:.0f}</span>
      <span class="p-score-max">/100</span>
    </div>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:4px;">
    <div>
      <div class="p-kpi-label">Delivery</div>
      <div class="p-kpi-value" style="color:{del_c};">{sel_row['Delivery']:.1f}%</div>
    </div>
    <div>
      <div class="p-kpi-label">Quality</div>
      <div class="p-kpi-value" style="color:{q_c};">{sel_row['Quality']:.1f}%</div>
    </div>
    <div>
      <div class="p-kpi-label">Price Dev</div>
      <div class="p-kpi-value" style="color:{pd_c};">{sel_row['PriceDev']:+.1f}%</div>
    </div>
    <div>
      <div class="p-kpi-label">Lead Time</div>
      <div class="p-kpi-value" style="color:{lt_c};">{sel_row['LeadTime']:.1f}d</div>
    </div>
    <div>
      <div class="p-kpi-label">Complaints</div>
      <div class="p-kpi-value" style="color:{cmp_c};">{sel_row['Complaint']:.2f}%</div>
    </div>
    <div>
      <div class="p-kpi-label">Anomalies</div>
      <div class="p-kpi-value">{int(sel_row['Anomalies'])}</div>
    </div>
  </div>

  <div style="margin-top:14px;padding-top:12px;border-top:1px solid #21262d;">
    <div style="color:#8b949e;font-size:0.72rem;margin-bottom:6px;">Score breakdown</div>
    <div style="background:#21262d;border-radius:6px;overflow:hidden;height:8px;">
      <div style="width:{score}%;height:8px;background:linear-gradient(90deg,{s_color}88,{s_color});border-radius:6px;"></div>
    </div>
    <div style="display:flex;justify-content:space-between;font-size:0.68rem;color:#6e7681;margin-top:4px;">
      <span>0</span><span>50</span><span>100</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# BOTTOM: scatter & risk distribution
# ─────────────────────────────────────────────────────────────────
st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
b1, b2 = st.columns(2)

with b1:
    st.markdown('<div class="s-card">', unsafe_allow_html=True)
    st.markdown('<div class="s-card-title">🎯 Delivery Reliability vs Quality Score</div>', unsafe_allow_html=True)
    fig_sc = px.scatter(filt, x="Delivery", y="Quality", size="Score", color="Score",
                        hover_name=COL_SUPPLIER, color_continuous_scale="RdYlGn",
                        range_color=[50,100], size_max=20)
    fig_sc.add_vline(x=95, line_dash="dash", line_color="rgba(255,255,255,0.2)")
    fig_sc.add_hline(y=97, line_dash="dash", line_color="rgba(255,255,255,0.2)")
    fig_sc.update_layout(**plotly_theme(), height=240, coloraxis_showscale=False,
                         xaxis_title="Delivery %", yaxis_title="Quality %")
    st.plotly_chart(fig_sc, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with b2:
    st.markdown('<div class="s-card">', unsafe_allow_html=True)
    st.markdown('<div class="s-card-title">🔴 Risk Distribution</div>', unsafe_allow_html=True)
    risk_df = filt["Risk"].value_counts().reset_index()
    risk_df.columns = ["Risk","Count"]
    color_map = {"Low":"#3fb950","Medium":"#d29922","High":"#f85149"}
    fig_risk = px.pie(risk_df, names="Risk", values="Count", hole=0.6,
                      color="Risk", color_discrete_map=color_map)
    fig_risk.update_traces(textinfo="percent+label", textfont_size=10)
    fig_risk.update_layout(**plotly_theme(), height=240, showlegend=True,
                           legend=dict(font=dict(color="#8b949e",size=10)),
                           margin=dict(t=5,b=5,l=5,r=5))
    st.plotly_chart(fig_risk, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;color:#6e7681;font-size:0.75rem;padding:20px 0 10px;">
  SupplierDash · Enterprise Edition &nbsp;·&nbsp; Powered by Streamlit
</div>""", unsafe_allow_html=True)
