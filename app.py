import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Lieferantenbewertung",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# STYLING
# =========================================================
st.markdown("""
<style>
    .stApp {
        background-color: #f4f7fb;
    }

    .block-container {
        max-width: 1500px;
        padding-top: 1.1rem;
        padding-bottom: 1rem;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div {
        color: white !important;
    }

    .page-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #111827;
        margin-bottom: 0.2rem;
        letter-spacing: -0.02em;
    }

    .page-subtitle {
        color: #6b7280;
        font-size: 1rem;
        margin-bottom: 1rem;
    }

    .main-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        box-shadow: 0 6px 20px rgba(15,23,42,0.05);
        padding: 18px 18px 16px 18px;
        color: #111827 !important;
    }

    .main-card * {
        color: #111827 !important;
    }

    .metric-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        box-shadow: 0 5px 18px rgba(15,23,42,0.05);
        padding: 16px 18px;
        min-height: 110px;
    }

    .metric-label {
        color: #6b7280;
        font-size: 0.9rem;
        margin-bottom: 8px;
        font-weight: 600;
    }

    .metric-value {
        color: #111827;
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.0;
    }

    .metric-sub {
        margin-top: 8px;
        color: #6b7280;
        font-size: 0.83rem;
    }

    .section-title {
        color: #111827;
        font-size: 1.2rem;
        font-weight: 800;
        margin-bottom: 12px;
    }

    .supplier-row {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 14px;
        box-shadow: 0 3px 14px rgba(15,23,42,0.04);
        margin-bottom: 10px;
    }

    .supplier-name {
        color: #111827;
        font-weight: 800;
        font-size: 1rem;
        margin-bottom: 4px;
    }

    .supplier-meta {
        color: #6b7280;
        font-size: 0.9rem;
        margin-bottom: 10px;
    }

    .pill {
        display: inline-block;
        border-radius: 999px;
        padding: 5px 10px;
        font-size: 0.82rem;
        font-weight: 700;
        margin-right: 6px;
        margin-bottom: 4px;
    }

    .pill-green {
        background: #dcfce7;
        color: #166534 !important;
    }

    .pill-amber {
        background: #fef3c7;
        color: #92400e !important;
    }

    .pill-red {
        background: #fee2e2;
        color: #991b1b !important;
    }

    .pill-blue {
        background: #dbeafe;
        color: #1d4ed8 !important;
    }

    .info-line {
        color: #111827;
        font-size: 1rem;
        margin-bottom: 8px;
        font-weight: 600;
    }

    .info-muted {
        color: #6b7280 !important;
        font-size: 0.92rem;
    }

    .status-box-good {
        background: #ecfdf5;
        border: 1px solid #a7f3d0;
        color: #065f46 !important;
        border-radius: 14px;
        padding: 12px 14px;
        font-weight: 600;
        margin-bottom: 10px;
    }

    .status-box-mid {
        background: #fffbeb;
        border: 1px solid #fde68a;
        color: #92400e !important;
        border-radius: 14px;
        padding: 12px 14px;
        font-weight: 600;
        margin-bottom: 10px;
    }

    .status-box-bad {
        background: #fef2f2;
        border: 1px solid #fecaca;
        color: #991b1b !important;
        border-radius: 14px;
        padding: 12px 14px;
        font-weight: 600;
        margin-bottom: 10px;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e5e7eb;
        padding: 14px 16px;
        border-radius: 16px;
        box-shadow: 0 4px 14px rgba(15,23,42,0.05);
    }

    div[data-testid="stMetricLabel"] {
        color: #6b7280 !important;
        font-weight: 700 !important;
    }

    div[data-testid="stMetricValue"] {
        color: #111827 !important;
        font-weight: 800 !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 46px;
        border-radius: 12px;
        background: #e9eef9;
        color: #1f2937;
        font-weight: 700;
        padding-left: 16px;
        padding-right: 16px;
    }

    .stTabs [aria-selected="true"] {
        background: white !important;
        color: #2563eb !important;
        border: 1px solid #dbeafe !important;
        box-shadow: 0 3px 10px rgba(37,99,235,0.12);
    }

    .stButton > button {
        border-radius: 12px;
        background: #2563eb;
        color: white;
        border: 1px solid #2563eb;
        font-weight: 700;
    }
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
    v = str(value).strip().lower()
    return 1 if v in {"yes", "ja", "y", "true", "1", "kritisch"} else 0

def calc_anomalies(row):
    count = 0
    if pd.notna(row.get("Liefertreue")) and row["Liefertreue"] < 95:
        count += 1
    if pd.notna(row.get("Lieferzeit")) and row["Lieferzeit"] > 10:
        count += 1
    if pd.notna(row.get("Qualitätsrate")) and row["Qualitätsrate"] < 97:
        count += 1
    if pd.notna(row.get("Reklamationsquote")) and row["Reklamationsquote"] > 1.0:
        count += 1
    if pd.notna(row.get("Preisabweichung")) and abs(row["Preisabweichung"]) > 1.0:
        count += 1
    return count

def calc_score(row):
    score = 100.0
    if pd.notna(row.get("Liefertreue")) and row["Liefertreue"] < 95:
        score -= (95 - row["Liefertreue"]) * 1.8
    if pd.notna(row.get("Lieferzeit")) and row["Lieferzeit"] > 10:
        score -= (row["Lieferzeit"] - 10) * 2.0
    if pd.notna(row.get("Qualitätsrate")) and row["Qualitätsrate"] < 97:
        score -= (97 - row["Qualitätsrate"]) * 2.5
    if pd.notna(row.get("Reklamationsquote")) and row["Reklamationsquote"] > 1.0:
        score -= (row["Reklamationsquote"] - 1.0) * 8.0
    if pd.notna(row.get("Preisabweichung")) and abs(row["Preisabweichung"]) > 1.0:
        score -= (abs(row["Preisabweichung"]) - 1.0) * 3.5
    if pd.notna(row.get("Anomalien")):
        score -= row["Anomalien"] * 0.5
    return max(round(score, 1), 0)

def risk_level(score):
    if score >= 90:
        return "Niedrig"
    elif score >= 75:
        return "Mittel"
    return "Hoch"

def status_text(score):
    if score >= 90:
        return "Sehr gut"
    elif score >= 75:
        return "Beobachten"
    return "Kritisch"

def critical_kpi(row):
    problems = {
        "Liefertreue": 95 - row["Liefertreue"] if pd.notna(row.get("Liefertreue")) and row["Liefertreue"] < 95 else 0,
        "Lieferzeit": row["Lieferzeit"] - 10 if pd.notna(row.get("Lieferzeit")) and row["Lieferzeit"] > 10 else 0,
        "Qualitätsrate": 97 - row["Qualitätsrate"] if pd.notna(row.get("Qualitätsrate")) and row["Qualitätsrate"] < 97 else 0,
        "Reklamationsquote": row["Reklamationsquote"] - 1.0 if pd.notna(row.get("Reklamationsquote")) and row["Reklamationsquote"] > 1.0 else 0,
        "Preisabweichung": abs(row["Preisabweichung"]) - 1.0 if pd.notna(row.get("Preisabweichung")) and abs(row["Preisabweichung"]) > 1.0 else 0,
    }
    m = max(problems, key=problems.get)
    return m if problems[m] > 0 else "Kein kritischer KPI"

def supplier_reason(row):
    reasons = []
    if row["Liefertreue"] >= 95:
        reasons.append("starke Liefertreue")
    if row["Qualitätsrate"] >= 97:
        reasons.append("hohe Qualitätsleistung")
    if row["Lieferzeit"] <= 10:
        reasons.append("kurze Lieferzeit")
    if row["Reklamationsquote"] <= 1.0:
        reasons.append("niedrige Reklamationsquote")
    if abs(row["Preisabweichung"]) <= 1.0:
        reasons.append("stabile Preisabweichung")
    return ", ".join(reasons[:3]) if reasons else "gemischtes Leistungsprofil"

def pill_status(score):
    if score >= 90:
        return "pill-green"
    elif score >= 75:
        return "pill-amber"
    return "pill-red"

def box_status(score):
    if score >= 90:
        return "status-box-good"
    elif score >= 75:
        return "status-box-mid"
    return "status-box-bad"

def donut_chart(value, color):
    fig = go.Figure(go.Pie(
        values=[value, max(0, 100 - value)],
        labels=["Score", ""],
        hole=0.78,
        marker_colors=[color, "#e5e7eb"],
        textinfo="none",
        sort=False
    ))
    fig.update_layout(
        showlegend=False,
        margin=dict(t=0, l=0, r=0, b=0),
        paper_bgcolor="white",
        annotations=[dict(
            text=f"<b>{value:.1f}</b><br><span style='font-size:12px;color:#6b7280'>von 100</span>",
            x=0.5, y=0.5, showarrow=False, font_size=28
        )]
    )
    return fig

def score_color(score):
    if score >= 90:
        return "#16a34a"
    elif score >= 75:
        return "#f59e0b"
    return "#ef4444"

# =========================================================
# HEADER
# =========================================================
st.markdown('<div class="page-title">Lieferantenbewertung</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">KPI-Monitoring · Anomalieerkennung · Procurement Performance Dashboard</div>', unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("## Datenquelle")
    uploaded_file = st.file_uploader("Excel-Datei hochladen", type=["xlsx", "xls"])

if uploaded_file is None:
    st.info("Bitte lade eine Excel-Datei in der Sidebar hoch.")
    st.stop()

raw_df = pd.read_excel(uploaded_file)
raw_df = clean_columns(raw_df)
all_cols = ["-- Nicht vorhanden --"] + list(raw_df.columns)

with st.sidebar:
    st.markdown("## Spaltenzuordnung")
    supplier_col = st.selectbox("Supplier", all_cols, index=all_cols.index("Supplier_Name") if "Supplier_Name" in all_cols else 0)
    country_col = st.selectbox("Country", all_cols, index=all_cols.index("Country") if "Country" in all_cols else 0)
    material_col = st.selectbox("Material", all_cols, index=all_cols.index("Category") if "Category" in all_cols else 0)
    delivery_col = st.selectbox("Liefertreue", all_cols, index=all_cols.index("Delivery_Performance_%") if "Delivery_Performance_%" in all_cols else 0)
    leadtime_col = st.selectbox("Lieferzeit", all_cols, index=all_cols.index("Lead_Time_Days") if "Lead_Time_Days" in all_cols else 0)
    quality_col = st.selectbox("Qualitätsrate", all_cols, index=all_cols.index("Quality_Score_%") if "Quality_Score_%" in all_cols else 0)
    complaint_col = st.selectbox("Reklamationsquote", all_cols, index=all_cols.index("Complaint_Rate_%") if "Complaint_Rate_%" in all_cols else 0)
    price_col = st.selectbox("Preisabweichung", all_cols, index=all_cols.index("Price_Deviation_%") if "Price_Deviation_%" in all_cols else 0)
    score_col = st.selectbox("Score (optional)", all_cols, index=all_cols.index("Overall_Score") if "Overall_Score" in all_cols else 0)
    status_col = st.selectbox("Status (optional)", all_cols, index=all_cols.index("Status") if "Status" in all_cols else 0)
    anomaly_col = st.selectbox("Anomaly Flag (optional)", all_cols, index=all_cols.index("Anomaly_Flag") if "Anomaly_Flag" in all_cols else 0)
    supplier_id_col = st.selectbox("Supplier ID (optional)", all_cols, index=all_cols.index("Supplier_ID") if "Supplier_ID" in all_cols else 0)
    load_data = st.button("Dashboard laden", use_container_width=True)

if not load_data:
    st.stop()

required = {
    "Supplier": supplier_col,
    "Country": country_col,
    "Material": material_col,
    "Liefertreue": delivery_col,
    "Lieferzeit": leadtime_col,
    "Qualitätsrate": quality_col,
    "Reklamationsquote": complaint_col,
    "Preisabweichung": price_col,
}

missing = [k for k, v in required.items() if v == "-- Nicht vorhanden --"]
if missing:
    st.error(f"Bitte ordne alle Pflichtfelder zu: {', '.join(missing)}")
    st.stop()

mapping = {
    supplier_col: "Supplier",
    country_col: "Country",
    material_col: "Material",
    delivery_col: "Liefertreue",
    leadtime_col: "Lieferzeit",
    quality_col: "Qualitätsrate",
    complaint_col: "Reklamationsquote",
    price_col: "Preisabweichung",
}

optional = {
    score_col: "Score",
    status_col: "Status",
    anomaly_col: "Anomaly_Flag",
    supplier_id_col: "Supplier_ID",
}

for src, tgt in optional.items():
    if src != "-- Nicht vorhanden --":
        mapping[src] = tgt

df = raw_df.rename(columns=mapping).copy()

if "Supplier_ID" not in df.columns:
    df["Supplier_ID"] = [f"S{i+1:02d}" for i in range(len(df))]

df = to_numeric_safe(df, ["Liefertreue", "Lieferzeit", "Qualitätsrate", "Reklamationsquote", "Preisabweichung", "Score"])
df = df.dropna(subset=["Supplier", "Country", "Material", "Liefertreue", "Lieferzeit", "Qualitätsrate", "Reklamationsquote", "Preisabweichung"])

if "Anomaly_Flag" in df.columns:
    df["Anomalien"] = df["Anomaly_Flag"].apply(normalize_anomaly_flag)
else:
    df["Anomalien"] = df.apply(calc_anomalies, axis=1)

if "Score" not in df.columns:
    df["Score"] = df.apply(calc_score, axis=1)

if "Status" not in df.columns:
    df["Status"] = df["Score"].apply(status_text)

df["Risikostufe"] = df["Score"].apply(risk_level)
df["Kritischer KPI"] = df.apply(critical_kpi, axis=1)
df["Begründung"] = df.apply(supplier_reason, axis=1)

agg = df.groupby("Supplier", as_index=False).agg({
    "Supplier_ID": "first",
    "Material": "first",
    "Country": "first",
    "Liefertreue": "mean",
    "Lieferzeit": "mean",
    "Qualitätsrate": "mean",
    "Reklamationsquote": "mean",
    "Preisabweichung": "mean",
    "Score": "mean",
    "Anomalien": "sum",
    "Status": "first",
    "Risikostufe": "first",
    "Kritischer KPI": "first",
    "Begründung": "first",
})
agg["Score"] = agg["Score"].round(1)
agg = agg.sort_values("Score", ascending=False).reset_index(drop=True)

# =========================================================
# FILTERS
# =========================================================
with st.sidebar:
    st.markdown("## Filter")
    materials = ["Alle"] + sorted(agg["Material"].dropna().astype(str).unique().tolist())
    selected_material = st.selectbox("Material filtern", materials)

filtered = agg.copy()
if selected_material != "Alle":
    filtered = filtered[filtered["Material"] == selected_material]

with st.sidebar:
    selected_supplier = st.selectbox("Lieferant auswählen", filtered["Supplier"].tolist())

selected = filtered[filtered["Supplier"] == selected_supplier].iloc[0]

# =========================================================
# TOP METRICS
# =========================================================
m1, m2, m3, m4, m5 = st.columns(5)
cards = [
    ("Lieferanten", filtered["Supplier"].nunique(), "im aktuellen Filter"),
    ("Ø Score", f"{filtered['Score'].mean():.1f}", "durchschnittliche Bewertung"),
    ("Anomalien", int(filtered["Anomalien"].sum()), "gesamt im Portfolio"),
    ("Top Material", filtered["Material"].mode().iloc[0] if not filtered.empty else "-", "häufigste Kategorie"),
    ("Bester Lieferant", filtered.iloc[0]["Supplier"] if not filtered.empty else "-", "höchster Score"),
]

for col, (label, value, sub) in zip([m1, m2, m3, m4, m5], cards):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

st.write("")

# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3, tab4 = st.tabs(["Übersicht", "Ranking & Insights", "Visual Analytics", "Lieferantendetails"])

with tab1:
    left, center, right = st.columns([1.15, 1.45, 1.0])

    with left:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Top Lieferanten</div>', unsafe_allow_html=True)

        for _, row in filtered.head(6).iterrows():
            pill_cls = pill_status(row["Score"])
            anomaly_cls = "pill-red" if row["Anomalien"] > 0 else "pill-green"
            st.markdown(f"""
            <div class="supplier-row">
                <div class="supplier-name">{row['Supplier']}</div>
                <div class="supplier-meta">{row['Material']} · {row['Country']}</div>
                <span class="pill {pill_cls}">Score {row['Score']}</span>
                <span class="pill {anomaly_cls}">{int(row['Anomalien'])} Anomalien</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with center:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="section-title">{selected["Supplier"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-line">Lieferanten-ID: <span class="info-muted">{selected["Supplier_ID"]}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-line">Kategorie: <span class="info-muted">{selected["Material"]}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-line">Land: <span class="info-muted">{selected["Country"]}</span></div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        c3, c4 = st.columns(2)
        c5, c6 = st.columns(2)

        c1.metric("Liefertreue", f"{selected['Liefertreue']:.1f}%")
        c2.metric("Qualitätsrate", f"{selected['Qualitätsrate']:.1f}%")
        c3.metric("Lieferzeit", f"{selected['Lieferzeit']:.1f} Tage")
        c4.metric("Reklamationsquote", f"{selected['Reklamationsquote']:.1f}%")
        c5.metric("Preisabweichung", f"{selected['Preisabweichung']:.1f}%")
        c6.metric("Anomalien", int(selected["Anomalien"]))

        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Gesamtscore</div>', unsafe_allow_html=True)
        st.plotly_chart(donut_chart(selected["Score"], score_color(selected["Score"])), use_container_width=True)

        box_cls = box_status(selected["Score"])
        st.markdown(f'<div class="{box_cls}">Risikostufe: {selected["Risikostufe"]}</div>', unsafe_allow_html=True)

        st.markdown(f'<div class="info-line">Status: <span class="info-muted">{selected["Status"]}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-line">Kritischer KPI: <span class="info-muted">{selected["Kritischer KPI"]}</span></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    a, b = st.columns([1.25, 1.0])

    with a:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Automatisches Ranking</div>', unsafe_allow_html=True)
        rank_df = filtered[["Supplier", "Material", "Country", "Score", "Anomalien", "Kritischer KPI"]].sort_values("Score", ascending=False)
        st.dataframe(rank_df, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with b:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Management Insights</div>', unsafe_allow_html=True)

        for i, (_, row) in enumerate(filtered.head(3).iterrows(), start=1):
            st.markdown(f"""
            <div class="status-box-good">
                Top {i}: {row['Supplier']} · Score {row['Score']}<br>
                Empfehlung: Lieferant überzeugt durch {row['Begründung']}.
            </div>
            """, unsafe_allow_html=True)

        for _, row in filtered.sort_values("Score").head(2).iterrows():
            st.markdown(f"""
            <div class="status-box-mid">
                Beobachten: {row['Supplier']} · Score {row['Score']}<br>
                Fokus auf KPI: {row['Kritischer KPI']}.
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    v1, v2 = st.columns(2)

    with v1:
        fig_rank = px.bar(
            filtered.sort_values("Score", ascending=False),
            x="Supplier",
            y="Score",
            color="Material",
            color_discrete_sequence=px.colors.qualitative.Set2,
            title="Lieferantenranking nach Score"
        )
        fig_rank.update_layout(plot_bgcolor="white", paper_bgcolor="white", legend_title_text="")
        st.plotly_chart(fig_rank, use_container_width=True)

        material_share = filtered["Material"].value_counts().reset_index()
        material_share.columns = ["Material", "Anzahl"]
        fig_pie = px.pie(
            material_share,
            names="Material",
            values="Anzahl",
            hole=0.55,
            title="Materialverteilung",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_pie.update_layout(paper_bgcolor="white")
        st.plotly_chart(fig_pie, use_container_width=True)

    with v2:
        fig_scatter = px.scatter(
            filtered,
            x="Liefertreue",
            y="Qualitätsrate",
            size="Score",
            color="Material",
            hover_name="Supplier",
            color_discrete_sequence=px.colors.qualitative.Bold,
            title="Liefertreue vs. Qualitätsrate"
        )
        fig_scatter.update_layout(plot_bgcolor="white", paper_bgcolor="white", legend_title_text="")
        st.plotly_chart(fig_scatter, use_container_width=True)

        ano = filtered.copy()
        ano["Anomaly Status"] = np.where(ano["Anomalien"] > 0, "Mit Anomalie", "Ohne Anomalie")
        ano_count = ano["Anomaly Status"].value_counts().reset_index()
        ano_count.columns = ["Status", "Anzahl"]

        fig_donut = px.pie(
            ano_count,
            names="Status",
            values="Anzahl",
            hole=0.6,
            title="Anomalieverteilung",
            color_discrete_sequence=["#ef4444", "#22c55e"]
        )
        fig_donut.update_layout(paper_bgcolor="white")
        st.plotly_chart(fig_donut, use_container_width=True)

with tab4:
    d1, d2 = st.columns([1.05, 1.15])

    with d1:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Lieferantenprofil</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-line">Lieferant: <span class="info-muted">{selected["Supplier"]}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-line">ID: <span class="info-muted">{selected["Supplier_ID"]}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-line">Kategorie: <span class="info-muted">{selected["Material"]}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-line">Land: <span class="info-muted">{selected["Country"]}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-line">Status: <span class="info-muted">{selected["Status"]}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-line">Risikostufe: <span class="info-muted">{selected["Risikostufe"]}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-line">Kritischer KPI: <span class="info-muted">{selected["Kritischer KPI"]}</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-line">Begründung: <span class="info-muted">{selected["Begründung"]}</span></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if selected["Score"] >= 90:
            st.markdown(f'<div class="status-box-good">Empfehlung: {selected["Supplier"]} kann als bevorzugter Lieferant genutzt werden. Stärken: {selected["Begründung"]}.</div>', unsafe_allow_html=True)
        elif selected["Score"] >= 75:
            st.markdown(f'<div class="status-box-mid">Empfehlung: Lieferant ist nutzbar, sollte aber bei {selected["Kritischer KPI"]} weiter beobachtet werden.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status-box-bad">Empfehlung: Lieferant kritisch. Eskalation oder Alternativlieferant prüfen.</div>', unsafe_allow_html=True)

    with d2:
        fig_profile = go.Figure()
        fig_profile.add_trace(go.Bar(
            x=["Liefertreue", "Qualitätsrate", "Reklamationsquote", "Preisabweichung", "Lieferzeit"],
            y=[
                selected["Liefertreue"],
                selected["Qualitätsrate"],
                selected["Reklamationsquote"],
                abs(selected["Preisabweichung"]),
                selected["Lieferzeit"]
            ],
            marker_color=["#2563eb", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6"]
        ))
        fig_profile.update_layout(
            title="KPI-Profil des Lieferanten",
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        st.plotly_chart(fig_profile, use_container_width=True)
