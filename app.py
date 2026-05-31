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
    .main-header {
        font-size: 3rem; font-weight: 900;
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 50%, #2563eb 100%);
        background-clip: text; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem; letter-spacing: -0.03em; line-height: 1.1;
    }
    .main-subtitle {
        font-size: 0.95rem; color: #9ca3af; font-weight: 500; margin-bottom: 2rem;
        letter-spacing: 0.05em; text-transform: uppercase;
    }
    .metric-card {
        background: linear-gradient(135deg, rgba(30,41,59,0.5) 0%, rgba(25,35,50,0.3) 100%);
        border: 1px solid rgba(96,165,250,0.15); border-radius: 14px;
        padding: 20px; min-height: 140px; box-shadow: 0 6px 24px rgba(0,0,0,0.25);
    }
    .metric-label { font-size: 0.85rem; color: #9ca3af; font-weight: 600; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.08em; }
    .metric-value { font-size: 2rem; font-weight: 800; color: #60a5fa; line-height: 1.2; }
    .metric-sub { margin-top: 12px; color: #6b7280; font-size: 0.82rem; font-weight: 500; }
    .premium-card {
        background: linear-gradient(135deg, rgba(30,41,59,0.6) 0%, rgba(25,35,50,0.4) 100%);
        border: 1px solid rgba(148,163,184,0.12); border-radius: 16px;
        padding: 22px; box-shadow: 0 8px 32px rgba(0,0,0,0.3); margin-bottom: 16px;
    }
    .section-title { font-size: 1.25rem; font-weight: 800; color: #f1f5f9; margin-bottom: 18px; }
    .supplier-item {
        background: rgba(30,41,59,0.4); border: 1px solid rgba(96,165,250,0.1);
        border-radius: 12px; padding: 16px; margin-bottom: 12px;
    }
    .supplier-name { font-weight: 700; color: #f1f5f9; font-size: 1.05rem; margin-bottom: 6px; }
    .supplier-meta { color: #9ca3af; font-size: 0.85rem; font-weight: 500; }
    .badge { display: inline-block; padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; margin-right: 6px; margin-bottom: 4px; }
    .badge-success { background: rgba(34,197,94,0.15); color: #86efac; border: 1px solid rgba(34,197,94,0.3); }
    .badge-warning { background: rgba(251,146,60,0.15); color: #fed7aa; border: 1px solid rgba(251,146,60,0.3); }
    .badge-danger  { background: rgba(239,68,68,0.15);  color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); }
    .insight-box  { background: rgba(34,197,94,0.08);  border: 1px solid rgba(34,197,94,0.2);  border-radius: 12px; padding: 16px; color: #d1fae5; margin-bottom: 12px; }
    .warning-box  { background: rgba(251,146,60,0.08); border: 1px solid rgba(251,146,60,0.2); border-radius: 12px; padding: 16px; color: #ffedd5; margin-bottom: 12px; }
    .critical-box { background: rgba(239,68,68,0.08);  border: 1px solid rgba(239,68,68,0.2);  border-radius: 12px; padding: 16px; color: #fecaca; margin-bottom: 12px; }
    div[data-testid="stMetric"] { background: rgba(30,41,59,0.5); border: 1px solid rgba(96,165,250,0.15); padding: 16px; border-radius: 12px; }
    div[data-testid="stMetric"] label { color: #9ca3af !important; font-weight: 600 !important; }
    div[data-testid="stMetric"] > div:nth-child(2) { color: #60a5fa !important; font-size: 1.8rem !important; font-weight: 800 !important; }
    .detect-badge { background: rgba(96,165,250,0.12); border: 1px solid rgba(96,165,250,0.25); border-radius: 8px; padding: 4px 10px; font-size: 0.78rem; color: #93c5fd; margin-left: 6px; }
</style>
""", unsafe_allow_html=True)


# =========================================================
# COLUMN SYNONYM REGISTRY
# Every possible variant a real-world Excel might use
# =========================================================
COLUMN_SYNONYMS = {
    "Supplier_ID": [
        "supplier_id","supplier id","supplierid","supplier.id","id_supplier",
        "supplier number","vendor_id","vendor id","vendorid","id_vendor",
        "lieferant_id","lieferanten id","lieferantennummer","lieferantnr",
        "sup id","sup_id","supp_id","supplier nr","lieferant nr",
    ],
    "Supplier_Name": [
        "supplier_name","supplier name","supplier.name","supplier","suppliername",
        "name_supplier","vendor","vendor_name","vendor name","vendorname",
        "lieferant","lieferantenname","lieferant name","company","company name",
        "firm","firma","name","sup name","supp name",
    ],
    "Country": [
        "country","supplier_country","vendor_country","land","region",
        "location","supplier location","vendor location","herkunftsland",
        "origin","origin country","lieferantenland","nation",
    ],
    "Category": [
        "category","material","material_category","material category",
        "commodity","commodity group","material group","product group",
        "warengruppe","produktgruppe","category name","kategorie",
        "materialgruppe","type","product type","segment",
    ],
    "Delivery_Performance_%": [
        "delivery_performance_%","delivery performance %","delivery performance",
        "delivery_performance","on time delivery","on-time delivery",
        "on_time_delivery","otd","otd%","liefertreue","lieferperformance",
        "delivery reliability","delivery rate","delivery score","deliveryperformance",
        "pünktlichkeit","punctuality","termintreue","on time %","delivery %",
    ],
    "Lead_Time_Days": [
        "lead_time_days","lead time days","lead time","leadtime",
        "delivery time","delivery_time","lieferzeit","lieferzeit tage",
        "lead days","lt days","lt","days","tage","vorlaufzeit","turnaround",
    ],
    "Quality_Score_%": [
        "quality_score_%","quality score %","quality score",
        "quality_score","quality","quality rate","quality performance",
        "qualitätsrate","qualitaetsrate","quality %","qualitypercent",
        "qualität","qualitaet","q score","defect free rate","good parts %",
    ],
    "Complaint_Rate_%": [
        "complaint_rate_%","complaint rate %","complaint rate",
        "complaint_rate","complaints","complaint","reklamationsquote",
        "defect rate","claim rate","claims","defects","reklamationen",
        "beanstandungen","fehlerquote","rejection rate","return rate",
    ],
    "Price_Deviation_%": [
        "price_deviation_%","price deviation %","price deviation",
        "price_deviation","price variance","price var","price variation",
        "preisabweichung","cost deviation","cost variance","preisvarianz",
        "price diff","price difference","cost diff","preisdifferenz",
    ],
    "Overall_Score": [
        "overall_score","overall score","score","supplier score",
        "rating","supplier rating","bewertung","gesamtbewertung",
        "performance score","total score","final score","kpi score",
        "gesamtscore","gesamtbewertung","punkte","points",
    ],
    "Status": [
        "status","supplier status","classification","class","klasse",
        "category status","performance status","bewertungsstatus",
        "einstufung","tier","supplier tier","level",
    ],
    "Anomaly_Flag": [
        "anomaly_flag","anomaly flag","anomaly","anomalie","flag",
        "risk flag","critical flag","issue flag","problem flag",
        "auffälligkeit","warnung","alert","warning","critical","risk",
    ],
}

NA = "-- Not available --"


# =========================================================
# DETECTION ENGINE
# =========================================================
def normalize(s):
    """Lowercase, strip everything except alphanumeric."""
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


def score_row_as_header(row_values):
    """
    Score a single Excel row as a potential header row.
    Returns (total_score, number_of_matched_fields).
    The row with the highest score is chosen as the header.
    """
    matched_fields = set()
    total_score = 0

    for cell in row_values:
        if pd.isna(cell):
            continue
        norm_cell = normalize(str(cell))
        if not norm_cell:
            continue

        for field, synonyms in COLUMN_SYNONYMS.items():
            if field in matched_fields:
                continue
            for syn in synonyms:
                norm_syn = normalize(syn)
                if norm_cell == norm_syn:
                    total_score += 10
                    matched_fields.add(field)
                    break
                elif norm_syn in norm_cell or norm_cell in norm_syn:
                    total_score += 6
                    matched_fields.add(field)
                    break
                elif similarity(norm_cell, norm_syn) >= 0.82:
                    total_score += 3
                    matched_fields.add(field)
                    break

    return total_score, len(matched_fields)


def detect_header_row(uploaded_file, max_scan_rows=20):
    """
    Scans up to max_scan_rows rows to find the real header row.
    Works even if the file has:
    - Title rows before the header
    - Empty rows at the top
    - Notes/metadata rows
    Returns (header_row_index, score, matched_fields_count).
    """
    uploaded_file.seek(0)
    preview = pd.read_excel(uploaded_file, header=None, nrows=max_scan_rows)

    best_row = 0
    best_score = -1
    best_matches = 0

    for i in range(len(preview)):
        row_vals = preview.iloc[i].tolist()
        score, matches = score_row_as_header(row_vals)
        if score > best_score:
            best_score = score
            best_row = i
            best_matches = matches

    uploaded_file.seek(0)
    return best_row, best_score, best_matches


def read_all_sheets(uploaded_file):
    """
    Read all sheets in the workbook.
    For each sheet, auto-detect the header row.
    Returns list of (sheet_name, dataframe, header_row, score, matches).
    """
    uploaded_file.seek(0)
    xl = pd.ExcelFile(uploaded_file)
    sheets = []

    for sheet_name in xl.sheet_names:
        uploaded_file.seek(0)
        try:
            preview = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=None, nrows=20)
            if preview.empty:
                continue

            best_row, best_score, best_matches = 0, -1, 0
            for i in range(len(preview)):
                score, matches = score_row_as_header(preview.iloc[i].tolist())
                if score > best_score:
                    best_score = score
                    best_row = i
                    best_matches = matches

            uploaded_file.seek(0)
            df = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=best_row)
            df.columns = [str(c).strip() for c in df.columns]
            df = df.dropna(how="all").dropna(axis=1, how="all")

            if not df.empty:
                sheets.append((sheet_name, df, best_row, best_score, best_matches))
        except Exception:
            continue

    return sheets


def find_best_column(target_field, uploaded_columns, threshold=0.55):
    """
    Finds best matching uploaded column for a target field.
    Priority: exact → contains → fuzzy.
    Lowered threshold to 0.55 for broader matching.
    """
    synonyms = COLUMN_SYNONYMS.get(target_field, [target_field])
    norm_synonyms = [normalize(s) for s in synonyms]

    best_col = NA
    best_score = 0.0

    for col in uploaded_columns:
        norm_col = normalize(col)
        for norm_syn in norm_synonyms:
            if norm_col == norm_syn:
                return col  # Perfect match → return immediately
            if norm_syn in norm_col or norm_col in norm_syn:
                score = 0.92
            else:
                score = similarity(norm_col, norm_syn)
            if score > best_score:
                best_score = score
                best_col = col

    return best_col if best_score >= threshold else NA


def auto_map_columns(df_columns):
    """Auto-map all known target fields to best matching uploaded columns."""
    return {field: find_best_column(field, df_columns) for field in COLUMN_SYNONYMS}


def merge_related_tables(sheets):
    """
    Attempt to merge sheets that appear related via a common key column.
    For example: main supplier table + country lookup table joined on Supplier_ID.
    Returns a merged dataframe.
    """
    if not sheets:
        return None

    # Score each sheet by how many KPI columns it has
    def kpi_count(df):
        kpi_fields = ["Delivery_Performance_%", "Lead_Time_Days", "Quality_Score_%",
                      "Complaint_Rate_%", "Price_Deviation_%"]
        return sum(1 for f in kpi_fields if find_best_column(f, df.columns) != NA)

    # Pick the sheet with the most KPI matches as primary
    primary_sheet = max(sheets, key=lambda s: (kpi_count(s[1]), s[3]))
    primary_name, primary_df = primary_sheet[0], primary_sheet[1].copy()

    if len(sheets) == 1:
        return primary_df, primary_name, []

    merge_log = []

    for sheet_name, df, _, _, _ in sheets:
        if sheet_name == primary_sheet[0]:
            continue

        # Find common key between primary and this sheet
        primary_mapping = auto_map_columns(primary_df.columns)
        secondary_mapping = auto_map_columns(df.columns)

        # Try joining on Supplier_ID or Supplier_Name
        for key_field in ["Supplier_ID", "Supplier_Name"]:
            primary_key = primary_mapping.get(key_field, NA)
            secondary_key = secondary_mapping.get(key_field, NA)

            if primary_key != NA and secondary_key != NA:
                try:
                    # Only bring in columns not already in primary
                    new_cols = [secondary_key] + [
                        c for c in df.columns
                        if c != secondary_key and normalize(c) not in [normalize(p) for p in primary_df.columns]
                    ]
                    merged = primary_df.merge(
                        df[new_cols],
                        left_on=primary_key,
                        right_on=secondary_key,
                        how="left",
                        suffixes=("", f"_{sheet_name}")
                    )
                    primary_df = merged
                    merge_log.append(f"Merged sheet '{sheet_name}' on {key_field}")
                    break
                except Exception as e:
                    merge_log.append(f"Could not merge '{sheet_name}': {e}")

    return primary_df, primary_sheet[0], merge_log


# =========================================================
# KPI CALCULATION HELPERS
# =========================================================
def to_numeric_safe(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def normalize_anomaly_flag(value):
    if pd.isna(value):
        return 0
    return 1 if str(value).strip().lower() in {"yes","ja","y","true","1","kritisch","critical","anomaly"} else 0


def calculate_anomalies(row):
    count = 0
    if pd.notna(row.get("Liefertreue")) and row["Liefertreue"] < 95: count += 1
    if pd.notna(row.get("Lieferzeit")) and row["Lieferzeit"] > 10: count += 1
    if pd.notna(row.get("Qualitätsrate")) and row["Qualitätsrate"] < 97: count += 1
    if pd.notna(row.get("Reklamationsquote")) and row["Reklamationsquote"] > 1.0: count += 1
    if pd.notna(row.get("Preisabweichung")) and abs(row["Preisabweichung"]) > 1.0: count += 1
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
    return "Low" if score >= 90 else "Medium" if score >= 75 else "High"

def status_label(score):
    return "Excellent" if score >= 90 else "Monitor" if score >= 75 else "Critical"

def critical_kpi(row):
    problems = {
        "Delivery":   (95 - row["Liefertreue"])         if pd.notna(row.get("Liefertreue"))     and row["Liefertreue"] < 95          else 0,
        "Lead Time":  (row["Lieferzeit"] - 10)          if pd.notna(row.get("Lieferzeit"))       and row["Lieferzeit"] > 10           else 0,
        "Quality":    (97 - row["Qualitätsrate"])        if pd.notna(row.get("Qualitätsrate"))    and row["Qualitätsrate"] < 97        else 0,
        "Complaints": (row["Reklamationsquote"] - 1.0)  if pd.notna(row.get("Reklamationsquote")) and row["Reklamationsquote"] > 1.0  else 0,
        "Price Dev.": (abs(row["Preisabweichung"]) - 1) if pd.notna(row.get("Preisabweichung"))  and abs(row["Preisabweichung"]) > 1  else 0,
    }
    mx = max(problems, key=problems.get)
    return mx if problems[mx] > 0 else "None"

def supplier_strengths(row):
    s = []
    if row["Liefertreue"] >= 95:      s.append("strong delivery")
    if row["Qualitätsrate"] >= 97:    s.append("excellent quality")
    if row["Lieferzeit"] <= 10:       s.append("fast lead time")
    if row["Reklamationsquote"] <= 1: s.append("low complaints")
    if abs(row["Preisabweichung"]) <= 1: s.append("stable pricing")
    return ", ".join(s[:3]) if s else "mixed profile"

def score_color(score):
    return "#22c55e" if score >= 90 else "#f59e0b" if score >= 75 else "#ef4444"


# =========================================================
# CHARTS
# =========================================================
def donut_chart(value, color):
    fig = go.Figure(go.Pie(
        values=[value, max(0, 100 - value)],
        hole=0.72,
        marker_colors=[color, "rgba(148,163,184,0.1)"],
        textinfo="none", sort=False, hoverinfo="skip",
    ))
    fig.update_layout(
        showlegend=False, margin=dict(t=0,l=0,r=0,b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        annotations=[dict(
            text=f"<b style='font-size:32px;color:{color}'>{value:.0f}</b><br>"
                 f"<span style='font-size:12px;color:#9ca3af'>out of 100</span>",
            x=0.5, y=0.5, showarrow=False, font_size=20,
        )],
    )
    return fig

def plotly_dark(**kwargs):
    base = dict(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9ca3af"), margin=dict(t=40,b=40,l=40,r=40),
    )
    base.update(kwargs)
    return base


# =========================================================
# HEADER
# =========================================================
h1, h2 = st.columns([0.7, 0.3])
with h1:
    st.markdown('<div class="main-header">Supplier Evaluation Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-subtitle">🔍 Performance Analytics · Risk Assessment · KPI Monitoring</div>', unsafe_allow_html=True)
with h2:
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
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx","xls"])

if uploaded_file is None:
    st.info("👈 Please upload an Excel file in the sidebar to get started.")
    st.stop()


# =========================================================
# READ AND DETECT ALL SHEETS
# =========================================================
try:
    sheets = read_all_sheets(uploaded_file)
except Exception as e:
    st.error(f"Could not read the uploaded Excel file: {e}")
    st.stop()

if not sheets:
    st.error("No readable data found in the uploaded file.")
    st.stop()

# Merge related tables across sheets
merged_df, primary_sheet_name, merge_log = merge_related_tables(sheets)

if merged_df is None or merged_df.empty:
    st.error("Could not build a usable dataset from the uploaded file.")
    st.stop()

# Auto-map columns
auto_mapping = auto_map_columns(merged_df.columns)
all_cols = [NA] + list(merged_df.columns)

def idx(field):
    detected = auto_mapping.get(field, NA)
    return all_cols.index(detected) if detected in all_cols else 0

def conf_badge(field):
    col = auto_mapping.get(field, NA)
    return "" if col == NA else "✓"


# =========================================================
# SIDEBAR — DETECTION SUMMARY + COLUMN MAPPING
# =========================================================
with st.sidebar:
    st.markdown('<div class="section-title">🔎 Detection Summary</div>', unsafe_allow_html=True)

    total_sheets = len(sheets)
    st.success(f"📄 {total_sheets} sheet(s) detected")

    for sname, sdf, hrow, hscore, hmatches in sheets:
        label = "⭐ Primary" if sname == primary_sheet_name else "🔗 Secondary"
        st.markdown(
            f"<small><b>{label}:</b> {sname}<br>"
            f"Header @ row {hrow+1} · {hmatches} fields matched</small>",
            unsafe_allow_html=True
        )

    if merge_log:
        for msg in merge_log:
            st.info(f"🔀 {msg}")

    mapped_count = sum(1 for v in auto_mapping.values() if v != NA)
    total_fields = len(COLUMN_SYNONYMS)
    pct = int(mapped_count / total_fields * 100)
    bar_color = "#22c55e" if pct >= 80 else "#f59e0b" if pct >= 50 else "#ef4444"
    st.markdown(
        f"<div style='margin:8px 0;'>"
        f"<div style='font-size:0.8rem;color:#9ca3af;margin-bottom:4px;'>Auto-mapping: {mapped_count}/{total_fields} fields ({pct}%)</div>"
        f"<div style='background:rgba(255,255,255,0.08);border-radius:6px;height:8px;'>"
        f"<div style='background:{bar_color};width:{pct}%;height:8px;border-radius:6px;'></div>"
        f"</div></div>",
        unsafe_allow_html=True
    )

    st.markdown('<div class="section-title" style="margin-top:1.5rem;">🔗 Column Mapping</div>', unsafe_allow_html=True)
    st.caption("Auto-detected. Correct if needed.")

    supplier_col  = st.selectbox("Supplier",            all_cols, index=idx("Supplier_Name"))
    country_col   = st.selectbox("Country",             all_cols, index=idx("Country"))
    material_col  = st.selectbox("Material / Category", all_cols, index=idx("Category"))
    delivery_col  = st.selectbox("On-Time Delivery %",  all_cols, index=idx("Delivery_Performance_%"))
    leadtime_col  = st.selectbox("Lead Time (Days)",    all_cols, index=idx("Lead_Time_Days"))
    quality_col   = st.selectbox("Quality Score %",     all_cols, index=idx("Quality_Score_%"))
    complaint_col = st.selectbox("Complaint Rate %",    all_cols, index=idx("Complaint_Rate_%"))
    price_col     = st.selectbox("Price Deviation %",   all_cols, index=idx("Price_Deviation_%"))
    score_col     = st.selectbox("Score (optional)",    all_cols, index=idx("Overall_Score"))
    status_col    = st.selectbox("Status (optional)",   all_cols, index=idx("Status"))
    anomaly_col   = st.selectbox("Anomaly Flag (opt.)", all_cols, index=idx("Anomaly_Flag"))
    supplier_id_col = st.selectbox("Supplier ID (opt.)",all_cols, index=idx("Supplier_ID"))

    st.markdown("")
    load_data = st.button("📈 Load Dashboard", use_container_width=True)

if not load_data:
    # Show preview of what was detected
    st.markdown("### 🔎 Auto-Detection Preview")
    cols_preview = st.columns(3)
    fields_display = [
        ("Supplier", supplier_col), ("Country", country_col), ("Category", material_col),
        ("Delivery %", delivery_col), ("Lead Time", leadtime_col), ("Quality %", quality_col),
        ("Complaint %", complaint_col), ("Price Dev.", price_col), ("Score", score_col),
    ]
    for i, (label, col) in enumerate(fields_display):
        with cols_preview[i % 3]:
            ok = col != NA
            st.markdown(
                f"<div style='background:rgba(30,41,59,0.5);border:1px solid rgba(96,165,250,0.1);border-radius:8px;padding:10px;margin-bottom:8px;'>"
                f"<div style='font-size:0.75rem;color:#9ca3af;'>{label}</div>"
                f"<div style='font-size:0.9rem;color:{'#86efac' if ok else '#fca5a5'};font-weight:600;'>{'✓ ' if ok else '✗ '}{col if ok else 'Not found'}</div>"
                f"</div>",
                unsafe_allow_html=True
            )
    st.info("Review the auto-mapping above and click **Load Dashboard** in the sidebar.")
    st.stop()


# =========================================================
# BUILD DATAFRAME
# =========================================================
required_map = {
    "Supplier":        supplier_col,
    "Country":         country_col,
    "Material":        material_col,
    "Liefertreue":     delivery_col,
    "Lieferzeit":      leadtime_col,
    "Qualitätsrate":   quality_col,
    "Reklamationsquote": complaint_col,
    "Preisabweichung": price_col,
}

missing = [k for k, v in required_map.items() if v == NA]
if missing:
    st.error(f"⚠️ Please map these required fields in the sidebar: {', '.join(missing)}")
    st.stop()

mapping = {src: tgt for tgt, src in required_map.items()}
for src, tgt in {score_col:"Score", status_col:"Status", anomaly_col:"Anomaly_Flag", supplier_id_col:"Supplier_ID"}.items():
    if src != NA:
        mapping[src] = tgt

df = merged_df.rename(columns=mapping).copy()
needed = list(set(list(required_map.keys()) + ["Score","Status","Anomaly_Flag","Supplier_ID"]))
df = df[[c for c in df.columns if c in needed]]

if "Supplier_ID" not in df.columns:
    df["Supplier_ID"] = [f"S{i+1:04d}" for i in range(len(df))]

df = to_numeric_safe(df, ["Liefertreue","Lieferzeit","Qualitätsrate","Reklamationsquote","Preisabweichung","Score"])

before_rows = len(df)
df = df.dropna(subset=list(required_map.keys()))
after_rows = len(df)

if df.empty:
    st.error("No valid rows remain after cleaning. Please check the column mapping.")
    st.stop()

if "Anomaly_Flag" in df.columns:
    df["Anomalien"] = df["Anomaly_Flag"].apply(normalize_anomaly_flag)
else:
    df["Anomalien"] = df.apply(calculate_anomalies, axis=1)

if "Score" not in df.columns:
    df["Score"] = df.apply(calculate_score, axis=1)
else:
    df["Score"] = df["Score"].fillna(df.apply(calculate_score, axis=1))

if "Status" not in df.columns:
    df["Status"] = df["Score"].apply(status_label)
else:
    df["Status"] = df["Status"].fillna(df["Score"].apply(status_label))

df["Risk"]      = df["Score"].apply(risk_level)
df["Crit_KPI"]  = df.apply(critical_kpi, axis=1)
df["Strengths"] = df.apply(supplier_strengths, axis=1)

agg = (
    df.groupby("Supplier", as_index=False)
    .agg({
        "Supplier_ID":"first","Material":"first","Country":"first",
        "Liefertreue":"mean","Lieferzeit":"mean","Qualitätsrate":"mean",
        "Reklamationsquote":"mean","Preisabweichung":"mean",
        "Score":"mean","Anomalien":"sum","Status":"first",
        "Risk":"first","Crit_KPI":"first","Strengths":"first",
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
        st.warning("No suppliers for this filter.")
        st.stop()
    sel_sup = st.selectbox("Select Supplier", filtered["Supplier"].tolist())

sel = filtered[filtered["Supplier"] == sel_sup].iloc[0]


# =========================================================
# PROCESSING SUMMARY EXPANDER
# =========================================================
with st.expander("📋 Data Processing Summary"):
    c1, c2, c3 = st.columns(3)
    c1.metric("Sheets Detected", total_sheets)
    c2.metric("Fields Auto-Mapped", f"{mapped_count}/{total_fields}")
    c3.metric("Valid Rows", after_rows)
    if merge_log:
        st.markdown("**Cross-sheet merges:**")
        for m in merge_log: st.success(m)
    st.markdown(f"**Primary sheet:** {primary_sheet_name}")
    st.markdown(f"**Rows dropped (missing KPIs):** {before_rows - after_rows}")
    st.json({v: k for k, v in mapping.items()})


# =========================================================
# TOP KPI CARDS
# =========================================================
kpi_cards = [
    ("📦","Suppliers",    filtered["Supplier"].nunique(),               "in portfolio"),
    ("⭐","Avg Score",    f"{filtered['Score'].mean():.1f}",            "overall rating"),
    ("⚠️","Anomalies",   int(filtered["Anomalien"].sum()),              "detected"),
    ("📂","Top Material", filtered["Material"].mode().iloc[0] if not filtered.empty else "-", "category"),
    ("🏆","Top Supplier", filtered.iloc[0]["Supplier"] if not filtered.empty else "-", "highest score"),
]
for col, (icon, label, value, sub) in zip(st.columns(5), kpi_cards):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size:1.5rem;margin-bottom:8px;">{icon}</div>
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("")


# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview","🎯 Rankings & Insights","📈 Analytics","👤 Supplier Profile","📋 Details"])


# =========== TAB 1 — OVERVIEW ===========
with tab1:
    c_left, c_mid, c_right = st.columns([1.2, 1.3, 0.95])

    with c_left:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🏆 Top Suppliers</div>', unsafe_allow_html=True)
        for rank, (_, row) in enumerate(filtered.head(6).iterrows(), 1):
            bt = "success" if row["Score"] >= 90 else "warning" if row["Score"] >= 75 else "danger"
            ab = f'<span class="badge badge-danger">⚠️ {int(row["Anomalien"])} Anomalies</span>' if row["Anomalien"] > 0 else '<span class="badge badge-success">✓ No Issues</span>'
            st.markdown(f"""
            <div class="supplier-item">
                <div style="display:flex;justify-content:space-between;align-items:start;">
                    <div>
                        <div class="supplier-name">#{rank} {row['Supplier']}</div>
                        <div class="supplier-meta">{row['Material']} · {row['Country']}</div>
                    </div>
                    <span class="badge badge-{bt}" style="font-size:0.9rem;font-weight:700;">{row['Score']}</span>
                </div>
                <div style="margin-top:8px;">{ab}</div>
            </div>""", unsafe_allow_html=True)
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
        with cc: st.metric("On-Time Delivery", f"{sel['Liefertreue']:.1f}%",   f"{sel['Liefertreue']-95:.1f}%")
        with cd: st.metric("Quality Score",    f"{sel['Qualitätsrate']:.1f}%", f"{sel['Qualitätsrate']-97:.1f}%")
        with ce: st.metric("Lead Time",        f"{sel['Lieferzeit']:.1f} d",   f"{sel['Lieferzeit']-10:.1f} d")
        with cf: st.metric("Complaint Rate",   f"{sel['Reklamationsquote']:.2f}%", f"{sel['Reklamationsquote']-1:.2f}%")
        st.markdown('</div>', unsafe_allow_html=True)

    with c_right:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🎯 Overall Score</div>', unsafe_allow_html=True)
        st.plotly_chart(donut_chart(sel["Score"], score_color(sel["Score"])), use_container_width=True, config={"displayModeBar":False})
        rc = "badge-success" if sel["Risk"]=="Low" else "badge-warning" if sel["Risk"]=="Medium" else "badge-danger"
        st.markdown(f'<span class="badge {rc}" style="font-size:0.9rem;">Risk: {sel["Risk"]}</span>', unsafe_allow_html=True)
        st.write("")
        st.markdown(f"**Critical KPI:** {sel['Crit_KPI']}")
        st.markdown('</div>', unsafe_allow_html=True)


# =========== TAB 2 — RANKINGS ===========
with tab2:
    c_rank, c_ins = st.columns([1.2, 0.95])
    with c_rank:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📊 Supplier Ranking</div>', unsafe_allow_html=True)
        rdf = filtered[["Supplier","Material","Country","Score","Anomalien","Risk"]].sort_values("Score", ascending=False).copy()
        rdf.insert(0, "Rank", range(1, len(rdf)+1))
        st.dataframe(rdf, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c_ins:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">💡 Key Insights</div>', unsafe_allow_html=True)
        for i, (_, row) in enumerate(filtered.head(3).iterrows(), 1):
            st.markdown(f'<div class="insight-box"><b>Top {i}: {row["Supplier"]}</b><br><span style="font-size:0.9rem;">Score: {row["Score"]} | {row["Material"]} | {row["Country"]}</span><br><span style="font-size:0.85rem;opacity:0.9;">Strengths: {row["Strengths"]}</span></div>', unsafe_allow_html=True)
        for _, row in filtered.sort_values("Score").head(2).iterrows():
            st.markdown(f'<div class="warning-box"><b>⚠️ Attention: {row["Supplier"]}</b><br><span style="font-size:0.9rem;">Critical: {row["Crit_KPI"]} | Score: {row["Score"]}</span></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# =========== TAB 3 — ANALYTICS ===========
with tab3:
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        fig = px.bar(filtered.sort_values("Score", ascending=False), x="Supplier", y="Score", color="Score", title="Supplier Ranking by Score", color_continuous_scale="Viridis")
        fig.update_traces(marker_line_width=0)
        fig.update_layout(**plotly_dark(title_font_size=14))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        mat = filtered["Material"].value_counts().reset_index(); mat.columns=["Material","Count"]
        fig2 = px.pie(mat, names="Material", values="Count", hole=0.5, title="Material Distribution", color_discrete_sequence=px.colors.qualitative.Set2)
        fig2.update_layout(**plotly_dark(title_font_size=14))
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

    with r1c2:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        fig3 = px.scatter(filtered, x="Liefertreue", y="Qualitätsrate", size="Score", color="Score", hover_name="Supplier", title="Delivery vs Quality", color_continuous_scale="Plasma")
        fig3.update_layout(**plotly_dark(title_font_size=14))
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        ano_df = filtered.copy()
        ano_df["AnomalyStatus"] = np.where(ano_df["Anomalien"] > 0, "Has Anomalies", "Clean")
        ano_s = ano_df["AnomalyStatus"].value_counts().reset_index(); ano_s.columns=["Status","Count"]
        fig4 = px.pie(ano_s, names="Status", values="Count", hole=0.6, title="Anomaly Distribution", color_discrete_sequence=["#ef4444","#22c55e"])
        fig4.update_layout(**plotly_dark(title_font_size=14))
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        fig5 = px.bar(filtered.sort_values("Lieferzeit"), x="Supplier", y="Lieferzeit", color="Lieferzeit", title="Lead Time Comparison", color_continuous_scale="Blues_r")
        fig5.update_traces(marker_line_width=0); fig5.update_layout(**plotly_dark(title_font_size=14))
        st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)
    with r2c2:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        fig6 = px.bar(filtered.sort_values("Reklamationsquote", ascending=False), x="Supplier", y="Reklamationsquote", color="Reklamationsquote", title="Complaint Rate Comparison", color_continuous_scale="Reds_r")
        fig6.update_traces(marker_line_width=0); fig6.update_layout(**plotly_dark(title_font_size=14))
        st.plotly_chart(fig6, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)


# =========== TAB 4 — PROFILE ===========
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
            st.markdown(f'<div class="insight-box"><b>✅ Recommendation</b><br>{sel["Supplier"]} is a preferred supplier. Strengths: {sel["Strengths"]}</div>', unsafe_allow_html=True)
        elif sel["Score"] >= 75:
            st.markdown(f'<div class="warning-box"><b>⚠️ Recommendation</b><br>Monitor <b>{sel["Crit_KPI"]}</b> closely.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="critical-box"><b>🔴 Critical</b><br>Focus on <b>{sel["Crit_KPI"]}</b>. Consider alternatives.</div>', unsafe_allow_html=True)
    with cp2:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📊 KPI Profile</div>', unsafe_allow_html=True)
        fp = go.Figure(go.Bar(
            x=["Delivery","Quality","Complaints","Price Var.","Lead Time"],
            y=[sel["Liefertreue"], sel["Qualitätsrate"], sel["Reklamationsquote"], abs(sel["Preisabweichung"]), sel["Lieferzeit"]],
            marker=dict(color=["#22c55e","#3b82f6","#f59e0b","#ef4444","#8b5cf6"], line=dict(width=0)),
        ))
        fp.update_layout(title="KPI Performance Profile", showlegend=False, **plotly_dark(title_font_size=14))
        st.plotly_chart(fp, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)


# =========== TAB 5 — DETAILS ===========
with tab5:
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📋 Complete Data View</div>', unsafe_allow_html=True)
    dcols = [c for c in ["Supplier","Supplier_ID","Material","Country","Liefertreue","Lieferzeit","Qualitätsrate","Reklamationsquote","Preisabweichung","Score","Anomalien","Status","Risk","Crit_KPI"] if c in agg.columns]
    st.dataframe(agg[dcols].round(2), use_container_width=True, hide_index=True)
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
