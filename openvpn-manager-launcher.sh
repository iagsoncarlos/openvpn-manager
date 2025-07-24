#!/bin/bash

# OpenVPN Manager Launcher Script
# This script handles privilege escalation and dependency checking for the GUI application

# Function to show error dialog
show_error() {
    local message="$1"
    echo "ERROR: $message" >&2
    if command -v zenity >/dev/null 2>&1; then
        zenity --error --text="$message" --title="OpenVPN Manager Error" --width=400
    elif command -v kdialog >/dev/null 2>&1; then
        kdialog --error "$message" --title "OpenVPN Manager Error"
    else
        echo "ERRO: $message" >&2
        exit 1
    fi
}

# Function to show info dialog
show_info() {
    local message="$1"
    echo "INFO: $message"
    if command -v zenity >/dev/null 2>&1; then
        zenity --info --text="$message" --title="OpenVPN Manager" --width=400
    elif command -v kdialog >/dev/null 2>&1; then
        kdialog --msgbox "$message" --title "OpenVPN Manager"
    else
        echo "INFO: $message"
    fi
}

# Function to check dependencies
check_dependencies() {
    local missing_deps=()
    
    echo "Checking dependencies..."
    
    # Check Python 3
    if ! command -v python3 >/dev/null 2>&1; then
        missing_deps+=("python3")
    fi
    
    # Check OpenVPN
    if ! command -v openvpn >/dev/null 2>&1; then
        missing_deps+=("openvpn")
    fi
    
    # Check PyQt6
    if ! python3 -c "import PyQt6.QtWidgets" 2>/dev/null; then
        missing_deps+=("PyQt6 (python3-pyqt6 or pip3 install PyQt6)")
    fi
    
    # Check main module
    export PYTHONPATH="/usr/lib/python3.10/dist-packages:$PYTHONPATH"
    if ! python3 -c "import main" 2>/dev/null; then
        missing_deps+=("main module (OpenVPN Manager not installed correctly)")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        local deps_text="Missing dependencies:\n"
        for dep in "${missing_deps[@]}"; do
            deps_text+="• $dep\n"
        done
        deps_text+="\nInstall the dependencies and try again."
        show_error "$deps_text"
        exit 1
    fi
    
    echo "All dependencies verified"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    show_error "Do not run this application as root.\nRun as normal user."
    exit 1
fi

# Run dependency check first
check_dependencies

# Check if user is in sudo group
if ! groups | grep -q '\bsudo\b'; then
    show_error "Your user needs to be in the sudo group to use this application.\nRun: sudo usermod -a -G sudo \$USER\nThen logout and login again."
    exit 1
fi

# Check if required commands exist
for cmd in openvpn pkill; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        show_error "Required command not found: $cmd\nInstall the openvpn package."
        exit 1
    fi
done

# Check if we have a terminal for password input
if [ ! -t 0 ]; then
    # No terminal available - launched from GUI
    echo "Graphical environment detected, configuring authentication..."
    
    # Use zenity or kdialog to ask for password if available
    if command -v zenity >/dev/null 2>&1; then
        PASSWORD=$(zenity --password --title="OpenVPN Manager" --text="Enter your password to manage VPN connections:")
        if [ $? -ne 0 ] || [ -z "$PASSWORD" ]; then
            show_error "Authentication cancelled. Cannot start application."
            exit 1
        fi
        # Test the password
        if ! echo "$PASSWORD" | sudo -S -v >/dev/null 2>&1; then
            show_error "Incorrect password. Cannot start application."
            exit 1
        fi
    elif command -v kdialog >/dev/null 2>&1; then
        PASSWORD=$(kdialog --password "Enter your password to manage VPN connections:")
        if [ $? -ne 0 ] || [ -z "$PASSWORD" ]; then
            show_error "Authentication cancelled. Cannot start application."
            exit 1
        fi
        # Test the password
        if ! echo "$PASSWORD" | sudo -S -v >/dev/null 2>&1; then
            show_error "Incorrect password. Cannot start application."
            exit 1
        fi
    else
        show_error "No password dialog available. Run from terminal: openvpn-manager-launcher"
        exit 1
    fi
    
    # Keep sudo session alive in background with the validated password
    (
        while sleep 60; do
            echo "$PASSWORD" | sudo -S -v >/dev/null 2>&1
            kill -0 "$$" || exit
        done 2>/dev/null &
    )
    
    # Export password for subprocess sudo calls
    export SUDO_PASSWORD="$PASSWORD"
    
    echo "Starting OpenVPN Manager..."
    export PYTHONPATH="/usr/lib/python3.10/dist-packages:$PYTHONPATH"
    
    # Add error handling for Python execution
    if ! python3 -c "import main; main.main()" "$@"; then
        echo "Failed to start OpenVPN Manager"
        
        # Try quick diagnostic if available
        if [ -f "/usr/share/openvpn-manager/openvpn-manager-diagnostics.sh" ]; then
            echo "Running automatic fix..."
            if /usr/share/openvpn-manager/openvpn-manager-diagnostics.sh "silent"; then
                echo "Trying to start again..."
                if python3 -c "import main; main.main()" "$@"; then
                    exit 0
                fi
            fi
        fi
        
        # Simple error message
        show_error "Failed to start OpenVPN Manager.\n\nExecute: /usr/share/openvpn-manager/openvpn-manager-diagnostics.sh\nOr: pip3 install PyQt6"
        exit 1
    fi
else
    # Terminal available, use sudo
    echo "Authenticating to manage VPN connections..."
    if ! sudo -v; then
        show_error "Authentication failed. Cannot start application."
        exit 1
    fi

    # Keep sudo session alive in background
    (
        while sleep 60; do
            sudo -n true
            kill -0 "$$" || exit
        done 2>/dev/null &
    )

    # Now launch the Python application using the installed module
    echo "Starting OpenVPN Manager..."
    export PYTHONPATH="/usr/lib/python3.10/dist-packages:$PYTHONPATH"
    
    # Add error handling for Python execution
    if ! python3 -c "import main; main.main()" "$@"; then
        echo "Failed to start OpenVPN Manager"
        
        # Try quick diagnostic if available
        if [ -f "/usr/share/openvpn-manager/openvpn-manager-diagnostics.sh" ]; then
            echo "Running automatic fix..."
            if /usr/share/openvpn-manager/openvpn-manager-diagnostics.sh "silent"; then
                echo "Trying to start again..."
                if python3 -c "import main; main.main()" "$@"; then
                    exit 0
                fi
            fi
        fi
        
        # Simple error message
        echo "Execute: /usr/share/openvpn-manager/openvpn-manager-diagnostics.sh"
        echo "Or: pip3 install PyQt6"
        exit 1
    fi
fi
