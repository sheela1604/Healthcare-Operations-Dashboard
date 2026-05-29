import streamlit as st
import pandas as pd
import plotly.express as px

# ===============================
# PAGE CONFIG
# ===============================
# st.set_page_config(page_title="Clinical & Disease Intelligence", layout="wide")
def run():
    PRIMARY = "#0A3D62"
    SOFT_BORDER = "#D6EAF8"
    LIGHT_CARD_BG = "#F8FBFD"
    KPI_BG = "#F5F7FA"
    KPI_BORDER = "#AED6F1"

    # ===============================
    # MAIN HEADER
    # ===============================
    st.markdown(f"""
    <h1 style='text-align:center; color:{PRIMARY}; font-size:44px;'>
    Clinical & Disease Intelligence
    </h1>
    <p style='text-align:center; font-size:18px; color:black;'>
    Major Medical Patterns & Surgical Analytics
    </p>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ===============================
    # LOAD DATA
    # ===============================
    file_path = "data/dataFinal.xlsx"

    patients = pd.read_excel(file_path, sheet_name="Patients")
    doctors = pd.read_excel(file_path, sheet_name="Doctor")
    departments = pd.read_excel(file_path, sheet_name="Department")
    surgeries = pd.read_excel(file_path, sheet_name="SurgeryRecord")

    # ===============================
    # SIDEBAR
    # ===============================
    st.sidebar.markdown("<h3 style='color:{PRIMARY};'>Filter Panel</h3>", unsafe_allow_html=True)

    selected_dept = st.sidebar.multiselect(
        "Select Department",
        departments['dept_Name'].unique()
    )

    selected_disease = st.sidebar.multiselect(
        "Select Diagnosis",
        surgeries['surgery_Type'].unique()
    )

    # ===============================
    # MERGE DATA
    # ===============================
    patients_surgeries_df = pd.merge(patients, surgeries, on='patient_Id', how='left')
    patients_surgeries_doctors_df = pd.merge(
        patients_surgeries_df,
        doctors[['doct_Id', 'dept_Id']],
        left_on='surgeon_Id',
        right_on='doct_Id',
        how='left'
    )
    final_merged_df = pd.merge(
        patients_surgeries_doctors_df.drop(columns=['doct_Id']),
        departments,
        on='dept_Id',
        how='left'
    )

    current = final_merged_df.copy()

    if selected_dept:
        current = current[current['dept_Name'].isin(selected_dept)]

    if selected_disease:
        current = current[current['surgery_Type'].isin(selected_disease)]

    # ===============================
    # KPI SECTION
    # ===============================
    st.markdown("""
    <h2 style='text-align:center; color:#0A3D62; font-size:32px; margin-bottom:25px;'>
    KEY METRICS
    </h2>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    def kpi_box(title, value):
        st.markdown(f"""
        <div style="
            background-color:{KPI_BG};
            padding:30px 10px;
            border-radius:14px;
            border:2px solid {KPI_BORDER};
            text-align:center;
        ">
            <div style="font-size:16px; color:#6c757d; margin-bottom:10px;">
                {title}
            </div>
            <div style="font-size:28px; font-weight:600; color:#1a1a2e;">
                {value}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col1:
        kpi_box("Total Patients", current['patient_Id'].nunique())
    with col2:
        kpi_box("Unique Diseases", current['surgery_Type'].nunique())
    with col3:
        kpi_box("Total Active Surgeons", current['surgeon_Id'].nunique())
    with col4:
        kpi_box("Departments Involved", current['dept_Name'].nunique())

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ===============================
    # CHART CONTAINER FUNCTION
    # ===============================
    def chart_container(title, explanation, fig):

        fig.update_layout(
            template="simple_white",
            font=dict(color="black"),
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis=dict(
                title_font=dict(color="black"),
                tickfont=dict(color="black"),
                showgrid=False
            ),
            yaxis=dict(
                title_font=dict(color="black"),
                tickfont=dict(color="black"),
                showgrid=True,
                gridcolor="rgba(0,0,0,0.06)"
            ),
            margin=dict(l=20, r=20, t=30, b=30)
        )

        st.markdown(f"""
        <div style="
            border:1.5px solid {SOFT_BORDER};
            border-radius:18px;
            padding:25px;
            margin-bottom:35px;
            background:{LIGHT_CARD_BG};
        ">
            <h3 style='text-align:center; color:{PRIMARY};'>
                {title}
            </h3>
            <p style='text-align:center; color:black; font-size:15px; line-height:1.6;'>
                {explanation}
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.plotly_chart(fig, use_container_width=True)

    # ===============================
    # CHARTS
    # ===============================

    # Top Diagnoses – Pie Chart
    top_diag = current['surgery_Type'].value_counts().head(10).reset_index()
    top_diag.columns = ['Diagnosis', 'Count']

    fig1 = px.pie(
        top_diag,
        names='Diagnosis',
        values='Count',
        hole=0.4,  # donut style
        color_discrete_sequence=px.colors.qualitative.Bold
    )


    chart_container(
        "Top 10 Diagnoses",
        "This chart highlights the most frequent diagnoses recorded, helping identify dominant health conditions affecting patients.",
        fig1
    )

    # Top Surgeries
    top_surg = surgeries['surgery_Type'].value_counts().head(10).reset_index()
    top_surg.columns = ['Surgery', 'Count']

    fig2 = px.bar(
        top_surg,
        x="Surgery",
        y="Count",
        color_discrete_sequence=["#1E3A8A"]
    )

    chart_container(
        "Top 10 Surgeries",
        "Displays the most frequently performed surgical procedures across departments.",
        fig2
    )

    # Disease Trend
    df_trend = current.copy()
    df_trend['surgery_Date'] = pd.to_datetime(df_trend['surgery_Date'])
    df_trend['Month'] = df_trend['surgery_Date'].dt.month_name()

    trend = df_trend.groupby("Month").size().reset_index(name="Count")

    fig3 = px.line(
        trend,
        x="Month",
        y="Count",
        markers=True,
        color_discrete_sequence=["#E74C3C"]
    )

    chart_container(
        "Disease Trend Over Time",
        "Displays month-wise variation in disease cases, indicating seasonal trends and demand fluctuations.",
        fig3
    )

    # Department Distribution
    dept_data = current.groupby(['dept_Name','surgery_Type']).size().reset_index(name='Count')

    fig4 = px.bar(
        dept_data,
        x="dept_Name",
        y="Count",
        color="surgery_Type",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )

    chart_container(
        "Disease Distribution by Department",
        "Shows the distribution of cases across hospital departments for workload comparison.",
        fig4
    )

    # Heatmap
    heat_df = current.copy()
    heat_df['Date_Of_Birth'] = pd.to_datetime(heat_df['Date_Of_Birth'])
    heat_df['Age'] = pd.to_datetime('today').year - heat_df['Date_Of_Birth'].dt.year

    bins = [0,18,30,45,60,100]
    labels = ['0-17','18-29','30-44','45-59','60+']
    heat_df['Age_Group'] = pd.cut(heat_df['Age'], bins=bins, labels=labels)

    heatmap_data = pd.crosstab(heat_df['Age_Group'], heat_df['surgery_Type'])

    fig5 = px.imshow(
    heatmap_data,
    text_auto=True,
    color_continuous_scale="Mint",
    aspect="auto"
    )

    chart_container(
        "Age Group vs Disease Matrix",
        "Identifies which age groups are more affected by specific diagnoses.",
        fig5
    )

    # Surgery Trend – Area Chart
    surgery_trend_df = surgeries.copy()
    surgery_trend_df['surgery_Date'] = pd.to_datetime(surgery_trend_df['surgery_Date'])
    surgery_trend_df['Month'] = surgery_trend_df['surgery_Date'].dt.month_name()

    surgery_trend = surgery_trend_df.groupby("Month").size().reset_index(name="Count")

    fig6 = px.area(
        surgery_trend,
        x="Month",
        y="Count",
        color_discrete_sequence=["#AF7AC5"]
    )

    chart_container(
        "Surgery Trend Over Time",
        "Tracks temporal patterns in surgeries performed across the hospital.",
        fig6
    )
