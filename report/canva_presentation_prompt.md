# Rihla Phase 2 Presentation: Canva Prompt and Slide Content

This file has two parts. Part 1 is one prompt that you paste into Canva (Magic Design or Canva AI) to get the deck layout. Part 2 gives the exact text, the speaker notes and the visuals for each of the 12 slides. Canva AI often shortens or changes text, so after it builds the deck, copy the slide text from Part 2 into each slide and add the diagrams and screenshots by hand.

All facts come from the Phase 2 Software Design Specification (report/rihla_report/Rihla_Phase2_SDS.pdf) and the code on branch main. All file paths are relative to the repository root (rihla_manual).

---

## Part 1: Prompt to paste into Canva

Copy everything inside the box below.

```
Create a 12-slide 16:9 presentation for a university Software Engineering course. The title is "Rihla: Phase 2 Software Design Specification". Rihla is a desktop app for booking desert safaris, dinners, yacht trips and other experiences in Dubai. It has six user roles (Customer, Vendor, Staff, Partner, Dispatcher, Admin) and is built with Python 3.12, a Tkinter client, a Flask REST server and one SQLite database.

Audience: a course instructor and classmates who know software engineering. They want to see the design clearly: architecture, data, components, diagrams, testing and limits.

Tone: clear, confident and professional, like senior computer engineering students presenting their own work. Simple English. Short bullet points, at most 5 bullets per slide (6 on the last slide) and at most 12 words per bullet. No long paragraphs on the slides.

Visual style: modern and clean with a light Dubai desert feeling. Use lots of white space, soft rounded cards, thin lines and simple flat icons (calendar, ticket, bus, shield, chart, users). A soft sand dune shape or a thin wave line can appear at the bottom of the title slide and the last slide only. No stock photos of people. Leave a large empty area (about half of the slide) on most content slides for a diagram or screenshot that I will add myself. Put a small "Rihla" logo spot in the top right corner of every content slide.

Colour palette (from the Rihla logo and the app):
- Desert Sand #E8C67E for highlights, title slide background shapes and number badges
- Oasis Teal #5CA1A8 as the main accent for headings, icons and lines
- Palm Green #75A771 for success, "done" and positive numbers
- Palm Brown #733D20 for small details only
- Midnight Navy #2C3E50 for body text and dark section backgrounds (this is the app's side menu colour)
- Cloud Grey #ECF0F1 as the light slide background (this is the app's page colour)
- White #FFFFFF for cards
- Alert Red #E74C3C only for limits, warnings and "refused" items

Fonts: a friendly rounded sans serif for titles, such as Poppins SemiBold or Montserrat SemiBold. A clean sans serif for body text, such as Open Sans or Segoe UI style. Title size large, body text at least 18 pt so it reads well on a projector.

Layout guidance:
- Slide 1: title slide with the logo in the centre, subtitle "Desert and City Experience Booking Platform for Dubai", and a list of the six team members.
- Slides 2 to 11: title at the top left, 3 to 5 short bullets on the left, a large image placeholder on the right for a UML diagram or app screenshot.
- Use a numbered badge in Desert Sand in the corner of each content slide.
- One slide (refund policy) needs a simple step chart, and one slide (testing) needs a horizontal bar chart. Leave space for both.
- Slide 12: demo plan as 6 small role cards in a grid, then a short conclusion and "Questions?".
- Add speaker notes space on every slide.

Slide list:
1. Rihla: Phase 2 Software Design Specification
2. From Phase 1 to Phase 2
3. Scope: What We Built
4. System Architecture
5. Data Design
6. Six Roles, One Frame
7. Booking with VAT and Currency
8. Cancellation and Refund Policy
9. Staff Venue Scoping and Check-in
10. Fleet, Dispatch and Partner Checkout
11. Admin, Reports, Testing and Limits
12. Demo Plan and Conclusion
```

Tip: if Canva asks for a style, pick a "minimal" or "modern professional" theme and then change the colours to the hex codes above with Styles, then Colour palettes, then Add new.

### Brand reference

| Name | Hex | Where it comes from | Use it for |
|---|---|---|---|
| Desert Sand | #E8C67E | the "R" in assets/logo.png | highlights, badges |
| Oasis Teal | #5CA1A8 | the "ihla" letters in assets/logo.png | headings, icons, lines |
| Palm Green | #75A771 | the palm leaves in assets/logo.png | success, done |
| Palm Brown | #733D20 | the palm trunk in assets/logo.png | small details only |
| Midnight Navy | #2C3E50 | DARK and TEXT in src/theme.py | body text, dark backgrounds |
| Cloud Grey | #ECF0F1 | PAGE_BG in src/theme.py | slide background |
| Alert Red | #E74C3C | the most used red in src/ | limits and warnings |

Logo file to upload to Canva: assets/logo.png (it has a transparent background).

