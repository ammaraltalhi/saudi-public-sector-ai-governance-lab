import streamlit as st

st.set_page_config(page_title="Saudi Public Sector AI Governance Lab", page_icon="⚖️", layout="wide")

pages = {
    "Governance Lab": [
        st.Page("views/home.py", title="Overview"),
        st.Page("views/use_case.py", title="AI Use Case Intake"),
        st.Page("views/risk_assessment.py", title="Risk Assessment"),
        st.Page("views/raci.py", title="RACI Matrix"),
        st.Page("views/inventory.py", title="AI Inventory"),
        st.Page("views/controls.py", title="Control Library"),
        st.Page("views/dashboard.py", title="Governance Dashboard"),
    ]
}

pg = st.navigation(pages)
pg.run()
