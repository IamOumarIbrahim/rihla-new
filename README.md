# Rihla

Desktop booking system for desert and city experiences in Dubai, with 6 roles: Customer, Vendor, Staff, Partner (travel agency), Dispatcher and Admin.

| Part | Technology | Folder |
| :--- | :--- | :--- |
| App (what users see) | Electron + React + Ant Design | `desktop/` |
| Server (all the rules) | Python Flask REST API | `server/` |
| Database | PostgreSQL | created by `setup_windows.ps1` |
| Tests | Python `unittest` on a separate test schema | `tests/` |

The old Tkinter client is still in `src/` (legacy). The new app talks to the same server.

## Why Electron and PostgreSQL

The Tkinter + SQLite version had problems outside Windows: Tk was missing on Linux, the screens fell back to a bitmap font, the theme used a Windows-only font and the icon package would not build. Electron screens are web pages with the fonts bundled, so they look the same on Windows and Linux. PostgreSQL is one real database server with row locks, instead of one SQLite file that locks completely on every write.

## Setup on Windows

1. Install Python 3.12+ (tick "Add python.exe to PATH"), Node.js 22+ and PostgreSQL 18.
2. From this folder run once:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1
```

3. Start Rihla (server window + app):

```powershell
powershell -ExecutionPolicy Bypass -File .\start_rihla.ps1
```

## Setup on Linux

```bash
# PostgreSQL with a rihla user and database
sudo -u postgres psql -c "CREATE ROLE rihla LOGIN PASSWORD 'rihla';" -c "CREATE DATABASE rihla OWNER rihla;"
python3 -m pip install -r requirements.txt
cd desktop && npm install && npm run build && cd ..
./start_rihla.sh
```

The database address can be changed with `RIHLA_DATABASE_URL` (default `postgresql://rihla:rihla@localhost:5432/rihla`).

## Demo accounts

The sign-in screen has one button per account.

| Role | Email | Password |
| :--- | :--- | :--- |
| Customer | `customer@email.com` | `customer1234` |
| Vendor | `vendor@email.com` | `vendor1234` |
| Staff | `staff@email.com` | `staff1234` |
| Partner | `partner@email.com` | `partner1234` |
| Dispatcher | `dispatcher@email.com` | `dispatcher1234` |
| Admin | `admin@email.com` | `admin1234` |

- Demo ticket for the staff scanner: `1234 5678 9012 3456` (New year dinner, Burj Khalifa).
- Payment forms are filled with demo card details. Changing any field makes the payment fail.
- Verification codes (sign up, forgot password) are always `000000`.

## Demo data

```powershell
powershell -ExecutionPolicy Bypass -File .\dummy_data.ps1
```

Safe to run again: it removes what it added last time and adds it again.

## Tests

```bash
python -m unittest discover -s tests -v
```

The tests use their own schema (`rihla_test`), so the demo data is never touched.

## Project structure

```text
desktop/          Electron app: main.js (window), src/ (React screens), tools/capture.js (screenshots)
server/           Flask API (server.py), rules (database_core.py, database_events.py), db.py (PostgreSQL)
tests/            Unit and integration tests
src/              Legacy Tkinter client
assets/           Pictures, icons and the fonts the app ships with
```
