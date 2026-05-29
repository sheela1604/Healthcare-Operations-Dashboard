import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Page Configuration
# st.set_page_config(page_title="Patient Demographics & Demand Analysis", layout="wide")
def run():
    st.title("Patient Demographics & Demand Analysis")

    # ---------------- LOAD DATA ----------------
    @st.cache_data
    def load_data():
        file_path = "data/dataFinal.xlsx"
        patients = pd.read_excel(file_path, sheet_name="Patients")
        appointments = pd.read_excel(file_path, sheet_name="Appointment")
        return patients, appointments

    patients, appointments = load_data()

    # Merge patients with appointments
    data = pd.merge(appointments, patients, on="patient_Id", how="left")

    # Convert dates
    data["appointment_Date"] = pd.to_datetime(data["appointment_Date"], errors="coerce")
    data["Date_Of_Birth"]    = pd.to_datetime(data["Date_Of_Birth"],    errors="coerce")

    # Calculate Age
    today = pd.Timestamp.today()
    data["Age"] = (today - data["Date_Of_Birth"]).dt.days // 365

    # Create Age Groups
    bins   = [0, 18, 30, 45, 60, 75, 100]
    labels = ["0-18", "19-30", "31-45", "46-60", "61-75", "76+"]
    data["Age_Group"] = pd.cut(data["Age"], bins=bins, labels=labels)

    # Extract time features
    data["Appointment_Hour"] = data["appointment_Date"].dt.hour
    data["Month"]            = data["appointment_Date"].dt.month
    data["Month_Name"]       = data["appointment_Date"].dt.strftime("%b")
    data["Year"]             = data["appointment_Date"].dt.year
    data["Day_of_Week"]      = data["appointment_Date"].dt.day_name()

    # Shared constants
    MONTH_ORDER = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    YEAR_COLORS = {2024: "#3498DB", 2025: "#E67E22"}

    # Pre-build monthly counts
    monthly_counts = (
        data.groupby(["Year", "Month", "Month_Name"])
        .size()
        .reset_index(name="Count")
        .sort_values(["Year", "Month"])
    )
    valid_years    = data.groupby("Year")["Month"].nunique()
    valid_years    = valid_years[valid_years >= 6].index.tolist()
    monthly_counts = monthly_counts[monthly_counts["Year"].isin(valid_years)]

    # ---------------- SIDEBAR FILTERS (from main.py) ----------------
    st.sidebar.header("Filter Data")

    min_age = int(data["Age"].min())
    max_age = int(data["Age"].max())

    age_range = st.sidebar.slider(
        "Select Age Range",
        min_value=min_age,
        max_value=max_age,
        value=(min_age, max_age)
    )

    gender_options = data["Gender"].dropna().unique().tolist()
    selected_gender = st.sidebar.multiselect(
        "Select Gender",
        options=gender_options,
        default=gender_options
    )

    # Apply filters
    filtered_data = data[
        (data["Age"].between(age_range[0], age_range[1])) &
        (data["Gender"].isin(selected_gender))
    ]

    # ---------------- KPI SECTION ----------------
    # 3 KPIs: Top Visit Reason, Peak Age Group, Top City
    most_common_reason = filtered_data["reason"].mode()[0] if not filtered_data["reason"].isna().all() else "N/A"
    peak_age_group     = filtered_data["Age_Group"].mode()[0] if not filtered_data["Age_Group"].isna().all() else "N/A"
    top_city           = filtered_data["city"].value_counts().index[0] if not filtered_data["city"].isna().all() else "N/A"

    # Custom CSS for KPI boxes
    st.markdown("""
        <style>
        .kpi-box {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 10px;
            padding: 18px 16px 14px 16px;
            text-align: center;
            height: 100%;
        }
        .kpi-label {
            font-size: 13px;
            color: #6c757d;
            font-weight: 600;
            margin-bottom: 6px;
            letter-spacing: 0.03em;
            text-transform: uppercase;
        }
        .kpi-value {
            font-size: 26px;
            font-weight: 700;
            color: #1a1a2e;
            line-height: 1.2;
        }
        </style>
    """, unsafe_allow_html=True)

    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

    reason_display = most_common_reason[:18] + "..." if len(str(most_common_reason)) > 18 else most_common_reason

    with kpi_col1:
        st.markdown(f"""
            <div class="kpi-box">
                <div class="kpi-label">Top Visit Reason</div>
                <div class="kpi-value">{reason_display}</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_col2:
        st.markdown(f"""
            <div class="kpi-box">
                <div class="kpi-label">Peak Age Group</div>
                <div class="kpi-value">{str(peak_age_group)}</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_col3:
        st.markdown(f"""
            <div class="kpi-box">
                <div class="kpi-label">Top City</div>
                <div class="kpi-value">{top_city}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    # ---------------- INDIA MAP SECTION ----------------
    st.markdown("### Patient Distribution Across India")

    city_coordinates = {
        # Metro Cities
        "Delhi":              (28.6139, 77.2090,  "Delhi"),
        "Mumbai":             (19.0760, 72.8777,  "Maharashtra"),
        "Bangalore":          (12.9716, 77.5946,  "Karnataka"),
        "Chennai":            (13.0827, 80.2707,  "Tamil Nadu"),
        "Kolkata":            (22.5726, 88.3639,  "West Bengal"),
        "Hyderabad":          (17.3850, 78.4867,  "Telangana"),
        # Tier 1
        "Ahmedabad":          (23.0225, 72.5714,  "Gujarat"),
        "Pune":               (18.5204, 73.8567,  "Maharashtra"),
        "Jaipur":             (26.9124, 75.7873,  "Rajasthan"),
        "Lucknow":            (26.8467, 80.9462,  "Uttar Pradesh"),
        "Kanpur":             (26.4499, 80.3319,  "Uttar Pradesh"),
        "Nagpur":             (21.1458, 79.0882,  "Maharashtra"),
        "Indore":             (22.7196, 75.8577,  "Madhya Pradesh"),
        "Bhopal":             (23.2599, 77.4126,  "Madhya Pradesh"),
        "Visakhapatnam":      (17.6868, 83.2185,  "Andhra Pradesh"),
        # Tier 2
        "Patna":              (25.5941, 85.1376,  "Bihar"),
        "Vadodara":           (22.3072, 73.1812,  "Gujarat"),
        "Ghaziabad":          (28.6692, 77.4538,  "Uttar Pradesh"),
        "Ludhiana":           (30.9010, 75.8573,  "Punjab"),
        "Agra":               (27.1767, 78.0081,  "Uttar Pradesh"),
        "Nashik":             (19.9975, 73.7898,  "Maharashtra"),
        "Faridabad":          (28.4089, 77.3178,  "Haryana"),
        "Meerut":             (28.9845, 77.7064,  "Uttar Pradesh"),
        "Rajkot":             (22.3039, 70.8022,  "Gujarat"),
        "Varanasi":           (25.3176, 82.9739,  "Uttar Pradesh"),
        "Srinagar":           (34.0837, 74.7973,  "Jammu and Kashmir"),
        "Amritsar":           (31.6340, 74.8723,  "Punjab"),
        "Allahabad":          (25.4358, 81.8463,  "Uttar Pradesh"),
        "Ranchi":             (23.3441, 85.3096,  "Jharkhand"),
        "Howrah":             (22.5958, 88.2636,  "West Bengal"),
        "Coimbatore":         (11.0168, 76.9558,  "Tamil Nadu"),
        "Jabalpur":           (23.1815, 79.9864,  "Madhya Pradesh"),
        "Gwalior":            (26.2183, 78.1828,  "Madhya Pradesh"),
        "Vijayawada":         (16.5062, 80.6480,  "Andhra Pradesh"),
        "Jodhpur":            (26.2389, 73.0243,  "Rajasthan"),
        "Madurai":            (9.9252,  78.1198,  "Tamil Nadu"),
        "Raipur":             (21.2514, 81.6296,  "Chhattisgarh"),
        "Kota":               (25.2138, 75.8648,  "Rajasthan"),
        "Chandigarh":         (30.7333, 76.7794,  "Chandigarh"),
        "Guwahati":           (26.1445, 91.7362,  "Assam"),
        "Thiruvananthapuram": (8.5241,  76.9366,  "Kerala"),
        "Bhubaneswar":        (20.2961, 85.8245,  "Odisha"),
        "Dehradun":           (30.3165, 78.0322,  "Uttarakhand"),
    }

    patients_copy = patients.copy()
    patients_copy["city"] = patients_copy["city"].astype(str).str.strip().str.title()
    city_counts_map = patients_copy.groupby("city").size().reset_index(name="Patient_Count")

    def get_coordinates(city_name):
        return city_coordinates.get(city_name, (None, None, None))

    city_counts_map[["lat", "lon", "state"]] = city_counts_map["city"].apply(
        lambda x: pd.Series(get_coordinates(x))
    )
    # Keep only top 15 mapped cities
    city_counts_mapped = city_counts_map.dropna().nlargest(15, "Patient_Count")

    if len(city_counts_mapped) > 0:
        min_val = city_counts_mapped["Patient_Count"].min()
        max_val = city_counts_mapped["Patient_Count"].max()

        fig_map = px.scatter_mapbox(
            city_counts_mapped,
            lat="lat",
            lon="lon",
            color="Patient_Count",
            size="Patient_Count",
            hover_name="city",
            hover_data={"Patient_Count": True, "state": True, "lat": False, "lon": False},
            zoom=3.8,
            center=dict(lat=22.5937, lon=78.9629),
            mapbox_style="carto-positron",
            color_continuous_scale=[[0.0, "#F7D410"], [1.0, "#E31906"]],
            range_color=(min_val, max_val),
            size_max=30
        )
        fig_map.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            coloraxis_colorbar=dict(title="Patient Count", thickness=20, len=0.7),
            height=520
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("No cities could be mapped to coordinates. Please check city names in the dataset.")

    st.markdown("---")

    # ---------------- PATIENT DEMOGRAPHICS ----------------
    st.markdown("### Patient Demographics")

    col1, col2 = st.columns(2)

    # 1 — Gender Distribution (Donut Chart) — uses filtered_data
    with col1:
        st.subheader("Gender Distribution")
        gender_counts = filtered_data["Gender"].value_counts()
        fig1 = go.Figure(data=[go.Pie(
            labels=gender_counts.index,
            values=gender_counts.values,
            hole=0.4,
            marker=dict(colors=["#FF6B6B", "#4ECDC4", "#95E1D3"]),
            textfont=dict(size=13)
        )])
        fig1.update_layout(
            showlegend=True,
            legend=dict(font=dict(size=13, color="#2C3E50", family="Arial Black")),
            height=350,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig1, use_container_width=True)

    # 2 — Age Groups (Horizontal Lollipop Chart) — uses filtered_data
    with col2:
        st.subheader("Age Groups")
        age_group_counts = filtered_data["Age_Group"].value_counts().sort_index()
        ag_labels = age_group_counts.index.astype(str).tolist()
        ag_values = age_group_counts.values.tolist()

        fig3 = go.Figure()

        # Horizontal stems (x0=0 to x1=value, y fixed at label)
        for lbl, val in zip(ag_labels, ag_values):
            fig3.add_shape(
                type="line",
                x0=0,   x1=val,
                y0=lbl, y1=lbl,
                line=dict(color="#9B59B6", width=2)
            )

        # Dots at end of each stem
        fig3.add_trace(go.Scatter(
            x=ag_values,
            y=ag_labels,
            mode="markers",
            marker=dict(color="#9B59B6", size=14, line=dict(color="white", width=2)),
            hovertemplate="Age Group: %{y}<br>Patients: %{x}<extra></extra>"
        ))

        fig3.update_layout(
            xaxis_title="Patients",
            yaxis_title="Age Group",
            xaxis=dict(
                tickfont=dict(size=13, color="#2C3E50", family="Arial Black"),
                title_font=dict(size=13, color="#2C3E50", family="Arial Black"),
                rangemode="tozero"
            ),
            yaxis=dict(
                tickfont=dict(size=13, color="#2C3E50", family="Arial Black"),
                title_font=dict(size=13, color="#2C3E50", family="Arial Black")
            ),
            height=350,
            margin=dict(l=20, r=20, t=30, b=20),
            showlegend=False,
            plot_bgcolor="rgba(248,249,250,0.8)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        fig3.update_xaxes(showgrid=True, gridcolor="rgba(200,200,200,0.4)")
        fig3.update_yaxes(showgrid=False)
        st.plotly_chart(fig3, use_container_width=True)

    # 3 — Top 10 Cities by Patient Count — Horizontal Bar Chart
    st.subheader("Top 10 Cities by Patient Count")

    city_counts_top = filtered_data["city"].value_counts().head(10).reset_index()
    city_counts_top.columns = ["City", "Patients"]
    city_counts_top = city_counts_top.sort_values("Patients", ascending=True)

    fig_city = go.Figure()
    fig_city.add_trace(go.Bar(
        x=city_counts_top["Patients"],
        y=city_counts_top["City"],
        orientation="h",
        marker=dict(color="#E74C3C"),
        hovertemplate="City: %{y}<br>Patients: %{x}<extra></extra>"
    ))

    fig_city.update_layout(
        xaxis_title="Number of Patients",
        yaxis_title="",
        xaxis=dict(
            tickfont=dict(size=13, color="#2C3E50", family="Arial Black"),
            title_font=dict(size=13, color="#2C3E50", family="Arial Black")
        ),
        yaxis=dict(
            tickfont=dict(size=13, color="#2C3E50", family="Arial Black")
        ),
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=False,
        plot_bgcolor="rgba(248,249,250,0.8)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    fig_city.update_xaxes(showgrid=True, gridcolor="rgba(200,200,200,0.4)")
    fig_city.update_yaxes(showgrid=False)
    st.plotly_chart(fig_city, use_container_width=True)

    st.markdown("---")

    # ---------------- DEMAND ANALYSIS ----------------
    st.markdown("### Demand Analysis")

    # Row 1: Peak Appointment Months (left) + Payment Methods Pie (right)
    col7, col8 = st.columns(2)

    # Peak Appointment Months — Grouped Bar (2024 vs 2025)
    with col7:
        st.subheader("Peak Appointment Months")

        fig_months = go.Figure()

        for year in sorted(monthly_counts["Year"].unique()):
            yd = monthly_counts[monthly_counts["Year"] == year].copy()
            yd["Month_Name"] = pd.Categorical(yd["Month_Name"], categories=MONTH_ORDER, ordered=True)
            yd = yd.sort_values("Month_Name")
            fig_months.add_trace(go.Bar(
                name=str(year),
                x=yd["Month_Name"],
                y=yd["Count"],
                marker=dict(color=YEAR_COLORS.get(year, "#95A5A6"), opacity=0.85),
                hovertemplate=f"<b>{year}</b><br>Month: %{{x}}<br>Appointments: %{{y}}<extra></extra>"
            ))

        peak_row = monthly_counts.loc[monthly_counts["Count"].idxmax()]
        fig_months.add_annotation(
            x=peak_row["Month_Name"], y=peak_row["Count"],
            text=f"Peak: {int(peak_row['Count'])}",
            showarrow=True, arrowhead=2,
            arrowcolor="#E74C3C",
            font=dict(color="#E74C3C", size=12),
            yshift=10,
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#E74C3C", borderwidth=1, borderpad=3
        )

        fig_months.update_layout(
            barmode="group",
            xaxis_title="Month",
            yaxis_title="Number of Appointments",
            legend_title="Year",
            xaxis=dict(
                tickfont=dict(size=13, color="#2C3E50", family="Arial Black"),
                title_font=dict(size=13, color="#2C3E50", family="Arial Black"),
                categoryorder="array",
                categoryarray=MONTH_ORDER
            ),
            yaxis=dict(
                tickfont=dict(size=13, color="#2C3E50", family="Arial Black"),
                title_font=dict(size=13, color="#2C3E50", family="Arial Black")
            ),
            height=420,
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor="rgba(248,249,250,0.8)",
            paper_bgcolor="rgba(0,0,0,0)",
            bargap=0.15,
            bargroupgap=0.05
        )
        fig_months.update_xaxes(showgrid=False)
        fig_months.update_yaxes(showgrid=True, gridcolor="rgba(200,200,200,0.4)")
        st.plotly_chart(fig_months, use_container_width=True)

    # Payment Methods Pie — sits beside Peak Months
    with col8:
        st.subheader("Payment Methods")

        payment_counts = filtered_data["mode_of_payment"].value_counts()

        fig_pay = go.Figure(data=[go.Pie(
            labels=payment_counts.index,
            values=payment_counts.values,
            hole=0,
            marker=dict(colors=["#2ECC71", "#3498DB", "#9B59B6", "#E67E22", "#E74C3C", "#1ABC9C"]),
            textfont=dict(size=13),
            hovertemplate="Method: %{label}<br>Count: %{value}<br>Share: %{percent}<extra></extra>"
        )])

        fig_pay.update_layout(
            showlegend=True,
            legend=dict(font=dict(size=13, color="#2C3E50", family="Arial Black")),
            height=420,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_pay, use_container_width=True)

    # Row 2: Appointment Trend Line Chart — full width below
    st.subheader("Appointment Trend: 2024 vs 2025")

    fig_line = go.Figure()

    line_styles = {
        2024: dict(color="#3498DB", width=3),
        2025: dict(color="#E67E22", width=3),
    }

    for year in sorted(monthly_counts["Year"].unique()):
        yd = monthly_counts[monthly_counts["Year"] == year].copy()
        yd["Month_Name"] = pd.Categorical(yd["Month_Name"], categories=MONTH_ORDER, ordered=True)
        yd = yd.sort_values("Month_Name")
        style = line_styles.get(year, dict(color="#95A5A6", width=2))
        fig_line.add_trace(go.Scatter(
            x=yd["Month_Name"], y=yd["Count"],
            mode="lines+markers",
            name=str(year),
            line=dict(color=style["color"], width=style["width"]),
            marker=dict(size=8, color=style["color"], symbol="circle",
                        line=dict(color="white", width=1.5)),
            hovertemplate=f"<b>{year}</b><br>Month: %{{x}}<br>Appointments: %{{y}}<extra></extra>"
        ))

    d24 = monthly_counts[monthly_counts["Year"] == 2024].sort_values("Month")
    d25 = monthly_counts[monthly_counts["Year"] == 2025].sort_values("Month")
    common = sorted(set(d24["Month_Name"]) & set(d25["Month_Name"]),
                    key=lambda m: MONTH_ORDER.index(m))
    d24c = d24[d24["Month_Name"].isin(common)].sort_values("Month")
    d25c = d25[d25["Month_Name"].isin(common)].sort_values("Month")
    fig_line.add_trace(go.Scatter(
        x=list(d24c["Month_Name"]) + list(d25c["Month_Name"])[::-1],
        y=list(d24c["Count"])     + list(d25c["Count"])[::-1],
        fill="toself",
        fillcolor="rgba(52,152,219,0.08)",
        line=dict(color="rgba(0,0,0,0)"),
        showlegend=False,
        hoverinfo="skip"
    ))

    fig_line.update_layout(
        xaxis_title="Month",
        yaxis_title="Number of Appointments",
        legend_title="Year",
        xaxis=dict(
            tickfont=dict(size=13, color="#2C3E50", family="Arial Black"),
            title_font=dict(size=13, color="#2C3E50", family="Arial Black"),
            categoryorder="array",
            categoryarray=MONTH_ORDER
        ),
        yaxis=dict(
            tickfont=dict(size=13, color="#2C3E50", family="Arial Black"),
            title_font=dict(size=13, color="#2C3E50", family="Arial Black")
        ),
        height=380,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="rgba(248,249,250,0.8)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified"
    )
    fig_line.update_xaxes(showgrid=True, gridcolor="rgba(200,200,200,0.4)")
    fig_line.update_yaxes(showgrid=True, gridcolor="rgba(200,200,200,0.4)")
    st.plotly_chart(fig_line, use_container_width=True)