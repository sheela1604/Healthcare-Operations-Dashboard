import streamlit as st

# ======================================================
# GLOBAL PAGE CONFIG (ONLY ONCE)
# ======================================================
st.set_page_config(
    page_title="Healthcare Management Dashboard",
    layout="wide",
)

# ======================================================
# IMPORT PAGES AS MODULES
# ======================================================
from myPages import page1
from myPages import page2
from myPages import page3
from myPages import page4
from myPages import page5

# ======================================================
# PROFESSIONAL SIDEBAR DESIGN
# ======================================================
st.markdown("""
<style>

/* Sidebar background */
section[data-testid="stSidebar"] {
    background-color: #F8FAFC;
    padding-top: 20px;
}

/* Sidebar title */
.sidebar-title {
    font-size: 22px;
    font-weight: 700;
    color: #1E3A8A;
    margin-bottom: 5px;
}

/* Sidebar subtitle */
.sidebar-subtitle {
    font-size: 13px;
    color: #6B7280;
    margin-bottom: 25px;
}

/* Radio buttons spacing */
div[role="radiogroup"] > label {
    padding: 10px 8px;
    border-radius: 8px;
    transition: all 0.2s ease-in-out;
}

/* Hover effect */
div[role="radiogroup"] > label:hover {
    background-color: #E0E7FF;
}

/* Selected radio */
div[role="radiogroup"] > label[data-checked="true"] {
    background-color: #2563EB !important;
    color: white !important;
    font-weight: 600;
}

/* Section divider */
.sidebar-divider {
    height: 1px;
    background-color: #E5E7EB;
    margin: 20px 0;
}

</style>
""", unsafe_allow_html=True)

# ======================================================
# SIDEBAR CONTENT
# ======================================================
with st.sidebar:
    st.markdown("<div class='sidebar-title'>Healthcare Dashboard</div>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-subtitle'>Hospital Analytics System</div>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)

    selected_page = st.radio(
        "",
        [
            "Executive Overview",
            "Patient Demographics & Demand",
            "Clinical & Disease Intelligence",
            "Operational Efficiency & Capacity",
            "Staffing & Resource Optimization"
        ]
    )

    st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)

    # ======================================================
    # DATASET DOWNLOAD BUTTON (GLOBAL)
    # ======================================================
    st.markdown("### Download Dataset")

    with open("data/dataFinal.xlsx", "rb") as file:
        st.download_button(
            label="Download Full Dataset",
            data=file,
            file_name="Hospital_Dataset.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)

    st.caption("Version 1.0 | 2026")

# ======================================================
# PAGE ROUTING
# ======================================================
if selected_page == "Executive Overview":
    page1.run()

elif selected_page == "Patient Demographics & Demand":
    page2.run()

elif selected_page == "Clinical & Disease Intelligence":
    page3.run()

elif selected_page == "Operational Efficiency & Capacity":
    page4.run()

elif selected_page == "Staffing & Resource Optimization":
    page5.run()