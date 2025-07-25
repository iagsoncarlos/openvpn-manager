#!/usr/bin/env python3
"""
Standalone setup.py for OpenVPN Manager
No imports from project modules to avoid dependency issues during build
"""
from setuptools import setup
import os

# Hardcoded version - will be updated by version.sh - FIXED
VERSION = "0.2.4"

# Find all wheel files (only for .deb builds)
wheels_dir = 'build-enhanced/wheels'
wheel_files = []
if os.path.exists(wheels_dir):
    wheel_files = [f for f in os.listdir(wheels_dir) if f.endswith('.whl')]

# Data files for system integration
data_files = [
    ("share/applications", ["debian/openvpn-manager.desktop"]),
    ("share/pixmaps", ["resources/vpn.png"]),
    ("share/polkit-1/actions", ["debian/org.example.openvpn-manager.policy"]),
]

# Add wheels only if they exist (for .deb builds)
if wheel_files:
    data_files.append(("share/openvpn-manager/wheels", [f"build-enhanced/wheels/{whl}" for whl in wheel_files]))

setup(
    name="openvpn-manager",
    version=VERSION,
    description="A PyQt6-based OpenVPN connection manager",
    long_description="OpenVPN Manager with bundled dependencies for offline installation.",
    author="Iágson Carlos Lima Silva",
    author_email="iagsoncarlos@gmail.com",
    url="https://github.com/iagsoncarlos/openvpn-manager",
    py_modules=["main", "config"],  # Just list them, don't import
    packages=[],  # No packages, just modules
    install_requires=[],  # No external dependencies for .deb build
    entry_points={
        "console_scripts": [
            "openvpn-manager=main:main",
        ],
    },
    data_files=data_files,
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
    python_requires=">=3.10",
    license="MIT",
)
