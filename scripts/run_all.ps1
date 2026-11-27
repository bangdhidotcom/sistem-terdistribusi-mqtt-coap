$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$py = (Get-Command python).Source
$jobs = @(
  @('mqtt_broker.py', @()),
  @('coap_server.py', @()),
  @('conversion_server.py', @()),
  @('mqtt_subscriber.py', @('--duration','600')),
  @('coap_client.py', @('--mode','get','--duration','600'))
)
foreach ($j in $jobs) {
  $argList = @("`"$root\src\$($j[0])`"") + $j[1]
  Start-Process -FilePath $py -ArgumentList $argList -WorkingDirectory $root -WindowStyle Hidden
  Start-Sleep -Milliseconds 400
}
Write-Output "Enam peran dapat dijalankan melalui experiments\run_matrix.py. Cek: python scripts\healthcheck.py"
