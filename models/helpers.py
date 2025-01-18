from datetime import timedelta
from datetime import datetime
import pandas as pd
import streamlit as st

class MeasurementFormat:
    TIMESTAMP = "Time (mins)"
    TEMPERATURE = "Temperature (°C)"

def GetEmptyMeasurementDataFrame() -> pd.DataFrame:
    """Return an empty measurement DataFrame with default columns."""
    return pd.DataFrame({
        MeasurementFormat.TIMESTAMP: [0],  # Default timestamp placeholder
        MeasurementFormat.TEMPERATURE: [0.0],      # Default temperature placeholder
    })

def seconds_to_hhmm(seconds: int) -> str:
    """Convert seconds to a string in HH:MM format."""
    return str(timedelta(seconds=seconds))[:-3]

def seconds_to_hhmm_pretty(seconds: int) -> str:
    """Convert seconds to a string in HH:MM format, adding respective labels, e.g., 3660 seconds -> 1h:01m."""
    hours = int(seconds // 3600)  # Calculate the number of hours
    minutes = int((seconds % 3600) // 60)  # Calculate the remaining minutes
    return f"{hours}h:{minutes:02}m"

def seconds_to_hhmmss(seconds: int) -> str:
    """Convert seconds to a string in HH:MM:SS format."""
    return str(timedelta(seconds=seconds))

def seconds_to_mmss_pretty(seconds: int) -> str:
    """Convert seconds to a string in MM:SS format, adding respective labels, e.g., 650 seconds -> 10m:50s."""
    minutes = int(seconds // 60)  # Calculate the number of hours
    seconds = int(seconds % 60)  # Calculate the remaining minutes
    return f"{minutes}m:{seconds:02}s"

def update_progress_bar(t, y, Delta_t :float, t_max:float, iteration_start_datetime : datetime, current_simulation_bar: st.progress) -> int:
        elapsed_timedelta = datetime.now() - iteration_start_datetime
        remaining_timedelta = elapsed_timedelta / (t+Delta_t) * (t_max - t)
        current_simulation_bar.progress(t/t_max, text=f"Simulating... Elapsed: {seconds_to_mmss_pretty(int(elapsed_timedelta.total_seconds()))}, Remaining: {seconds_to_mmss_pretty(int(remaining_timedelta.total_seconds()))}")
        return 1
    
    