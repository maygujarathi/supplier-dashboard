import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re
from difflib import SequenceMatcher


# =========================================================
# PAGE CONFIG
# =========================================================
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
    @import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700;800;900&family=Geist+Mono:wght@400;500;600&display=swap');

    * {
        font-family: 'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
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
        background: linear-gradient(180deg, rgba(10, 14, 39, 0.95) 0%, rgba(13, 15, 34, 0.95) 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
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

    .metric-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.5) 0%, rgba(25, 35, 50, 0.3) 100%);
        border: 1px solid rgba(96, 165, 250, 0.15);
        border-radius: 14px;
        padding: 20px;
        min-height: 140px;
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.25);
    }

    .metric-label {
        font-size: 0.85rem;
        color: #9ca3af;
        font-weight: 600;
        margin-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: #60a5fa;
        line-height: 1.2;
    }

    .metric-sub {
        margin-top: 12px;
        color: #6b7280;
        font-size: 0.82rem;
        font-weight: 500;
    }

    .premium-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(25, 35, 50, 0.4) 100%);
        border: 1px solid rgba(148, 163, 184, 0.12);
        border-radius: 16px;
        padding: 22px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        margin-bottom: 16px;
    }

    .section-title {
        font-size: 1.25rem;
        font-weight: 800;
        color: #f1f5f9;
        margin-bottom: 18px;
    }

    .supplier-item {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(96, 165, 250, 0.1);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }

    .supplier-name {
        font-weight: 700;
        color: #f1f5f9;
        font-size: 1.05rem;
        margin-bottom: 6px;
    }

    .supplier-meta {
        color: #9ca3af;
        font-size: 0.85rem;
        font-weight: 500;
    }

    .badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 4px;
    }

    .badge-success {
        background: rgba(34, 197, 94, 0.15);
        color: #86efac;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }

    .badge-warning {
        background: rgba(251, 146, 60, 0.15);
        color: #fed7aa;
        border: 1px solid rgba(251, 146, 60, 0.3);
    }

    .badge-danger {
        background: rgba(239, 68, 68, 0.15);
        color: #fca5a5;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    .insight-box {
        background: rgba(34, 197, 94, 0.08);
        border: 1px solid rgba(34, 197, 94, 0.2);
        border-radius: 12px;
        padding: 16px;
        color: #d1fae5;
        margin-bottom: 12px;
    }

    .warning-box {
        background: rgba(251, 146, 60, 0.08);
        border: 1px solid rgba(251, 146, 60, 0.2);
        border-radius: 12px;
        padding: 16px;
        color: #ffedd5;
        margin-bottom: 12px;
    }

    .critical-box {
        background: rgba(239, 68, 68, 0.08);
        border: 1px solid rgba(239, 68, 68, 0.2);
        border-radius: 12px;
        padding: 16px;
        color: #fecaca;
        margin-bottom: 12px;
    }

    div[data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(96, 165, 250, 0.15);
        padding: 16px;
        border-radius: 12px;
    }

    div[data-testid="stMetric"] label {
        color: #9ca3af !important;
        font-weight: 600 !important;
    }

    div[data-testid="stMetric"] > div:nth-child(2) {
        color: #60a5fa !important;
        font-size: 1.8rem !important;
        font-weight: 800 !important;
    }
</style>
""", unsafe_allow_html=True)


# =========================================================
# COLUMN DETECTION CONFIG
# =========================================================
COLUMN_SYNONYMS = {
    "Supplier_ID": [
        "supplier_id", "supplier id", "supplier.id", "supplierid", "id_supplier",
        "supplier number", "vendor_id", "vendor id", "vendorid", "id_vendor",
        "lieferant_id", "lieferanten id", "lieferantennummer"
    ],
    "Supplier_Name": [
        "supplier_name", "supplier name", "supplier.name", "supplier", "suppliername",
        "name_supplier", "vendor", "vendor_name", "vendor name", "vendorname",
        "lieferant", "lieferantenname", "lieferant name"
    ],
    "Country": [
        "country", "supplier_country", "vendor_country", "land", "region",
        "location", "supplier location", "vendor location"
    ],
    "Category": [
        "category", "material", "material_category", "material category",
        "commodity", "commodity group", "material group", "product group",
        "warengruppe", "produktgruppe", "category name"
    ],
    "Delivery_Performance_%": [
        "delivery_performance_%", "delivery performance", "delivery performance %",
        "delivery_performance", "on time delivery", "on-time delivery",
        "on_time_delivery", "otd", "otd%", "liefertreue", "lieferperformance",
        "delivery reliability", "delivery rate", "delivery score"
    ],
    "Lead_Time_Days": [
        "lead_time_days", "lead time days", "lead time", "leadtime",
        "delivery time", "delivery_time", "lieferzeit", "lieferzeit tage",
        "lead days", "lt days"
    ],
    "Quality_Score_%": [
        "quality_score_%", "quality score", "quality score %",
        "quality_score", "quality", "quality rate", "quality performance",
        "qualitätsrate", "qualitaetsrate", "quality %", "qualitypercent"
    ],
    "Complaint_Rate_%": [
        "complaint_rate_%", "complaint rate", "complaint rate %",
        "complaint_rate", "complaints", "complaint", "reklamationsquote",
        "defect rate", "claim rate", "claims", "defects"
    ],
    "Price_Deviation_%": [
        "price_deviation_%", "price deviation", "price deviation %",
        "price_deviation", "price variance", "price var", "price variation",
        "preisabweichung", "cost deviation", "cost variance"
    ],
    "Overall_Score": [
        "overall_score", "overall score", "score", "supplier score",
        "rating", "supplier rating", "bewertung", "gesamtbewertung",
        "performance score"
    ],
    "Status": [
        "status", "supplier status", "classification", "class", "klasse",
        "category status", "performance status"
    ],
    "Anomaly_Flag": [
        "anomaly_flag", "anomaly flag", "anomaly", "anomalie", "flag",
        "risk flag", "critical flag", "issue flag", "problem flag"
    ],
}


# =========================================================
# HELPER FUNCTIONS
# =========================================================
def normalize_text(value):
    """Lowercase and remove spaces, dots, underscores and special characters."""
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def clean_columns(df):
    """Clean dataframe column names."""
    df.columns = [str(c).strip() for c in df.columns]
    return df


def row_header_score(row_values):
    """
    Scores a potential header row.
    Higher score = row probably contains supplier/KPI column names.
    """
    score = 0
    normalized_cells = [normalize_text(x) for x in row_values if pd.notna(x)]

    for cell in normalized_cells:
        for synonyms in COLUMN_SYNONYMS.values():
            for synonym in synonyms:
                norm_syn = normalize_text(synonym)
                if cell == norm_syn:
                    score += 3
                elif norm_syn in cell or cell in norm_syn:
                    score += 2
                elif SequenceMatcher(None, cell, norm_syn).ratio() >= 0.82:
                    score += 1

    return score


def detect_header_row(uploaded_file, max_scan_rows=10):
    """
    Detects if the Excel file has a title row before the real header.
    Example:
    Row 1: Test Dataset 1 - Clean Supplier Data
    Row 2: Supplier_ID | Supplier_Name | Country | ...
    In that case this function detects row 2 as header.
    """
    uploaded_file.seek(0)

    preview = pd.read_excel(uploaded_file, header=None, nrows=max_scan_rows)
    best_row = 0
    best_score = -1

    for i in range(len(preview)):
        score = row_header_score(preview.iloc[i].tolist())
        if score > best_score:
            best_score = score
            best_row = i

    uploaded_file.seek(0)

    # If no useful header is detected, use first row as header.
    if best_score <= 0:
        return 0

    return best_row


def read_excel_smart(uploaded_file):
    """
    Reads Excel file with automatic header detection.
    """
    header_row = detect_header_row(uploaded_file)
    uploaded_file.seek(0)
    df = pd.read_excel(uploaded_file, header=header_row)
    df = clean_columns(df)

    # Remove completely empty rows/columns
    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")

    return df, header_row


def find_best_column(target_field, uploaded_columns, threshold=0.70):
    """
    Finds the best matching uploaded column for a required target field.
    Uses:
    1. exact match after normalization,
    2. contains match,
    3. fuzzy similarity.
    """
    synonyms = COLUMN_SYNONYMS.get(target_field, [])

    best_col = "-- Not available --"
    best_score = 0

    for col in uploaded_columns:
        norm_col = normalize_text(col)

        for synonym in synonyms:
            norm_syn = normalize_text(synonym)

            if norm_col == norm_syn:
                return col

            if norm_syn in norm_col or norm_col in norm_syn:
                score = 0.95
            else:
                score = SequenceMatcher(None, norm_col, norm_syn).ratio()

            if score > best_score:
                best_score = score
                best_col = col

    if best_score >= threshold:
        return best_col

    return "-- Not available --"


def to_numeric_safe(df, cols):
    """Convert KPI columns into numeric values."""
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def normalize_anomaly_flag(value):
    """Convert anomaly values like Yes/No, True/False, Ja/Nein into 1/0."""
    if pd.isna(value):
        return 0

    value = str(value).strip().lower()

    positive_values = {"yes", "ja", "y", "true", "1", "kritisch", "critical", "anomaly"}
    return 1 if value in positive_values else 0


def calculate_anomalies(row):
    """
    Counts KPI threshold violations.
    Threshold logic:
    - Delivery below 95% = anomaly
    - Lead time above 10 days = anomaly
    - Quality below 97% = anomaly
    - Complaint rate above 1% = anomaly
    - Absolute price deviation above 1% = anomaly
    """
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
    """
    Supplier score starts at 100.
    Penalty points are deducted when KPI values are below/above thresholds.
    """
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
    """Risk classification based on supplier score."""
    if score >= 90:
        return "Low"
    elif score >= 75:
        return "Medium"
    else:
        return "High"


def status_label(score):
    """Status label based on score."""
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Monitor"
    else:
        return "Critical"


def critical_kpi(row):
    """Find the KPI with the strongest negative deviation."""
    problems = {
        "Delivery": (95 - row["Liefertreue"]) if pd.notna(row.get("Liefertreue")) and row["Liefertreue"] < 95 else 0,
        "Lead Time": (row["Lieferzeit"] - 10) if pd.notna(row.get("Lieferzeit")) and row["Lieferzeit"] > 10 else 0,
        "Quality": (97 - row["Qualitätsrate"]) if pd.notna(row.get("Qualitätsrate")) and row["Qualitätsrate"] < 97 else 0,
        "Complaints": (row["Reklamationsquote"] - 1.0) if pd.notna(row.get("Reklamationsquote")) and row["Reklamationsquote"] > 1.0 else 0,
        "Price Dev.": (abs(row["Preisabweichung"]) - 1.0) if pd.notna(row.get("Preisabweichung")) and abs(row["Preisabweichung"]) > 1.0 else 0,
    }

    max_problem = max(problems, key=problems.get)
    return max_problem if problems[max_problem] > 0 else "None"


def supplier_strengths(row):
    """Generate short supplier strength text."""
    strengths = []

    if row["Liefertreue"] >= 95:
        strengths.append("strong delivery")
    if row["Qualitätsrate"] >= 97:
        strengths.append("excellent quality")
    if row["Lieferzeit"] <= 10:
        strengths.append("fast lead time")
    if row["Reklamationsquote"] <= 1.0:
        strengths.append("low complaints")
    if abs(row["Preisabweichung"]) <= 1.0:
        strengths.append("stable pricing")

    return ", ".join(strengths[:3]) if strengths else "mixed profile"


def score_color(score):
    if score >= 90:
        return "#22c55e"
    elif score >= 75:
        return "#f59e0b"
    else:
        return "#ef4444"


def donut_chart(value, color):
    fig = go.Figure(go.Pie(
        values=[value, max(0, 100 - value)],
        hole=0.72,
        marker_colors=[color, "rgba(148,163,184,0.1)"],
        textinfo="none",
        sort=False,
        hoverinfo="skip",
    ))

    fig.update_layout(
        showlegend=False,
        margin=dict(t=0, l=0, r=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        annotations=[dict(
            text=f"<b style='font-size:32px;color:{color}'>{value:.0f}</b><br>"
                 f"<span style='font-size:12px;color:#9ca3af'>out of 100</span>",
            x=0.5,
            y=0.5,
            showarrow=False,
            font_size=20,
        )],
    )

    return fig


def plotly_dark_layout(**kwargs):
    base = dict(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9ca3af"),
        margin=dict(t=40, b=40, l=40, r=40),
    )
    base.update(kwargs)
    return base


# =========================================================
# HEADER
# =========================================================
h1, h2 = st.columns([0.7, 0.3])

with h1:
    st.markdown('<div class="main-header">Supplier Evaluation Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="main-subtitle">🔍 Performance Analytics · Risk Assessment · KPI Monitoring</div>',
        unsafe_allow_html=True
    )

with h2:
    st.write("")
    st.markdown(
        f'<p style="text-align:right;color:#6b7280;font-size:0.9rem;">'
        f'Last updated: {datetime.now().strftime("%d.%m.%Y %H:%M")}</p>',
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


# Read Excel with automatic header detection
try:
    raw_df, detected_header_row = read_excel_smart(uploaded_file)
except Exception as e:
    st.error(f"Could not read the uploaded Excel file. Error: {e}")
    st.stop()


if raw_df.empty:
    st.error("The uploaded file is empty or could not be processed.")
    st.stop()


all_cols = ["-- Not available --"] + list(raw_df.columns)


def idx_auto(target_field):
    """
    Returns index for selectbox.
    Automatically detects the best matching uploaded column.
    """
    detected_col = find_best_column(target_field, raw_df.columns)

    if detected_col in all_cols:
        return all_cols.index(detected_col)

    return 0


# =========================================================
# SIDEBAR — COLUMN MAPPING
# =========================================================
with st.sidebar:
    st.markdown('<div class="section-title">🔗 Column Mapping</div>', unsafe_allow_html=True)

    if detected_header_row > 0:
        st.success(f"Header row automatically detected at Excel row {detected_header_row + 1}.")
    else:
        st.info("Header row detected at Excel row 1.")

    st.caption("Columns are auto-detected. Please review and correct if needed.")

    supplier_col = st.selectbox(
        "Supplier",
        all_cols,
        index=idx_auto("Supplier_Name")
    )

    country_col = st.selectbox(
        "Country",
        all_cols,
        index=idx_auto("Country")
    )

    material_col = st.selectbox(
        "Material / Category",
        all_cols,
        index=idx_auto("Category")
    )

    delivery_col = st.selectbox(
        "On-Time Delivery %",
        all_cols,
        index=idx_auto("Delivery_Performance_%")
    )

    leadtime_col = st.selectbox(
        "Lead Time (Days)",
        all_cols,
        index=idx_auto("Lead_Time_Days")
    )

    quality_col = st.selectbox(
        "Quality Score %",
        all_cols,
        index=idx_auto("Quality_Score_%")
    )

    complaint_col = st.selectbox(
        "Complaint Rate %",
        all_cols,
        index=idx_auto("Complaint_Rate_%")
    )

    price_col = st.selectbox(
        "Price Deviation %",
        all_cols,
        index=idx_auto("Price_Deviation_%")
    )

    score_col = st.selectbox(
        "Score (optional)",
        all_cols,
        index=idx_auto("Overall_Score")
    )

    status_col = st.selectbox(
        "Status (optional)",
        all_cols,
        index=idx_auto("Status")
    )

    anomaly_col = st.selectbox(
        "Anomaly Flag (optional)",
        all_cols,
        index=idx_auto("Anomaly_Flag")
    )

    supplier_id_col = st.selectbox(
        "Supplier ID (optional)",
        all_cols,
        index=idx_auto("Supplier_ID")
    )

    st.markdown("")
    load_data = st.button("📈 Load Dashboard", use_container_width=True)


if not load_data:
    st.info("Please review the automatic column mapping in the sidebar and click **Load Dashboard**.")
    st.stop()


# =========================================================
# VALIDATION AND DATAFRAME BUILDING
# =========================================================
required_map = {
    "Supplier": supplier_col,
    "Country": country_col,
    "Material": material_col,
    "Liefertreue": delivery_col,
    "Lieferzeit": leadtime_col,
    "Qualitätsrate": quality_col,
    "Reklamationsquote": complaint_col,
    "Preisabweichung": price_col,
}

missing = [k for k, v in required_map.items() if v == "-- Not available --"]

if missing:
    st.error(f"⚠️ Please map all required fields: {', '.join(missing)}")
    st.stop()


# Build mapping dictionary
mapping = {source_col: target_col for target_col, source_col in required_map.items()}

optional_map = {
    score_col: "Score",
    status_col: "Status",
    anomaly_col: "Anomaly_Flag",
    supplier_id_col: "Supplier_ID",
}

for source_col, target_col in optional_map.items():
    if source_col != "-- Not available --":
        mapping[source_col] = target_col


df = raw_df.rename(columns=mapping).copy()


# Remove columns not needed for the dashboard
needed_cols = list(set(list(required_map.keys()) + ["Score", "Status", "Anomaly_Flag", "Supplier_ID"]))
df = df[[c for c in df.columns if c in needed_cols]]


# Generate Supplier ID if missing
if "Supplier_ID" not in df.columns:
    df["Supplier_ID"] = [f"S{i+1:04d}" for i in range(len(df))]


# Convert KPI columns to numeric
df = to_numeric_safe(
    df,
    [
        "Liefertreue",
        "Lieferzeit",
        "Qualitätsrate",
        "Reklamationsquote",
        "Preisabweichung",
        "Score",
    ]
)


# Drop rows where required fields are missing
before_rows = len(df)
df = df.dropna(subset=list(required_map.keys()))
after_rows = len(df)
dropped_rows = before_rows - after_rows


if df.empty:
    st.error("No valid rows remain after removing rows with missing required KPI data.")
    st.stop()


# Calculate anomaly values
if "Anomaly_Flag" in df.columns:
    df["Anomalien"] = df["Anomaly_Flag"].apply(normalize_anomaly_flag)
else:
    df["Anomalien"] = df.apply(calculate_anomalies, axis=1)


# Calculate score if missing
if "Score" not in df.columns:
    df["Score"] = df.apply(calculate_score, axis=1)
else:
    df["Score"] = df["Score"].fillna(df.apply(calculate_score, axis=1))


# Calculate status if missing
if "Status" not in df.columns:
    df["Status"] = df["Score"].apply(status_label)
else:
    df["Status"] = df["Status"].fillna(df["Score"].apply(status_label))


# Additional calculated fields
df["Risk"] = df["Score"].apply(risk_level)
df["Crit_KPI"] = df.apply(critical_kpi, axis=1)
df["Strengths"] = df.apply(supplier_strengths, axis=1)


# Supplier-level aggregation
agg = (
    df.groupby("Supplier", as_index=False)
    .agg({
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
        "Risk": "first",
        "Crit_KPI": "first",
        "Strengths": "first",
    })
    .sort_values("Score", ascending=False)
    .reset_index(drop=True)
)

agg["Score"] = agg["Score"].round(1)


# =========================================================
# SIDEBAR — FILTERS
# =========================================================
with st.sidebar:
    st.markdown('<div class="section-title" style="margin-top:2rem;">🎯 Filters</div>', unsafe_allow_html=True)

    materials = ["All"] + sorted(agg["Material"].astype(str).dropna().unique().tolist())
    sel_mat = st.selectbox("Material Category", materials)

    filtered = agg if sel_mat == "All" else agg[agg["Material"].astype(str) == sel_mat]

    if filtered.empty:
        st.warning("No suppliers available for the selected filter.")
        st.stop()

    sel_sup = st.selectbox("Select Supplier", filtered["Supplier"].tolist())


sel = filtered[filtered["Supplier"] == sel_sup].iloc[0]


# =========================================================
# DATA PROCESSING SUMMARY
# =========================================================
with st.expander("Data processing summary"):
    st.write(f"Detected header row: Excel row {detected_header_row + 1}")
    st.write(f"Original rows: {before_rows}")
    st.write(f"Valid rows after cleaning: {after_rows}")
    st.write(f"Rows removed due to missing required data: {dropped_rows}")
    st.write("Applied column mapping:")
    st.json(mapping)


# =========================================================
# TOP KPI CARDS
# =========================================================
st.markdown("")

kpi_cards = [
    ("📦", "Suppliers", filtered["Supplier"].nunique(), "in portfolio"),
    ("⭐", "Avg Score", f"{filtered['Score'].mean():.1f}", "overall rating"),
    ("⚠️", "Anomalies", int(filtered["Anomalien"].sum()), "detected"),
    ("📂", "Top Material", filtered["Material"].mode().iloc[0] if not filtered.empty else "-", "category"),
    ("🏆", "Top Supplier", filtered.iloc[0]["Supplier"] if not filtered.empty else "-", "highest score"),
]

for col, (icon, label, value, sub) in zip(st.columns(5), kpi_cards):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size:1.5rem;margin-bottom:8px;">{icon}</div>
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{sub}</div>
        </div>
        """, unsafe_allow_html=True)


