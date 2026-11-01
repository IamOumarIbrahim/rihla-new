# Rihla

Desktop booking system for desert and city experiences in Dubai. Features a Tkinter client (`src/`), a Flask REST API (`server/`), and a local SQLite database (`server/users.db`).

Supports 6 roles: Customer, Vendor, Staff, Partner (travel agency), Dispatcher, and Admin.

## Requirements

- Windows 10/11
- Python 3.12+ with Tkinter (`Add python.exe to PATH`)
- Dependencies: `Flask`, `requests`, `Pillow`, `tksvg`

## Setup & Running

```bash
git clone https://github.com/IamOumarIbrahim/rihla-new.git rihla_manual
cd rihla_manual
python -m pip install -r requirements.txt
```

Seed database with demo events, vehicles, and bookings:
```powershell
powershell -ExecutionPolicy Bypass -File .\dummy_data.ps1
```

Start the server (Terminal 1):
```bash
python start_server.py
```

Start the desktop client (Terminal 2):
```bash
python start_client.py
```

## Demo Accounts

The login screen provides one-click buttons for each default role:

| Role | Email | Password |
| :--- | :--- | :--- |
| Customer | `customer@email.com` | `customer1234` |
| Vendor | `vendor@email.com` | `vendor1234` |
| Staff | `staff@email.com` | `staff1234` |
| Partner | `partner@email.com` | `partner1234` |
| Dispatcher | `dispatcher@email.com` | `dispatcher1234` |
| Admin | `admin@email.com` | `admin1234` |

- **Sample Ticket Code (Staff Scanner):** `1234567890123456` (Burj Khalifa event).
- **Payment:** Checkout forms are pre-filled with test card details.

## Project Structure

```text
server/        Flask API (server.py), database schema, default accounts
src/           Tkinter client (main.py entrypoint, api_client.py)
src/screens/   Login, sign-up, password reset, event listings
src/welcome/   Role-specific home dashboards and shared widgets
assets/        UI assets, icons, and event imagery
tests/         Unit tests (isolated temporary database)
```

## Tests

```bash
python -m unittest discover -s tests
```
