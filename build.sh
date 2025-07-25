#!/bin/bash

# OpenVPN Manager - Enhanced Self-Contained Builder
# Downloads Python wheels and includes them in the .deb package

set -e

echo "=============================================="
echo "  OpenVPN Manager - Self-Contained Builder"
echo "=============================================="

# Get current version from VERSION file
if [ ! -f "VERSION" ]; then
    echo "0.2.0" > VERSION
fi

CURRENT_VERSION=$(cat VERSION)

echo " Build version: $CURRENT_VERSION"
echo ""
echo " To increment version before build:"
echo "   ./version.sh patch  # For bug fixes"
echo "   ./version.sh minor  # For new features"
echo "   ./version.sh major  # For breaking changes"
echo ""

# Configuration
BUILD_DIR="build-enhanced"
WHEELS_DIR="$BUILD_DIR/wheels"

# Clean and prepare
echo " Preparing build environment..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
mkdir -p "$WHEELS_DIR"

# Download Python wheels
echo " Downloading Python dependencies as wheels..."
pip3 download --dest "$WHEELS_DIR" --prefer-binary PyQt6>=6.4.0

echo " Downloaded wheels:"
ls -la "$WHEELS_DIR"

# Create enhanced setup.py that includes wheels
cat > "$BUILD_DIR/setup-enhanced.py" << 'EOF'
#!/usr/bin/env python3
from setuptools import setup, find_packages
from config import (
    APP_NAME, APP_VERSION, APP_DESCRIPTION, ORGANIZATION_NAME, 
    ORGANIZATION_EMAIL, APP_URL, REQUIRED_PACKAGES, PYTHON_REQUIRES
)
import os

# Find all wheel files
wheels_dir = 'build-enhanced/wheels'
wheel_files = []
if os.path.exists(wheels_dir):
    wheel_files = [f for f in os.listdir(wheels_dir) if f.endswith('.whl')]

