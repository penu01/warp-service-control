import subprocess
import tkinter as tk
from tkinter import messagebox
import ctypes
import sys
import os
import time

# Service name
SERVICE_NAME = "cloudflarewarp"

# Check for administrator privileges
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Check if Warp service is running
def is_warp_running():
    try:
        result = subprocess.run(['sc', 'query', SERVICE_NAME], capture_output=True, text=True, check=True)
        output = result.stdout
        if "STATE" in output:
            if "RUNNING" in output:
                return True
            if "STOPPED" in output or "STATE              : 1  STOPPED" in output:
                return False
            if "STOP_PENDING" in output or "START_PENDING" in output:
                # Wait 1 second for intermediate states and check again
                time.sleep(1)
                return is_warp_running()
        return False
    except subprocess.CalledProcessError as e:
        if e.returncode == 1060:
            update_message(f"Error: Cloudflare WARP service not found. ({SERVICE_NAME})", "red")
        else:
            update_message(f"Error: Service status check failed: {e.stderr}", "red")
        return False
    except Exception as e:
        update_message(f"Unexpected error: {str(e)}", "red")
        return False

# Start the service
def start_warp():
    update_message("Starting Warp service...", "blue")
    if is_warp_running():
        update_message("Info: Warp service is already running.", "green")
        return
    try:
        result = subprocess.run(['net', 'start', SERVICE_NAME], capture_output=True, text=True, check=True, shell=True)
        update_status()
        update_message("Info: Warp service started successfully.", "green")
    except subprocess.CalledProcessError as e:
        update_message(f"Error: Could not start Warp service: {e.stderr}", "red")
    except Exception as e:
        update_message(f"Unexpected error: {str(e)}", "red")

# Stop the service
def stop_warp():
    update_message("Stopping Warp service...", "blue")
    if not is_warp_running():
        update_message("Info: Warp service is already stopped.", "green")
        return
    try:
        result = subprocess.run(['net', 'stop', SERVICE_NAME], capture_output=True, text=True, check=True, shell=True)
        if result.returncode == 2:
            update_message("Warning: Service is already stopped or could not be stopped.", "orange")
        elif result.returncode != 0:
            update_message(f"Error: Could not stop Warp service: {e.stderr}", "red")
        else:
            update_message("Info: Warp service stopped successfully.", "green")
        update_status()
    except subprocess.CalledProcessError as e:
        update_message(f"Error: Could not stop Warp service: {e.stderr}", "red")
    except Exception as e:
        update_message(f"Unexpected error: {str(e)}", "red")

# Update the interface status
def update_status():
    if is_warp_running():
        status_label.config(text="Status: Active", fg="green")
    else:
        status_label.config(text="Status: Inactive", fg="red")

# Update the notification message
def update_message(message, color="black"):
    message_label.config(text=message, fg=color)
    root.update_idletasks()  # Ensures the interface is updated immediately

# GUI Initialization
if is_admin():
    root = tk.Tk()
    root.title("Cloudflare WARP Control")
    root.geometry("300x180")  # Increased window height
    root.resizable(False, False)

    status_label = tk.Label(root, text="", font=("Arial", 14))
    status_label.pack(pady=10)

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=5)

    start_btn = tk.Button(btn_frame, text="Start", width=10, command=start_warp)
    start_btn.pack(side="left", padx=10)

    stop_btn = tk.Button(btn_frame, text="Stop", width=10, command=stop_warp)
    stop_btn.pack(side="right", padx=10)

    message_label = tk.Label(root, text="", font=("Arial", 10))
    message_label.pack(pady=5)

    update_status()
    root.mainloop()
else:
    # If not an admin, restart the script with admin privileges
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
