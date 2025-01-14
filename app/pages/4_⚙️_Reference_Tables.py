import streamlit as st 
import numpy as np
import pandas as pd
from matplotlib import colormaps
from matplotlib.colors import Normalize
import plotly.graph_objects as go

from models.parameters import MeatSimulationParameters, LOG_REDUCTION_MIN_THRESHOLD
from models.solvers import SimulateMeat
from models.solvers import LogReduction
from models.helpers import seconds_to_hhmm

# Allow acces to the models 
import sys
from pathlib import Path
# Add the parent directory to the sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

st.set_page_config(
    page_title="Sous Vide simulation tool",
    page_icon="♨️",
)

st.title("⚙️ Reference tables")

## Sidebar - Input parameters for the simulation
################################################

st.sidebar.header("⚙️ Parameters")

option = st.sidebar.selectbox(
    "Select table type",
    ("Heating", "Pasteurization"),
)

st.sidebar.markdown("---")

if option == "Heating":
    thickness = st.sidebar.slider("Thickness (mm):", min_value=10,max_value=115, value=(10,60), step=5)
    shape_options = {
        "🥩 Slab": "slab",
        "🍖 Cylinder": "cylinder",
        "🟤 Sphere": "sphere"
    }
    shape = shape_options[st.sidebar.selectbox("Shape:", shape_options.keys())]
    initial_temperature = st.sidebar.number_input("Food Initial Temperature (°C):", value=5.0, step=0.5, format="%.1f")
    roner_termperature = st.sidebar.number_input("Roner Temperature (°C):", value=58.0, step=0.5, format="%.1f")
    final_time = st.sidebar.number_input("Simulation Time (h):", value=6, step=1)
    thermal_diffusivity = st.sidebar.slider("[α] Thermal Diffusivity (10⁻⁷ m²/s):", min_value=1.10, max_value=1.80, value=1.40, step=0.01, format="%.2f")
    heat_transfer = st.sidebar.number_input("[h] Surface Heat Transfer Coefficient (W/m²-K):", value=95, step=1)
    thermal_conductivity = st.sidebar.number_input("[k] Thermal Conductivity (W/m-K):", value=0.48, step=0.01, format="%.2f")
elif option == "Pasteurization":
    #TODO: Implement
    st.write("TO BE IMPLEMENTED") 


# Display Simulation results
if st.sidebar.button("Run Simulation"):
    with st.spinner("Running simulation..."):
        if option == "Heating":
            
            # Initialize parameters
            msp = MeatSimulationParameters()
            msp.T_initial = initial_temperature
            msp.T_fluid = roner_termperature
            msp.simulation_hours = final_time
            msp.alpha = thermal_diffusivity * 1e-7
            msp.h = heat_transfer
            msp.k = thermal_conductivity
            r_values = msp.r_values
            thermal_stability_threshold = msp.thermal_stability_threshold    
            
            result = []
            for curr_thickness in range (thickness[0], thickness[1]+1, 5):
                msp.define_meat_shape(shape=shape,thickness_mm=curr_thickness)
                T_sol, time_points, second_stability_reached = SimulateMeat(msp)
                
                st.toast(f"Simulation for {curr_thickness}mm completed and thermal stability found at {seconds_to_hhmm(second_stability_reached)}", icon="ℹ️")
                result.append({"Thickness (mm)": curr_thickness, "Time (h:mm)": f"{seconds_to_hhmm(second_stability_reached)}"})
            
            st.write("Estimated heating time:")
            st.dataframe(pd.DataFrame(result))
            
        elif option == "Pasteurization":
            raise NotImplementedError("Pasteurization simulation is not implemented yet.")

