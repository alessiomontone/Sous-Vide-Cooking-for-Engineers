from datetime import timedelta

def seconds_to_hhmm(seconds: int) -> str:
    """Convert seconds to a string in HH:MM format."""
    return str(timedelta(seconds=seconds))[:-3]