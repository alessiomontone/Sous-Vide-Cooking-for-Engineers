import streamlit as st 

st.set_page_config(
    page_title="Sous Vide simulation tool",
    page_icon="♨️",
)

st.title("❓ Help")

st.write("Quick guide for basic funcionalities")

with st.expander ("**How to run a simple simulation?**"):
    st.markdown("""
                * Go to the "Quick simulation Page"
                * Select the food inital temperature and roner temperature
                * Select time you are foreseeing starting cooking
                * Press "Run Simulation" and check results                
                """)
    st.video("https://youtu.be/bPIrgbWuKXA")

with st.expander ("**How to check pasteurization progress while cooking?**"):
    st.markdown("""
                * Go to the "Check pasteurization page"
                * Set the roner temperature
                * Start adding measured food temperature in the middle (e.g., one every 20 minutes for the first hour) 
                * Look at the estimated pasteurization time               
                """)
    st.video("https://youtu.be/o_31AqXmDdM")

with st.expander("What are the scientifc basis of these simulations?"):
    st.markdown("""
            **References:**
            
            The simulation tool is based on the paper by Douglas E. Baldwin, 
            _Sous vide cooking: A review, International Journal of Gastronomy and Food Science_, 
            vol. 1(1), pp. 15–30 (2012). [Download PDF](https://douglasbaldwin.com/Baldwin-IJGFS-Preprint.pdf)

            The Thermal Diffusivity coefficients are taken from Pedro D. Sanz et al., 
            _Thermophysical Properties of Meat Products: General Bibliography and Experimental Values_ [Download PDF](https://www.researchgate.net/publication/286657774)
            """)


st.divider()

st.write("[👉Full Documentation](https://alessiomontone.github.io/Sous-Vide-Cooking-for-Engineers/introduction.html), including User Guide, source code documentation and underlying math")
