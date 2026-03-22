import sys
import os
import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, Optional

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
        QPushButton, QLabel, QListWidget, QTextEdit, QFileDialog,
        QMessageBox, QGroupBox, QLineEdit, QTabWidget, QListWidgetItem,
        QComboBox, QFormLayout, QDialog, QDialogButtonBox, QFrame,
        QScrollArea, QStackedWidget, QSizePolicy, QSpacerItem, QStyledItemDelegate, QStyle
    )
    from PyQt6.QtCore import QTimer, QThread, pyqtSignal, Qt, QSize, QPoint, QRect, QEvent
    from PyQt6.QtGui import (
        QFont, QIcon, QPainter, QColor, QPen, QPixmap, QPainterPath,
        QLinearGradient, QBrush, QPalette, QConicalGradient, QRadialGradient
    )
except ImportError as e:
    print(f"ERROR: PyQt6 not installed: {e}")
    sys.exit(1)

import datetime
import re
import math


# ── Custom ComboBox Delegate with Accent Hover Effect ──────────────────────────
class AccentHoverDelegate(QStyledItemDelegate):
    """Custom delegate for ComboBox that highlights items with accent color on hover."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._hover_index = -1
    
    def paint(self, painter, option, index):
        """Paint item with custom hover highlighting in accent color."""
        # Check if this is the hovered item
        is_hover = index.row() == self._hover_index
        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        
        # Paint background
        if is_selected or is_hover:
            # Use accent color for both hover and selected states with full opacity
            color = QColor(Colors.ORANGE)
            color.setAlpha(255)  # Full opacity for maximum contrast
            painter.fillRect(option.rect, color)
            
            # Add slight border for extra definition
            painter.setPen(QColor(255, 255, 255, 60))  # Subtle white border
            painter.drawRect(option.rect.adjusted(0, 0, -1, -1))
        else:
            painter.fillRect(option.rect, QColor(Colors.BG_ELEV))
        
        # Paint text - white on accent background for best contrast
        if is_selected or is_hover:
            painter.setPen(QColor(255, 255, 255))  # White text on accent
        else:
            painter.setPen(QColor(Colors.TXT_PRI))
        
        painter.setFont(option.font)
        painter.drawText(option.rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, 
                        '  ' + index.data())
    
    def editorEvent(self, event, model, option, index):
        """Track mouse hover position."""
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.MouseMove:
            self._hover_index = index.row()
        elif event.type() == QEvent.Type.Leave:
            self._hover_index = -1
        return super().editorEvent(event, model, option, index)


# ── Config fallback ──────────────────────────────────────────────────────────
try:
    from config import (
        APP_NAME, APP_VERSION, ORGANIZATION_NAME,
        get_developer_string, get_version_string, OPENVPN_DNS_SCRIPT
    )
except ImportError:
    APP_NAME = "OpenVPN Connect"
    APP_VERSION = "3.5.0"
    ORGANIZATION_NAME = "OpenVPN Inc."
    OPENVPN_DNS_SCRIPT = None
    def get_developer_string(): return "OpenVPN Connect"
    def get_version_string(): return f"v{APP_VERSION}"

# ── Theme — ALL colors live here, reads from GNOME/Ubuntu gsettings ───────────
from theme import ThemeManager, Colors


# ── CSS builders — rebuilt on every theme change ─────────────────────────────

def build_main_css() -> str:
    c = Colors
    ar, ag, ab = c.accent_rgb()
    return f"""
QMainWindow {{ background: {c.BG_BASE}; }}
QWidget {{ font-family: 'Ubuntu', 'Noto Sans', 'Segoe UI', sans-serif; }}

#Sidebar {{
    background: {c.BG_SIDEBAR};
    border-right: 1px solid {c.BORDER};
}}

QPushButton#NavBtn {{
    background: transparent;
    color: {c.TXT_MUT};
    border: none;
    border-radius: 0;
    text-align: left;
    padding: 0 16px;
    font-size: 12px;
    min-height: 44px;
}}
QPushButton#NavBtn:checked {{
    background: rgba({ar},{ag},{ab},38);
    color: {c.ORANGE};
    border-left: 3px solid {c.ORANGE};
}}
QPushButton#NavBtn:hover:!checked {{
    background: rgba(255,255,255,13);
    color: {c.TXT_SEC};
}}

#Content {{ background: {c.BG_BASE}; }}

#Card {{
    background: {c.BG_CARD};
    border: 1px solid {c.BORDER};
    border-radius: 8px;
}}

QComboBox {{
    background: {c.BG_ELEV};
    color: {c.TXT_PRI};
    border: 1px solid {c.BORDER_LT};
    border-radius: 5px;
    padding: 0 10px;
    font-size: 12px;
    min-height: 32px;
}}
QComboBox:hover {{ 
    border: 2px solid {c.ORANGE};
    padding: 0 9px;
}}
QComboBox:focus {{ 
    border: 2px solid {c.ORANGE};
    padding: 0 9px;
    background: {c.BG_SURF};
}}
QComboBox::drop-down {{ 
    border: none; 
    width: 22px;
    background: transparent;
}}
QComboBox QAbstractItemView {{
    background: {c.BG_ELEV};
    color: {c.TXT_PRI};
    border: 1px solid {c.BORDER_LT};
    border-radius: 4px;
    outline: none;
    margin: 0px;
    padding: 0px;
}}
QComboBox QAbstractItemView::item {{
    height: 28px;
    padding: 4px 12px;
}}
QComboBox QAbstractItemView {{ 
    selection-background-color: rgba({ar},{ag},{ab},128);
    selection-color: {c.ORANGE};
}}

QListWidget {{
    background: {c.BG_CARD};
    color: {c.TXT_PRI};
    border: 1px solid {c.BORDER};
    border-radius: 6px;
    outline: none;
    font-size: 12px;
}}
QListWidget::item {{ padding: 7px 12px; border-radius: 4px; }}
QListWidget::item:hover {{ background: {c.BG_ELEV}; }}
QListWidget::item:selected {{
    background: rgba({ar},{ag},{ab},64);
    color: {c.ORANGE};
}}

QTextEdit {{
    background: {c.BG_BASE};
    color: {c.LOG_TEXT};
    border: 1px solid {c.BORDER};
    border-radius: 6px;
    padding: 8px;
    font-family: 'Ubuntu Mono', 'Courier New', monospace;
    font-size: 11px;
}}

