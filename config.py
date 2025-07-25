#!/usr/bin/env python3
"""
Configuration file for OpenVPN Manager
Contains application metadata and version information
"""

# Application Information
APP_NAME = "OpenVPN Manager"
APP_VERSION = "0.2.2"
ORGANIZATION_NAME = "Iágson Carlos Lima Silva"
ORGANIZATION_EMAIL = "iagsoncarlos@gmail.com"

# Application Details
APP_DESCRIPTION = "A PyQt6-based OpenVPN connection manager"
APP_URL = "https://github.com/iagsoncarlos/openvpn-manager"

# Development Information
DEVELOPMENT_STATUS = "3 - Alpha"
LICENSE = "MIT License"

# Python Requirements
PYTHON_REQUIRES = ">=3.10"
REQUIRED_PACKAGES = [
    "PyQt6>=6.4.0",
]

# System Requirements
SYSTEM_PACKAGES = [
    "openvpn",              # Core OpenVPN client
    "python3-pyqt6",        # PyQt6 GUI framework
    "zenity",               # GUI password dialogs (GNOME)
    "kdialog",              # GUI password dialogs (KDE) - alternative
    "policykit-1",          # PolicyKit for privilege escalation
    "resolvconf",           # DNS resolution management
    "systemd-resolved",     # Modern DNS resolution (alternative)
    "sudo",                 # Privilege escalation
    "procps",               # Process management (pgrep, pkill)
    "iproute2",             # Network interface management (ip command)
    "net-tools",            # Network tools (ifconfig) - fallback
    "iputils-ping",         # Network connectivity testing
]

# Optional packages that enhance functionality
OPTIONAL_PACKAGES = [
    "network-manager-openvpn",       # NetworkManager OpenVPN plugin
    "network-manager-openvpn-gnome", # GNOME integration
    "openvpn-systemd-resolved",      # systemd-resolved integration
]

# File Information
ICON_FILE = "resources/vpn.png"
DESKTOP_FILE = "debian/openvpn-manager.desktop"
POLICY_FILE = "debian/org.example.openvpn-manager.policy"

def get_app_info():
    """Returns application information as a dictionary"""
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "organization": ORGANIZATION_NAME,
        "email": ORGANIZATION_EMAIL,
        "description": APP_DESCRIPTION,
        "url": APP_URL,
        "license": LICENSE,
        "python_requires": PYTHON_REQUIRES,
        "icon": ICON_FILE
    }

def get_version_string():
    """Returns formatted version string"""
    return f"{APP_NAME} v{APP_VERSION}"

def get_developer_string():
    """Returns formatted developer string"""
    return f"Developed by {ORGANIZATION_NAME}"
