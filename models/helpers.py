from datetime import timedelta

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