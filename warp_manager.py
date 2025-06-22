import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import ctypes
import sys
import threading
import time
import json
import os

SETTINGS_FILE = "settings.json"

class WarpManager:
    """
    A GUI application to manage the Cloudflare WARP service.
    It monitors status, starts/stops the service, and handles admin rights.
    """
    def __init__(self, root, on_ready_callback=None):
        self.root = root
        self.on_ready_callback = on_ready_callback
        self.service_names = ["CloudflareWARP", "cloudflarewarp", "WarpSvc"]
        self.active_service = None
        
        self.setup_ui()
        self.initialize_app()

    def setup_ui(self):
        """Creates the user interface for the application."""
        self.root.title("WARP Manager")

        window_width = 320
        window_height = 200

        # Ekran boyutlarını al ve pencereyi ortala
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(expand=True, fill=tk.BOTH)

        title_label = ttk.Label(main_frame, text="Cloudflare WARP", font=("Segoe UI", 16, "bold"))
        title_label.pack(pady=(0, 10))

        self.status_var = tk.StringVar(value="Searching for service...")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, font=("Segoe UI", 11))
        self.status_label.pack(pady=(0, 15))

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=5)
        
        style = ttk.Style()
        style.configure("W.TButton", font=("Segoe UI", 10))
        
        self.start_button = ttk.Button(button_frame, text="Start", command=self.start_service, style="W.TButton", width=12)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))

        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_service, style="W.TButton", width=12)
        self.stop_button.pack(side=tk.LEFT, padx=(5, 0))

        self.message_var = tk.StringVar(value="Ready.")
        message_label = ttk.Label(main_frame, textvariable=self.message_var, font=("Segoe UI", 9), wraplength=280)
        message_label.pack(pady=(15, 0))
        
        self.monitoring_active = True

    def initialize_app(self):
        """Initializes the necessary checks and processes for the application to run."""
        if not is_admin():
            messagebox.showerror("Administrator Privileges Required", 
                                 "This application must be run as an administrator to manage Windows services.")
            self.root.destroy()
            return
        
        # Servis bulma işlemini başlat. Bu işlem bitince durum izleyiciyi kendisi tetikleyecek.
        self.run_threaded(self.find_warp_service)

    def run_threaded(self, target_func, *args):
        """Runs the given function in a background thread."""
        thread = threading.Thread(target=target_func, args=args, daemon=True)
        thread.start()

    def find_warp_service(self):
        """Finds the current WARP service and then starts the status monitor."""
        # This flag prevents a console window from appearing for subprocess calls on Windows.
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0

        for service_name in self.service_names:
            try:
                # 'sc query' is sufficient to check for the existence of the service.
                subprocess.run(['sc', 'query', service_name], check=True, capture_output=True, creationflags=creation_flags)
                self.active_service = service_name
                self.root.after(0, lambda: self.message_var.set(f"Service found: {self.active_service}"))
                
                # Start the status monitor after the service is found
                self.start_status_monitor()
                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        self.root.after(0, lambda: self.message_var.set("Cloudflare WARP service not found."))
        self.root.after(0, lambda: self.update_status_display("not_found"))

    def get_service_status(self):
        """Returns the current status of the service (e.g., running, stopped)."""
        if not self.active_service:
            return "not_found"
        
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        try:
            result = subprocess.run(['sc', 'query', self.active_service], capture_output=True, text=True, timeout=5, creationflags=creation_flags)
            output = result.stdout.upper()
            
            if "RUNNING" in output: return "running"
            if "STOPPED" in output: return "stopped"
            if "START_PENDING" in output: return "starting"
            if "STOP_PENDING" in output: return "stopping"
            return "unknown"
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return "error"

    def update_status_display(self, status):
        """Updates the status text and color in the UI."""
        status_map = {
            "running": ("🟢 Active", "green"),
            "stopped": ("🔴 Inactive", "red"),
            "starting": ("🟡 Starting...", "orange"),
            "stopping": ("🟡 Stopping...", "orange"),
            "not_found": ("❌ Service not found", "gray"),
            "unknown": ("❓ Status unknown", "gray"),
            "error": ("⚠️ Query error", "red")
        }
        text, color = status_map.get(status, ("❓", "black"))
        self.status_var.set(text)
        self.status_label.config(foreground=color)
        
        # Buttons should only be updated if the service has been found and is in a stable state.
        is_running = status == "running"
        is_stopped = status == "stopped"
        
        if self.active_service:
            self.start_button.config(state=tk.DISABLED if is_running else tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL if is_running else tk.DISABLED)
        else:
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.DISABLED)

    def start_status_monitor(self):
        """Starts the loop that periodically checks the service status."""
        def monitor():
            # Show the initial status immediately without waiting.
            if self.active_service:
                initial_status = self.get_service_status()
                self.root.after(0, self.update_status_display, initial_status)
        
            # Loading is complete, time to show the main application.
            if self.on_ready_callback:
                self.root.after(200, self.on_ready_callback)

            while self.monitoring_active:
                time.sleep(2) # Wait at the beginning of the loop
                if self.active_service:
                    status = self.get_service_status()
                    self.root.after(0, self.update_status_display, status)
        
        self.run_threaded(monitor)
        
    def manage_service(self, action):
        """Manages the service start and stop operations."""
        if not self.active_service:
            self.message_var.set("Operation failed, service not found.")
            return

        current_status = self.get_service_status()
        
        if action == 'start' and current_status == 'running':
            self.message_var.set("Service is already running.")
            return
            
        if action == 'stop' and current_status == 'stopped':
            self.message_var.set("Service is already stopped.")
            return

        action_gerund = "Starting..." if action == 'start' else "Stopping..."
        self.message_var.set(action_gerund)

        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        try:
            subprocess.run(['net', action, self.active_service], check=True, capture_output=True, text=True,
                         timeout=30, creationflags=creation_flags)
            success_message = "✅ Successfully started." if action == 'start' else "✅ Successfully stopped."
            self.message_var.set(success_message)
        except subprocess.TimeoutExpired:
            self.message_var.set("❌ Operation timed out.")
        except subprocess.CalledProcessError as e:
            # Clean up the error message and display it to the user.
            error_details = e.stderr.strip().splitlines()[-1]
            self.message_var.set(f"❌ Error: {error_details}")
        except Exception as e:
            self.message_var.set(f"❌ An unexpected error occurred: {e}")

    def start_service(self):
        self.run_threaded(self.manage_service, 'start')

    def stop_service(self):
        self.run_threaded(self.manage_service, 'stop')
        
    def on_closing(self):
        """Stops background processes when the application is closing."""
        self.monitoring_active = False
        self.root.destroy()

