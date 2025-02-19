import streamlit as st 
import numpy as np
import pandas as pd
from matplotlib import colormaps
from matplotlib.colors import Normalize
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Allow acces to the models 
import sys
from pathlib import Path
# Add the parent directory to the sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from models.parameters import MeatSimulationParameters, LOG_REDUCTION_MIN_THRESHOLD
from models.solvers import SimulateMeat
from models.solvers import LogReduction
from models.helpers import seconds_to_hhmm_pretty, update_progress_bar

REFERENCE_TABLE_TYPE_STATUS = "RefTable_type_Status"
REFERENCE_TABLE_STATUS = "RefTable_Status"
EMPTY_SELECTION = " "

st.set_page_config(
    page_title="Sous vide simulation tool",
    page_icon="♨️",
)

st.title("⚙️ Reference tables")

intro = st.markdown("""
                    This page will generate reference tables regarding Sous-Vide heating and pasteurization iterating through different parameter values:\\
                    👈 Parameters can be set in the sidebar.

                    * **Heating time** simulates required time to reach thermal stability depending on different thicknesses and shapes of the meat
                        (i.e., it will recreate Table 1 of Baldwin's paper)
                    * **Pasteurization** simulates required time to reach pasteurization depending on different thicknesses and Roner temperatures 
                       (i.e., it will recreate Table 2 of Baldwin's paper)
                    """)
## Sidebar - Input parameters for the simulation
################################################

st.sidebar.header("⚙️ Parameters")

# Initialize session state to track user's choice
if REFERENCE_TABLE_TYPE_STATUS not in st.session_state:
    st.session_state[REFERENCE_TABLE_TYPE_STATUS] = EMPTY_SELECTION

# Dropdown with dynamic options
if st.session_state[REFERENCE_TABLE_TYPE_STATUS] == EMPTY_SELECTION:
    options = [EMPTY_SELECTION, "Heating", "Pasteurization"]  # Include placeholder
else:
    options = ["Heating", "Pasteurization"]  # Remove placeholder after selection

# Render the dropdown
option = st.sidebar.selectbox("Choose a Table:", options, key=REFERENCE_TABLE_TYPE_STATUS)

st.sidebar.markdown("---")

## Run Simulations
##################

