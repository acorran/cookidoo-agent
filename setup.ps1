# Quick Start Script for Cookidoo Agent Assistant
# This script helps set up and run the application locally

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 68) -ForegroundColor Cyan
Write-Host " Cookidoo Agent Assistant - Quick Start" -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan

Write-Host "`nThis script will help you set up and run the application.`n"

# Function to check if command exists
function Test-Command($command) {
    $null = Get-Command $command -ErrorAction SilentlyContinue
    return $?
}

# Check prerequisites
Write-Host "[1/5] Checking prerequisites..." -ForegroundColor Yellow

$prerequisites = @{
    "Python"  = "python --version"
    "Node.js" = "node --version"
    "npm"     = "npm --version"
    "Docker"  = "docker --version"
}

$missingPrereqs = @()

foreach ($prereq in $prerequisites.GetEnumerator()) {
    $cmd = $prereq.Value.Split()[0]
    if (Test-Command $cmd) {
        $version = Invoke-Expression $prereq.Value 2>$null
        Write-Host "  ✓ $($prereq.Key): $version" -ForegroundColor Green
    }
    else {
        Write-Host "  ✗ $($prereq.Key): Not found" -ForegroundColor Red
        $missingPrereqs += $prereq.Key
    }
}

if ($missingPrereqs.Count -gt 0) {
    Write-Host "`n Missing prerequisites: $($missingPrereqs -join ', ')" -ForegroundColor Red
    Write-Host "`nInstallation Guide:" -ForegroundColor Yellow
    Write-Host "  See PREREQUISITES.md for detailed installation instructions`n" -ForegroundColor Cyan
    
    Write-Host "Quick Install Commands:" -ForegroundColor Yellow
    if ($missingPrereqs -contains 'Node.js' -or $missingPrereqs -contains 'npm') {
        Write-Host "  Node.js (includes npm):" -ForegroundColor Cyan
        Write-Host "    Download: https://nodejs.org/ (Choose LTS version)"
        Write-Host "    Or run:   winget install OpenJS.NodeJS.LTS"
    }
    if ($missingPrereqs -contains 'Docker') {
        Write-Host "  Docker Desktop:" -ForegroundColor Cyan
        Write-Host "    Download: https://www.docker.com/products/docker-desktop/"
        Write-Host "    Or run:   winget install Docker.DockerDesktop"
    }
    if ($missingPrereqs -contains 'Python') {
        Write-Host "  Python 3.11+:" -ForegroundColor Cyan
        Write-Host "    Download: https://www.python.org/downloads/"
        Write-Host "    Or run:   winget install Python.Python.3.11"
    }
    
    Write-Host "`nAfter installation:" -ForegroundColor Yellow
    Write-Host "  1. Restart PowerShell/Terminal"
    Write-Host "  2. Run this script again: .\setup.ps1`n"
    
    $openDocs = Read-Host "Open PREREQUISITES.md in browser? (Y/N)"
    if ($openDocs -eq 'Y' -or $openDocs -eq 'y') {
        Start-Process "PREREQUISITES.md"
    }
    
    exit 1
}

# Setup options
Write-Host "`n[2/5] Choose setup option:" -ForegroundColor Yellow
Write-Host "  1. Full setup (Backend + Frontend + MCP Server)"
Write-Host "  2. Docker setup (Recommended for production)"
Write-Host "  3. Backend only"
Write-Host "  4. Frontend only"
Write-Host "  5. Exit"

$choice = Read-Host "`nEnter your choice (1-5)"

