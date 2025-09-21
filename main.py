import sys
import os
import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, Optional

# Check PyQt6 availability before importing
try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
        QPushButton, QLabel, QListWidget, QTextEdit, QFileDialog,
        QMessageBox, QProgressBar, QGroupBox, QLineEdit,
        QTabWidget, QListWidgetItem, QComboBox, QFormLayout,
        QDialog, QDialogButtonBox
    )
    from PyQt6.QtCore import QTimer, QThread, pyqtSignal, Qt
    from PyQt6.QtGui import QFont, QIcon
except ImportError as e:
    print(f"ERRO: PyQt6 não está instalado ou não pode ser importado: {e}")
    print("\nPossíveis soluções:")
    print("1. Instalar via apt: sudo apt install python3-pyqt6")
    print("2. Instalar via pip: pip3 install PyQt6")
    print("3. Verificar se o pacote foi instalado corretamente")
    sys.exit(1)

import datetime
import re # For regular expressions to parse network interface output

# Import application configuration
try:
    from config import APP_NAME, APP_VERSION, ORGANIZATION_NAME, get_app_info, get_developer_string, get_version_string
except ImportError as e:
    print(f"ERRO: Não foi possível importar configuração: {e}")
    print("Verifique se o arquivo config.py está presente e no PYTHONPATH")
    sys.exit(1)

def run_privileged_command(cmd, **kwargs):
    """Run a privileged command. 
    
    If already running as root, execute directly.
    Otherwise, use pkexec/sudo for privilege escalation.
    
    cmd: list without sudo/pkexec prefix (e.g. ['pkill','-TERM','openvpn'])
    Returns CompletedProcess
    """
    # If we're already running as root, execute directly
    if os.getuid() == 0:
        return subprocess.run(cmd, **kwargs)
    
    # Otherwise, use privilege escalation
    full_cmd = None
    if shutil.which('pkexec'):
        full_cmd = ['pkexec'] + cmd
    else:
        full_cmd = ['sudo'] + cmd
    return subprocess.run(full_cmd, **kwargs)


