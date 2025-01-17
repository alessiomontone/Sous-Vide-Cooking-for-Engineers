from datetime import timedelta
from datetime import datetime
import streamlit as st

def seconds_to_hhmm(seconds: int) -> str:
    """Convert seconds to a string in HH:MM format."""
    return str(timedelta(seconds=seconds))[:-3]

def seconds_to_hhmmss(seconds: int) -> str:
    """Convert seconds to a string in HH:MM:SS format."""
    return str(timedelta(seconds=seconds))

def seconds_to_mmss(seconds: int) -> str:
    """Convert seconds to a string in MM:SS format."""
    minutes, seconds = divmod(seconds, 60)  # Convert to minutes and seconds
    return f"{minutes:02}:{seconds:02}"  # Format with leading zeros if needed

def update_progress_bar(t, y, Delta_t :float, t_max:float, iteration_start_datetime : datetime, current_simulation_bar: st.progress) -> int:
        elapsed_timedelta = datetime.now() - iteration_start_datetime
        remaining_timedelta = elapsed_timedelta / (t+Delta_t) * (t_max - t)
        current_simulation_bar.progress(t/t_max, text=f"Simulating... Elapsed: {seconds_to_mmss(int(elapsed_timedelta.total_seconds()))}, Remaining: {seconds_to_mmss(int(remaining_timedelta.total_seconds()))}")
        return 1
    
    