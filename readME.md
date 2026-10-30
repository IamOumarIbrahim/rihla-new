# Rihla

Desktop app (Python, Tkinter, SQLite) for booking desert and city experiences in Dubai.

## Run

```
pip install -r requirements.txt
python src/main.py
```

Tkinter ships with the standard Python installer for Windows. The database file
`src/users.db` is created on the first start and is ignored by git.

## Demo accounts

The login screen has quick buttons for these accounts. They are created automatically.

| Role       | Email                 | Password       |
|------------|-----------------------|----------------|
| Customer   | customer@email.com    | customer1234   |
| Vendor     | vendor@email.com      | vendor1234     |
| Staff      | staff@email.com       | staff1234      |
| Partner    | partner@email.com     | partner1234    |
| Dispatcher | dispatcher@email.com  | dispatcher1234 |

Test ticket code for the staff scanner: `1234567890123456` (event: New year dinner).
