#!/usr/bin/env python3
from setuptools import setup, find_packages
import os

# Read version from VERSION file
def get_version():
    with open('VERSION', 'r') as f:
        return f.read().strip()

# Find all wheel files
wheels_dir = 'build-enhanced/wheels'
wheel_files = []
if os.path.exists(wheels_dir):
    wheel_files = [f for f in os.listdir(wheels_dir) if f.endswith('.whl')]

setup(
    name="openvpn-manager",
    version=get_version(),
    description="A PyQt6-based OpenVPN connection manager",
    author="Iágson Carlos Lima Silva",
    author_email="iagsoncarlos@gmail.com",
    url="https://github.com/iagsoncarlos/openvpn-manager",
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
    python_requires=">=3.10",
)