---

## Part 2: The 12 slides

How to read each slide:
- **Slide text** is what goes on the slide.
- **Speaker notes** go in the notes box under the slide.
- **Visual** tells you what to add by hand and which file to use.
- **Suggested speaker** follows the team split in report/SPLIT FOR PHASE 2.pdf. Change it if your team agrees on another order.

---

### Slide 1: Rihla: Phase 2 Software Design Specification

**Slide text**
- Rihla
- Desert and City Experience Booking Platform for Dubai
- Phase 2: Software Design Specification
- Salem Al Tamimi, Hamzah, Hamad, Mir Umer, Omar Arif, Oumar Ibrahim
- Python 3.12, Tkinter, Flask, SQLite

**Speaker notes**
Good morning. We are the Rihla team and today we present the design of our system. Rihla is a desktop app that lets tourists book desert safaris, dinners, yacht trips and other experiences in Dubai. In this talk we show how we really built it, from the architecture down to the tests.

**Visual**
- Put the logo from assets/logo.png in the centre.
- Optional background: assets/background.jpg with a light white overlay (about 70%) so the text stays readable.

**Suggested speaker:** Salem Al Tamimi

---

### Slide 2: From Phase 1 to Phase 2

**Slide text**
- Phase 1: requirements, use cases, first plan with Odoo and PostgreSQL
- Phase 2: data design, architecture, components, interface and tests
- Final build: Tkinter client, Flask REST server, one SQLite database
- Why we changed: the team knows Python well, Tkinter ships with Python
- A small server we write ourselves is easier to test and explain

**Speaker notes**
In Phase 1 we wrote the requirements and planned to build Rihla on top of Odoo with PostgreSQL. During the semester we changed this plan to a Python program with a Tkinter client and a Flask server. We did this because the whole team knows Python, and a small server is easier to test and to explain than a large framework. This presentation and our report describe the final design, not the Phase 1 plan.

**Visual**
- Make a simple 3-step timeline in Canva: Phase 1 (requirements) to Phase 2 (design, this talk) to Phase 3 (implementation and testing). Highlight Phase 2 in Oasis Teal.
- Below it, two small boxes: "Planned: Odoo + PostgreSQL" (grey, crossed out) and "Built: Tkinter + Flask + SQLite" (Palm Green).

**Suggested speaker:** Salem Al Tamimi

---

### Slide 3: Scope: What We Built

**Slide text**
- Goal: connect tourists with local experience providers on live, shared data
- Safe seat booking: capacity checked inside one server transaction
- Clear prices: 5% UAE VAT, money kept in AED
- Digital tickets: unique 16-digit code, checked in only once
- Fair cancellations and role-based work for six roles

**Speaker notes**
Our main goal is to give every person in the booking process a clear screen for their job, all on the same live data. We ranked 20 functions as essential, desirable or future, and all 13 essential functions are done and tested. Three of the four desirable functions are done. The three future functions, such as a real payment gateway and Arabic, are not in the current code.

**Visual**
- Create a stacked horizontal bar chart in Canva (Elements, then Charts, then Bar). Data from Table 1 of the report:

| Priority | Done | Not done |
|---|---|---|
| Essential | 13 | 0 |
| Desirable | 3 | 1 |
| Future | 0 | 3 |

- Colour "Done" in Palm Green #75A771 and "Not done" in Cloud Grey or Alert Red #E74C3C.
- The one desirable function not done is real email and SMS verification (the code is always 000000).

**Suggested speaker:** Salem Al Tamimi

---

### Slide 4: System Architecture

**Slide text**
- Layered client and server design with three layers
- Presentation: Tkinter screens in src/, one home screen per role
- Service: Flask REST API on 127.0.0.1, port 5000
- Data: database_core.py and database_events.py hold all business rules
- The client never opens the database. The server checks everything again

**Speaker notes**
Rihla uses a layered client and server architecture. The client only shows screens and sends JSON requests through api_client.py. The Flask server is the only program that opens the database, so rules like capacity, VAT, refunds, bans and venue scope live in one place. For example, the event page checks free seats, but the server checks them again inside a transaction, so two people cannot book the last seat.

**Visual**
- Main image: report/uml/04_component_deployment.png (Figure 1 in the report).
- Optional second image, smaller: report/uml/05b_class_modules_server.png (Figure 4, client modules, Flask server and data modules).

**Suggested speaker:** Hamzah and Hamad

---

### Slide 5: Data Design

**Slide text**
- One SQLite database: server/users.db, 13 tables
- Core tables: users, events, venues, bookings, tickets
- Support tables: reviews, support_tickets, reports, vehicles, partner_cart
- Passwords: salted PBKDF2. SSN: only a hash and the last 4 digits
- Bookings store the total in AED with VAT included

