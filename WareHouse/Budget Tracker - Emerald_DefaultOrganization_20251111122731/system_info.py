'''
Module to fetch and display system information.
'''
import psutil
class SystemInfo:
    def get_info(self):
        # Fetch CPU and memory usage
        cpu_usage = psutil.cpu_percent(interval=None)  # Non-blocking call
        memory_usage = psutil.virtual_memory().percent
        return f"CPU Usage: {cpu_usage}%\nMemory Usage: {memory_usage}%"