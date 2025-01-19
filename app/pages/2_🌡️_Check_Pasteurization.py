import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from matplotlib import colormaps
from matplotlib.colors import Normalize
import plotly.graph_objects as go

# Allow acces to the models 
import sys
from pathlib import Path
# Add the parent directory to the sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from models.helpers import GetEmptyMeasurementDataFrame, seconds_to_hhmm_pretty, MeasurementFormat
from models.solvers import ExtrapolateHeatingCurve_1exp, ExtrapolateHeatingCurve_2exp, LogReduction
from models.parameters import LOG_REDUCTION_MIN_THRESHOLD

PASTEURIZATION_MEASUREMENT_STATUS = "CheckPasteurization_Measurements"

st.set_page_config(
    page_title="Sous vide simulation tool",
    page_icon="♨️",
)

st.title("🌡️ Check pasteurization")

## Sidebar - Input parameters for the simulation
################################################

st.sidebar.header("🌡️ Parameters")
# Upload an Excel file #########
################################

uploaded_file = st.sidebar.file_uploader("Load measurements from Excel file", type=["xlsx", "xls"],accept_multiple_files=False)

if uploaded_file is not None:
    try:
        # Read the Excel file into a DataFrame
        df = pd.read_excel(uploaded_file)
        df.columns = [MeasurementFormat.TIMESTAMP, MeasurementFormat.TEMPERATURE]

        # Display the dataframe
        st.sidebar.success("Excel file loaded successfully!")
        st.session_state[PASTEURIZATION_MEASUREMENT_STATUS] = df
    except Exception as e:
        st.sidebar.error(f"Error loading Excel file: {e}")


# Initialize the dataframe in session state and display howto
if PASTEURIZATION_MEASUREMENT_STATUS not in st.session_state:
    intro = st.markdown("""
                    This page will allow to evaluate the pasteurization progress of a meat heating starting from direct temperature measurements of the center of the food. 
                    """)
    st.info("Please upload an Excel file with the measurements (👈) or start adding measurements manually (👇).")
    #st.session_state[PASTEURIZATION_MEASUREMENT_STATUS] = GetEmptyMeasurementDataFrame()

## Input Parametes
col1, col2 = st.columns([1, 1])  # Create columns with relative widths
with col1:  # Place the button in the center column
    roner_termperature = st.number_input("Roner Temperature (°C):", min_value=54.0, value=58.0, step=0.5, format="%.1f")
with col2: 
    extrapolated_minutes = st.number_input("Analized Time (h):",min_value=1, value=5, step=1) *60

st.markdown("---")

# Display the editable dataframe
if PASTEURIZATION_MEASUREMENT_STATUS in st.session_state:
    st.write("Measurements")
    config = {
        MeasurementFormat.TIMESTAMP : st.column_config.NumberColumn(MeasurementFormat.TIMESTAMP, min_value=0, required=True),
        MeasurementFormat.TEMPERATURE : st.column_config.NumberColumn(MeasurementFormat.TEMPERATURE, format= "%.1f",  required=True),
    }

    edited_df = st.data_editor(
        st.session_state[PASTEURIZATION_MEASUREMENT_STATUS],
        use_container_width=True,  # Expand to fit the container
        column_config=config,
        num_rows="dynamic",        # Allow adding/deleting rows dynamically
        #disabled=[MeasurementFormat.TEMPERATURE, MeasurementFormat.TIMESTAMP], 
        hide_index=True, 
        key="temperature_editor",  # Unique key for the editor
    )

    if not edited_df.equals(st.session_state[PASTEURIZATION_MEASUREMENT_STATUS]):
        st.session_state[PASTEURIZATION_MEASUREMENT_STATUS] = edited_df
        st.rerun()

    if not pd.api.types.is_numeric_dtype(edited_df[MeasurementFormat.TIMESTAMP]):
        st.error("Timestamp must be a numeric value.")

    if not pd.api.types.is_numeric_dtype(edited_df[MeasurementFormat.TEMPERATURE]):
        st.error("Temperature must be a numeric value.")

