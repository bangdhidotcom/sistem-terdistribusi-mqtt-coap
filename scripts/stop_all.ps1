Get-CimInstance Win32_Process |
  Where-Object { $_.CommandLine -like '*sistem-terdistribusi-mqtt-coap*src*' -and $_.Name -like 'python*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Write-Output 'Proses project dihentikan.'
