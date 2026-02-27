#!/usr/bin/env python3
"""
Configuration file for OpenVPN Manager
Contains application metadata and version information
"""


# Read version from VERSION file
def _get_version():
    """Read version from VERSION file"""
    try:
        from pathlib import Path

        # 1) Same directory as this file
        base = Path(__file__).resolve().parent
        candidate = base / 'VERSION'
        if candidate.exists():
            return candidate.read_text(encoding='utf-8').strip()

        # 2) Walk up a few parents (project root may be above the package dir)
        cur = base
        for _ in range(4):
            cur = cur.parent
            candidate = cur / 'VERSION'
            if candidate.exists():
                return candidate.read_text(encoding='utf-8').strip()

        # 3) Try package metadata names that are commonly used
        try:
            from importlib.metadata import version, PackageNotFoundError
            for pkg_name in ("openvpn-manager", "openvpn_manager", "openvpn-manager-py", "openvpn_manager-py"):
                try:
                    v = version(pkg_name)
                    if v:
                        return v
                except PackageNotFoundError:
                    continue
                except Exception:
                    continue
        except Exception:
            pass

        return "unknown"
    except Exception:
        return "unknown"


# Application Information
APP_NAME = "OpenVPN Manager"
APP_VERSION = _get_version()
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
    "network-manager-openvpn-gnome",  # GNOME integration
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


# Optional override for the DNS update script path used with OpenVPN
# Set to None to let the application auto-detect; otherwise provide the
# full path to the helper script (for example '/etc/openvpn/update-resolv-conf')
OPENVPN_DNS_SCRIPT = None
