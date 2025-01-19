import streamlit as st

# Allow acces to the models 
import sys
from pathlib import Path
# Add the parent directory to the sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

st.set_page_config(
    page_title="Sous-vide simulation tool",
    page_icon="♨️",
)

st.markdown("""<p style="text-align: center;font-size: 2.75rem; font-weight:bold">Sous-vide simulation tool</p>""",unsafe_allow_html=True,)

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""<p style="text-align: center">Plan in advance cooking time or check progress at cooking time</p>""",unsafe_allow_html=True,)

col1, col2 = st.columns(2)
with col1:
    if st.button("Quick simulation (in advance)", icon="👨‍🍳", use_container_width=True, help="Compute time required to safely sous-vide cook a piece of meat with conservative presets"):
        st.switch_page("pages/1_👨‍🍳_Quick_Simulation.py")
with col2:
    if st.button("Check pasteurization (at cooking time)", icon="🌡️", use_container_width=True, help="At cooking time, collect real time temperature measurements and evalute pasteurization progress"):
        st.switch_page("pages/2_🌡️_Check_Pasteurization.py")

st.markdown("<br><br>", unsafe_allow_html=True)


with st.expander ("Advanced functionalities"):
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Advanced simulation", icon="♨️", use_container_width=True, help="Simulate the heat transfer with a full control on parameters and detailed results"):
            st.switch_page("pages/3_♨️_Advanced_Simulation.py")
    with col2:
        if st.button("Diffusivity estimation", icon="⚙️", use_container_width=True, help="Estimate the thermal diffusivity of a piece of meat based on a range of values"):
            st.switch_page("pages/4_⚙️_Diffusivity_Estimation.py")
    with col3:
        if st.button("Reference tables", icon="⚙️", use_container_width=True, help="Compute sensitivity of thermal stability/pasteurization time with respect to different parameters"):
            st.switch_page("pages/5_⚙️_Reference_Tables.py")

st.divider()
if st.button("Help", icon="❓", use_container_width=True, type="tertiary"):
    st.switch_page("pages/6_❓_Help.py")

# st.sidebar.success("Select a page from above.")

version_number = "0.2.2"
footer_html = f"""
    <div style="position: fixed; bottom: 0; width: 100%; display: flex; justify-content: flex-start; padding: 10px; font-size: 10px;">
        Sous-vide simulation tool v{version_number} | © 2025, Alessio Montone
    </div>
"""

# Inject the footer HTML into the Streamlit app
st.markdown(footer_html, unsafe_allow_html=True)