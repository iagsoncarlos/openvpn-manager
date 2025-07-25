#  OpenVPN Manager - Development Guide

##  Complete development environment for OpenVPN Manager

###  Quick Start

```bash
# Setup development environment
./install-dev.sh

# Run application
./openvpn-manager-launcher.sh

# Build .deb package
./build.sh
```

##  Workflow

### Version Management:
```bash
./version.sh show               # Show current version
./version.sh patch             # Increment patch (0.2.0 → 0.2.1)
./version.sh minor             # Increment minor (0.2.0 → 0.3.0)
./version.sh major             # Increment major (0.2.0 → 1.0.0)
```

### For Development:
```bash
./install-dev.sh           # Setup development environment
```

### For Distribution:
```bash
./version.sh patch         # Increment version for release
./build.sh                 # Create .deb package with updated version
```

### For Uninstallation:
```bash
./uninstall.sh             # Complete removal
```

##  Project Structure

```
openvpn-manager/
├── main.py                           # Main application code
├── config.py                         # Configuration and metadata
├── version.sh                        # Version management script
├── openvpn-manager-launcher.sh       # Launch script
├── build.sh                          # Build script for distribution
├── install-dev.sh                    # Development installer
├── uninstall.sh                      # Uninstaller
├── VERSION                           # Current version file
├── pyproject.toml                    # Python configuration
├── setup.py                          # Python setup (generated by build)
├── MANIFEST.in                       # Packaging manifest
├── README-DEV.md                     # This file
├── VERSIONING-GUIDE.md               # Version management guide
├── PROJETO-ESTRUTURA.md              # Project structure overview
├── resources/                        # Application resources
│   └── vpn.png                       # Application icon
└── debian/                           # Debian packaging files
    ├── control                       # Dependencies and metadata
    ├── postinst                      # Post-installation script
    ├── rules                         # Build rules
    ├── changelog                     # Version history
    ├── copyright                     # Copyright information
    ├── compat                        # Debhelper compatibility
    ├── openvpn-manager.desktop       # Desktop file
    ├── org.example.openvpn-manager.policy  # PolicyKit policy
    └── openvpn-manager-diagnostics.sh      # Qt diagnostics script
```

##  Development Scripts

### `install-dev.sh`
- Sets up complete development environment
- Installs system dependencies
- Configures Python environment
- Creates development shortcuts
- Tests installation

### `version.sh`
- Manages project versioning
- Updates all version references automatically
- Supports semantic versioning (major.minor.patch)
- Updates: VERSION, config.py, pyproject.toml, setup.py, debian/changelog

### `build.sh`
- Creates self-contained .deb package
- Downloads and bundles PyQt6 wheels
- Includes Qt XCB fix for compatibility
- Uses current version from VERSION file
- No internet required for installation

### `uninstall.sh`
- Complete system cleanup
- Removes packages and system files
- Optional Python dependency cleanup
- Cleans desktop integration

##  Features

###  Application Features:
- PyQt6-based GUI for OpenVPN management
- Load and manage .ovpn configuration files
- Real-time connection monitoring
- Secure credential storage
- Desktop integration
- Automatic DNS management

###  Development Features:
- Automated version management
- Self-contained packaging
- Qt XCB compatibility fix
- Complete development workflow
- Professional Debian packaging

###  Distribution Features:
- No internet required for installation
- Bundled Python dependencies
- System integration (PolicyKit, desktop files)
- Automatic Qt diagnostics and fixes

##  Development Commands

```bash
# Show current version
./version.sh show

# Development setup
./install-dev.sh

# Run application directly
python3 main.py

# Run with launcher
./openvpn-manager-launcher.sh

# Create new version and build
./version.sh patch    # Increment version
./build.sh           # Build package

# Test package
sudo dpkg -i ../openvpn-manager_*.deb

# Complete removal
./uninstall.sh
```

##  Development Notes

- Always use `./version.sh` to manage versions
- Run `./install-dev.sh` after checkout for development setup
- Use `source .env` to load development environment
- Desktop shortcut available as "OpenVPN Manager (Dev)"
- Build creates completely self-contained packages

## 🐛 Troubleshooting

### Qt XCB Issues:
- Automatically handled by `openvpn-manager-diagnostics.sh`
- Included in all .deb packages
- Run manually: `/usr/share/openvpn-manager/openvpn-manager-diagnostics.sh`

### Python Dependencies:
- Use `./install-dev.sh` to fix development environment
- Use `pip3 install --user PyQt6` for manual installation
- Check with: `python3 -c "import PyQt6.QtWidgets; print('OK')"`

### Version Sync Issues:
- Use `./version.sh set X.Y.Z` to reset version
- All files updated automatically
- Check with: `./version.sh show`

---

**Ready for professional development and distribution!** 
