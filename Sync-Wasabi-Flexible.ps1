#Requires -Version 5.1
<#
.SYNOPSIS
    High-performance Wasabi sync with flexible source/destination selection.
    Reuses proven rclone tuning from sync_mtc_continune.bat.

.DESCRIPTION
    Syncs local folder to Wasabi bucket using rclone with aggressive parallelism.
    Uses --update flag to skip files already present on destination.
    No re-upload of existing files.

.PARAMETER SourcePath
    Local source directory to sync from.

.PARAMETER DestBucket
    Wasabi bucket name (e.g., "mtc1212").

.PARAMETER DestPrefix
    Destination prefix/path within bucket (e.g., "MTC_Continune").

.PARAMETER Region
    Wasabi region endpoint. Default: us-east-1.

.PARAMETER DryRun
    Preview what would be synced without actually transferring.

.PARAMETER Verbose
    Enable verbose rclone output.

.EXAMPLE
    .\Sync-Wasabi-Flexible.ps1 -SourcePath "D:\MyFolder" -DestBucket "mybucket" -DestPrefix "backup"

.EXAMPLE
    .\Sync-Wasabi-Flexible.ps1 "D:\Data" "mtc1212" "MTC_Continune" -Verbose
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateScript({Test-Path $_ -PathType Container})]
    [string]$SourcePath,

    [Parameter(Mandatory=$true, Position=1)]
    [string]$DestBucket,

    [Parameter(Mandatory=$true, Position=2)]
    [string]$DestPrefix,

    [Parameter()]
    [ValidateSet("us-east-1", "us-west-1", "eu-central-1", "ap-southeast-1")]
    [string]$Region = "us-east-1",

    [Parameter()]
    [switch]$DryRun,

    [Parameter()]
    [switch]$ShowProgress = $true,

    [Parameter()]
    [string]$AccessKey,

    [Parameter()]
    [string]$SecretKey,

    [Parameter()]
    [switch]$UseEnvAuth = $true
)

# Configuration
$RCLONE = "C:\Dev\MTC_Download\rclone\rclone.exe"
$LOG_DIR = "C:\Dev\MTC_Download\logs"
$MAX_RETRIES = 3

# Ensure log directory exists
if (-not (Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = Join-Path $LOG_DIR "wasabi_sync_$timestamp.log"

# Validate rclone exists
if (-not (Test-Path $RCLONE)) {
    Write-Error "rclone not found at: $RCLONE"
    Write-Host "Download from: https://rclone.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Build destination path
$dest = "wasabi:$DestBucket/$DestPrefix"

# Build rclone arguments (proven tuning from sync_mtc_continune.bat)
$rcloneArgs = @(
    "sync"
    $SourcePath
    $dest
    "--s3-provider=Wasabi"
    "--s3-endpoint=s3.$Region.wasabisys.com"
    "--s3-force-path-style"
    "--checkers=64"
    "--buffer-size=512M"
    "--multi-thread-cutoff=100M"
    "--multi-thread-streams=8"
    "--fast-list"
    "--update"  # KEY: Skip files already present on destination
    "--stats=5s"
    "--stats-one-line-date"
    "--stats-file-name-length=0"
    "--log-level=INFO"
    "--log-format=date,time"
    "--log-file=$logFile"
)

if ($DryRun) {
    $rcloneArgs += "--dry-run"
}

if ($ShowProgress) {
    $rcloneArgs += "--progress"
}

# Display configuration
Write-Host "`n=== Wasabi Sync Configuration ===" -ForegroundColor Cyan
Write-Host "Source:    $SourcePath" -ForegroundColor White
Write-Host "Destination: $dest" -ForegroundColor White
Write-Host "Region:    $Region" -ForegroundColor White
Write-Host "Log:       $logFile" -ForegroundColor Gray
if ($DryRun) {
    Write-Host "Mode:      DRY RUN (no actual transfer)" -ForegroundColor Yellow
}
Write-Host "=================================`n" -ForegroundColor Cyan

# Retry wrapper function
function Invoke-RcloneWithRetry {
    param(
        [string[]]$Arguments,
        [int]$MaxRetries = 3
    )

    for ($attempt = 1; $attempt -le $MaxRetries; $attempt++) {
        Write-Host "[Attempt $attempt/$MaxRetries] Starting sync..." -ForegroundColor Yellow

        $process = Start-Process -FilePath $RCLONE -ArgumentList $Arguments `
            -NoNewWindow -Wait -PassThru

        if ($process.ExitCode -eq 0) {
            Write-Host "`n[SUCCESS] Sync completed successfully" -ForegroundColor Green
            return $true
        }

        Write-Warning "Sync failed with exit code: $($process.ExitCode)"

        if ($attempt -lt $MaxRetries) {
            $waitTime = 5 * $attempt
            Write-Host "Retrying in $waitTime seconds..." -ForegroundColor Yellow
            Start-Sleep -Seconds $waitTime
        }
    }

    Write-Error "Sync failed after $MaxRetries attempts"
    return $false
}

# Execute sync
try {
    $success = Invoke-RcloneWithRetry -Arguments $rcloneArgs -MaxRetries $MAX_RETRIES

    if ($success) {
        Write-Host "`nSync log saved to: $logFile" -ForegroundColor Gray
        exit 0
    } else {
        exit 1
    }
} catch {
    Write-Error "Unexpected error: $_"
    exit 1
}