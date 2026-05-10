import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Lieferantenbewertung", page_icon="📊", layout="wide")

# -----------------------------
# Helper functions
# -----------------------------
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(col).strip() for col in df.columns]
    return df


def validate_columns(df: pd.DataFrame):
    required_cols = [
        "Supplier",
        "Country",
        "Material",
        "Month",
        "Liefertreue",
        "Lieferzeit",
        "Qualitätsrate",
        "Reklamationsquote",
        "Preisabweichung",
    ]
    missing = [col for col in required_cols if col not in df.columns]
    return missing


def calculate_anomaly_count(row):
    count = 0
    if row["Liefertreue"] < 95:
        count += 1
    if row["Lieferzeit"] > 10:
        count += 1
    if row["Qualitätsrate"] < 97:
        count += 1
    if row["Reklamationsquote"] > 1.0:
        count += 1
    if abs(row["Preisabweichung"]) > 1.0:
        count += 1
    return count


def calculate_score(row):
    score = 100.0

    if row["Liefertreue"] < 95:
        score -= (95 - row["Liefertreue"]) * 2

    if row["Lieferzeit"] > 10:
        score -= (row["Lieferzeit"] - 10) * 2

    if row["Qualitätsrate"] < 97:
        score -= (97 - row["Qualitätsrate"]) * 3

    if row["Reklamationsquote"] > 1.0:
        score -= (row["Reklamationsquote"] - 1.0) * 10

    if abs(row["Preisabweichung"]) > 1.0:
        score -= (abs(row["Preisabweichung"]) - 1.0) * 5

    score -= row["Anomalien"] * 0.5
    return max(round(score, 1), 0)


def get_risk_level(score):
    if score >= 90:
        return "Niedrig"
    elif score >= 75:
        return "Mittel"
    return "Hoch"


def get_status(score):
    if score >= 90:
        return "Gut"
    elif score >= 75:
        return "Beobachten"
    return "Kritisch"


def get_critical_kpi(row):
    problems = {
        "Liefertreue": 95 - row["Liefertreue"] if row["Liefertreue"] < 95 else 0,
        "Lieferzeit": row["Lieferzeit"] - 10 if row["Lieferzeit"] > 10 else 0,
        "Qualitätsrate": 97 - row["Qualitätsrate"] if row["Qualitätsrate"] < 97 else 0,
        "Reklamationsquote": row["Reklamationsquote"] - 1.0 if row["Reklamationsquote"] > 1.0 else 0,
        "Preisabweichung": abs(row["Preisabweichung"]) - 1.0 if abs(row["Preisabweichung"]) > 1.0 else 0,
    }
    max_kpi = max(problems, key=problems.get)
    return max_kpi if problems[max_kpi] > 0 else "Kein kritischer KPI"


# -----------------------------
# App title
# -----------------------------
st.title("Lieferantenbewertung")
st.caption("KPI-Monitoring · Anomalieerkennung · Excel Upload")

# -----------------------------
# File upload
# -----------------------------
uploaded_file = st.file_uploader("Excel-Datei hochladen", type=["xlsx", "xls"])

if uploaded_file is None:
    st.info("Bitte lade deine Excel-Datei hoch.")
    st.stop()

try:
    df = pd.read_excel(uploaded_file)
except Exception as e:
    st.error(f"Fehler beim Lesen der Excel-Datei: {e}")
    st.stop()

df = normalize_columns(df)

missing_cols = validate_columns(df)
if missing_cols:
    st.error("Folgende Spalten fehlen in deiner Excel-Datei:")
    st.write(missing_cols)
    st.stop()

# Optional columns defaults
if "ContractValue" not in df.columns:
    df["ContractValue"] = 0.0

if "Category" not in df.columns:
    df["Category"] = df["Material"]

# Numeric conversion
numeric_cols = [
    "Liefertreue",
    "Lieferzeit",
    "Qualitätsrate",
    "Reklamationsquote",
    "Preisabweichung",
    "ContractValue",
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=[
    "Supplier",
    "Country",
    "Material",
    "Month",
    "Liefertreue",
    "Lieferzeit",
    "Qualitätsrate",
    "Reklamationsquote",
    "Preisabweichung",
])

