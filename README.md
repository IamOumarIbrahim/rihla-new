# Rihla

Desktop app for booking desert and city experiences in Dubai. The app is a Tkinter client (`src/`)
that talks to a small Flask API server (`server/`). All data lives in one SQLite file, `server/users.db`.

There are six roles: Customer, Vendor, Staff, Partner (travel agency), Dispatcher and Admin.

## Requirements

- Windows 10 or 11
- Python 3.12 from [python.org](https://www.python.org/downloads/) (Tkinter is included; tick "Add python.exe to PATH")
- The packages in `requirements.txt` (Flask, requests, Pillow, and the optional tksvg for icons)

## Setup

Run these from the project folder (the one that contains `src` and `server`):

```
git clone <repo-url> rihla_manual
cd rihla_manual
python -m pip install -r requirements.txt
```

## Fill the database with demo data

```
powershell -ExecutionPolicy Bypass -File .\dummy_data.ps1
```

This creates `server/users.db` if it does not exist and adds venues, events with pictures, vehicles,
extra customers, bookings (upcoming, today and past), reviews, support tickets, reports for the admin
and a partner cart. Dates are relative to today, so there are always events to check in today.

It is safe to run again: each run removes what the previous run added and seeds fresh data.
Your own accounts and the demo login accounts are never touched. To remove only the seeded data:

```
powershell -ExecutionPolicy Bypass -File .\dummy_data.ps1 -Clear
```

## Start the app

Open two terminals in the project folder.

1. Start the server first and leave it running (stop it with Ctrl+C):

   ```
   python start_server.py
   ```

2. Then start the app:

   ```
   python start_client.py
   ```

The server listens on http://127.0.0.1:5000. Restart it after changing anything in `server/`.

## Demo accounts

The login screen has a quick button for each of these. They are created automatically when the server starts.

| Role       | Email                 | Password       |
|------------|-----------------------|----------------|
| Customer   | customer@email.com    | customer1234   |
| Vendor     | vendor@email.com      | vendor1234     |
| Staff      | staff@email.com       | staff1234      |
| Partner    | partner@email.com     | partner1234    |
| Dispatcher | dispatcher@email.com  | dispatcher1234 |
| Admin      | admin@email.com       | admin1234      |

`dummy_data.ps1` also adds these accounts, all with the password `demo1234`:

- Customers: layla.hassan@example.com, james.carter@example.com, sofia.rossi@example.com, omar.khalid@example.com
- Staff: nadia.saleh@example.com (Al Qudra Desert Camp), yousef.marina@example.com (Dubai Marina Yacht Club)
- Partner: desert.routes@example.com, Dispatcher: karim.dispatch@example.com

Other useful values:

- Test ticket code for the staff scanner: `1234567890123456` (event: New year dinner at Burj Khalifa,
  so only staff of Burj Khalifa, such as staff@email.com, can check it in)
- Payment: the checkout form is filled in with demo Visa, Mastercard or bank transfer details.
  Leave them as they are; changing them makes the demo payment fail on purpose.
- Sign-up: every account type except Customer needs a 16-digit SSN (any 16 digits that are not all the same). Admin accounts cannot be registered.
- Staff sign-up also asks for the venue they work at (one of the existing venues) and the email of
  that venue's manager. No manager account is needed; the email is only stored and shown to the admin.

## Staff and venues

- Every staff account works at one venue. The *Venue Operations* page checks tickets in and shows
  today's schedule for that venue only. The server enforces this: a ticket for an event at another
  venue is refused, and the schedule never includes other venues.
- *Support Tickets* also only lists (and lets staff resolve) questions about their own venue's events.
  Old tickets from before customers had to pick an event are shown to all staff.
- Staff change their venue and manager email in *Settings*; check-in, the schedule and support tickets follow at once.
- The admin *User Accounts* table shows each staff member's Venue and Manager Email.
- Staff accounts made before venues were assigned get one automatically when the server starts
  (the demo staff account gets Burj Khalifa, others the first venue) with a placeholder manager email.

## Cancellations and refunds

- Customers and partners cancel their own bookings from *My Bookings* / *Partner Bookings*:
  a full refund 48 hours or more before the event starts, 50% from 48 to 24 hours, and no
  cancelling in the last 24 hours. VAT is refunded in the same proportion.
- Vendors (their own events) and admins (any booking) can cancel until the event starts,
  always with a full refund, and must give the customer a reason.
- Deleting an event cancels its upcoming unused bookings with a full refund.
- Every cancellation records when, who, why and the refund; the booking card, the vendor table and
  the admin *Bookings* page show it. Cancelling frees the seats at once.
- Payments are a demo, so a refund is recorded, not sent anywhere.
- Pages that show other people's changes (bookings, venue operations, dispatch) have a **Refresh** button.

## Demo script

A suggested order for the final demo, about 10 minutes. Run `dummy_data.ps1` right before so the dates are fresh.

1. **Customer** (customer@email.com)
   - *Explore Tours*: filter by category, open an event. Show the picture, the venue link and
     **Open in Google Maps**, and the capacity bar ("N of TOTAL remaining", "Hurry up!" when almost full).
   - Pick a date and guests, book, pay with the prefilled card. Show the VAT line, the currency
     picker, the Booking Details window and **Download PDF** (saved to Downloads).
   - *My Bookings*: the new ticket and its 16-digit code; cancel an unused one and show the refund line.
   - *My Experiences*: past trips and reviews. *Support*: send a message to staff.
   - *Settings*: change the preferred currency (AED, EUR, GBP, USD).
2. **Vendor** (vendor@email.com)
   - *My Events*: event cards with pictures; edit an event (capacity, picture, recurrence days).
   - *Bookings*: the bookings table. Click a heading with a gear to filter (for example Status = Cancelled).
     Select a confirmed booking and cancel it with a reason (full refund).
   - *Manage Venues*: add a venue with a Google Maps link, or edit the link.
3. **Staff** (staff@email.com)
   - *Venue Operations*: the staff member's venue (Burj Khalifa) and manager, ticket check-in and
     today's schedule for that venue. Check in `1234567890123456`; it admits a ticket once.
   - Log in as nadia.saleh@example.com (Al Qudra Desert Camp) and try the same code: it is refused,
     because the ticket is for another venue. Her schedule shows only Al Qudra events.
   - *Support Tickets*: questions about Burj Khalifa events only (nadia.saleh sees the Al Qudra ones).
4. **Partner** (partner@email.com)
   - *Explore Tours*: add several events for client groups to the cart, then pay for all of them at once.
   - *Partner Bookings*: the group bookings.
5. **Dispatcher** (dispatcher@email.com)
   - *Register Vehicles*, *Fleet Maintenance* (filterable table), *Event Dispatch*: assign vehicles to an event.
     The event's capacity becomes the seats of its vehicles.
6. **Admin** (admin@email.com)
   - *User Accounts*: every account with sign-up date and age (staff also show Venue and Manager Email); ban a demo customer, then try to log in as them.
   - *Reports*: reports sent with the *Report* button from other roles; resolve one or ban the offender.
   - *Bookings*: every booking; cancel one with a reason and see who cancelled what and the refund.

## Project layout

```
server/            Flask API (server.py), database code, demo accounts (config.py)
src/               Tkinter client; main.py is the entry point, api_client.py talks to the server
src/screens/       Login, sign-up, password reset, event page
src/welcome/       Home screen for each role and the shared table style
assets/            Background, logo, icons and the pictures used by dummy_data.ps1
tests/             Unit tests (use a temporary database)
dummy_data.ps1     Demo data seeder
```

## Tests

```
python -m unittest discover -s tests
```

The tests use a temporary database, so `server/users.db` is never touched. A few tests open
Tkinter windows briefly, so run them on a desktop session.
