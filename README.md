# Inspyre GPU Sheriff

A Windows-first watchdog to detect common display-driver incidents (TDR-ish) and recover by escalating actions:
1) Win+Ctrl+Shift+B graphics reset
2) PnP disable/enable bounce
3) DevCon disable/enable bounce (optional)

## Quick start
```powershell
poetry install
poetry run inspy-gpu status
poetry run inspy-gpu watch
```

## Scheduled task (run at logon, highest privileges)
```powershell
# run in an elevated PowerShell
poetry run inspy-gpu install-task
poetry run inspy-gpu uninstall-task
```

## Config
First run writes a config TOML to:
- %APPDATA%\InspyreGPU_Sheriff\config.toml

Lock a specific device instance id:
```powershell
poetry run inspy-gpu set-device "PCI\VEN_1002&DEV_...."
```

## Notes
- Device toggling requires Administrator privileges.
- 'watch' includes rate limiting + cooldown to avoid bounce-loops.
