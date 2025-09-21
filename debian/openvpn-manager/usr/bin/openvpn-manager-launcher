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

# Function to authenticate and run with privileges
authenticate_and_run() {
    echo "Requesting authentication for OpenVPN Manager..."
    
    # Collect theme-related environment variables
    local env_vars=""
    
    # GTK Theme variables
    [ -n "$GTK_THEME" ] && env_vars="$env_vars GTK_THEME=$GTK_THEME"
    [ -n "$GTK2_RC_FILES" ] && env_vars="$env_vars GTK2_RC_FILES=$GTK2_RC_FILES"
    [ -n "$GTK_RC_FILES" ] && env_vars="$env_vars GTK_RC_FILES=$GTK_RC_FILES"
    
    # Desktop session variables
    [ -n "$XDG_CURRENT_DESKTOP" ] && env_vars="$env_vars XDG_CURRENT_DESKTOP=$XDG_CURRENT_DESKTOP"
    [ -n "$DESKTOP_SESSION" ] && env_vars="$env_vars DESKTOP_SESSION=$DESKTOP_SESSION"
    [ -n "$XDG_SESSION_DESKTOP" ] && env_vars="$env_vars XDG_SESSION_DESKTOP=$XDG_SESSION_DESKTOP"
    
    # KDE specific variables
    [ -n "$KDE_SESSION_VERSION" ] && env_vars="$env_vars KDE_SESSION_VERSION=$KDE_SESSION_VERSION"
    [ -n "$KDE_FULL_SESSION" ] && env_vars="$env_vars KDE_FULL_SESSION=$KDE_FULL_SESSION"
    
    # QT Theme variables
    [ -n "$QT_STYLE_OVERRIDE" ] && env_vars="$env_vars QT_STYLE_OVERRIDE=$QT_STYLE_OVERRIDE"
    [ -n "$QT_QPA_PLATFORMTHEME" ] && env_vars="$env_vars QT_QPA_PLATFORMTHEME=$QT_QPA_PLATFORMTHEME"
    
    # Try pkexec first (preferred for GUI applications)
    if command -v pkexec >/dev/null 2>&1; then
        export PYTHONPATH="/usr/lib/python3.10/dist-packages:$PYTHONPATH"
        exec pkexec env DISPLAY="$DISPLAY" XAUTHORITY="$XAUTHORITY" PYTHONPATH="$PYTHONPATH" $env_vars python3 -c "import main; main.main()" "$@"
    # Fallback to sudo
    elif command -v sudo >/dev/null 2>&1; then
        export PYTHONPATH="/usr/lib/python3.10/dist-packages:$PYTHONPATH"
        exec sudo -E env $env_vars python3 -c "import main; main.main()" "$@"
    else
        show_error "No privilege escalation method available (pkexec or sudo).\nPlease install policykit-1 or sudo."
        exit 1
    fi
}

# Launch application with elevated privileges from the start
echo "Starting OpenVPN Manager with elevated privileges..."
authenticate_and_run "$@"

# This part should not be reached if exec is successful
echo "Failed to start OpenVPN Manager"
if [ -f "/usr/share/openvpn-manager/openvpn-manager-diagnostics.sh" ]; then
    echo "Running automatic fix..."
    if /usr/share/openvpn-manager/openvpn-manager-diagnostics.sh "silent"; then
        echo "Trying to start again..."
        authenticate_and_run "$@"
    fi
fi
show_error "Failed to start OpenVPN Manager.\n\nExecute: /usr/share/openvpn-manager/openvpn-manager-diagnostics.sh\nOr: pip3 install PyQt6"
exit 1