**Speaker notes**
All data lives in one SQLite file that only the server opens. The init_db function creates the tables, upgrades older databases and adds the demo accounts and demo data. Many links use the email address instead of a numeric key, because the users table has no integer id. For privacy, we never store the raw SSN, only a salted hash and the last four digits.

**Visual**
- Main image: report/uml/06_er_diagram.png (Figure 2, entity relationship diagram).
- If the diagram is too small on the slide, crop it to the bookings, events, tickets and users tables and say that the full diagram is in the report.

**Suggested speaker:** Salem Al Tamimi

---

### Slide 6: Six Roles, One Frame

**Slide text**
- Customer and Partner book experiences. Partners book groups
- Vendor publishes events, venues and categories
- Staff check tickets in at their own venue
- Dispatcher assigns vehicles. Admin manages accounts and reports
- One frame for all: side menu, top bar, Report, Settings, Log Out

**Speaker notes**
Rihla has six roles and each one has its own home screen and its own server rules. Sign-up offers five roles, because nobody can register as an admin, and every role except Customer must give a 16-digit SSN. All home screens extend one base class, BaseWelcomeScreen, so every role sees the same layout. This follows Shneiderman's first golden rule, strive for consistency.

**Visual**
- Pick one use case diagram as the main image: report/uml/01_use_case_customer_partner.png. Put the other two as small thumbnails: report/uml/02_use_case_vendor_dispatcher.png and report/uml/03_use_case_staff_admin.png.
- Alternative: report/uml/05a_class_client_screens.png (class hierarchy of the home screens).
- Optional screenshot: report/rihla_report/screens/03_customer_explore.png to show the shared frame.

**Suggested speaker:** Hamzah and Hamad (roles), Mir Umer (interface frame)

---

### Slide 7: Booking with VAT and Currency

**Slide text**
- Pick a date from allowed dates, then choose guests
- Capacity bar: "N of TOTAL remaining", "Hurry up!" when almost full
- 3 x 240 AED = 720 + 36 VAT = 756 AED
- Prices shown in AED, USD, EUR or GBP. Always charged in AED
- After payment: Booking Details window with a PDF receipt

**Speaker notes**
The customer picks a date from a calendar that only allows valid dates, then chooses 1 to 10 guests. The payment window shows the base price, the 5% VAT line and the total in the user's preferred currency. Payment is a demo that checks fixed demo card or bank details. Only after the payment is approved does the client send the booking, and the server checks the seats again inside a BEGIN IMMEDIATE transaction and creates a 16-digit ticket code.

**Visual**
- Main image: report/uml/07_seq_booking_vat.png (Figure 8, booking sequence diagram).
- Small screenshots next to it: report/rihla_report/screens/05_payment.png (VAT line and currency picker) and report/rihla_report/screens/06_booking_details.png (receipt window).
- Optional small Canva chart: a stacked bar for one booking, Base 720 AED (Oasis Teal) and VAT 36 AED (Desert Sand), total 756 AED.

**Suggested speaker:** Hamzah and Hamad

---

### Slide 8: Cancellation and Refund Policy

**Slide text**
- Customer or partner: 100% refund 48 hours or more before the start
- 50% refund from 48 to 24 hours. No cancel inside 24 hours
- Vendor and Admin: always 100%, reason required (up to 300 characters)
- VAT is refunded in the same proportion
- Every cancel records who, when, which role, why and how much

**Speaker notes**
We use one written refund policy for everybody. A booker gets all the money back two days or more before the start, half between two days and one day, and cannot cancel in the last day. A vendor or an admin can cancel until the event starts, always with a full refund and a reason. The app shows the refund before the user confirms, and refunds are recorded only, because payments are a demo.

**Visual**
- Main image: report/uml/14_activity_refund_policy.png (Figure 15, activity diagram of the refund decision).
- Create a step chart in Canva (a column chart works too). X axis: hours before the event starts. Y axis: refund percent for a customer or partner.

| Hours before start | Refund |
|---|---|
| 48 or more | 100% |
| 24 to under 48 | 50% |
| under 24 | 0% (cancel refused) |

- Colours: 100% in Palm Green, 50% in Desert Sand, 0% in Alert Red.
- Optional: report/uml/08_seq_cancel_refund.png (Figure 9) or report/uml/12_state_booking.png (Figure 13).

**Suggested speaker:** Hamzah and Hamad

---

### Slide 9: Staff Venue Scoping and Check-in

**Slide text**
- Every staff account works at one venue, with a manager email
- Venue Operations: ticket check-in and today's schedule for that venue
- A ticket for another venue is refused by the server
- A ticket is admitted only once, even by two staff at once
- Support tickets are scoped to the staff member's venue

**Speaker notes**
At sign-up, staff choose a venue and enter the manager's email. The server finds the staff member's venue and refuses a ticket that belongs to another venue, without giving details about it. The update to "Used" only runs when the ticket is still "Valid", so the same ticket cannot be checked in twice. The schedule and the support tickets also show only the staff member's own venue.

