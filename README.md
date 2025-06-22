# Warp Manager

A simple and modern desktop GUI for Windows to easily manage the Cloudflare WARP service.

![WarpManager_UjrREp3zUN](https://github.com/user-attachments/assets/3278a661-7bed-4656-8916-b50d11b66430)

## ✨ Features

- **One-Click Control:** Easily start and stop the Cloudflare WARP service.
- **Real-Time Status:** Instantly see the service status (Active, Inactive, Starting...).
- **Smart Admin Handling:** Asks for your permission to always run as administrator for a smoother experience on subsequent launches.
- **Professional Splash Screen:** A "Loading..." screen prevents the feeling of a slow start.
- **No Flickering Windows:** All background tasks run invisibly without any annoying console windows popping up.
- **Standalone Executable:** No installation required. Just a single `.exe` file that you can run from anywhere.

## 🚀 How to Use

1. Go to the **[Releases](https://github.com/penu01/warp-service-control/releases)** page of this repository.
2. Download the latest `WarpManager.exe` file.
3. Run it! That's all.

## ⚠️ Antivirus False Positives

Some antivirus programs may flag the `WarpManager.exe` file as malicious. **This is a false positive.**

This happens because the application is created with PyInstaller, a tool that bundles Python code into a single executable. The way these executables work (unpacking files into a temporary folder to run) can sometimes resemble the behavior of malware, causing some antivirus heuristics to trigger a warning.

The project is fully open-source. You can review the code yourself to see that it is safe. For transparency, you can see a full VirusTotal scan report below, which indicates that the detection is based on the PyInstaller YARA rule and is not a sign of malware.

![VirusTotal Scan](https://github.com/user-attachments/assets/7d4bea4f-8126-4096-be2c-051deea5fcb2)

## 🛠️ How to Build from Source

If you want to build the application yourself:

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/penu01/warp-service-control.git
    ```
2.  **Navigate to the project directory:**
    ```sh
    cd warp-service-control
    ```
3.  **Create a virtual environment and activate it:**
    ```sh
    python -m venv .venv
    .venv\Scripts\activate
    ```
4.  **Install the required build tool:**
    ```sh
    pip install pyinstaller
    ```
5.  **Run the build command:**
    ```sh
    pyinstaller --onefile --windowed --name "WarpManager" --icon="cloudflare.ico" warp_manager.py
    ```
The final `.exe` will be in the `dist` folder. 