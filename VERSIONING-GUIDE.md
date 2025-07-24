#  Version Management Quick Guide

## How to use the complete versioning system

### 1.  Check current version
```bash
./version.sh show
```

### 2.  Local development
```bash
./install-dev.sh           # Install for development
```

### 3.  Create new version and build
```bash
# For bug fixes:
./version.sh patch         # 0.2.0 → 0.2.1
./build.sh                 # Build with v0.2.1

# For new features:
./version.sh minor         # 0.2.0 → 0.3.0
./build.sh                 # Build with v0.3.0

# For breaking changes:
./version.sh major         # 0.2.0 → 1.0.0
./build.sh                 # Build with v1.0.0
```

### 4.  Specific version
```bash
./version.sh set 1.2.3     # Set specific version
./build.sh                 # Build with v1.2.3
```

### 5.  Uninstall
```bash
./uninstall.sh             # Remove completely
```

##  Files updated automatically:
- `VERSION` - Central version file
- `config.py` - APP_VERSION of the application
- `pyproject.toml` - Python project version
- `setup.py` - setup version
- `debian/changelog` - Changelog entry

##  Result:
- Build always uses correct version from VERSION file
- All files stay synchronized
- Simplified release process
- Full control over versioning
