param(
    [string]$Repo = "D:\Dev\MTC_Done",
    [string]$SourceRef = "main",
    [string]$DestinationRef = "refs/heads/main",
    [switch]$ForceWithLease
)

$ErrorActionPreference = 'Stop'
Set-Location $Repo

$args = @(
    '-c','pack.threads=1',
    '-c','core.compression=1',
    '-c','http.version=HTTP/1.1',
    'push'
)

if ($ForceWithLease) {
    $remoteMain = (& git rev-parse origin/main).Trim()
    if (-not $remoteMain) { throw 'Cannot resolve origin/main' }
    $args += "--force-with-lease=refs/heads/main:$remoteMain"
}

$args += 'origin'
$args += "$SourceRef`:$DestinationRef"

& git @args
exit $LASTEXITCODE
