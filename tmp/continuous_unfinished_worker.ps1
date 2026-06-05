$env:PYTHONPATH='C:\Dev\MTC_Download\scripts;C:\Dev\MTC_Download\scripts\download'
$env:PYTHONIOENCODING='utf-8'
$env:MTC_HTTP_TIMEOUT='45'
$env:MTC_HTTP_RETRIES='5'
$env:MTC_HTTP_BACKOFF='1.0'
$env:MTC_HTTP_POOL='160'
Set-Location 'C:\Dev\MTC_Download'
while ($true) {
  $p = Start-Process python -ArgumentList 'scripts\download\download_unfinished_id_queue_to_repo.py','--max-seconds','1800','--chapter-workers','32','--batch-size','128' -NoNewWindow -PassThru -RedirectStandardOutput 'logs\worker_stdout.tmp' -RedirectStandardError 'logs\worker_stderr.tmp'
  try { $p.PriorityClass = 'High' } catch {}
  $p.WaitForExit()
  if (Test-Path 'logs\worker_stdout.tmp') { Get-Content 'logs\worker_stdout.tmp' | Tee-Object -FilePath 'logs\continuous_unfinished_worker.log' -Append }
  if (Test-Path 'logs\worker_stderr.tmp') { Get-Content 'logs\worker_stderr.tmp' | Tee-Object -FilePath 'logs\continuous_unfinished_worker.log' -Append }
  python logs\audit_mtc_continune_local.py | Tee-Object -FilePath 'logs\continuous_unfinished_worker.log' -Append
  $audit = Get-Content 'logs\mtc_continune_local_audit.json' -Raw | ConvertFrom-Json
  if (($audit.issues | Measure-Object).Count -eq 0) {
    git -C C:\Dev\MTC_Continune push | Tee-Object -FilePath 'logs\continuous_unfinished_worker.log' -Append
  }
}
