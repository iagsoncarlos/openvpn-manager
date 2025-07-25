#!/bin/bash
set -e

# Self-contained .deb builder for OpenVPN Manager
# 1. Downloads dependency wheels
# 2. Copies them to the package folder
# 3. Generates the .deb with everything included

VERSION=$(cat VERSION)
BUILD_DIR="dist"
WHEELS_DIR="$BUILD_DIR/wheels"

# Clean up and prepare
rm -rf "$BUILD_DIR/wheels"
mkdir -p "$WHEELS_DIR"

# Download dependencies as wheels
pip3 download --dest "$WHEELS_DIR" --prefer-binary PyQt6>=6.4.0

# Copy wheels to the package location
mkdir -p debian/openvpn-manager/usr/share/openvpn-manager/wheels
cp $WHEELS_DIR/*.whl debian/openvpn-manager/usr/share/openvpn-manager/wheels/

# Generate the .deb normally
# (uses the standard debian/rules, which already installs wheels and scripts)
dpkg-buildpackage -b -uc -us

# Clean up temporary wheels from the package directory (optional)
rm -rf debian/openvpn-manager/usr/share/openvpn-manager/wheels/*

# Move the .deb to dist/ for CI/CD workflows
DEB_FILE=$(find .. -maxdepth 1 -name "openvpn-manager_${VERSION}-1_all.deb" | sort -V | tail -n1)

if [ -f "$DEB_FILE" ]; then
    mv "$DEB_FILE" "$BUILD_DIR/" || true
    echo -e "\n✅ Self-contained .deb generated! See $BUILD_DIR/$(basename "$DEB_FILE")"
else
    echo -e "\n❌ .deb file not found after build!"
fi