setup(
    name=APP_NAME.lower().replace(" ", "-"),
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
EOF

# Create enhanced control file
cat > "$BUILD_DIR/control-enhanced" << EOF
Source: openvpn-manager
Section: net
Priority: optional
Maintainer: Iágson Carlos Lima Silva <iagsoncarlos@gmail.com>
Build-Depends: debhelper-compat (= 13), python3-all, python3-setuptools, dh-python
Standards-Version: 4.6.0
Homepage: https://github.com/iagsoncarlos/openvpn-manager
Rules-Requires-Root: no

Package: openvpn-manager
Architecture: all
Depends: \${misc:Depends}, 
 python3 (>= 3.10),
 python3-pip,
 openvpn,
 resolvconf | systemd-resolved,
 policykit-1,
 zenity | kdialog,
 sudo,
 procps,
 iproute2 | net-tools,
 iputils-ping
Recommends: network-manager-openvpn, network-manager-openvpn-gnome
Suggests: openvpn-systemd-resolved
Description: An OpenVPN connection manager
 OpenVPN Manager with all Python dependencies bundled within the package.
 This version includes PyQt6 wheels and installs them automatically during
 package configuration, ensuring a completely self-contained installation.
 .
 Features include:
  - Load and manage OpenVPN configuration files (.ovpn)
  - Connect and disconnect from VPN servers with GUI authentication
  - Real-time connection monitoring and data usage statistics
  - Save connection credentials securely
  - Desktop integration with application menu
  - Automatic DNS resolution management
  - Support for both terminal and GUI authentication
  - Bundled PyQt6 dependencies (no internet required)
 .
 This package includes all necessary Python dependencies and requires
 no external package downloads during installation.
EOF

# Create enhanced postinst script
cat > "$BUILD_DIR/postinst-enhanced" << EOF
#!/bin/bash

set -e

case "\$1" in
    configure)
        echo "Configuring OpenVPN Manager (Self-Contained v$CURRENT_VERSION)..."
        
        # Function to log messages
        log_msg() {
            echo "[POSTINST] $1"
        }
        
        # Function to check if a Python package is available
        check_python_package() {
            python3 -c "import $1" 2>/dev/null
        }
        
        log_msg "Checking Python dependencies..."
        
        # Install bundled Python wheels
        WHEELS_DIR="/usr/share/openvpn-manager/wheels"
        if [ -d "$WHEELS_DIR" ] && [ "$(ls -A "$WHEELS_DIR" 2>/dev/null)" ]; then
            log_msg "Installing bundled Python dependencies..."
            
            # Install wheels for all users
            for wheel in "$WHEELS_DIR"/*.whl; do
                if [ -f "$wheel" ]; then
                    WHEEL_NAME=$(basename "$wheel")
                    log_msg "Installing $WHEEL_NAME..."
                    pip3 install --force-reinstall --no-deps "$wheel" || {
                        log_msg "Warning: Failed to install $WHEEL_NAME"
                    }
                fi
            done
            
            log_msg " Bundled dependencies installed successfully!"
        else
            log_msg "  No bundled wheels found, installing PyQt6 from internet..."
            pip3 install PyQt6>=6.4.0 || {
                log_msg " Failed to install PyQt6. Manual installation required."
            }
        fi
        
        # Test PyQt6 installation
        if check_python_package "PyQt6.QtWidgets"; then
            log_msg " PyQt6 installation verified!"
        else
            log_msg "  PyQt6 verification failed. GUI may not work."
            log_msg "Manual installation: pip3 install PyQt6"
        fi
        
        # Ensure OpenVPN scripts directory exists
        if [ ! -d "/etc/openvpn" ]; then
            mkdir -p /etc/openvpn
        fi
        
        # Check if update-resolv-conf script exists, if not create a basic one
        if [ ! -f "/etc/openvpn/update-resolv-conf" ]; then
            echo "Creating basic DNS update script..."
            cat > /etc/openvpn/update-resolv-conf << 'EOFSCRIPT'
#!/bin/bash
# Enhanced DNS update script for OpenVPN
case "$script_type" in
    up)
        echo "Setting up VPN DNS..."
        if [ -n "$foreign_option_1" ]; then
            # Backup current resolv.conf
            cp /etc/resolv.conf /etc/resolv.conf.openvpn.backup 2>/dev/null || true
            # Extract DNS server from foreign_option_1
            DNS_SERVER=$(echo "$foreign_option_1" | sed 's/dhcp-option DNS //')
            if [ -n "$DNS_SERVER" ]; then
                echo "nameserver $DNS_SERVER" > /etc/resolv.conf
                echo "# OpenVPN DNS - $DNS_SERVER" >> /etc/resolv.conf
            fi
        fi
        ;;
    down)
        echo "Restoring original DNS..."
        if [ -f /etc/resolv.conf.openvpn.backup ]; then
            mv /etc/resolv.conf.openvpn.backup /etc/resolv.conf
        fi
        ;;
esac
EOFSCRIPT
            chmod +x /etc/openvpn/update-resolv-conf
        fi
        
        # Ensure PolicyKit is properly configured
        if command -v systemctl &> /dev/null; then
            systemctl reload polkit.service || true
        fi
        
        # Update desktop database
        if command -v update-desktop-database &> /dev/null; then
            update-desktop-database /usr/share/applications || true
        fi
        
        # Update icon cache
        if command -v gtk-update-icon-cache &> /dev/null; then
            gtk-update-icon-cache -f /usr/share/pixmaps || true
        fi
        
        echo ""
        echo " OpenVPN Manager (Self-Contained) installation completed!"
        echo " All Python dependencies included in package"
        echo " Launch with: openvpn-manager-launcher"
        echo "  Or find 'OpenVPN Manager' in your applications menu"
        echo ""
        
        log_msg "Installation completed!"
        ;;
esac

#DEBHELPER#

exit 0
EOF

# Update changelog
cat > "$BUILD_DIR/changelog-enhanced" << EOF
openvpn-manager ($CURRENT_VERSION-1) unstable; urgency=medium

  * Self-contained package with bundled Python dependencies
  * Includes PyQt6 wheels within the .deb package
  * No internet connection required during installation
  * Enhanced postinst script with dependency verification
  * Improved DNS update script with better error handling
  * Complete offline installation capability
  * Automatic fallback to internet installation if wheels fail

 -- Iágson Carlos Lima Silva <iagsoncarlos@gmail.com>  $(date -R)

EOF

# Create enhanced rules file
cat > "$BUILD_DIR/rules-enhanced" << 'EOF'
#!/usr/bin/make -f

%:
	dh $@ --with python3 --buildsystem=pybuild

override_dh_auto_build:
	cp build-enhanced/setup-enhanced.py setup.py
	dh_auto_build

override_dh_auto_install:
	dh_auto_install
	# Install launcher script
	mkdir -p debian/openvpn-manager/usr/bin
	cp openvpn-manager-launcher.sh debian/openvpn-manager/usr/bin/openvpn-manager-launcher
	# Install desktop file
	mkdir -p debian/openvpn-manager/usr/share/applications
	cp debian/openvpn-manager.desktop debian/openvpn-manager/usr/share/applications/
	# Install icon
	mkdir -p debian/openvpn-manager/usr/share/pixmaps
	cp resources/vpn.png debian/openvpn-manager/usr/share/pixmaps/openvpn-manager.png
	# Install polkit policy
	mkdir -p debian/openvpn-manager/usr/share/polkit-1/actions
	cp debian/org.example.openvpn-manager.policy debian/openvpn-manager/usr/share/polkit-1/actions/
	# Install bundled wheels
	mkdir -p debian/openvpn-manager/usr/share/openvpn-manager/wheels
	if [ -d "build-enhanced/wheels" ] && [ "$$(ls -A build-enhanced/wheels 2>/dev/null)" ]; then \
		cp build-enhanced/wheels/*.whl debian/openvpn-manager/usr/share/openvpn-manager/wheels/ || true; \
	fi
	# Install Qt diagnostics script
	mkdir -p debian/openvpn-manager/usr/share/openvpn-manager
	cp debian/openvpn-manager-diagnostics.sh debian/openvpn-manager/usr/share/openvpn-manager/openvpn-manager-diagnostics.sh || true

override_dh_fixperms:
	dh_fixperms
	# Set proper permissions for scripts
	chmod 755 debian/openvpn-manager/usr/bin/openvpn-manager
	chmod 755 debian/openvpn-manager/usr/bin/openvpn-manager-launcher
	# Set permissions for diagnostics script
	chmod 755 debian/openvpn-manager/usr/share/openvpn-manager/openvpn-manager-diagnostics.sh || true
EOF

# Backup original files and use enhanced versions
echo " Setting up enhanced build configuration..."
cp debian/control debian/control.backup
cp debian/postinst debian/postinst.backup
cp debian/rules debian/rules.backup
if [ -f debian/changelog ]; then
    cp debian/changelog debian/changelog.backup
else
    echo " Warning: debian/changelog not found, creating minimal one..."
    echo "openvpn-manager ($CURRENT_VERSION-1) unstable; urgency=medium" > debian/changelog
    echo "" >> debian/changelog
    echo "  * Version $CURRENT_VERSION" >> debian/changelog
    echo "" >> debian/changelog
    echo " -- Iágson Carlos Lima Silva <iagsoncarlos@gmail.com>  $(date -R)" >> debian/changelog
fi

cp "$BUILD_DIR/control-enhanced" debian/control
cp "$BUILD_DIR/postinst-enhanced" debian/postinst
cp "$BUILD_DIR/rules-enhanced" debian/rules
cp "$BUILD_DIR/changelog-enhanced" debian/changelog

chmod +x debian/rules debian/postinst

# Build the enhanced package
echo " Building self-contained package..."
dpkg-buildpackage -b -uc -us

# Restore original files
echo " Restoring original configuration files..."
mv debian/control.backup debian/control
mv debian/postinst.backup debian/postinst
mv debian/rules.backup debian/rules
if [ -f debian/changelog.backup ]; then
    mv debian/changelog.backup debian/changelog
fi

echo ""
echo " Self-contained package build completed!"
echo " Package: ../openvpn-manager_${CURRENT_VERSION}-1_all.deb"
echo " Size: $(du -sh ../openvpn-manager_${CURRENT_VERSION}-1_all.deb 2>/dev/null | cut -f1 || echo 'Unknown')"
echo ""
echo " This package includes:"
echo "   • OpenVPN Manager application"
echo "   • Bundled PyQt6 wheels ($(ls "$WHEELS_DIR" | wc -l) files)"
echo "   • All system integration files"
echo "   • Enhanced configuration scripts"
echo "   • No internet required for Python dependencies"
echo ""
echo " Install with:"
echo "   sudo dpkg -i ../openvpn-manager_${CURRENT_VERSION}-1_all.deb"
echo "   sudo apt-get install -f  # Only for system packages"
echo ""
echo " The package will automatically install PyQt6 from bundled wheels!"
