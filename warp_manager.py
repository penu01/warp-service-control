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
    Cloudflare WARP servisini yönetmek için geliştirilmiş bir arayüz.
    Servis durumunu izler, başlatır, durdurur ve yönetici haklarını kontrol eder.
    """
    def __init__(self, root, on_ready_callback=None):
        self.root = root
        self.on_ready_callback = on_ready_callback
        self.service_names = ["CloudflareWARP", "cloudflarewarp", "WarpSvc"]
        self.active_service = None
        
        self.setup_ui()
        self.initialize_app()

    def setup_ui(self):
        """Uygulamanın kullanıcı arayüzünü oluşturur."""
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

        self.status_var = tk.StringVar(value="Hizmet aranıyor...")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, font=("Segoe UI", 11))
        self.status_label.pack(pady=(0, 15))

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=5)
        
        style = ttk.Style()
        style.configure("W.TButton", font=("Segoe UI", 10))
        
        self.start_button = ttk.Button(button_frame, text="Başlat", command=self.start_service, style="W.TButton", width=12)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))

        self.stop_button = ttk.Button(button_frame, text="Durdur", command=self.stop_service, style="W.TButton", width=12)
        self.stop_button.pack(side=tk.LEFT, padx=(5, 0))

        self.message_var = tk.StringVar(value="Hazır.")
        message_label = ttk.Label(main_frame, textvariable=self.message_var, font=("Segoe UI", 9), wraplength=280)
        message_label.pack(pady=(15, 0))
        
        self.monitoring_active = True

    def initialize_app(self):
        """Uygulamanın çalışması için gerekli kontrolleri ve işlemleri başlatır."""
        if not self.is_admin():
            messagebox.showerror("Yönetici Yetkisi Gerekli", 
                                 "Bu uygulama Windows hizmetlerini yönetmek için yönetici olarak çalıştırılmalıdır.")
            self.root.destroy()
            return
        
        # Servis bulma işlemini başlat. Bu işlem bitince durum izleyiciyi kendisi tetikleyecek.
        self.run_threaded(self.find_warp_service)

    def run_threaded(self, target_func, *args):
        """Verilen fonksiyonu bir arka plan thread'inde çalıştırır."""
        thread = threading.Thread(target=target_func, args=args, daemon=True)
        thread.start()

    def is_admin(self):
        """Kullanıcının yönetici yetkilerine sahip olup olmadığını kontrol eder."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except AttributeError:
            return False

    def find_warp_service(self):
        """Mevcut WARP servisini bulur ve ardından durum izleyiciyi başlatır."""
        # Komutların arka planda görünmez bir pencere oluşturmasını önlemek için
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0

        for service_name in self.service_names:
            try:
                # 'sc query' komutu hizmetin varlığını kontrol etmek için yeterlidir.
                subprocess.run(['sc', 'query', service_name], check=True, capture_output=True, creationflags=creation_flags)
                self.active_service = service_name
                self.root.after(0, lambda: self.message_var.set(f"Hizmet bulundu: {self.active_service}"))
                
                # Servis bulunduktan sonra durum izleyiciyi başlat
                self.start_status_monitor()
                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        self.root.after(0, lambda: self.message_var.set("Cloudflare WARP hizmeti bulunamadı."))
        self.root.after(0, lambda: self.update_status_display("not_found"))

    def get_service_status(self):
        """Hizmetin mevcut durumunu (running, stopped vb.) döndürür."""
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
        """Arayüzdeki durum metnini ve rengini günceller."""
        status_map = {
            "running": ("🟢 Aktif", "green"),
            "stopped": ("🔴 İnaktif", "red"),
            "starting": ("🟡 Başlatılıyor...", "orange"),
            "stopping": ("🟡 Durduruluyor...", "orange"),
            "not_found": ("❌ Hizmet bulunamadı", "gray"),
            "unknown": ("❓ Durum bilinmiyor", "gray"),
            "error": ("⚠️ Sorgulama hatası", "red")
        }
        text, color = status_map.get(status, ("❓", "black"))
        self.status_var.set(text)
        self.status_label.config(foreground=color)
        
        # Duruma göre butonları aktif/pasif yap
        is_running = status == "running"
        is_stopped = status == "stopped"
        
        if self.active_service:
            self.start_button.config(state=tk.DISABLED if is_running else tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL if is_running else tk.DISABLED)
        else:
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.DISABLED)

    def start_status_monitor(self):
        """Servis durumunu periyodik olarak kontrol eden döngüyü başlatır."""
        def monitor():
            # İlk durumu hemen, beklemeden göster
            if self.active_service:
                initial_status = self.get_service_status()
                self.root.after(0, self.update_status_display, initial_status)
        
            # Hazırlık bitti, ana uygulamayı gösterme zamanı.
            if self.on_ready_callback:
                self.root.after(200, self.on_ready_callback)

            while self.monitoring_active:
                time.sleep(2) # Döngünün başında bekle
                if self.active_service:
                    status = self.get_service_status()
                    self.root.after(0, self.update_status_display, status)
        
        self.run_threaded(monitor)
        
    def manage_service(self, action):
        """Servis başlatma veya durdurma işlemini yönetir."""
        if not self.active_service:
            self.message_var.set("İşlem yapılamıyor, hizmet bulunamadı.")
            return

        current_status = self.get_service_status()
        
        if action == 'start' and current_status == 'running':
            self.message_var.set("Hizmet zaten çalışıyor.")
            return
            
        if action == 'stop' and current_status == 'stopped':
            self.message_var.set("Hizmet zaten durdurulmuş.")
            return

        action_gerund = "Başlatılıyor..." if action == 'start' else "Durduruluyor..."
        self.message_var.set(action_gerund)

        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        try:
            subprocess.run(['net', action, self.active_service], check=True, capture_output=True, text=True, timeout=30, creationflags=creation_flags)
            success_message = "✅ Başarıyla başlatıldı." if action == 'start' else "✅ Başarıyla durduruldu."
            self.message_var.set(success_message)
        except subprocess.TimeoutExpired:
            self.message_var.set("❌ İşlem zaman aşımına uğradı.")
        except subprocess.CalledProcessError as e:
            # Hata mesajını temizleyerek kullanıcıya göster
            error_details = e.stderr.strip().splitlines()[-1]
            self.message_var.set(f"❌ Hata: {error_details}")
        except Exception as e:
            self.message_var.set(f"❌ Beklenmedik bir hata oluştu: {e}")

    def start_service(self):
        self.run_threaded(self.manage_service, 'start')

    def stop_service(self):
        self.run_threaded(self.manage_service, 'stop')
        
    def on_closing(self):
        """Uygulama kapatılırken arka plan işlemlerini durdurur."""
        self.monitoring_active = False
        self.root.destroy()

class SplashScreen:
    """Uygulama yüklenirken gösterilecek olan açılış ekranı."""
    def __init__(self, root):
        self.root = root
        self.splash = tk.Toplevel(self.root)
        self.splash.overrideredirect(True)  # Kenarlık ve başlık çubuğu olmayan pencere

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
        ttk.Label(splash_frame, text="Yükleniyor...", font=("Segoe UI", 10), background='#fafafa').pack()
        
        self.progress = ttk.Progressbar(splash_frame, orient='horizontal', length=200, mode='indeterminate')
        self.progress.pack(pady=(10, 0))
        self.progress.start(15)

    def destroy(self):
        self.progress.stop()
        self.splash.destroy()

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f)
    except Exception:
        pass

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except AttributeError:
        return False

def request_admin_rights_and_rerun():
    try:
        # Use pythonw.exe if available to avoid console window
        exe = sys.executable
        if exe.lower().endswith("python.exe"):
            pythonw = exe[:-10] + "pythonw.exe"
            if os.path.exists(pythonw):
                exe = pythonw
        ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, " ".join(sys.argv), None, 1)
    except Exception as e:
        print(f"Yönetici hakları alınamadı, program başlatılamıyor. Hata: {e}")

def ask_always_admin(root):
    """Kullanıcıya programı her zaman yönetici olarak çalıştırmak isteyip istemediğini sorar."""
    result = None
    def ask():
        nonlocal result
        result = messagebox.askyesno(
            "Yönetici Olarak Çalıştırma",
            "Programı her zaman yönetici olarak çalıştırmak ister misiniz?\n\nEvet derseniz, program her açılışta otomatik olarak yönetici olarak başlatılır.")
    root.after(0, ask)
    root.wait_window()  # Wait for the dialog to close
    return result

def main():
    """Ana uygulama fonksiyonu."""
    settings = load_settings()
    admin = is_admin()
    always_admin = settings.get("always_admin", None)

    if not admin:
        # Kullanıcıya sorulmuş mu?
        if always_admin is None:
            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning(
                "Yönetici Yetkisi Gerekli",
                "Bu programın tam işlevselliği için yönetici olarak çalıştırılması önerilir!"
            )
            answer = messagebox.askyesno(
                "Yönetici Olarak Çalıştırma",
                "Programı her zaman yönetici olarak çalıştırmak ister misiniz?\n\nEvet derseniz, program her açılışta otomatik olarak yönetici olarak başlatılır."
            )
            settings["always_admin"] = bool(answer)
            save_settings(settings)
            if answer:
                root.destroy()
                request_admin_rights_and_rerun()
                return
            root.destroy()
        elif always_admin:
            # Kullanıcı daha önce "evet" dedi, otomatik olarak yönetici olarak başlat
            request_admin_rights_and_rerun()
            return
        else:
            # Kullanıcı daha önce "hayır" dedi, sadece uyarı göster
            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning(
                "Yönetici Yetkisi Gerekli",
                "Bu programın tam işlevselliği için yönetici olarak çalıştırılması önerilir!"
            )
            root.destroy()

    # Artık ya yönetici olarak çalışıyoruz, ya da kullanıcı "hayır" dedi
    root = tk.Tk()
    root.withdraw()  # Ana pencereyi başlangıçta gizle

    splash = SplashScreen(root)

    def on_app_ready():
        splash.destroy()
        root.deiconify()  # Gizlenmiş ana pencereyi göster

    app = WarpManager(root, on_ready_callback=on_app_ready)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Uygulama kapatıldı.")

if __name__ == "__main__":
    main() 