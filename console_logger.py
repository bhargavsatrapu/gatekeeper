
import threading
from datetime import datetime
from typing import List, Dict

# Console logging system
console_logs: List[Dict] = []
console_lock = threading.Lock()

def log_to_console(message: str, log_type: str = "info"):
    """Add a message to the console logs"""
    with console_lock:
        console_logs.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "message": message,
            "type": log_type
        })
        
        # Keep only last 1000 logs
        if len(console_logs) > 1000:
            console_logs.pop(0)

def get_console_logs():
    """Get recent console logs"""
    with console_lock:
        return console_logs[-100:]  # Return last 100 logs

def clear_console():
    """Clear all console logs"""
    with console_lock:
        console_logs.clear()
