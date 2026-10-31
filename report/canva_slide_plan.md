# Rihla Phase 2 Presentation: Slide Plan (32 slides)

This plan follows the structure of the two saved examples (PPTEXAMPLE1.pdf has 32 slides, PPTEXAMPLE2.pdf has 25). Both use the same pattern: a title slide, an introduction, then a big section title slide before each group of diagrams, diagram slides with almost no text, a walk through of the interface with screenshots, and a conclusion. Use the same colours and fonts as before (see canva_presentation_prompt.md).

Section slides: one big title in the middle of a dark Midnight Navy (#2C3E50) slide with a thin Oasis Teal (#5CA1A8) wave line.
Diagram slides: the image fills most of the slide on a white card, with a short label in the top left corner.

| # | Slide type | Text to put on the slide | Image to add |
|---|---|---|---|
| 1 | Title | Rihla. Desert and City Experience Booking Platform for Dubai. Phase 2 Presentation. Salem Al Tamimi, Hamzah, Hamad, Mir Umer, Omar Arif, Oumar Ibrahim | assets/logo.png, optional background assets/background.jpg |
| 2 | Introduction (three columns) | Phase 1: introduced the app idea, use case and activity diagrams, first plan with Odoo and PostgreSQL. Phase 2: detailed class, sequence and state diagrams, user interface design, final architecture with Tkinter, Flask and SQLite. Phase 3: implementation, testing the system, measuring its quality | small icons only |
| 3 | Section | SYSTEM ARCHITECTURE | none |
| 4 | Diagram + text | Layered Architecture (client and server). Why layered? All business rules, such as capacity, VAT, refunds and bans, live in one place on the server. The client only shows screens and never opens the database. | report/uml/04_component_deployment.png |
| 5 | Section | CLASS DIAGRAM | none |
| 6 | Diagram + text | Client screens. Every home screen extends BaseWelcomeScreen. One screen per role: Customer, Vendor, Staff, Partner, Dispatcher, Admin. Shared views: ReportView, VehicleView, DispatchView | report/uml/05a_class_client_screens.png |
| 7 | Diagram + text | Client modules, Flask server and data modules. server.py: REST API. database_core.py: users, SSN, staff venues, support tickets, reports. database_events.py: events, bookings, VAT, refunds, vehicles, cart, reviews | report/uml/05b_class_modules_server.png |
| 8 | Diagram | Database (13 tables) | report/uml/06_er_diagram.png |
| 9 | Section | USE CASE DIAGRAMS | none |
| 10 | Diagram | Customer and Partner | report/uml/01_use_case_customer_partner.png |
| 11 | Diagram | Vendor and Dispatcher | report/uml/02_use_case_vendor_dispatcher.png |
| 12 | Diagram | Staff and Admin | report/uml/03_use_case_staff_admin.png |
| 13 | Section | 5 SEQUENCE DIAGRAMS | none |
| 14 | Diagram | Booking with VAT and currency | report/uml/07_seq_booking_vat.png |
| 15 | Diagram | Cancellation and refund | report/uml/08_seq_cancel_refund.png |
| 16 | Diagram | Staff ticket check-in | report/uml/09_seq_staff_checkin.png |
| 17 | Diagram | Partner checkout | report/uml/10_seq_partner_checkout.png |
| 18 | Diagram | Report and ban | report/uml/11_seq_admin_report_ban.png |
| 19 | Section | STATE CHART AND ACTIVITY DIAGRAMS | none |
| 20 | Diagram | Booking and ticket | report/uml/12_state_booking.png |
| 21 | Diagram | Vehicle | report/uml/13_state_vehicle.png |
| 22 | Diagram + text | Refund decision. 48 hours or more: 100%. 48 to 24 hours: 50%. Under 24 hours: no cancel. Vendor and Admin: always 100% with a reason | report/uml/14_activity_refund_policy.png |
| 23 | Section | WALK THROUGH OF GUI | none |
| 24 | Screenshots | LOG IN AND SIGN UP PAGES | report/rihla_report/screens/01_login.png and 02_create_account.png |
| 25 | Screenshots | CUSTOMER PAGES: EXPLORE AND BOOK | screens/03_customer_explore.png and 04_event_page.png |
| 26 | Screenshots | CUSTOMER PAGES: PAYMENT AND TICKETS | screens/05_payment.png, 06_booking_details.png and 07_customer_bookings.png |
| 27 | Screenshots | VENDOR PAGES | screens/08_vendor_events.png and 09_vendor_bookings.png |
| 28 | Screenshots | STAFF VENUE OPERATIONS | screens/10_staff_operations.png |
| 29 | Screenshots | PARTNER AND DISPATCHER PAGES | screens/11_partner_cart.png and 12_dispatch.png |
| 30 | Screenshots | ADMIN PAGES AND REPORTS | screens/13_admin_users.png, 14_admin_reports.png and 15_report_form.png |
| 31 | Text (optional, not in the examples) | TESTING. 70 automated tests, all passed on 31 October 2026. Black-box, white-box and Flask integration tests. Tests use a temporary database | none, or a bar chart of tests per class: StaffVenue 14, Booking 13, Capacity 13, Cancellation 11, PartnerAndPayment 7, Admin 7, Report 3, ApiAccountGuard 2 |
| 32 | Conclusion | CONCLUSION. Rihla covers the full life of a booking, from event creation to check-in, review and refund, with six roles and all rules on one server. Thank you. Questions? | assets/logo.png |

All screenshots are in report/rihla_report/screens/. All diagrams are in report/uml/.
