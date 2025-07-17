import streamlit as st
import pandas as pd
from fpdf import FPDF
from io import BytesIO
import base64
from datetime import date

st.set_page_config(layout="wide", page_title="Footfall Summary Report")

# Custom CSS for compact, beautiful design with bold headers
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700;900&display=swap');

    .main {
        background: linear-gradient(135deg, #f0f4f8 0%, #ffffff 100%);
        padding: 20px;
        font-family: 'Roboto', sans-serif;
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        gap: 15px;
    }
    .header {
        background: linear-gradient(90deg, #1e90ff, #1565c0);
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        text-align: center;
    }
    .title {
        color: #ffffff;
        font-size: 32px;
        font-weight: 700;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .dashboard-container {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
        transition: transform 0.3s ease;
    }
    .dashboard-container:hover {
        transform: translateY(-3px);
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 3px 8px rgba(0,0,0,0.1);
        text-align: center;
        margin: 10px;
        border-left: 4px solid #1e90ff;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .metric-card:hover {
        transform: scale(1.03);
        box-shadow: 0 5px 12px rgba(0,0,0,0.2);
    }
    .metric-label {
        font-size: 16px;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .metric-label::before {
        content: '📊';
        margin-right: 6px;
    }
    .metric-value {
        font-size: 24px;
        color: #1e90ff;
        font-weight: 700;
    }
    .subheader {
        color: #2c3e50;
        font-size: 24px;
        font-weight: 700;
        margin: 15px 0 10px;
        border-bottom: 2px solid #1e90ff;
        padding-bottom: 5px;
    }
    .summary-container {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
        max-height: 300px;
        overflow-y: auto;
    }
    .stButton>button {
        background-color: #1e90ff;
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 700;
        font-size: 14px;
        transition: background-color 0.3s ease, transform 0.3s ease, box-shadow 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #1565c0;
        transform: translateY(-2px);
        box-shadow: 0 3px 8px rgba(0,0,0,0.3);
    }
    .stFileUploader > div > label, .stSelectbox > div > label, .stDateInput > div > label {
        color: #2c3e50 !important;
        font-weight: 900 !important;
        font-size: 20px !important;
        font-family: 'Roboto', sans-serif !important;
        margin-bottom: 8px !important;
    }
    .stDateInput div[data-baseweb="base-input"], .stSelectbox div[data-baseweb="select"] {
        border-radius: 8px;
        border: 2px solid #1e90ff;
    }
</style>
""", unsafe_allow_html=True)

def clean_columns(df):
    df.columns = [col.strip() for col in df.columns]
    return df

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.fillna(0).to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

def create_pdf(df, title):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Arial", size=8)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(0, 10, title, ln=1, align='C')

    col_widths = []
    for col in df.columns:
        if col == 'Facility_Name':
            col_widths.append(60)
        elif col == 'District_Name':
            col_widths.append(35)
        elif col == 'AAM_Type':
            col_widths.append(25)
        else:
            col_widths.append(30)

    for i, col in enumerate(df.columns):
        wrapped_header = col.replace(' ', '\n')
        x, y = pdf.get_x(), pdf.get_y()
        pdf.multi_cell(col_widths[i], 5, wrapped_header, border=1, align='C')
        pdf.set_xy(x + col_widths[i], y)
    pdf.ln()

    for _, row in df.fillna(0).iterrows():
        for i, val in enumerate(row):
            pdf.cell(col_widths[i], 10, str(val), border=1)
        pdf.ln()

    return pdf.output(dest='S').encode('latin1')

def to_combined_excel(facility_df, district_df, total_registered, total_reported):
    output = BytesIO()
    combined_summary = pd.DataFrame({
        'Metric': ['Total Facilities (AAM-UPHC)', 'Total Facilities (AAM-USHC)', 'Reported Facilities (AAM-UPHC)', 'Reported Facilities (AAM-USHC)'],
        'Value': [
            total_registered.get('AAM-UPHC', 0),
            total_registered.get('AAM-USHC', 0),
            total_reported.get('AAM-UPHC', 0),
            total_reported.get('AAM-USHC', 0)
        ]
    })
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        facility_df.fillna(0).to_excel(writer, index=False, sheet_name='Facility-wise Summary')
        district_df.fillna(0).to_excel(writer, index=False, sheet_name='District-wise Summary')
        combined_summary.to_excel(writer, index=False, sheet_name='Dashboard Summary')
        workbook = writer.book
        for sheet_name, df in {
            'Facility-wise Summary': facility_df.fillna(0),
            'District-wise Summary': district_df.fillna(0),
            'Dashboard Summary': combined_summary
        }.items():
            worksheet = writer.sheets[sheet_name]
            for i, width in enumerate(df.columns.astype(str)):
                col_width = max(df[width].astype(str).map(len).max(), len(width)) + 2
                worksheet.set_column(i, i, col_width)
    return output.getvalue()

# Initialize session state for date inputs
if 'start_date' not in st.session_state:
    st.session_state.start_date = None
if 'end_date' not in st.session_state:
    st.session_state.end_date = None

# File uploaders and filters in a single row
col_upload1, col_upload2, col_filters = st.columns([1, 1, 1])
with col_upload1:
    footfall_file = st.file_uploader("Upload Daily_Entry (Footfall Report)", type=["xlsx", "xls", "csv"])
with col_upload2:
    master_file = st.file_uploader("Upload FPE_Entry (Facility Master)", type=["xlsx", "xls", "csv"])
with col_filters:
    aam_type_filter = st.selectbox("Select AAM Type", options=["AAM-USHC", "AAM-UPHC"])
    col_date1, col_date2 = st.columns(2)

if footfall_file and master_file:
    try:
        if footfall_file.name.endswith(".csv"):
            footfall_df = pd.read_csv(footfall_file)
        else:
            footfall_df = pd.read_excel(footfall_file)

        if master_file.name.endswith(".csv"):
            master_df = pd.read_csv(master_file)
        else:
            master_df = pd.read_excel(master_file)

        footfall_df = clean_columns(footfall_df)
        master_df = clean_columns(master_df)

        # Enhanced column renaming for robustness
        footfall_column_map = {
            'Facility Name': 'Facility_Name',
            'Facility_Name': 'Facility_Name',
            'facility name': 'Facility_Name',
            'facility_name': 'Facility_Name',
            'AAM Type': 'AAM_Type',
            'AAM_Type': 'AAM_Type',
            'aam type': 'AAM_Type',
            'aam_type': 'AAM_Type',
            'District': 'District_Name',
            'District_Name': 'District_Name',
            'district': 'District_Name',
            'district_name': 'District_Name',
            'Entry Date': 'Entry_Date',
            'Entry_Date': 'Entry_Date',
            'entry date': 'Entry_Date',
            'entry_date': 'Entry_Date',
            'Footfall Female': 'Footfall_Female',
            'Footfall Female ': 'Footfall_Female',
            'footfall female': 'Footfall_Female',
            'Footfall Total': 'Footfall_Total',
            'Footfall_Total': 'Footfall_Total',
            'footfall total': 'Footfall_Total'
        }

        master_column_map = {
            'HFI_Name': 'Facility_Name',
            'HFI Name': 'Facility_Name',
            'Facility_Name': 'Facility_Name',
            'facility name': 'Facility_Name',
            'facility_name': 'Facility_Name',
            'FACILITY_TYPE': 'AAM_Type',
            'Facility Type': 'AAM_Type',
            'facility type': 'AAM_Type',
            'AAM Type': 'AAM_Type',
            'AAM_Type': 'AAM_Type',
            'aam type': 'AAM_Type',
            'aam_type': 'AAM_Type',
            'District_Name': 'District_Name',
            'District': 'District_Name',
            'district': 'District_Name',
            'district_name': 'District_Name'
        }

        footfall_df.rename(columns={k: v for k, v in footfall_column_map.items() if k in footfall_df.columns}, inplace=True)
        master_df.rename(columns={k: v for k, v in master_column_map.items() if k in master_df.columns}, inplace=True)

        # Check for required columns
        required_footfall_cols = ['Facility_Name', 'AAM_Type', 'District_Name', 'Entry_Date', 'Footfall_Total', 'Footfall_Female']
        required_master_cols = ['Facility_Name', 'AAM_Type', 'District_Name']
        missing_footfall_cols = [col for col in required_footfall_cols if col not in footfall_df.columns]
        missing_master_cols = [col for col in required_master_cols if col not in master_df.columns]

        if missing_footfall_cols or missing_master_cols:
            st.error(f"Missing columns in Footfall DataFrame: {missing_footfall_cols}, Master DataFrame: {missing_master_cols}")
            st.stop()

        # Debug: Log raw data before standardization
        with open("debug.log", "a") as f:
            f.write("--- Raw Data Before Standardization ---\n")
            f.write(f"Master DataFrame AAM_Type values: {master_df['AAM_Type'].unique().tolist()}\n")
            f.write(f"Master DataFrame Facility_Name count (all entries): {len(master_df['Facility_Name'])}\n")
            f.write(f"Master DataFrame Facility_Name unique count: {master_df['Facility_Name'].nunique()}\n")
            f.write(f"Footfall DataFrame AAM_Type values: {footfall_df['AAM_Type'].unique().tolist()}\n")
            f.write(f"Footfall DataFrame Facility_Name count (all entries): {len(footfall_df['Facility_Name'])}\n")
            f.write(f"Footfall DataFrame Facility_Name unique count: {footfall_df['Facility_Name'].nunique()}\n")

        # Standardize AAM_Type and Facility_Name
        footfall_df['AAM_Type'] = footfall_df['AAM_Type'].str.strip().str.upper()
        master_df['AAM_Type'] = master_df['AAM_Type'].str.strip().str.upper()
        footfall_df['Facility_Name'] = footfall_df['Facility_Name'].str.strip().str.upper()
        master_df['Facility_Name'] = master_df['Facility_Name'].str.strip().str.upper()

        footfall_df['Entry_Date'] = pd.to_datetime(footfall_df['Entry_Date'], errors='coerce')

        # Set default dates for the entire dataset
        unique_dates = footfall_df['Entry_Date'].dropna().dt.date.unique()
        if len(unique_dates) > 0:
            default_start_date = min(unique_dates)
            default_end_date = max(unique_dates)
        else:
            default_start_date = date.today()
            default_end_date = date.today()

        # Update session state with default dates only if not already set
        if st.session_state.start_date is None:
            st.session_state.start_date = default_start_date
        if st.session_state.end_date is None:
            st.session_state.end_date = default_end_date

        # Render date inputs once, using session state
        with col_date1:
            st.session_state.start_date = st.date_input(
                "From Date",
                value=st.session_state.start_date,
                format="YYYY-MM-DD",
                disabled=not (footfall_file and master_file)
            )
        with col_date2:
            st.session_state.end_date = st.date_input(
                "To Date",
                value=st.session_state.end_date,
                format="YYYY-MM-DD",
                disabled=not (footfall_file and master_file)
            )

        # Debug: Log data after standardization and date rendering
        with open("debug.log", "a") as f:
            f.write("--- Data After Standardization ---\n")
            f.write(f"Master DataFrame AAM_Type values: {master_df['AAM_Type'].unique().tolist()}\n")
            f.write(f"Master DataFrame Facility_Name count (all entries): {len(master_df['Facility_Name'])}\n")
            f.write(f"Master DataFrame Facility_Name unique count: {master_df['Facility_Name'].nunique()}\n")
            f.write(f"Footfall DataFrame AAM_Type values: {footfall_df['AAM_Type'].unique().tolist()}\n")
            f.write(f"Footfall DataFrame Facility_Name count (all entries): {len(footfall_df['Facility_Name'])}\n")
            f.write(f"Footfall DataFrame Facility_Name unique count: {footfall_df['Facility_Name'].nunique()}\n")
            f.write(f"Sample master_df facilities: {master_df['Facility_Name'].head().tolist()}\n")
            f.write(f"Sample footfall_df facilities: {footfall_df['Facility_Name'].head().tolist()}\n")
            f.write(f"Selected Date Range: From {st.session_state.start_date} to {st.session_state.end_date}\n")
            f.write("Date Inputs Rendered: From Date and To Date\n")

        # Filter footfall_df by date range
        footfall_df_filtered = footfall_df
        if st.session_state.start_date and st.session_state.end_date and st.session_state.start_date <= st.session_state.end_date:
            footfall_df_filtered = footfall_df[
                (footfall_df['Entry_Date'].dt.date >= st.session_state.start_date) &
                (footfall_df['Entry_Date'].dt.date <= st.session_state.end_date)
            ]

        # Debug: Log filtered data
        with open("debug.log", "a") as f:
            f.write(f"Footfall DataFrame after date filtering (rows): {len(footfall_df_filtered)}\n")
            f.write(f"Footfall DataFrame AAM_Type values after filtering: {footfall_df_filtered['AAM_Type'].unique().tolist()}\n")
            f.write(f"Footfall DataFrame Facility_Name count (all entries) after filtering: {len(footfall_df_filtered['Facility_Name'])}\n")

        # Calculate metrics for dashboard (count all Facility_Name entries, including duplicates)
        total_registered = master_df.groupby('AAM_Type')['Facility_Name'].count().to_dict()
        total_reported = footfall_df_filtered.groupby('AAM_Type')['Facility_Name'].count().to_dict()

        total_uphc = total_registered.get('AAM-UPHC', 0)
        total_ushc = total_registered.get('AAM-USHC', 0)
        reported_uphc = total_reported.get('AAM-UPHC', 0)
        reported_ushc = total_reported.get('AAM-USHC', 0)

        # Debug: Log calculated metrics
        with open("debug.log", "a") as f:
            f.write("--- Calculated Metrics ---\n")
            f.write(f"Total UPHC Facilities (all entries): {total_uphc}\n")
            f.write(f"Total USHC Facilities (all entries): {total_ushc}\n")
            f.write(f"Reported UPHC Facilities (all entries, date-filtered): {reported_uphc}\n")
            f.write(f"Reported USHC Facilities (all entries, date-filtered): {reported_ushc}\n")
            f.write(f"Total entries in master_df: {len(master_df)}\n")
            f.write(f"Total unique facilities in master_df: {master_df['Facility_Name'].nunique()}\n")
            f.write(f"Total entries in footfall_df (filtered): {len(footfall_df_filtered)}\n")
            f.write(f"Total unique facilities in footfall_df (filtered): {footfall_df_filtered['Facility_Name'].nunique()}\n")

        # Dashboard display
        st.markdown('<div class="header"><h1 class="title">Footfall Summary Report</h1></div>', unsafe_allow_html=True)
        st.markdown('<div class="subheader">📈 Dashboard</div>', unsafe_allow_html=True)
        with st.container():
            st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Total Facilities (AAM-UPHC)</div>
                        <div class="metric-value">{total_uphc}</div>
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Total Facilities (AAM-USHC)</div>
                        <div class="metric-value">{total_ushc}</div>
                    </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Reported Facilities (AAM-UPHC)</div>
                        <div class="metric-value">{reported_uphc}</div>
                    </div>
                """, unsafe_allow_html=True)
            with col4:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Reported Facilities (AAM-USHC)</div>
                        <div class="metric-value">{reported_ushc}</div>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Filter by AAM Type
        footfall_df_filtered = footfall_df_filtered[footfall_df_filtered['AAM_Type'] == aam_type_filter.upper()]
        master_df_filtered = master_df[master_df['AAM_Type'] == aam_type_filter.upper()]

        footfall_df_filtered.fillna(0, inplace=True)
        master_df_filtered.fillna(0, inplace=True)

        # Facility-wise Summary (date-filtered, includes all Facility_Name entries)
        facility_summary = footfall_df_filtered.groupby(['District_Name', 'Facility_Name', 'AAM_Type'], as_index=False)[['Footfall_Total', 'Footfall_Female']].sum()
        facility_summary['% Female Footfall'] = round((facility_summary['Footfall_Female'] / facility_summary['Footfall_Total'].replace(0, 1)) * 100, 2)
        facility_summary.insert(0, 'S.No.', range(1, len(facility_summary) + 1))

        total_footfall = facility_summary['Footfall_Total'].sum()
        total_female = facility_summary['Footfall_Female'].sum()
        total_percent_female = round((total_female / total_footfall) * 100, 2) if total_footfall != 0 else 0
        total_row = {
            'S.No.': '',
            'District_Name': 'Total',
            'Facility_Name': '',
            'AAM_Type': '',
            'Footfall_Total': total_footfall,
            'Footfall_Female': total_female,
            '% Female Footfall': total_percent_female
        }
        facility_summary = pd.concat([facility_summary, pd.DataFrame([total_row])], ignore_index=True)

        # District-wise Summary (date-filtered, count all Facility_Name entries)
        total_registered_summary = master_df_filtered.groupby('District_Name')['Facility_Name'].count().reset_index(name='Registered_Facilities')
        total_reported = footfall_df_filtered.groupby('District_Name')['Facility_Name'].count().reset_index(name='Reported_Facilities')
        total_footfall = footfall_df_filtered.groupby('District_Name')['Footfall_Total'].sum().reset_index(name='Total_Footfall')

        district_summary = total_registered_summary.merge(total_reported, on='District_Name', how='left') \
                                                  .merge(total_footfall, on='District_Name', how='left')

        district_summary['Reported_Facilities'].fillna(0, inplace=True)
        district_summary['Reported_Facilities'] = district_summary['Reported_Facilities'].astype(int)
        district_summary['Unreported_Facilities'] = district_summary['Registered_Facilities'] - district_summary['Reported_Facilities']
        district_summary['Avg_Footfall_Per_Facility'] = round(district_summary['Total_Footfall'] / district_summary['Reported_Facilities'].replace(0, 1), 2)
        district_summary['%_Reported'] = round((district_summary['Reported_Facilities'] / district_summary['Registered_Facilities']) * 100, 2)
        district_summary.insert(0, 'S.No.', range(1, len(district_summary) + 1))

        district_summary = district_summary[
            ['S.No.', 'District_Name', 'Registered_Facilities', 'Reported_Facilities', 'Unreported_Facilities',
             'Total_Footfall', 'Avg_Footfall_Per_Facility', '%_Reported']
        ]

        sum_row = {
            'S.No.': '',
            'District_Name': 'Total',
            'Registered_Facilities': district_summary['Registered_Facilities'].sum(),
            'Reported_Facilities': district_summary['Reported_Facilities'].sum(),
            'Unreported_Facilities': district_summary['Unreported_Facilities'].sum(),
            'Total_Footfall': district_summary['Total_Footfall'].sum(),
            'Avg_Footfall_Per_Facility': round(district_summary['Total_Footfall'].sum() / district_summary['Reported_Facilities'].sum(), 2) if district_summary['Reported_Facilities'].sum() != 0 else 0,
            '%_Reported': round((district_summary['Reported_Facilities'].sum() / district_summary['Registered_Facilities'].sum()) * 100, 2) if district_summary['Registered_Facilities'].sum() != 0 else 0
        }
        district_summary = pd.concat([district_summary, pd.DataFrame([sum_row])], ignore_index=True)

        # Debug: Log summary data
        with open("debug.log", "a") as f:
            f.write("--- Summary Data ---\n")
            f.write(f"Facility-wise Summary rows: {len(facility_summary)}\n")
            f.write(f"Facility-wise Summary Facility_Name count (all entries): {len(facility_summary) - 1}\n")  # Exclude total row
            f.write(f"Facility-wise Summary Facility_Name unique count: {facility_summary['Facility_Name'].nunique()}\n")
            f.write(f"District-wise Summary rows: {len(district_summary)}\n")
            f.write(f"District-wise Summary Reported_Facilities sum: {district_summary['Reported_Facilities'].sum()}\n")

        # Summaries and download buttons
        col_summary1, col_summary2 = st.columns(2)
        with col_summary1:
            st.markdown('<div class="subheader">📋 Facility-wise Summary</div>', unsafe_allow_html=True)
            st.markdown('<div class="summary-container">', unsafe_allow_html=True)
            st.dataframe(facility_summary.fillna(0))
            st.markdown('</div>', unsafe_allow_html=True)
            st.download_button("📥 Download Facility-wise Excel", to_excel(facility_summary), file_name="FacilityWiseReport.xlsx")
            st.download_button("🧾 Download Facility-wise PDF", create_pdf(facility_summary, "Facility-wise Summary Report"), file_name="FacilityWiseReport.pdf")
        with col_summary2:
            st.markdown('<div class="subheader">📊 District-wise Summary</div>', unsafe_allow_html=True)
            st.markdown('<div class="summary-container">', unsafe_allow_html=True)
            st.dataframe(district_summary.fillna(0))
            st.markdown('</div>', unsafe_allow_html=True)
            st.download_button("📥 Download District-wise Excel", to_excel(district_summary), file_name="DistrictWiseReport.xlsx")
            st.download_button("🧾 Download District-wise PDF", create_pdf(district_summary, "District-wise Summary Report"), file_name="DistrictWiseReport.pdf")
            st.download_button("📤 Download Combined Excel Report", to_combined_excel(facility_summary, district_summary, total_registered, total_reported), file_name="Combined_Footfall_Report.xlsx")

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")
else:
    st.info("👆 Please upload both required files to generate the reports.")