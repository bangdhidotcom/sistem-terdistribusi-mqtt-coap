# Putaran terakhir: ulangi semua run gagal, lalu rebuild seluruh artefak.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$log = "$root\data\perfect_run.log"

Remove-Item -LiteralPath "$root\data\perfect_done.txt" -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $log -Force -ErrorAction SilentlyContinue

& python experiments/rerun_failed.py --direction both 2>&1 | Tee-Object -FilePath $log
& python experiments/summarize.py 2>&1 | Tee-Object -FilePath $log -Append
& python experiments/plotting.py 2>&1 | Tee-Object -FilePath $log -Append
& python laporan/build_report.py 2>&1 | Tee-Object -FilePath $log -Append
& python slide/build_slides.py 2>&1 | Tee-Object -FilePath $log -Append

$zero = 0
Get-ChildItem "$root\data\raw" -Filter 'run_*.json' | ForEach-Object {
    $j = Get-Content $_.FullName -Raw | ConvertFrom-Json
    if ($j.delivered -eq 0) { $zero++ }
}
if ($zero -eq 0) {
    $readme = "$root\README.md"
    (Get-Content $readme -Raw) -replace '40 run \(36 valid, 4 gagal total\)', '40 run (40 valid)' |
        Set-Content -LiteralPath $readme -Encoding UTF8 -NoNewline
}

"DONE_PERFECT zero=$zero at=$(Get-Date -Format o)" |
    Set-Content -LiteralPath "$root\data\perfect_done.txt" -Encoding UTF8
Get-Content -LiteralPath "$root\data\perfect_done.txt"
