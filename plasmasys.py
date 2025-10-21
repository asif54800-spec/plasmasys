#!/usr/bin/env python3
"""
A Python-based sensor monitor for the KDE Plasma 6 desktop with a detailed dashboard and system tray icon.
Full layout + tray icon + dimming + bottom menu + close confirmation.
Version: 1.0
"""

import sys, os, platform, psutil, socket, time, json, csv, subprocess
from collections import deque
from typing import List, Dict, Tuple, Optional

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QScrollArea, QFrame, QSizePolicy, QMenu, QPushButton, QSystemTrayIcon,
    QStyle, QFileDialog, QDialog, QFormLayout, QSpinBox, QDialogButtonBox,
    QMessageBox
)
from PyQt6.QtGui import (
    QCursor, QPainter, QPen, QColor, QFont, QIcon, QPainterPath, QAction, QPixmap
)
from PyQt6.QtCore import Qt, QTimer

# ---------------- Constants ----------------
UPDATE_INTERVAL_MS = 2000
HISTORY_POINTS = 60
CARD_MIN_WIDTH = 320
CONFIG_DIR = os.path.expanduser("~/.config/plasmasys")
LOG_DIR = os.path.expanduser("~/.local/share/plasmasys")
SETTINGS_PATH = os.path.join(CONFIG_DIR, "settings.json")
LOG_PATH = os.path.join(LOG_DIR, "logs.csv")

DEFAULT_SETTINGS = {
    "cpu_temp_alert_celsius": 85,
    "sensor_temp_alert_celsius": 80,
    "log_enable": True,
    "log_interval_seconds": 5
}

# ---------- Helpers ----------
def ensure_dirs():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

def load_settings():
    ensure_dirs()
    s = DEFAULT_SETTINGS.copy()
    if os.path.exists(SETTINGS_PATH):
        try:
            s.update(json.load(open(SETTINGS_PATH)))
        except Exception:
            pass
    return s

def save_settings(s): json.dump(s, open(SETTINGS_PATH,"w"), indent=2)

def get_cpu_model():
    try:
        for line in open("/proc/cpuinfo"):
            if "model name" in line:
                return line.split(":",1)[1].strip()
    except: pass
    return platform.processor() or "Unknown CPU"

def get_board_model(): # Renamed from get_ram_model
    path="/sys/devices/virtual/dmi/id/board_name"
    if os.path.exists(path):
        try: return open(path).read().strip()
        except: pass
    return "N/A"

def get_disk_model():
    try:
        part = next((p for p in psutil.disk_partitions() if p.mountpoint=="/"),None)
        if not part: return None
        dev = ''.join(filter(str.isalpha, os.path.basename(part.device)))
        path=f"/sys/block/{dev}/device/model"
        if os.path.exists(path):
            return open(path).read().strip()
    except: pass
    return None

def get_local_ip():
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.connect(("8.8.8.8",80))
        ip=s.getsockname()[0]; s.close(); return ip
    except: return "N/A"

def get_connected_ssid():
    try:
        code,out=subprocess.getstatusoutput("iwgetid -r")
        if code==0 and out: return out.strip()
    except: pass
    return "N/A"

def get_os_distro():
    """Tries to get the OS/Distro name from /etc/os-release."""
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=",1)[1].strip().strip('"')
    except Exception:
        pass
    # Fallback
    return f"{platform.system()} {platform.release()}"

def format_speed(bytes_per_sec):
    """Formats speed in B/s to KB/s, MB/s, etc."""
    if bytes_per_sec < 1024:
        return f"{bytes_per_sec:.0f} B/s"
    elif bytes_per_sec < 1024**2:
        return f"{bytes_per_sec/1024:.1f} KB/s"
    elif bytes_per_sec < 1024**3:
        return f"{bytes_per_sec/1024**2:.1f} MB/s"
    else:
        return f"{bytes_per_sec/1024**3:.1f} GB/s"