# Preserve month order if possible
month_order = ["Jan", "Feb", "Mar", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
if df["Month"].astype(str).isin(month_order).all():
    df["Month"] = pd.Categorical(df["Month"], categories=month_order, ordered=True)
    df = df.sort_values(["Supplier", "Month"])

# -----------------------------
# KPI logic
# -----------------------------
df["Anomalien"] = df.apply(calculate_anomaly_count, axis=1)

summary = df.groupby(
    ["Supplier", "Country", "Material", "Category"],
    as_index=False
).agg({
    "Liefertreue": "mean",
    "Lieferzeit": "mean",
    "Qualitätsrate": "mean",
    "Reklamationsquote": "mean",
    "Preisabweichung": "mean",
    "Anomalien": "sum",
    "ContractValue": "max",
})

summary["Score"] = summary.apply(calculate_score, axis=1)
summary["Risikostufe"] = summary["Score"].apply(get_risk_level)
summary["Status"] = summary["Score"].apply(get_status)
summary["Kritischer KPI"] = summary.apply(get_critical_kpi, axis=1)
summary = summary.sort_values("Score", ascending=False).reset_index(drop=True)

# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("Filter")

supplier_list = summary["Supplier"].tolist()
selected_supplier = st.sidebar.selectbox("Lieferant auswählen", supplier_list)

material_options = ["Alle"] + sorted(df["Material"].dropna().astype(str).unique().tolist())
selected_material = st.sidebar.selectbox("Material", material_options)

filtered_df = df.copy()
if selected_material != "Alle":
    filtered_df = filtered_df[filtered_df["Material"] == selected_material]

filtered_summary = summary.copy()
if selected_material != "Alle":
    filtered_summary = filtered_summary[filtered_summary["Material"] == selected_material]

selected_summary = summary[summary["Supplier"] == selected_supplier]
if selected_summary.empty:
    st.warning("Ausgewählter Lieferant nicht in den Daten gefunden.")
    st.stop()

selected_summary = selected_summary.iloc[0]
selected_df = df[df["Supplier"] == selected_supplier].copy()

# -----------------------------
# Top cards
# -----------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Lieferanten", int(filtered_summary["Supplier"].nunique()))
c2.metric("Ø Score", f"{filtered_summary['Score'].mean():.1f}")
c3.metric("Gesamt-Anomalien", int(filtered_df["Anomalien"].sum()))
c4.metric("Vertragsvolumen", f"€ {filtered_summary['ContractValue'].sum():,.1f}")

st.divider()

# -----------------------------
# Main layout
# -----------------------------
left, center, right = st.columns([1.2, 2.3, 1.1])

with left:
    st.subheader("Lieferantenliste")
    display_summary = filtered_summary[[
        "Supplier", "Material", "Country", "Score", "Anomalien", "Status"
    ]].copy()
    display_summary["Score"] = display_summary["Score"].round(1)
    st.dataframe(display_summary, use_container_width=True, hide_index=True)

with center:
    st.subheader(f"{selected_summary['Supplier']}")
    st.write(
        f"**Material:** {selected_summary['Material']}  |  "
        f"**Kategorie:** {selected_summary['Category']}  |  "
        f"**Land:** {selected_summary['Country']}  |  "
        f"**Vertragsvolumen:** € {selected_summary['ContractValue']:,.1f}"
    )

    k1, k2, k3 = st.columns(3)
    k4, k5, k6 = st.columns(3)

    k1.metric("Ø Liefertreue", f"{selected_summary['Liefertreue']:.1f}%")
    k2.metric("Ø Lieferzeit", f"{selected_summary['Lieferzeit']:.1f} Tage")
    k3.metric("Ø Qualitätsrate", f"{selected_summary['Qualitätsrate']:.1f}%")
    k4.metric("Ø Reklamationsquote", f"{selected_summary['Reklamationsquote']:.2f}%")
    k5.metric("Ø Preisabweichung", f"{selected_summary['Preisabweichung']:.2f}%")
    k6.metric("Anomalien", int(selected_summary["Anomalien"]))

with right:
    st.subheader("Bewertung")
    st.metric("Gesamtscore", f"{selected_summary['Score']:.1f}/100")
    st.write(f"**Risikostufe:** {selected_summary['Risikostufe']}")
    st.write(f"**Status:** {selected_summary['Status']}")
    st.write(f"**Kritischer KPI:** {selected_summary['Kritischer KPI']}")

st.divider()

# -----------------------------
# Trend charts
# -----------------------------
st.subheader("KPI-Trendanalyse")

col_a, col_b = st.columns(2)

with col_a:
    fig1 = px.line(selected_df, x="Month", y="Liefertreue", markers=True, title="Liefertreue (%)")
    fig1.add_hline(y=95, line_dash="dash")
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.line(selected_df, x="Month", y="Qualitätsrate", markers=True, title="Qualitätsrate (%)")
    fig2.add_hline(y=97, line_dash="dash")
    st.plotly_chart(fig2, use_container_width=True)

    fig3 = px.line(selected_df, x="Month", y="Preisabweichung", markers=True, title="Preisabweichung (%)")
    fig3.add_hline(y=1.0, line_dash="dash")
    fig3.add_hline(y=-1.0, line_dash="dash")
    st.plotly_chart(fig3, use_container_width=True)

with col_b:
    fig4 = px.line(selected_df, x="Month", y="Lieferzeit", markers=True, title="Lieferzeit (Tage)")
    fig4.add_hline(y=10, line_dash="dash")
    st.plotly_chart(fig4, use_container_width=True)

    fig5 = px.line(selected_df, x="Month", y="Reklamationsquote", markers=True, title="Reklamationsquote (%)")
    fig5.add_hline(y=1.0, line_dash="dash")
    st.plotly_chart(fig5, use_container_width=True)

    fig6 = px.bar(selected_df, x="Month", y="Anomalien", title="Anomalien pro Monat")
    st.plotly_chart(fig6, use_container_width=True)

st.divider()

# -----------------------------
# Comparison section
# -----------------------------
comp1, comp2 = st.columns([1.2, 1.8])

with comp1:
    st.subheader("Lieferantenvergleich")
    fig_compare = px.bar(
        filtered_summary.sort_values("Score", ascending=True),
        x="Score",
        y="Supplier",
        orientation="h",
        title="Score je Lieferant",
        text="Score"
    )
    st.plotly_chart(fig_compare, use_container_width=True)

with comp2:
    st.subheader("Detailtabelle")
    detail_table = filtered_summary[[
        "Supplier",
        "Material",
        "Country",
        "Liefertreue",
        "Lieferzeit",
        "Qualitätsrate",
        "Reklamationsquote",
        "Preisabweichung",
        "Anomalien",
        "Score",
        "Risikostufe",
        "Status"
    ]].copy()

    for col in ["Liefertreue", "Lieferzeit", "Qualitätsrate", "Reklamationsquote", "Preisabweichung", "Score"]:
        detail_table[col] = detail_table[col].round(2)

    st.dataframe(detail_table, use_container_width=True, hide_index=True)
