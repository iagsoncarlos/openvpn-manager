#!/bin/bash
set -eo pipefail # Added 'o pipefail' for safer script execution

# Self-contained .deb builder for OpenVPN Manager
# 1. Downloads dependency wheels
# 2. Prepares the Debian package staging area with wheels
# 3. Generates the .deb package with all components included


# --- Configuration ---
VERSION=$(cat VERSION)
PROJECT_NAME="openvpn-manager" # Define project name for clarity
BUILD_DIR="dist"
WHEELS_SUBDIR="wheels" # Subdirectory within BUILD_DIR for downloaded wheels
DEB_STAGING_WHEELS_DIR="debian/$PROJECT_NAME/usr/share/$PROJECT_NAME/wheels"

# --- Version Consistency Check ---
DEBIAN_VERSION=$(awk '/^openvpn-manager \(/ {gsub(/[()]/, "", $2); split($2, v, "-"); print v[1]; exit}' debian/changelog)
if [ "$VERSION" != "$DEBIAN_VERSION" ]; then
    echo "❌ ERROR: VERSION ($VERSION) does not match debian/changelog version ($DEBIAN_VERSION)."
    echo "Please synchronize the VERSION file and debian/changelog before building."
    exit 1
fi

# --- Setup and Cleanup ---
echo "⚙️  Preparing build environment..."
# Clean up previous build artifacts in 'dist'
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/$WHEELS_SUBDIR" # Create directory for downloaded wheels

# --- Download Python Dependencies (Wheels) ---
echo "⬇️  Downloading PyQt6 dependencies..."
pip3 download --dest "$BUILD_DIR/$WHEELS_SUBDIR" --prefer-binary "PyQt6>=6.4.0"

# --- Copy Wheels to Debian Staging Area ---
# Ensure the target directory for wheels exists within the Debian staging area
echo "📦 Copying wheels to Debian package staging directory: $DEB_STAGING_WHEELS_DIR"
mkdir -p "$DEB_STAGING_WHEELS_DIR"
cp "$BUILD_DIR/$WHEELS_SUBDIR"/*.whl "$DEB_STAGING_WHEELS_DIR/"

# --- Build Debian Package ---
echo "🏗️  Building .deb package for $PROJECT_NAME version $VERSION..."
# dpkg-buildpackage uses debian/rules to define the build process.
# We explicitly specify the project name to avoid ambiguity.
dpkg-buildpackage -b -uc -us

# --- Post-Build Cleanup and Packaging ---
echo "🧹 Cleaning up and moving final .deb package..."


# Find any .deb file that starts with the project name and version in the parent directory.
DEB_FILE=$(find .. -maxdepth 1 -name "${PROJECT_NAME}_${VERSION}*.deb" | sort -V | tail -n1)

if [[ -f "$DEB_FILE" ]]; then
    mkdir -p "$BUILD_DIR" # Ensure dist directory exists if it was removed earlier
    mv "$DEB_FILE" "$BUILD_DIR/"
    echo -e "\n✅ Self-contained .deb generated successfully! Find it at: $BUILD_DIR/$(basename "$DEB_FILE")"
else
    echo -e "\n❌ Error: .deb file not found after build!"
    exit 1 # Exit with an error code if the .deb is not found
fi

# Optional: Clean up downloaded wheels from the temporary 'dist/wheels' directory
echo "🧹 Cleaning up temporary downloaded wheels..."
rm -rf "$BUILD_DIR/$WHEELS_SUBDIR"

echo "🎉 Build process finished."