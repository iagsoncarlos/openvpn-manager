# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| < 0.2   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in OpenVPN Manager, please report it responsibly:

### How to Report

1. **Do NOT** create a public GitHub issue for security vulnerabilities
2. Send an email to: **iagsoncarlos@gmail.com**
3. Include in your report:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Response Time**: Within 48 hours
- **Updates**: Every 72 hours until resolved
- **Credit**: Security researchers will be credited in the changelog (unless they prefer to remain anonymous)

### Security Best Practices for Users

When using OpenVPN Manager:

1. **VPN Configurations**: 
   - Store `.ovpn` files in secure locations (`~/.config/openvpn-manager/`)
   - Use strong authentication (certificates + passwords)
   - Regularly update VPN configurations

2. **System Security**:
   - Keep the application updated
   - Use strong sudo passwords
   - Regularly review active VPN connections

3. **File Permissions**:
   - VPN configuration files should have restricted permissions (600)
   - Certificate files should be readable only by owner

### Known Security Considerations

- Application requires sudo privileges for VPN management
- Credentials are handled via secure system dialogs (zenity/kdialog)
- No credentials are stored permanently by the application
- All VPN operations use standard OpenVPN client tools

## Encryption and Data Handling

- **Credentials**: Handled via OS-level secure input dialogs
- **VPN Traffic**: Encrypted by OpenVPN (application doesn't modify encryption)
- **Configuration Storage**: Plain text (follows OpenVPN standard practices)
- **Logs**: Application logs do not contain sensitive information

## Dependencies Security

This application relies on:
- OpenVPN client (system package)
- PyQt6 (GUI framework)
- Standard Linux utilities (systemctl, pkexec)

Keep all dependencies updated through your system package manager.

---

**Last Updated**: July 2025
**Contact**: iagsoncarlos@gmail.com
