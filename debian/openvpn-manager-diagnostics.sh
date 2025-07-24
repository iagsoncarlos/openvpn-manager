#!/bin/bash
# OpenVPN Manager - Qt XCB Fix Integration
# Minimal script integrated into the .deb package

set -e

# Test Qt platform
test_qt_platform() {
    python3 -c "
from PyQt6.QtWidgets import QApplication
import sys
try:
    app = QApplication(sys.argv)
    print('Qt platform test: SUCCESS')
    app.quit()
except Exception as e:
    print(f'Qt platform test: FAILED - {str(e)}')
    sys.exit(1)
" 2>&1
}

# Fix Qt XCB issues
fix_qt_xcb() {
    apt-get update >/dev/null 2>&1 || return 1
    
    # Install essential XCB libraries
    apt-get install -y \
        libxcb-cursor0 libxcb-cursor-dev \
        libxcb-xinerama0 libxcb-icccm4 \
        libxcb-image0 libxcb-keysyms1 \
        libxcb-randr0 libxcb-render-util0 \
        libxcb-shape0 libxcb-sync1 \
        libxcb-xfixes0 >/dev/null 2>&1 || return 1
    
    # Install Qt6 base packages
    apt-get install -y \
        qt6-base-dev libqt6core6 \
        libqt6widgets6 libqt6gui6 \
        libqt6dbus6 >/dev/null 2>&1 || return 1
    
    return 0
}

# Main function
main() {
    local mode="${1:-auto}"
    
    case "$mode" in
        "test-only")
            test_qt_platform >/dev/null 2>&1
            ;;
        "fix-only")
            fix_qt_xcb
            ;;
        "silent")
            if ! test_qt_platform >/dev/null 2>&1; then
                fix_qt_xcb >/dev/null 2>&1
                test_qt_platform >/dev/null 2>&1
            fi
            ;;
        "auto"|*)
            echo " Testing Qt platform..."
            if qt_result=$(test_qt_platform 2>&1); then
                if echo "$qt_result" | grep -q "SUCCESS"; then
                    echo " Qt platform plugin working"
                    return 0
                fi
            fi
            
            if echo "$qt_result" | grep -q "xcb-cursor\|xcb platform plugin\|Qt platform plugin"; then
                echo " Applying Qt XCB fix..."
                if fix_qt_xcb; then
                    if qt_result=$(test_qt_platform 2>&1) && echo "$qt_result" | grep -q "SUCCESS"; then
                        echo " Qt XCB fix successful"
                        return 0
                    fi
                fi
            fi
            
            echo " Qt issues persist"
            return 1
            ;;
    esac
}

# Execute if called directly
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
