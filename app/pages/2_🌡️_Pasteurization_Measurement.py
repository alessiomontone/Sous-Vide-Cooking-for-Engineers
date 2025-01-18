import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from matplotlib import colormaps
from matplotlib.colors import Normalize
import plotly.graph_objects as go

from models.helpers import GetEmptyMeasurementDataFrame, seconds_to_hhmm_pretty, MeasurementFormat
from models.solvers import ExtrapolateHeatingCurve_1exp, ExtrapolateHeatingCurve_2exp, LogReduction
from models.parameters import LOG_REDUCTION_MIN_THRESHOLD


st.set_page_config(
    page_title="Sous Vide simulation tool",
    page_icon="♨️",
)

st.title("🌡️ Check pasteurization progress")

## Sidebar - Input parameters for the simulation
################################################

st.sidebar.header("🌡️ Parameters")
# Upload an Excel file #########
################################
roner_termperature = st.sidebar.number_input("Roner Temperature (°C):", min_value=54.0, value=58.0, step=0.5, format="%.1f")
extrapolated_minutes = st.sidebar.number_input("Estimated Time (h):",min_value=1, value=1, step=1) *60

uploaded_file = st.sidebar.file_uploader("Load measurements from Excel file", type=["xlsx", "xls"],accept_multiple_files=False)

if uploaded_file is not None:
    try:
        # Read the Excel file into a DataFrame
        df = pd.read_excel(uploaded_file)
        df.columns = [MeasurementFormat.TIMESTAMP, MeasurementFormat.TEMPERATURE]

        # Display the dataframe
        st.sidebar.success("Excel file loaded successfully!")
        st.session_state.dfmeasurements = df
    except Exception as e:
        st.sidebar.error(f"Error loading Excel file: {e}")

# Initialize the dataframe in session state and display howto

if "dfmeasurements" not in st.session_state:
    intro = st.markdown("""
                    This page will allow to evaluate the pasteurization progress of a meat heating starting from direct temperature measurements of the center of the food. 
                    """)
    st.info("Please upload an Excel file with the measurements or start adding measurements manually.")
    st.session_state.dfmeasurements = GetEmptyMeasurementDataFrame()

# Display the editable dataframe
st.subheader("Temperature measurements")
edited_df = st.data_editor(
    st.session_state.dfmeasurements,
    use_container_width=True,  # Expand to fit the container
    num_rows="dynamic",        # Allow adding/deleting rows dynamically
    key="temperature_editor",  # Unique key for the editor
)

if not pd.api.types.is_numeric_dtype(edited_df[MeasurementFormat.TIMESTAMP]):
    st.error("Timestamp must be a numeric value.")

if not pd.api.types.is_numeric_dtype(edited_df[MeasurementFormat.TEMPERATURE]):
    st.error("Temperature must be a numeric value.")

# Update the dataframe in session state
st.session_state.dfmeasurements = edited_df

st.sidebar.markdown("---")

# Create a download button for the DataFrame as an Excel file
#############################################################
def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
    output.seek(0)  # Move pointer to the start of the buffer
    return output

# Convert the DataFrame to an Excel binary
excel_file = convert_df_to_excel(edited_df)

# Add a download button
st.sidebar.download_button(
    label="Download Measurements as Excel",
    data=excel_file,
    file_name="dataframe.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

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
            st.success(f"""The meat reaches **acceptables healthy levels {seconds_to_hhmm_pretty(safety_second)} after the start of cooking**. \\
                    [i.e., in {safety_second//60 - edited_df[MeasurementFormat.TIMESTAMP].max()} minutes from last measurement] \\
                    (Note: healtyhy level means pathogens reduction by 99.9999%)""")
        
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
                text="Temperature Evolution",
                x=0.5,  # Center the title
                xanchor="center",  # Align the title anchor to the center,
                font=dict(
                    size=24,  # Increase the font size
                )
            ),
            xaxis_title='Time (minutes)',
            yaxis_title='Temperature (°C)',
            legend=dict(title='Legend'),
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
            legend_title="Legend",
        )

        # Render the Plotly chart in Streamlit
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Cannot interpolate yet, please add more point or check measurements")
        st.error(f"Error: {e}")


