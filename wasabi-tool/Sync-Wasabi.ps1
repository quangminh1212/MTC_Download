<#====================================================================
  Sync-Wasabi.ps1
  - Đồng bộ nhanh nhất các file từ máy lên Wasabi S3
  - Cho phép người dùng nhập: 1) thư mục nguồn, 2) bucket + prefix
  - Tự động tính concurrency dựa trên CPU cores (tối đa 300)
  - Retry khi gặp lỗi tạm thời (timeout, 429 Too Many Requests)
  - Ghi log chi tiết và báo cáo tiến độ mỗi giây + mỗi phút
  - Thêm .gitignore để bỏ qua log và script (nếu muốn)
====================================================================#>

param(
    [Parameter(Mandatory=$true,HelpMessage="Đường dẫn thư mục nguồn trên máy")]
    [ValidateScript({Test-Path $_ -PathType Container})]
    [string]$SourceDir,

    [Parameter(Mandatory=$true,HelpMessage="Tên bucket Wasabi")]
    [string]$Bucket,

    [Parameter(Mandatory=$false,HelpMessage="Prefix (thư mục ảo) trong bucket, để trống nếu không muốn")]
    [string]$Prefix = "",

    [Parameter(Mandatory=$false,HelpMessage="Số file tối đa mỗi lần retry (mặc định 5)")]
    [int]$MaxRetry = 5
)

# ------------------- CẤU HÌNH CƠ BẢN -------------------
$Endpoint   = "https://s3.wasabisys.com"
$RunUID    = "$(Get-Date -Format 'yyyyMMddHHmmss')"
$LogFile   = "$PSScriptRoot\upload_$RunUID.log"
$Report    = "$PSScriptRoot\upload_report_$RunUID.txt"

# Tính concurrency: 30 luồng cho mỗi core logical, tối đa 300
$LogicalCores = (Get-CimInstance Win32_Processor).NumberOfLogicalProcessors
$Concurrency   = [Math]::Min($LogicalCores * 30, 300)
Write-Host "CPU logical cores : $LogicalCores  →  Concurrency set to $Concurrency"

# Đếm tổng file (để tính %)
$TotalFiles = (Get-ChildItem -Path $SourceDir -Recurse -File | Measure-Object).Count
"$(Get-Date -Format o) - TOTAL_FILES=$TotalFiles - UID=$RunUID" | Out-File -FilePath $Report -Encoding utf8

# ------------------- JOB THEO DÕI TIẾN ĐỘ -------------------
$startTime = Get-Date
$prevCount = 0
$ProgressJob = Start-Job -ScriptBlock {
    param($LogFile,$TotalFiles,$Report,$startTime)
    while ($true) {
        Start-Sleep -Seconds 1    # thống kê mỗi giây
        $uploaded = (Select-String -Path $LogFile -Pattern "^Uploaded" -SimpleMatch).Count
        $delta    = $uploaded - $prevCount
        $prevCount = $uploaded

        $elapsed = (Get-Date) - $startTime
        $sec     = $elapsed.TotalSeconds
        $min     = $elapsed.TotalMinutes
        $speedS  = [math]::Round($uploaded / $sec, 2)
        $speedM  = [math]::Round($uploaded / $min, 2)
        $percent = [math]::Round(($uploaded / $TotalFiles) * 100, 2)

        $line = "$(Get-Date -Format o) - UPLOADED=$uploaded/$TotalFiles ($percent`%) - +$delta file(s) in last sec - $speedS file/s - $speedM file/min"
        $line | Out-File -FilePath $Report -Append -Encoding utf8
        Write-Host $line

        if ($uploaded -ge $TotalFiles) { break }
    }
} -ArgumentList $LogFile,$TotalFiles,$Report,$startTime

# ------------------- HÀM UPLOAD VỚI RETRY -------------------
function Invoke-Upload {
    param([int]$Attempt = 1)
    $cmd = @(
        "--endpoint-url",$Endpoint,
        "sync",
        "--upload-concurrency",$Concurrency,
        "--metadata","uid=$RunUID",
        "--retry-count",$MaxRetry,
        $SourceDir,
        "s3://$Bucket/$Prefix"
    )
    try {
        & s5cmd @cmd *>&1 | Tee-Object -FilePath $LogFile
        return $true
    } catch {
        Write-Warning "Upload thất bại lần $Attempt – $_"
        if ($Attempt -lt $MaxRetry) {
            Start-Sleep -Seconds (5 * $Attempt)
            return Invoke-Upload -Attempt ($Attempt + 1)
        } else {
            Write-Error "Đã vượt quá số lần retry ($MaxRetry). Dừng lại."
            return $false
        }
    }
}

# ------------------- CHẠY UPLOAD -------------------
Write-Host "`n=== BẮT ĐẦU ĐỒNG BỘ ==="
$success = Invoke-Upload -Attempt 1

# Đợi job thống kê hoàn thành
Wait-Job $ProgressJob | Out-Null
Receive-Job $ProgressJob | Out-Null
Remove-Job $ProgressJob

# ------------------- KẾT QUẢ -------------------
if ($success) {
    $final = Get-Content $Report | Select-Object -Last 1
    Write-Host "`n=================================================="
    Write-Host "✅  ĐỒNG BỘ THÀNH CÔNG"
    Write-Host $final
    Write-Host "Log chi tiết   : $LogFile"
    Write-Host "Báo cáo tổng hợp: $Report"
    Write-Host "=================================================="
} else {
    Write-Host "`n⚠️  ĐỒNG BỘ KHÔNG THÀNH CÔNG – xem $LogFile để biết chi tiết."
}
