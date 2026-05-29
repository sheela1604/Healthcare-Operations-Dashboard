import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# =====================================================
# PAGE CONFIG
# =====================================================
# st.set_page_config(page_title="Operational Efficiency & Capacity", layout="wide")

def run():
    

    st.title("Operational Efficiency & Capacity")


    # =====================================================
    # LOAD DATA (MERGED VERSION OF ALL PARTS)
    # =====================================================
    @st.cache_data
    def load_data():
        file_path = "data/dataFinal.xlsx"
        xls = pd.ExcelFile(file_path)

        bed_records = xls.parse("BedRecords")
        bed = xls.parse("Bed")
        ward = xls.parse("Ward")
        department = xls.parse("Department")

        df = bed_records.merge(bed, on="bed_No", how="left")
        df = df.merge(ward, on="ward_No", how="left")
        df = df.merge(department, on="dept_Id", how="left")

        df['admission_Date'] = pd.to_datetime(df['admission_Date'])
        df['discharge_Date'] = pd.to_datetime(df['discharge_Date'])
        df['Length_of_Stay'] = (df['discharge_Date'] - df['admission_Date']).dt.days

        return df[df['Length_of_Stay'] >= 0]

    df = load_data()
    df_completed = df.dropna(subset=["discharge_Date"]).copy()

    # =====================================================
    # KPI — Hospital Average Length of Stay
    # =====================================================
    hospital_alos = df["Length_of_Stay"].mean()

    st.markdown(
        f"""
        <div style="
            font-size:22px;
            font-weight:600;
            color:#1B365D;
            margin-bottom:20px;
        ">
            Hospital Average Length of Stay: 
            <span style="font-size:28px; font-weight:700;">
                {hospital_alos:.2f} days
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # =====================================================
    # CUTOFF FOR DEC 2025 (AS IN PART-1)
    # =====================================================
    cutoff_date = pd.Timestamp("2025-12-01")

    #----------------------------------------------------------------------------------------------------

    df["Month"] = df["admission_Date"].dt.to_period("M").astype(str)
    df_completed["Month"] = df_completed["discharge_Date"].dt.to_period("M").astype(str)

    monthly_admissions = (
        df.groupby("Month")["admission_Id"]
        .count()
        .reset_index()
    )

    monthly_discharges = (
        df_completed.groupby("Month")["admission_Id"]
        .count()
        .reset_index()
    )

    monthly_summary = pd.merge(
        monthly_admissions,
        monthly_discharges,
        on="Month",
        how="outer",
        suffixes=("_Admissions", "_Discharges")
    ).fillna(0)

    monthly_summary = monthly_summary.sort_values("Month")

    # REMOVE INCOMPLETE MONTH (PART-3 LOGIC KEPT)
    avg_adm_before = monthly_summary["admission_Id_Admissions"].mean()
    last_month = monthly_summary["Month"].max()

    last_month_adm = monthly_summary.loc[
        monthly_summary["Month"] == last_month,
        "admission_Id_Admissions"
    ].values[0]

    if last_month_adm < (avg_adm_before * 0.5):
        monthly_summary = monthly_summary[
            monthly_summary["Month"] != last_month
        ]

    # =====================================================




    col1, col2 = st.columns([1,2])

    with col1:
        
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader("Length of Stay Distribution")

        los_df = df[df['discharge_Date'] < cutoff_date]

        fig1, ax1 = plt.subplots(figsize=(6,5), constrained_layout=True)
        sns.histplot(los_df['Length_of_Stay'],bins=20,kde=True,color="#93C5FD",edgecolor="black",linewidth=0.5,ax=ax1)

        # Make KDE line darker and thicker
        for line in ax1.lines:
            line.set_color("#1E3A8A")   # Dark navy line
            line.set_linewidth(2)
        
        ax1.set_title("Length of Stay Distribution")
        
        st.pyplot(fig1)
        plt.close(fig1)

        st.markdown('</div>', unsafe_allow_html=True)


    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader("Deviation from Hospital Average Length of Stay")

        overall_avg = df["Length_of_Stay"].mean()

        dept_los = df.groupby('dept_Name')['Length_of_Stay'].mean()
        dept_diff = (dept_los - overall_avg).sort_values()

        fig2, ax2 = plt.subplots(figsize=(11,5), constrained_layout=True)

        colors = ["#C0392B" if x > 0 else "#1F618D" for x in dept_diff]
        bars = ax2.bar(dept_diff.index, dept_diff.values, color=colors)

        ax2.axhline(0, color='black', linewidth=1)
        ax2.set_ylabel("Days Above / Below Hospital Average")
        ax2.set_title("Deviation from Hospital Average")

        plt.xticks(rotation=45, ha='right', fontsize=9)

        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2,
                    height,
                    f"{height:.2f}",
                    ha='center',
                    va='bottom' if height > 0 else 'top',
                    fontsize=7)

        st.pyplot(fig2)
        plt.close(fig2)

        st.markdown('</div>', unsafe_allow_html=True)



    col3, col4 = st.columns(2)

    with col3:
        # st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader("Admission vs Discharge Trend")

        admissions_df = df[df['admission_Date'] < cutoff_date]
        discharges_df = df[df['discharge_Date'] < cutoff_date]

        monthly_admissions = admissions_df.groupby(
            admissions_df['admission_Date'].dt.to_period('M').astype(str)
        )['patient_Id'].count()

        monthly_discharges = discharges_df.groupby(
            discharges_df['discharge_Date'].dt.to_period('M').astype(str)
        )['patient_Id'].count()

        plt.figure(figsize=(6,5))
        monthly_admissions.plot(label="Admissions")
        monthly_discharges.plot(label="Discharges")
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(plt)
        plt.clf()
        # st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        # st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader("Monthly Admission Trend")

        plt.figure(figsize=(6,5))
        sns.lineplot(
            data=monthly_summary,
            x="Month",
            y="admission_Id_Admissions",
            marker="o"
        )
        plt.xticks(rotation=45)
        plt.ylabel("Admissions")
        st.pyplot(plt)
        plt.clf()
        # st.markdown('</div>', unsafe_allow_html=True)


    with st.container():
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader("Department Workload Heatmap")

        heat_data = df.groupby(['ward_Name', 'dept_Name']).size().unstack(fill_value=0)

        fig2, ax2 = plt.subplots(figsize=(12, 5))
        sns.heatmap(heat_data, annot=True, fmt="d", cmap="Blues", cbar=False, ax=ax2)

        ax2.set_xlabel("Medical Specialty")
        ax2.set_ylabel("Ward Unit")

        st.pyplot(fig2)
        st.markdown('</div>', unsafe_allow_html=True)

    total_beds = df["bed_No"].nunique()
    avg_monthly_admissions = monthly_summary["admission_Id_Admissions"].mean()
    avg_monthly_discharges = monthly_summary["admission_Id_Discharges"].mean()
    total_discharges = df_completed["admission_Id"].nunique()
    annual_btr = total_discharges / total_beds

    monthly_summary["Monthly_BTR"] = (
        monthly_summary["admission_Id_Discharges"] / total_beds
    )

    avg_monthly_btr = monthly_summary["Monthly_BTR"].mean()

    with st.container():
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader("Monthly Bed Turnover Rate")

        plt.figure(figsize=(10,5))
        sns.barplot(
            data=monthly_summary,
            x="Month",
            y="Monthly_BTR",
            color='#a78bfa' 
        )
        plt.xticks(rotation=45)
        plt.ylabel("Turnover Rate")
        st.pyplot(plt)
        plt.clf()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### Monthly Admission vs Discharge Summary")

    st.dataframe(
        monthly_summary.rename(columns={
            "admission_Id_Admissions": "Admissions",
            "admission_Id_Discharges": "Discharges",
            "Monthly_BTR": "Bed Turnover Rate"
        }),
        use_container_width=True
    )

