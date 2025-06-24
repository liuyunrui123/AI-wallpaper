from datetime import datetime, timedelta

def get_current_time():
    return datetime.now()

def get_time_difference(start_time, end_time):
    return end_time - start_time

def format_time_delta(delta):
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours} hours, {minutes} minutes, {seconds} seconds"

def analyze_time_period(start_time_str, end_time_str):
    start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
    time_difference = get_time_difference(start_time, end_time)
    formatted_difference = format_time_delta(time_difference)
    return {
        "start_time": start_time,
        "end_time": end_time,
        "time_difference": formatted_difference
    }
