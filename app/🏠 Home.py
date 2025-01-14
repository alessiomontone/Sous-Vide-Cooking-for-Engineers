import streamlit as st

st.set_page_config(
    page_title="Sous Vide simulation tool",
    page_icon="♨️",
)

st.write("# Welcome to the Sous Vide simulation tool")

st.markdown("""
            
            For most users, a **<a href='/Quick_Simulation' target='_self'>🏃 Quick Simulation</a>** would be fine: compute time required to safely sous-vide cook a piece of meat with conservative presets.
            """,unsafe_allow_html=True)
            

st.markdown("""
            
            Furthermore you may want most advanced functionalities:
            
            * **♨️ Advanced Simulation**: if you want to simulate the heat transfer with a full control on parameters and detailed results
            * **⚙️ Diffusivity Estimation**: if you want to estimate the thermal diffusivity of a piece of meat based on a range of values
            
            
            **Refereces:**
            
            The simulation tool is based on the paper by Douglas E. Baldwin, 
            _Sous vide cooking: A review, International Journal of Gastronomy and Food Science_, 
            vol. 1(1), pp. 15–30 (2012). [Download PDF](https://douglasbaldwin.com/Baldwin-IJGFS-Preprint.pdf)

            The Thermal Diffusivity coefficients are taken from Pedro D. Sanz et al., 
            _Thermophysical Properties of Meat Products: General Bibliography and Experimental Values_ [Download PDF](https://www.researchgate.net/publication/286657774)
            """)

st.sidebar.success("Select a page from above.")