import subprocess
import tkinter as tk
from tkinter import messagebox
import ctypes
import sys
import os
import time

# Servis adı
SERVICE_NAME = "cloudflarewarp"

# Yönetici haklarını kontrol etme
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Warp durumu kontrolü
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
                # Ara durumlar için 1 saniye bekle ve tekrar kontrol et
                time.sleep(1)
                return is_warp_running()
        return False
    except subprocess.CalledProcessError as e:
        if e.returncode == 1060:
            update_message(f"Hata: Cloudflare WARP servisi bulunamadı. ({SERVICE_NAME})", "red")
        else:
            update_message(f"Hata: Servis durumu kontrol edilemedi: {e.stderr}", "red")
        return False
    except Exception as e:
        update_message(f"Beklenmeyen hata: {str(e)}", "red")
        return False

# Servisi başlatma
def start_warp():
    update_message("Warp servisi başlatılıyor...", "blue")
    if is_warp_running():
        update_message("Bilgi: Warp servisi zaten çalışıyor.", "green")
        return
    try:
        result = subprocess.run(['net', 'start', SERVICE_NAME], capture_output=True, text=True, check=True, shell=True)
        update_status()
        update_message("Bilgi: Warp servisi başarıyla başlatıldı.", "green")
    except subprocess.CalledProcessError as e:
        update_message(f"Hata: Warp servisi başlatılamadı: {e.stderr}", "red")
    except Exception as e:
        update_message(f"Beklenmeyen hata: {str(e)}", "red")

# Servisi durdurma
def stop_warp():
    update_message("Warp servisi durduruluyor...", "blue")
    if not is_warp_running():
        update_message("Bilgi: Warp servisi zaten durdurulmuş.", "green")
        return
    try:
        result = subprocess.run(['net', 'stop', SERVICE_NAME], capture_output=True, text=True, check=True, shell=True)
        if result.returncode == 2:
            update_message("Uyarı: Servis zaten durdurulmuş veya durdurulamadı.", "orange")
        elif result.returncode != 0:
            update_message(f"Hata: Warp servisi durdurulamadı: {e.stderr}", "red")
        else:
            update_message("Bilgi: Warp servisi başarıyla durduruldu.", "green")
        update_status()
    except subprocess.CalledProcessError as e:
        update_message(f"Hata: Warp servisi durdurulamadı: {e.stderr}", "red")
    except Exception as e:
        update_message(f"Beklenmeyen hata: {str(e)}", "red")

# Arayüzü güncelle
def update_status():
    if is_warp_running():
        status_label.config(text="Durum: Aktif", fg="green")
    else:
        status_label.config(text="Durum: Deaktif", fg="red")

# Bildirim mesajını güncelleme fonksiyonu
def update_message(message, color="black"):
    message_label.config(text=message, fg=color)
    root.update_idletasks() # Arayüzün hemen güncellenmesini sağlar

# GUI Başlangıcı
if is_admin():
    root = tk.Tk()
    root.title("Cloudflare WARP Kontrol")
    root.geometry("300x180") # Pencere yüksekliği artırıldı
    root.resizable(False, False)

    status_label = tk.Label(root, text="", font=("Arial", 14))
    status_label.pack(pady=10)

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=5)

    start_btn = tk.Button(btn_frame, text="Çalıştır", width=10, command=start_warp)
    start_btn.pack(side="left", padx=10)

    stop_btn = tk.Button(btn_frame, text="Durdur", width=10, command=stop_warp)
    stop_btn.pack(side="right", padx=10)

    message_label = tk.Label(root, text="", font=("Arial", 10))
    message_label.pack(pady=5)

    update_status()
    root.mainloop()
else:
    # Yönetici değilse, betiği yönetici olarak yeniden başlat
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)