def read_native_temps():
    temps={}
    base="/sys/class/thermal"
    if os.path.exists(base):
        for zone in os.listdir(base):
            if not zone.startswith("thermal_zone"): continue
            try:
                t=float(open(f"{base}/{zone}/temp").read().strip())
                typ=open(f"{base}/{zone}/type").read().strip()
                temps[typ]=t/1000 if t>1000 else t
            except: pass
    return temps

# ---------- Charts ----------
class LineChart(QWidget):
    def __init__(self, hist, color):
        super().__init__()
        self.h=hist; self.c=color
        self.setMinimumHeight(60)
    def paintEvent(self,e):
        if not self.h: return
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r=self.rect().adjusted(4,4,-4,-4)
        vmax=max(max(self.h),1)*1.05
        step=r.width()/max(1,len(self.h)-1)
        pen=QPen(self.c,2); p.setPen(pen)
        path=QPainterPath()
        data=list(self.h)
        path.moveTo(r.left(), r.bottom()-(data[0]/vmax)*r.height())
        for i,v in enumerate(data[1:],1):
            x=r.left()+i*step; y=r.bottom()-(v/vmax)*r.height()
            path.lineTo(x,y)
        p.drawPath(path)

# ---------- Cards ----------
class Card(QFrame):
    def __init__(self,title):
        super().__init__(); self.setFrameShape(QFrame.Shape.StyledPanel)
        v=QVBoxLayout(self); t=QLabel(title)
        t.setFont(QFont("Noto Sans",11,QFont.Weight.Bold))
        v.addWidget(t); self.body=QVBoxLayout(); v.addLayout(self.body)

class GeneralCard(Card):
    def __init__(self):
        super().__init__("General Info"); self.lbl=QLabel(); self.lbl.setWordWrap(True)
        self.body.addWidget(self.lbl); self.chart=None
    def set_chart(self,ch): self.body.addWidget(ch); self.chart=ch
    def update(self, host, ip, ssid, up_speed, down_speed, kernel, os_distro, board):
        text = (
            f"<b>Host:</b> {host}\n"
            f"<b>Model:</b> {board}\n"
            f"<b>OS:</b> {os_distro}\n"
            f"<b>Kernel:</b> {kernel}\n"
            f"<b>IP:</b> {ip}\n"
            f"<b>Network:</b> {ssid}\n"
            f"<b>Up:</b> {up_speed} | <b>Down:</b> {down_speed}"
        )
        self.lbl.setText(text.replace('\n', '<br>'))

class CpuCard(Card):
    def __init__(self):
        super().__init__("CPU"); self.info=QLabel(); self.info.setWordWrap(True)
        self.body.addWidget(self.info); self.core=QLabel(); self.core.setWordWrap(True)
        self.body.addWidget(self.core); self.chart=None
    def set_chart(self,ch): self.body.insertWidget(1,ch); self.chart=ch
    def update(self,model,cores):
        tot=sum(cores)/len(cores) if cores else 0
        self.info.setText(f"<b>{model}</b> — Total {tot:.0f}%")
        h=(len(cores)+1)//2
        L="<br>".join([f"Core{i+1}:{p:.0f}%" for i,p in enumerate(cores[:h])])
        R="<br>".join([f"Core{i+1+h}:{p:.0f}%" for i,p in enumerate(cores[h:])])
        self.core.setText(f"<table width=100%><tr><td>{L}</td><td>{R}</td></tr></table>")

class StorageCard(Card):
    def __init__(self):
        super().__init__("Memory & Storage")
        self.mem=QLabel(); self.mem.setWordWrap(True); self.body.addWidget(self.mem)
        self.chart=None; self.store=QLabel(); self.store.setWordWrap(True); self.body.addWidget(self.store)
    def set_chart(self,ch): self.body.insertWidget(1,ch); self.chart=ch
    def update_mem(self,tot,used,pct,model):
        ms=f"{model} • " if model and model != "N/A" else ""
        self.mem.setText(f"<b>RAM:</b> {ms}{used:.1f}/{tot:.1f} GB ({pct:.0f}%)")
    def update_store(self,txt): self.store.setText(txt)

