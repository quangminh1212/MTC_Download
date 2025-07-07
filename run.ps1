# MTC Downloader Run Script
param (
    [string]$mode = "web"
)

# Check if virtual environment exists
if (-not (Test-Path -Path "venv")) {
    Write-Host "[ERROR] Virtual environment is not set up." -ForegroundColor Red
    Write-Host "Please run setup.bat first to set up the environment."
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate virtual environment
Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Yellow
& "./venv/Scripts/Activate.ps1"

# Run based on selected mode
switch ($mode) {
    "web" {
        Write-Host "===== STARTING WEB APPLICATION =====" -ForegroundColor Green
        Write-Host "Access the application at http://localhost:3000"
        python -c "from mtc_downloader.cli import web_cmd; web_cmd()"
    }
    "gui" {
        Write-Host "===== STARTING GUI APPLICATION =====" -ForegroundColor Green
        python -c "from mtc_downloader.cli import gui_cmd; gui_cmd()"
    }
    "cli" {
        Write-Host "===== STARTING COMMAND LINE APPLICATION =====" -ForegroundColor Green
        Write-Host "Usage instructions:"
        python -c "from mtc_downloader.cli import download_cmd; print('Help for download command:'); import sys; sys.argv = ['mtc-download', '--help']; download_cmd()"
        Write-Host ""
        Write-Host "Examples:"
        Write-Host "mtc-download https://metruyencv.com/truyen/ten-truyen/chuong-XX"
        Write-Host "mtc-extract -i file.html"
        Write-Host ""
        # Start a new PowerShell session in the current window
        if ($host.Name -eq 'ConsoleHost') {
            PowerShell -NoExit -Command {
                cd $pwd
                # Keep the virtual environment active
                & "./venv/Scripts/Activate.ps1"
            }
        }
    }
    default {
        Write-Host "[ERROR] Invalid parameter: $mode" -ForegroundColor Red
        Write-Host "Valid parameters: web, gui, cli"
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Deactivate virtual environment if not in CLI mode
if ($mode -ne "cli") {
    # In PowerShell, we can just deactivate directly if the function is defined
    if (Get-Command "deactivate" -ErrorAction SilentlyContinue) {
        deactivate
    }
} 