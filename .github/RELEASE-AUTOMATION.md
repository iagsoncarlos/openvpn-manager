# GitHub Actions for Release and Version Management

This repository includes two GitHub Actions workflows to automate release creation and version management:

## 🚀 Workflows Overview

### 1. Create Release (`release.yml`)
**Manually triggered workflow** for creating releases with automatic version bumping and artifact building.

#### Features:
- ✅ Automatic version incrementation (patch/minor/major)
- ✅ Custom version setting
- ✅ Automatic CHANGELOG.md updates
- ✅ Builds .deb packages, wheels, and source distributions
- ✅ Creates GitHub releases with artifacts
- ✅ Git tagging
- ✅ Pre-release support
- ✅ Comprehensive build summaries

#### How to Use:
1. Go to **Actions** tab in your GitHub repository
2. Select **"Create Release"** workflow
3. Click **"Run workflow"**
4. Choose your options:
   - **Version type**: `patch`, `minor`, or `major`
   - **Custom version**: Optional (overrides version type)
   - **Pre-release**: Check if this is a beta/alpha release

### 2. Simple Auto Version (`simple-auto-version.yml`)
**Automatically triggered** when Pull Requests are merged to automatically bump patch versions.

#### Features:
- ✅ Automatically increments patch version on PR merge
- ✅ Updates all version files (VERSION, config.py, pyproject.toml, setup.py)
- ✅ Smart detection to avoid version bump loops
- ✅ No manual intervention required

## 📋 Prerequisites

### Repository Setup:
1. **VERSION file**: Must exist in repository root
2. **version.sh script**: Must be executable and working
3. **Proper file structure**: The workflows expect your existing project structure

### GitHub Settings:
1. **Actions must be enabled** in repository settings
2. **Write permissions**: Workflows need `contents: write` permission
3. **GITHUB_TOKEN**: Automatically available, no setup needed

## 🏗️ Project Integration

### Your Existing Tools:
These workflows integrate with your existing version management:

- **`version.sh`**: Used for version incrementation
- **`build.sh`**: Used for building packages
- **`VERSION` file**: Source of truth for current version
- **`pyproject.toml`**: Updated automatically
- **`config.py`**: Updated automatically
- **`setup.py`**: Updated automatically
- **`CHANGELOG.md`**: Updated automatically

## 🎯 Usage Examples

### Example 1: Patch Release (Bug Fixes)
```
1. Merge bug fix PR → Simple Auto Version runs → Version goes from 0.2.0 to 0.2.1
2. Go to Actions → Run "Create Release" → Select "patch" → Creates v0.2.1 release
```

### Example 2: Minor Release (New Features)
```
1. Go to Actions → Run "Create Release"
2. Select "minor" → Version goes from 0.2.1 to 0.3.0
3. Release v0.3.0 is created with all artifacts
```

### Example 3: Major Release (Breaking Changes)
```
1. Go to Actions → Run "Create Release"
2. Select "major" → Version goes from 0.3.0 to 1.0.0
3. Release v1.0.0 is created
```

### Example 4: Custom Version
```
1. Go to Actions → Run "Create Release"
2. Enter custom version: "2.0.0-beta.1"
3. Check "Pre-release" → Creates v2.0.0-beta.1 pre-release
```

## 📁 Generated Artifacts

Each release creates the following artifacts:
- ** `.whl` file**: Python wheel for pip installation (always created)
- **📄 `.tar.gz`**: Source distribution (always created)
- **� `.deb` package**: Ready for Debian/Ubuntu installation (created when build environment supports it)
- **�📋 Release notes**: Auto-generated from CHANGELOG.md

**Note**: The .deb package creation depends on the build environment having full Debian build tools. In GitHub Actions, you'll always get the Python wheel and source distribution, which cover most installation needs.

## 🔧 Customization Options

### Disable Auto-Versioning:
Add these labels to PRs to skip automatic version bumps:
- `no-release`
- `skip-release`

### Version Type Detection:
The auto-version workflow analyzes PR labels and titles:
- **Major**: `breaking`, `major` labels or keywords
- **Minor**: `feature`, `minor` labels or keywords  
- **Patch**: Default for all other changes

### Custom Changelog:
The workflows automatically update `CHANGELOG.md`. To customize:
1. Edit the changelog sections in the workflow files
2. Or manually edit `CHANGELOG.md` before running releases

## 🚨 Important Notes

### Version Bump Loop Prevention:
- Auto-version workflow skips commits with "chore: bump version" in title
- This prevents infinite loops of version updates

### File Dependencies:
- Ensure `version.sh` has execute permissions: `chmod +x version.sh`
- Ensure `build.sh` has execute permissions: `chmod +x build.sh`
- All version-related files must exist and be properly formatted

### Release Branch Strategy:
- Workflows are configured for `main` branch
- Auto-version only triggers on PR merges to `main`
- To use different branch, edit the workflow files

## 🔍 Troubleshooting

### Common Issues:

1. **"version.sh not found"**
   - Ensure script exists and is executable
   - Check file permissions

2. **"Build failed"**
   - Check `build.sh` script compatibility
   - Ensure all dependencies are available in workflow

3. **"Git push failed"**
   - Check repository permissions
   - Ensure GITHUB_TOKEN has write access

4. **"Version not updated"**
   - Check if PR has `no-release` label
   - Verify `version.sh` script works locally

### Getting Help:

1. Check the **Actions** tab for detailed logs
2. Each workflow provides comprehensive step summaries
3. Review the generated artifacts in **Releases** section

## 🎉 Benefits

- **⚡ Faster Releases**: No manual version management
- **🔄 Consistency**: Same process every time
- **📊 Tracking**: Full audit trail in git history
- **🐛 Fewer Errors**: Automated updates reduce mistakes
- **📋 Documentation**: Auto-generated changelogs and release notes
- **📦 Ready Artifacts**: Immediately installable packages

Your release process is now fully automated! 🚀
