#!/usr/bin/env python3
from setuptools import setup, find_packages
import os

# Read version from VERSION file
def get_version():
    try:
        with open('VERSION', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "0.2.0"  # Fallback version

# Application metadata
APP_NAME = "openvpn-manager"
APP_VERSION = get_version()
APP_DESCRIPTION = "A PyQt6-based OpenVPN connection manager"
ORGANIZATION_NAME = "Iágson Carlos Lima Silva"
ORGANIZATION_EMAIL = "iagsoncarlos@gmail.com"
APP_URL = "https://github.com/iagsoncarlos/openvpn-manager"
PYTHON_REQUIRES = ">=3.10"
REQUIRED_PACKAGES = [
    "PyQt6>=6.4.0",
]

# Find all wheel files
wheels_dir = 'build-enhanced/wheels'
wheel_files = []
if os.path.exists(wheels_dir):
    wheel_files = [f for f in os.listdir(wheels_dir) if f.endswith('.whl')]

setup(
    name=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    author=ORGANIZATION_NAME,
    author_email=ORGANIZATION_EMAIL,
    url=APP_URL,
    py_modules=["main", "config"],
    install_requires=[],  # No external dependencies
    entry_points={
        "console_scripts": [
            "openvpn-manager=main:main",
        ],
    },
    data_files=[
        ("share/applications", ["debian/openvpn-manager.desktop"]),
        ("share/pixmaps", ["resources/vpn.png"]),
        ("share/polkit-1/actions", ["debian/org.example.openvpn-manager.policy"]),
        ("share/openvpn-manager/wheels", [f"build-enhanced/wheels/{whl}" for whl in wheel_files]),
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: POSIX :: Linux",
        "Topic :: System :: Networking",
    ],
    python_requires=PYTHON_REQUIRES,
)
