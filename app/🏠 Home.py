import streamlit as st

st.set_page_config(
    page_title="Sous Vide simulation tool",
    page_icon="♨️",
)

st.write("# Welcome to the Sous Vide simulation tool")

st.markdown("""
            The simulation tool is based on the paper by Douglas E. Baldwin, 
            _Sous vide cooking: A review, International Journal of Gastronomy and Food Science_, 
            vol. 1(1), pp. 15–30 (2012). [Download PDF](https://douglasbaldwin.com/Baldwin-IJGFS-Preprint.pdf)

            The Thermal Diffusivity coefficients are taken from Pedro D. Sanz et al., 
            _Thermophysical Properties of Meat Products: General Bibliography and Experimental Values_ [Download PDF](https://www.researchgate.net/publication/286657774)
            """)

st.sidebar.success("Select a page from above.")