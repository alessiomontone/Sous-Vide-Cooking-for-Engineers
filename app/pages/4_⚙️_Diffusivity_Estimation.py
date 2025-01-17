import streamlit as st 
import pandas as pd
import numpy as np
from matplotlib import colormaps
from matplotlib.colors import Normalize
import plotly.graph_objects as go
from datetime import datetime

from models.parameters import MeatSimulationParameters
from models.solvers import SimulateMeat
from models.solvers import LogReduction
from models.helpers import update_progress_bar

# Allow acces to the models 
import sys
from pathlib import Path
# Add the parent directory to the sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

st.set_page_config(
    page_title="Sous Vide simulation tool",
    page_icon="♨️",
)

st.title("⚙️ Diffusivity Estimation")

intro = st.markdown("""
                    Here you can estimate the thermal diffusivity of a piece of meat by simulating the heating process with **different values of α to be checked against actual measured heating time**.
                    
                    E.g., for a 30mm slab heating from 5.0 °C to 58.0°C (given all the other standard parameters), can be simulated here for a range of α values from 1.00 to 2.00;
                    Looking at the simulation result, if actual measures with meat thermometer show that the meat reached 58.0°C in 100 minutes,  then the thermal diffusivity α is around 1.30 x 10⁻⁷ m²/s.
                    """)

# Input parameters for the differential equation
st.sidebar.header("⚙️ Parameters")

st.sidebar.subheader("Diffusivity Range")
(start_thermal_diffusivity, end_thermal_diffusivity) = st.sidebar.slider("[α] Start Thermal Diffusivity (10⁻⁷ m²/s):", min_value=1.0,max_value=2.0, value=(1.10,1.50), step=0.01, format="%.2f")

num_simulations = st.sidebar.number_input("Simulations (#):",min_value=2, value=5, step=1)

st.sidebar.subheader("Meat characteristics")
thickness = st.sidebar.number_input("Thickness (mm):", min_value=5, value=20, step=5)
if thickness<10:
        st.sidebar.warning("For thicknesses below 10mm, each simulation may require several minutes", icon="⚠️")

shape_options = {
    "🥩 Slab": "slab",
    "🍖 Cylinder": "cylinder",
    "🟤 Sphere": "sphere"
}
shape = shape_options[st.sidebar.selectbox("Shape:", shape_options.keys())]

initial_temperature = st.sidebar.number_input("Initial Temperature (°C):", value=5.0, step=0.5, format="%.1f")
roner_termperature = st.sidebar.number_input("Roner Temperature (°C):",min_value=54.0, value=58.0, step=0.5, format="%.1f")

#with st.sidebar.expander("Advanced"):
final_time = st.sidebar.number_input("Simulation Time (h):", min_value=1, value=5, step=1)
heat_transfer = st.sidebar.number_input("[h] Surface Heat Transfer Coefficient (W/m²-K):",min_value=1, value=95, step=1)
thermal_conductivity = st.sidebar.number_input("[k] Thermal Conductivity (W/m-K):",min_value=0.01, value=0.48, step=0.01, format="%.2f")

# Display Simulation results
if st.sidebar.button("Run Simulation"):
    intro.empty()
    
    # with st.spinner("Running simulation..."):
    overall_progress_bar = st.progress(0, "Running simulations...")


    
    msp = MeatSimulationParameters()
    msp.define_meat_shape(shape=shape,thickness_mm=thickness)
    msp.T_initial = initial_temperature
    msp.T_fluid = roner_termperature
    msp.simulation_hours = final_time
    msp.h = heat_transfer
    msp.k = thermal_conductivity
    
    alphas = np.linspace (start_thermal_diffusivity * 1e-7, end_thermal_diffusivity * 1e-7, num_simulations)
    results = []
    
 
    for index, a in enumerate(alphas):
        msp.alpha = a
        
        current_simulation_bar = st.progress(0, text=f"Simulating...")
        iteration_start_datetime = datetime.now()
        _update_progress = lambda t,y : update_progress_bar(t=t, y=y, Delta_t=msp.delta_time,t_max= msp.t_max, 
                                                            iteration_start_datetime= iteration_start_datetime, current_simulation_bar=current_simulation_bar)
    
        T_sol, time_points, stability_instant = SimulateMeat(msp, progress_callback=_update_progress)
        current_simulation_bar.empty()
        
        if stability_instant is not None:
            results.append({"Diffusivity": a, "Heating time": stability_instant/60})
        
        progress_percentage = int((index + 1) / len(alphas) * 100)
        overall_progress_bar.progress(progress_percentage,text=f"Performed simulations {index +1}/{len(alphas)}")
        
    overall_progress_bar.empty()

    # Plot the results using Plotly Go
    df_results = pd.DataFrame (results)
    if (df_results.shape[0]>0):
        fig = go.Figure()

        # Add scatter plot
        fig.add_trace(go.Scatter(
            x=df_results["Diffusivity"]*1e7,
            y=df_results["Heating time"],
            mode="lines+markers",
            marker=dict(size=10, color='blue', opacity=0.7),
            line=dict(color='blue', width=2),  # Customize the line color and width
            text=[f"Alpha {i}" for i in df_results["Diffusivity"]],
            hovertemplate="<b>Simulation:</b> %{text}<br><b>Parameter:</b> %{x:.2f}<br><b>Time to Stability:</b> %{y:.2f}<extra></extra>"
        ))

        # Customize layout
        fig.update_layout(
            title=dict(
                text="Heating time vs. Diffusivity (α)",  # Title text
                x=0.5,  # Center the title horizontally
                xanchor="center",  # Ensure proper alignment
            ),
            xaxis_title="Thermal Diffusivity (α, 10⁻⁷)",
            yaxis_title="Time to Thermal Stability (minutes)",
            template="plotly_white",
            hovermode="closest",
        )

        # Display the plot
        st.plotly_chart(fig)
    else:   
        st.error(f"""No stable temperature reached in any condition with current simulation parameters. Please consider increasing simulation time (h)""")
