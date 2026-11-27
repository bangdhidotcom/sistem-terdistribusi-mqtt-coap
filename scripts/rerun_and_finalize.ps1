# Menjalankan rerun dua arah sebagai proses Windows terlepas, lalu finalisasi.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Remove-Item -LiteralPath "$root\data\finalize_v2_done.txt" -Force -ErrorAction SilentlyContinue

$py = (Get-Command python).Source
$jobs = @(
    @{ Name = 'm2c'; Args = @('experiments/rerun_failed.py', '--direction', 'm2c') },
    @{ Name = 'c2m'; Args = @('experiments/rerun_failed.py', '--direction', 'c2m') }
)
$pids = @()
foreach ($job in $jobs) {
    $out = "$root\data\rerun_$($job.Name).log"
    $err = "$root\data\rerun_$($job.Name).err"
    $p = Start-Process -FilePath $py -ArgumentList $job.Args -WorkingDirectory $root `
        -RedirectStandardOutput $out -RedirectStandardError $err `
        -WindowStyle Hidden -PassThru
    $pids += $p.Id
    "rerun $($job.Name) PID=$($p.Id)"
}
"pids=$($pids -join ',') started=$(Get-Date -Format o)" |
    Set-Content -LiteralPath "$root\data\rerun_pids.txt" -Encoding UTF8

while (Get-Process -Id $pids -ErrorAction SilentlyContinue) {
    Start-Sleep -Seconds 30
}

& python experiments/summarize.py
& python experiments/plotting.py
& python laporan/build_report.py
& python slide/build_slides.py
"DONE_V2 $(Get-Date -Format o)" |
    Set-Content -LiteralPath "$root\data\finalize_v2_done.txt" -Encoding UTF8
Get-Content -LiteralPath "$root\data\finalize_v2_done.txt"