class OpenVPNThread(QThread):
    """Thread to run OpenVPN without blocking the UI"""
    status_changed = pyqtSignal(str)
    output_received = pyqtSignal(str)
    # Modified signal to also pass the VPN interface name
    connection_established = pyqtSignal(str)
    connection_failed = pyqtSignal(str)
    finished_cleanup = pyqtSignal()

    def __init__(self, config_path: str, username: str = None, password: str = None):
        super().__init__()
        self.config_path = config_path
        self.username = username
        self.password = password
        self.process = None
        self.should_stop = False
        self.auth_file = None # Store auth_file path at class level
        self.vpn_interface_name = None # To store the name of the VPN interface

    def run(self):
        try:
            # If already running as root, use openvpn directly
            # Otherwise, the launcher should have elevated privileges already
            if os.getuid() == 0:
                cmd = ['openvpn']
            else:
                # This should not happen if launched properly, but keep as fallback
                if shutil.which('pkexec'):
                    cmd = ['pkexec', 'openvpn']
                else:
                    cmd = ['sudo', 'openvpn']
            
            cmd += [
                '--config', self.config_path,
                '--verb', '3',
                '--script-security', '2',
                '--up', '/etc/openvpn/update-resolv-conf',
                '--down', '/etc/openvpn/update-resolv-conf'
            ]
            
            if self.username and self.password:
                import tempfile
                # Store the path in the instance variable
                auth_fd, self.auth_file = tempfile.mkstemp(suffix='_openvpn_auth', text=True)
                try:
                    with os.fdopen(auth_fd, 'w') as f:
                        f.write(f"{self.username}\n{self.password}\n")
                    cmd.extend(['--auth-user-pass', self.auth_file])
                    os.chmod(self.auth_file, 0o600)
                except Exception as e:
                    os.close(auth_fd) # Ensure fd is closed on error before raising
                    # Remove potentially created file on error within this block
                    if self.auth_file and os.path.exists(self.auth_file):
                         try:
                             os.unlink(self.auth_file)
                         except:
                             pass
                    self.auth_file = None # Reset it
                    raise e # Re-raise the exception

            self.status_changed.emit("Connecting...")
            self.output_received.emit(f"Executing command: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                preexec_fn=os.setsid
            )

            connected = False
            failed = False
            for line in iter(self.process.stdout.readline, ''):
                if self.should_stop:
                    break
                line = line.strip()
                if line:
                    self.output_received.emit(line)

                if not connected and not failed:
                    # Detect VPN interface name. OpenVPN usually logs this.
                    # Example: "TUN/TAP device tun0 opened" or "ifconfig_ipv6_remote: tun0"
                    match_tun = re.search(r'TUN/TAP device (\w+) opened', line)
                    match_ifconfig = re.search(r'ifconfig_ipv6_remote: (\w+)', line)
                    if match_tun:
                        self.vpn_interface_name = match_tun.group(1)
                    elif match_ifconfig:
                        self.vpn_interface_name = match_ifconfig.group(1)

                    if any(phrase in line for phrase in [
                        "Initialization Sequence Completed",
                        "Sequence Completed",
                        "VPN tunnel is ready"
                    ]):
                        self.status_changed.emit("Connected")
                        self.connection_established.emit(self.vpn_interface_name if self.vpn_interface_name else "")
                        connected = True
                    elif any(phrase in line for phrase in [
                        "AUTH_FAILED",
                        "Authentication failed"
                    ]):
                        self.status_changed.emit("Authentication Failed")
                        self.connection_failed.emit("Invalid credentials")
                        failed = True
                    elif any(phrase in line for phrase in [
                        "TLS Error",
                        "TLS handshake failed",
                        "Certificate verification failed"
                    ]):
                        self.status_changed.emit("TLS/Certificate Error")
                        self.connection_failed.emit("Certificate or TLS error")
                        failed = True
                    elif any(phrase in line for phrase in [
                        "Cannot resolve host address",
                        "Name resolution failure",
                        "RESOLVE:"
                    ]):
                        self.status_changed.emit("DNS Error")
                        self.connection_failed.emit("Could not resolve server")
                        failed = True
                    elif any(phrase in line for phrase in [
                        "Connection refused",
                        "Connection timed out",
                        "Network is unreachable"
                    ]):
                        self.status_changed.emit("Network Error")
                        self.connection_failed.emit("Network connection failed")
                        failed = True
                    elif "FATAL" in line:
                        self.status_changed.emit("Fatal Error")
                        self.connection_failed.emit(f"Fatal error: {line}")
                        failed = True

            return_code = self.process.wait()

            if not connected and not failed and not self.should_stop:
                 error_msg = f"Connection failed - process terminated unexpectedly (code: {return_code})"
                 if return_code != 0:
                     error_msg += f". Exit code: {return_code}"
                 self.connection_failed.emit(error_msg)

        except PermissionError:
            self.connection_failed.emit("Permission error - Run as root/sudo")
        except FileNotFoundError:
            self.connection_failed.emit("OpenVPN not found - Install the openvpn package")
        except Exception as e:
            self.connection_failed.emit(f"Error starting OpenVPN: {str(e)}")
        finally:
            self.cleanup()
            self.finished_cleanup.emit()


    def cleanup(self):
         """Ensures cleanup of temporary files and attempts to run down script if needed."""
         if self.auth_file and os.path.exists(self.auth_file):
             try:
                 os.unlink(self.auth_file)
                 self.output_received.emit(f"Temporary authentication file removed.")
             except Exception as e:
                 self.output_received.emit(f"Error removing temporary authentication file ({self.auth_file}): {e}")
             finally:
                 self.auth_file = None

    def stop(self):
        self.should_stop = True
        
        # First, try to kill OpenVPN processes directly
        try:
            self.output_received.emit("Attempting to stop OpenVPN processes...")
            
            # If running as root, use direct commands
            if os.getuid() == 0:
                subprocess.run(['pkill', '-TERM', 'openvpn'], capture_output=True, timeout=10)
                self.output_received.emit("Sent SIGTERM to OpenVPN processes.")
            else:
                # Use privilege escalation (should not be needed if launched properly)
                run_privileged_command(['pkill', '-TERM', 'openvpn'], capture_output=True, timeout=10)
                self.output_received.emit("Sent SIGTERM to OpenVPN processes via privilege escalation.")
            
            # Wait a bit for graceful termination
            import time
            time.sleep(2)
            
            # Check if any openvpn processes are still running
            result = subprocess.run(['pgrep', 'openvpn'], capture_output=True)
            if result.returncode == 0:
                # Still running, force kill
                self.output_received.emit("OpenVPN still running, forcing termination...")
                if os.getuid() == 0:
                    subprocess.run(['pkill', '-KILL', 'openvpn'], capture_output=True, timeout=10)
                    self.output_received.emit("Sent SIGKILL to OpenVPN processes.")
                else:
                    run_privileged_command(['pkill', '-KILL', 'openvpn'], capture_output=True, timeout=10)
                    self.output_received.emit("Sent SIGKILL to OpenVPN processes via privilege escalation.")
            else:
                self.output_received.emit("OpenVPN processes terminated successfully.")
                
        except subprocess.TimeoutExpired:
            self.output_received.emit("Timeout trying to kill OpenVPN.")
        except Exception as e:
            self.output_received.emit(f"Error killing OpenVPN: {e}")
        
        # Also try to stop our direct process if it exists
        if self.process and self.process.poll() is None:
            try:
                self.output_received.emit("Stopping local OpenVPN process...")
                os.killpg(os.getpgid(self.process.pid), subprocess.signal.SIGTERM)

                try:
                    self.process.wait(timeout=5)
                    self.output_received.emit("Local OpenVPN process terminated gracefully.")
                except subprocess.TimeoutExpired:
                    self.output_received.emit("Timeout waiting for local process, forcing SIGKILL...")
                    os.killpg(os.getpgid(self.process.pid), subprocess.signal.SIGKILL)
                    self.process.wait()
                    self.output_received.emit("Local OpenVPN process forced to terminate.")

            except ProcessLookupError:
                self.output_received.emit("Local OpenVPN process already terminated.")
            except Exception as e:
                self.output_received.emit(f"Error stopping local OpenVPN process: {e}")
                try:
                   if self.process.poll() is None:
                       os.killpg(os.getpgid(self.process.pid), subprocess.signal.SIGKILL)
                       self.process.wait()
                       self.output_received.emit("Local OpenVPN process forced to terminate after error.")
                except:
                   pass
            finally:
                self.process = None
        else:
            self.output_received.emit("No local OpenVPN process to stop.")

        self.cleanup()


