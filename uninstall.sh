#!/bin/bash

# OpenVPN Manager - Uninstaller
# Removes the application and cleans up system files

set -e

echo "  OpenVPN Manager Uninstaller"
echo "==============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    log_error "Do not run this script as root. Run as normal user."
    exit 1
fi

# Function to check if package is installed
is_package_installed() {
    dpkg -l openvpn-manager >/dev/null 2>&1
}

# Function to remove package
remove_package() {
    log_info "Removing OpenVPN Manager package..."
    
    if is_package_installed; then
        sudo dpkg -r openvpn-manager || {
            log_warning "Failed to remove package via dpkg, trying apt..."
            sudo apt-get remove -y openvpn-manager || {
                log_error "Failed to remove package"
                return 1
            }
        }
        log_success "Package removed successfully"
    else
        log_warning "Package is not installed"
    fi
}

# Function to clean up Python dependencies
cleanup_python_deps() {
    log_info "Checking installed Python dependencies..."
    
    # Check if PyQt6 was installed by our package
    if python3 -c "import PyQt6" >/dev/null 2>&1; then
        echo "PyQt6 found. Do you want to remove it? (may affect other applications)"
        read -p "Remove PyQt6? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Removing PyQt6..."
            pip3 uninstall -y PyQt6 PyQt6-Qt6 PyQt6-sip || {
                log_warning "Failed to remove PyQt6 via pip"
            }
            log_success "PyQt6 removed"
        else
            log_info "PyQt6 kept"
        fi
    fi
}

# Function to clean up system files
cleanup_system_files() {
    log_info "Cleaning up system files..."
    
    # Remove application files that might remain
    local files_to_remove=(
        "/usr/bin/openvpn-manager"
        "/usr/bin/openvpn-manager-launcher"
        "/usr/share/applications/openvpn-manager.desktop"
        "/usr/share/pixmaps/openvpn-manager.png"
        "/usr/share/polkit-1/actions/org.example.openvpn-manager.policy"
        "/usr/share/openvpn-manager"
    )
    
    for file in "${files_to_remove[@]}"; do
        if [ -e "$file" ]; then
            log_info "Removing $file..."
            sudo rm -rf "$file" || log_warning "Failed to remove $file"
        fi
    done
    
    # Clean up desktop database
    if command -v update-desktop-database >/dev/null 2>&1; then
        log_info "Updating desktop database..."
        sudo update-desktop-database /usr/share/applications 2>/dev/null || true
    fi
    
    # Clean up icon cache
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        log_info "Updating icon cache..."
        sudo gtk-update-icon-cache -f /usr/share/pixmaps 2>/dev/null || true
    fi
    
    log_success "System cleanup completed"
}

# Function to clean up OpenVPN scripts created by the app
cleanup_openvpn_scripts() {
    log_info "Checking OpenVPN scripts created by the application..."
    
    if [ -f "/etc/openvpn/update-resolv-conf" ]; then
        echo "DNS script found at /etc/openvpn/update-resolv-conf"
        echo "This script may have been created by OpenVPN Manager."
        read -p "Remove DNS script? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo rm -f /etc/openvpn/update-resolv-conf
            log_success "DNS script removed"
        else
            log_info "DNS script kept"
        fi
    fi
}

# Main uninstall process
main() {
    echo "This script will completely remove OpenVPN Manager from the system."
    echo ""
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Uninstallation cancelled by user"
        exit 0
    fi
    
    echo ""
    log_info "Starting uninstallation process..."
    
    # Remove the package
    remove_package
    
    # Clean up system files
    cleanup_system_files
    
    # Optional cleanup
    echo ""
    log_info "Optional cleanup (recommended):"
    cleanup_python_deps
    cleanup_openvpn_scripts
    
    echo ""
    log_success " Uninstallation completed!"
    echo ""
    echo " What was removed:"
    echo "  • OpenVPN Manager package"
    echo "  • System files (/usr/bin, /usr/share)"
    echo "  • Application menu entries"
    echo "  • PolicyKit policies"
    echo ""
    echo " Note: User configurations in ~/.config may remain"
    echo "     For complete removal, delete manually if needed"
}

# Execute main function
main "$@"