switch ($choice) {
    "1" {
        Write-Host "`n[3/5] Setting up Backend..." -ForegroundColor Yellow
        Set-Location backend
        
        if (!(Test-Path "venv")) {
            Write-Host "Creating Python virtual environment..." -ForegroundColor Cyan
            python -m venv venv
        }
        
        Write-Host "Activating virtual environment..." -ForegroundColor Cyan
        .\venv\Scripts\Activate.ps1
        
        Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
        pip install -r requirements.txt
        
        if (!(Test-Path ".env")) {
            Write-Host "Creating .env file from template..." -ForegroundColor Cyan
            Copy-Item .env.example .env
            Write-Host "Please edit backend/.env with your configuration" -ForegroundColor Yellow
        }
        
        Set-Location ..
        
        Write-Host "`n[4/5] Setting up Frontend..." -ForegroundColor Yellow
        Set-Location frontend
        
        Write-Host "Installing npm dependencies..." -ForegroundColor Cyan
        npm install
        
        if (!(Test-Path ".env")) {
            Write-Host "Creating .env file from template..." -ForegroundColor Cyan
            Copy-Item .env.example .env
        }
        
        Set-Location ..
        
        Write-Host "`n[5/5] Setting up MCP Server..." -ForegroundColor Yellow
        Set-Location mcp-server
        
        if (!(Test-Path "venv")) {
            Write-Host "Creating Python virtual environment..." -ForegroundColor Cyan
            python -m venv venv
        }
        
        Write-Host "Activating virtual environment..." -ForegroundColor Cyan
        .\venv\Scripts\Activate.ps1
        
        Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
        pip install -r requirements.txt
        
        Set-Location ..
        
        Write-Host "`n" + ("=" * 69) -ForegroundColor Green
        Write-Host " Setup Complete!" -ForegroundColor Green
        Write-Host ("=" * 69) -ForegroundColor Green
        
        Write-Host "`nTo start the application:`n"
        Write-Host "1. Backend:" -ForegroundColor Cyan
        Write-Host "   cd backend"
        Write-Host "   .\venv\Scripts\Activate.ps1"
        Write-Host "   uvicorn main:app --reload --port 8000`n"
        
        Write-Host "2. Frontend:" -ForegroundColor Cyan
        Write-Host "   cd frontend"
        Write-Host "   npm start`n"
        
        Write-Host "3. MCP Server:" -ForegroundColor Cyan
        Write-Host "   cd mcp-server"
        Write-Host "   .\venv\Scripts\Activate.ps1"
        Write-Host "   uvicorn server:app --reload --port 8001`n"
        
        Write-Host "Access the application at: http://localhost:3000" -ForegroundColor Green
    }
    
    "2" {
        Write-Host "`n[3/5] Docker Setup..." -ForegroundColor Yellow
        
        Write-Host "Building Docker containers..." -ForegroundColor Cyan
        docker-compose build
        
        Write-Host "`n[4/5] Starting containers..." -ForegroundColor Yellow
        docker-compose up -d
        
        Write-Host "`n" + ("=" * 69) -ForegroundColor Green
        Write-Host " Docker Setup Complete!" -ForegroundColor Green
        Write-Host ("=" * 69) -ForegroundColor Green
        
        Write-Host "`nServices are running at:"
        Write-Host "  Frontend:   http://localhost:3000" -ForegroundColor Cyan
        Write-Host "  Backend:    http://localhost:8000" -ForegroundColor Cyan
        Write-Host "  MCP Server: http://localhost:8001" -ForegroundColor Cyan
        Write-Host "  API Docs:   http://localhost:8000/docs" -ForegroundColor Cyan
        
        Write-Host "`nTo view logs:" -ForegroundColor Yellow
        Write-Host "  docker-compose logs -f`n"
        
        Write-Host "To stop services:" -ForegroundColor Yellow
        Write-Host "  docker-compose down`n"
    }
    
    "3" {
        Write-Host "`n[3/5] Setting up Backend only..." -ForegroundColor Yellow
        Set-Location backend
        
        if (!(Test-Path "venv")) {
            python -m venv venv
        }
        
        .\venv\Scripts\Activate.ps1
        pip install -r requirements.txt
        
        if (!(Test-Path ".env")) {
            Copy-Item .env.example .env
            Write-Host "Please edit backend/.env with your configuration" -ForegroundColor Yellow
        }
        
        Write-Host "`n" + ("=" * 69) -ForegroundColor Green
        Write-Host " Backend Setup Complete!" -ForegroundColor Green
        Write-Host ("=" * 69) -ForegroundColor Green
        
        Write-Host "`nTo start the backend:"
        Write-Host "  cd backend"
        Write-Host "  .\venv\Scripts\Activate.ps1"
        Write-Host "  uvicorn main:app --reload --port 8000`n"
    }
    
    "4" {
        Write-Host "`n[3/5] Setting up Frontend only..." -ForegroundColor Yellow
        Set-Location frontend
        
        npm install
        
        if (!(Test-Path ".env")) {
            Copy-Item .env.example .env
        }
        
        Write-Host "`n" + ("=" * 69) -ForegroundColor Green
        Write-Host " Frontend Setup Complete!" -ForegroundColor Green
        Write-Host ("=" * 69) -ForegroundColor Green
        
        Write-Host "`nTo start the frontend:"
        Write-Host "  cd frontend"
        Write-Host "  npm start`n"
    }
    
    "5" {
        Write-Host "`nExiting...`n"
        exit 0
    }
    
    default {
        Write-Host "`nInvalid choice. Exiting.`n" -ForegroundColor Red
        exit 1
    }
}

Write-Host "See PROJECT_SUMMARY.md for more details.`n" -ForegroundColor Cyan