class VPNConfig:
    """Represents a VPN configuration with user details"""
    def __init__(self, name: str, config_path: str, username: str = "", password: str = ""):
        self.name = name
        self.config_path = config_path
        self.username = username
        self.password = password

class ConfigManager:
    """Manages VPN configurations"""
    def __init__(self):
        self.config_dir = Path.home() / '.openvpn_gui'
        self.config_dir.mkdir(exist_ok=True)
        self.configs_file = self.config_dir / 'configs.json'
        self.configs = self.load_configs()

    def load_configs(self) -> Dict[str, VPNConfig]:
        if self.configs_file.exists():
            try:
                with open(self.configs_file, 'r') as f:
                    data = json.load(f)
                    return {k: VPNConfig(**v) for k, v in data.items()}
            except:
                return {}
        return {}

    def save_configs(self):
        data = {k: v.__dict__ for k, v in self.configs.items()}
        with open(self.configs_file, 'w') as f:
            json.dump(data, f, indent=2)

    def add_config(self, config: VPNConfig):
        self.configs[config.name] = config
        self.save_configs()

    def remove_config(self, name: str):
        if name in self.configs:
            del self.configs[name]
            self.save_configs()

    def get_config(self, name: str) -> Optional[VPNConfig]:
        return self.configs.get(name)

class AddConfigDialog(QDialog):
    """Dialog for adding/editing a configuration"""
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Add Configuration" if not config else "Edit Configuration")
        self.setModal(True)
        self.resize(350, 250)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.name_input = QLineEdit()
        form_layout.addRow("Name:", self.name_input)
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_file)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.browse_btn)
        form_layout.addRow(".ovpn File:", path_layout)
        self.username_input = QLineEdit()
        form_layout.addRow("Username:", self.username_input)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.password_input)
        layout.addLayout(form_layout)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        if self.config:
            self.name_input.setText(self.config.name)
            self.path_input.setText(self.config.config_path)
            self.username_input.setText(self.config.username)
            self.password_input.setText(self.config.password)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select OpenVPN Configuration File",
            "",
            "OpenVPN Config (*.ovpn);;All Files (*)"
        )
        if file_path:
            self.path_input.setText(file_path)
            if not self.name_input.text():
                self.name_input.setText(Path(file_path).stem)

    def get_data(self):
        return {
            'name': self.name_input.text().strip(),
            'config_path': self.path_input.text().strip(),
            'username': self.username_input.text().strip(),
            'password': self.password_input.text().strip()
        }

class OpenVPNGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.vpn_thread = None
        self.is_connected = False
        self.current_config = None
        self.connection_start_time = None
        self.vpn_interface_name = None # To store the name of the active VPN interface
        self.init_ui()
        self.setup_timer()

    def init_ui(self):
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QIcon("resources/vpn.png"))
        self.setFixedSize(400, 600)  # Increased size for new labels
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.connection_tab = self.create_connection_tab()
        self.tabs.addTab(self.connection_tab, "Connection")

        self.management_tab = self.create_management_tab()
        self.tabs.addTab(self.management_tab, "Management")

        # Developer and Version Information
        self.developer_label = QLabel(get_developer_string())
        self.developer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.developer_label.setFont(QFont("Arial", 8))
        main_layout.addWidget(self.developer_label)

        self.version_label = QLabel(get_version_string())
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version_label.setFont(QFont("Arial", 8))
        main_layout.addWidget(self.version_label)

        self.load_config_list()

    def create_connection_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        selection_group = QGroupBox("Select Configuration")
        selection_layout = QHBoxLayout(selection_group)
        self.config_combo = QComboBox()
        self.config_combo.currentTextChanged.connect(self.on_config_combo_changed)
        selection_layout.addWidget(QLabel("Configuration:"))
        selection_layout.addWidget(self.config_combo, 1)
        layout.addWidget(selection_group)

        status_group = QGroupBox("Connection Status")
        status_layout = QVBoxLayout(status_group)

        self.status_label = QLabel("Disconnected")
        self.status_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("QLabel { color: red; padding: 10px; }")
        status_layout.addWidget(self.status_label)

        # New labels for connection time and data usage
        self.connected_time_label = QLabel("Connected Time: 00h 00m 00s")
        self.data_sent_label = QLabel("Data Sent: 0 KB")
        self.data_received_label = QLabel("Data Received: 0 KB")

        status_layout.addWidget(self.connected_time_label)
        status_layout.addWidget(self.data_sent_label)
        status_layout.addWidget(self.data_received_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        layout.addWidget(status_group)

        control_layout = QHBoxLayout()
        self.btn_connect = QPushButton("Connect")
        self.btn_connect.clicked.connect(self.connect_vpn)
        self.btn_connect.setEnabled(False)
        control_layout.addWidget(self.btn_connect)
        self.btn_disconnect = QPushButton("Disconnect")
        self.btn_disconnect.clicked.connect(self.disconnect_vpn)
        self.btn_disconnect.setEnabled(False)
        control_layout.addWidget(self.btn_disconnect)
        layout.addLayout(control_layout)

        log_group = QGroupBox("Connection Log")
        log_layout = QVBoxLayout(log_group)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Courier", 8))
        log_layout.addWidget(self.log_output)
        self.btn_clear_log = QPushButton("Clear Log")
        self.btn_clear_log.clicked.connect(self.log_output.clear)
        log_layout.addWidget(self.btn_clear_log)
        layout.addWidget(log_group)
        return widget

    def create_management_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        list_group = QGroupBox("Saved Configurations")
        list_layout = QVBoxLayout(list_group)
        self.config_list = QListWidget()
        self.config_list.itemClicked.connect(self.on_config_selected)
        list_layout.addWidget(self.config_list)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add")
        self.btn_add.clicked.connect(self.add_config)
        btn_layout.addWidget(self.btn_add)
        self.btn_edit = QPushButton("Edit")
        self.btn_edit.clicked.connect(self.edit_config)
        self.btn_edit.setEnabled(False)
        btn_layout.addWidget(self.btn_edit)
        self.btn_remove = QPushButton("Remove")
        self.btn_remove.clicked.connect(self.remove_config)
        self.btn_remove.setEnabled(False)
        btn_layout.addWidget(self.btn_remove)
        list_layout.addLayout(btn_layout)
        layout.addWidget(list_group)

        self.details_group = QGroupBox("Details")
        self.details_group.setEnabled(False)
        details_layout = QFormLayout(self.details_group)
        self.details_name = QLabel()
        details_layout.addRow("Name:", self.details_name)
        self.details_path = QLabel()
        self.details_path.setWordWrap(True)
        self.details_path.setMinimumSize(0, 30)
        details_layout.addRow("File:", self.details_path)
        self.details_username = QLabel()
        details_layout.addRow("Username:", self.details_username)
        layout.addWidget(self.details_group)
        return widget

    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000) # Update every second

    def load_config_list(self):
        self.config_list.clear()
        self.config_combo.clear()
        self.config_combo.addItem("")
        for name in self.config_manager.configs.keys():
            item = QListWidgetItem(name)
            self.config_list.addItem(item)
            self.config_combo.addItem(name)

    def on_config_combo_changed(self, text):
        if text:
            config = self.config_manager.get_config(text)
            if config:
                self.btn_connect.setEnabled(True)
                self.current_config = config
                self.log_output.append(f"Configuration '{text}' selected for connection.")
            else:
                self.btn_connect.setEnabled(False)
                self.current_config = None
        else:
            self.btn_connect.setEnabled(False)
            self.current_config = None

    def add_config(self):
        dialog = AddConfigDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data['name'] or not data['config_path']:
                QMessageBox.warning(self, "Error", "Name and configuration file are required.")
                return
            if not os.path.exists(data['config_path']):
                QMessageBox.critical(self, "Error", f"Configuration file not found:\n{data['config_path']}")
                return
            config = VPNConfig(**data)
            self.config_manager.add_config(config)
            self.load_config_list()
            self.log_output.append(f"Configuration '{data['name']}' added.")

    def edit_config(self):
        current_item = self.config_list.currentItem()
        if current_item:
            name = current_item.text()
            config = self.config_manager.get_config(name)
            if config:
                dialog = AddConfigDialog(self, config)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    data = dialog.get_data()
                    if not data['name'] or not data['config_path']:
                        QMessageBox.warning(self, "Error", "Name and configuration file are required.")
                        return
                    if not os.path.exists(data['config_path']):
                        QMessageBox.critical(self, "Error", f"Configuration file not found:\n{data['config_path']}")
                        return
                    if data['name'] != name:
                        self.config_manager.remove_config(name)
                    config = VPNConfig(**data)
                    self.config_manager.add_config(config)
                    self.load_config_list()
                    self.log_output.append(f"Configuration '{name}' updated.")

    def remove_config(self):
        current_item = self.config_list.currentItem()
        if current_item:
            name = current_item.text()
            reply = QMessageBox.question(
                self, "Confirm Deletion",
                f"Are you sure you want to delete configuration '{name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.config_manager.remove_config(name)
                self.load_config_list()
                self.btn_edit.setEnabled(False)
                self.btn_remove.setEnabled(False)
                self.details_group.setEnabled(False)
                self.log_output.append(f"Configuration '{name}' deleted.")

    def on_config_selected(self, item):
        config_name = item.text()
        config = self.config_manager.get_config(config_name)
        if config:
            self.btn_edit.setEnabled(True)
            self.btn_remove.setEnabled(True)
            self.details_group.setEnabled(True)
            self.details_name.setText(config.name)
            self.details_path.setText(config.config_path)
            self.details_username.setText(config.username if config.username else "None")
            self.log_output.append(f"Configuration '{config_name}' selected.")

    def connect_vpn(self):
        if not self.current_config:
            QMessageBox.warning(self, "Error", "Please select a configuration.")
            return
        config_path = self.current_config.config_path
        if not os.path.exists(config_path):
            QMessageBox.critical(self, "Error", f"Configuration file not found:\n{config_path}")
            return
        try:
            with open(config_path, 'r') as f:
                config_content = f.read()
                if len(config_content.strip()) == 0:
                    QMessageBox.critical(self, "Error", "Configuration file is empty.")
                    return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not read configuration file:\n{str(e)}")
            return
        username = self.current_config.username
        password = self.current_config.password
        if "auth-user-pass" in config_content.lower() and not username:
            reply = QMessageBox.question(
                self, "Credentials Required",
                "This configuration file requires user credentials.\n"
                "Do you want to continue without credentials? (May fail)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.vpn_thread = OpenVPNThread(
            config_path,
            username if username else None,
            password if password else None
        )
        self.vpn_thread.status_changed.connect(self.on_status_changed)
        self.vpn_thread.output_received.connect(self.on_output_received)
        # Connect to the modified signal to get the interface name
        self.vpn_thread.connection_established.connect(self.on_connection_established)
        self.vpn_thread.connection_failed.connect(self.on_connection_failed)
        self.vpn_thread.finished_cleanup.connect(self.on_thread_finished_cleanup)

        self.vpn_thread.start()
        self.btn_connect.setEnabled(False)
        self.btn_disconnect.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.log_output.append("=" * 35)
        self.log_output.append(f"Initiating VPN connection: {self.current_config.name}")
        self.log_output.append(f"File: {config_path}")
        self.log_output.append("=" * 35)

        # Reset connection time and data labels
        self.connected_time_label.setText("Connected Time: 00h 00m 00s")
        self.data_sent_label.setText("Data Sent: 0 KB")
        self.data_received_label.setText("Data Received: 0 KB")
        self.connection_start_time = None
        self.vpn_interface_name = None


    def disconnect_vpn(self):
        if self.vpn_thread and self.vpn_thread.isRunning():
            self.log_output.append("Requesting VPN disconnection...")
            self.vpn_thread.stop()

            finished_cleanly = self.vpn_thread.wait(15000)

            if not finished_cleanly:
                self.log_output.append("Waiting for VPN shutdown timed out.")
                if self.vpn_thread.isRunning():
                    self.vpn_thread.terminate()
                    self.vpn_thread.wait(2000)
                    self.log_output.append("VPN thread forcibly terminated after timeout.")
        else:
            self.log_output.append("No active VPN connection to disconnect.")

        # Force check if OpenVPN processes are still running
        try:
            result = subprocess.run(['pgrep', 'openvpn'], capture_output=True)
            if result.returncode == 0:
                self.log_output.append("OpenVPN processes still detected, forcing termination...")
                try:
                    if os.getuid() == 0:
                        # Running as root, use direct command
                        subprocess.run(['pkill', '-KILL', 'openvpn'], capture_output=True, timeout=10)
                    else:
                        # Use privilege escalation
                        run_privileged_command(['pkill', '-KILL', 'openvpn'], capture_output=True, timeout=10)
                    self.log_output.append("Forcibly terminated remaining OpenVPN processes.")
                except Exception as e:
                    self.log_output.append(f"Error force-killing OpenVPN: {e}")
            else:
                self.log_output.append("All OpenVPN processes successfully terminated.")
        except Exception as e:
            self.log_output.append(f"Error checking OpenVPN processes: {e}")

        self.is_connected = False
        self.btn_connect.setEnabled(True)
        self.btn_disconnect.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Disconnected")
        self.status_label.setStyleSheet("QLabel { color: red; padding: 10px; }")
        self.log_output.append("VPN disconnected (or disconnection attempt completed).")
        self.log_output.append("=" * 35)

        # Reset the specific VPN status labels
        self.connected_time_label.setText("Connected Time: 00h 00m 00s")
        self.data_sent_label.setText("Data Sent: 0 KB")
        self.data_received_label.setText("Data Received: 0 KB")
        self.connection_start_time = None
        self.vpn_interface_name = None


    def on_status_changed(self, status):
        self.status_label.setText(status)
        if status == "Connected":
            self.status_label.setStyleSheet("QLabel { color: green; padding: 10px; }")
        elif "Error" in status or "Failed" in status:
            self.status_label.setStyleSheet("QLabel { color: red; padding: 10px; }")
        else:
            self.status_label.setStyleSheet("QLabel { color: orange; padding: 10px; }")

    def on_output_received(self, output):
        self.log_output.append(output)
        self.log_output.verticalScrollBar().setValue(
            self.log_output.verticalScrollBar().maximum()
        )

    def on_connection_established(self, interface_name: str):
        self.is_connected = True
        self.progress_bar.setVisible(False)
        self.connection_start_time = datetime.datetime.now()
        self.vpn_interface_name = interface_name if interface_name else self.get_vpn_interface_name()
        if not self.vpn_interface_name:
            self.log_output.append("Warning: Could not determine VPN interface name. Data traffic may not be displayed.")

        self.log_output.append("✓ VPN connection successfully established!")
        if self.vpn_interface_name:
            self.log_output.append(f"VPN interface detected: {self.vpn_interface_name}")


    def on_connection_failed(self, error):
        self.progress_bar.setVisible(False)
        self.btn_connect.setEnabled(True)
        self.btn_disconnect.setEnabled(False)
        self.is_connected = False
        self.connection_start_time = None # Reset time on failure
        self.vpn_interface_name = None # Reset interface name on failure

        self.log_output.append(f"✗ CONNECTION FAILED: {error}")
        self.log_output.append("=" * 35)
        suggestions = ""
        if "permission" in error.lower():
            suggestions = "\nSuggestions:\n• Run the program with sudo\n• Check if you have administrative privileges"
        elif "not found" in error.lower():
            suggestions = "\nSuggestions:\n• Install OpenVPN: sudo apt install openvpn\n• Check if it's in your PATH"
        elif "credentials" in error.lower():
            suggestions = "\nSuggestions:\n• Verify username and password\n• Confirm if the server accepts these credentials"
        elif "certificate" in error.lower():
            suggestions = "\nSuggestions:\n• Check if the certificate is valid\n• Confirm if it has not expired"
        elif "network" in error.lower() or "dns" in error.lower():
            suggestions = "\nSuggestions:\n• Check your internet connection\n• Test if you can reach the VPN server\n• Check DNS settings"
        QMessageBox.critical(
            self, "Connection Failed",
            f"Error: {error}{suggestions}"
        )

    def on_thread_finished_cleanup(self):
        self.log_output.append("OpenVPN thread finished.")
        if not self.is_connected:
             self.btn_connect.setEnabled(True)
             self.btn_disconnect.setEnabled(False)
             self.progress_bar.setVisible(False)
             self.status_label.setText("Disconnected")
             self.status_label.setStyleSheet("QLabel { color: red; padding: 10px; }")
             # Ensure data and time labels are reset if thread finished due to failure/disconnection
             self.connected_time_label.setText("Connected Time: 00h 00m 00s")
             self.data_sent_label.setText("Data Sent: 0 KB")
             self.data_received_label.setText("Data Received: 0 KB")
             self.connection_start_time = None
             self.vpn_interface_name = None

    def update_status(self):
        # Check if OpenVPN is actually running
        if self.is_connected:
            # Check if openvpn process is still running
            try:
                result = subprocess.run(['pgrep', 'openvpn'], capture_output=True)
                if result.returncode != 0:
                    # No openvpn processes found, force disconnect state
                    self.log_output.append("⚠ OpenVPN process not found. Connection lost.")
                    self.is_connected = False
                    self.btn_connect.setEnabled(True)
                    self.btn_disconnect.setEnabled(False)
                    self.progress_bar.setVisible(False)
                    self.status_label.setText("Disconnected (Process Lost)")
                    self.status_label.setStyleSheet("QLabel { color: red; padding: 10px; }")
                    self.connected_time_label.setText("Connected Time: 00h 00m 00s")
                    self.data_sent_label.setText("Data Sent: 0 KB")
                    self.data_received_label.setText("Data Received: 0 KB")
                    self.connection_start_time = None
                    self.vpn_interface_name = None
                    return
            except:
                pass  # If pgrep fails, continue with normal status update
        
        if self.is_connected:
            # Update connected time
            if self.connection_start_time:
                elapsed_time = datetime.datetime.now() - self.connection_start_time
                hours, remainder = divmod(int(elapsed_time.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                self.connected_time_label.setText(f"Connected Time: {hours:02d}h {minutes:02d}m {seconds:02d}s")

            # Update data usage
            if self.vpn_interface_name:
                sent, received = self.get_interface_data_usage(self.vpn_interface_name)
                if sent is not None and received is not None:
                    self.data_sent_label.setText(f"Data Sent: {self.format_bytes(sent)}")
                    self.data_received_label.setText(f"Data Received: {self.format_bytes(received)}")
                else:
                    # If data collection fails, it might mean the interface is down or not found
                    self.data_sent_label.setText("Data Sent: N/A")
                    self.data_received_label.setText("Data Received: N/A")
            else:
                self.data_sent_label.setText("Data Sent: N/A")
                self.data_received_label.setText("Data Received: N/A")

            # Check if the thread finished unexpectedly while connected
            if self.vpn_thread is None or not self.vpn_thread.isRunning():
                self.log_output.append("⚠ VPN connection lost or terminated unexpectedly. Restoring state...")
                self.is_connected = False
                self.btn_connect.setEnabled(True)
                self.btn_disconnect.setEnabled(False)
                self.progress_bar.setVisible(False)
                self.status_label.setText("Disconnected (Connection Lost)")
                self.status_label.setStyleSheet("QLabel { color: red; padding: 10px; }")
                self.connected_time_label.setText("Connected Time: 00h 00m 00s")
                self.data_sent_label.setText("Data Sent: 0 KB")
                self.data_received_label.setText("Data Received: 0 KB")
                self.connection_start_time = None
                self.vpn_interface_name = None
                self.log_output.append("=" * 35)
        else:
            # Ensure labels are reset when not connected
            self.connected_time_label.setText("Connected Time: 00h 00m 00s")
            self.data_sent_label.setText("Data Sent: 0 KB")
            self.data_received_label.setText("Data Received: 0 KB")

    def get_vpn_interface_name(self) -> Optional[str]:
        """
        Attempts to find the VPN interface name (e.g., tun0, tap0) by looking for common patterns
        in `ip link show` or `ifconfig` output.
        This is a fallback if the OpenVPN log parsing fails.
        """
        try:
            # Prefer 'ip link show' as it's more modern and often available
            result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True, check=True)
            output = result.stdout
            # Common patterns for VPN interfaces: tunX, tapX
            match = re.search(r'(tun\d+|tap\d+):', output)
            if match:
                return match.group(1)
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                # Fallback to 'ifconfig' if 'ip' is not available or fails
                result = subprocess.run(['ifconfig'], capture_output=True, text=True, check=True)
                output = result.stdout
                match = re.search(r'(tun\d+|tap\d+):', output)
                if match:
                    return match.group(1)
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
        return None

    def get_interface_data_usage(self, interface_name: str) -> tuple[Optional[int], Optional[int]]:
        """
        Retrieves data sent and received for a given network interface.
        Parses output from 'ip -s link show <interface_name>' or 'ifconfig <interface_name>'.
        Returns (bytes_sent, bytes_received) or (None, None) if not found/error.
        """
        sent_bytes = None
        received_bytes = None

        try:
            # Try parsing 'ip -s link show'
            result = subprocess.run(['ip', '-s', 'link', 'show', interface_name],
                                    capture_output=True, text=True, check=True)
            output = result.stdout

            # Example output snippet for 'ip -s link show':
            # RX:  bytes packets errors dropped  missed   mcast
            # 12345678 12345    0       0        0        0
            # TX:  bytes packets errors dropped carrier collsns
            # 87654321 8765     0       0        0        0

            rx_match = re.search(r'RX:\s+bytes\s+packets.*\n\s*(\d+)', output)
            tx_match = re.search(r'TX:\s+bytes\s+packets.*\n\s*(\d+)', output)

            if rx_match:
                received_bytes = int(rx_match.group(1))
            if tx_match:
                sent_bytes = int(tx_match.group(1))

            if sent_bytes is not None and received_bytes is not None:
                return sent_bytes, received_bytes

        except (subprocess.CalledProcessError, FileNotFoundError):
            pass # Continue to try ifconfig

        try:
            # Fallback to 'ifconfig' for older systems or if 'ip' fails
            result = subprocess.run(['ifconfig', interface_name],
                                    capture_output=True, text=True, check=True)
            output = result.stdout

            # Example output snippet for 'ifconfig':
            # RX bytes:12345678 (11.7 MB)  TX bytes:87654321 (83.5 MB)
            # OR (older/different format):
            # RX packets 123456  bytes 12345678 (11.7 MiB)
            # TX packets 876543  bytes 87654321 (83.5 MiB)

            rx_match = re.search(r'RX bytes:(\d+)|RX packets \d+\s+bytes (\d+)', output)
            tx_match = re.search(r'TX bytes:(\d+)|TX packets \d+\s+bytes (\d+)', output)

            if rx_match:
                received_bytes = int(rx_match.group(1) or rx_match.group(2))
            if tx_match:
                sent_bytes = int(tx_match.group(1) or tx_match.group(2))

            if sent_bytes is not None and received_bytes is not None:
                return sent_bytes, received_bytes

        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        return None, None

    def format_bytes(self, bytes_val: int) -> str:
        """Formats byte count into human-readable string (KB, MB, GB)."""
        if bytes_val is None:
            return "N/A"
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024 * 1024:
            return f"{bytes_val / 1024:.2f} KB"
        elif bytes_val < 1024 * 1024 * 1024:
            return f"{bytes_val / (1024 * 1024):.2f} MB"
        else:
            return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"

    def closeEvent(self, event):
        # Debug: log close event
        print("DEBUG: closeEvent called")
        
        if self.is_connected:
            reply = QMessageBox.question(
                self, "VPN Connected",
                "There is an active VPN connection. Do you want to disconnect before exiting?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.disconnect_vpn()
                # Don't close the application, just disconnect
                event.ignore()
                return
            else:
                event.ignore()
                return
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    try:
        subprocess.run(['openvpn', '--version'],
                      capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        QMessageBox.critical(
            None, "OpenVPN Not Found",
            "OpenVPN is not installed or not in your system's PATH.\n"
            "Please install OpenVPN before using this application.\n"
            "Ubuntu/Debian: sudo apt install openvpn\n"
            "CentOS/RHEL: sudo yum install openvpn\n"
            "Arch: sudo pacman -S openvpn"
        )
        sys.exit(1)
    
    # Check if running with elevated privileges
    if os.getuid() == 0:
        print("INFO: Running with elevated privileges - no additional authentication required.")
    else:
        print("WARNING: Not running with elevated privileges - authentication may be required for each operation.")
        QMessageBox.warning(
            None, "Privileges Notice",
            "This application is not running with elevated privileges.\n"
            "You may be prompted for authentication when connecting/disconnecting VPN.\n\n"
            "For better experience, launch using:\n"
            "openvpn-manager-launcher"
        )
    
    window = OpenVPNGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()