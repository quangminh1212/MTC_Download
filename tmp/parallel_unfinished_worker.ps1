$env:PYTHONPATH='C:\Dev\MTC_Download\scripts;C:\Dev\MTC_Download\scripts\download'
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONUNBUFFERED='1'
$env:MTC_HTTP_TIMEOUT='50'
$env:MTC_HTTP_RETRIES='4'
$env:MTC_HTTP_BACKOFF='0.75'
$env:MTC_HTTP_POOL='256'
Set-Location 'C:\Dev\MTC_Download'

$shardCount = 5
$chapterWorkers = 20
$batchSize = 96
$procs = @{}

function Start-Shard([int]$shard) {
  $stdout = "logs\worker_shard_${shard}.out.log"
  $stderr = "logs\worker_shard_${shard}.err.log"
  $args = @('-u','scripts\download\download_unfinished_id_queue_to_repo.py','--max-seconds','1200','--chapter-workers',"$chapterWorkers",'--batch-size',"$batchSize",'--shard-index',"$shard",'--shard-count',"$shardCount")
  $p = Start-Process python -ArgumentList $args -NoNewWindow -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
  try { $p.PriorityClass = 'High' } catch {}
  $script:procs[$shard] = [PSCustomObject]@{ Proc=$p; Out=$stdout; Err=$stderr; Shard=$shard; Started=Get-Date }
  "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] started shard=$shard pid=$($p.Id) workers=$chapterWorkers batch=$batchSize" | Tee-Object -FilePath 'logs\continuous_unfinished_worker.log' -Append | Out-Null
}

foreach ($shard in 0..($shardCount-1)) {
  Start-Shard $shard
}

while ($true) {
  foreach ($shard in 0..($shardCount-1)) {
    $entry = $procs[$shard]
    if (-not $entry) {
      Start-Shard $shard
      continue
    }
    if ($entry.Proc.HasExited) {
      if (Test-Path $entry.Out) { Get-Content $entry.Out | Tee-Object -FilePath 'logs\continuous_unfinished_worker.log' -Append | Out-Null }
      if (Test-Path $entry.Err) { Get-Content $entry.Err | Tee-Object -FilePath 'logs\continuous_unfinished_worker.log' -Append | Out-Null }
      "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] restarting shard=$shard exit=$($entry.Proc.ExitCode)" | Tee-Object -FilePath 'logs\continuous_unfinished_worker.log' -Append | Out-Null
      Start-Sleep -Milliseconds 200
      Start-Shard $shard
    }
  }
  Start-Sleep -Seconds 2
}