class TempsCard(Card):
    def __init__(self):
        super().__init__("Temperatures & Fans"); self.lbl=QLabel(); self.lbl.setWordWrap(True); self.body.addWidget(self.lbl)
    def update(self,temps,fans):
        t="<br>".join(temps); f="<br>".join(fans)
        self.lbl.setText(f"<table width=100%><tr><td><b>Temps</b><br>{t}</td><td><b>Fans</b><br>{f}</td></tr></table>")

# ---------------- Settings ----------------
class SettingsDialog(QDialog):
    def __init__(self,s,parent=None):
        super().__init__(parent)
        self.s=s
        self.setWindowTitle("Settings")
        f=QFormLayout(self)
        self.cpu=QSpinBox(); self.cpu.setRange(40,120); self.cpu.setValue(s.get("cpu_temp_alert_celsius",85))
        f.addRow("CPU alert (°C)",self.cpu)
        self.sensor=QSpinBox(); self.sensor.setRange(30,120); self.sensor.setValue(s.get("sensor_temp_alert_celsius",80))
        f.addRow("Sensor alert (°C)",self.sensor)
        bb=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        f.addWidget(bb)
    def accept(self):
        self.s["cpu_temp_alert_celsius"]=self.cpu.value()
        self.s["sensor_temp_alert_celsius"]=self.sensor.value()
        save_settings(self.s)
        super().accept()