class SplashScreen:
    """The splash screen to be displayed while the application is loading."""
    def __init__(self, root):
        self.root = root
        self.splash = tk.Toplevel(self.root)
        self.splash.overrideredirect(True)  # Window without border and title bar

        width, height = 250, 120
        screen_width = self.splash.winfo_screenwidth()
        screen_height = self.splash.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        self.splash.geometry(f'{width}x{height}+{x}+{y}')
        
        # Stil ve çerçeve
        splash_frame = ttk.Frame(self.splash, style="Splash.TFrame")
        splash_frame.pack(expand=True, fill='both')
        ttk.Style().configure("Splash.TFrame", background='#fafafa')

        ttk.Label(splash_frame, text="Warp Manager", font=("Segoe UI", 14, "bold"), background='#fafafa').pack(pady=(20, 5))
        ttk.Label(splash_frame, text="Loading...", font=("Segoe UI", 10), background='#fafafa').pack()
        
        self.progress = ttk.Progressbar(splash_frame, orient='horizontal', length=200, mode='indeterminate')
        self.progress.pack(pady=(10, 0))
        self.progress.start(15)

    def destroy(self):
        self.progress.stop()
        self.splash.destroy()

def load_settings():
    """Loads settings from the settings file."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_settings(settings):
    """Saves settings to the settings file."""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f)
    except Exception:
        pass

def is_admin():
    """Checks if the user has administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except AttributeError:
        return False

def request_admin_rights_and_rerun():
    """Requests admin rights and reruns the script."""
    try:
        # Use pythonw.exe if available to avoid console window
        exe = sys.executable
        if exe.lower().endswith("python.exe"):
            pythonw = exe[:-10] + "pythonw.exe"
            if os.path.exists(pythonw):
                exe = pythonw
        ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, " ".join(sys.argv), None, 1)
    except Exception as e:
        print(f"Could not get admin rights, unable to start program. Error: {e}")

def ask_always_admin(root):
    """Kullanıcıya programı her zaman yönetici olarak çalıştırmak isteyip istemediğini sorar."""
    result = None
    def ask():
        nonlocal result
        result = messagebox.askyesno(
            "Run as Administrator",
            "Would you like to always run this program as an administrator?\n\n"
            "If you choose yes, it will automatically start as an administrator every time."
        )
    root.after(0, ask)
    root.wait_window()  # Wait for the dialog to close
    return result

def main():
    """Main application function."""
    settings = load_settings()
    admin = is_admin()
    always_run_as_admin = settings.get("always_admin", None)

    if not admin:
        # Has the user been asked before?
        if always_run_as_admin is None:
            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning(
                "Administrator Privileges Recommended",
                "It is recommended to run this program as an administrator for full functionality!"
            )
            answer = messagebox.askyesno(
                "Run as Administrator",
                "Would you like to always run this program as an administrator?\n\n"
                "If you choose yes, it will automatically start as an administrator every time."
            )
            settings["always_admin"] = bool(answer)
            save_settings(settings)
            if answer:
                root.destroy()
                request_admin_rights_and_rerun()
                return
            root.destroy()
        elif always_run_as_admin:
            # User previously chose "yes", so automatically start as admin.
            request_admin_rights_and_rerun()
            return
        else:
            # User previously chose "no", so just show the warning.
            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning(
                "Administrator Privileges Recommended",
                "It is recommended to run this program as an administrator for full functionality!"
            )
            root.destroy()

    # At this point, we are either running as admin, or the user chose "no".
    root = tk.Tk()
    root.withdraw() # Hide the main window initially.

    splash = SplashScreen(root)

    def on_app_ready():
        """This function is called when the main application is ready."""
        splash.destroy()
        root.deiconify() # Show the hidden main window.

    # The main application will call the on_app_ready function when it's ready.
    app = WarpManager(root, on_ready_callback=on_app_ready)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Application closed.")

if __name__ == "__main__":
    main() 