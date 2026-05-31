import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="Supplier Evaluation Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    *, *::before, *::after {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }

    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #10111f 50%, #0d0f22 100%);
        color: #e5e7eb;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
        max-width: 1600px;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10,14,39,0.95) 0%, rgba(13,15,34,0.95) 100%);
        border-right: 1px solid rgba(255,255,255,0.08);
        backdrop-filter: blur(10px);
    }

    section[data-testid="stSidebar"] * {
        color: #e5e7eb !important;
    }

    .main-header {
        font-size: 3rem;
        font-weight: 900;
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 50%, #2563eb 100%);
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
        letter-spacing: -0.03em;
        line-height: 1.1;
    }

    .main-subtitle {
        font-size: 0.95rem;
        color: #9ca3af;
        font-weight: 500;
        margin-bottom: 2rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .premium-card {
        background: linear-gradient(135deg, rgba(30,41,59,0.6) 0%, rgba(25,35,50,0.4) 100%);
        border: 1px solid rgba(148,163,184,0.12);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05);
        backdrop-filter: blur(20px);
        transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
        margin-bottom: 1rem;
    }

    .premium-card:hover {
        background: linear-gradient(135deg, rgba(30,41,59,0.8) 0%, rgba(25,35,50,0.6) 100%);
        border-color: rgba(148,163,184,0.25);
        box-shadow: 0 12px 40px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.08);
    }

    .metric-card {
        background: linear-gradient(135deg, rgba(30,41,59,0.5) 0%, rgba(25,35,50,0.3) 100%);
        border: 1px solid rgba(96,165,250,0.15);
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 6px 24px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.05);
        backdrop-filter: blur(15px);
        min-height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.3s ease;
        margin-bottom: 0.5rem;
    }

    .metric-card:hover {
        border-color: rgba(96,165,250,0.3);
        background: linear-gradient(135deg, rgba(30,41,59,0.7) 0%, rgba(25,35,50,0.5) 100%);
    }

    .metric-label {
        font-size: 0.78rem;
        color: #9ca3af;
        font-weight: 600;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    .metric-value {
        font-size: 1.85rem;
        font-weight: 800;
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.2;
        word-break: break-word;
    }

    .metric-sub {
        margin-top: 10px;
        color: #6b7280;
        font-size: 0.78rem;
        font-weight: 500;
    }

    /* ── inline KPI grid inside premium-card ── */
    .kpi-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin: 8px 0 12px;
    }

    .kpi-cell {
        background: rgba(30,41,59,0.5);
        border: 1px solid rgba(96,165,250,0.12);
        border-radius: 10px;
        padding: 12px 14px;
    }

    .kpi-cell-label {
        font-size: 0.72rem;
        font-weight: 600;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 4px;
    }

    .kpi-cell-value {
        font-size: 1.15rem;
        font-weight: 700;
        color: #f1f5f9;
        line-height: 1.2;
    }

    .kpi-cell-delta {
        font-size: 0.75rem;
        font-weight: 500;
        margin-top: 2px;
    }

    .delta-pos { color: #4ade80; }
    .delta-neg { color: #f87171; }

    .supplier-item {
        background: linear-gradient(135deg, rgba(30,41,59,0.4) 0%, rgba(25,35,50,0.2) 100%);
        border: 1px solid rgba(96,165,250,0.1);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }

    .supplier-item:hover {
        background: linear-gradient(135deg, rgba(30,41,59,0.6) 0%, rgba(25,35,50,0.4) 100%);
        border-color: rgba(96,165,250,0.25);
        box-shadow: 0 6px 24px rgba(0,0,0,0.3);
    }

    .supplier-name {
        font-weight: 700;
        color: #f1f5f9;
        font-size: 1.0rem;
        margin-bottom: 4px;
        letter-spacing: -0.01em;
    }

    .supplier-meta {
        color: #9ca3af;
        font-size: 0.82rem;
        font-weight: 500;
    }

    .badge {
        display: inline-block;
        padding: 5px 11px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 4px;
        letter-spacing: 0.02em;
    }

    .badge-success {
        background: rgba(34,197,94,0.15);
        color: #86efac;
        border: 1px solid rgba(34,197,94,0.3);
    }

    .badge-warning {
        background: rgba(251,146,60,0.15);
        color: #fed7aa;
        border: 1px solid rgba(251,146,60,0.3);
    }

    .badge-danger {
        background: rgba(239,68,68,0.15);
        color: #fca5a5;
        border: 1px solid rgba(239,68,68,0.3);
    }

    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #f1f5f9;
        margin-bottom: 16px;
        letter-spacing: -0.01em;
    }

    .insight-box {
        background: linear-gradient(135deg, rgba(34,197,94,0.08) 0%, rgba(34,197,94,0.04) 100%);
        border: 1px solid rgba(34,197,94,0.2);
        border-radius: 12px;
        padding: 14px 16px;
        color: #d1fae5;
        margin-bottom: 10px;
        backdrop-filter: blur(10px);
        font-size: 0.9rem;
        line-height: 1.6;
    }

    .warning-box {
        background: linear-gradient(135deg, rgba(251,146,60,0.08) 0%, rgba(251,146,60,0.04) 100%);
        border: 1px solid rgba(251,146,60,0.2);
        border-radius: 12px;
        padding: 14px 16px;
        color: #ffedd5;
        margin-bottom: 10px;
        backdrop-filter: blur(10px);
        font-size: 0.9rem;
        line-height: 1.6;
    }

    .critical-box {
        background: linear-gradient(135deg, rgba(239,68,68,0.08) 0%, rgba(239,68,68,0.04) 100%);
        border: 1px solid rgba(239,68,68,0.2);
        border-radius: 12px;
        padding: 14px 16px;
        color: #fecaca;
        margin-bottom: 10px;
        backdrop-filter: blur(10px);
        font-size: 0.9rem;
        line-height: 1.6;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
        border-bottom: 1px solid rgba(148,163,184,0.1);
    }

    .stTabs [data-baseweb="tab"] {
        height: 44px;
        border-radius: 8px 8px 0 0;
        background: transparent;
        color: #9ca3af;
        font-weight: 600;
        padding: 0 18px;
        font-size: 0.9rem;
        transition: all 0.3s ease;
        border: none;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(96,165,250,0.15) 0%, rgba(96,165,250,0.08) 100%) !important;
        color: #60a5fa !important;
        border-bottom: 2px solid #3b82f6 !important;
    }

    .stButton > button {
        border-radius: 10px;
        border: 1px solid rgba(96,165,250,0.3);
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        font-weight: 600;
        padding: 10px 20px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(59,130,246,0.3);
        font-size: 0.9rem;
    }

    .stButton > button:hover {
        border-color: rgba(96,165,250,0.5);
        box-shadow: 0 6px 20px rgba(59,130,246,0.4);
        transform: translateY(-2px);
    }

    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: rgba(30,41,59,0.3); }
    ::-webkit-scrollbar-thumb { background: rgba(96,165,250,0.3); border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(96,165,250,0.5); }

    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .premium-card, .metric-card { animation: fadeInUp 0.6s ease-out; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# HELPERS
# =========================================================
def clean_columns(df):
    df.columns = [str(c).strip() for c in df.columns]
    return df

def to_numeric_safe(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def normalize_anomaly_flag(value):
    if pd.isna(value):
        return 0
    return 1 if str(value).strip().lower() in {"yes","ja","y","true","1","kritisch"} else 0

def calculate_anomalies(row):
    count = 0
    if pd.notna(row.get("Liefertreue"))      and row["Liefertreue"]      < 95:  count += 1
    if pd.notna(row.get("Lieferzeit"))        and row["Lieferzeit"]        > 10:  count += 1
    if pd.notna(row.get("Qualitätsrate"))     and row["Qualitätsrate"]     < 97:  count += 1
    if pd.notna(row.get("Reklamationsquote")) and row["Reklamationsquote"] > 1.0: count += 1
    if pd.notna(row.get("Preisabweichung"))   and abs(row["Preisabweichung"]) > 1.0: count += 1
    return count

def calculate_score(row):
    s = 100.0
    if pd.notna(row.get("Liefertreue"))      and row["Liefertreue"]      < 95:  s -= (95  - row["Liefertreue"])      * 1.8
    if pd.notna(row.get("Lieferzeit"))        and row["Lieferzeit"]        > 10:  s -= (row["Lieferzeit"]  - 10)       * 2.0
    if pd.notna(row.get("Qualitätsrate"))     and row["Qualitätsrate"]     < 97:  s -= (97  - row["Qualitätsrate"])    * 2.5
    if pd.notna(row.get("Reklamationsquote")) and row["Reklamationsquote"] > 1.0: s -= (row["Reklamationsquote"] - 1.0) * 8
    if pd.notna(row.get("Preisabweichung"))   and abs(row["Preisabweichung"]) > 1.0: s -= (abs(row["Preisabweichung"]) - 1.0) * 3.5
    if pd.notna(row.get("Anomalien")):        s -= row["Anomalien"] * 0.5
    return max(round(s, 1), 0)

def risk_level(score):
    return "Low" if score >= 90 else "Medium" if score >= 75 else "High"

def status_label(score):
    return "Excellent" if score >= 90 else "Monitor" if score >= 75 else "Critical"

def critical_kpi(row):
    problems = {
        "Delivery":   (95  - row["Liefertreue"])        if pd.notna(row.get("Liefertreue"))      and row["Liefertreue"]      < 95  else 0,
        "Lead Time":  (row["Lieferzeit"]  - 10)          if pd.notna(row.get("Lieferzeit"))        and row["Lieferzeit"]        > 10  else 0,
        "Quality":    (97  - row["Qualitätsrate"])        if pd.notna(row.get("Qualitätsrate"))     and row["Qualitätsrate"]     < 97  else 0,
        "Complaints": (row["Reklamationsquote"] - 1.0)   if pd.notna(row.get("Reklamationsquote")) and row["Reklamationsquote"] > 1.0 else 0,
        "Price Dev.": (abs(row["Preisabweichung"]) - 1.0) if pd.notna(row.get("Preisabweichung"))  and abs(row["Preisabweichung"]) > 1.0 else 0,
    }
    m = max(problems, key=problems.get)
    return m if problems[m] > 0 else "None"

def supplier_strengths(row):
    r = []
    if row["Liefertreue"]      >= 95:  r.append("strong delivery")
    if row["Qualitätsrate"]    >= 97:  r.append("excellent quality")
    if row["Lieferzeit"]       <= 10:  r.append("fast lead time")
    if row["Reklamationsquote"]<= 1.0: r.append("low complaints")
    if abs(row["Preisabweichung"]) <= 1.0: r.append("stable pricing")
    return ", ".join(r[:3]) if r else "mixed profile"

def score_color(score):
    return "#22c55e" if score >= 90 else "#f59e0b" if score >= 75 else "#ef4444"

def donut_chart(value, color):
    fig = go.Figure(go.Pie(
        values=[value, max(0, 100 - value)],
        hole=0.72,
        marker_colors=[color, "rgba(148,163,184,0.1)"],
        textinfo="none", sort=False, hoverinfo="skip",
    ))
    fig.update_layout(
        showlegend=False,
        margin=dict(t=0, l=0, r=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        annotations=[dict(
            text=f"<b style='font-size:32px;color:{color}'>{value:.0f}</b><br>"
                 f"<span style='font-size:12px;color:#9ca3af'>out of 100</span>",
            x=0.5, y=0.5, showarrow=False, font_size=20,
        )],
    )
    return fig

def plotly_dark_layout(**kwargs):
    base = dict(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9ca3af", family="Inter, -apple-system, sans-serif"),
        margin=dict(t=40, b=40, l=40, r=40),
    )
    base.update(kwargs)
    return base

def delta_html(val, target, invert=False):
    """Return HTML delta span. invert=True means lower is better."""
    diff = val - target
    if invert:
        good = diff <= 0
    else:
        good = diff >= 0
    cls = "delta-pos" if good else "delta-neg"
    sign = "+" if diff > 0 else ""
    return f'<span class="kpi-cell-delta {cls}">{sign}{diff:.1f}</span>'

# =========================================================
# HEADER
# =========================================================
h1, h2 = st.columns([0.7, 0.3])
with h1:
    st.markdown('<div class="main-header">Supplier Evaluation Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-subtitle">🔍 Performance Analytics · Risk Assessment · KPI Monitoring</div>', unsafe_allow_html=True)
with h2:
    st.write("")
    st.markdown(
        f'<p style="text-align:right;color:#6b7280;font-size:0.9rem;">Last updated: {datetime.now().strftime("%d.%m.%Y %H:%M")}</p>',
        unsafe_allow_html=True,
    )
st.markdown("---")

# =========================================================
# SIDEBAR — UPLOAD
# =========================================================
with st.sidebar:
    st.markdown('<div class="section-title" style="margin-top:1rem;">📊 Data Source</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])

if uploaded_file is None:
    st.info("👈 Please upload an Excel file in the sidebar to get started.")
    st.stop()

raw_df = clean_columns(pd.read_excel(uploaded_file))
all_cols = ["-- Not available --"] + list(raw_df.columns)

def idx(name):
    return all_cols.index(name) if name in all_cols else 0

with st.sidebar:
    st.markdown('<div class="section-title">🔗 Column Mapping</div>', unsafe_allow_html=True)
    supplier_col    = st.selectbox("Supplier",             all_cols, index=idx("Supplier_Name"))
    country_col     = st.selectbox("Country",              all_cols, index=idx("Country"))
    material_col    = st.selectbox("Material / Category",  all_cols, index=idx("Category"))
    delivery_col    = st.selectbox("On-Time Delivery %",   all_cols, index=idx("Delivery_Performance_%"))
    leadtime_col    = st.selectbox("Lead Time (Days)",     all_cols, index=idx("Lead_Time_Days"))
    quality_col     = st.selectbox("Quality Score %",      all_cols, index=idx("Quality_Score_%"))
    complaint_col   = st.selectbox("Complaint Rate %",     all_cols, index=idx("Complaint_Rate_%"))
    price_col       = st.selectbox("Price Deviation %",    all_cols, index=idx("Price_Deviation_%"))
    score_col       = st.selectbox("Score (optional)",     all_cols, index=idx("Overall_Score"))
    status_col      = st.selectbox("Status (optional)",    all_cols, index=idx("Status"))
    anomaly_col     = st.selectbox("Anomaly Flag (opt.)",  all_cols, index=idx("Anomaly_Flag"))
    supplier_id_col = st.selectbox("Supplier ID (opt.)",   all_cols, index=idx("Supplier_ID"))
    st.markdown("")
    load_data = st.button("📈 Load Dashboard", use_container_width=True)

if not load_data:
    st.stop()

# =========================================================
# VALIDATE & BUILD DATAFRAME
# =========================================================
required_map = {
    "Supplier": supplier_col, "Country": country_col, "Material": material_col,
    "Liefertreue": delivery_col, "Lieferzeit": leadtime_col, "Qualitätsrate": quality_col,
    "Reklamationsquote": complaint_col, "Preisabweichung": price_col,
}
missing = [k for k, v in required_map.items() if v == "-- Not available --"]
if missing:
    st.error(f"⚠️ Please map all required fields: {', '.join(missing)}")
    st.stop()

mapping = {v: k for k, v in required_map.items()}
for src, tgt in {score_col:"Score", status_col:"Status", anomaly_col:"Anomaly_Flag", supplier_id_col:"Supplier_ID"}.items():
    if src != "-- Not available --":
        mapping[src] = tgt

df = raw_df.rename(columns=mapping).copy()
if "Supplier_ID" not in df.columns:
    df["Supplier_ID"] = [f"S{i+1:04d}" for i in range(len(df))]

df = to_numeric_safe(df, ["Liefertreue","Lieferzeit","Qualitätsrate","Reklamationsquote","Preisabweichung","Score"])
df = df.dropna(subset=list(required_map.keys()))

df["Anomalien"]     = df["Anomaly_Flag"].apply(normalize_anomaly_flag) if "Anomaly_Flag" in df.columns else df.apply(calculate_anomalies, axis=1)
if "Score"  not in df.columns: df["Score"]  = df.apply(calculate_score,  axis=1)
if "Status" not in df.columns: df["Status"] = df["Score"].apply(status_label)

df["Risk"]     = df["Score"].apply(risk_level)
df["Crit_KPI"] = df.apply(critical_kpi, axis=1)
df["Strengths"]= df.apply(supplier_strengths, axis=1)

agg = df.groupby("Supplier", as_index=False).agg({
    "Supplier_ID":"first","Material":"first","Country":"first",
    "Liefertreue":"mean","Lieferzeit":"mean","Qualitätsrate":"mean",
    "Reklamationsquote":"mean","Preisabweichung":"mean",
    "Score":"mean","Anomalien":"sum",
    "Status":"first","Risk":"first","Crit_KPI":"first","Strengths":"first",
}).sort_values("Score", ascending=False).reset_index(drop=True)
agg["Score"] = agg["Score"].round(1)

# =========================================================
# SIDEBAR — FILTERS
# =========================================================
with st.sidebar:
    st.markdown('<div class="section-title" style="margin-top:2rem;">🎯 Filters</div>', unsafe_allow_html=True)
    materials = ["All"] + sorted(agg["Material"].astype(str).dropna().unique().tolist())
    sel_mat   = st.selectbox("Material Category", materials)
    filtered  = agg if sel_mat == "All" else agg[agg["Material"] == sel_mat]
    sel_sup   = st.selectbox("Select Supplier", filtered["Supplier"].tolist())

sel = filtered[filtered["Supplier"] == sel_sup].iloc[0]

# =========================================================
# TOP KPI CARDS  — pure HTML, no st.metric() inside divs
# =========================================================
st.markdown("")
for col, (icon, label, value, sub) in zip(
    st.columns(5),
    [
        ("📦", "Suppliers",    filtered["Supplier"].nunique(),                                      "in portfolio"),
        ("⭐", "Avg Score",    f"{filtered['Score'].mean():.1f}",                                   "overall rating"),
        ("⚠️", "Anomalies",   int(filtered["Anomalien"].sum()),                                    "detected"),
        ("📂", "Top Material", filtered["Material"].mode().iloc[0] if not filtered.empty else "-",  "category"),
        ("🏆", "Top Supplier", filtered.iloc[0]["Supplier"]        if not filtered.empty else "-",  "highest score"),
    ],
):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size:1.4rem;margin-bottom:6px;">{icon}</div>
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("")

# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Overview", "🎯 Rankings & Insights", "📈 Analytics", "👤 Supplier Profile", "📋 Details"]
)

# ── TAB 1: OVERVIEW ──────────────────────────────────────
with tab1:
    c_left, c_mid, c_right = st.columns([1.2, 1.3, 0.95])

    with c_left:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🏆 Top Suppliers</div>', unsafe_allow_html=True)
        for rank, (_, row) in enumerate(filtered.head(6).iterrows(), 1):
            lvl = "success" if row["Score"] >= 90 else "warning" if row["Score"] >= 75 else "danger"
            ano_badge = (
                f'<span class="badge badge-danger">⚠️ {int(row["Anomalien"])} Anomalies</span>'
                if row["Anomalien"] > 0 else
                '<span class="badge badge-success">✓ No Issues</span>'
            )
            st.markdown(f"""
            <div class="supplier-item">
                <div style="display:flex;justify-content:space-between;align-items:start;">
                    <div>
                        <div class="supplier-name">#{rank} {row['Supplier']}</div>
                        <div class="supplier-meta">{row['Material']} · {row['Country']}</div>
                    </div>
                    <span class="badge badge-{lvl}" style="font-size:0.88rem;font-weight:700;">{row['Score']}</span>
                </div>
                <div style="margin-top:8px;">{ano_badge}</div>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c_mid:
        # ── Pure-HTML supplier detail card — no st.metric() inside raw HTML divs ──
        d_lt  = sel['Liefertreue']  - 95
        d_q   = sel['Qualitätsrate'] - 97
        d_ld  = sel['Lieferzeit']   - 10
        d_rc  = sel['Reklamationsquote'] - 1.0

        def delta_span(diff, invert=False):
            good = (diff <= 0) if invert else (diff >= 0)
            cls  = "delta-pos" if good else "delta-neg"
            sign = "+" if diff > 0 else ""
            return f'<span class="kpi-cell-delta {cls}">{sign}{diff:.1f}</span>'

        st.markdown(f"""
        <div class="premium-card">
            <div class="section-title">📍 {sel['Supplier']}</div>

            <div class="kpi-grid">
                <div class="kpi-cell">
                    <div class="kpi-cell-label">ID</div>
                    <div class="kpi-cell-value">{sel['Supplier_ID']}</div>
                </div>
                <div class="kpi-cell">
                    <div class="kpi-cell-label">Category</div>
                    <div class="kpi-cell-value">{sel['Material']}</div>
                </div>
                <div class="kpi-cell">
                    <div class="kpi-cell-label">Country</div>
                    <div class="kpi-cell-value">{sel['Country']}</div>
                </div>
                <div class="kpi-cell">
                    <div class="kpi-cell-label">Status</div>
                    <div class="kpi-cell-value">{sel['Status']}</div>
                </div>
            </div>

            <div class="kpi-grid">
                <div class="kpi-cell">
                    <div class="kpi-cell-label">On-Time Delivery</div>
                    <div class="kpi-cell-value">{sel['Liefertreue']:.1f}%</div>
                    {delta_span(d_lt)}
                </div>
                <div class="kpi-cell">
                    <div class="kpi-cell-label">Quality Score</div>
                    <div class="kpi-cell-value">{sel['Qualitätsrate']:.1f}%</div>
                    {delta_span(d_q)}
                </div>
                <div class="kpi-cell">
                    <div class="kpi-cell-label">Lead Time</div>
                    <div class="kpi-cell-value">{sel['Lieferzeit']:.1f} d</div>
                    {delta_span(d_ld, invert=True)}
                </div>
                <div class="kpi-cell">
                    <div class="kpi-cell-label">Complaint Rate</div>
                    <div class="kpi-cell-value">{sel['Reklamationsquote']:.2f}%</div>
                    {delta_span(d_rc, invert=True)}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c_right:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🎯 Overall Score</div>', unsafe_allow_html=True)
        st.plotly_chart(donut_chart(sel["Score"], score_color(sel["Score"])), use_container_width=True, config={"displayModeBar": False})
        risk_cls = "badge-success" if sel["Risk"] == "Low" else "badge-warning" if sel["Risk"] == "Medium" else "badge-danger"
        st.markdown(f'<span class="badge {risk_cls}" style="font-size:0.88rem;">Risk: {sel["Risk"]}</span>', unsafe_allow_html=True)
        st.write("")
        st.markdown(f"**Critical KPI:** {sel['Crit_KPI']}")
        st.markdown('</div>', unsafe_allow_html=True)

# ── TAB 2: RANKINGS & INSIGHTS ───────────────────────────
with tab2:
    c_rank, c_ins = st.columns([1.2, 0.95])

    with c_rank:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📊 Supplier Ranking</div>', unsafe_allow_html=True)
        rank_df = filtered[["Supplier","Material","Country","Score","Anomalien","Risk"]].sort_values("Score", ascending=False).copy()
        rank_df.insert(0, "Rank", range(1, len(rank_df)+1))
        st.dataframe(rank_df, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c_ins:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">💡 Key Insights</div>', unsafe_allow_html=True)
        for i, (_, row) in enumerate(filtered.head(3).iterrows(), 1):
            st.markdown(f"""
            <div class="insight-box">
                <b>Top {i}: {row['Supplier']}</b><br>
                Score: {row['Score']} · {row['Material']} · {row['Country']}<br>
                <span style="opacity:0.85;">Strengths: {row['Strengths']}</span>
            </div>""", unsafe_allow_html=True)
        for _, row in filtered.sort_values("Score").head(2).iterrows():
            st.markdown(f"""
            <div class="warning-box">
                <b>⚠️ Attention: {row['Supplier']}</b><br>
                Critical: {row['Crit_KPI']} · Score: {row['Score']}<br>
                <span style="opacity:0.85;">Action: Monitor performance closely.</span>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ── TAB 3: ANALYTICS ─────────────────────────────────────
with tab3:
    r1c1, r1c2 = st.columns(2)

    with r1c1:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        fig = px.bar(filtered.sort_values("Score", ascending=False), x="Supplier", y="Score",
                     color="Score", title="Supplier Ranking by Score", color_continuous_scale="Viridis")
        fig.update_traces(marker_line_width=0)
        fig.update_layout(**plotly_dark_layout(title_font_size=14))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        mat = filtered["Material"].value_counts().reset_index()
        mat.columns = ["Material","Count"]
        fig2 = px.pie(mat, names="Material", values="Count", hole=0.5,
                      title="Material Distribution", color_discrete_sequence=px.colors.qualitative.Set2)
        fig2.update_layout(**plotly_dark_layout(title_font_size=14))
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    with r1c2:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        fig3 = px.scatter(filtered, x="Liefertreue", y="Qualitätsrate", size="Score", color="Score",
                          hover_name="Supplier", title="Delivery Reliability vs Quality",
                          color_continuous_scale="Plasma")
        fig3.update_layout(**plotly_dark_layout(title_font_size=14))
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        ano_df = filtered.copy()
        ano_df["AnomalyStatus"] = np.where(ano_df["Anomalien"] > 0, "Has Anomalies", "Clean")
        ano_share = ano_df["AnomalyStatus"].value_counts().reset_index()
        ano_share.columns = ["Status","Count"]
        fig4 = px.pie(ano_share, names="Status", values="Count", hole=0.6,
                      title="Anomaly Distribution", color_discrete_sequence=["#ef4444","#22c55e"])
        fig4.update_layout(**plotly_dark_layout(title_font_size=14))
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        fig5 = px.bar(filtered.sort_values("Lieferzeit"), x="Supplier", y="Lieferzeit",
                      color="Lieferzeit", title="Lead Time Comparison", color_continuous_scale="Blues_r")
        fig5.update_traces(marker_line_width=0)
        fig5.update_layout(**plotly_dark_layout(title_font_size=14))
        st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    with r2c2:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        fig6 = px.bar(filtered.sort_values("Reklamationsquote", ascending=False),
                      x="Supplier", y="Reklamationsquote", color="Reklamationsquote",
                      title="Complaint Rate Comparison", color_continuous_scale="Reds_r")
        fig6.update_traces(marker_line_width=0)
        fig6.update_layout(**plotly_dark_layout(title_font_size=14))
        st.plotly_chart(fig6, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

# ── TAB 4: SUPPLIER PROFILE ──────────────────────────────
with tab4:
    cp1, cp2 = st.columns([1.1, 1.1])

    with cp1:
        st.markdown(f"""
        <div class="premium-card">
            <div class="section-title">👤 Supplier Profile</div>
            <div class="kpi-grid">
                <div class="kpi-cell">
                    <div class="kpi-cell-label">Supplier ID</div>
                    <div class="kpi-cell-value">{sel['Supplier_ID']}</div>
                </div>
                <div class="kpi-cell">
                    <div class="kpi-cell-label">Supplier Name</div>
                    <div class="kpi-cell-value">{sel['Supplier']}</div>
                </div>
                <div class="kpi-cell">
                    <div class="kpi-cell-label">Category</div>
                    <div class="kpi-cell-value">{sel['Material']}</div>
                </div>
                <div class="kpi-cell">
                    <div class="kpi-cell-label">Country</div>
                    <div class="kpi-cell-value">{sel['Country']}</div>
                </div>
                <div class="kpi-cell">
                    <div class="kpi-cell-label">Status</div>
                    <div class="kpi-cell-value">{sel['Status']}</div>
                </div>
                <div class="kpi-cell">
                    <div class="kpi-cell-label">Risk Level</div>
                    <div class="kpi-cell-value">{sel['Risk']}</div>
                </div>
            </div>
            <div style="margin-top:4px;font-size:0.88rem;color:#9ca3af;">
                Critical KPI: <span style="color:#f1f5f9;font-weight:600;">{sel['Crit_KPI']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if sel["Score"] >= 90:
            st.markdown(f'<div class="insight-box"><b>✅ Recommendation</b><br>{sel["Supplier"]} is a preferred supplier. Strengths: {sel["Strengths"]}</div>', unsafe_allow_html=True)
        elif sel["Score"] >= 75:
            st.markdown(f'<div class="warning-box"><b>⚠️ Recommendation</b><br>Monitor <b>{sel["Crit_KPI"]}</b> closely. Supplier is usable but requires oversight.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="critical-box"><b>🔴 Critical</b><br>Focus on <b>{sel["Crit_KPI"]}</b>. Consider alternative suppliers.</div>', unsafe_allow_html=True)

    with cp2:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📊 KPI Profile</div>', unsafe_allow_html=True)
        fig_p = go.Figure(go.Bar(
            x=["Delivery","Quality","Complaints","Price Var.","Lead Time"],
            y=[sel["Liefertreue"], sel["Qualitätsrate"], sel["Reklamationsquote"],
               abs(sel["Preisabweichung"]), sel["Lieferzeit"]],
            marker=dict(color=["#22c55e","#3b82f6","#f59e0b","#ef4444","#8b5cf6"], line=dict(width=0)),
            hovertemplate="<b>%{x}</b><br>Value: %{y:.1f}<extra></extra>",
        ))
        fig_p.update_layout(title="KPI Performance Profile", showlegend=False,
                            **plotly_dark_layout(title_font_size=14))
        st.plotly_chart(fig_p, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

# ── TAB 5: DETAILS ───────────────────────────────────────
with tab5:
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📋 Complete Data View</div>', unsafe_allow_html=True)
    detail_cols = ["Supplier","Supplier_ID","Material","Country","Liefertreue","Lieferzeit",
                   "Qualitätsrate","Reklamationsquote","Preisabweichung","Score","Anomalien","Status","Risk"]
    st.dataframe(agg[[c for c in detail_cols if c in agg.columns]].round(2), use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.markdown("""
<div style='text-align:center;color:#6b7280;font-size:0.85rem;margin-top:2rem;'>
    Supplier Evaluation Dashboard · Enterprise Edition<br>
    Built with Streamlit | Powered by Advanced Analytics
</div>""", unsafe_allow_html=True)
