#!/bin/bash

# OpenVPN Manager - Version Manager
# Manages version updates across all project files

set -e

VERSION_FILE="VERSION"
DEFAULT_VERSION="0.2.0"

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

# Function to get current version
get_current_version() {
    if [ -f "$VERSION_FILE" ]; then
        cat "$VERSION_FILE"
    else
        echo "$DEFAULT_VERSION"
    fi
}

# Function to validate version format (semantic versioning)
validate_version() {
    local version="$1"
    if [[ $version =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9]+)?$ ]]; then
        return 0
    else
        return 1
    fi
}

# Function to update version in all files
update_version_in_files() {
    local old_version="$1"
    local new_version="$2"
    
    log_info "Updating version from $old_version to $new_version..."
    
    # Update config.py
    if [ -f "config.py" ]; then
        sed -i "s/APP_VERSION = \"$old_version\"/APP_VERSION = \"$new_version\"/" config.py
        log_success "config.py updated"
    fi
    
    # Update pyproject.toml
    if [ -f "pyproject.toml" ]; then
        sed -i "s/version = \"$old_version\"/version = \"$new_version\"/" pyproject.toml
        log_success "pyproject.toml updated"
    fi
    
    # Update setup.py
    if [ -f "setup.py" ]; then
        sed -i "s/VERSION = \"$old_version\"/VERSION = \"$new_version\"/" setup.py
        log_success "setup.py updated"
    fi
    
    # Update debian/changelog
    if [ -f "debian/changelog" ]; then
        # Create new changelog entry
        local temp_changelog=$(mktemp)
        local current_date=$(date -R)
        
        # Ensure we're using the current year (not future dates)
        local current_year=$(date +%Y)
        current_date=$(date -R | sed "s/[0-9]\{4\}/$current_year/")
        
        echo "openvpn-manager ($new_version-1) unstable; urgency=medium" > "$temp_changelog"
        echo "" >> "$temp_changelog"
        echo "  * Version bump to $new_version" >> "$temp_changelog"
        echo "" >> "$temp_changelog"
        echo " -- Iágson Carlos Lima Silva <iagsoncarlos@gmail.com>  $current_date" >> "$temp_changelog"
        echo "" >> "$temp_changelog"
        cat "debian/changelog" >> "$temp_changelog"
        mv "$temp_changelog" "debian/changelog"
        log_success "debian/changelog updated"
    fi
    
    # Update VERSION file
    echo "$new_version" > "$VERSION_FILE"
    log_success "VERSION file updated"
}

# Function to increment version
increment_version() {
    local version="$1"
    local part="$2"  # major, minor, patch
    
    local major=$(echo "$version" | cut -d. -f1)
    local minor=$(echo "$version" | cut -d. -f2)
    local patch=$(echo "$version" | cut -d. -f3 | cut -d- -f1)
    
    case "$part" in
        "major")
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        "minor")
            minor=$((minor + 1))
            patch=0
            ;;
        "patch")
            patch=$((patch + 1))
            ;;
        *)
            log_error "Invalid increment type: $part"
            return 1
            ;;
    esac
    
    echo "$major.$minor.$patch"
}

# Main function
main() {
    local action="$1"
    local version_arg="$2"
    
    local current_version=$(get_current_version)
    
    case "$action" in
        "show"|"current"|"")
            echo "Current version: $current_version"
            ;;
        "set")
            if [ -z "$version_arg" ]; then
                log_error "Version not specified"
                echo "Usage: $0 set <version>"
                exit 1
            fi
            
            if ! validate_version "$version_arg"; then
                log_error "Invalid version format: $version_arg"
                echo "Use semantic format: X.Y.Z (e.g.: 1.0.0)"
                exit 1
            fi
            
            update_version_in_files "$current_version" "$version_arg"
            log_success "Version updated to $version_arg"
            ;;
        "patch"|"minor"|"major")
            local new_version=$(increment_version "$current_version" "$action")
            update_version_in_files "$current_version" "$new_version"
            log_success "Version incremented ($action): $current_version → $new_version"
            ;;
        "help"|"-h"|"--help")
            cat << 'EOF'
OpenVPN Manager - Version Manager

Usage:
  ./version.sh [command] [arguments]

Commands:
  show, current, (empty)  Show current version
  set <version>          Set specific version (e.g.: 1.2.3)
  patch                  Increment patch version (0.2.0 → 0.2.1)
  minor                  Increment minor version (0.2.0 → 0.3.0)
  major                  Increment major version (0.2.0 → 1.0.0)
  help, -h, --help       Show this help

Examples:
  ./version.sh show               # Show current version
  ./version.sh set 1.0.0         # Set version to 1.0.0
  ./version.sh patch             # 0.2.0 → 0.2.1
  ./version.sh minor             # 0.2.0 → 0.3.0
  ./version.sh major             # 0.2.0 → 1.0.0

Files updated automatically:
  - VERSION
  - config.py
  - pyproject.toml
  - setup.py
  - debian/changelog
EOF
            ;;
        *)
            log_error "Unknown command: $action"
            echo "Use '$0 help' to see available commands"
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"
