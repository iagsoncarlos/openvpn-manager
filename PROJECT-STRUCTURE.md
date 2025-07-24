# OpenVPN Manager - Project Structure

##  Complete Structure for Development and Distribution

```
openvpn-manager/
├──   DEVELOPMENT SCRIPTS
│   ├── build.sh              # Complete .deb build with dynamic versioning
│   ├── install-dev.sh        # Development installation
│   ├── uninstall.sh          # Complete uninstallation
│   ├── version.sh            # Version management
│   └── README-DEV.md         # Development documentation
│
├──  SOURCE CODE
│   ├── main.py               # Main PyQt6 application
│   ├── config.py             # Configuration
│   ├── setup.py              # Python setup
│   ├── pyproject.toml        # Project configuration
│   └── MANIFEST.in           # File manifest
│
├──  LAUNCHER AND RESOURCES
│   ├── openvpn-manager-launcher.sh  # Launcher script
│   └── resources/
│       └── vpn.png          # Application icon
│
├──  DEBIAN PACKAGING
│   └── debian/
│       ├── control          # Package control
│       ├── rules            # Build rules
│       ├── postinst         # Post-installation script
│       ├── preinst          # Pre-installation script
│       ├── changelog        # Change history
│       ├── copyright        # License
│       ├── openvpn-manager.desktop     # Menu entry
│       ├── openvpn-manager-diagnostics.sh  # Qt XCB fix
│       └── org.example.openvpn-manager.policy  # PolicyKit
│
└──  VERSION CONTROL
    ├── .git/                # Git repository
    ├── .gitignore          # Ignored files
    └── VERSION             # Current version file
```

##  Workflow

### Version Management:
```bash
./version.sh show               # Show current version
./version.sh patch             # 0.2.0 → 0.2.1 (bug fixes)
./version.sh minor             # 0.2.0 → 0.3.0 (features)
./version.sh major             # 0.2.0 → 1.0.0 (breaking changes)
```

### For Development:
```bash
./install-dev.sh           # Setup development environment
```

### For Distribution:
```bash
./version.sh patch         # Increment version
./build.sh                 # Create .deb package with updated version
```

### For Uninstallation:
```bash
./uninstall.sh             # Complete removal and cleanup
```

##  Implemented Features

-  **Qt XCB fix integrated** in .deb package
-  **Automatic version management**
-  **Complete development environment**
-  **Automated build** with dynamic versions
-  **Complete uninstallation** with cleanup
-  **Development documentation**
-  **Git version control** configured
-  **Professional Debian packaging**

## Ready for Versioning

The project is completely organized for:
- Continuous development
- Git version control
- Automated build and distribution
- Clean installation and uninstallation
- Future maintenance and updates

All files are maintained to support the complete development cycle!
