# Retry final 7 run gagal secara BERURUTAN, lalu rebuild seluruh artefak.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# Tunggu finalize putaran kedua selesai agar tidak bentrok rebuild.
while (-not (Test-Path "$root\data\finalize_v2_done.txt")) {
    Start-Sleep -Seconds 30
}
Remove-Item -LiteralPath "$root\data\finalize_v3_done.txt" -Force -ErrorAction SilentlyContinue

& python experiments/rerun_failed.py --direction both 2>&1 |
    Tee-Object -FilePath "$root\data\rerun_final.log"

& python experiments/summarize.py
& python experiments/plotting.py
& python laporan/build_report.py
& python slide/build_slides.py

"DONE_V3 $(Get-Date -Format o)" |
    Set-Content -LiteralPath "$root\data\finalize_v3_done.txt" -Encoding UTF8
Get-Content -LiteralPath "$root\data\finalize_v3_done.txt"