@st.dialog("Add measurement")
def add_measurement():
    #st.write(f"Add measurement details?")
    if PASTEURIZATION_MEASUREMENT_STATUS in st.session_state:
        df = st.session_state[PASTEURIZATION_MEASUREMENT_STATUS]
        if len(df) > 0:
            last_time = int(df[MeasurementFormat.TIMESTAMP].max())
            last_temperature = df[MeasurementFormat.TEMPERATURE].max()
        else:
            last_time, last_temperature = 0, 5.0
    else:
        last_time, last_temperature = 0, 5.0
    
    col1, col2 = st.columns(2)
    with col1:
        new_time = st.number_input(MeasurementFormat.TIMESTAMP, step=1, value=last_time)
    with col2:
        new_temp = st.number_input(MeasurementFormat.TEMPERATURE, step=0.1, value=last_temperature, format="%.1f")
        
    if st.button("Add", use_container_width=True):
        if PASTEURIZATION_MEASUREMENT_STATUS in st.session_state:
            df = st.session_state[PASTEURIZATION_MEASUREMENT_STATUS]
            new_row = pd.DataFrame({MeasurementFormat.TIMESTAMP: [new_time], MeasurementFormat.TEMPERATURE: [new_temp]})
            st.session_state[PASTEURIZATION_MEASUREMENT_STATUS] = pd.concat([df,new_row], ignore_index=True)
        else:
            new_row = pd.DataFrame({MeasurementFormat.TIMESTAMP: [new_time], MeasurementFormat.TEMPERATURE: [new_temp]})
            st.session_state[PASTEURIZATION_MEASUREMENT_STATUS] = pd.concat([new_row])
        st.rerun()

if st.button("Add measurement", use_container_width=True):
    add_measurement()

# Create a download button for the DataFrame as an Excel file
#############################################################
def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
    output.seek(0)  # Move pointer to the start of the buffer
    return output