QScrollBar:vertical {{ background: transparent; width: 5px; margin: 0; }}
QScrollBar::handle:vertical {{
    background: {c.BORDER_LT}; border-radius: 2px; min-height: 16px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QPushButton#ConnectBtn {{
    background: {c.ORANGE};
    color: #fff;
    border: none;
    border-radius: 5px;
    font-size: 12px;
    font-weight: 600;
    min-height: 34px;
    padding: 5px 20px;
}}
QPushButton#ConnectBtn:hover   {{ background: {c.ORANGE_L}; }}
QPushButton#ConnectBtn:pressed {{ background: {c.ORANGE_D}; }}
QPushButton#ConnectBtn:disabled {{
    background: {c.BG_ELEV};
    color: {c.TXT_MUT};
    border: 1px solid {c.BORDER};
}}

QPushButton#DisconnectBtn {{
    background: {c.RED_DARK};
    color: #fff;
    border: none;
    border-radius: 5px;
    font-size: 12px;
    font-weight: 600;
    min-height: 34px;
    padding: 5px 20px;
}}
QPushButton#DisconnectBtn:hover   {{ background: {c.RED_ERR};  }}
QPushButton#DisconnectBtn:pressed {{ background: {c.RED_DEEP}; }}

QPushButton#SmBtn {{
    background: {c.BG_ELEV};
    color: {c.TXT_SEC};
    border: 1px solid {c.BORDER};
    border-radius: 5px;
    padding: 5px 12px;
    font-size: 11px;
    min-height: 28px;
}}
QPushButton#SmBtn:hover {{
    background: {c.BORDER};
    color: {c.TXT_PRI};
    border-color: {c.BORDER_LT};
}}
QPushButton#SmBtn[danger="true"] {{ color: {c.RED_ERR}; }}
QPushButton#SmBtn[danger="true"]:hover {{
    background: rgba(231,76,60,38);
    border-color: {c.RED_ERR};
}}

QPushButton#AddBtn {{
    background: rgba({ar},{ag},{ab},38);
    color: {c.ORANGE};
    border: 1px solid rgba({ar},{ag},{ab},77);
    border-radius: 5px;
    padding: 5px 14px;
    font-size: 11px;
    font-weight: 600;
    min-height: 28px;
}}
QPushButton#AddBtn:hover {{ background: rgba({ar},{ag},{ab},71); }}
"""


def build_dialog_css() -> str:
    c = Colors
    return f"""