if option == "Heating":
    thickness = st.sidebar.slider("Thickness (mm):", min_value=5,max_value=115, value=(5,115), step=5)
    
    if thickness[0]<10:
        st.sidebar.warning("For thicknesses below 10mm, each simulation may require several minutes", icon="⚠️")
    
    shape_options = {
        "🥩 Slab": "slab",
        "🍖 Cylinder": "cylinder",
        "🟤 Sphere": "sphere"
    }
    shapes = [shape_options[key] for key in st.sidebar.multiselect("Shape:", shape_options.keys()) if key in shape_options.keys()]
    if len(shapes) == 0:
        st.sidebar.warning("Please select at least one shape", icon="⚠️")
    
    if "slab" in shapes:
        correct_beta_for_large_slabs = st.sidebar.checkbox(label="Correct Beta for large values of slab thickenss (>30mm)", value = False, 
                                                        help="For computaton of Table 1 in Baldwin's paper it has not been used")
    else:
        correct_beta_for_large_slabs = None
    
    initial_temperature = st.sidebar.number_input("Food Initial Temperature (°C):", value=5.0, step=0.5, format="%.1f")
    roner_termperature = st.sidebar.number_input("Roner Temperature (°C):",min_value=54.0, value=58.0, step=0.5, format="%.1f")
    simulation_time_h_int = st.sidebar.number_input("Simulation Time (h):",min_value=1, value=6, step=1)
    thermal_diffusivity = st.sidebar.slider("[α] Thermal Diffusivity (10⁻⁷ m²/s):", min_value=1.10, max_value=1.80, value=1.40, step=0.01, format="%.2f")
    heat_transfer = st.sidebar.number_input("[h] Surface Heat Transfer Coefficient (W/m²-K):",min_value=1, value=95, step=1)
    thermal_conductivity = st.sidebar.number_input("[k] Thermal Conductivity (W/m-K):",min_value=0.01, value=0.48, step=0.01, format="%.2f")
    if len(shapes)>0:
        if st.sidebar.button("Run heating simulations", use_container_width=True):
            intro.empty()    
            # Initialize parameters
            msp = MeatSimulationParameters()
            msp.T_initial = initial_temperature
            msp.T_fluid = roner_termperature
            msp.simulation_hours = simulation_time_h_int
            msp.alpha = thermal_diffusivity * 1e-7
            msp.h = heat_transfer
            msp.k = thermal_conductivity
            radius_values_list = msp.list_radius_values
            thermal_stability_threshold = msp.thermal_stability_threshold    
            
            result = []
            total_combinations = len(shapes) * ((thickness[1]-thickness[0])//5 + 1)
            curr_idx = 0
            overall_progress_bar = st.progress(0,text="Preparing simulation...")
            for curr_thickness in range (thickness[0], thickness[1]+1, 5):
                dict_result = {"Thickness (mm)": curr_thickness}
                for curr_shape in shapes:
                    
                    # Manage overall and current iteration progress bars
                    overall_progress_bar.progress(curr_idx/total_combinations, f"Table computation. Running simulation for {curr_shape}-{curr_thickness}mm")
                    msp.define_meat_shape(shape=curr_shape,thickness_mm=curr_thickness,thick_slabs_beta_correction=correct_beta_for_large_slabs)
                    
                    current_simulation_bar = st.progress(0, text="Current simulation progress")
                    iteration_start_datetime = datetime.now()         
                    _update_progress = lambda t,y : update_progress_bar(t=t, y=y, Delta_t=msp.delta_time,t_max= msp.t_max, 
                                                                iteration_start_datetime= iteration_start_datetime, current_simulation_bar=current_simulation_bar)
                    
                    # Main simulation
                    T_sol_matrix, time_points_array, second_stability_reached = SimulateMeat(msp, progress_callback=_update_progress)
                    
                    # update current iteration progress bar
                    current_simulation_bar.empty()
                    if second_stability_reached is not None:
                        st.toast(f"Simulation for {curr_shape}-{curr_thickness}mm completed and thermal stability reached at {seconds_to_hhmm_pretty(second_stability_reached)}", icon="ℹ️")
                        dict_result[curr_shape] = seconds_to_hhmm_pretty(second_stability_reached)
                    else:
                        st.toast(f"Simulation for {curr_shape}-{curr_thickness}mm completed and thermal stability has not been reached", icon="ℹ️")
                        dict_result[curr_shape] = None

                    curr_idx += 1
                result.append(dict_result)
            overall_progress_bar.empty()

            message = "Estimated heating time:"
            st.session_state[REFERENCE_TABLE_STATUS] = (message, pd.DataFrame(result))

## Pasteurization reference table generation
############################################

elif option == "Pasteurization":
    thickness = st.sidebar.slider("Thickness (mm):", min_value=5,max_value=115, value=(5,70), step=5)
    if thickness[0]<10:
        st.sidebar.warning("For thicknesses below 10mm, each simulation time may require several minutes", icon="⚠️")
        
    shape_options = {
        "🥩 Slab": "slab",
        "🍖 Cylinder": "cylinder",
        "🟤 Sphere": "sphere"
    }
    shape = shape_options[st.sidebar.selectbox("Shape:", shape_options.keys())]
    if shape == "slab":
        correct_beta_for_large_slabs = st.sidebar.checkbox(label="Correct Beta for large values of slab thickenss (>30mm)", value = True, 
                                                       help="For computaton of Table 2 in Baldwin's paper it has been used")
    else:
        correct_beta_for_large_slabs = None
        
    initial_temperature = st.sidebar.number_input("Food Initial Temperature (°C):", value=5.0, step=0.5, format="%.1f")
    roner_temperatures = st.sidebar.slider("Roner Temperature (°C):", min_value=55, max_value=80,value=(55,66), step=1)
    simulation_time_h_int = st.sidebar.number_input("Simulation Time (h):", value=6, step=1)
    thermal_diffusivity = st.sidebar.slider("[α] Thermal Diffusivity (10⁻⁷ m²/s):", min_value=1.10, max_value=1.80, value=1.11, step=0.01, format="%.2f")
    heat_transfer = st.sidebar.number_input("[h] Surface Heat Transfer Coefficient (W/m²-K):", value=95, step=1)
    thermal_conductivity = st.sidebar.number_input("[k] Thermal Conductivity (W/m-K):", value=0.48, step=0.01, format="%.2f")

    if st.sidebar.button("Run pasteurization simulations", use_container_width=True):
        intro.empty()
        msp = MeatSimulationParameters()
        msp.T_initial = initial_temperature
        msp.simulation_hours = simulation_time_h_int
        msp.alpha = thermal_diffusivity * 1e-7
        msp.h = heat_transfer
        msp.k = thermal_conductivity
        radius_values_list = msp.list_radius_values
        thermal_stability_threshold = msp.thermal_stability_threshold    
        
        result = []
        total_combinations = (roner_temperatures[1]-roner_temperatures[0]+1) * ((thickness[1]-thickness[0])//5 + 1)
        curr_idx = 0
        overall_progress_bar = st.progress(0,text="Preparing simulation...")
        for curr_thickness in range (thickness[0], thickness[1]+1, 5):
            dict_result = {"Thickness (mm)": curr_thickness}
            msp.define_meat_shape(shape=shape,thickness_mm=curr_thickness)
            for curr_temp in range((roner_temperatures[0]), (roner_temperatures[1])+1):
                
                # Final initialization
                msp.T_fluid = curr_temp
                
                # Manage overall and current iteration progress bars
                overall_progress_bar.progress(curr_idx/total_combinations, f"Table computation. Running simulation for {curr_thickness}mm-{curr_temp}°C")
                current_simulation_bar = st.progress(0, text="Current simulation progress")
                iteration_start_datetime = datetime.now()         
                _update_progress = lambda t,y : update_progress_bar(t=t, y=y, Delta_t=msp.delta_time,t_max= msp.t_max, 
                                                                    iteration_start_datetime= iteration_start_datetime, current_simulation_bar=current_simulation_bar)
            
                
                # Main Simulation (Meat and LR)
                T_sol_matrix, _, _ = SimulateMeat(msp, progress_callback=_update_progress)
                center_temperatures = T_sol_matrix[0, :]  # First row corresponds to T[0] (r = 0)
                LR_total, LR_in_time, safety_instant = LogReduction(center_temperatures, msp.delta_time)
                
                # update current iteration progress bar
                current_simulation_bar.empty()
                if safety_instant is not None:
                    st.toast(f"Simulation for {curr_thickness}mm-{curr_temp}°C completed and thermal stability reached at {seconds_to_hhmm_pretty(safety_instant)}", icon="ℹ️")
                    dict_result[f"{curr_temp}°C"] = seconds_to_hhmm_pretty(safety_instant)
                else:
                    st.toast(f"Simulation for {curr_thickness}mm-{curr_temp}°C completed and thermal stability has not been reached", icon="ℹ️")
                    dict_result[f"{curr_temp}°C"] = None
                curr_idx += 1
            result.append(dict_result)
        
        overall_progress_bar.empty()
        message = "Estimated pasteurization time:"
        st.session_state[REFERENCE_TABLE_STATUS] = (message, pd.DataFrame(result))

# Display simulation result
###########################

if REFERENCE_TABLE_STATUS in st.session_state:

    intro.empty()
    (message, df_result) = st.session_state[REFERENCE_TABLE_STATUS]
    st.write(message)
    st.dataframe(df_result)