if PASTEURIZATION_MEASUREMENT_STATUS in st.session_state:
    # Convert the DataFrame to an Excel binary
    excel_file = convert_df_to_excel(edited_df)

    # Add a download button
    st.sidebar.download_button(
        label="Download Measurements as Excel",
        data=excel_file,
        file_name="dataframe.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    # If there are enough elements to interpolate
    if len(edited_df)> 2:
        try: 
            ### Core computation
            #########################
            
            l = ExtrapolateHeatingCurve_1exp(edited_df,roner_termperature)
            t_fit = np.arange(max(edited_df[MeasurementFormat.TIMESTAMP])+extrapolated_minutes) # np.linspace(0, max(edited_df[MeasurementFormat.TIMESTAMP])+extrapolated_minutes, 200)
            T_fit = l(t_fit)
            LR_total, LR_in_time, safety_second = LogReduction(center_temperature=T_fit, dt=60)
            
            ######## Display key figures
            #######################################################
            if safety_second is None:
                st.error("The meat does not reach acceptable healthy levels for eating during simulation time.")
            else:
                t_delta = safety_second//60 - edited_df[MeasurementFormat.TIMESTAMP].max()
                st.success(f"""The meat reaches **acceptables healthy levels {seconds_to_hhmm_pretty(safety_second)} after the start of cooking**: 
                           this is {abs(t_delta)} minutes {'after' if t_delta >=0 else 'before'} last measurement""")
            
            ### Temperature Interpolation plot
            ##################################
            
            # Create the figure
            fig = go.Figure()

            # Add the scatter plot for original data
            fig.add_trace(go.Scatter(
                x=edited_df[MeasurementFormat.TIMESTAMP],
                y=edited_df[MeasurementFormat.TEMPERATURE],
                mode='markers',
                marker=dict(color='red'),
                name='Measured Data'
            ))

            # Add the line plot for the fitted temperatures
            fig.add_trace(go.Scatter(
                x=t_fit,
                y=T_fit,
                mode='lines',
                line=dict(color='blue'),
                name='Fitting curve'
            ))

            # Add the steady-state horizontal line
            fig.add_trace(go.Scatter(
                x=[t_fit.min(), t_fit.max()],
                y=[roner_termperature, roner_termperature],
                mode='lines',
                line=dict(color='green', dash='dash'),
                name='Final Temperature'
            ))

            # Update layout for title, labels, and grid
            fig.update_layout(
                title=dict(
                    text="Temperature evolution",
                    x=0.5,  # Center the title
                    xanchor="center",  # Align the title anchor to the center,
                    font=dict(
                        size=24,  # Increase the font size
                    )
                ),
                xaxis_title='Time (minutes)',
                yaxis_title='Temperature (°C)',
                legend=dict(
                    # title="Legend",
                    orientation="v",  # Horizontal orientation
                    #x=0.5, y=1.05, xanchor="center" 
                    x=1,              # Position at the far right
                    y=0.1,              # Position at the bottom
                    xanchor="right",  # Align legend to the right
                    yanchor="bottom",  # Align legend to the bottom
                    bgcolor="rgba(0, 0, 0, 0)"  # Transparent background
                ),
                template='plotly_white',
                width=800,
                height=500
            )

            # Show the figure in Streamlit
            import streamlit as st
            st.plotly_chart(fig)
            
            # Create the Plotly figure
            fig = go.Figure()
            
            # Create a colormap for points
            norm = Normalize(vmin=np.min(LR_in_time), vmax=LOG_REDUCTION_MIN_THRESHOLD)  # Normalize values
            cmap_below_threshold = colormaps.get_cmap("YlOrRd_r")  # Gradient colormap for below threshold
            cmap_above_threshold = "green"  # Fixed green color above the threshold

            # Function to assign colors to points
            def get_color(value):
                if value <= LOG_REDUCTION_MIN_THRESHOLD:
                    rgba = cmap_below_threshold(norm(value))
                    return f"rgba({rgba[0]*255},{rgba[1]*255},{rgba[2]*255},{rgba[3]})"
                else:
                    return cmap_above_threshold

            # Assign colors to points
            colors = [get_color(value) for value in LR_in_time]

            # Plot the cumulative sum
            fig.add_trace(go.Scatter(
                x=t_fit,
                y=LR_in_time,
                mode='markers+lines',
                name='Log reduction (LR)',
                marker=dict(
                    color=colors,  # Use the gradient color list
                    size=8,  # Marker size
                ),
                line=dict(color='yellow')  # Line color (optional)
            ))

            # Add a vertical line when the threshold is exceeded
            if safety_second is not None:
                
                fig.add_trace(go.Scatter(
                    x=[safety_second//60],
                    y=[LOG_REDUCTION_MIN_THRESHOLD],
                    mode='markers+text',
                    name=f"{LOG_REDUCTION_MIN_THRESHOLD}D reduction instant",
                    marker=dict(color='yellow', size=14, symbol='star', line=dict(color='blue', width=2)),
                    text=f"{seconds_to_hhmm_pretty(safety_second)}m",
                    textposition="top center"
                ))

            # Add a horizontal line for the threshold
            fig.add_trace(go.Scatter(
                x=[t_fit[0], t_fit[-1]],
                y=[LOG_REDUCTION_MIN_THRESHOLD, LOG_REDUCTION_MIN_THRESHOLD],
                mode='lines',
                name=f"Threshold = {LOG_REDUCTION_MIN_THRESHOLD}D reduction",
                line=dict(color='green', dash='dash')
            ))

            # Update layout for titles and labels
            fig.update_layout(
                title=dict(
                    text="Log reduction of pathogens",
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
                yaxis=dict(title="Log reduction (LR)"),
                legend=dict(
                    # title="Legend",
                    orientation="v",  # Horizontal orientation
                    #x=0.5, y=1.05, xanchor="center" 
                    x=1,              # Position at the far right
                    y=0.05,              # Position at the bottom
                    xanchor="right",  # Align legend to the right
                    yanchor="bottom",  # Align legend to the bottom
                    bgcolor="rgba(0, 0, 0, 0)"  # Transparent background
                ),
            )

            # Render the Plotly chart in Streamlit
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Cannot interpolate yet, please add more point or check measurements")
            st.error(f"Error: {e}")


