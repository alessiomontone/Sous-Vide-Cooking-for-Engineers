import streamlit as st 
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

st.title("♨️ Cooking Simulation")

# Input parameters for the differential equation

st.sidebar.header("♨️ Parameters")
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
    thermal_diffusivity = st.number_input("[α] Thermal Diffusivity (e-7 m²/s):", value=1.11, step=0.01, format="%.2f")
    heat_transfer = st.number_input("[h] Surface Heat Transfer Coefficient (W/m²-K):", value=100, step=1)
    thermal_conductivity = st.number_input("[k] Thermal Conductivity (W/m-K):", value=0.48, step=0.01, format="%.2f")

# Display Simulation results
if st.button("Run Simulation"):
    from models.parameters import MeatSimulationParameters
    msp = MeatSimulationParameters()
    msp.define_meat_shape(shape=shape,thickness_mm=thickness)
    msp.T_initial = initial_temperature
    msp.T_fluid = roner_termperature
    msp.simulation_hours = final_time
    msp.alpha = thermal_diffusivity * 1e-7
    msp.h = heat_transfer
    msp.k = thermal_conductivity
    
    st.write(msp.to_json())
    with st.spinner("Running simulation..."):
        from models.solvers import SimulateMeat
        from models.solvers import LogReduction
        T_sol, time_points = SimulateMeat(msp)
        center_temperatures = T_sol[0, :]  # First row corresponds to T[0] (r = 0)
        LR_total, LR_in_time = LogReduction(center_temperatures)
    
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

    # Display the result
    if minute_reached is not None:
        st.info(f"The piece of meat reaches thermal stability (i.e., 0.5°C below the final temperature) at approximately {int(minute_reached)//60}h:{int(minute_reached)%60}m")
    else:
        st.info("The center does not reach 0.5°C below the final temperature within the simulated time.")

    # Create the Plotly figure
    fig = go.Figure()

    # Plot the center temperature
    fig.add_trace(go.Scatter(
        x=time_points_minutes,
        y=center_temperatures,
        mode='markers+lines',  # Use both markers and lines
        name="Temperature in the center",
        marker=dict(
            color=center_temperatures,  # Set color based on temperature
            colorscale='RdBu',  # Colorscale transitioning from blue to red
        ),
        line=dict(color='rgba(0,0,0,0)')  # Make the line itself transparent (optional)
    ))

    # Plot the threshold temperature as a horizontal line
    fig.add_trace(go.Scatter(
        x=[time_points_minutes[0], time_points_minutes[-1]],
        y=[threshold_temperature, threshold_temperature],
        mode='lines',
        name="0.5°C below final temperature",
        line=dict(color='red', dash='dash')
    ))

    # Mark the time when the center reaches the threshold, if applicable
    if minute_reached is not None:
        fig.add_trace(go.Scatter(
            x=[minute_reached],
            y=[threshold_temperature],
            mode='markers+text',
            name=f"Stability approx. at {int(minute_reached)//60}h:{int(minute_reached)%60}m",
            marker=dict(color='green', size=10),
            text=f"{int(minute_reached)//60}h:{int(minute_reached)%60}m",
            textposition="top center"
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
            title="Time (Minutes)",  # X-axis title
            tickmode="linear",      # Use linear tick mode for evenly spaced ticks
            dtick=30,               # Interval for ticks (30 minutes)
            tickformat=".0f"        # Format tick labels to show integers only
        ),
        yaxis=dict(title="Temperature (°C)"),
        legend=dict(title="Legend")
    )
    
    # Render the Plotly figure in Streamlit
    st.plotly_chart(fig, use_container_width=True)
    
    ######## Display the Pastorization info (Log Reduction)
    #######################################################
    
    # Identify the point where cumulative sum exceeds 6
    LR_THRESHOLD = 6
    time_to_exceed = next((i for i, value in enumerate(LR_in_time) if value > LR_THRESHOLD), None)
    
    if time_to_exceed is None:
        st.error("The meat does not reach acceptable healthy levels for eating during simulation time.")
    else:
        st.success(f"The meat reaches acceptables healthy levels {int(time_points_minutes[time_to_exceed])//60}h:{int(time_points_minutes[time_to_exceed])%60}m, i.e., a 6-log reduction (99.9999% reduction of pathogens)")
    
    # Create the Plotly figure
    fig = go.Figure()
    
    # Create a colormap for points
    norm = Normalize(vmin=np.min(LR_in_time), vmax=LR_THRESHOLD)  # Normalize values
    cmap_below_threshold = colormaps.get_cmap("YlOrRd_r")  # Gradient colormap for below threshold
    cmap_above_threshold = "green"  # Fixed green color above the threshold

    # Function to assign colors to points
    def get_color(value):
        if value <= LR_THRESHOLD:
            rgba = cmap_below_threshold(norm(value))
            return f"rgba({rgba[0]*255},{rgba[1]*255},{rgba[2]*255},{rgba[3]})"
        else:
            return cmap_above_threshold

    # Assign colors to points
    colors = [get_color(value) for value in LR_in_time]

    # Plot the cumulative sum
    fig.add_trace(go.Scatter(
        x=time_points_minutes,
        y=LR_in_time,
        mode='markers+lines',
        name='Log Reduction (LR)',
        marker=dict(
            color=colors,  # Use the gradient color list
            size=8,  # Marker size
        ),
        line=dict(color='yellow')  # Line color (optional)
    ))

    # Add a vertical line when the threshold is exceeded
    if time_to_exceed is not None:
        time_to_exceed_min = time_points_minutes[time_to_exceed]
        fig.add_trace(go.Scatter(
            x=[time_to_exceed_min],
            y=[LR_in_time[time_to_exceed]],
            mode='markers+text',
            name=f"{LR_THRESHOLD}-D reduction",
            marker=dict(color='yellow', size=14, symbol='star', line=dict(color='blue', width=2)),
            text=f"{int(time_to_exceed_min)//60}h:{int(time_to_exceed_min)%60}m",
            textposition="top center"
        ))

    # Add a horizontal line for the threshold
    fig.add_trace(go.Scatter(
        x=[time_points_minutes[0], time_points_minutes[-1]],
        y=[LR_THRESHOLD, LR_THRESHOLD],
        mode='lines',
        name=f"Threshold = {LR_THRESHOLD}-D reduction",
        line=dict(color='green', dash='dash')
    ))

    # Update layout for titles and labels
    fig.update_layout(
        title=dict(
            text="Log Reduction (LR) of pathogens over Time",
            x=0.5,  # Center the title
            xanchor="center",  # Align the title anchor to the center,
            font=dict(
                size=24,  # Increase the font size
            )
        ),
        xaxis=dict(
            title="Time (Minutes)",  # X-axis title
            tickmode="linear",      # Use linear tick mode for evenly spaced ticks
            dtick=30,               # Interval for ticks (30 minutes)
            tickformat=".0f"        # Format tick labels to show integers only
        ),
        yaxis=dict(title="Log Reduction (LR)"),
        legend_title="Legend",
    )

    # Render the Plotly chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)
    
    ######## Display the detailed information T(r,t)
    #####################################################
    with st.expander ("Show details"):
        # Normalize center temperatures for colormap
        norm_center_temps = (center_temperatures - np.min(center_temperatures)) / (np.max(center_temperatures) - np.min(center_temperatures))

        # Get colors from a blue-to-red colormap
        cmap = colormaps.get_cmap("coolwarm")
        colors = [cmap(value) for value in norm_center_temps]
        
        # Create the Plotly figure
        fig = go.Figure()

        # Add a trace for every 10th time point (i.e., every 10 minutes)
        for i in range(0, len(time_points), 10): 
            color = colors[i]
            rgba_color = f"rgba({color[0]*255},{color[1]*255},{color[2]*255},{color[3]})"
            fig.add_trace(
                go.Scatter(
                    x=r*1000,
                    y=T_sol[:, i],
                    mode='lines',
                    name=f"{int(time_points[i] // 3600):02d}h:{int((time_points[i] % 3600) // 60):02d}m",
                    line=dict(color=rgba_color)
                )
            )

        # Update the layout for axis customization
        fig.update_layout(
            title=dict(
                text="Temporal evolution across the section of the meat",
                x=0.5,  # Center the title
                xanchor="center",  # Align the title anchor to the center,
                font=dict(
                    size=18,  # Increase the font size
                )
            ),
            xaxis=dict(
                title="Distance from the center (mm)",
                tickmode="linear",
                tick0=0,
                dtick=5,  # 5 mm increments
            ),
            yaxis=dict(
                title="Temperature (°C)"
            ),
            legend_title="Time Points",
        )

        # Render the Plotly chart in Streamlit
        st.plotly_chart(fig, use_container_width=True)