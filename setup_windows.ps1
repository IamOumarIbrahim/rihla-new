<#
.SYNOPSIS
    One-time setup of Rihla on a Windows laptop.

.DESCRIPTION
    Before running this, install (default options are fine):
      1. Python 3.12+   https://www.python.org/downloads/   (tick "Add python.exe to PATH")
      2. Node.js 22+    https://nodejs.org/
      3. PostgreSQL 18  https://www.postgresql.org/download/windows/
         Remember the password you choose for the "postgres" user.

    Then, from the project folder, run:
        powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1

    What it does:
      - creates the database "rihla" and the user "rihla" (password "rihla")
      - installs the Python packages and the Electron app packages
      - builds the app screens
      - fills the database with demo data (dummy_data.ps1)
#>

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot

function Step($text) {
    Write-Host ""
    Write-Host "== $text" -ForegroundColor Cyan
}

# 1. find psql (the PostgreSQL command line), it is not always on PATH
Step "Looking for PostgreSQL"
$psql = (Get-Command psql -ErrorAction SilentlyContinue).Source
if (-not $psql) {
    $found = Get-ChildItem "C:\Program Files\PostgreSQL\*\bin\psql.exe" -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1
    if ($found) { $psql = $found.FullName }
}
if (-not $psql) { throw "PostgreSQL was not found. Install it from https://www.postgresql.org/download/windows/ first." }
Write-Host "Using $psql"

# 2. create the rihla user and database (asks for the postgres password once)
Step "Creating the rihla database"
$pw = Read-Host "Password of the postgres user (the one you chose when installing PostgreSQL)" -AsSecureString
$env:PGPASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($pw))
$roleExists = & $psql -U postgres -h localhost -tAc "SELECT 1 FROM pg_roles WHERE rolname = 'rihla'"
if ($roleExists -ne "1") {
    & $psql -U postgres -h localhost -c "CREATE ROLE rihla LOGIN PASSWORD 'rihla';"
}
$dbExists = & $psql -U postgres -h localhost -tAc "SELECT 1 FROM pg_database WHERE datname = 'rihla'"
if ($dbExists -ne "1") {
    & $psql -U postgres -h localhost -c "CREATE DATABASE rihla OWNER rihla;"
}
Remove-Item Env:\PGPASSWORD
Write-Host "Database ready: postgresql://rihla:rihla@localhost:5432/rihla"

# 3. Python packages
Step "Installing Python packages"
python -m pip install -r (Join-Path $root "requirements.txt")

# 4. the tables and the demo accounts are made by the server code
Step "Creating the tables"
python -c "import sys; sys.path.insert(0, r'$root\server'); import database_core; database_core.init_db(); print('Tables ready')"

# 5. Electron app
Step "Installing and building the app"
Push-Location (Join-Path $root "desktop")
npm install
npm run build
Pop-Location

# 6. demo data
Step "Adding demo data"
& (Join-Path $root "dummy_data.ps1")

Step "Done. Start Rihla with:  powershell -ExecutionPolicy Bypass -File .\start_rihla.ps1"
