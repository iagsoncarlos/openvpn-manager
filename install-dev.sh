#!/bin/bash

# OpenVPN Manager - Development Installer
# Installs the application for local development and testing

set -e

echo " OpenVPN Manager - Development Installer"
echo "=========================================="

# Get current version
if [ -f "VERSION" ]; then
    CURRENT_VERSION=$(cat VERSION)
else
    CURRENT_VERSION="0.2.0"
fi

echo " Version: $CURRENT_VERSION"
echo ""

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

# Function to check dependencies
check_dependencies() {
    log_info "Checking system dependencies..."
    
    local missing_deps=()
    local system_deps=("python3" "python3-pip" "openvpn" "zenity")
    
    for dep in "${system_deps[@]}"; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            missing_deps+=("$dep")
        fi
    done
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_warning "Missing dependencies: ${missing_deps[*]}"
        log_info "Installing system dependencies..."
        sudo apt update
        sudo apt install -y "${missing_deps[@]}" || {
            log_error "Failed to install system dependencies"
            exit 1
        }
    fi
    
    log_success "System dependencies verified"
}

# Function to install Python dependencies
install_python_deps() {
    log_info "Installing Python dependencies..."
    
    # Check if PyQt6 is available
    if ! python3 -c "import PyQt6.QtWidgets" >/dev/null 2>&1; then
        log_info "Installing PyQt6..."
        pip3 install --user PyQt6>=6.4.0 || {
            log_warning "Failed to install PyQt6 via pip, trying apt..."
            sudo apt install -y python3-pyqt6 || {
                log_error "Failed to install PyQt6"
                exit 1
            }
        }
    fi
    
    log_success "Python dependencies installed"
}

# Function to setup development environment
setup_dev_environment() {
    log_info "Setting up development environment..."
    
    # Make scripts executable
    chmod +x openvpn-manager-launcher.sh
    chmod +x build.sh
    chmod +x uninstall.sh
    
    # Add current directory to PYTHONPATH for development
    echo "export PYTHONPATH=\"$(pwd):\$PYTHONPATH\"" > .env
    
    log_success "Development environment configured"
}

# Function to create development shortcuts
create_dev_shortcuts() {
    log_info "Creating development shortcuts..."
    
    # Create local desktop file for testing
    mkdir -p ~/.local/share/applications
    cat > ~/.local/share/applications/openvpn-manager-dev.desktop << EOF
[Desktop Entry]
Version=$CURRENT_VERSION
Type=Application
Name=OpenVPN Manager (Dev v$CURRENT_VERSION)
Comment=OpenVPN connection manager - Development version
Exec=$(pwd)/openvpn-manager-launcher.sh
Icon=$(pwd)/resources/vpn.png
Terminal=false
Categories=Network;Settings;
Keywords=vpn;openvpn;network;connection;
EOF

    # Update desktop database
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database ~/.local/share/applications 2>/dev/null || true
    fi
    
    log_success "Development shortcuts created"
}

# Function to test installation
test_installation() {
    log_info "Testing installation..."
    
    # Test Python imports
    if python3 -c "import main, config; print(' Main modules OK')" 2>/dev/null; then
        log_success "Module import OK"
    else
        log_error "Module import failed"
        return 1
    fi
    
    # Test PyQt6
    if python3 -c "import PyQt6.QtWidgets; print(' PyQt6 OK')" 2>/dev/null; then
        log_success "PyQt6 OK"
    else
        log_error "PyQt6 failed"
        return 1
    fi
    
    # Test launcher script
    if [ -x "openvpn-manager-launcher.sh" ]; then
        log_success "Launcher script OK"
    else
        log_error "Launcher script not executable"
        return 1
    fi
    
    log_success "All tests passed!"
}

# Function to show usage instructions
show_usage() {
    echo ""
    log_success " Development installation completed!"
    echo ""
    echo " How to use:"
    echo "  • Run application: ./openvpn-manager-launcher.sh"
    echo "  • Run with debug: python3 main.py"
    echo "  • Build package: ./build.sh"
    echo "  • Uninstall: ./uninstall.sh"
    echo ""
    echo " Development:"
    echo "  • Load environment: source .env"
    echo "  • Desktop shortcut: OpenVPN Manager (Dev) in menu"
    echo "  • Main files: main.py, config.py"
    echo ""
    echo " Project structure:"
    echo "  • main.py - Main code"
    echo "  • config.py - Configuration"
    echo "  • openvpn-manager-launcher.sh - Launch script"
    echo "  • debian/ - Packaging files"
    echo "  • resources/ - Resources (icons, etc)"
    echo "  • build.sh - Build script"
    echo ""
}

# Main installation process
main() {
    echo "This script will configure OpenVPN Manager for local development."
    echo ""
    read -p "Do you want to continue? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        log_info "Installation cancelled by user"
        exit 0
    fi
    
    echo ""
    log_info "Starting development installation..."
    
    # Check system dependencies
    check_dependencies
    
    # Install Python dependencies
    install_python_deps
    
    # Setup development environment
    setup_dev_environment
    
    # Create development shortcuts
    create_dev_shortcuts
    
    # Test installation
    test_installation
    
    # Show usage instructions
    show_usage
}

# Execute main function
main "$@"