st.markdown("")


# =========================================================
# DASHBOARD TABS
# =========================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Overview", "🎯 Rankings & Insights", "📈 Analytics", "👤 Supplier Profile", "📋 Details"]
)


# =========================================================
# TAB 1 — OVERVIEW
# =========================================================
with tab1:
    c_left, c_mid, c_right = st.columns([1.2, 1.3, 0.95])

    with c_left:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🏆 Top Suppliers</div>', unsafe_allow_html=True)

        for rank, (_, row) in enumerate(filtered.head(6).iterrows(), 1):
            badge_type = "success" if row["Score"] >= 90 else "warning" if row["Score"] >= 75 else "danger"

            anomaly_badge = (
                f'<span class="badge badge-danger">⚠️ {int(row["Anomalien"])} Anomalies</span>'
                if row["Anomalien"] > 0
                else '<span class="badge badge-success">✓ No Issues</span>'
            )

            st.markdown(f"""
            <div class="supplier-item">
                <div style="display:flex;justify-content:space-between;align-items:start;">
                    <div>
                        <div class="supplier-name">#{rank} {row['Supplier']}</div>
                        <div class="supplier-meta">{row['Material']} · {row['Country']}</div>
                    </div>
                    <span class="badge badge-{badge_type}" style="font-size:0.9rem;font-weight:700;">
                        {row['Score']}
                    </span>
                </div>
                <div style="margin-top:8px;">{anomaly_badge}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with c_mid:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="section-title">📍 {sel["Supplier"]}</div>', unsafe_allow_html=True)

        ca, cb = st.columns(2)

        with ca:
            st.metric("ID", sel["Supplier_ID"])
            st.metric("Category", sel["Material"])

        with cb:
            st.metric("Country", sel["Country"])
            st.metric("Status", sel["Status"])

        st.write("")

        cc, cd = st.columns(2)
        ce, cf = st.columns(2)

        with cc:
            st.metric("On-Time Delivery", f"{sel['Liefertreue']:.1f}%", f"{sel['Liefertreue'] - 95:.1f}%")
        with cd:
            st.metric("Quality Score", f"{sel['Qualitätsrate']:.1f}%", f"{sel['Qualitätsrate'] - 97:.1f}%")
        with ce:
            st.metric("Lead Time", f"{sel['Lieferzeit']:.1f} d", f"{sel['Lieferzeit'] - 10:.1f} d")
        with cf:
            st.metric("Complaint Rate", f"{sel['Reklamationsquote']:.2f}%", f"{sel['Reklamationsquote'] - 1.0:.2f}%")

        st.markdown('</div>', unsafe_allow_html=True)

    with c_right:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🎯 Overall Score</div>', unsafe_allow_html=True)

        st.plotly_chart(
            donut_chart(sel["Score"], score_color(sel["Score"])),
            use_container_width=True,
            config={"displayModeBar": False}
        )

        risk_cls = "badge-success" if sel["Risk"] == "Low" else "badge-warning" if sel["Risk"] == "Medium" else "badge-danger"

        st.markdown(
            f'<span class="badge {risk_cls}" style="font-size:0.9rem;">Risk: {sel["Risk"]}</span>',
            unsafe_allow_html=True
        )

        st.write("")
        st.markdown(f"**Critical KPI:** {sel['Crit_KPI']}")
        st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# TAB 2 — RANKINGS AND INSIGHTS
# =========================================================
with tab2:
    c_rank, c_ins = st.columns([1.2, 0.95])

    with c_rank:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📊 Supplier Ranking</div>', unsafe_allow_html=True)

        rank_df = filtered[["Supplier", "Material", "Country", "Score", "Anomalien", "Risk"]].sort_values("Score", ascending=False).copy()
        rank_df.insert(0, "Rank", range(1, len(rank_df) + 1))

        st.dataframe(rank_df, use_container_width=True, hide_index=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with c_ins:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">💡 Key Insights</div>', unsafe_allow_html=True)

        for i, (_, row) in enumerate(filtered.head(3).iterrows(), 1):
            st.markdown(f"""
            <div class="insight-box">
                <b>Top {i}: {row['Supplier']}</b><br>
                <span style="font-size:0.9rem;">Score: {row['Score']} | {row['Material']} | {row['Country']}</span><br>
                <span style="font-size:0.85rem;opacity:0.9;">Strengths: {row['Strengths']}</span>
            </div>
            """, unsafe_allow_html=True)

        for _, row in filtered.sort_values("Score").head(2).iterrows():
            st.markdown(f"""
            <div class="warning-box">
                <b>⚠️ Attention: {row['Supplier']}</b><br>
                <span style="font-size:0.9rem;">Critical: {row['Crit_KPI']} | Score: {row['Score']}</span><br>
                <span style="font-size:0.85rem;opacity:0.9;">Action: Monitor performance closely.</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# TAB 3 — ANALYTICS
# =========================================================
with tab3:
    r1c1, r1c2 = st.columns(2)

    with r1c1:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)

        fig = px.bar(
            filtered.sort_values("Score", ascending=False),
            x="Supplier",
            y="Score",
            color="Score",
            title="Supplier Ranking by Score",
            color_continuous_scale="Viridis",
        )

        fig.update_traces(marker_line_width=0)
        fig.update_layout(**plotly_dark_layout(title_font_size=14))

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="premium-card">', unsafe_allow_html=True)

        mat = filtered["Material"].value_counts().reset_index()
        mat.columns = ["Material", "Count"]

        fig2 = px.pie(
            mat,
            names="Material",
            values="Count",
            hole=0.5,
            title="Material Distribution",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )

        fig2.update_layout(**plotly_dark_layout(title_font_size=14))

        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    with r1c2:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)

        fig3 = px.scatter(
            filtered,
            x="Liefertreue",
            y="Qualitätsrate",
            size="Score",
            color="Score",
            hover_name="Supplier",
            title="Delivery Reliability vs Quality",
            color_continuous_scale="Plasma",
        )

        fig3.update_layout(**plotly_dark_layout(title_font_size=14))

        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="premium-card">', unsafe_allow_html=True)

        ano_df = filtered.copy()
        ano_df["AnomalyStatus"] = np.where(ano_df["Anomalien"] > 0, "Has Anomalies", "Clean")
        ano_share = ano_df["AnomalyStatus"].value_counts().reset_index()
        ano_share.columns = ["Status", "Count"]

        fig4 = px.pie(
            ano_share,
            names="Status",
            values="Count",
            hole=0.6,
            title="Anomaly Distribution",
            color_discrete_sequence=["#ef4444", "#22c55e"],
        )

        fig4.update_layout(**plotly_dark_layout(title_font_size=14))

        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    r2c1, r2c2 = st.columns(2)

    with r2c1:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)

        fig5 = px.bar(
            filtered.sort_values("Lieferzeit"),
            x="Supplier",
            y="Lieferzeit",
            color="Lieferzeit",
            title="Lead Time Comparison",
            color_continuous_scale="Blues_r",
        )

        fig5.update_traces(marker_line_width=0)
        fig5.update_layout(**plotly_dark_layout(title_font_size=14))

        st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    with r2c2:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)

        fig6 = px.bar(
            filtered.sort_values("Reklamationsquote", ascending=False),
            x="Supplier",
            y="Reklamationsquote",
            color="Reklamationsquote",
            title="Complaint Rate Comparison",
            color_continuous_scale="Reds_r",
        )

        fig6.update_traces(marker_line_width=0)
        fig6.update_layout(**plotly_dark_layout(title_font_size=14))

        st.plotly_chart(fig6, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# TAB 4 — SUPPLIER PROFILE
# =========================================================
with tab4:
    cp1, cp2 = st.columns([1.1, 1.1])

    with cp1:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">👤 Supplier Profile</div>', unsafe_allow_html=True)

        st.markdown(f"""
**Supplier ID:** {sel['Supplier_ID']}  
**Supplier Name:** {sel['Supplier']}  
**Category:** {sel['Material']}  
**Country:** {sel['Country']}  
**Status:** {sel['Status']}  
**Risk Level:** {sel['Risk']}  
**Critical KPI:** {sel['Crit_KPI']}  
        """)

        st.markdown('</div>', unsafe_allow_html=True)

        if sel["Score"] >= 90:
            st.markdown(
                f'<div class="insight-box"><b>✅ Recommendation</b><br>'
                f'{sel["Supplier"]} is a preferred supplier. Strengths: {sel["Strengths"]}</div>',
                unsafe_allow_html=True
            )
        elif sel["Score"] >= 75:
            st.markdown(
                f'<div class="warning-box"><b>⚠️ Recommendation</b><br>'
                f'Monitor <b>{sel["Crit_KPI"]}</b> closely. Supplier is usable but requires oversight.</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="critical-box"><b>🔴 Critical</b><br>'
                f'Focus on <b>{sel["Crit_KPI"]}</b>. Consider alternative suppliers.</div>',
                unsafe_allow_html=True
            )

    with cp2:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📊 KPI Profile</div>', unsafe_allow_html=True)

        fig_p = go.Figure(go.Bar(
            x=["Delivery", "Quality", "Complaints", "Price Var.", "Lead Time"],
            y=[
                sel["Liefertreue"],
                sel["Qualitätsrate"],
                sel["Reklamationsquote"],
                abs(sel["Preisabweichung"]),
                sel["Lieferzeit"],
            ],
            marker=dict(
                color=["#22c55e", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6"],
                line=dict(width=0)
            ),
            hovertemplate="<b>%{x}</b><br>Value: %{y:.1f}<extra></extra>",
        ))

        fig_p.update_layout(
            title="KPI Performance Profile",
            showlegend=False,
            **plotly_dark_layout(title_font_size=14)
        )

        st.plotly_chart(fig_p, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# TAB 5 — DETAILS
# =========================================================
with tab5:
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📋 Complete Data View</div>', unsafe_allow_html=True)

    detail_cols = [
        "Supplier",
        "Supplier_ID",
        "Material",
        "Country",
        "Liefertreue",
        "Lieferzeit",
        "Qualitätsrate",
        "Reklamationsquote",
        "Preisabweichung",
        "Score",
        "Anomalien",
        "Status",
        "Risk",
        "Crit_KPI",
    ]

    display_cols = [c for c in detail_cols if c in agg.columns]
    st.dataframe(agg[display_cols].round(2), use_container_width=True, hide_index=True)

    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.markdown("""
<div style='text-align:center;color:#6b7280;font-size:0.85rem;margin-top:2rem;'>
    Supplier Evaluation Dashboard · Enterprise Edition<br>
    Built with Streamlit | Powered by Advanced Analytics
</div>
""", unsafe_allow_html=True)
