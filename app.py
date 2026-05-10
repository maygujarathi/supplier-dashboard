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
# PROFESSIONAL STYLING
# =========================================================
st.markdown("""
<style>
    .stApp {
        background-color: #f5f7fb;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1.2rem;
        max-width: 1500px;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    section[data-testid="stSidebar"] * {
        color: white !important;
    }

    .top-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #111827;
        margin-bottom: 0.1rem;
        letter-spacing: -0.02em;
    }

    .top-subtitle {
        color: #6b7280;
        font-size: 1rem;
        margin-bottom: 1rem;
    }

    .card {
        background: white;
        border-radius: 18px;
        padding: 18px 20px;
        box-shadow: 0 6px 24px rgba(15, 23, 42, 0.06);
        border: 1px solid #e5e7eb;
    }

    .metric-card {
        background: white;
        border-radius: 18px;
        padding: 16px 18px;
        box-shadow: 0 4px 18px rgba(15, 23, 42, 0.06);
        border: 1px solid #e5e7eb;
        min-height: 118px;
    }

    .metric-label {
        color: #6b7280;
        font-size: 0.9rem;
        margin-bottom: 8px;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 750;
        color: #111827;
        line-height: 1.05;
    }

    .metric-sub {
        margin-top: 8px;
        color: #6b7280;
        font-size: 0.85rem;
    }

    .supplier-item {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 14px 14px 12px 14px;
        margin-bottom: 10px;
        box-shadow: 0 3px 12px rgba(15,23,42,0.04);
    }

    .supplier-name {
        font-weight: 700;
        color: #111827;
        font-size: 1rem;
        margin-bottom: 2px;
    }

    .supplier-meta {
        color: #6b7280;
        font-size: 0.88rem;
    }

    .pill-good {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 999px;
        background: #dcfce7;
        color: #166534;
        font-size: 0.82rem;
        font-weight: 600;
    }

    .pill-mid {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 999px;
        background: #fef3c7;
        color: #92400e;
        font-size: 0.82rem;
        font-weight: 600;
    }

    .pill-bad {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 999px;
        background: #fee2e2;
        color: #991b1b;
        font-size: 0.82rem;
        font-weight: 600;
    }

    .section-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 12px;
    }

    .insight-box {
        background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%);
        border: 1px solid #dbeafe;
        border-radius: 16px;
        padding: 14px 16px;
        color: #1e3a8a;
        margin-bottom: 10px;
    }

    .warn-box {
        background: linear-gradient(135deg, #fff7ed 0%, #fffbeb 100%);
        border: 1px solid #fed7aa;
        border-radius: 16px;
        padding: 14px 16px;
        color: #9a3412;
        margin-bottom: 10px;
    }

    .small-note {
        color: #6b7280;
        font-size: 0.84rem;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e5e7eb;
        padding: 14px;
        border-radius: 16px;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        height: 46px;
        border-radius: 12px;
        background: #eef2ff;
        color: #1f2937;
        font-weight: 600;
        padding-left: 18px;
        padding-right: 18px;
    }

    .stTabs [aria-selected="true"] {
        background: white !important;
        border: 1px solid #dbeafe !important;
        box-shadow: 0 4px 14px rgba(59,130,246,0.12);
        color: #2563eb !important;
    }

    .stButton > button {
        border-radius: 12px;
        border: 1px solid #2563eb;
        background: #2563eb;
        color: white;
        font-weight: 600;
        padding: 0.5rem 1rem;
    }

    .stSelectbox label, .stSlider label {
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# HELPERS
# =========================================================
def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip() for c in df.columns]
    return df

def to_numeric_safe(df: pd.DataFrame, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def normalize_anomaly_flag(value):
    if pd.isna(value):
        return 0
    v = str(value).strip().lower()
    return 1 if v in {"yes", "ja", "y", "true", "1", "kritisch"} else 0

def calculate_anomalies(row):
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

def calculate_score(row):
    score = 100.0
    if pd.notna(row.get("Liefertreue")) and row["Liefertreue"] < 95:
        score -= (95 - row["Liefertreue"]) * 1.8
    if pd.notna(row.get("Lieferzeit")) and row["Lieferzeit"] > 10:
        score -= (row["Lieferzeit"] - 10) * 2.0
    if pd.notna(row.get("Qualitätsrate")) and row["Qualitätsrate"] < 97:
        score -= (97 - row["Qualitätsrate"]) * 2.5
    if pd.notna(row.get("Reklamationsquote")) and row["Reklamationsquote"] > 1.0:
        score -= (row["Reklamationsquote"] - 1.0) * 8
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

def status_label(score):
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
    if not reasons:
        return "gemischtes Leistungsprofil"
    return ", ".join(reasons[:3])

def score_color(score):
    if score >= 90:
        return "#16a34a"
    elif score >= 75:
        return "#d97706"
    return "#dc2626"

def pill_html(text, level):
    cls = {"good":"pill-good","mid":"pill-mid","bad":"pill-bad"}[level]
    return f'<span class="{cls}">{text}</span>'

def donut_chart(value, color):
    fig = go.Figure(go.Pie(
        values=[value, max(0, 100 - value)],
        labels=["Score", ""],
        hole=0.76,
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

# =========================================================
# HEADER
# =========================================================
st.markdown('<div class="top-title">Lieferantenbewertung</div>', unsafe_allow_html=True)
st.markdown('<div class="top-subtitle">KPI-Monitoring · Anomalieerkennung · Procurement Performance Dashboard</div>', unsafe_allow_html=True)

# =========================================================
# SIDEBAR: UPLOAD + MAPPING
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
    material_col = st.selectbox("Material / Category", all_cols, index=all_cols.index("Category") if "Category" in all_cols else 0)
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
missing = [k for k,v in required.items() if v == "-- Nicht vorhanden --"]
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

df = to_numeric_safe(df, ["Liefertreue","Lieferzeit","Qualitätsrate","Reklamationsquote","Preisabweichung","Score"])
df = df.dropna(subset=["Supplier","Country","Material","Liefertreue","Lieferzeit","Qualitätsrate","Reklamationsquote","Preisabweichung"])

if "Anomaly_Flag" in df.columns:
    df["Anomalien"] = df["Anomaly_Flag"].apply(normalize_anomaly_flag)
else:
    df["Anomalien"] = df.apply(calculate_anomalies, axis=1)

if "Score" not in df.columns:
    df["Score"] = df.apply(calculate_score, axis=1)

if "Status" not in df.columns:
    df["Status"] = df["Score"].apply(status_label)

df["Risikostufe"] = df["Score"].apply(risk_level)
df["Kritischer KPI"] = df.apply(critical_kpi, axis=1)
df["Begründung"] = df.apply(supplier_reason, axis=1)

agg = df.groupby("Supplier", as_index=False).agg({
    "Supplier_ID":"first",
    "Material":"first",
    "Country":"first",
    "Liefertreue":"mean",
    "Lieferzeit":"mean",
    "Qualitätsrate":"mean",
    "Reklamationsquote":"mean",
    "Preisabweichung":"mean",
    "Score":"mean",
    "Anomalien":"sum",
    "Status":"first",
    "Risikostufe":"first",
    "Kritischer KPI":"first",
    "Begründung":"first",
})
agg["Score"] = agg["Score"].round(1)
agg = agg.sort_values("Score", ascending=False).reset_index(drop=True)

# =========================================================
# SIDEBAR FILTERS
# =========================================================
with st.sidebar:
    st.markdown("## Filter")
    materials = ["Alle"] + sorted(agg["Material"].astype(str).dropna().unique().tolist())
    selected_material = st.selectbox("Material filtern", materials)
    filtered = agg.copy()
    if selected_material != "Alle":
        filtered = filtered[filtered["Material"] == selected_material]

    selected_supplier = st.selectbox("Lieferant auswählen", filtered["Supplier"].tolist())

selected = filtered[filtered["Supplier"] == selected_supplier].iloc[0]

# =========================================================
# TOP KPI CARDS
# =========================================================
k1, k2, k3, k4, k5 = st.columns(5)

cards = [
    ("Lieferanten", filtered["Supplier"].nunique(), "im aktuellen Filter"),
    ("Ø Score", f"{filtered['Score'].mean():.1f}", "durchschnittliche Bewertung"),
    ("Anomalien", int(filtered["Anomalien"].sum()), "gesamt im Portfolio"),
    ("Top Material", filtered["Material"].mode().iloc[0] if not filtered.empty else "-", "häufigste Kategorie"),
    ("Bester Lieferant", filtered.iloc[0]["Supplier"] if not filtered.empty else "-", "höchster Score"),
]

for col, (label, value, sub) in zip([k1,k2,k3,k4,k5], cards):
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
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Top Lieferanten</div>', unsafe_allow_html=True)
        for _, row in filtered.head(6).iterrows():
            level = "good" if row["Score"] >= 90 else "mid" if row["Score"] >= 75 else "bad"
            st.markdown(f"""
            <div class="supplier-item">
                <div class="supplier-name">{row['Supplier']}</div>
                <div class="supplier-meta">{row['Material']} · {row['Country']}</div>
                <div style="margin-top:8px;">{pill_html(f"Score {row['Score']}", level)} &nbsp; {pill_html(f"{int(row['Anomalien'])} Anomalien", "mid" if row['Anomalien'] > 0 else "good")}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with center:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f'<div class="section-title">{selected["Supplier"]}</div>', unsafe_allow_html=True)
        st.markdown(f"**Lieferanten-ID:** {selected['Supplier_ID']}  \n**Kategorie:** {selected['Material']}  \n**Land:** {selected['Country']}")
        st.write("")
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
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Gesamtscore</div>', unsafe_allow_html=True)
        st.plotly_chart(donut_chart(selected["Score"], score_color(selected["Score"])), use_container_width=True)
        st.markdown(pill_html(selected["Risikostufe"], "good" if selected["Risikostufe"]=="Niedrig" else "mid" if selected["Risikostufe"]=="Mittel" else "bad"), unsafe_allow_html=True)
        st.write("")
        st.markdown(f"**Status:** {selected['Status']}")
        st.markdown(f"**Kritischer KPI:** {selected['Kritischer KPI']}")
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    a, b = st.columns([1.25, 1.0])

    with a:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Automatisches Ranking</div>', unsafe_allow_html=True)
        rank_df = filtered[["Supplier","Material","Country","Score","Anomalien","Kritischer KPI"]].sort_values("Score", ascending=False)
        st.dataframe(rank_df, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with b:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Management Insights</div>', unsafe_allow_html=True)
        top3 = filtered.head(3)
        for i, (_, row) in enumerate(top3.iterrows(), start=1):
            st.markdown(f"""
            <div class="insight-box">
                <b>Top {i}: {row['Supplier']}</b><br>
                Score: {row['Score']} · {row['Material']} · {row['Country']}<br>
                Empfehlung: Lieferant ist stark wegen {row['Begründung']}.
            </div>
            """, unsafe_allow_html=True)

        bottom = filtered.sort_values("Score", ascending=True).head(2)
        for _, row in bottom.iterrows():
            st.markdown(f"""
            <div class="warn-box">
                <b>Beobachten: {row['Supplier']}</b><br>
                Kritischer KPI: {row['Kritischer KPI']} · Score: {row['Score']}<br>
                Handlung: Performance prüfen und Eskalationslogik vorbereiten.
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    r1, r2 = st.columns(2)

    with r1:
        fig_rank = px.bar(
            filtered.sort_values("Score", ascending=False),
            x="Supplier",
            y="Score",
            color="Material",
            title="Lieferantenranking nach Score",
            color_discrete_sequence=px.colors.qualitative.Set2
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
            title="Materialverteilung im Portfolio",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_pie.update_layout(paper_bgcolor="white")
        st.plotly_chart(fig_pie, use_container_width=True)

    with r2:
        fig_scatter = px.scatter(
            filtered,
            x="Liefertreue",
            y="Qualitätsrate",
            size="Score",
            color="Material",
            hover_name="Supplier",
            title="Performance-Matrix: Liefertreue vs. Qualitätsrate",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_scatter.update_layout(plot_bgcolor="white", paper_bgcolor="white", legend_title_text="")
        st.plotly_chart(fig_scatter, use_container_width=True)

        ano = filtered.copy()
        ano["AnomalyStatus"] = np.where(ano["Anomalien"] > 0, "Mit Anomalie", "Ohne Anomalie")
        ano_share = ano["AnomalyStatus"].value_counts().reset_index()
        ano_share.columns = ["Status", "Anzahl"]
        fig_donut = px.pie(
            ano_share,
            names="Status",
            values="Anzahl",
            hole=0.6,
            title="Anomalieverteilung",
            color_discrete_sequence=["#ef4444", "#22c55e"]
        )
        fig_donut.update_layout(paper_bgcolor="white")
        st.plotly_chart(fig_donut, use_container_width=True)

    r3, r4 = st.columns(2)

    with r3:
        fig_lt = px.bar(
            filtered.sort_values("Lieferzeit", ascending=True),
            x="Supplier",
            y="Lieferzeit",
            color="Lieferzeit",
            title="Lieferzeitvergleich",
            color_continuous_scale="Blues"
        )
        fig_lt.update_layout(plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig_lt, use_container_width=True)

    with r4:
        fig_comp = px.bar(
            filtered.sort_values("Reklamationsquote", ascending=False),
            x="Supplier",
            y="Reklamationsquote",
            color="Reklamationsquote",
            title="Reklamationsquotevergleich",
            color_continuous_scale="Oranges"
        )
        fig_comp.update_layout(plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig_comp, use_container_width=True)

with tab4:
    d1, d2 = st.columns([1.1, 1.1])

    with d1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Lieferantenprofil</div>', unsafe_allow_html=True)
        st.write(f"**Lieferant:** {selected['Supplier']}")
        st.write(f"**ID:** {selected['Supplier_ID']}")
        st.write(f"**Kategorie:** {selected['Material']}")
        st.write(f"**Land:** {selected['Country']}")
        st.write(f"**Status:** {selected['Status']}")
        st.write(f"**Risikostufe:** {selected['Risikostufe']}")
        st.write(f"**Kritischer KPI:** {selected['Kritischer KPI']}")
        st.write(f"**Begründung:** {selected['Begründung']}")
        st.markdown('</div>', unsafe_allow_html=True)

        if selected["Score"] >= 90:
            st.markdown(f'<div class="insight-box"><b>Empfehlung:</b> {selected["Supplier"]} kann als bevorzugter Lieferant betrachtet werden, da das Profil durch {selected["Begründung"]} überzeugt.</div>', unsafe_allow_html=True)
        elif selected["Score"] >= 75:
            st.markdown(f'<div class="warn-box"><b>Empfehlung:</b> Lieferant ist grundsätzlich nutzbar, aber der KPI <b>{selected["Kritischer KPI"]}</b> sollte eng beobachtet werden.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="warn-box"><b>Empfehlung:</b> Lieferant ist kritisch. Fokus auf {selected["Kritischer KPI"]}; mögliche Eskalation oder Alternativlieferant prüfen.</div>', unsafe_allow_html=True)

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
            marker_color=["#2563eb", "#16a34a", "#d97706", "#dc2626", "#7c3aed"]
        ))
        fig_profile.update_layout(
            title="KPI-Profil des ausgewählten Lieferanten",
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        st.plotly_chart(fig_profile, use_container_width=True)