# ---------------- Main ----------------
class SensorMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PlasmaSys — Sensor Monitor")
        self.setWindowIcon(QIcon.fromTheme("plasmasys"))
        self.resize(800, 600)  # <-- Set a larger default size

        # --- Load settings and static info ---
        self.settings=load_settings()
        self.monitoring=True
        self.cpu_model=get_cpu_model()
        self.board_model = get_board_model() # <-- Use new function name
        self.disk_model = get_disk_model()   # <-- This is for the / disk, (not used in new code)
        self.kernel = platform.release()
        self.os_distro = get_os_distro()
        self.hostname = platform.node()

        # --- History & I/O counters for speed calculation ---
        self.cpu_hist=deque([0]*HISTORY_POINTS,maxlen=HISTORY_POINTS)
        self.mem_hist=deque([0]*HISTORY_POINTS,maxlen=HISTORY_POINTS)
        self.net_hist=deque([0]*HISTORY_POINTS,maxlen=HISTORY_POINTS)

        self.last_net_io = psutil.net_io_counters()
        self.last_disk_io = psutil.disk_io_counters()
        self.last_io_time = time.time()

        # --- Main Layout ---
        main=QVBoxLayout(self)
        scroll=QScrollArea(); scroll.setWidgetResizable(True)
        main.addWidget(scroll)

        container=QWidget(); grid=QGridLayout(container)
        grid.setContentsMargins(10,10,10,10)
        scroll.setWidget(container)

        # --- Make grid columns stretchable ---
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        # --- Cards ---
        self.general=GeneralCard()
        self.cpu=CpuCard()
        self.mem=StorageCard()
        self.temp=TempsCard()
        grid.addWidget(self.general,0,0)
        grid.addWidget(self.cpu,0,1)
        grid.addWidget(self.mem,1,0)
        grid.addWidget(self.temp,1,1)

        # --- Charts ---
        self.cpu.set_chart(LineChart(self.cpu_hist,QColor(136,190,210)))
        self.mem.set_chart(LineChart(self.mem_hist,QColor(235,203,139)))
        self.general.set_chart(LineChart(self.net_hist,QColor(163,190,140)))

        # Bottom bar
        row=QHBoxLayout()
        self.start_stop_btn=QPushButton("Stop"); self.start_stop_btn.clicked.connect(self.toggle_monitoring)
        self.export_btn=QPushButton("Export Logs"); self.export_btn.clicked.connect(self.export_logs)
        self.settings_btn=QPushButton("Settings"); self.settings_btn.clicked.connect(self.open_settings)
        self.about_btn=QPushButton("About"); self.about_btn.clicked.connect(self.show_about)
        for b in [self.start_stop_btn, self.export_btn, self.settings_btn, self.about_btn]:
            row.addWidget(b)
        row.addStretch(1)
        main.addLayout(row)

        # Tray
        self.tray=QSystemTrayIcon(self)
        self.tray_icon=QIcon.fromTheme("plasmasys") or self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray.setIcon(self.tray_icon)
        self.menu=QMenu()
        act_show=QAction("Show",self); act_show.triggered.connect(self.show_and_raise)
        act_set=QAction("Settings",self); act_set.triggered.connect(self.open_settings)
        act_quit=QAction("Quit",self); act_quit.triggered.connect(self.quit_app)
        self.menu.addActions([act_show,act_set,act_quit])
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

        self.timer=QTimer(self); self.timer.timeout.connect(self.update_all); self.timer.start(UPDATE_INTERVAL_MS)
        self.tooltip_timer=QTimer(self); self.tooltip_timer.timeout.connect(self.update_tooltip); self.tooltip_timer.start(3000)

        # Start first update
        self.update_all()

    # ---- Tray Dimming ----
    def set_tray_dimmed(self, dimmed: bool):
        base_icon = QIcon.fromTheme("plasmasys") or self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        pix = base_icon.pixmap(32, 32)
        img = pix.toImage()
        if dimmed:
            for y in range(img.height()):
                for x in range(img.width()):
                    c = QColor(img.pixel(x, y))
                    gray = int((c.red() + c.green() + c.blue()) / 3)
                    c.setRgb(gray, gray, gray, c.alpha())
                    img.setPixelColor(x, y, c)
        icon = QIcon(QPixmap.fromImage(img))
        self.tray.setIcon(icon)

    def on_tray_activated(self, reason):
        from PyQt6.QtWidgets import QSystemTrayIcon as STI
        if reason == STI.ActivationReason.Context:
            QTimer.singleShot(50, lambda: self.menu.exec(QCursor.pos()))
        elif reason == STI.ActivationReason.Trigger:
            self.show_and_raise()

    def toggle_monitoring(self):
        self.monitoring = not self.monitoring
        self.start_stop_btn.setText("Stop" if self.monitoring else "Start")
        self.set_tray_dimmed(not self.monitoring)

    def show_and_raise(self): self.show(); self.activateWindow(); self.raise_()
    def open_settings(self):
        dlg=SettingsDialog(self.settings,self)
        if dlg.exec(): self.settings=load_settings()
    def show_about(self):
        QMessageBox.information(self,"About","PlasmaSys — Sensor Monitor\nDeveloper: Muhammad Asif Rauf\nVersion: 1.0 (KDE6 Compatible)")
    def quit_app(self): self.tray.hide(); QApplication.quit()

    # 🔔 Confirmation when closing window
    def closeEvent(self, event):
        reply = QMessageBox(self)
        reply.setWindowTitle("Exit PlasmaSys")
        reply.setText("Do you want to quit PlasmaSys or keep it running in the system tray?")
        reply.setIcon(QMessageBox.Icon.Question)
        quit_button = reply.addButton("Quit", QMessageBox.ButtonRole.AcceptRole)
        tray_button = reply.addButton("Keep in Tray", QMessageBox.ButtonRole.RejectRole)
        reply.setDefaultButton(tray_button)
        reply.exec()
        if reply.clickedButton() == quit_button:
            self.tray.hide()
            QApplication.quit()
        else:
            event.ignore()
            self.hide()
            self.tray.showMessage("PlasmaSys", "PlasmaSys is still running in the system tray.")

    def export_logs(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Logs", os.path.expanduser("~/plasmasys_logs.csv"), "CSV Files (*.csv)")
        if path:
            try:
                with open(LOG_PATH, "r", encoding="utf-8") as src, open(path, "w", encoding="utf-8") as dst:
                    dst.write(src.read())
                QMessageBox.information(self, "Export", f"Logs exported to:\n{path}")
            except Exception as e:
                QMessageBox.warning(self, "Export Failed", str(e))

    def update_tooltip(self):
        try:
            cpu=psutil.cpu_percent()
            mem=psutil.virtual_memory().percent
            temps=psutil.sensors_temperatures()
            t=None
            for v in temps.values():
                for e in v:
                    if e.current: t=e.current
            text=f"CPU: {cpu:.0f}% | Mem: {mem:.0f}%"
            if t: text+=f" | Temp: {t:.1f}°C"
            self.tray.setToolTip(f"PlasmaSys — {text}")
        except Exception:
            self.tray.setToolTip("PlasmaSys — Monitoring...")

    def update_all(self):
        if not self.monitoring: return

        # --- Calculate time delta for speeds ---
        current_time = time.time()
        time_delta = current_time - self.last_io_time
        # Prevent division by zero on first run or if timer is too fast
        if time_delta == 0:
             time_delta = 1

        # --- CPU ---
        cores=psutil.cpu_percent(interval=None,percpu=True)
        total=sum(cores)/len(cores)
        self.cpu_hist.append(total)
        self.cpu.update(self.cpu_model,cores)

        # --- Memory ---
        mem=psutil.virtual_memory()
        self.mem_hist.append(mem.percent)
        # Pass the board_model (renamed from ram_model)
        self.mem.update_mem(mem.total/(1024**3), mem.used/(1024**3), mem.percent, self.board_model)

        # --- Storage & Disk I/O ---
        disk_info = []
        try:
            # Get all partitions
            partitions = psutil.disk_partitions()
            valid_partitions = [p for p in partitions if p.fstype and not p.mountpoint.startswith(('/snap', '/boot', '/var/lib/docker'))]

            for p in valid_partitions:
                usage = psutil.disk_usage(p.mountpoint)
                # Format mountpoint
                mp = p.mountpoint
                if len(mp) > 15:
                    mp = mp[:12] + "..."

                disk_info.append(f"<b>{mp} ({p.fstype}):</b> {usage.used/(1024**3):.1f}/{usage.total/(1024**3):.1f} GB ({usage.percent:.0f}%)")

            # Get Disk R/W Speed
            current_disk_io = psutil.disk_io_counters()
            read_speed = (current_disk_io.read_bytes - self.last_disk_io.read_bytes) / time_delta
            write_speed = (current_disk_io.write_bytes - self.last_disk_io.write_bytes) / time_delta

            disk_info.append(f"<b>Disk R/W:</b> {format_speed(read_speed)} / {format_speed(write_speed)}")
            self.last_disk_io = current_disk_io

            self.mem.update_store("<br>".join(disk_info))

        except Exception as e:
            self.mem.update_store(f"<b>Disk Info:</b> Error")

        # --- Temperatures & Fans ---
        temps=[]
        try:
            td=psutil.sensors_temperatures()
            for k,v in td.items():
                for e in v:
                    temps.append(f"{e.label or k}: {e.current:.1f}°C")
        except Exception:
            temps.append("No temp sensors")

        fans = []
        try:
            fd = psutil.sensors_fans()
            for k, v in fd.items():
                for e in v:
                    fans.append(f"{e.label or k}: {e.current} RPM")
        except Exception:
            fans.append("No fan sensors")

        self.temp.update(temps, fans)

        # --- General Info & Network I/O ---
        try:
            # Get Network Speeds
            current_net_io = psutil.net_io_counters()
            up_speed = (current_net_io.bytes_sent - self.last_net_io.bytes_sent) / time_delta
            down_speed = (current_net_io.bytes_recv - self.last_net_io.bytes_recv) / time_delta
            self.net_hist.append((up_speed + down_speed) / 1024) # Log total speed in KB/s
            self.last_net_io = current_net_io

            # Get dynamic network info
            ip = get_local_ip()
            ssid = get_connected_ssid()

            # Update the card
            self.general.update(
                host=self.hostname,
                ip=ip,
                ssid=ssid,
                up_speed=format_speed(up_speed),
                down_speed=format_speed(down_speed),
                kernel=self.kernel,
                os_distro=self.os_distro,
                board=self.board_model
            )
        except Exception as e:
            self.general.update("Error", str(e), "N/A", "N/A", "N/A", "N/A", "N/A", "N/A")

        # --- Update shared I/O time ---
        self.last_io_time = current_time

# ---------------- main ----------------
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PlasmaSys")
    win = SensorMonitor()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
