import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Lieferantenbewertung", page_icon="📊", layout="wide")


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(col).strip() for col in df.columns]
    return df


def to_numeric_safe(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def get_risk_level(score):
    if pd.isna(score):
        return "Unbekannt"
    if score >= 90:
        return "Niedrig"
    elif score >= 75:
        return "Mittel"
    return "Hoch"


def get_default_status(score):
    if pd.isna(score):
        return "Unbekannt"
    if score >= 90:
        return "Gut"
    elif score >= 75:
        return "Beobachten"
    return "Kritisch"


def normalize_anomaly_flag(value):
    if pd.isna(value):
        return 0
    value = str(value).strip().lower()
    yes_values = {"yes", "y", "true", "1", "ja", "kritisch"}
    return 1 if value in yes_values else 0


def calculate_anomalies_from_kpis(row):
    count = 0
    if "Liefertreue" in row and pd.notna(row["Liefertreue"]) and row["Liefertreue"] < 95:
        count += 1
    if "Lieferzeit" in row and pd.notna(row["Lieferzeit"]) and row["Lieferzeit"] > 10:
        count += 1
    if "Qualitätsrate" in row and pd.notna(row["Qualitätsrate"]) and row["Qualitätsrate"] < 97:
        count += 1
    if "Reklamationsquote" in row and pd.notna(row["Reklamationsquote"]) and row["Reklamationsquote"] > 1.0:
        count += 1
    if "Preisabweichung" in row and pd.notna(row["Preisabweichung"]) and abs(row["Preisabweichung"]) > 1.0:
        count += 1
    return count


def calculate_score_from_kpis(row):
    score = 100.0

    if pd.notna(row.get("Liefertreue")) and row["Liefertreue"] < 95:
        score -= (95 - row["Liefertreue"]) * 2

    if pd.notna(row.get("Lieferzeit")) and row["Lieferzeit"] > 10:
        score -= (row["Lieferzeit"] - 10) * 2

    if pd.notna(row.get("Qualitätsrate")) and row["Qualitätsrate"] < 97:
        score -= (97 - row["Qualitätsrate"]) * 3

    if pd.notna(row.get("Reklamationsquote")) and row["Reklamationsquote"] > 1.0:
        score -= (row["Reklamationsquote"] - 1.0) * 10

    if pd.notna(row.get("Preisabweichung")) and abs(row["Preisabweichung"]) > 1.0:
        score -= (abs(row["Preisabweichung"]) - 1.0) * 5

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
    max_kpi = max(problems, key=problems.get)
    return max_kpi if problems[max_kpi] > 0 else "Kein kritischer KPI"


def make_mapping_options(columns):
    return ["-- Nicht vorhanden --"] + list(columns)


# --------------------------------------------------
# Title
# --------------------------------------------------
st.title("Lieferantenbewertung")
st.caption("KPI-Monitoring · Anomalieerkennung · Flexible Excel-Spaltenzuordnung")


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

if raw_df.empty:
    st.error("Die hochgeladene Datei enthält keine Daten.")
    st.stop()

st.subheader("1. Erkannte Spalten")
st.dataframe(pd.DataFrame({"Spaltenname": raw_df.columns}), use_container_width=True, hide_index=True)


# --------------------------------------------------
# Column mapping
# --------------------------------------------------
st.subheader("2. Spaltenzuordnung")

all_columns = make_mapping_options(raw_df.columns)

left_map, right_map = st.columns(2)

with left_map:
    supplier_col = st.selectbox("Supplier / Lieferantenname *", all_columns, index=1 if len(all_columns) > 1 else 0)
    country_col = st.selectbox("Country / Land *", all_columns)
    material_col = st.selectbox("Material / Category *", all_columns)
    delivery_col = st.selectbox("Liefertreue / Delivery Performance *", all_columns)
    leadtime_col = st.selectbox("Lieferzeit / Lead Time *", all_columns)
    quality_col = st.selectbox("Qualitätsrate / Quality Score *", all_columns)

with right_map:
    complaint_col = st.selectbox("Reklamationsquote / Complaint Rate *", all_columns)
    price_col = st.selectbox("Preisabweichung / Price Deviation *", all_columns)
    score_col = st.selectbox("Overall Score (optional)", all_columns)
    status_col = st.selectbox("Status (optional)", all_columns)
    anomaly_col = st.selectbox("Anomaly Flag (optional)", all_columns)
    supplier_id_col = st.selectbox("Supplier ID (optional)", all_columns)
    month_col = st.selectbox("Month (optional, for trend charts)", all_columns)

generate = st.button("Dashboard generieren", type="primary")

if not generate:
    st.stop()

required_selected = {
    "Supplier": supplier_col,
    "Country": country_col,
    "Material": material_col,
    "Liefertreue": delivery_col,
    "Lieferzeit": leadtime_col,
    "Qualitätsrate": quality_col,
    "Reklamationsquote": complaint_col,
    "Preisabweichung": price_col,
}

missing_required = [k for k, v in required_selected.items() if v == "-- Nicht vorhanden --"]
if missing_required:
    st.error(f"Bitte ordne alle Pflichtfelder zu: {', '.join(missing_required)}")
    st.stop()

selected_real_cols = list(required_selected.values())
if len(selected_real_cols) != len(set(selected_real_cols)):
    st.error("Mindestens eine Pflichtspalte wurde mehrfach zugeordnet. Bitte jede Pflichtrolle nur einer Spalte zuordnen.")
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

optional_map = {
    score_col: "Score",
    status_col: "Status",
    anomaly_col: "Anomaly_Flag",
    supplier_id_col: "Supplier_ID",
    month_col: "Month",
}

for src, target in optional_map.items():
    if src != "-- Nicht vorhanden --":
        mapping[src] = target

df = raw_df.rename(columns=mapping).copy()

# Add optional fallback columns if missing
if "Supplier_ID" not in df.columns:
    df["Supplier_ID"] = [f"S{i+1:02d}" for i in range(len(df))]

# Convert numeric fields
numeric_cols = ["Liefertreue", "Lieferzeit", "Qualitätsrate", "Reklamationsquote", "Preisabweichung"]
if "Score" in df.columns:
    numeric_cols.append("Score")

df = to_numeric_safe(df, numeric_cols)

# Keep only rows with essential data
df = df.dropna(subset=["Supplier", "Country", "Material", "Liefertreue", "Lieferzeit", "Qualitätsrate", "Reklamationsquote", "Preisabweichung"])

if df.empty:
    st.error("Nach der Bereinigung sind keine gültigen Datenzeilen mehr vorhanden.")
    st.stop()

# Anomalies
if "Anomaly_Flag" in df.columns:
    df["Anomalien"] = df["Anomaly_Flag"].apply(normalize_anomaly_flag)
else:
    df["Anomalien"] = df.apply(calculate_anomalies_from_kpis, axis=1)

# Score
if "Score" not in df.columns:
    df["Score"] = df.apply(calculate_score_from_kpis, axis=1)

# Status
if "Status" not in df.columns:
    df["Status"] = df["Score"].apply(get_default_status)

# Risk + critical KPI
df["Risikostufe"] = df["Score"].apply(get_risk_level)
df["Kritischer KPI"] = df.apply(get_critical_kpi, axis=1)

# Month ordering if available
if "Month" in df.columns:
    month_order = ["Jan", "Feb", "Mar", "Apr", "Mai", "May", "Jun", "Jul", "Aug", "Sep", "Okt", "Oct", "Nov", "Dez", "Dec"]
    if df["Month"].astype(str).isin(month_order).all():
        df["Month"] = pd.Categorical(df["Month"], categories=month_order, ordered=True)
        df = df.sort_values(["Supplier", "Month"])

st.success("Spalten erfolgreich zugeordnet.")


# --------------------------------------------------
# Filters
# --------------------------------------------------
st.subheader("3. Dashboard")

st.sidebar.header("Filter")

material_options = ["Alle"] + sorted(df["Material"].astype(str).dropna().unique().tolist())
selected_material = st.sidebar.selectbox("Material", material_options)

filtered_df = df.copy()
if selected_material != "Alle":
    filtered_df = filtered_df[filtered_df["Material"] == selected_material]

supplier_options = filtered_df["Supplier"].astype(str).dropna().unique().tolist()
selected_supplier = st.sidebar.selectbox("Lieferant auswählen", supplier_options)

selected_df = filtered_df[filtered_df["Supplier"] == selected_supplier].copy()

if selected_df.empty:
    st.warning("Kein Lieferant nach aktuellem Filter gefunden.")
    st.stop()

# For card values, aggregate supplier if multiple rows exist
selected_row = selected_df.iloc[0].copy()
if len(selected_df) > 1:
    selected_row["Liefertreue"] = selected_df["Liefertreue"].mean()
    selected_row["Lieferzeit"] = selected_df["Lieferzeit"].mean()
    selected_row["Qualitätsrate"] = selected_df["Qualitätsrate"].mean()
    selected_row["Reklamationsquote"] = selected_df["Reklamationsquote"].mean()
    selected_row["Preisabweichung"] = selected_df["Preisabweichung"].mean()
    selected_row["Score"] = selected_df["Score"].mean()
    selected_row["Anomalien"] = selected_df["Anomalien"].sum()
    selected_row["Risikostufe"] = get_risk_level(selected_row["Score"])
    selected_row["Status"] = get_default_status(selected_row["Score"])
    selected_row["Kritischer KPI"] = get_critical_kpi(selected_row)

# Top summary across filtered set
agg_view = filtered_df.groupby("Supplier", as_index=False).agg({
    "Material": "first",
    "Country": "first",
    "Score": "mean",
    "Anomalien": "sum",
    "Liefertreue": "mean",
    "Lieferzeit": "mean",
    "Qualitätsrate": "mean",
    "Reklamationsquote": "mean",
    "Preisabweichung": "mean",
})
agg_view["Risikostufe"] = agg_view["Score"].apply(get_risk_level)
agg_view["Status"] = agg_view["Score"].apply(get_default_status)

# Top cards
c1, c2, c3, c4 = st.columns(4)
c1.metric("Lieferanten", int(agg_view["Supplier"].nunique()))
c2.metric("Ø Score", f"{agg_view['Score'].mean():.1f}")
c3.metric("Gesamt-Anomalien", int(agg_view["Anomalien"].sum()))
c4.metric("Ø Liefertreue", f"{agg_view['Liefertreue'].mean():.1f}%")

st.divider()

# Main layout
left, center, right = st.columns([1.15, 2.2, 1.0])

with left:
    st.subheader("Lieferantenliste")
    supplier_table = agg_view[["Supplier", "Material", "Country", "Score", "Status", "Anomalien"]].copy()
    supplier_table["Score"] = supplier_table["Score"].round(1)
    st.dataframe(supplier_table.sort_values("Score", ascending=False), use_container_width=True, hide_index=True)

with center:
    st.subheader(str(selected_row["Supplier"]))
    st.write(
        f"**Lieferanten-ID:** {selected_row.get('Supplier_ID', '-')}" + "  |  "
        f"**Kategorie:** {selected_row['Material']}" + "  |  "
        f"**Land:** {selected_row['Country']}"
    )

    k1, k2, k3 = st.columns(3)
    k4, k5, k6 = st.columns(3)

    k1.metric("Liefertreue", f"{selected_row['Liefertreue']:.1f}%")
    k2.metric("Lieferzeit", f"{selected_row['Lieferzeit']:.1f} Tage")
    k3.metric("Qualitätsrate", f"{selected_row['Qualitätsrate']:.1f}%")
    k4.metric("Reklamationsquote", f"{selected_row['Reklamationsquote']:.1f}%")
    k5.metric("Preisabweichung", f"{selected_row['Preisabweichung']:.1f}%")
    k6.metric("Anomalien", int(selected_row["Anomalien"]))

with right:
    st.subheader("Bewertung")
    st.metric("Gesamtscore", f"{selected_row['Score']:.1f}/100")
    st.write(f"**Risikostufe:** {selected_row['Risikostufe']}")
    st.write(f"**Status:** {selected_row['Status']}")
    st.write(f"**Kritischer KPI:** {selected_row['Kritischer KPI']}")

st.divider()

# Charts
if "Month" in selected_df.columns and selected_df["Month"].nunique() > 1:
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

        if "Anomalien" in selected_df.columns:
            fig6 = px.bar(selected_df, x="Month", y="Anomalien", title="Anomalien pro Monat")
            st.plotly_chart(fig6, use_container_width=True)
else:
    st.subheader("KPI-Vergleich aller Lieferanten")

    col1, col2 = st.columns(2)

    with col1:
        fig1 = px.bar(agg_view, x="Supplier", y="Liefertreue", color="Liefertreue", title="Liefertreue (%)")
        st.plotly_chart(fig1, use_container_width=True)

        fig2 = px.bar(agg_view, x="Supplier", y="Qualitätsrate", color="Qualitätsrate", title="Qualitätsrate (%)")
        st.plotly_chart(fig2, use_container_width=True)

        fig3 = px.bar(agg_view, x="Supplier", y="Score", color="Score", title="Gesamtscore")
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        fig4 = px.bar(agg_view, x="Supplier", y="Lieferzeit", color="Lieferzeit", title="Lieferzeit (Tage)")
        st.plotly_chart(fig4, use_container_width=True)

        fig5 = px.bar(agg_view, x="Supplier", y="Reklamationsquote", color="Reklamationsquote", title="Reklamationsquote (%)")
        st.plotly_chart(fig5, use_container_width=True)

        fig6 = px.bar(agg_view, x="Supplier", y="Preisabweichung", color="Preisabweichung", title="Preisabweichung (%)")
        st.plotly_chart(fig6, use_container_width=True)

st.divider()

# Anomaly overview
st.subheader("Anomalien-Übersicht")

anomaly_df = agg_view[agg_view["Anomalien"] > 0].copy()

if anomaly_df.empty:
    st.success("Keine Anomalien in den aktuellen Daten gefunden.")
else:
    st.dataframe(
        anomaly_df[[
            "Supplier",
            "Material",
            "Country",
            "Liefertreue",
            "Lieferzeit",
            "Qualitätsrate",
            "Reklamationsquote",
            "Preisabweichung",
            "Score",
            "Status",
            "Anomalien",
        ]].sort_values("Anomalien", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

st.divider()

with st.expander("Vorschau der intern verwendeten Spaltenzuordnung"):
    mapping_preview = pd.DataFrame(
        [
            ["Supplier", supplier_col],
            ["Country", country_col],
            ["Material", material_col],
            ["Liefertreue", delivery_col],
            ["Lieferzeit", leadtime_col],
            ["Qualitätsrate", quality_col],
            ["Reklamationsquote", complaint_col],
            ["Preisabweichung", price_col],
            ["Score", score_col],
            ["Status", status_col],
            ["Anomaly_Flag", anomaly_col],
            ["Supplier_ID", supplier_id_col],
            ["Month", month_col],
        ],
        columns=["Interne Dashboard-Spalte", "Zugeordnete Excel-Spalte"],
    )
    st.dataframe(mapping_preview, use_container_width=True, hide_index=True)
