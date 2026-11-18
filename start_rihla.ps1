<#
.SYNOPSIS
    Starts Rihla on Windows: the server in its own window, then the app.
    Run setup_windows.ps1 once before this.
#>
$root = $PSScriptRoot

# the server keeps running in its own window (close it to stop the server)
Start-Process python -ArgumentList "`"$root\server\server.py`"" -WorkingDirectory $root

# give the server a moment to start
Start-Sleep -Seconds 2

Push-Location (Join-Path $root "desktop")
npx electron .
Pop-Location
