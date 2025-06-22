# Warp Manager

A simple and modern desktop GUI for Windows to easily manage the Cloudflare WARP service.

*It's highly recommended to add a screenshot of the application here!*

![Warp Manager Screenshot](https://user-images.githubusercontent.com/35674355/269176191-22e69818-4a52-4752-9b7e-f51b5c490a60.png)

## ✨ Features

- **One-Click Control:** Easily start and stop the Cloudflare WARP service.
- **Real-Time Status:** See the current status (Active, Inactive, Starting...) at a glance.
- **Smart Admin Handling:** Asks for permission to always run as administrator for a smoother experience.
- **Splash Screen:** A "Loading..." screen provides a professional feel while the app starts.
- **No Flashing Windows:** Runs background checks without any annoying pop-up command windows.
- **Standalone EXE:** No installation needed, just a single executable file.

## 🚀 How to Use

1. Go to the **Releases** page of this repository.
2. Download the latest `WarpManager.exe` file.
3. Run it! That's all.

## 🛠️ How to Build from Source

If you want to build the application yourself:

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/your-username/your-repository-name.git
    ```
2.  **Navigate to the project directory:**
    ```sh
    cd your-repository-name
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