$ErrorActionPreference = 'Stop'
$root = 'C:\Dev\MTC'
$items = Get-ChildItem -LiteralPath $root -Recurse -Force | Where-Object { $_.Name -like '*+*' } | Sort-Object { $_.FullName.Length } -Descending
$renamed = @()
foreach($item in $items){
  $parent = $item.PSParentPath -replace '^.*::',''
  $newName = ($item.Name -replace '\+','').Trim()
  $newName = ($newName -replace '\s{2,}',' ').Trim()
  if([string]::IsNullOrWhiteSpace($newName) -or $newName -eq $item.Name){ continue }
  $target = Join-Path $parent $newName
  if(Test-Path -LiteralPath $target){
    $base = $newName
    $i = 1
    do {
      $alt = "{0} __renamed_{1}" -f $base, $i
      $target = Join-Path $parent $alt
      $i++
    } while (Test-Path -LiteralPath $target)
    $newName = Split-Path -Leaf $target
  }
  Rename-Item -LiteralPath $item.FullName -NewName $newName
  $renamed += [pscustomobject]@{ Old=$item.FullName; New=(Join-Path $parent $newName) }
}
$renamed | ConvertTo-Json -Depth 3
