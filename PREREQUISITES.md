# Prerequisites Installation Guide

This guide walks you through installing all prerequisites needed for the Cookidoo Agent Assistant on Windows.

## Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Backend API and scripts |
| Node.js | 16+ | Frontend React application |
| npm | (included with Node.js) | JavaScript package manager |
| Docker Desktop | Latest | Containerization and deployment |
| Git | Latest | Version control |

## Installation Steps

### 1. Python 3.11+

#### Check if Already Installed
```powershell
python --version
```

#### Installation Options

**Option A: Microsoft Store (Easiest)**
1. Open Microsoft Store
2. Search for "Python 3.11" or "Python 3.12"
3. Click "Get" or "Install"
4. Verify: `python --version`

**Option B: python.org**
1. Visit https://www.python.org/downloads/
2. Download Python 3.11 or 3.12 for Windows
3. Run installer
   - ✅ Check "Add Python to PATH"
   - ✅ Check "Install pip"
4. Verify installation:
   ```powershell
   python --version
   pip --version
   ```

### 2. Node.js and npm

#### Check if Already Installed
```powershell
node --version
npm --version
```

#### Installation (Two Options)

**Option A: Official Installer (Recommended)**
1. Visit https://nodejs.org/
2. Download **LTS version** (Long Term Support)
   - Currently Node.js 20.x LTS
3. Run the `.msi` installer
   - Accept defaults
   - Installer includes npm automatically
4. **Restart PowerShell/Terminal**
5. Verify installation:
   ```powershell
   node --version   # Should show v20.x.x or v18.x.x
   npm --version    # Should show 10.x.x or 9.x.x
   ```

**Option B: Using winget (Windows Package Manager)**
```powershell
# Install Node.js LTS
winget install OpenJS.NodeJS.LTS

# Restart terminal, then verify
node --version
npm --version
```

**Option C: Using Chocolatey**
```powershell
# Install Chocolatey first if needed: https://chocolatey.org/install

# Install Node.js
choco install nodejs-lts -y

# Restart terminal, then verify
node --version
npm --version
```

### 3. Docker Desktop

#### Check if Already Installed
```powershell
docker --version
docker-compose --version
```

#### Installation Steps

1. **Download Docker Desktop**
   - Visit: https://www.docker.com/products/docker-desktop/
   - Click "Download for Windows"
   - File: `Docker Desktop Installer.exe`

2. **System Requirements**
   - Windows 10/11 64-bit
   - WSL 2 feature enabled (Windows Subsystem for Linux)
   - Virtualization enabled in BIOS

3. **Run Installer**
   - Double-click `Docker Desktop Installer.exe`
   - Follow installation wizard
   - ✅ Enable "Use WSL 2 instead of Hyper-V" (recommended)

4. **Enable WSL 2** (if not already enabled)
   ```powershell
   # Run as Administrator
   wsl --install
   
   # Or manually:
   dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
   dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
   
   # Set WSL 2 as default
   wsl --set-default-version 2
   
   # Restart computer
   ```

5. **Start Docker Desktop**
   - Launch Docker Desktop from Start Menu
   - Wait for Docker to start (may take 1-2 minutes)
   - Look for green "running" indicator in system tray

6. **Verify Installation**
   ```powershell
   docker --version
   docker-compose --version
   docker run hello-world
   ```

### 4. Git (Optional but Recommended)

#### Check if Already Installed
```powershell
git --version
```

#### Installation
```powershell
# Using winget
winget install Git.Git

# Or download from: https://git-scm.com/download/win
```

## Verification Script

After installing prerequisites, run this verification script:

```powershell
# Save as: verify-prerequisites.ps1

Write-Host "`n=== Prerequisites Check ===" -ForegroundColor Cyan

$prereqs = @{
    "Python" = "python --version"
    "pip" = "pip --version"
    "Node.js" = "node --version"
    "npm" = "npm --version"
    "Docker" = "docker --version"
    "Docker Compose" = "docker-compose --version"
    "Git" = "git --version"
}

$allGood = $true

foreach ($prereq in $prereqs.GetEnumerator()) {
    try {
        $version = Invoke-Expression $prereq.Value 2>&1
        Write-Host "  ✓ $($prereq.Key): " -NoNewline -ForegroundColor Green
        Write-Host $version
    }
    catch {
        Write-Host "  ✗ $($prereq.Key): Not found" -ForegroundColor Red
        $allGood = $false
    }
}

Write-Host "`n" -NoNewline

