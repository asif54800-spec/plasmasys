# PlasmaSys
<Div><img src="plasmasys.svg" alt="PlasmaSys Icon" width="64" display:block margin="auto"/><p> A Python-based sensor monitor for the KDE Plasma 6 desktop with a detailed dashboard and system tray icon.
</p></Div>

![A screenshot of PlasmaSys in action](https://github.com/asif54800-spec/plasmasys/blob/main/app-screen.png)

# Features

## 📊 Real-Time Monitoring Dashboard


### 1. General Info Card
* **Host:** Your computer's network name.
* **Model:** The make and model of your device (e.g., laptop model).
* **OS:** Your currently installed Linux distribution (e.g., "Kubuntu 24.04 LTS").
* **Kernel:** The running Linux kernel version.
* **Network:** Local IP address and the name (SSID) of the connected Wi-Fi network.
* **Live Network Speed:** Real-time upload and download speeds (KB/s, MB/s).
* **Network History:** A live-scrolling chart of your total network activity.

### 2. CPU Card
* **CPU Model:** The full name of your processor.
* **Total Usage:** A live percentage of your total CPU load.
* **Per-Core Usage:** A complete list of utilization for every CPU core/thread.
* **CPU History:** A live-scrolling line chart of your CPU's recent load history.

### 3. Memory & Storage Card
* **RAM:** Tracks memory usage (e.g., "8.2 / 15.5 GB (53%)").
* **RAM History:** A live-scrolling chart of your system's RAM usage.
* **Partition Details:** Lists all major disk partitions, showing their filesystem type, used space, and total space (e.g., "`/ (ext4): 150.1 / 450.5 GB (33%)`").
* **Live Disk I/O:** Real-time disk read and write speeds (KB/s, MB/s).

### 4. Temperatures & Fans Card
* **All Sensors:** Displays readings from all available temperature sensors on your system.
* **All Fans:** Shows the current speed (RPM) of all detected system fans.

## ⚙️ System Integration

* **System Tray Icon:** Runs conveniently in the KDE Plasma system tray.
* **Tray Tooltip:** Hover over the tray icon for a quick summary of CPU, Memory, and Temp.
* **Close to Tray:** Closing the main window sends the app to the tray instead of quitting, with a clear confirmation dialog.
* **Dimming Icon:** The tray icon visibly dims when monitoring is paused, so you know its status at a glance.
* **Tray Menu:** Right-click the tray icon to quickly show the app, open settings, or quit.

## 🔧 Utilities & Configuration

* **Pause/Resume:** A "Stop" / "Start" button to pause and resume all real-time monitoring to save resources.
* **Settings Panel:** A simple dialog to configure alerts (CPU temp, sensor temp).
* **Export Logs:** A button to export the application's collected data to a `.csv` file.
* **Persistent Config:** Saves your settings to `~/.config/plasmasys/settings.json`.
## 💻 Installation

### Arch User Repository (AUR)

The easiest way to install on Arch Linux is from the AUR using a helper like `yay` or `paru`:

```bash

AUR: https://aur.archlinux.org/packages/plasmasys
yay -S plasmasys

(This link will work once your package is approved on the AUR)

Manual Installation (from Source)

If you're not on Arch or want to run the latest development version:

    Clone the repository:
    Bash

git clone [https://github.com/asif54800-spec/plasmasys.git]
cd plasmasys

Install dependencies:
Bash
pip install PyQt6 psutil

(You also need wireless_tools for SSID support: sudo pacman -S wireless_tools)

⚙️ Dependencies

    Python 3

    python-pyqt6

    python-psutil

    wireless_tools (for iwgetid to get SSID)

    lm-sensors (optional, but needed for temperature/fan data)

    Build and install
    bash
    makepkg -si
    
    bash 
📜 License

This project is open-source and licensed under the MIT License. See the LICENSE file for details.

🧑‍💻 Author

Developed by Muhammad Asif Rauf (asif54800@gmail.com).
# plasmasys
A Python-based sensor monitor for the KDE Plasma 6 desktop with a detailed dashboard and system tray icon
