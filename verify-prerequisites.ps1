# Prerequisites Verification Script
# Run this to check if all required software is installed

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host " Prerequisites Verification" -ForegroundColor Cyan
Write-Host ("=" * 70) -ForegroundColor Cyan

$prerequisites = @{
    "Python"         = "python --version"
    "pip"            = "pip --version"
    "Node.js"        = "node --version"
    "npm"            = "npm --version"
    "Docker"         = "docker --version"
    "Docker Compose" = "docker-compose --version"
    "Git"            = "git --version"
}

$results = @()
$allInstalled = $true

Write-Host "`nChecking installed software...`n"

foreach ($prereq in $prerequisites.GetEnumerator()) {
    $prereqName = $prereq.Key
    $command = $prereq.Value.Split()[0]
    
    try {
        $version = Invoke-Expression $prereq.Value 2>&1
        Write-Host "  \u2713 $prereqName : " -NoNewline -ForegroundColor Green
        Write-Host $version
        
        $results += [PSCustomObject]@{
            Name    = $prereqName
            Status  = "Installed"
            Version = $version
        }
    }
    catch {
        Write-Host "  \u2717 $prereqName : Not found" -ForegroundColor Red
        
        $results += [PSCustomObject]@{
            Name    = $prereqName
            Status  = "Missing"
            Version = "N/A"
        }
        
        $allInstalled = $false
    }
}

Write-Host "`n" + ("=" * 70)

if ($allInstalled) {
    Write-Host " Status: All prerequisites installed! \u2713" -ForegroundColor Green
    Write-Host ("=" * 70) -ForegroundColor Green
    
    Write-Host "`nYou're ready to start! Run:" -ForegroundColor Cyan
    Write-Host "  .\setup.ps1`n"
}
else {
    Write-Host " Status: Missing prerequisites \u2717" -ForegroundColor Red
    Write-Host ("=" * 70) -ForegroundColor Red
    
    $missing = $results | Where-Object { $_.Status -eq "Missing" }
    
    Write-Host "`nMissing software:" -ForegroundColor Yellow
    foreach ($item in $missing) {
        Write-Host "  - $($item.Name)" -ForegroundColor Yellow
    }
    
    Write-Host "`nInstallation instructions:" -ForegroundColor Cyan
    Write-Host "  See: PREREQUISITES.md"
    Write-Host "  Or visit: https://github.com/<your-repo>/cookidoo-agent/blob/main/PREREQUISITES.md`n"
    
    # Provide quick install commands
    Write-Host "Quick install (using winget):" -ForegroundColor Cyan
    
    if (($missing | Where-Object { $_.Name -eq "Python" }).Count -gt 0) {
        Write-Host "  winget install Python.Python.3.11"
    }
    if (($missing | Where-Object { $_.Name -match "Node|npm" }).Count -gt 0) {
        Write-Host "  winget install OpenJS.NodeJS.LTS"
    }
    if (($missing | Where-Object { $_.Name -match "Docker" }).Count -gt 0) {
        Write-Host "  winget install Docker.DockerDesktop"
    }
    if (($missing | Where-Object { $_.Name -eq "Git" }).Count -gt 0) {
        Write-Host "  winget install Git.Git"
    }
    
    Write-Host "`nOr download installers:" -ForegroundColor Cyan
    if (($missing | Where-Object { $_.Name -match "Node|npm" }).Count -gt 0) {
        Write-Host "  Node.js: https://nodejs.org/"
    }
    if (($missing | Where-Object { $_.Name -match "Docker" }).Count -gt 0) {
        Write-Host "  Docker: https://www.docker.com/products/docker-desktop/"
    }
    if (($missing | Where-Object { $_.Name -eq "Python" }).Count -gt 0) {
        Write-Host "  Python: https://www.python.org/downloads/"
    }
    
    Write-Host "`nAfter installation:" -ForegroundColor Yellow
    Write-Host "  1. Restart PowerShell"
    Write-Host "  2. Run this script again: .\verify-prerequisites.ps1`n"
}

Write-Host ("=" * 70)
Write-Host ""

# Export results to CSV (optional)
# $results | Export-Csv -Path "prerequisites-check.csv" -NoTypeInformation