**Visual**
- Main image: report/uml/09_seq_staff_checkin.png (Figure 10, staff check-in sequence diagram).
- Screenshot: report/rihla_report/screens/10_staff_operations.png (Figure 25, Venue Operations page).

**Suggested speaker:** Hamzah and Hamad

---

### Slide 10: Fleet, Dispatch and Partner Checkout

**Slide text**
- Dispatcher registers vehicles: Available, Assigned or Maintenance
- Assigned vehicles set the event capacity
- Example: two 4x4 Land Cruisers give 12 seats
- Partners book groups above 10 guests for their clients
- Partner shopping list: one payment, one transaction, all or nothing

**Speaker notes**
The dispatcher assigns a combination of available vehicles to an event, and the event capacity becomes the sum of their seats. When a vehicle is freed or set to Maintenance, the capacity goes back to the vendor's number. Partners are travel agencies. They collect several events in a shopping list and pay once, and the server books every item in one transaction, so a partner never gets half a cart.

**Visual**
- Main image: report/uml/10_seq_partner_checkout.png (Figure 11) or report/uml/13_state_vehicle.png (Figure 14). Pick one as the main image and the other as a thumbnail.
- Screenshots: report/rihla_report/screens/12_dispatch.png (Figure 27) and report/rihla_report/screens/11_partner_cart.png (Figure 26).

**Suggested speaker:** Hamzah and Hamad

---

### Slide 11: Admin, Reports, Testing and Limits

**Slide text**
- Admin bans and restores accounts. Banned users get HTTP 403
- Other roles send reports. Admin resolves them or bans the offender
- 70 automated unittest tests, all passed on 31 October 2026
- Black-box, white-box and Flask integration tests
- Known limits: no login tokens, demo payments, local server only

**Speaker notes**
The admin can ban any account except their own or another admin, and the server then refuses every login and write request from that email. For testing, we have 70 automated tests that use a temporary database, and all of them passed on 31 October 2026. We are also honest about the limits: there is no session token, payments are demo records, and the server runs only locally with plain HTTP. Phase 1 ideas such as QR codes, live vehicle tracking and Arabic are not built yet.

**Visual**
- Create a horizontal bar chart in Canva with the number of tests per test class (counted from the tests/ folder):

| Test class | Tests |
|---|---|
| StaffVenueTests | 14 |
| BookingTests | 13 |
| CapacityTests | 13 |
| CancellationTests | 11 |
| PartnerAndPaymentTests | 7 |
| AdminTests | 7 |
| ReportTests | 3 |
| ApiAccountGuardTests | 2 |
| Total | 70 |

- Use Oasis Teal for the bars. Do not chart the "Total" row, write "70 tests, all passed" as a big number next to the chart in Palm Green.
- Small images: report/uml/11_seq_admin_report_ban.png (Figure 12) and report/rihla_report/screens/14_admin_reports.png (Figure 29).
- Put the limits in a small card with an Alert Red border.

**Suggested speaker:** Oumar Ibrahim (testing), Omar Arif (limits)

---

### Slide 12: Demo Plan and Conclusion

**Slide text**
- Customer: explore, book, pay, PDF receipt, cancel with refund
- Vendor: edit an event, filter bookings, cancel with a reason
- Staff: check in a ticket, then try it at another venue
- Partner: shopping list. Dispatcher: assign vehicles
- Admin: ban a user, resolve a report
- Rihla is built, tested and ready to demo. Questions?

**Speaker notes**
Our live demo follows the per-role script in README.md and takes about 10 minutes. We run dummy_data.ps1 right before the demo so all dates are fresh. To conclude, Rihla covers the full life of a booking, from event creation to check-in, review and refund, with all rules on one server. Thank you for listening, and we are happy to take your questions.

**Visual**
- Make a 3 by 2 grid of small role cards in Canva, one per role, each with an icon and the demo login email:
  - Customer: customer@email.com
  - Vendor: vendor@email.com
  - Staff: staff@email.com
  - Partner: partner@email.com
  - Dispatcher: dispatcher@email.com
  - Admin: admin@email.com
- Do not put the passwords on the slide.
- Optional screenshot: report/rihla_report/screens/01_login.png (login screen with the quick demo account chips).
- Repeat the sand dune shape from the title slide and put the logo (assets/logo.png) next to "Questions?".

**Suggested speaker:** Mir Umer (demo), all members for questions

---

## Checklist before you present

- Every diagram and screenshot path in this file exists in the repository.
- Check that the text is still readable after Canva AI shortens it. Copy the exact slide text from Part 2 if needed.
- Practise the demo once with a fresh run of dummy_data.ps1 and the server running.
- Aim for about one minute per slide, plus 10 minutes for the live demo.
