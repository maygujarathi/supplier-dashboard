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

# =========================================================
# STYLING
# =========================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700;800;900&display=swap');
    * { font-family: 'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }

    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #10111f 50%, #0d0f22 100%);
        color: #e5e7eb;
    }
    .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; max-width: 1600px; }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10,14,39,0.95) 0%, rgba(13,15,34,0.95) 100%);
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    section[data-testid="stSidebar"] * { color: #e5e7eb !important; }

    /* ── HEADER ── */
    .page-header {
        padding: 0 0 0.5rem 0;
    }
    .main-header {
        font-size: clamp(1.6rem, 2.5vw, 2.8rem);
        font-weight: 900;
        background: linear-gradient(135deg, #60a5fa, #3b82f6, #2563eb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.03em;
        line-height: 1.15;
        margin: 0;
    }
    .main-subtitle {
        font-size: 0.82rem;
        color: #6b7280;
        font-weight: 500;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-top: 4px;
    }

    /* ── CARD WRAPPER ── */
    /* Cards are pure CSS — no split open/close divs */
    .card {
        background: linear-gradient(135deg, rgba(30,41,59,0.6), rgba(25,35,50,0.4));
        border: 1px solid rgba(148,163,184,0.12);
        border-radius: 16px;
        padding: 22px 22px 18px 22px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05);
        margin-bottom: 16px;
    }

    /* ── METRIC CARDS (top row) ── */
    .metric-card {
        background: linear-gradient(135deg, rgba(30,41,59,0.5), rgba(25,35,50,0.3));
        border: 1px solid rgba(96,165,250,0.15);
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 6px 24px rgba(0,0,0,0.25);
        min-height: 130px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .metric-icon  { font-size: 1.4rem; margin-bottom: 6px; }
    .metric-label { font-size: 0.78rem; color: #9ca3af; font-weight: 600;
                    text-transform: uppercase; letter-spacing: 0.08em; }
    .metric-value { font-size: 1.9rem; font-weight: 800;
                    background: linear-gradient(135deg, #60a5fa, #3b82f6);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                    background-clip: text; line-height: 1.2; }
    .metric-sub   { font-size: 0.78rem; color: #6b7280; font-weight: 500; margin-top: 6px; }

    /* ── SECTION TITLE ── */
    .section-title {
        font-size: 1.1rem; font-weight: 800; color: #f1f5f9;
        margin: 0 0 16px 0; letter-spacing: -0.01em;
    }

    /* ── SUPPLIER LIST ITEMS ── */
    .supplier-item {
        background: linear-gradient(135deg, rgba(30,41,59,0.4), rgba(25,35,50,0.2));
        border: 1px solid rgba(96,165,250,0.1);
        border-radius: 12px; padding: 14px; margin-bottom: 10px;
    }
    .supplier-name { font-weight: 700; color: #f1f5f9; font-size: 1rem; margin-bottom: 4px; }
    .supplier-meta { color: #9ca3af; font-size: 0.82rem; font-weight: 500; }

    /* ── BADGES ── */
    .badge { display:inline-block; padding:5px 11px; border-radius:20px;
             font-size:0.78rem; font-weight:600; margin-right:5px; margin-bottom:3px; }
    .badge-success { background:rgba(34,197,94,0.15); color:#86efac; border:1px solid rgba(34,197,94,0.3); }
    .badge-warning { background:rgba(251,146,60,0.15); color:#fed7aa; border:1px solid rgba(251,146,60,0.3); }
    .badge-danger  { background:rgba(239,68,68,0.15);  color:#fca5a5; border:1px solid rgba(239,68,68,0.3); }

    /* ── INSIGHT / WARNING / CRITICAL BOXES ── */
    .insight-box  { background:linear-gradient(135deg,rgba(34,197,94,0.08),rgba(34,197,94,0.04));
                    border:1px solid rgba(34,197,94,0.2); border-radius:12px; padding:14px;
                    color:#d1fae5; margin-bottom:10px; }
    .warning-box  { background:linear-gradient(135deg,rgba(251,146,60,0.08),rgba(251,146,60,0.04));
                    border:1px solid rgba(251,146,60,0.2); border-radius:12px; padding:14px;
                    color:#ffedd5; margin-bottom:10px; }
    .critical-box { background:linear-gradient(135deg,rgba(239,68,68,0.08),rgba(239,68,68,0.04));
                    border:1px solid rgba(239,68,68,0.2); border-radius:12px; padding:14px;
                    color:#fecaca; margin-bottom:10px; }

    /* ── TABS ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px; background: transparent;
        border-bottom: 1px solid rgba(148,163,184,0.1);
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px; border-radius: 8px 8px 0 0; background: transparent;
        color: #9ca3af; font-weight: 600; padding: 0 16px; font-size: 0.9rem; border: none;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg,rgba(96,165,250,0.15),rgba(96,165,250,0.08)) !important;
        color: #60a5fa !important; border-bottom: 2px solid #3b82f6 !important;
    }

    /* ── STREAMLIT METRIC WIDGET ── */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg,rgba(30,41,59,0.5),rgba(25,35,50,0.3));
        border: 1px solid rgba(96,165,250,0.15);
        padding: 14px; border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.2);
    }
    div[data-testid="stMetric"] label { color:#9ca3af !important; font-weight:600 !important; }
    div[data-testid="stMetric"] > div:nth-child(2) {
        color:#60a5fa !important; font-size:1.8rem !important; font-weight:800 !important;
    }

    /* ── BUTTON ── */
    .stButton > button {
        border-radius:10px; border:1px solid rgba(96,165,250,0.3);
        background:linear-gradient(135deg,#3b82f6,#2563eb); color:white;
        font-weight:600; padding:10px 20px;
        box-shadow:0 4px 12px rgba(59,130,246,0.3);
    }

    ::-webkit-scrollbar { width:8px; height:8px; }
    ::-webkit-scrollbar-track { background:rgba(30,41,59,0.3); }
    ::-webkit-scrollbar-thumb { background:rgba(96,165,250,0.3); border-radius:4px; }

    @keyframes fadeInUp { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }
    .card, .metric-card { animation: fadeInUp 0.5s ease-out; }
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
    if pd.isna(value): return 0
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
    if pd.notna(row.get("Liefertreue"))      and row["Liefertreue"]      < 95:  s -= (95  - row["Liefertreue"])       * 1.8
    if pd.notna(row.get("Lieferzeit"))        and row["Lieferzeit"]        > 10:  s -= (row["Lieferzeit"]   - 10)      * 2.0
    if pd.notna(row.get("Qualitätsrate"))     and row["Qualitätsrate"]     < 97:  s -= (97  - row["Qualitätsrate"])    * 2.5
    if pd.notna(row.get("Reklamationsquote")) and row["Reklamationsquote"] > 1.0: s -= (row["Reklamationsquote"] - 1.0)* 8
    if pd.notna(row.get("Preisabweichung"))   and abs(row["Preisabweichung"]) > 1.0: s -= (abs(row["Preisabweichung"])-1.0)*3.5
    if pd.notna(row.get("Anomalien")):        s -= row["Anomalien"] * 0.5
    return max(round(s, 1), 0)

def risk_level(score):
    return "Low" if score >= 90 else "Medium" if score >= 75 else "High"

def status_label(score):
    return "Excellent" if score >= 90 else "Monitor" if score >= 75 else "Critical"

def critical_kpi(row):
    problems = {
        "Delivery":   (95  - row["Liefertreue"])         if pd.notna(row.get("Liefertreue"))      and row["Liefertreue"]      < 95  else 0,
        "Lead Time":  (row["Lieferzeit"]  - 10)           if pd.notna(row.get("Lieferzeit"))        and row["Lieferzeit"]        > 10  else 0,
        "Quality":    (97  - row["Qualitätsrate"])         if pd.notna(row.get("Qualitätsrate"))     and row["Qualitätsrate"]     < 97  else 0,
        "Complaints": (row["Reklamationsquote"] - 1.0)    if pd.notna(row.get("Reklamationsquote")) and row["Reklamationsquote"] > 1.0 else 0,
        "Price Dev.": (abs(row["Preisabweichung"]) - 1.0) if pd.notna(row.get("Preisabweichung"))   and abs(row["Preisabweichung"]) > 1.0 else 0,
    }
    m = max(problems, key=problems.get)
    return m if problems[m] > 0 else "None"

def supplier_strengths(row):
    r = []
    if row["Liefertreue"]       >= 95:  r.append("strong delivery")
    if row["Qualitätsrate"]     >= 97:  r.append("excellent quality")
    if row["Lieferzeit"]        <= 10:  r.append("fast lead time")
    if row["Reklamationsquote"] <= 1.0: r.append("low complaints")
    if abs(row["Preisabweichung"]) <= 1.0: r.append("stable pricing")
    return ", ".join(r[:3]) if r else "mixed profile"

def score_color(score):
    return "#22c55e" if score >= 90 else "#f59e0b" if score >= 75 else "#ef4444"

def donut_chart(value, color):
    fig = go.Figure(go.Pie(
        values=[value, max(0, 100 - value)], hole=0.72,
        marker_colors=[color, "rgba(148,163,184,0.1)"],
        textinfo="none", sort=False, hoverinfo="skip",
    ))
    fig.update_layout(
        showlegend=False,
        margin=dict(t=0, l=0, r=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        annotations=[dict(
            text=f"<b style='font-size:30px;color:{color}'>{value:.0f}</b><br>"
                 "<span style='font-size:11px;color:#9ca3af'>out of 100</span>",
            x=0.5, y=0.5, showarrow=False, font_size=18,
        )],
    )
    return fig

def plotly_layout(**kw):
    base = dict(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9ca3af"), margin=dict(t=40,b=40,l=40,r=40),
    )
    base.update(kw)
    return base

# =========================================================
# PAGE HEADER  — single self-contained HTML block, no columns
# =========================================================
now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
st.markdown(f"""
<div class="page-header" style="display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:8px;">
    <div>
        <div class="main-header">Supplier Evaluation Dashboard</div>
        <div class="main-subtitle">🔍 Performance Analytics · Risk Assessment · KPI Monitoring</div>
    </div>
    <div style="color:#6b7280;font-size:0.85rem;white-space:nowrap;">Last updated: {now_str}</div>
</div>
<hr style="border:none;border-top:1px solid rgba(148,163,184,0.15);margin:12px 0 20px 0;">
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR — UPLOAD + COLUMN MAPPING
# =========================================================
with st.sidebar:
    st.markdown('<p style="font-size:1.1rem;font-weight:800;color:#f1f5f9;margin:1rem 0 0.5rem 0;">📊 Data Source</p>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx","xls"])

if uploaded_file is None:
    st.info("👈 Please upload an Excel file in the sidebar to get started.")
    st.stop()

raw_df = clean_columns(pd.read_excel(uploaded_file))
all_cols = ["-- Not available --"] + list(raw_df.columns)

def idx(name):
    return all_cols.index(name) if name in all_cols else 0

with st.sidebar:
    st.markdown('<p style="font-size:1.1rem;font-weight:800;color:#f1f5f9;margin:1rem 0 0.5rem 0;">🔗 Column Mapping</p>', unsafe_allow_html=True)
    supplier_col    = st.selectbox("Supplier",            all_cols, index=idx("Supplier_Name"))
    country_col     = st.selectbox("Country",             all_cols, index=idx("Country"))
    material_col    = st.selectbox("Material / Category", all_cols, index=idx("Category"))
    delivery_col    = st.selectbox("On-Time Delivery %",  all_cols, index=idx("Delivery_Performance_%"))
    leadtime_col    = st.selectbox("Lead Time (Days)",    all_cols, index=idx("Lead_Time_Days"))
    quality_col     = st.selectbox("Quality Score %",     all_cols, index=idx("Quality_Score_%"))
    complaint_col   = st.selectbox("Complaint Rate %",    all_cols, index=idx("Complaint_Rate_%"))
    price_col       = st.selectbox("Price Deviation %",   all_cols, index=idx("Price_Deviation_%"))
    score_col       = st.selectbox("Score (optional)",    all_cols, index=idx("Overall_Score"))
    status_col      = st.selectbox("Status (optional)",   all_cols, index=idx("Status"))
    anomaly_col     = st.selectbox("Anomaly Flag (opt.)", all_cols, index=idx("Anomaly_Flag"))
    supplier_id_col = st.selectbox("Supplier ID (opt.)",  all_cols, index=idx("Supplier_ID"))

# =========================================================
# BUILD DATAFRAME
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
df["Anomalien"]  = df["Anomaly_Flag"].apply(normalize_anomaly_flag) if "Anomaly_Flag" in df.columns else df.apply(calculate_anomalies, axis=1)
if "Score"  not in df.columns: df["Score"]  = df.apply(calculate_score,  axis=1)
if "Status" not in df.columns: df["Status"] = df["Score"].apply(status_label)
df["Risk"]       = df["Score"].apply(risk_level)
df["Crit_KPI"]   = df.apply(critical_kpi,         axis=1)
df["Strengths"]  = df.apply(supplier_strengths,    axis=1)

agg = df.groupby("Supplier", as_index=False).agg({
    "Supplier_ID":"first","Material":"first","Country":"first",
    "Liefertreue":"mean","Lieferzeit":"mean","Qualitätsrate":"mean",
    "Reklamationsquote":"mean","Preisabweichung":"mean",
    "Score":"mean","Anomalien":"sum",
    "Status":"first","Risk":"first","Crit_KPI":"first","Strengths":"first",
}).sort_values("Score", ascending=False).reset_index(drop=True)
agg["Score"] = agg["Score"].round(1)

# =========================================================
# SIDEBAR — LIVE FILTERS
# =========================================================
with st.sidebar:
    st.markdown('<p style="font-size:1.1rem;font-weight:800;color:#f1f5f9;margin:1.5rem 0 0.5rem 0;">🎯 Filters</p>', unsafe_allow_html=True)
    materials = ["All"] + sorted(agg["Material"].astype(str).dropna().unique().tolist())

    if "sel_mat" not in st.session_state:
        st.session_state["sel_mat"] = "All"

    sel_mat = st.selectbox(
        "Material Category", materials,
        index=materials.index(st.session_state["sel_mat"]) if st.session_state["sel_mat"] in materials else 0,
        key="sel_mat",
    )
    filtered     = agg if sel_mat == "All" else agg[agg["Material"] == sel_mat].copy()
    supplier_list = filtered["Supplier"].tolist()

    if not supplier_list:
        st.warning("No suppliers found for this material.")
        st.stop()

    if "sel_sup" not in st.session_state or st.session_state["sel_sup"] not in supplier_list:
        st.session_state["sel_sup"] = supplier_list[0]

    sel_sup = st.selectbox(
        "Select Supplier", supplier_list,
        index=supplier_list.index(st.session_state["sel_sup"]) if st.session_state["sel_sup"] in supplier_list else 0,
        key="sel_sup",
    )

sel = filtered[filtered["Supplier"] == sel_sup].iloc[0]

# =========================================================
# TOP KPI CARDS
# =========================================================
kpi_data = [
    ("📦", "Suppliers",    str(filtered["Supplier"].nunique()),                               "in portfolio"),
    ("⭐", "Avg Score",    f"{filtered['Score'].mean():.1f}",                                 "overall rating"),
    ("⚠️", "Anomalies",   str(int(filtered["Anomalien"].sum())),                             "detected"),
    ("📂", "Top Material", str(filtered["Material"].mode().iloc[0]) if not filtered.empty else "-", "category"),
    ("🏆", "Top Supplier", str(filtered.iloc[0]["Supplier"]) if not filtered.empty else "-", "highest score"),
]
for col, (icon, label, value, sub) in zip(st.columns(5), kpi_data):
    with col:
        st.markdown(f"""
<div class="metric-card">
    <div class="metric-icon">{icon}</div>
    <div class="metric-label">{label}</div>
    <div class="metric-value">{value}</div>
    <div class="metric-sub">{sub}</div>
</div>""", unsafe_allow_html=True)

st.markdown("<div style='margin-bottom:12px'></div>", unsafe_allow_html=True)

# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Overview", "🎯 Rankings & Insights", "📈 Analytics", "👤 Supplier Profile", "📋 Details"]
)

# ─────────────────────────────────────────────────────────
# TAB 1 — OVERVIEW
# Each "card" is a single complete st.markdown HTML block.
# st.container() is used only where Streamlit widgets (metrics,
# charts) must sit inside a visually-styled region — using
# st.container with a border=False approach and CSS class applied
# via a wrapper div before the container.
# ─────────────────────────────────────────────────────────
with tab1:
    c_left, c_mid, c_right = st.columns([1.2, 1.3, 0.95])

    # ── LEFT: Top Suppliers list (pure HTML — no widgets inside) ──
    with c_left:
        items_html = ""
        for rank, (_, row) in enumerate(filtered.head(6).iterrows(), 1):
            lvl = "success" if row["Score"] >= 90 else "warning" if row["Score"] >= 75 else "danger"
            ano = (f'<span class="badge badge-danger">⚠️ {int(row["Anomalien"])} Anomalies</span>'
                   if row["Anomalien"] > 0 else '<span class="badge badge-success">✓ No Issues</span>')
            items_html += f"""
<div class="supplier-item">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div>
            <div class="supplier-name">#{rank} {row['Supplier']}</div>
            <div class="supplier-meta">{row['Material']} · {row['Country']}</div>
        </div>
        <span class="badge badge-{lvl}" style="font-size:0.88rem;font-weight:700;">{row['Score']}</span>
    </div>
    <div style="margin-top:8px;">{ano}</div>
</div>"""
        st.markdown(f"""
<div class="card">
    <div class="section-title">🏆 Top Suppliers</div>
    {items_html}
</div>""", unsafe_allow_html=True)

    # ── MIDDLE: Selected supplier KPIs (uses st.metric widgets) ──
    with c_mid:
        st.markdown(f"""
<div class="card" style="margin-bottom:0;">
    <div class="section-title">📍 {sel["Supplier"]}</div>
</div>""", unsafe_allow_html=True)
        # Metrics live outside the card HTML but inside the column
        ca, cb = st.columns(2)
        with ca:
            st.metric("ID",       sel["Supplier_ID"])
            st.metric("Category", sel["Material"])
        with cb:
            st.metric("Country",  sel["Country"])
            st.metric("Status",   sel["Status"])
        st.write("")
        cc, cd = st.columns(2)
        ce, cf = st.columns(2)
        with cc: st.metric("On-Time Delivery", f"{sel['Liefertreue']:.1f}%",       f"{sel['Liefertreue']-95:.1f}%")
        with cd: st.metric("Quality Score",    f"{sel['Qualitätsrate']:.1f}%",     f"{sel['Qualitätsrate']-97:.1f}%")
        with ce: st.metric("Lead Time",        f"{sel['Lieferzeit']:.1f} d",       f"{sel['Lieferzeit']-10:.1f} d")
        with cf: st.metric("Complaint Rate",   f"{sel['Reklamationsquote']:.2f}%", f"{sel['Reklamationsquote']-1.0:.2f}%")

    # ── RIGHT: Score donut (uses plotly chart widget) ──
    with c_right:
        risk_cls = "badge-success" if sel["Risk"] == "Low" else "badge-warning" if sel["Risk"] == "Medium" else "badge-danger"
        st.markdown(f"""
<div class="card" style="margin-bottom:0;">
    <div class="section-title">🎯 Overall Score</div>
    <span class="badge {risk_cls}">Risk: {sel['Risk']}</span>
    &nbsp;<span style="color:#9ca3af;font-size:0.85rem;">Critical KPI: <b style="color:#f1f5f9">{sel['Crit_KPI']}</b></span>
</div>""", unsafe_allow_html=True)
        st.plotly_chart(donut_chart(sel["Score"], score_color(sel["Score"])),
                        use_container_width=True, config={"displayModeBar": False})

# ─────────────────────────────────────────────────────────
# TAB 2 — RANKINGS & INSIGHTS
# ─────────────────────────────────────────────────────────
with tab2:
    c_rank, c_ins = st.columns([1.2, 0.95])

    with c_rank:
        st.markdown('<div class="card"><div class="section-title">📊 Supplier Ranking</div></div>',
                    unsafe_allow_html=True)
        rank_df = filtered[["Supplier","Material","Country","Score","Anomalien","Risk"]].sort_values("Score", ascending=False).copy()
        rank_df.insert(0, "Rank", range(1, len(rank_df)+1))
        st.dataframe(rank_df, use_container_width=True, hide_index=True)

    with c_ins:
        top_html = ""
        for i, (_, row) in enumerate(filtered.head(3).iterrows(), 1):
            top_html += f"""
<div class="insight-box">
    <b>Top {i}: {row['Supplier']}</b><br>
    <span style="font-size:0.88rem;">Score: {row['Score']} | {row['Material']} | {row['Country']}</span><br>
    <span style="font-size:0.82rem;opacity:0.9;">Strengths: {row['Strengths']}</span>
</div>"""
        warn_html = ""
        for _, row in filtered.sort_values("Score").head(2).iterrows():
            warn_html += f"""
<div class="warning-box">
    <b>⚠️ Attention: {row['Supplier']}</b><br>
    <span style="font-size:0.88rem;">Critical: {row['Crit_KPI']} | Score: {row['Score']}</span><br>
    <span style="font-size:0.82rem;opacity:0.9;">Action: Monitor performance closely.</span>
</div>"""
        st.markdown(f"""
<div class="card">
    <div class="section-title">💡 Key Insights</div>
    {top_html}{warn_html}
</div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
# TAB 3 — ANALYTICS  (charts — no split divs needed)
# ─────────────────────────────────────────────────────────
with tab3:
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.markdown('<div class="card"><div class="section-title">📊 Supplier Ranking by Score</div></div>', unsafe_allow_html=True)
        fig = px.bar(filtered.sort_values("Score", ascending=False), x="Supplier", y="Score",
                     color="Score", color_continuous_scale="Viridis")
        fig.update_traces(marker_line_width=0)
        fig.update_layout(**plotly_layout())
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.markdown('<div class="card"><div class="section-title">📦 Material Distribution</div></div>', unsafe_allow_html=True)
        mat = filtered["Material"].value_counts().reset_index()
        mat.columns = ["Material","Count"]
        fig2 = px.pie(mat, names="Material", values="Count", hole=0.5,
                      color_discrete_sequence=px.colors.qualitative.Set2)
        fig2.update_layout(**plotly_layout())
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    with r1c2:
        st.markdown('<div class="card"><div class="section-title">🎯 Delivery Reliability vs Quality</div></div>', unsafe_allow_html=True)
        fig3 = px.scatter(filtered, x="Liefertreue", y="Qualitätsrate", size="Score", color="Score",
                          hover_name="Supplier", color_continuous_scale="Plasma")
        fig3.update_layout(**plotly_layout())
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

        st.markdown('<div class="card"><div class="section-title">⚠️ Anomaly Distribution</div></div>', unsafe_allow_html=True)
        ano_df = filtered.copy()
        ano_df["AnomalyStatus"] = np.where(ano_df["Anomalien"] > 0, "Has Anomalies", "Clean")
        ano_share = ano_df["AnomalyStatus"].value_counts().reset_index()
        ano_share.columns = ["Status","Count"]
        fig4 = px.pie(ano_share, names="Status", values="Count", hole=0.6,
                      color_discrete_sequence=["#ef4444","#22c55e"])
        fig4.update_layout(**plotly_layout())
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.markdown('<div class="card"><div class="section-title">⏱ Lead Time Comparison</div></div>', unsafe_allow_html=True)
        fig5 = px.bar(filtered.sort_values("Lieferzeit"), x="Supplier", y="Lieferzeit",
                      color="Lieferzeit", color_continuous_scale="Blues_r")
        fig5.update_traces(marker_line_width=0)
        fig5.update_layout(**plotly_layout())
        st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar": False})

    with r2c2:
        st.markdown('<div class="card"><div class="section-title">📋 Complaint Rate Comparison</div></div>', unsafe_allow_html=True)
        fig6 = px.bar(filtered.sort_values("Reklamationsquote", ascending=False),
                      x="Supplier", y="Reklamationsquote",
                      color="Reklamationsquote", color_continuous_scale="Reds_r")
        fig6.update_traces(marker_line_width=0)
        fig6.update_layout(**plotly_layout())
        st.plotly_chart(fig6, use_container_width=True, config={"displayModeBar": False})

# ─────────────────────────────────────────────────────────
# TAB 4 — SUPPLIER PROFILE
# ─────────────────────────────────────────────────────────
with tab4:
    cp1, cp2 = st.columns([1.1, 1.1])
    with cp1:
        if sel["Score"] >= 90:
            rec_html = f'<div class="insight-box"><b>✅ Recommendation</b><br>{sel["Supplier"]} is a preferred supplier. Strengths: {sel["Strengths"]}</div>'
        elif sel["Score"] >= 75:
            rec_html = f'<div class="warning-box"><b>⚠️ Recommendation</b><br>Monitor <b>{sel["Crit_KPI"]}</b> closely. Usable but requires oversight.</div>'
        else:
            rec_html = f'<div class="critical-box"><b>🔴 Critical</b><br>Focus on <b>{sel["Crit_KPI"]}</b>. Consider alternative suppliers.</div>'

        st.markdown(f"""
<div class="card">
    <div class="section-title">👤 Supplier Profile</div>
    <table style="width:100%;border-collapse:collapse;font-size:0.92rem;">
        <tr><td style="color:#9ca3af;padding:6px 0;width:40%">Supplier ID</td><td style="color:#f1f5f9;font-weight:600">{sel['Supplier_ID']}</td></tr>
        <tr><td style="color:#9ca3af;padding:6px 0">Name</td><td style="color:#f1f5f9;font-weight:600">{sel['Supplier']}</td></tr>
        <tr><td style="color:#9ca3af;padding:6px 0">Category</td><td style="color:#f1f5f9;font-weight:600">{sel['Material']}</td></tr>
        <tr><td style="color:#9ca3af;padding:6px 0">Country</td><td style="color:#f1f5f9;font-weight:600">{sel['Country']}</td></tr>
        <tr><td style="color:#9ca3af;padding:6px 0">Status</td><td style="color:#f1f5f9;font-weight:600">{sel['Status']}</td></tr>
        <tr><td style="color:#9ca3af;padding:6px 0">Risk Level</td><td style="color:#f1f5f9;font-weight:600">{sel['Risk']}</td></tr>
        <tr><td style="color:#9ca3af;padding:6px 0">Critical KPI</td><td style="color:#f1f5f9;font-weight:600">{sel['Crit_KPI']}</td></tr>
    </table>
    <div style="margin-top:16px;">{rec_html}</div>
</div>""", unsafe_allow_html=True)

    with cp2:
        st.markdown('<div class="card"><div class="section-title">📊 KPI Performance Profile</div></div>', unsafe_allow_html=True)
        fig_p = go.Figure(go.Bar(
            x=["Delivery","Quality","Complaints","Price Var.","Lead Time"],
            y=[sel["Liefertreue"], sel["Qualitätsrate"], sel["Reklamationsquote"],
               abs(sel["Preisabweichung"]), sel["Lieferzeit"]],
            marker=dict(color=["#22c55e","#3b82f6","#f59e0b","#ef4444","#8b5cf6"], line=dict(width=0)),
            hovertemplate="<b>%{x}</b><br>Value: %{y:.1f}<extra></extra>",
        ))
        fig_p.update_layout(showlegend=False, **plotly_layout())
        st.plotly_chart(fig_p, use_container_width=True, config={"displayModeBar": False})

# ─────────────────────────────────────────────────────────
# TAB 5 — DETAILS
# ─────────────────────────────────────────────────────────
with tab5:
    st.markdown('<div class="card"><div class="section-title">📋 Complete Data View</div></div>', unsafe_allow_html=True)
    detail_cols = ["Supplier","Supplier_ID","Material","Country","Liefertreue","Lieferzeit",
                   "Qualitätsrate","Reklamationsquote","Preisabweichung","Score","Anomalien","Status","Risk"]
    st.dataframe(agg[[c for c in detail_cols if c in agg.columns]].round(2), use_container_width=True, hide_index=True)

# =========================================================
# FOOTER
# =========================================================
st.markdown("""
<hr style="border:none;border-top:1px solid rgba(148,163,184,0.1);margin:2rem 0 1rem 0;">
<div style='text-align:center;color:#6b7280;font-size:0.82rem;'>
    Supplier Evaluation Dashboard · Enterprise Edition &nbsp;·&nbsp; Built with Streamlit
</div>""", unsafe_allow_html=True)
