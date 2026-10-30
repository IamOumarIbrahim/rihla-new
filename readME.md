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

- **Customer**: browse events, see the capacity and vehicles of each event, pick a date and number of guests, book and get a 16-digit ticket code.
  The booking screen shows the seats left on the chosen date. A booking that is bigger than the seats left is refused.
  *My Bookings* shows every ticket (Confirmed, Checked in, Expired, Cancelled) and lets you cancel an unused one.
  *Support* sends a message to staff.
- **Vendor**: create events (with a capacity), venues and categories. *Bookings* shows who booked and the guests and money booked.
  Deleting an event cancels its unused bookings and tickets.
- **Staff**: *Ticket Scanner* admits a ticket once and says how many guests to let in. *Support Tickets* lists open
  messages from customers. *Schedule* lists today's events with expected guests.
- **Dispatcher**: register and assign vehicles. The dispatch screen shows the guests booked and the capacity of the chosen event.
- **Event capacity**: an event with vehicles can take as many guests as the seats of its vehicles (any mix of types).
  An event with no vehicles uses the capacity the vendor typed in. Seats are counted per date, and cancelled bookings free their seats.
  Capacity is visualized as a bar filled with blue when full and white when empty, with simple text next to it: `N remaining` (and `Hurry up!` when N <= 5).
- **Every role**: *Dashboard* returns to the home screen, *Settings* changes the password.
- **Partner (OTA)**: Online Travel Agency partner portal. Can book extended group capacity across multiple events for various client groups, add events to a shopping list, and make a singular payment for all events combined.
- **Demo Payment**: Simulated payment checkout for customers and partners supporting Visa, Mastercard, and Bank Transfer with hardcoded demo credentials. Manual alterations from the authorized demo records cause the payment to fail.

## Tests

```
python -m unittest discover -s tests
```

The tests use a temporary database, so `src/users.db` is never touched.
