import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Lieferantenbewertung",
    page_icon="📊",
    layout="wide",
)

# --------------------------------------------------
# Styling
# --------------------------------------------------
st.markdown("""
<style>
    .main {
        background-color: #f6f8fc;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1rem;
    }
    .metric-card {
        background: white;
        padding: 16px 18px;
        border-radius: 16px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        border-left: 6px solid #3b82f6;
    }
    .section-card {
        background: white;
        padding: 18px;
        border-radius: 18px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        margin-bottom: 14px;
    }
    .insight-good {
        background: #ecfdf5;
        color: #065f46;
        padding: 10px 14px;
        border-radius: 12px;
        margin-bottom: 8px;
    }
    .insight-warn {
        background: #fff7ed;
        color: #9a3412;
        padding: 10px 14px;
        border-radius: 12px;
        margin-bottom: 8px;
    }
    .small-muted {
        color: #6b7280;
        font-size: 0.92rem;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Helpers
# --------------------------------------------------
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

def get_risk_level(score):
    if pd.isna(score):
        return "Unbekannt"
    if score >= 90:
        return "Niedrig"
    elif score >= 75:
        return "Mittel"
    return "Hoch"

def get_status_default(score):
    if pd.isna(score):
        return "Unbekannt"
    if score >= 90:
        return "Sehr gut"
    elif score >= 75:
        return "Beobachten"
    return "Kritisch"

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

def get_critical_kpi(row):
    problems = {
        "Liefertreue": 95 - row["Liefertreue"] if pd.notna(row.get("Liefertreue")) and row["Liefertreue"] < 95 else 0,
        "Lieferzeit": row["Lieferzeit"] - 10 if pd.notna(row.get("Lieferzeit")) and row["Lieferzeit"] > 10 else 0,
        "Qualitätsrate": 97 - row["Qualitätsrate"] if pd.notna(row.get("Qualitätsrate")) and row["Qualitätsrate"] < 97 else 0,
        "Reklamationsquote": row["Reklamationsquote"] - 1.0 if pd.notna(row.get("Reklamationsquote")) and row["Reklamationsquote"] > 1.0 else 0,
        "Preisabweichung": abs(row["Preisabweichung"]) - 1.0 if pd.notna(row.get("Preisabweichung")) and abs(row["Preisabweichung"]) > 1.0 else 0,
    }
    best = max(problems, key=problems.get)
    return best if problems[best] > 0 else "Kein kritischer KPI"

def get_reason_text(row):
    reasons = []
    if row["Liefertreue"] >= 95:
        reasons.append("hohe Liefertreue")
    if row["Qualitätsrate"] >= 97:
        reasons.append("starke Qualitätsleistung")
    if row["Lieferzeit"] <= 10:
        reasons.append("gute Lieferzeit")
    if row["Reklamationsquote"] <= 1.0:
        reasons.append("niedrige Reklamationsquote")
    if abs(row["Preisabweichung"]) <= 1.0:
        reasons.append("stabile Preisabweichung")
    if not reasons:
        return "gemischtes Leistungsprofil"
    return ", ".join(reasons[:3])

def make_donut(label, value, color="#3b82f6"):
    fig = go.Figure(go.Pie(
        values=[value, max(0, 100 - value)],
        labels=[label, ""],
        hole=0.72,
        marker_colors=[color, "#e5e7eb"],
        textinfo="none",
        sort=False
    ))
    fig.update_layout(
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0),
        paper_bgcolor="white",
        annotations=[dict(text=f"<b>{value:.1f}</b>", x=0.5, y=0.5, font_size=26, showarrow=False)]
    )
    return fig

# --------------------------------------------------
# Header
# --------------------------------------------------
st.title("Lieferantenbewertung")
st.caption("KPI-Monitoring · Anomalieerkennung · Interaktive Dashboard-App")

# --------------------------------------------------
# Upload
# --------------------------------------------------
uploaded_file = st.file_uploader("Excel-Datei hochladen", type=["xlsx", "xls"])

if uploaded_file is None:
    st.info("Bitte lade eine Excel-Datei hoch.")
    st.stop()

try:
    raw_df = pd.read_excel(uploaded_file)
except Exception as e:
    st.error(f"Fehler beim Lesen der Datei: {e}")
    st.stop()

raw_df = clean_columns(raw_df)
all_cols = ["-- Nicht vorhanden --"] + list(raw_df.columns)

# --------------------------------------------------
# Mapping UI - cleaner
# --------------------------------------------------
with st.expander("Spaltenzuordnung", expanded=True):
    c1, c2, c3 = st.columns(3)

    with c1:
        supplier_col = st.selectbox("Supplier", all_cols, index=all_cols.index("Supplier_Name") if "Supplier_Name" in all_cols else 0)
        country_col = st.selectbox("Country", all_cols, index=all_cols.index("Country") if "Country" in all_cols else 0)
        material_col = st.selectbox("Material / Category", all_cols, index=all_cols.index("Category") if "Category" in all_cols else 0)
        supplier_id_col = st.selectbox("Supplier ID (optional)", all_cols, index=all_cols.index("Supplier_ID") if "Supplier_ID" in all_cols else 0)

    with c2:
        delivery_col = st.selectbox("Liefertreue", all_cols, index=all_cols.index("Delivery_Performance_%") if "Delivery_Performance_%" in all_cols else 0)
        leadtime_col = st.selectbox("Lieferzeit", all_cols, index=all_cols.index("Lead_Time_Days") if "Lead_Time_Days" in all_cols else 0)
        quality_col = st.selectbox("Qualitätsrate", all_cols, index=all_cols.index("Quality_Score_%") if "Quality_Score_%" in all_cols else 0)
        complaint_col = st.selectbox("Reklamationsquote", all_cols, index=all_cols.index("Complaint_Rate_%") if "Complaint_Rate_%" in all_cols else 0)

    with c3:
        price_col = st.selectbox("Preisabweichung", all_cols, index=all_cols.index("Price_Deviation_%") if "Price_Deviation_%" in all_cols else 0)
        score_col = st.selectbox("Score (optional)", all_cols, index=all_cols.index("Overall_Score") if "Overall_Score" in all_cols else 0)
        status_col = st.selectbox("Status (optional)", all_cols, index=all_cols.index("Status") if "Status" in all_cols else 0)
        anomaly_col = st.selectbox("Anomaly Flag (optional)", all_cols, index=all_cols.index("Anomaly_Flag") if "Anomaly_Flag" in all_cols else 0)
        month_col = st.selectbox("Month (optional)", all_cols)

    run_dashboard = st.button("Dashboard laden", type="primary")

if not run_dashboard:
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
    st.error(f"Bitte ordne alle Pflichtspalten zu: {', '.join(missing)}")
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
    supplier_id_col: "Supplier_ID",
    score_col: "Score",
    status_col: "Status",
    anomaly_col: "Anomaly_Flag",
    month_col: "Month",
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
    df["Anomalien"] = df.apply(calculate_anomalies, axis=1)

if "Score" not in df.columns:
    df["Score"] = df.apply(calculate_score, axis=1)

if "Status" not in df.columns:
    df["Status"] = df["Score"].apply(get_status_default)

df["Risikostufe"] = df["Score"].apply(get_risk_level)
df["Kritischer KPI"] = df.apply(get_critical_kpi, axis=1)
df["Warum gut?"] = df.apply(get_reason_text, axis=1)

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
    "Warum gut?": "first",
})

agg["Score"] = agg["Score"].round(1)
agg = agg.sort_values("Score", ascending=False).reset_index(drop=True)

# --------------------------------------------------
# Sidebar filters
# --------------------------------------------------
st.sidebar.header("Filter")

materials = ["Alle"] + sorted(agg["Material"].dropna().astype(str).unique().tolist())
selected_material = st.sidebar.selectbox("Material filtern", materials)

filtered = agg.copy()
if selected_material != "Alle":
    filtered = filtered[filtered["Material"] == selected_material]

top_n = st.sidebar.slider("Top Lieferanten anzeigen", 3, min(10, max(3, len(filtered))), min(5, max(3, len(filtered))))
selected_supplier = st.sidebar.selectbox("Lieferant auswählen", filtered["Supplier"].tolist())

selected = filtered[filtered["Supplier"] == selected_supplier].iloc[0]

# --------------------------------------------------
# KPI cards row
# --------------------------------------------------
c1, c2, c3, c4, c5 = st.columns(5)
c1.markdown(f'<div class="metric-card"><div class="small-muted">Lieferanten</div><h2>{filtered["Supplier"].nunique()}</h2></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="metric-card"><div class="small-muted">Ø Score</div><h2>{filtered["Score"].mean():.1f}</h2></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="metric-card"><div class="small-muted">Anomalien</div><h2>{int(filtered["Anomalien"].sum())}</h2></div>', unsafe_allow_html=True)
c4.markdown(f'<div class="metric-card"><div class="small-muted">Top Material</div><h2>{filtered["Material"].mode().iloc[0] if not filtered.empty else "-"}</h2></div>', unsafe_allow_html=True)
c5.markdown(f'<div class="metric-card"><div class="small-muted">Bester Lieferant</div><h2>{filtered.iloc[0]["Supplier"] if not filtered.empty else "-"}</h2></div>', unsafe_allow_html=True)

st.write("")

# --------------------------------------------------
# Tabs
# --------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["Übersicht", "Top 3", "Visualisierungen", "Lieferantendetails"])

with tab1:
    a, b, c = st.columns([1.2, 1.4, 1.1])

    with a:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Ranking")
        ranking_table = filtered[["Supplier", "Material", "Country", "Score", "Anomalien"]].sort_values("Score", ascending=False).head(top_n)
        st.dataframe(ranking_table, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with b:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader(f"Ausgewählter Lieferant: {selected['Supplier']}")
        st.write(f"**Lieferanten-ID:** {selected['Supplier_ID']}")
        st.write(f"**Material:** {selected['Material']}")
        st.write(f"**Land:** {selected['Country']}")
        st.write(f"**Risikostufe:** {selected['Risikostufe']}")
        st.write(f"**Status:** {selected['Status']}")
        st.write(f"**Kritischer KPI:** {selected['Kritischer KPI']}")
        st.write(f"**Stärken:** {selected['Warum gut?']}")
        st.markdown("</div>", unsafe_allow_html=True)

    with c:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Gesamtscore")
        st.plotly_chart(make_donut("Score", selected["Score"], "#2563eb"), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    r1, r2, r3, r4, r5 = st.columns(5)
    r1.metric("Liefertreue", f"{selected['Liefertreue']:.1f}%")
    r2.metric("Lieferzeit", f"{selected['Lieferzeit']:.1f} Tage")
    r3.metric("Qualitätsrate", f"{selected['Qualitätsrate']:.1f}%")
    r4.metric("Reklamationsquote", f"{selected['Reklamationsquote']:.1f}%")
    r5.metric("Preisabweichung", f"{selected['Preisabweichung']:.1f}%")

with tab2:
    top3 = filtered.sort_values("Score", ascending=False).head(3).copy()

    st.subheader("Top 3 empfohlene Lieferanten")
    for i, (_, row) in enumerate(top3.iterrows(), start=1):
        color = "#16a34a" if i == 1 else "#2563eb" if i == 2 else "#f59e0b"
        st.markdown(f"""
        <div class="section-card">
            <h3 style="margin-bottom:6px;color:{color};">#{i} {row['Supplier']}</h3>
            <div><b>Material:</b> {row['Material']} &nbsp; | &nbsp; <b>Land:</b> {row['Country']} &nbsp; | &nbsp; <b>Score:</b> {row['Score']}</div>
            <div style="margin-top:8px;"><b>Warum empfohlen?</b> {row['Warum gut?']}</div>
            <div style="margin-top:6px;"><b>Kritischer KPI:</b> {row['Kritischer KPI']}</div>
        </div>
        """, unsafe_allow_html=True)

with tab3:
    v1, v2 = st.columns(2)

    with v1:
        fig_score = px.bar(
            filtered.sort_values("Score", ascending=False).head(top_n),
            x="Supplier",
            y="Score",
            color="Score",
            color_continuous_scale="Blues",
            title="Lieferantenranking nach Score"
        )
        fig_score.update_layout(plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig_score, use_container_width=True)

        pie_data = filtered["Material"].value_counts().reset_index()
        pie_data.columns = ["Material", "Anzahl"]
        fig_pie = px.pie(
            pie_data,
            names="Material",
            values="Anzahl",
            hole=0.45,
            title="Verteilung nach Material",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with v2:
        fig_scatter = px.scatter(
            filtered,
            x="Liefertreue",
            y="Qualitätsrate",
            size="Score",
            color="Material",
            hover_name="Supplier",
            title="Liefertreue vs. Qualitätsrate",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_scatter.update_layout(plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig_scatter, use_container_width=True)

        anomaly_counts = filtered.copy()
        anomaly_counts["Anomaly Status"] = anomaly_counts["Anomalien"].apply(lambda x: "Mit Anomalie" if x > 0 else "Ohne Anomalie")
        fig_donut = px.pie(
            anomaly_counts["Anomaly Status"].value_counts().reset_index(),
            names="Anomaly Status",
            values="count",
            hole=0.55,
            title="Anomalie-Verteilung",
            color_discrete_sequence=["#ef4444", "#22c55e"]
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    h1, h2 = st.columns(2)
    with h1:
        fig_lt = px.bar(
            filtered.sort_values("Lieferzeit", ascending=True).head(top_n),
            x="Supplier",
            y="Lieferzeit",
            color="Lieferzeit",
            color_continuous_scale="Tealgrn",
            title="Lieferzeitvergleich"
        )
        st.plotly_chart(fig_lt, use_container_width=True)

    with h2:
        fig_comp = px.bar(
            filtered.sort_values("Reklamationsquote", ascending=False).head(top_n),
            x="Supplier",
            y="Reklamationsquote",
            color="Reklamationsquote",
            color_continuous_scale="OrRd",
            title="Reklamationsquotevergleich"
        )
        st.plotly_chart(fig_comp, use_container_width=True)

with tab4:
    left, right = st.columns([1.5, 1.2])

    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader(selected["Supplier"])
        st.write(f"**ID:** {selected['Supplier_ID']}")
        st.write(f"**Material:** {selected['Material']}")
        st.write(f"**Country:** {selected['Country']}")
        st.write(f"**Status:** {selected['Status']}")
        st.write(f"**Risikostufe:** {selected['Risikostufe']}")
        st.write(f"**Warum ist der Lieferant so bewertet?**")
        if selected["Score"] >= 90:
            st.markdown(f'<div class="insight-good">Dieser Lieferant gehört zu den besten, weil er {selected["Warum gut?"]} zeigt.</div>', unsafe_allow_html=True)
        elif selected["Score"] >= 75:
            st.markdown(f'<div class="insight-warn">Dieser Lieferant ist akzeptabel, aber der KPI "{selected["Kritischer KPI"]}" sollte beobachtet werden.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="insight-warn">Dieser Lieferant ist kritisch. Hauptproblem ist "{selected["Kritischer KPI"]}".</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        fig_supplier = go.Figure()
        fig_supplier.add_trace(go.Bar(
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
        fig_supplier.update_layout(
            title="KPI-Profil des Lieferanten",
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        st.plotly_chart(fig_supplier, use_container_width=True)

# Optional mapping preview
with st.expander("Interne Spaltenzuordnung anzeigen"):
    preview = pd.DataFrame({
        "Dashboard-Feld": list(required.keys()) + ["Score", "Status", "Anomaly_Flag", "Supplier_ID", "Month"],
        "Excel-Spalte": [supplier_col, country_col, material_col, delivery_col, leadtime_col, quality_col, complaint_col, price_col, score_col, status_col, anomaly_col, supplier_id_col, month_col]
    })
    st.dataframe(preview, use_container_width=True, hide_index=True)
