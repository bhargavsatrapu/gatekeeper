
import threading
import json
import os
from datetime import datetime
from typing import List, Dict

# Console logging system
console_logs: List[Dict] = []
console_lock = threading.Lock()
LOG_FILE = "console_logs.json"

def _load_logs_from_file():
    """Load logs from persistent storage"""
    global console_logs
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r') as f:
                console_logs = json.load(f)
        except (json.JSONDecodeError, IOError):
            console_logs = []

def _save_logs_to_file():
    """Save logs to persistent storage"""
    try:
        with open(LOG_FILE, 'w') as f:
            json.dump(console_logs, f, indent=2)
    except IOError:
        pass  # Fail silently if we can't save

# Load existing logs on startup
_load_logs_from_file()

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
        
        # Save to file periodically (every 10 logs)
        if len(console_logs) % 10 == 0:
            _save_logs_to_file()

def get_console_logs():
    """Get all console logs"""
    with console_lock:
        return console_logs.copy()  # Return all logs

def clear_console():
    """Clear all console logs"""
    with console_lock:
        console_logs.clear()
        _save_logs_to_file()
