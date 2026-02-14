# Uninstall Inspyre GPU Sheriff scheduled task
param(
  [string]$TaskName = "Inspyre GPU Sheriff"
)

schtasks /Delete /TN "$TaskName" /F
Write-Host "Removed task: $TaskName"