if ($allGood) {
    Write-Host "All prerequisites installed! ✓" -ForegroundColor Green
    Write-Host "You can now run: .\setup.ps1" -ForegroundColor Cyan
}
else {
    Write-Host "Please install missing prerequisites." -ForegroundColor Yellow
    Write-Host "See: PREREQUISITES.md for installation instructions" -ForegroundColor Cyan
}
```

Run it:
```powershell
.\verify-prerequisites.ps1
```

## Troubleshooting

### Python Issues

**Problem**: `python: command not found`

**Solution**:
1. Reinstall Python with "Add to PATH" checked
2. Or manually add Python to PATH:
   ```powershell
   # Find Python installation
   $pythonPath = "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311"
   
   # Add to PATH (current session)
   $env:Path += ";$pythonPath;$pythonPath\Scripts"
   
   # Add permanently (requires restart)
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";$pythonPath;$pythonPath\Scripts", "User")
   ```

### Node.js/npm Issues

**Problem**: `node: command not found` after installation

**Solution**:
1. **Restart PowerShell/Terminal** (most common fix)
2. Verify Node.js installation location:
   ```powershell
   Get-Command node
   ```
3. If not found, check installation directory:
   - Default: `C:\Program Files\nodejs\`
4. Add to PATH if needed:
   ```powershell
   $nodePath = "C:\Program Files\nodejs"
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";$nodePath", "User")
   ```

**Problem**: npm permission errors

**Solution**:
```powershell
# Fix npm global directory
npm config set prefix "$env:APPDATA\npm"

# Add to PATH
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$env:APPDATA\npm", "User")
```

### Docker Issues

**Problem**: "Docker daemon is not running"

**Solution**:
1. Start Docker Desktop from Start Menu
2. Wait for green indicator in system tray
3. If fails to start:
   - Enable virtualization in BIOS
   - Ensure WSL 2 is installed
   - Restart computer

**Problem**: "WSL 2 installation is incomplete"

**Solution**:
```powershell
# Run as Administrator
wsl --install
wsl --update

# Download WSL 2 kernel update:
# https://aka.ms/wsl2kernel

# Restart computer
```

**Problem**: Docker Desktop won't start on Windows 11

**Solution**:
1. Open Docker Desktop settings
2. General → Enable "Use the WSL 2 based engine"
3. Resources → WSL Integration → Enable integration with default WSL distro
4. Restart Docker Desktop

### General PATH Issues

If commands still not found after installation:

```powershell
# View current PATH
$env:Path -split ';'

# Reload environment variables
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Or simply restart PowerShell
```

## Quick Install (All Prerequisites)

If you have **winget** (Windows Package Manager), install everything at once:

```powershell
# Install all prerequisites
winget install Python.Python.3.11
winget install OpenJS.NodeJS.LTS
winget install Docker.DockerDesktop
winget install Git.Git

# Restart terminal
exit

# New terminal - verify
python --version
node --version
npm --version
docker --version
```

## After Installation

Once all prerequisites are installed:

1. **Restart PowerShell/Terminal**
2. **Verify installations**:
   ```powershell
   python --version
   node --version
   npm --version
   docker --version
   ```
3. **Run the setup script**:
   ```powershell
   .\setup.ps1
   ```

## Additional Tools (Optional)

### Visual Studio Code
```powershell
winget install Microsoft.VisualStudioCode
```

### Azure CLI (for Azure Key Vault)
```powershell
winget install Microsoft.AzureCLI
```

### Databricks CLI
```powershell
pip install databricks-cli
```

## System Requirements

### Minimum
- Windows 10/11 64-bit
- 8GB RAM
- 10GB free disk space
- Internet connection

### Recommended
- Windows 11 64-bit
- 16GB RAM
- 20GB free disk space
- SSD storage

## Next Steps

After installing all prerequisites:

1. ✅ Run `.\setup.ps1` to set up the project
2. ✅ Follow setup option 1 (Full setup) or 2 (Docker)
3. ✅ See [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for detailed project information
4. ✅ See [docs/COOKIDOO_MCP_INTEGRATION.md](docs/COOKIDOO_MCP_INTEGRATION.md) for Cookidoo setup

## Support

If you encounter issues not covered here:

1. Check error messages carefully
2. Google the specific error
3. Check Stack Overflow
4. Ensure Windows is up to date
5. Try running PowerShell as Administrator

---

**Last Updated**: December 23, 2025  
**For**: Windows 10/11 PowerShell
