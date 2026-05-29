import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def run():

    EXCEL_PATH = "data/dataFinal.xlsx"

    # Professional Color Palette
    PRIMARY_BLUE = '#2563eb'
    LIGHT_BLUE = '#93c5fd'
    LAVENDER = '#a78bfa'
    RED = '#ef4444'
    ACCENT_TEAL = '#06b6d4'
    SUCCESS_GREEN = '#10b981'
    WARNING_AMBER = '#f59e0b'
    LIGHT_GRAY = '#94a3b8'

    @st.cache_data
    def load_healthcare_data(path):
        sheets = pd.read_excel(path, sheet_name=None)
        sheets = {k.strip().lower(): v for k, v in sheets.items()}
        
        dfs = [sheets[name].copy() for name in ["patients", "appointment", "surgeryrecord", "roomrecords", "room", "bedrecords", "department"]]
        for df in dfs:
            df.columns = df.columns.str.strip().str.lower()
        
        if "appointment_date" in dfs[1].columns:
            dfs[1]["appointment_date"] = pd.to_datetime(dfs[1]["appointment_date"], errors="coerce")
        if "admission_date" in dfs[3].columns:
            dfs[3]["admission_date"] = pd.to_datetime(dfs[3]["admission_date"], errors="coerce")
        
        return dfs

    pts, apps, surg, room_recs, rooms, bed, depts = load_healthcare_data(EXCEL_PATH)

    # KPI Calculations
    total_patients = pts["patient_id"].nunique()
    total_appointments = apps["appointment_id"].nunique()
    admitted_patients = pd.concat([room_recs["patient_id"], bed["patient_id"]]).dropna()
    total_admissions = admitted_patients.nunique()
    cancel_count = apps["appointment_status"].astype(str).str.lower().isin(["cancelled", "canceled"]).sum()
    cancel_rate = round((cancel_count / max(total_appointments, 1)) * 100, 2)
    completed_count = apps["appointment_status"].astype(str).str.lower().isin(["completed"]).sum()

    # Styling
    st.markdown("""
    <style>
        .main-header {
            font-size: 42px;
            font-weight: bold;
            color: #000000;
            text-align: center;
            margin-bottom: 10px;
        }
        .sub-header {
            font-size: 24px;
            font-weight: 600;
            color: #000000;
            margin-top: 20px;
            margin-bottom: 15px;
        }
        .kpi-card {
            background: linear-gradient(135deg, #dbeafe 0%, #93c5fd 100%);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            color: #1e3a8a;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .kpi-card h3 {
            font-size: 16px;
            margin-bottom: 10px;
            font-weight: 500;
            color: #1e40af;
        }
        .kpi-card h1 {
            font-size: 36px;
            margin: 0;
            font-weight: bold;
            color: #1e3a8a;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("<div class='main-header'>Healthcare Dashboard</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header' style='text-align: center;'>Executive Overview</div>", unsafe_allow_html=True)

    # KPI Cards
    st.markdown(f"""
    <div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px;'>
        <div class='kpi-card'><h3>Total Patients</h3><h1>{total_patients:,}</h1></div>
        <div class='kpi-card'><h3>Appointments</h3><h1>{total_appointments:,}</h1></div>
        <div class='kpi-card'><h3>Admissions</h3><h1>{total_admissions:,}</h1></div>
        <div class='kpi-card'><h3>Cancellation Rate</h3><h1>{cancel_rate}%</h1></div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Chart 1: Patient Flow
    st.subheader("1. Patient Flow: Appointments vs Admissions")
    if "appointment_date" in apps.columns and "admission_date" in room_recs.columns:
        flow_apps = apps.dropna(subset=["appointment_date"]).groupby(apps["appointment_date"].dt.to_period("M")).size().rename("Appointments")
        flow_adm = room_recs.dropna(subset=["admission_date"]).groupby(room_recs["admission_date"].dt.to_period("M")).size().rename("Admissions")
        flow_data = pd.concat([flow_apps, flow_adm], axis=1).fillna(0)
        flow_data.index = flow_data.index.astype(str)
        
        fig_flow = go.Figure()
        fig_flow.add_trace(go.Scatter(x=flow_data.index, y=flow_data["Appointments"], mode='lines+markers', name='Appointments',
                                    line=dict(color=PRIMARY_BLUE, width=3), marker=dict(size=8, color=PRIMARY_BLUE),
                                    fill='tozeroy', fillcolor='rgba(37, 99, 235, 0.1)'))
        fig_flow.add_trace(go.Scatter(x=flow_data.index, y=flow_data["Admissions"], mode='lines+markers', name='Admissions',
                                    line=dict(color=RED, width=3), marker=dict(size=8, color=RED),
                                    fill='tozeroy', fillcolor='rgba(6, 182, 212, 0.1)'))
        fig_flow.update_layout(template="plotly_white",xaxis_title="Month", yaxis_title="Count", hovermode="x unified", height=400,
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_flow, use_container_width=True)

    # Charts 2 & 3
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("2. Appointment Outcome Distribution")
        if "appointment_status" in apps.columns:
            status_counts = apps["appointment_status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            
            fig_pie = px.pie(status_counts, values="Count", names="Status", hole=0.4,
                            color_discrete_sequence=[PRIMARY_BLUE, ACCENT_TEAL, LIGHT_GRAY, WARNING_AMBER])
            fig_pie.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='white', width=2)))
            fig_pie.update_layout(height=400, showlegend=True,
                                legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=0.85))
            st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.subheader("3. Admissions by Department")
        dept_flow = room_recs.merge(rooms, on="room_no", how="left").merge(depts, on="dept_id", how="left")
        dept_chart = dept_flow.groupby("dept_name").size().reset_index(name="Admissions").sort_values("Admissions", ascending=True)
        
        fig_dept = px.bar(dept_chart, x="Admissions", y="dept_name", orientation="h", color_discrete_sequence=[LAVENDER])
        fig_dept.update_layout(showlegend=False, height=400,
                            xaxis_title="Number of Admissions", yaxis_title="Department")
        st.plotly_chart(fig_dept, use_container_width=True)

    # Charts 4a & 4b
    st.subheader("4. Monthly Appointment & Completion Analysis")
    col3, col4 = st.columns(2)

    with col3:
        if "appointment_date" in apps.columns:
            st.markdown("**4a. Monthly Appointment Volume**")
            apps["month"] = apps["appointment_date"].dt.to_period("M").astype(str)
            monthly_total = apps.groupby("month").size().reset_index(name="Total Appointments")
            
            fig_monthly = go.Figure()
            fig_monthly.add_trace(go.Bar(x=monthly_total["month"], y=monthly_total["Total Appointments"],
                                        marker_color=LIGHT_BLUE, text=monthly_total["Total Appointments"], textposition='outside'))
            fig_monthly.update_layout(xaxis_title="Month", yaxis_title="Total Appointments", hovermode="x",
                                    showlegend=False, height=350,
                                    margin=dict(t=50, b=50, l=50, r=50))
            st.plotly_chart(fig_monthly, use_container_width=True)

    with col4:
        if "appointment_date" in apps.columns and "appointment_status" in apps.columns:
            st.markdown("**4b. Appointment Completion Rate Trend**")
            apps["month"] = apps["appointment_date"].dt.to_period("M").astype(str)
            monthly_total = apps.groupby("month").size()
            monthly_completed = apps[apps["appointment_status"].astype(str).str.lower() == "completed"].groupby("month").size()
            completion_rate_data = ((monthly_completed / monthly_total) * 100).fillna(0).reset_index()
            completion_rate_data.columns = ["Month", "Completion Rate (%)"]
            
            fig_completion = go.Figure()
            fig_completion.add_trace(go.Scatter(x=completion_rate_data["Month"], y=completion_rate_data["Completion Rate (%)"],
                                            mode='lines+markers', line=dict(color=SUCCESS_GREEN, width=3),
                                            marker=dict(size=8, color=RED), fill='tozeroy',
                                            fillcolor='rgba(59, 130, 246, 0.1)'))
            fig_completion.update_layout(xaxis_title="Month", yaxis_title="Completion Rate (%)", hovermode="x unified",
                                        showlegend=False, height=400,
                                        margin=dict(t=50, b=50, l=50, r=50))
            st.plotly_chart(fig_completion, use_container_width=True)

    st.caption("Source: Hospital_Management_Updated_2024_2025.xlsx")