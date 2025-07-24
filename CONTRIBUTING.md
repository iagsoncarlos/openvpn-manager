# Contributing to OpenVPN Manager

Thank you for your interest in contributing to OpenVPN Manager! This document provides guidelines and information for contributors.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. We are committed to providing a welcoming and inspiring community for all.

## How to Contribute

### Reporting Issues

Before creating an issue, please:

1. **Search existing issues** to avoid duplicates
2. **Use the latest version** to ensure the issue hasn't been fixed
3. **Provide detailed information** including:
   - Operating system and version
   - Python version
   - PyQt6 version
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages or logs

### Suggesting Features

We welcome feature suggestions! Please:

1. **Check existing feature requests** first
2. **Describe the use case** clearly
3. **Explain the expected behavior**
4. **Consider implementation complexity**

### Pull Requests

1. **Fork the repository** and create a feature branch
2. **Follow the development setup** instructions in [README-DEV.md](README-DEV.md)
3. **Make your changes** with clear, focused commits
4. **Test thoroughly** on your target platform
5. **Update documentation** if needed
6. **Submit a pull request** with a clear description

## Development Guidelines

### Code Style

- **Python**: Follow PEP 8 standards
- **Comments**: Use clear, concise comments for complex logic
- **Docstrings**: Document all public functions and classes
- **Naming**: Use descriptive variable and function names

### Testing

- Test your changes on multiple Linux distributions when possible
- Verify that existing functionality remains intact
- Test both GUI and command-line interfaces
- Include edge cases in your testing

### Documentation

- Update relevant documentation for any new features
- Keep README.md current with new installation or usage instructions
- Document any new dependencies or requirements
- Update version information using the version management system

## Development Environment

### Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/openvpn-manager.git
cd openvpn-manager

# Set up development environment
./install-dev.sh

# Create a feature branch
git checkout -b feature-name
```

### Version Management

Use the built-in version management system:

```bash
# Check current version
./version.sh show

# Increment version for your changes
./version.sh patch   # Bug fixes
./version.sh minor   # New features
./version.sh major   # Breaking changes
```

### Building and Testing

```bash
# Test your changes
python3 main.py

# Build package for testing
./build.sh

# Test the built package
sudo dpkg -i openvpn-manager_*.deb
```

## Commit Guidelines

### Commit Messages

Use clear, descriptive commit messages:

```
feat: add support for WireGuard configurations
fix: resolve Qt XCB compatibility issue on Ubuntu 24.04
docs: update installation instructions for Debian 12
refactor: improve connection status monitoring
```

### Commit Types

- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

## Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. Update version using `./version.sh`
2. Update CHANGELOG.md
3. Test thoroughly on target platforms
4. Build and test .deb package
5. Create release notes
6. Tag the release

## Community

### Getting Help

- **Issues**: For bug reports and feature requests
- **Discussions**: For questions and general discussion
- **Email**: Contact the maintainer directly for sensitive issues

### Recognition

Contributors will be recognized in:

- README.md acknowledgments
- Release notes
- Git commit history

## Project Structure

Understanding the codebase:

```
├── main.py              # Main application entry point
├── config.py           # Configuration and metadata
├── version.sh          # Version management
├── build.sh           # Build and packaging
├── install-dev.sh     # Development setup
├── uninstall.sh       # Clean removal
├── debian/            # Debian packaging
├── resources/         # Application resources
└── docs/             # Documentation
```

## Quality Standards

### Code Quality

- Write clean, readable code
- Follow established patterns in the codebase
- Minimize external dependencies
- Handle errors gracefully

### User Experience

- Maintain consistent UI/UX
- Provide clear error messages
- Ensure accessibility
- Test on various screen resolutions

### Performance

- Optimize for responsiveness
- Minimize memory usage
- Handle large configuration files efficiently
- Test with multiple concurrent connections

## License

By contributing to OpenVPN Manager, you agree that your contributions will be licensed under the MIT License.

## Questions?

If you have questions about contributing, please:

1. Check existing documentation
2. Search closed issues and discussions
3. Open a new discussion for general questions
4. Contact the maintainers directly if needed

Thank you for contributing to OpenVPN Manager!
