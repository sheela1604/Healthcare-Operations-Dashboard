import streamlit as st
import pandas as pd
import plotly.express as px


def run():
    st.markdown("""
    <style>
    

    .section-title {
        font-size: 28px;
        font-weight: 700;
        color: #1f4e79;
        margin-top: 30px;
        margin-bottom: 15px;
        text-align: center;
    }

    .kpi-card {
        background-color: white;
        padding: 25px;
        border-radius: 14px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.08);
        text-align: center;
    }

    .kpi-title {
        font-size: 16px;
        color: #1f4e79;
    }

    .kpi-value {
        font-size: 34px;
        font-weight: bold;
        color: #1f4e79;
    }
    </style>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------
    # LOAD DATA
    # ---------------------------------------------------
    @st.cache_data
    def load_data():
        xls = pd.ExcelFile("data/dataFinal.xlsx")
        return {sheet: pd.read_excel(xls, sheet) for sheet in xls.sheet_names}

    tables = load_data()

    patients = tables["Patients"]
    appointments = tables["Appointment"]
    bed_records = tables["BedRecords"]
    doctor = tables["Doctor"]
    department = tables["Department"]
    nurse = tables["Nurse"]

    # ---------------------------------------------------
    # PREPROCESSING
    # ---------------------------------------------------
    appointments["appointment_Date"] = pd.to_datetime(appointments["appointment_Date"])
    bed_records["admission_Date"] = pd.to_datetime(bed_records["admission_Date"])

    doctor_dept = doctor.merge(department, on="dept_Id", how="left")

    appointments = appointments.merge(
        doctor_dept[["doct_Id", "dept_Name", "FName"]],
        on="doct_Id",
        how="left"
    )

    appointments["Doctor_Name"] = appointments["FName"]

    nurse_dept = nurse.merge(department, on="dept_Id", how="left")

    # ---------------------------------------------------
    # SIDEBAR FILTERS ONLY
    # ---------------------------------------------------
    st.sidebar.subheader("Filters")

    date_range = st.sidebar.date_input(
        "Select Date Range",
        [
            appointments["appointment_Date"].min(),
            appointments["appointment_Date"].max()
        ]
    )

    dept_filter = st.sidebar.multiselect(
        "Department",
        appointments["dept_Name"].dropna().unique(),
        default=appointments["dept_Name"].dropna().unique()
    )

    # Apply filters
    appointments_f = appointments[
        (appointments["appointment_Date"] >= pd.to_datetime(date_range[0])) &
        (appointments["appointment_Date"] <= pd.to_datetime(date_range[1])) &
        (appointments["dept_Name"].isin(dept_filter))
    ]

    patients_f = patients[
        patients["patient_Id"].isin(appointments_f["patient_Id"])
    ]

    bed_f = bed_records[
        bed_records["patient_Id"].isin(patients_f["patient_Id"])
    ]

    # ---------------------------------------------------
    # TITLE
    # ---------------------------------------------------
    st.markdown(
        '<div class="section-title">Staffing & Resource Optimization</div>',
        unsafe_allow_html=True
    )

    # ---------------------------------------------------
    # KPI CARDS
    # ---------------------------------------------------
    col1, col2, col3 = st.columns(3)

    def kpi_card(column, title, value):
        column.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """, unsafe_allow_html=True)

    kpi_card(col1, "Active Doctors", appointments_f["doct_Id"].nunique())
    kpi_card(col2, "Total Nurses", nurse["nurse_Id"].nunique())
    kpi_card(col3, "Total Admissions", bed_f["admission_Id"].nunique())

    st.markdown("---")

    # ---------------------------------------------------
    # NURSE DISTRIBUTION
    # ---------------------------------------------------
    st.markdown(
        '<div class="section-title">Nurse Distribution by Department</div>',
        unsafe_allow_html=True
    )

    nurse_count = nurse_dept.groupby("dept_Name")["nurse_Id"].nunique().reset_index()

    fig = px.pie(
        nurse_count,
        names="dept_Name",
        values="nurse_Id",
        hole=0.5,
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------
    # DOCTOR WORKLOAD HEATMAP
    # ---------------------------------------------------
    st.markdown(
        '<div class="section-title">Doctor Workload Heatmap (Top 10)</div>',
        unsafe_allow_html=True
    )

    doctor_workload = appointments_f.groupby(
        ["Doctor_Name", "dept_Name"]
    ).size().reset_index(name="Appointments")

    top10_doctors = doctor_workload.groupby("Doctor_Name")["Appointments"] \
        .sum().sort_values(ascending=False).head(10).index

    heatmap_df = doctor_workload[
        doctor_workload["Doctor_Name"].isin(top10_doctors)
    ]

    pivot_heatmap = heatmap_df.pivot(
        index="Doctor_Name",
        columns="dept_Name",
        values="Appointments"
    ).fillna(0)

    fig = px.imshow(
        pivot_heatmap,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Purples",
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------
    # PATIENT-TO-NURSE RATIO
    # ---------------------------------------------------
    st.markdown(
        '<div class="section-title">Patient-to-Nurse Ratio</div>',
        unsafe_allow_html=True
    )

    admissions_dept = bed_f.merge(
        appointments_f[["patient_Id", "dept_Name"]].drop_duplicates(),
        on="patient_Id",
        how="left"
    ).groupby("dept_Name").size().reset_index(name="Total_Admissions")

    ratio_df = admissions_dept.merge(
        nurse_count,
        on="dept_Name",
        how="left"
    )

    ratio_df["Patient_per_Nurse"] = (
        ratio_df["Total_Admissions"] / ratio_df["nurse_Id"]
    ).round(2)

    fig = px.scatter(
        ratio_df,
        x="nurse_Id",
        y="Total_Admissions",
        size="Patient_per_Nurse",
        color="Patient_per_Nurse",
        hover_name="dept_Name",
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------
    # DEPARTMENT-WISE ADMISSIONS VS STAFF
    # ---------------------------------------------------
    st.markdown(
        '<div class="section-title">Department-wise Admissions vs Staff</div>',
        unsafe_allow_html=True
    )

    fig = px.bar(
        ratio_df,
        x="dept_Name",
        y=["Total_Admissions", "nurse_Id"],
        barmode="group",
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------
    # MONTHLY ADMISSIONS
    # ---------------------------------------------------
    st.markdown(
        '<div class="section-title">Admissions Reference View for Staffing</div>',
        unsafe_allow_html=True
    )

    monthly_admissions = bed_f.set_index("admission_Date") \
        .resample("M").size().reset_index(name="Admissions")

    fig = px.line(
        monthly_admissions,
        x="admission_Date",
        y="Admissions",
        markers=True,   # ✅ adds markers
        template="plotly_white"
    )

    fig.update_traces(
        line=dict(color="#065F46", width=3),
        marker=dict(size=8, color="#065F46")

    )

    fig.update_layout(
        xaxis_title="Admission Date",
        yaxis_title="Admissions",
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)