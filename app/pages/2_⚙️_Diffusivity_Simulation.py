import streamlit as st 
import pandas as pd
import numpy as np
from matplotlib import colormaps
from matplotlib.colors import Normalize
import plotly.graph_objects as go

# Allow acces to the models 
import sys
from pathlib import Path
# Add the parent directory to the sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

st.set_page_config(
    page_title="Sous Vide simulation tool",
    page_icon="♨️",
)

st.title("⚙️ Diffusivity Simulation")

# Input parameters for the differential equation

st.sidebar.header("⚙️ Parameters")

st.sidebar.subheader("Simulations")
start_thermal_diffusivity = st.sidebar.number_input("[α] Start Thermal Diffusivity (e-7 m²/s):", value=1.11, step=0.01, format="%.2f")
end_thermal_diffusivity = st.sidebar.number_input("[α] End Thermal Diffusivity (e-7 m²/s):", value=1.41, step=0.01, format="%.2f")
num_simulations = st.sidebar.number_input("Simulations (#):", value=5, step=1)

st.sidebar.subheader("Meat")
thickness = st.sidebar.number_input("Thickness (mm):", value=20, step=5)

shape_options = {
    "🥩 Slab": "slab",
    "🍖 Cylinder": "cylinder",
    "🟤 Sphere": "sphere"
}
shape = shape_options[st.sidebar.selectbox("Shape:", shape_options.keys())]


st.sidebar.subheader("Temperatures")
initial_temperature = st.sidebar.number_input("Initial Temperature (°C):", value=5.0, step=0.5, format="%.1f")
roner_termperature = st.sidebar.number_input("Roner Temperature (°C):", value=58.0, step=0.5, format="%.1f")

st.sidebar.subheader("Timing")
final_time = st.sidebar.number_input("Simulation Time (h):", value=5, step=1)

with st.sidebar.expander("Advanced"):
    # thermal_diffusivity = st.number_input("[α] Thermal Diffusivity (e-7 m²/s):", value=1.11, step=0.01, format="%.2f")
    heat_transfer = st.number_input("[h] Surface Heat Transfer Coefficient (W/m²-K):", value=100, step=1)
    thermal_conductivity = st.number_input("[k] Thermal Conductivity (W/m-K):", value=0.48, step=0.01, format="%.2f")

# Display Simulation results
if st.button("Run Simulation"):

    # with st.spinner("Running simulation..."):
    progress_bar = st.progress(0)
    status_text = st.empty()  # For displaying the current progress text

    from models.parameters import MeatSimulationParameters
    from models.solvers import SimulateMeat
    from models.solvers import LogReduction
    
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
    
        T_sol, time_points = SimulateMeat(msp)
        center_temperatures = T_sol[0, :]  # First row corresponds to T[0] (r = 0)
        
        # Prepare data for Streamlit line_chart
        time_points_minutes = time_points / 60  # Convert seconds to minutes
        r = np.linspace(0, msp.R, msp.N)  # Radial points from 0 to R
        
        ######## Display the temporal evolution of the Center
        #####################################################
        # Extract the temperature at the center of the cylinder (r = 0)
        threshold_temperature = roner_termperature - 0.5  # Threshold temperature

        # Find the first time where the center temperature exceeds the threshold
        minute_reached = None
        for i, temp in enumerate(center_temperatures):
            if temp >= threshold_temperature:
                minute_reached = time_points_minutes[i]
                break
        
        if minute_reached is not None:
                results.append({"Diffusivity": a, "Heating time": minute_reached})
        
        progress_percentage = int((index + 1) / len(alphas) * 100)
        progress_bar.progress(progress_percentage)
        status_text.text(f"Progress: {progress_percentage}%")
        
    progress_bar.empty()
    status_text.empty()

    # Plot the results using Plotly Go
    df_results = pd.DataFrame (results)
    fig = go.Figure()

    # Add scatter plot
    fig.add_trace(go.Scatter(
        x=df_results["Diffusivity"],
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
        xaxis_title="Parameter Value",
        yaxis_title="Time to Stability (seconds)",
        template="plotly_white",
        hovermode="closest",
    )

    # Display the plot
    st.plotly_chart(fig)
