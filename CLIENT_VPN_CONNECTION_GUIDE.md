# AWS Client VPN Connection Guide

This guide helps colleagues connect to the company's AWS Client VPN.

## Prerequisites

- VPN configuration file (grupp-vpn.ovpn) provided by IT admin
- OpenVPN client software
- Authentication credentials (depends on your company's setup):
  - **IAM Authentication**: Your AWS IAM username/password
  - **Certificate Authentication**: Embedded in .ovpn file (no additional credentials needed)

## Step 1: Install OpenVPN Client

### Windows
1. Download [OpenVPN Connect](https://openvpn.net/client-connect-vpn-for-windows/)
2. Install and run as administrator
3. Import your .ovpn configuration file

### macOS
1. Download [Tunnelblick](https://tunnelblick.net/) or [OpenVPN Connect](https://openvpn.net/client-connect-vpn-for-mac-os/)
2. Install the application
3. Import your .ovpn configuration file

### Linux
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install openvpn

# CentOS/RHEL
sudo yum install openvpn
```

### Mobile Devices

#### iOS (iPhone/iPad)
1. Download **OpenVPN Connect** from App Store
2. Install the app
3. Transfer grupp-vpn.ovpn file to your device via:
   - Email attachment
   - AirDrop from Mac
   - Cloud storage (iCloud, Dropbox)
4. Open the .ovpn file with OpenVPN Connect

#### Android
1. Download **OpenVPN Connect** from Google Play Store
2. Install the app
3. Transfer grupp-vpn.ovpn file to your device via:
   - Email attachment
   - Google Drive, Dropbox, or other cloud storage
   - USB transfer from computer
4. Open the .ovpn file with OpenVPN Connect

## Step 2: Get Your VPN Configuration

Contact your IT administrator to receive:
- **Configuration file** (grupp-vpn.ovpn) - Shared configuration for all users
- **Authentication method** - Your company uses one of these:
  - **IAM Authentication**: Your AWS IAM username and password
  - **Certificate Authentication**: No additional credentials (certificates embedded in .ovpn file)
- **Connection instructions** specific to your setup

## Step 3: Connect to VPN

### Using OpenVPN Connect (Windows/macOS)
1. Open OpenVPN Connect
2. Click "Import Profile"
3. Select the grupp-vpn.ovpn file
4. **For IAM Authentication**: Enter your IAM username and password when prompted
   **For Certificate Authentication**: No credentials needed (auto-connect)
5. Click "Connect"

### Using Command Line (Linux)
```bash
sudo openvpn --config /path/to/your-config.ovpn
```

### Using Tunnelblick (macOS)
1. Double-click your .ovpn file
2. Tunnelblick will import it automatically
3. Click the Tunnelblick icon in menu bar
4. Select your VPN connection
5. Enter credentials and connect

### Using OpenVPN Connect (Mobile)

#### iOS (iPhone/iPad)
1. Open OpenVPN Connect app
2. Tap the "+" button to add profile
3. Select "File" tab
4. Browse and select your grupp-vpn.ovpn file
5. Tap "Add" to import the profile
6. Tap the toggle switch to connect
7. **For IAM Authentication**: Enter your IAM credentials when prompted
   **For Certificate Authentication**: Connection starts automatically
8. Allow VPN configuration when iOS prompts

#### Android
1. Open OpenVPN Connect app
2. Tap the "+" button or "Import Profile"
3. Select "File" and browse to your grupp-vpn.ovpn file
4. Tap "Import" to add the profile
5. Tap the profile name to connect
6. **For IAM Authentication**: Enter your IAM credentials when prompted
   **For Certificate Authentication**: Connection starts automatically
7. Allow VPN permissions when Android prompts

## Step 4: Verify Connection

Once connected, verify your VPN is working:

1. **Check IP Address:**
   - Visit [whatismyipaddress.com](https://whatismyipaddress.com)
   - Your IP should show the company's VPN IP range

2. **Test Internal Resources:**
   - Try accessing internal company systems
   - Ping internal servers (if permitted)

3. **Check DNS Resolution:**
   ```bash
   nslookup internal.company.com
   ```

4. **Mobile Verification:**
   - **iOS**: Check VPN status in Settings > General > VPN & Device Management
   - **Android**: Look for VPN key icon in status bar
   - Test accessing internal company websites in mobile browser

## Troubleshooting

### Common Issues

**Connection Fails:**
- Check internet connection
- Verify grupp-vpn.ovpn file is correct
- **For IAM Authentication**: 
  - Ensure your IAM credentials are accurate
  - Verify you're in the VPN-Users IAM group
- **For Certificate Authentication**: 
  - Ensure certificates are properly embedded in .ovpn file
  - Contact IT if certificate has expired

**Slow Connection:**
- Try different VPN server locations
- Check if split tunneling is enabled
- Contact IT for server status

**Can't Access Internal Resources:**
- Verify VPN is connected (check IP address)
- Check if you have proper permissions
- Ensure internal DNS is working

**Authentication Errors:**
- **For IAM Authentication**:
  - Verify your IAM username and password
  - Check if you're in the VPN-Users group
  - Contact IT if your account is locked
- **For Certificate Authentication**:
  - Verify .ovpn file contains valid certificates
  - Check if certificates have expired
  - Contact IT for new certificate if needed

**Mobile-Specific Issues:**
- **iOS**: Go to Settings > General > VPN & Device Management to check VPN status
- **Android**: Check VPN settings in Settings > Network & Internet > VPN
- **Battery Optimization**: Disable battery optimization for OpenVPN Connect app
- **Background App Refresh**: Enable background refresh for OpenVPN Connect (iOS)
- **File Transfer Issues**: Try different methods (email, cloud storage, AirDrop)

### Getting Help

1. **Check VPN Status:** Ensure connection shows "Connected"
2. **Review Logs:** Check OpenVPN logs for error messages
3. **Contact IT Support:** Provide error messages and connection logs

## Security Best Practices

- **Always disconnect** when not using company resources
- **Don't share** your IAM credentials or VPN configuration file
- **Use strong passwords** for VPN authentication
- **Keep software updated** (OpenVPN client)
- **Report issues** immediately to IT security team
- **Mobile Security**: 
  - Lock your device with PIN/password/biometric
  - Don't save VPN credentials on shared devices
  - Disconnect VPN when using public Wi-Fi is not needed
  - Enable auto-lock on your mobile device

## Quick Reference Commands

### Check Connection Status
```bash
# Windows
ipconfig /all

# macOS/Linux
ifconfig
ip addr show
```

### Test Connectivity
```bash
# Ping VPN gateway
ping <vpn-gateway-ip>

# Test DNS resolution
nslookup <internal-domain>

# Check routing table
route -n  # Linux/macOS
route print  # Windows
```

## Contact Information

**IT Support:**
**VPN Issues:** 
**Emergency:** 

---

