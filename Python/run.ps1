# PowerShell script for running the Unity Screenshot + Doubao AI Image Generation System
# Set UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Script title
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "      Unity Screenshot + Doubao AI Image System" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

# Get current script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$venvPath = Join-Path $scriptDir "venv"
$requirementsPath = Join-Path $scriptDir "requirements.txt"

# Check if Python is installed
try {
    $pythonVersion = python --version
    Write-Host "[OK] Python detected: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not detected!" -ForegroundColor Red
    Write-Host "Please install Python 3.8 or higher: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to add Python to PATH environment variable" -ForegroundColor Yellow
    Read-Host "Press any key to exit"
    exit 1
}# Check if pip is available
try {
    $pipVersion = python -m pip --version
    Write-Host "[OK] pip detected: $($pipVersion -split ' ')[1]" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] pip not detected!" -ForegroundColor Red
    Write-Host "Trying to install pip..." -ForegroundColor Yellow
    
    try {
        python -m ensurepip --upgrade
        Write-Host "[OK] pip installation successful" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] pip installation failed, please install pip manually" -ForegroundColor Red
        Read-Host "Press any key to exit"
        exit 1
    }
}

# Check if uv tool is available, use it if available
$useUv = $false
try {
    $uvVersion = uv --version
    Write-Host "[OK] uv detected: $uvVersion, will use uv to accelerate dependency installation" -ForegroundColor Green
    $useUv = $true
} catch {
    Write-Host "[INFO] uv tool not detected, will use standard pip" -ForegroundColor Yellow
    Write-Host "   Tip: Install uv to speed up dependency installation (https://github.com/astral-sh/uv)" -ForegroundColor Gray
}# Check if virtual environment exists
if (-not (Test-Path $venvPath)) {
    Write-Host "[INFO] Virtual environment not detected, creating..." -ForegroundColor Yellow
    
    try {
        if ($useUv) {
            # Use uv to create virtual environment
            uv venv $venvPath
        } else {
            # Use standard method to create virtual environment
            python -m venv $venvPath
        }
        Write-Host "[OK] Virtual environment created successfully" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Failed to create virtual environment: $_" -ForegroundColor Red
        Read-Host "Press any key to exit"
        exit 1
    }
} else {
    Write-Host "[OK] Existing virtual environment detected" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Yellow
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

try {
    . $activateScript
    Write-Host "[OK] Virtual environment activated successfully" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to activate virtual environment: $_" -ForegroundColor Red
    Read-Host "Press any key to exit"
    exit 1
}# Check and install dependencies
Write-Host "[INFO] Checking project dependencies..." -ForegroundColor Yellow

try {
    if ($useUv) {
        # Use uv to install dependencies
        uv pip install -r $requirementsPath
    } else {
        # Use pip to install dependencies
        python -m pip install -r $requirementsPath
    }
    Write-Host "[OK] Dependencies installed/updated successfully" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to install dependencies: $_" -ForegroundColor Red
    Read-Host "Press any key to exit"
    exit 1
}

# Start main program
Write-Host ""
Write-Host "[LAUNCH] Starting Unity Screenshot + Doubao AI Image System..." -ForegroundColor Green
Write-Host "   Press Ctrl+C to stop the program" -ForegroundColor Yellow
Write-Host ""

try {
    # Change to Python directory
    Set-Location $scriptDir
    # Start main program
    python main.py
} catch {
    Write-Host "[ERROR] Program execution error: $_" -ForegroundColor Red
} finally {
    # Restore original directory
    Set-Location $PSScriptRoot
    # Deactivate virtual environment
    if (Get-Command deactivate -ErrorAction SilentlyContinue) {
        deactivate
    }
}

# Program end
Write-Host ""
Write-Host "Program has exited" -ForegroundColor Cyan
Read-Host "Press any key to close this window"