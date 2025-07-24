#!/bin/bash

# GitHub Repository Setup Script for Release Automation
# This script helps set up labels and other configurations for the release workflows

set -e

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

# Check if GitHub CLI is installed
check_gh_cli() {
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI (gh) is not installed"
        log_info "Install it from: https://cli.github.com/"
        exit 1
    fi
    
    # Check if authenticated
    if ! gh auth status &> /dev/null; then
        log_error "GitHub CLI is not authenticated"
        log_info "Run: gh auth login"
        exit 1
    fi
    
    log_success "GitHub CLI is ready"
}

# Function to create labels
create_labels() {
    log_info "Creating GitHub labels for release automation..."
    
    # Read labels from JSON file
    if [ ! -f ".github/labels.json" ]; then
        log_error "Labels file not found: .github/labels.json"
        exit 1
    fi
    
    # Create each label
    while IFS= read -r label_data; do
        if [[ "$label_data" =~ \"name\":\ \"([^\"]+)\" ]]; then
            name="${BASH_REMATCH[1]}"
            
            if [[ "$label_data" =~ \"color\":\ \"([^\"]+)\" ]]; then
                color="${BASH_REMATCH[1]}"
                
                if [[ "$label_data" =~ \"description\":\ \"([^\"]+)\" ]]; then
                    description="${BASH_REMATCH[1]}"
                    
                    # Try to create the label
                    if gh label create "$name" --color "$color" --description "$description" 2>/dev/null; then
                        log_success "Created label: $name"
                    else
                        # Label might already exist, try to update it
                        if gh label edit "$name" --color "$color" --description "$description" 2>/dev/null; then
                            log_warning "Updated existing label: $name"
                        else
                            log_error "Failed to create/update label: $name"
                        fi
                    fi
                fi
            fi
        fi
    done < .github/labels.json
}

# Function to check workflow files
check_workflows() {
    log_info "Checking workflow files..."
    
    WORKFLOWS=(
        ".github/workflows/release.yml"
        ".github/workflows/simple-auto-version.yml"
        ".github/workflows/validate-release.yml"
    )
    
    for workflow in "${WORKFLOWS[@]}"; do
        if [ -f "$workflow" ]; then
            log_success "Found: $workflow"
        else
            log_error "Missing: $workflow"
        fi
    done
}

# Function to check project files
check_project_files() {
    log_info "Checking project files..."
    
    REQUIRED_FILES=(
        "VERSION"
        "version.sh"
        "build.sh"
        "config.py"
        "pyproject.toml"
        "setup.py"
        "CHANGELOG.md"
    )
    
    for file in "${REQUIRED_FILES[@]}"; do
        if [ -f "$file" ]; then
            log_success "Found: $file"
        else
            log_warning "Missing: $file"
        fi
    done
    
    # Check if scripts are executable
    if [ -f "version.sh" ]; then
        if [ -x "version.sh" ]; then
            log_success "version.sh is executable"
        else
            log_warning "version.sh is not executable - fixing..."
            chmod +x version.sh
            log_success "Fixed version.sh permissions"
        fi
    fi
    
    if [ -f "build.sh" ]; then
        if [ -x "build.sh" ]; then
            log_success "build.sh is executable"
        else
            log_warning "build.sh is not executable - fixing..."
            chmod +x build.sh
            log_success "Fixed build.sh permissions"
        fi
    fi
}

# Function to test version script
test_version_script() {
    log_info "Testing version script..."
    
    if [ -f "version.sh" ] && [ -x "version.sh" ]; then
        CURRENT_VERSION=$(./version.sh show 2>/dev/null || echo "unknown")
        log_success "Current version: $CURRENT_VERSION"
        
        # Test version validation
        if ./version.sh help >/dev/null 2>&1; then
            log_success "version.sh help command works"
        else
            log_warning "version.sh help command failed"
        fi
    else
        log_error "version.sh not found or not executable"
    fi
}

# Function to show setup summary
show_summary() {
    log_info "Setup Summary:"
    echo ""
    echo "✅ GitHub Actions workflows created:"
    echo "   • release.yml - Manual release creation"
    echo "   • simple-auto-version.yml - Automatic version bumping"
    echo "   • validate-release.yml - Release validation"
    echo ""
    echo "✅ Documentation created:"
    echo "   • .github/RELEASE-AUTOMATION.md - Complete usage guide"
    echo ""
    echo "✅ Labels configured for version management:"
    echo "   • major, minor, patch - Version increment types"
    echo "   • feature, bugfix, breaking - Automatic detection"
    echo "   • no-release, skip-release - Skip auto-versioning"
    echo ""
    echo "🎯 Next Steps:"
    echo "1. Push these changes to GitHub"
    echo "2. Go to Actions tab to see available workflows"
    echo "3. Create a test PR to see auto-versioning in action"
    echo "4. Run 'Create Release' workflow to make your first automated release"
    echo ""
    echo "📚 For detailed instructions, see:"
    echo "   .github/RELEASE-AUTOMATION.md"
    echo ""
}

# Main function
main() {
    echo "=========================================="
    echo "  GitHub Release Automation Setup"
    echo "=========================================="
    echo ""
    
    # Check prerequisites
    check_gh_cli
    
    # Check project structure
    check_project_files
    check_workflows
    
    # Test tools
    test_version_script
    
    # Create GitHub labels
    create_labels
    
    # Show summary
    echo ""
    log_success "Setup completed successfully!"
    echo ""
    show_summary
}

# Execute main function
main "$@"
