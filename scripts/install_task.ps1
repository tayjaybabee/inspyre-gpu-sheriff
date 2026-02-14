# Install Inspyre GPU Sheriff scheduled task (runs at logon, highest privileges)
param(
  [string]$TaskName = "Inspyre GPU Sheriff",
  [string]$PythonExe = ""
)

if ([string]::IsNullOrWhiteSpace($PythonExe)) {
  $PythonExe = (Get-Command python).Source
}

$Cmd = "`"$PythonExe`" -m inspyre_gpu_sheriff.cli watch"

schtasks /Create /F /RL HIGHEST /SC ONLOGON /TN "$TaskName" /TR "$Cmd"
Write-Host "Installed task: $TaskName"