QDialog {{ background: {c.BG_BASE}; }}
QLabel {{ color: {c.TXT_SEC}; font-size: 12px; }}
QLabel#title {{ color: {c.TXT_PRI}; font-size: 13px; font-weight: 600; }}
QLineEdit {{
    background: {c.BG_ELEV};
    color: {c.TXT_PRI};
    border: 1px solid {c.BORDER_LT};
    border-radius: 5px;
    padding: 7px 10px;
    font-size: 12px;
    selection-background-color: {c.ORANGE};
}}
QLineEdit:focus {{ border-color: {c.ORANGE}; }}
QPushButton {{
    background: {c.BG_ELEV};
    color: {c.TXT_SEC};
    border: 1px solid {c.BORDER};
    border-radius: 5px;
    padding: 7px 14px;
    font-size: 12px;
}}
QPushButton:hover {{ background: {c.BORDER}; color: {c.TXT_PRI}; }}
QPushButton#ok {{
    background: {c.ORANGE};
    color: #fff;
    border: none;
    font-weight: 600;
}}
QPushButton#ok:hover   {{ background: {c.ORANGE_L}; }}
QPushButton#ok:pressed {{ background: {c.ORANGE_D}; }}
"""


# ── Misc helpers ──────────────────────────────────────────────────────────────

def run_privileged(cmd, **kwargs):
    if os.getuid() == 0:
        return subprocess.run(cmd, **kwargs)
    tool = 'pkexec' if shutil.which('pkexec') else 'sudo'
    return subprocess.run([tool] + cmd, **kwargs)


def fmt_bytes(b):
    if b is None: return "—"
    if b < 1024:    return f"{b} B"
    if b < 1024**2: return f"{b/1024:.1f} KB"
    if b < 1024**3: return f"{b/1024**2:.2f} MB"
    return f"{b/1024**3:.2f} GB"


def fmt_dur(secs):
    h, r = divmod(max(int(secs), 0), 3600)
    m, s = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def h_rule():
    f = QFrame(); f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"color: {Colors.BORDER};")
    return f


# ── Animated Status Dot ───────────────────────────────────────────────────────

class StatusDot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = "off"
        self._angle = 0
        self._pulse = 0.0
        self._pd = 1
        self.setFixedSize(56, 56)
        t = QTimer(self); t.timeout.connect(self._tick); t.start(25)

    def set_state(self, s):
        self._state = s; self.update()

    def _tick(self):
        if self._state == "spinning":
            self._angle = (self._angle + 8) % 360
        self._pulse += 0.05 * self._pd
        if self._pulse >= 1: self._pd = -1
        elif self._pulse <= 0: self._pd = 1
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy, r = 28, 28, 20
        accent = QColor(Colors.ORANGE)

        if self._state == "on":
            glow = int(18 + 12 * self._pulse)
            for gr in [r + 9, r + 5]:
                p.setPen(Qt.PenStyle.NoPen)
                gc = QColor(accent); gc.setAlpha(glow); p.setBrush(gc)
                p.drawEllipse(cx - gr, cy - gr, gr * 2, gr * 2)

        pen = QPen(QColor(Colors.BORDER_LT)); pen.setWidth(5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        if self._state == "on":
            pen = QPen(accent); pen.setWidth(5)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawEllipse(cx - r, cy - r, r * 2, r * 2)
        elif self._state == "spinning":
            grad = QConicalGradient(cx, cy, self._angle)
            ar, ag, ab = accent.red(), accent.green(), accent.blue()
            grad.setColorAt(0.0, QColor(ar, ag, ab, 255))
            grad.setColorAt(0.4, QColor(ar, ag, ab, 80))
            grad.setColorAt(0.9, QColor(ar, ag, ab, 0))
            arc_pen = QPen(QBrush(grad), 5)
            arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(arc_pen)
            p.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor(Colors.BG_ELEV))
        p.drawEllipse(cx - r + 7, cy - r + 7, (r - 7) * 2, (r - 7) * 2)

        if self._state == "on":
            self._draw_shield(p, cx, cy, True)
        elif self._state == "spinning":
            alpha = int(120 + 120 * abs(math.sin(math.radians(self._angle))))
            sc = QColor(accent); sc.setAlpha(alpha); p.setBrush(sc)
            p.drawEllipse(cx - 3, cy - 3, 6, 6)
        else:
            self._draw_shield(p, cx, cy, False)

    def _draw_shield(self, p, cx, cy, active):
        color = QColor(Colors.ORANGE) if active else QColor(Colors.TXT_MUT)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(color)
        path = QPainterPath()
        path.moveTo(cx, cy - 7); path.lineTo(cx + 6, cy - 4)
        path.lineTo(cx + 6, cy + 1)
        path.quadTo(cx + 6, cy + 7, cx, cy + 9)
        path.quadTo(cx - 6, cy + 7, cx - 6, cy + 1)
        path.lineTo(cx - 6, cy - 4); path.closeSubpath()
        p.fillPath(path, color)
        if active:
            pen = QPen(QColor(Colors.BG_ELEV)); pen.setWidth(2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawLine(int(cx - 3), int(cy + 1), int(cx), int(cy + 4))
            p.drawLine(int(cx), int(cy + 4), int(cx + 4), int(cy - 2))


# ── Mini Traffic Chart ────────────────────────────────────────────────────────

class TinyChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ups, self.dns = [], []
        self.setMinimumHeight(40)

    def push(self, up, dn):
        self.ups.append(max(up, 0)); self.dns.append(max(dn, 0))
        if len(self.ups) > 80: self.ups.pop(0)
        if len(self.dns) > 80: self.dns.pop(0)
        self.update()

    def clear(self):
        self.ups, self.dns = [], []; self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, QColor(Colors.BG_BASE))
        n = max(len(self.ups), len(self.dns))
        if n < 2: return
        pk = max(max(self.ups, default=0), max(self.dns, default=0), 1.0)

        def series(pts, hex_col, alpha):
            if len(pts) < 2: return
            fill = QPainterPath(); line = QPainterPath()
            for i, v in enumerate(pts):
                x = int(w * i / (n - 1)); y = int(h - h * v / pk)
                if i == 0:
                    fill.moveTo(x, h); fill.lineTo(x, y); line.moveTo(x, y)
                else:
                    fill.lineTo(x, y); line.lineTo(x, y)
            fill.lineTo(w, h); fill.closeSubpath()
            fc = QColor(hex_col); fc.setAlpha(alpha); p.fillPath(fill, fc)
            pen = QPen(QColor(hex_col)); pen.setWidth(1)
            p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush); p.drawPath(line)

        series(self.dns, Colors.ORANGE, 45)
        series(self.ups, Colors.BLUE_UP, 35)


# ── VPN Thread ────────────────────────────────────────────────────────────────

class OpenVPNThread(QThread):
    status_changed         = pyqtSignal(str)
    output_received        = pyqtSignal(str)
    connection_established = pyqtSignal(str)
    connection_failed      = pyqtSignal(str)
    finished_cleanup       = pyqtSignal()

    def __init__(self, config_path, username=None, password=None):
        super().__init__()
        self.config_path = config_path
        self.username = username
        self.password = password
        self.process = None
        self.should_stop = False
        self.auth_file = None
        self.vpn_iface = None
        self.temp_config = None

    def _prepare_config(self, config_path):
        try:
            with open(config_path, 'r') as f:
                lines = f.readlines()
            filtered = []; removed = set()
            for line in lines:
                s = line.strip()
                if s.startswith('up ') or s.startswith('down '):
                    parts = s.split(None, 1)
                    if len(parts) > 1:
                        script = parts[1].strip().strip('\'"')
                        if not (os.path.exists(script) and os.access(script, os.X_OK)):
                            removed.add(script); continue
                filtered.append(line)
            if not removed:
                return config_path
            for sc in removed:
                self.output_received.emit(f"⚠ Skipping missing script: {sc}")
            import tempfile
            fd, self.temp_config = tempfile.mkstemp(suffix='.ovpn', text=True)
            try:
                with os.fdopen(fd, 'w') as f: f.writelines(filtered)
                os.chmod(self.temp_config, 0o600)
                return self.temp_config
            except Exception as ex:
                os.close(fd)
                if self.temp_config and os.path.exists(self.temp_config):
                    try: os.unlink(self.temp_config)
                    except: pass
                self.temp_config = None; raise ex
        except Exception as ex:
            try: self.output_received.emit(f"⚠ Could not preprocess config: {ex}")
            except: pass
            return config_path

    def run(self):
        try:
            if os.getuid() == 0:          cmd = ['openvpn']
            elif shutil.which('pkexec'):   cmd = ['pkexec', 'openvpn']
            else:                          cmd = ['sudo', 'openvpn']

            cfg = self._prepare_config(self.config_path)
            cmd += ['--config', cfg, '--verb', '3', '--script-security', '2']

            dns = None
            if OPENVPN_DNS_SCRIPT and os.path.exists(OPENVPN_DNS_SCRIPT) and os.access(OPENVPN_DNS_SCRIPT, os.X_OK):
                dns = OPENVPN_DNS_SCRIPT
            if not dns:
                for s in ['/etc/openvpn/update-resolv-conf', '/etc/openvpn/update-systemd-resolved']:
                    if os.path.exists(s) and os.access(s, os.X_OK): dns = s; break
            if dns:
                cmd += ['--up', dns, '--down', dns]

            if self.username and self.password:
                import tempfile
                fd, self.auth_file = tempfile.mkstemp(suffix='_ovpn_auth', text=True)
                try:
                    with os.fdopen(fd, 'w') as f: f.write(f"{self.username}\n{self.password}\n")
                    cmd += ['--auth-user-pass', self.auth_file]
                    os.chmod(self.auth_file, 0o600)
                except Exception as ex:
                    os.close(fd)
                    if self.auth_file and os.path.exists(self.auth_file):
                        try: os.unlink(self.auth_file)
                        except: pass
                    self.auth_file = None; raise ex

            self.status_changed.emit("Connecting…")
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, bufsize=1, preexec_fn=os.setsid
            )
            ok = fail = False
            for line in iter(self.process.stdout.readline, ''):
                if self.should_stop: break
                line = line.strip()
                if line: self.output_received.emit(line)
                if not ok and not fail:
                    m = re.search(r'TUN/TAP device (\w+) opened', line)
                    if m: self.vpn_iface = m.group(1)
                    if any(x in line for x in ["Initialization Sequence Completed", "VPN tunnel is ready"]):
                        self.status_changed.emit("Connected")
                        self.connection_established.emit(self.vpn_iface or ""); ok = True
                    elif "AUTH_FAILED" in line or "Authentication failed" in line:
                        self.connection_failed.emit("Authentication failed"); fail = True
                    elif "TLS Error" in line or "TLS handshake failed" in line:
                        self.connection_failed.emit("TLS/Certificate error"); fail = True
                    elif "FATAL" in line:
                        self.connection_failed.emit(f"Fatal: {line}"); fail = True

            rc = self.process.wait()
            if not ok and not fail and not self.should_stop:
                self.connection_failed.emit(f"Connection failed (exit {rc})")
        except PermissionError:
            self.connection_failed.emit("Permission denied — run as root/sudo")
        except FileNotFoundError:
            self.connection_failed.emit("openvpn not found — install the openvpn package")
        except Exception as ex:
            self.connection_failed.emit(str(ex))
        finally:
            self._cleanup(); self.finished_cleanup.emit()

    def _cleanup(self):
        for attr in ('auth_file', 'temp_config'):
            path = getattr(self, attr)
            if path and os.path.exists(path):
                try: os.unlink(path)
                except: pass
            setattr(self, attr, None)

    def stop(self):
        self.should_stop = True
        try:
            kill = ['pkill', '-TERM', 'openvpn']
            if os.getuid() == 0: subprocess.run(kill, capture_output=True, timeout=10)
            else: run_privileged(kill, capture_output=True, timeout=10)
            import time; time.sleep(2)
            if subprocess.run(['pgrep', 'openvpn'], capture_output=True).returncode == 0:
                kill9 = ['pkill', '-KILL', 'openvpn']
                if os.getuid() == 0: subprocess.run(kill9, capture_output=True, timeout=10)
                else: run_privileged(kill9, capture_output=True, timeout=10)
        except: pass
        if self.process and self.process.poll() is None:
            try:
                import signal as _sig
                os.killpg(os.getpgid(self.process.pid), _sig.SIGTERM)
                try: self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(self.process.pid), _sig.SIGKILL)
                    self.process.wait()
            except: pass
            finally: self.process = None
        self._cleanup()


# ── Data models ───────────────────────────────────────────────────────────────

class VPNConfig:
    def __init__(self, name, config_path, username="", password=""):
        self.name = name; self.config_path = config_path
        self.username = username; self.password = password


class ConfigManager:
    def __init__(self):
        d = Path.home() / '.openvpn_gui'; d.mkdir(exist_ok=True)
        self._f = d / 'configs.json'
        self.configs: Dict[str, VPNConfig] = self._load()

    def _load(self):
        if self._f.exists():
            try:
                with open(self._f) as f:
                    return {k: VPNConfig(**v) for k, v in json.load(f).items()}
            except: pass
        return {}

    def save(self):
        with open(self._f, 'w') as f:
            json.dump({k: v.__dict__ for k, v in self.configs.items()}, f, indent=2)

    def add(self, c): self.configs[c.name] = c; self.save()
    def remove(self, n):
        if n in self.configs: del self.configs[n]; self.save()
    def get(self, n): return self.configs.get(n)


# ── Add / Edit Profile Dialog ─────────────────────────────────────────────────

class AddProfileDialog(QDialog):
    def __init__(self, parent=None, cfg=None):
        super().__init__(parent)
        self.cfg = cfg
        self.setWindowTitle("Add Profile" if not cfg else "Edit Profile")
        self.setModal(True); self.setFixedSize(420, 310)
        self.setStyleSheet(build_dialog_css()); self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(22, 20, 22, 20); lay.setSpacing(12)
        t = QLabel("Profile" if not self.cfg else "Edit Profile")
        t.setObjectName("title"); lay.addWidget(t)

        form = QFormLayout(); form.setVerticalSpacing(8); form.setHorizontalSpacing(14)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.name_e = QLineEdit(); self.name_e.setPlaceholderText("My VPN")
        self.name_e.setMinimumHeight(34); form.addRow("Name:", self.name_e)

        pr = QHBoxLayout(); pr.setSpacing(6)
        self.path_e = QLineEdit(); self.path_e.setPlaceholderText("config.ovpn")
        self.path_e.setMinimumHeight(34)
        brw = QPushButton("…"); brw.setFixedSize(34, 34); brw.clicked.connect(self._browse)
        pr.addWidget(self.path_e); pr.addWidget(brw); form.addRow(".ovpn:", pr)

        self.user_e = QLineEdit(); self.user_e.setPlaceholderText("optional")
        self.user_e.setMinimumHeight(34); form.addRow("User:", self.user_e)

        self.pass_e = QLineEdit(); self.pass_e.setPlaceholderText("optional")
        self.pass_e.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_e.setMinimumHeight(34); form.addRow("Pass:", self.pass_e)

        lay.addLayout(form); lay.addStretch()
        brow = QHBoxLayout(); brow.setSpacing(8)
        cancel = QPushButton("Cancel"); cancel.setMinimumHeight(34); cancel.clicked.connect(self.reject)
        ok = QPushButton("Save"); ok.setObjectName("ok"); ok.setMinimumHeight(34)
        ok.clicked.connect(self.accept)
        brow.addWidget(cancel); brow.addWidget(ok); lay.addLayout(brow)

        if self.cfg:
            self.name_e.setText(self.cfg.name); self.path_e.setText(self.cfg.config_path)
            self.user_e.setText(self.cfg.username); self.pass_e.setText(self.cfg.password)

    def _browse(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Select .ovpn", "", "OpenVPN (*.ovpn);;All (*)")
        if fp:
            self.path_e.setText(fp)
            if not self.name_e.text(): self.name_e.setText(Path(fp).stem)

    def data(self):
        return {
            'name': self.name_e.text().strip(), 'config_path': self.path_e.text().strip(),
            'username': self.user_e.text().strip(), 'password': self.pass_e.text().strip(),
        }


# ── Main Window ───────────────────────────────────────────────────────────────

class OpenVPNConnectGUI(QMainWindow):

    def __init__(self):
        super().__init__()
        self.cfgman = ConfigManager()
        self.vpn_thread = None
        self.connected = False
        self.cur_cfg: Optional[VPNConfig] = None
        self.start_time = None; self.vpn_iface = None
        self.sent_pts, self.recv_pts = [], []
        self.last_sent = self.last_recv = None
        self.ss_sent = self.ss_recv = None
        self.sessions = []; self.total_secs = 0; self.sess_final = True

        # Theme — reads gsettings on startup, watches for live changes
        self._theme = ThemeManager(self)
        self._theme.theme_changed.connect(self._apply_theme)
        self._theme.start()

        self.setStyleSheet(build_main_css())
        self._build()
        self._timer = QTimer(self); self._timer.timeout.connect(self._tick); self._timer.start(1000)

    # ── Theme helpers ─────────────────────────────────────────────────────────

    def _make_connect_style(self) -> str:
        c = Colors
        return (
            f"QPushButton {{ background: {c.ORANGE}; color: #fff; border: none; "
            f"border-radius: 5px; font-size: 12px; font-weight: 600; }}"
            f"QPushButton:hover   {{ background: {c.ORANGE_L}; }}"
            f"QPushButton:pressed {{ background: {c.ORANGE_D}; }}"
            f"QPushButton:disabled {{ background: {c.BG_ELEV}; color: {c.TXT_MUT}; "
            f"border: 1px solid {c.BORDER}; }}"
        )

    def _make_disconnect_style(self) -> str:
        c = Colors
        return (
            f"QPushButton {{ background: {c.RED_DARK}; color: #fff; border: none; "
            f"border-radius: 5px; font-size: 12px; font-weight: 600; }}"
            f"QPushButton:hover   {{ background: {c.RED_ERR};  }}"
            f"QPushButton:pressed {{ background: {c.RED_DEEP}; }}"
        )

    def _apply_theme(self, accent_hex: str, is_dark: bool):
        """Rebuild all styles when Ubuntu/GNOME theme changes."""
        self.setStyleSheet(build_main_css())
        c = Colors
        self._conn_btn_style_connect    = self._make_connect_style()
        self._conn_btn_style_disconnect = self._make_disconnect_style()

        if self.connected:
            self._conn_btn.setStyleSheet(self._conn_btn_style_disconnect)
            self._big_status.setStyleSheet(
                f"color: {c.ORANGE}; font-size: 14px; font-weight: 700; background: transparent;"
            )
        else:
            self._conn_btn.setStyleSheet(self._conn_btn_style_connect)
            self._big_status.setStyleSheet(
                f"color: {c.TXT_SEC}; font-size: 14px; font-weight: 700; background: transparent;"
            )
        self._up_rate.setStyleSheet(f"color: {c.BLUE_UP}; font-size: 10px; font-weight: 700;")
        self._dn_rate.setStyleSheet(f"color: {c.ORANGE};  font-size: 10px; font-weight: 700;")
        self._dot.update()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self):
        self.setWindowTitle(APP_NAME); self.setMinimumSize(680, 520); self.resize(700, 540)
        root = QWidget(); self.setCentralWidget(root)
        rl = QHBoxLayout(root); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(0)

        # Sidebar
        sb = QWidget(); sb.setObjectName("Sidebar"); sb.setFixedWidth(172)
        sbl = QVBoxLayout(sb); sbl.setContentsMargins(0, 0, 0, 0); sbl.setSpacing(0)

        logo_w = QWidget(); logo_w.setFixedHeight(60)
        logo_w.setStyleSheet(f"background: {Colors.BG_SIDEBAR};")
        ll = QHBoxLayout(logo_w); ll.setContentsMargins(0, 0, 0, 0)
        name_lbl = QLabel("OpenVPN Manager"); name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet(
            f"color: {Colors.TXT_PRI}; font-size: 12px; font-weight: 700; "
            f"background: transparent; border-right: 1px solid {Colors.BORDER};"
        )
        ll.addWidget(name_lbl); sbl.addWidget(logo_w)
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {Colors.BORDER};"); sbl.addWidget(sep)
        sbl.addSpacing(4)

        self._navbtns = []
        for icon, label, idx in [("●", "Status", 0), ("☰", "Profiles", 1),
                                   ("📊", "Stats", 2), ("▶", "Log", 3)]:
            b = QPushButton(f"  {icon}   {label}"); b.setObjectName("NavBtn"); b.setCheckable(True)
            b.clicked.connect(lambda _=False, i=idx: self._nav(i))
            self._navbtns.append(b); sbl.addWidget(b)

        sbl.addStretch()
        try:   dev_str = get_developer_string()
        except: dev_str = "OpenVPN Manager"
        vl = QLabel(f"{dev_str}  ·  v{APP_VERSION}")
        vl.setAlignment(Qt.AlignmentFlag.AlignCenter); vl.setWordWrap(True)
        vl.setStyleSheet(f"color: {Colors.TXT_MUT}; font-size: 9px; padding: 6px 8px;")
        sbl.addWidget(vl); rl.addWidget(sb)

        # Content
        content = QWidget(); content.setObjectName("Content")
        cl = QVBoxLayout(content); cl.setContentsMargins(0, 0, 0, 0); cl.setSpacing(0)
        self.stack = QStackedWidget(); self.stack.setStyleSheet(f"background: {Colors.BG_BASE};")
        cl.addWidget(self.stack); rl.addWidget(content, 1)

        self.stack.addWidget(self._pg_status())
        self.stack.addWidget(self._pg_profiles())
        self.stack.addWidget(self._pg_stats())
        self.stack.addWidget(self._pg_log())
        self._nav(0)

    def _nav(self, idx):
        self.stack.setCurrentIndex(idx)
        for i, b in enumerate(self._navbtns): b.setChecked(i == idx)

    # ── Status page ───────────────────────────────────────────────────────────

    def _pg_status(self):
        c = Colors
        pg = QWidget(); pg.setStyleSheet(f"background: {c.BG_BASE};")
        lay = QVBoxLayout(pg); lay.setContentsMargins(20, 18, 20, 18); lay.setSpacing(12)

        card = QFrame(); card.setObjectName("Card")
        cl = QVBoxLayout(card); cl.setContentsMargins(18, 16, 18, 16); cl.setSpacing(10)

        top_row = QHBoxLayout(); top_row.setSpacing(14)
        self._dot = StatusDot(); top_row.addWidget(self._dot)
        status_col = QVBoxLayout(); status_col.setSpacing(2)
        self._big_status = QLabel("Disconnected")
        self._big_status.setStyleSheet(
            f"color: {c.TXT_SEC}; font-size: 14px; font-weight: 700; background: transparent;"
        )
        self._profile_badge = QLabel("No profile selected")
        self._profile_badge.setStyleSheet(f"color: {c.TXT_MUT}; font-size: 11px; background: transparent;")
        status_col.addWidget(self._big_status); status_col.addWidget(self._profile_badge)
        top_row.addLayout(status_col, 1); cl.addLayout(top_row)
        cl.addWidget(h_rule())

        prow = QHBoxLayout(); prow.setSpacing(8)
        pl = QLabel("Profile"); pl.setStyleSheet(f"color: {c.TXT_MUT}; font-size: 11px; min-width: 46px;")
        self._combo = QComboBox()
        self._combo.currentTextChanged.connect(self._on_combo)
        self._combo.setItemDelegate(AccentHoverDelegate(self._combo))
        prow.addWidget(pl); prow.addWidget(self._combo, 1); cl.addLayout(prow)

        conn_row = QHBoxLayout(); conn_row.setContentsMargins(0, 2, 0, 2)
        self._conn_btn = QPushButton("Connect"); self._conn_btn.setObjectName("ConnectBtn")
        self._conn_btn.setEnabled(False); self._conn_btn.setFixedSize(160, 34)
        self._conn_btn.clicked.connect(self._toggle)
        self._conn_btn_style_connect    = self._make_connect_style()
        self._conn_btn_style_disconnect = self._make_disconnect_style()
        self._conn_btn.setStyleSheet(self._conn_btn_style_connect)
        conn_row.addStretch(); conn_row.addWidget(self._conn_btn); conn_row.addStretch()
        cl.addLayout(conn_row); lay.addWidget(card)

        stats_row = QHBoxLayout(); stats_row.setSpacing(8)
        self._dur_lbl = self._stat_box(stats_row, "Duration",   c.TXT_PRI)
        self._up_lbl  = self._stat_box(stats_row, "Uploaded",   c.BLUE_UP)
        self._dn_lbl  = self._stat_box(stats_row, "Downloaded", c.ORANGE)
        lay.addLayout(stats_row)

        chart_card = QFrame(); chart_card.setObjectName("Card")
        chart_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        ccl = QVBoxLayout(chart_card); ccl.setContentsMargins(14, 10, 14, 10); ccl.setSpacing(6)
        chart_hdr = QHBoxLayout()
        ct = QLabel("Live Traffic")
        ct.setStyleSheet(f"color: {c.TXT_MUT}; font-size: 9px; font-weight: 600; letter-spacing: 1px;")
        chart_hdr.addWidget(ct); chart_hdr.addStretch()
        self._up_rate = QLabel("↑ 0.0 KB/s")
        self._up_rate.setStyleSheet(f"color: {c.BLUE_UP}; font-size: 10px; font-weight: 700;")
        self._dn_rate = QLabel("↓ 0.0 KB/s")
        self._dn_rate.setStyleSheet(f"color: {c.ORANGE}; font-size: 10px; font-weight: 700;")
        chart_hdr.addWidget(self._up_rate); chart_hdr.addSpacing(12); chart_hdr.addWidget(self._dn_rate)
        ccl.addLayout(chart_hdr)
        self._chart = TinyChart()
        self._chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._chart.setMinimumHeight(60); ccl.addWidget(self._chart, 1)
        lay.addWidget(chart_card, 1)
        self._refresh_combo()
        return pg

    def _stat_box(self, parent_layout, label, color):
        c = Colors
        box = QFrame(); box.setObjectName("Card")
        box.setStyleSheet(
            f"QFrame#Card {{ background: {c.BG_CARD}; border: 1px solid {c.BORDER}; border-radius: 8px; }}"
        )
        bl = QVBoxLayout(box); bl.setContentsMargins(12, 10, 12, 10); bl.setSpacing(2)
        lbl = QLabel(label.upper())
        lbl.setStyleSheet(
            f"color: {c.TXT_MUT}; font-size: 9px; letter-spacing: 0.8px; font-weight: 600; background: transparent;"
        )
        val = QLabel("—")
        val.setStyleSheet(f"color: {color}; font-size: 15px; font-weight: 700; background: transparent;")
        bl.addWidget(lbl); bl.addWidget(val); parent_layout.addWidget(box, 1)
        return val

    # ── Profiles page ─────────────────────────────────────────────────────────

    def _pg_profiles(self):
        c = Colors
        pg = QWidget(); pg.setStyleSheet(f"background: {c.BG_BASE};")
        lay = QVBoxLayout(pg); lay.setContentsMargins(20, 18, 20, 18); lay.setSpacing(10)
        hdr = QHBoxLayout()
        t = QLabel("Profiles"); t.setStyleSheet(f"color: {c.TXT_PRI}; font-size: 14px; font-weight: 700;")
        hdr.addWidget(t); hdr.addStretch()
        ab = QPushButton("＋  Add"); ab.setObjectName("AddBtn"); ab.clicked.connect(self._add_profile)
        hdr.addWidget(ab); lay.addLayout(hdr)
        self._profile_list = QListWidget(); self._profile_list.itemClicked.connect(self._on_list_click)
        lay.addWidget(self._profile_list, 1)
        btn_row = QHBoxLayout(); btn_row.setSpacing(8)
        self._edit_btn = QPushButton("✎  Edit"); self._edit_btn.setObjectName("SmBtn")
        self._edit_btn.setEnabled(False); self._edit_btn.clicked.connect(self._edit_profile)
        self._del_btn = QPushButton("✕  Delete"); self._del_btn.setObjectName("SmBtn")
        self._del_btn.setProperty("danger", "true"); self._del_btn.setEnabled(False)
        self._del_btn.clicked.connect(self._delete_profile)
        btn_row.addStretch(); btn_row.addWidget(self._edit_btn); btn_row.addWidget(self._del_btn)
        lay.addLayout(btn_row); self._refresh_list()
        return pg

    # ── Stats page ────────────────────────────────────────────────────────────

    def _pg_stats(self):
        c = Colors
        pg = QWidget(); pg.setStyleSheet(f"background: {c.BG_BASE};")
        lay = QVBoxLayout(pg); lay.setContentsMargins(20, 18, 20, 18); lay.setSpacing(12)
        t = QLabel("Statistics"); t.setStyleSheet(f"color: {c.TXT_PRI}; font-size: 14px; font-weight: 700;")
        lay.addWidget(t)
        grid = QHBoxLayout(); grid.setSpacing(8)
        self._st_sess  = self._stat_box(grid, "Sessions",    c.TXT_PRI)
        self._st_time  = self._stat_box(grid, "Total Time",  c.BLUE_UP)
        self._st_pk_up = self._stat_box(grid, "Peak Upload", c.BLUE_UP)
        self._st_pk_dn = self._stat_box(grid, "Peak Down",   c.ORANGE)
        lay.addLayout(grid)
        hist_card = QFrame(); hist_card.setObjectName("Card")
        hcl = QVBoxLayout(hist_card); hcl.setContentsMargins(14, 12, 14, 12); hcl.setSpacing(8)
        ht = QLabel("Session History")
        ht.setStyleSheet(f"color: {c.TXT_MUT}; font-size: 9px; font-weight: 600; letter-spacing: 1px;")
        hcl.addWidget(ht)
        self._hist_box = QTextEdit(); self._hist_box.setReadOnly(True)
        self._hist_box.setMinimumHeight(160); hcl.addWidget(self._hist_box)
        lay.addWidget(hist_card, 1); self._refresh_stats()
        return pg

    # ── Log page ──────────────────────────────────────────────────────────────

    def _pg_log(self):
        c = Colors
        pg = QWidget(); pg.setStyleSheet(f"background: {c.BG_BASE};")
        lay = QVBoxLayout(pg); lay.setContentsMargins(20, 18, 20, 18); lay.setSpacing(10)
        hdr = QHBoxLayout()
        t = QLabel("Log"); t.setStyleSheet(f"color: {c.TXT_PRI}; font-size: 14px; font-weight: 700;")
        hdr.addWidget(t); hdr.addStretch()
        clr = QPushButton("Clear"); clr.setObjectName("SmBtn"); clr.setFixedWidth(60)
        clr.clicked.connect(lambda: self._log_box.clear())
        hdr.addWidget(clr); lay.addLayout(hdr)
        self._log_box = QTextEdit(); self._log_box.setReadOnly(True)
        lay.addWidget(self._log_box, 1)
        return pg

    # ── Interactions ──────────────────────────────────────────────────────────

    def _refresh_combo(self):
        self._combo.blockSignals(True); self._combo.clear()
        self._combo.addItem("— select profile —")
        for n in self.cfgman.configs: self._combo.addItem(n)
        if self.cur_cfg:
            i = self._combo.findText(self.cur_cfg.name)
            if i >= 0: self._combo.setCurrentIndex(i)
        self._combo.blockSignals(False)

    def _refresh_list(self):
        self._profile_list.clear()
        for n, cfg in self.cfgman.configs.items():
            item = QListWidgetItem()
            connected = self.connected and self.cur_cfg and self.cur_cfg.name == n
            item.setText(f"{'● ' if connected else '  '}{n}  —  {os.path.basename(cfg.config_path)}")
            self._profile_list.addItem(item)
        self._edit_btn.setEnabled(False); self._del_btn.setEnabled(False)

    def _on_combo(self, text):
        if text and text != "— select profile —":
            cfg = self.cfgman.get(text)
            if cfg:
                self.cur_cfg = cfg
                self._profile_badge.setText(os.path.basename(cfg.config_path))
                if not self.connected: self._conn_btn.setEnabled(True)
        else:
            if not self.connected:
                self.cur_cfg = None
                self._profile_badge.setText("No profile selected")
                self._conn_btn.setEnabled(False)

    def _on_list_click(self, item):
        self._edit_btn.setEnabled(True); self._del_btn.setEnabled(True)

    def _toggle(self):
        if self.connected: self._disconnect()
        else: self._connect()

    def _connect(self):
        if not self.cur_cfg: return
        if not os.path.exists(self.cur_cfg.config_path):
            QMessageBox.critical(self, "Error", f"File not found:\n{self.cur_cfg.config_path}"); return
        self.vpn_thread = OpenVPNThread(
            self.cur_cfg.config_path, self.cur_cfg.username or None, self.cur_cfg.password or None,
        )
        self.vpn_thread.output_received.connect(self._log)
        self.vpn_thread.connection_established.connect(self._on_connected)
        self.vpn_thread.connection_failed.connect(self._on_failed)
        self.vpn_thread.finished_cleanup.connect(self._on_thread_done)
        self.vpn_thread.start()
        self._conn_btn.setEnabled(False); self._dot.set_state("spinning")
        self._big_status.setText("Connecting…")
        self._big_status.setStyleSheet(
            f"color: {Colors.ORANGE}; font-size: 14px; font-weight: 700; background: transparent;"
        )
        self._reset_live(); self.start_time = None; self.sess_final = True
        self._log(f"=== Connecting to '{self.cur_cfg.name}' ===")

    def _disconnect(self):
        if self.vpn_thread and self.vpn_thread.isRunning():
            self.vpn_thread.stop(); self.vpn_thread.wait(15000)
        try:
            r = subprocess.run(['pgrep', 'openvpn'], capture_output=True)
            if r.returncode == 0:
                kill = ['pkill', '-KILL', 'openvpn']
                if os.getuid() == 0: subprocess.run(kill, capture_output=True, timeout=10)
                else: run_privileged(kill, capture_output=True, timeout=10)
        except: pass
        self._finalize("Manual disconnect"); self.connected = False
        self._apply_disconnected(); self._reset_live()
        self.start_time = self.vpn_iface = None; self._refresh_list()

    def _apply_disconnected(self):
        self._dot.set_state("off")
        self._big_status.setText("Disconnected")
        self._big_status.setStyleSheet(
            f"color: {Colors.TXT_SEC}; font-size: 14px; font-weight: 700; background: transparent;"
        )
        self._conn_btn.setStyleSheet(self._conn_btn_style_connect)
        self._conn_btn.setText("Connect"); self._conn_btn.setEnabled(self.cur_cfg is not None)

    def _on_connected(self, iface):
        self.connected = True; self.start_time = datetime.datetime.now()
        self.vpn_iface = iface or self._detect_iface(); self.sess_final = False
        self.last_sent = self.last_recv = None; self.ss_sent = self.ss_recv = None
        self.sent_pts = []; self.recv_pts = []; self._chart.clear()
        self._dot.set_state("on")
        self._big_status.setText("Connected")
        self._big_status.setStyleSheet(
            f"color: {Colors.ORANGE}; font-size: 14px; font-weight: 700; background: transparent;"
        )
        self._conn_btn.setStyleSheet(self._conn_btn_style_disconnect)
        self._conn_btn.setText("Disconnect"); self._conn_btn.setEnabled(True)
        self._log(f"✓ Connected!  iface={self.vpn_iface or 'unknown'}"); self._refresh_list()

    def _on_failed(self, err):
        self._finalize("Failed"); self.connected = False
        self._apply_disconnected(); self._reset_live()
        self.start_time = self.vpn_iface = None
        self._log(f"✗ FAILED: {err}"); QMessageBox.critical(self, "Connection Failed", err)

    def _on_thread_done(self):
        if not self.connected:
            self._apply_disconnected(); self._reset_live()
            self.start_time = self.vpn_iface = None

    def _add_profile(self):
        d = AddProfileDialog(self)
        if d.exec() == QDialog.DialogCode.Accepted:
            data = d.data()
            if not data['name'] or not data['config_path']:
                QMessageBox.warning(self, "Error", "Name and file required."); return
            if not os.path.exists(data['config_path']):
                QMessageBox.critical(self, "Error", f"File not found:\n{data['config_path']}"); return
            self.cfgman.add(VPNConfig(**data)); self._refresh_list(); self._refresh_combo()
            self._log(f"Profile '{data['name']}' added.")

    def _edit_profile(self):
        item = self._profile_list.currentItem()
        if not item: return
        name = item.text().strip().lstrip("● ").split("  —  ")[0].strip()
        cfg = self.cfgman.get(name)
        if not cfg: return
        d = AddProfileDialog(self, cfg)
        if d.exec() == QDialog.DialogCode.Accepted:
            data = d.data()
            if not data['name'] or not data['config_path']:
                QMessageBox.warning(self, "Error", "Name and file required."); return
            if not os.path.exists(data['config_path']):
                QMessageBox.critical(self, "Error", f"File not found:\n{data['config_path']}"); return
            if data['name'] != name: self.cfgman.remove(name)
            self.cfgman.add(VPNConfig(**data)); self._refresh_list(); self._refresh_combo()

    def _delete_profile(self):
        item = self._profile_list.currentItem()
        if not item: return
        name = item.text().strip().lstrip("● ").split("  —  ")[0].strip()
        r = QMessageBox.question(self, "Delete", f"Delete profile '{name}'?",
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if r == QMessageBox.StandardButton.Yes:
            self.cfgman.remove(name); self._refresh_list(); self._refresh_combo()
            self._log(f"Profile '{name}' deleted.")

    # ── Timer ─────────────────────────────────────────────────────────────────

    def _tick(self):
        if not self.connected: return
        try:
            r = subprocess.run(['pgrep', 'openvpn'], capture_output=True)
            if r.returncode != 0:
                self._log("⚠ Process lost."); self._finalize("Process lost")
                self.connected = False; self._apply_disconnected(); self._reset_live()
                self.start_time = self.vpn_iface = None; self._refresh_list(); return
        except: pass

        if self.start_time:
            secs = int((datetime.datetime.now() - self.start_time).total_seconds())
            self._dur_lbl.setText(fmt_dur(secs))

        if self.vpn_iface:
            sent, recv = self._iface_bytes(self.vpn_iface)
            if sent is not None:
                self._up_lbl.setText(fmt_bytes(sent)); self._dn_lbl.setText(fmt_bytes(recv))
                if self.ss_sent is None: self.ss_sent = sent; self.ss_recv = recv
                up_k = dn_k = 0.0
                if self.last_sent is not None:
                    up_k = max(0.0, (sent - self.last_sent) / 1024.0)
                    dn_k = max(0.0, (recv - self.last_recv) / 1024.0)
                self.last_sent = sent; self.last_recv = recv
                self._up_rate.setText(f"↑ {up_k:.1f} KB/s"); self._dn_rate.setText(f"↓ {dn_k:.1f} KB/s")
                self._chart.push(up_k, dn_k)
                self.sent_pts.append(up_k); self.recv_pts.append(dn_k)
                if len(self.sent_pts) > 120: self.sent_pts.pop(0)
                if len(self.recv_pts) > 120: self.recv_pts.pop(0)

    def _reset_live(self):
        self._dur_lbl.setText("—"); self._up_lbl.setText("—"); self._dn_lbl.setText("—")
        self._up_rate.setText("↑ 0.0 KB/s"); self._dn_rate.setText("↓ 0.0 KB/s")
        self._chart.clear(); self.last_sent = self.last_recv = None
        self.ss_sent = self.ss_recv = None; self.sent_pts = []; self.recv_pts = []

    def _finalize(self, reason="Disconnected"):
        if self.sess_final or not self.start_time: return
        dur = int((datetime.datetime.now() - self.start_time).total_seconds())
        self.total_secs += max(dur, 0)
        pk_up = max(self.sent_pts) if self.sent_pts else 0.0
        pk_dn = max(self.recv_pts) if self.recv_pts else 0.0
        self.sessions.insert(0, {
            "started": self.start_time.strftime("%Y-%m-%d %H:%M"), "duration": dur,
            "upload":   max(0, (self.last_sent or 0) - (self.ss_sent or 0)),
            "download": max(0, (self.last_recv or 0) - (self.ss_recv or 0)),
            "pk_up": pk_up, "pk_dn": pk_dn, "reason": reason,
        })
        self.sessions = self.sessions[:20]; self.sess_final = True; self._refresh_stats()

    def _refresh_stats(self):
        n = len(self.sessions)
        self._st_sess.setText(str(n))
        h, r = divmod(self.total_secs, 3600); m, _ = divmod(r, 60)
        self._st_time.setText(f"{h:02d}h {m:02d}m")
        if n:
            self._st_pk_up.setText(f"{max(e['pk_up'] for e in self.sessions):.1f} KB/s")
            self._st_pk_dn.setText(f"{max(e['pk_dn'] for e in self.sessions):.1f} KB/s")
            lines = []
            for i, s in enumerate(self.sessions, 1):
                h2, r2 = divmod(s['duration'], 3600); m2, s2 = divmod(r2, 60)
                lines.append(
                    f"[{i:02d}] {s['started']}  {h2:02d}:{m2:02d}:{s2:02d}"
                    f"  ↑{fmt_bytes(s['upload'])}  ↓{fmt_bytes(s['download'])}"
                    f"  peak ↑{s['pk_up']:.1f} ↓{s['pk_dn']:.1f}  {s['reason']}"
                )
            self._hist_box.setPlainText("\n".join(lines))
        else:
            self._st_pk_up.setText("—"); self._st_pk_dn.setText("—")
            self._hist_box.setPlainText("No sessions yet.")

    # ── Network helpers ───────────────────────────────────────────────────────

    def _detect_iface(self):
        try:
            r = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True, check=True)
            m = re.search(r'(tun\d+|tap\d+):', r.stdout)
            if m: return m.group(1)
        except: pass
        return None

    def _iface_bytes(self, iface):
        try:
            r = subprocess.run(['ip', '-s', 'link', 'show', iface],
                                capture_output=True, text=True, check=True)
            rx = re.search(r'RX:\s+bytes\s+packets.*\n\s*(\d+)', r.stdout)
            tx = re.search(r'TX:\s+bytes\s+packets.*\n\s*(\d+)', r.stdout)
            if rx and tx: return int(tx.group(1)), int(rx.group(1))
        except: pass
        try:
            r = subprocess.run(['ifconfig', iface], capture_output=True, text=True, check=True)
            rx = re.search(r'RX bytes:(\d+)|RX packets \d+\s+bytes (\d+)', r.stdout)
            tx = re.search(r'TX bytes:(\d+)|TX packets \d+\s+bytes (\d+)', r.stdout)
            if rx and tx:
                return int(tx.group(1) or tx.group(2)), int(rx.group(1) or rx.group(2))
        except: pass
        return None, None

    def _log(self, msg):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self._log_box.append(f"[{ts}] {msg}")
        self._log_box.verticalScrollBar().setValue(self._log_box.verticalScrollBar().maximum())

    def closeEvent(self, e):
        if self.connected:
            r = QMessageBox.question(self, "Exit", "Disconnect and exit?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if r != QMessageBox.StandardButton.Yes:
                e.ignore(); return
            try:
                args = ['pkill', '-TERM', 'openvpn']
                kw = dict(stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                if os.getuid() == 0:              subprocess.Popen(args, **kw)
                elif shutil.which('pkexec'):      subprocess.Popen(['pkexec'] + args, **kw)
                elif shutil.which('sudo'):        subprocess.Popen(['sudo']   + args, **kw)
            except: pass
        self._theme.stop()
        e.accept()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    try:
        subprocess.run(['openvpn', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        QMessageBox.critical(None, "OpenVPN Not Found",
                             "Install OpenVPN:\n  sudo apt install openvpn")
        sys.exit(1)

    if os.getuid() != 0:
        QMessageBox.warning(None, "Privileges",
                            "Not running as root.\nAuthentication may be required.")

    w = OpenVPNConnectGUI(); w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()