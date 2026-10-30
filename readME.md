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

## What each role can do

- **Customer**: browse events, pick a date and number of guests, book and get a 16-digit ticket code.
  *My Bookings* shows every ticket (Confirmed, Checked in, Expired, Cancelled) and lets you cancel an unused one.
  *Support* sends a message to staff.
- **Vendor**: create events, venues and categories. *Bookings* shows who booked and the guests and money booked.
  Deleting an event cancels its unused bookings and tickets.
- **Staff**: *Ticket Scanner* admits a ticket once and says how many guests to let in. *Support Tickets* lists open
  messages from customers. *Schedule* lists today's events with expected guests.
- **Dispatcher**: register and assign vehicles. The dispatch screen shows the guests booked for the chosen event.
- **Every role**: *Dashboard* returns to the home screen, *Settings* changes the password.
- **Partner**: the screens are still placeholders.

## Tests

```
python -m unittest discover -s tests
```

The tests use a temporary database, so `src/users.db` is never touched.
