import streamlit as st 
import numpy as np
from matplotlib import colormaps
from matplotlib.colors import Normalize
import plotly.graph_objects as go
from datetime import time, date, datetime, timedelta

from models.solvers import SimulateMeat
from models.solvers import LogReduction

# Allow acces to the models 
import sys
from pathlib import Path
# Add the parent directory to the sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

st.set_page_config(
    page_title="Sous Vide simulation tool",
    page_icon="♨️",
)

st.title("♨️ Quick Simulation")

## Sidebar - Input parameters for the simulation
################################################

st.sidebar.header("♨️ Parameters")

thickness = st.sidebar.number_input("Thickness (mm):", value=20, step=5)

shape_options = {
    "🥩 Slab": "slab",
    "🍖 Cylinder": "cylinder",
    "🟤 Sphere": "sphere"
}
shape = shape_options[st.sidebar.selectbox("Shape:", shape_options.keys())]

start_hhmm = st.sidebar.time_input("Starting time (h:mm):", value=time(9, 00))

initial_temperature = st.sidebar.number_input("Food Initial Temperature (°C):", value=5.0, step=0.5, format="%.1f")

roner_termperature = st.sidebar.number_input("Roner Temperature (°C):", value=58.0, step=0.5, format="%.1f")

# Display Simulation results
if st.sidebar.button("Run Simulation"):
    from models.parameters import MeatSimulationParameters, LOG_REDUCTION_MIN_THRESHOLD
    msp = MeatSimulationParameters()
    msp.define_meat_shape(shape=shape,thickness_mm=thickness)
    msp.T_initial = initial_temperature
    msp.T_fluid = roner_termperature
    r_values = msp.r_values
    thermal_stability_threshold = msp.thermal_stability_threshold
    # msp.simulation_hours => TODO: Iterate over the hours
    
    with st.spinner("Running simulation..."):
        st.toast("Starting simulation...", icon="ℹ️")
        for hour in [5,6,12,18,24]:
            msp.simulation_hours = hour
            T_sol, time_points, second_stability_reached = SimulateMeat(msp)
            center_temperatures = T_sol[0, :]  # First row corresponds to T[0] (r = 0)
            LR_total, LR_in_time, safety_instant = LogReduction(center_temperatures, msp.dt)
            
            if safety_instant is not None:
                break
            else:
                st.toast("No safety level reached yet... increasing simulation time", icon="⏳")
        

    ######## Display the temporal evolution of the Center
    #####################################################
    # Extract the temperature at the center of the cylinder (r = 0)
    
    # Convert instant at which thermal stability is reached in minutes
    time_points_minutes = time_points / 60  # Convert seconds to minutes
    start_time = datetime.combine(date(2025,1,1), start_hhmm)  # Example: Experiment starts at 9:00 AM
    time_points_hhmm = [start_time + timedelta(minutes=minutes) for minutes in time_points_minutes]
    hhmm_stability_reached = start_time + timedelta(seconds=second_stability_reached) if second_stability_reached is not None else None
    hhmm_safety_reached = start_time + timedelta(seconds=safety_instant) if safety_instant is not None else None
    

    # Display the result
    if hhmm_stability_reached is not None:
        st.info(f"The piece of meat reaches thermal stability (i.e., 0.5°C below the final temperature) at approximately {hhmm_stability_reached:%H:%M}")
    else:
        st.info("The center does not reach 0.5°C below the final temperature within the simulated time.")

    # Create the Plotly figure
    fig = go.Figure()

    # Plot the center temperature
    fig.add_trace(go.Scatter(
        x=time_points_hhmm,
        y=center_temperatures,
        mode='markers+lines',  # Use both markers and lines
        name="Temperature in the center",
        marker=dict(
            color=center_temperatures,  # Set color based on temperature
            colorscale='RdBu',  # Colorscale transitioning from blue to red
        ),
        line=dict(color='rgba(0,0,0,0)'),  # Make the line itself transparent (optional)
        showlegend=False
    ))

    # Mark the time when the center reaches the threshold, if applicable
    if hhmm_stability_reached is not None:
        fig.add_trace(go.Scatter(
            x=[hhmm_stability_reached],
            y=[thermal_stability_threshold],
            mode='markers+text',
            name=f"Thermal stability",
            marker=dict(color='yellow', symbol='circle', size=20),
            text=f"<b>{hhmm_stability_reached:%H:%M}</b>",
            textposition="bottom center"
        ))
        
    # Mark the time when the safety level is reached, if applicable
    if hhmm_safety_reached is not None:
        fig.add_trace(go.Scatter(
            x=[hhmm_safety_reached],
            y=[thermal_stability_threshold],
            mode='markers+text',
            name=f"Safety level reached",
            marker=dict(color='green', symbol='circle-dot', size=20),
            text=f"<b>{hhmm_safety_reached:%H:%M}</b>",
            textposition="top center"
        ))
        
        fig.add_shape(
            type="rect",
            x0=hhmm_safety_reached,
            x1=time_points_hhmm[-1],
            y0=0,
            y1=max(center_temperatures),
            fillcolor="green",    # Rectangle color
            opacity=0.3,          # Transparency for shadow effect
            line_width=0          # No border for the rectangle
        )
        
        # Add an invisible trace to represent the rectangle in the legend
        fig.add_trace(go.Scatter(
            x=[None],  # No points to plot
            y=[None],
            mode='markers',
            marker=dict(size=10, color='green', symbol='square', opacity=0.3),
            name='Safety Area'
        ))
  
    # Update the layout
    fig.update_layout(
        title=dict(
            text="Temporal Variation of Temperature at the meat center",
            x=0.5,  # Center the title
            xanchor="center",  # Align the title anchor to the center,
            font=dict(
                size=24,  # Increase the font size
            )
        ),
        xaxis=dict(
            title="Time of the day (h:mm)",  # X-axis title
            tickmode="linear",      # Use linear tick mode for evenly spaced ticks
            dtick=15*60*1000,               # Interval for ticks (30 minutes)
            tickformat="%H:%M"        # Format tick labels to show integers only
        ),
        yaxis=dict(title="Temperature in the center (°C)"),
        legend=dict(title="Legend")
    )
    
    # Render the Plotly figure in Streamlit
    st.plotly_chart(fig, use_container_width=True)
    