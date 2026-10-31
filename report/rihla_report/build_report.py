"""Builds the Phase 2 Software Design Specification for Rihla.

It starts from a copy of the course template (Rihla_Phase2_SDS_template_copy.docx), keeps its
title block and styles, and writes the report text, tables, screenshots and UML figures.

Run from the repository root:
    python report/rihla_report/build_report.py
Then (on Windows with Word installed) the script also refreshes the table of contents and
saves a PDF next to the .docx.
"""
import os
import sys

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.dirname(HERE)
UML = os.path.join(REPORT, "uml")
SCREENS = os.path.join(HERE, "screens")
TEMPLATE_COPY = os.path.join(HERE, "Rihla_Phase2_SDS_template_copy.docx")
OUT_DOCX = os.path.join(HERE, "Rihla_Phase2_SDS.docx")
OUT_PDF = os.path.join(HERE, "Rihla_Phase2_SDS.pdf")

doc = Document(TEMPLATE_COPY)
FIG = [0]
TAB = [0]
TEXT_WIDTH = Inches(6.5)

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(11)
normal.paragraph_format.space_after = Pt(6)
normal.paragraph_format.line_spacing = 1.15


def _outline(style, level):
    ppr = style.element.get_or_add_pPr()
    for old in ppr.findall(qn("w:outlineLvl")):
        ppr.remove(old)
    lvl = OxmlElement("w:outlineLvl")
    lvl.set(qn("w:val"), str(level))
    ppr.append(lvl)


def heading_style(name, size, color, level):
    try:
        st = doc.styles[name]
    except KeyError:
        st = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        st.base_style = doc.styles["Normal"]
        st.next_paragraph_style = doc.styles["Normal"]
    st.font.name = "Calibri"
    st.font.size = Pt(size)
    st.font.bold = True
    st.font.color.rgb = color
    st.paragraph_format.space_before = Pt(14 if level == 0 else 10)
    st.paragraph_format.space_after = Pt(6)
    st.paragraph_format.keep_with_next = True
    _outline(st, level)
    return st


NAVY = RGBColor(0x1F, 0x3A, 0x5F)
heading_style("Heading 1", 16, NAVY, 0)
heading_style("Heading 2", 13, NAVY, 1)
heading_style("Heading 3", 11.5, RGBColor(0x2C, 0x3E, 0x50), 2)
heading_style("Heading 4", 11, RGBColor(0x34, 0x49, 0x5E), 3)

code_style = doc.styles.add_style("PDL Code", WD_STYLE_TYPE.PARAGRAPH)
code_style.base_style = doc.styles["Normal"]
code_style.font.name = "Consolas"
code_style.font.size = Pt(9)
code_style.paragraph_format.space_after = Pt(0)
code_style.paragraph_format.line_spacing = 1.0

cap_style = doc.styles.add_style("Figure Caption", WD_STYLE_TYPE.PARAGRAPH)
cap_style.base_style = doc.styles["Normal"]
cap_style.font.size = Pt(9.5)
cap_style.font.italic = True
cap_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
cap_style.paragraph_format.space_after = Pt(10)

# ---------------------------------------------------------------------------
# Keep the template's title block, drop its instruction text
# ---------------------------------------------------------------------------
body = doc.element.body
title_par = doc.paragraphs[0]
for p in doc.paragraphs[1:]:
    p._element.getparent().remove(p._element)
for t in doc.tables:
    t._element.getparent().remove(t._element)
title_par.alignment = WD_ALIGN_PARAGRAPH.CENTER
# The title block uses Heading 1 in the template. Keep its look but leave it out of the table of contents.
title_par.style = doc.styles["Normal"]
for _r in title_par.runs:
    _r.bold = True
    _r.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def para(text="", style=None, bold_lead=None, align=None, size=None, italic=False):
    p = doc.add_paragraph(style=style)
    if bold_lead:
        r = p.add_run(bold_lead)
        r.bold = True
    if text:
        r = p.add_run(text)
        r.italic = italic
        if size:
            r.font.size = Pt(size)
    if align is not None:
        p.alignment = align
    else:
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return p


def h(level, text):
    p = doc.add_paragraph(style=f"Heading {level}")
    p.add_run(text)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    return p


def bullets(items, numbered=False):
    style = "List Number" if numbered else "List Bullet"
    try:
        doc.styles[style]
    except KeyError:
        style = "List Paragraph"
    for item in items:
        p = doc.add_paragraph(style=style)
        if isinstance(item, tuple):
            r = p.add_run(item[0])
            r.bold = True
            p.add_run(item[1])
        else:
            p.add_run(item)
        p.paragraph_format.space_after = Pt(3)
        if style == "List Paragraph":
            p.paragraph_format.left_indent = Inches(0.3)
            p.runs[0].text = "•  " + p.runs[0].text


def shade(cell, hex_color):
    tcpr = cell._element.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcpr.append(shd)


def table(headers, rows, caption, widths=None, font=9.5):
    TAB[0] += 1
    t = doc.add_table(rows=1, cols=len(headers))
    # The template has no "Table Grid" style, so the borders are set directly.
    tblpr = t._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:color"), "9AA5B1")
        borders.append(el)
    tblpr.append(borders)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, text in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(text)
        r.bold = True
        r.font.size = Pt(font)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        shade(c, "1F3A5F")
    for k, row in enumerate(rows):
        cells = t.add_row().cells
        for i, text in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            r = p.add_run(str(text))
            r.font.size = Pt(font)
            p.paragraph_format.space_after = Pt(0)
            if k % 2:
                shade(cells[i], "EEF2F7")
    # Repeat the heading row on every page.
    trpr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    trpr.append(th)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Inches(w)
    p = doc.add_paragraph(style="Figure Caption")
    p.add_run(f"Table {TAB[0]}: {caption}")
    return t


def figure(path, caption, width=6.3, max_height=8.4):
    from PIL import Image
    FIG[0] += 1
    with Image.open(path) as im:
        w, hgt = im.size
    width_in = width
    if hgt / w * width_in > max_height:
        width_in = max_height * w / hgt
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(path, width=Inches(width_in))
    c = doc.add_paragraph(style="Figure Caption")
    c.add_run(f"Figure {FIG[0]}: {caption}")
    return FIG[0]


def uml(name, caption, **kw):
    return figure(os.path.join(UML, name + ".png"), caption, **kw)


def shot(name, caption, **kw):
    return figure(os.path.join(SCREENS, name + ".png"), caption, **kw)


def code(lines):
    for line in lines.strip("\n").split("\n"):
        p = doc.add_paragraph(style="PDL Code")
        p.add_run(line if line else " ")
        p.paragraph_format.left_indent = Inches(0.25)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def page_break():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def toc():
    p = doc.add_paragraph()
    run = p.add_run()
    for kind, text in (("begin", None), (None, 'TOC \\o "1-2" \\h \\z \\u'), ("separate", None), ("end", None)):
        if kind:
            fc = OxmlElement("w:fldChar")
            fc.set(qn("w:fldCharType"), kind)
            run._r.append(fc)
            if kind == "separate":
                t = OxmlElement("w:t")
                t.text = "Right-click and choose Update Field to build the table of contents."
                run._r.append(t)
        else:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = text
            run._r.append(it)


def page_numbers():
    footer = doc.sections[0].footer
    p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    for kind, text in (("begin", None), (None, "PAGE"), ("end", None)):
        if kind:
            fc = OxmlElement("w:fldChar")
            fc.set(qn("w:fldCharType"), kind)
            run._r.append(fc)
        else:
            it = OxmlElement("w:instrText")
            it.text = text
            run._r.append(it)


# ===========================================================================
# Cover
# ===========================================================================
para("")
para("Rihla", align=WD_ALIGN_PARAGRAPH.CENTER, size=34).runs[0].bold = True
para("Desert and City Experience Booking Platform for Dubai", align=WD_ALIGN_PARAGRAPH.CENTER, size=14)
para("Software Design Specification (SDS)", align=WD_ALIGN_PARAGRAPH.CENTER, size=14).runs[0].bold = True
para("")
para("Team members and parts", align=WD_ALIGN_PARAGRAPH.CENTER, size=12).runs[0].bold = True
for line in ("Salem Al Tamimi: Sections 1 and 2", "Hamzah and Hamad: Section 3",
             "Mir Umer: Section 4", "Omar Arif: Section 5", "Oumar Ibrahim: Section 6"):
    para(line, align=WD_ALIGN_PARAGRAPH.CENTER, size=11)
para("")
para("Implementation: Python 3.12, Tkinter client, Flask REST server, SQLite database",
     align=WD_ALIGN_PARAGRAPH.CENTER, size=10, italic=True)
para("All facts in this document were checked against the project source code "
     "(repository rihla_manual, branch main).", align=WD_ALIGN_PARAGRAPH.CENTER, size=10, italic=True)
page_break()

para("Table of Contents", align=WD_ALIGN_PARAGRAPH.LEFT, size=16).runs[0].bold = True
toc()
page_break()

# ===========================================================================
# 1.0 Introduction
# ===========================================================================
h(1, "1.0 Introduction")
para("This Software Design Specification (SDS) describes how Rihla is built. Rihla is a desktop "
     "application for booking desert safaris, dinners, yacht trips and other experiences in Dubai. "
     "In Phase 1 we wrote the requirements. In this phase we explain the data design, the architecture, "
     "the components, the user interface and the tests of the software that we really implemented.")
para("Our Phase 1 plan was to build Rihla as a custom module on top of Odoo with PostgreSQL. During the "
     "semester we changed this plan. The final product is a Python program with two parts: a Tkinter "
     "desktop client and a small Flask web server that owns one SQLite database. We made this change "
     "because the whole team knows Python well, Tkinter ships with Python, and a small server we write "
     "ourselves is easier to test and to explain than a large framework. This document describes the "
     "final design, not the Phase 1 plan.")

h(2, "1.1 Goals and objectives")
para("The main goal of Rihla is to connect tourists with local experience providers and to give every "
     "person in the process a clear screen for their own job. A tourist should find an experience, see "
     "how many seats are left, pay, and get a ticket code in a few steps. The provider, the venue staff, "
     "the transport team, travel agencies and the platform administrator should each work with the same "
     "live data, so seats are never sold twice.")
para("Our objectives are:")
bullets([
    ("Safe seat booking: ", "check capacity on the server inside one database transaction, so two people "
     "cannot book the last seats at the same time."),
    ("Clear prices: ", "add the mandatory 5% UAE VAT to every booking, keep all money in AED, and show "
     "prices in AED, USD, EUR or GBP for the user."),
    ("Digital tickets: ", "give every booking a unique 16-digit ticket code that venue staff can check in "
     "only once, and a booking receipt the user can save as a PDF."),
    ("Fair cancellations: ", "apply one written refund policy for everybody and record who cancelled, when, "
     "why and how much was refunded."),
    ("Role-based work: ", "give each of the six roles (Customer, Vendor, Staff, Partner, Dispatcher, Admin) "
     "its own home screen and its own server rules."),
    ("Trust and safety: ", "require a 16-digit SSN for every non-customer account, let users report "
     "problems, and let the admin ban accounts."),
])

h(2, "1.2 Statement of scope")
para("Rihla covers the full life of a booking: an event is created by a vendor, transport is assigned by "
     "a dispatcher, a customer or partner books and pays, staff check the ticket in at the venue, and the "
     "customer can review the experience afterwards. Cancellations, refunds, support questions, reports "
     "and bans are part of the scope.")
para("Major inputs are account details, event details (title, category, price in AED, venue, date or weekly "
     "days, time, capacity and a JPEG picture), booking requests (event, date, guests), payment details, "
     "ticket codes, vehicle data, support messages and reports. Major outputs are event lists with live "
     "capacity, booking confirmations with ticket codes, VAT breakdowns, PDF receipts, check-in results, "
     "daily venue schedules, refund amounts and admin tables.")
para("The table below ranks the main functions from the developer's point of view. Essential functions are "
     "finished and tested. Desirable functions were planned and are partly done. Future functions are not "
     "in the current code.")
table(["Function", "Priority", "Status in the code"], [
    ["Sign up, log in, password reset, six roles", "Essential", "Done. Passwords use salted PBKDF2."],
    ["16-digit SSN for non-customer accounts", "Essential", "Done. Only a hash and the last 4 digits are stored."],
    ["Event, venue and category management (vendor)", "Essential", "Done, with pictures and weekly recurrence."],
    ["Explore, search and filter tours", "Essential", "Done (category, maximum price, text search)."],
    ["Capacity check per date", "Essential", "Done. Vehicle seats or the event capacity."],
    ["Booking with 5% VAT and currency display", "Essential", "Done. Totals are stored in AED with VAT."],
    ["Demo payment (Visa, Mastercard, bank transfer)", "Essential", "Done. Checked against fixed demo records."],
    ["Booking Details window and PDF receipt", "Essential", "Done. PDF written without extra libraries."],
    ["Ticket check-in by venue staff", "Essential", "Done. Scoped to the staff member's venue."],
    ["Cancellation and refund policy", "Essential", "Done. 100%, 50% or refused, with an audit trail."],
    ["Partner shopping list and one-payment checkout", "Essential", "Done. All items in one transaction."],
    ["Vehicle registration and event dispatch", "Essential", "Done. Assigned seats become the capacity."],
    ["Admin: accounts, bans, reports, all bookings", "Essential", "Done."],
    ["Reviews and average ratings", "Desirable", "Done (0 to 5 in steps of 0.5)."],
    ["Support tickets answered by venue staff", "Desirable", "Done, scoped to the venue."],
    ["Google Maps link for venues", "Desirable", "Done (only Google Maps https links)."],
    ["Real email and SMS verification", "Desirable", "Not done. The code is always 000000."],
    ["Real payment gateway and real refunds", "Future", "Not done. Payments and refunds are demo records."],
    ["QR codes, offline driver app, live vehicle map", "Future", "Not done."],
    ["Arabic and other languages", "Future", "Not done. The interface is English only."],
], "Ranking of the major functions", widths=[2.6, 0.9, 3.0])

h(2, "1.3 Software context")
para("Tourism is one of the biggest industries in Dubai. Many small operators still take bookings by phone "
     "and chat, and they lose track of seats when bookings come from walk-in tourists, hotels and travel "
     "agencies at the same time. Rihla puts all these channels on one system. Customers book for "
     "themselves. Partners (travel agencies) book groups for their clients and can book more than 10 guests "
     "at once. Vendors see every booking for their events. Dispatchers decide how many seats an event has "
     "by assigning vehicles. Staff at the venue see the schedule of the day and admit guests.")
para("Technically, Rihla is a client and server system. The client (folder src/) is a Tkinter desktop program "
     "that the user starts with start_client.py. It never opens the database. Every read and write goes "
     "through api_client.py, which sends HTTP requests with JSON to the Flask server (folder server/). The "
     "server listens on 127.0.0.1 port 5000 and is the only program that opens server/users.db. This keeps "
     "all business rules (capacity, VAT, refunds, bans, venue scope) in one place. Figure 1 shows this "
     "structure.")
uml("04_component_deployment", "Component and deployment view of Rihla", width=6.5)

h(2, "1.4 Major constraints")
bullets([
    ("Time and team size: ", "the project had to be finished in one semester by a student team, so we chose "
     "tools we already knew (Python, Tkinter, Flask, SQLite) and avoided large frameworks."),
    ("UAE tax rules: ", "VAT is 5% and must be shown as a separate line. Money is kept in AED. Other "
     "currencies are for display only."),
    ("Platform: ", "the client targets Windows 10 or 11 with Python 3.12. Some details are Windows specific, "
     "for example finding the Downloads folder through the Windows registry."),
    ("No real payments: ", "we may not process real cards in a course project, so payment is a demo that "
     "compares the form with fixed demo details."),
    ("Privacy: ", "an SSN is sensitive data, so the server stores only a salted hash and the last 4 digits."),
    ("Demo readiness: ", "the project must be easy to show, so the server creates six demo accounts at start "
     "and dummy_data.ps1 fills the database with realistic data relative to today."),
])
page_break()

# ===========================================================================
# 2.0 Data design
# ===========================================================================
h(1, "2.0 Data design")
para("This section describes the data that moves inside Rihla. It covers the data passed between "
     "components, the data shared by large parts of the program, temporary files, and the database.")

h(2, "2.1 Internal software data structure")
para("Components exchange plain Python dictionaries and lists. Between the client and the server the same "
     "dictionaries travel as JSON. Every server answer has a success flag, and a failed answer also has a "
     "message that the client shows to the user without changes. The most important structures are:")
table(["Structure", "Main fields", "Produced by and used by"], [
    ["Event", "id, title, category, price, desc, vendor_email, venue_id, venue_name, maps_url, event_datetime, "
     "is_recurring, recur_day, recur_time, capacity", "database_events.get_all_events to the explore, event "
     "and vendor screens"],
    ["Capacity info", "total, source ('vehicles' or 'event'), vehicles, booked, remaining",
     "_capacity_info to the event page and the CapacityBar widget"],
    ["Booking", "id, event_id, event_title, venue_name, booking_date, event_time, guests, total_price, "
     "ticket_code, status, can_cancel, refund_if_cancelled, cancelled_by, cancel_reason, refund_percent, "
     "refund_amount", "_booking_dict to My Bookings, vendor, partner and admin tables"],
    ["Booking result", "success, message, booking (with base_price and vat)",
     "create_booking to payment.show_booking_details_window"],
    ["Payment", "txn_id, method, currency", "payment modal to the Booking Details window and PDF"],
    ["Receipt lines", "list of (text, font size, bold)", "payment._receipt_lines to the window and booking_pdf"],
    ["Refund", "percent, base, vat, total", "_cancel to the cancel dialogs"],
    ["Cart item", "id, event_id, booking_date, guests, client_name, title, unit_price, total_price",
     "get_cart_items to the partner shopping list"],
    ["Vehicle assignment", "vehicle_id, auto_reassign_recurring", "dispatch view to dispatch_vehicle_combination"],
    ["User row (admin)", "email, role, created_at, banned, banned_at, banned_by, venue_name, manager_email",
     "get_all_users to the admin User Accounts table"],
], "Data structures passed between components", widths=[1.25, 3.0, 2.25])
para("Booking statuses are computed when the booking is read. The database keeps status 'Confirmed' or "
     "'Cancelled' in bookings and 'Valid', 'Used' or 'Cancelled' in tickets. The function _booking_dict joins "
     "both and shows 'Cancelled', 'Checked in', 'Expired' (date passed) or 'Confirmed'.")

h(2, "2.2 Global data structure")
para("The main global data store is the SQLite database server/users.db. Every component reads and writes "
     "it only through the server functions in database_core.py and database_events.py. Next to it, the "
     "server keeps event pictures as files in server/event_images/<event id>.jpg.")
para("Some constants are shared by large parts of the program:")
bullets([
    ("config.py ", "(one copy in src/ and one in server/): the six roles, the demo accounts, SIGNUP_ROLES "
     "(all roles except Admin) and MIN_PASSWORD_LENGTH = 8."),
    ("pricing.py ", "(client): VAT_RATE = 0.05, the display rates for 1 AED (USD 0.2723, EUR 0.2510, "
     "GBP 0.2150) and the money formatting functions."),
    ("database_events.py ", "(server): VAT_RATE = 0.05, FULL_REFUND_HOURS = 48, HALF_REFUND_HOURS = 24, "
     "MAX_CANCEL_REASON = 300."),
    ("database_core.py ", "(server): DEFAULT_EVENT_CAPACITY = 20, MAX_EVENT_CAPACITY = 5000, "
     "MAX_GUESTS_PER_BOOKING = 10, MAX_OPEN_SUPPORT_TICKETS = 3, SSN_LENGTH = 16."),
    ("theme.py ", "(client): shared colours and the Segoe UI font, so every screen looks the same."),
])
para("On the client, each home screen object keeps the signed-in email and role in memory while the window "
     "is open. There is no other global session state.")

h(2, "2.3 Temporary data structure")
bullets([
    ("Partner cart: ", "the partner_cart table holds events a partner wants to book. Rows are deleted after a "
     "successful checkout, or when the partner removes them."),
    ("Image cache: ", "the client keeps downloaded event pictures in memory (event_images.py) and forgets one "
     "when the vendor changes it."),
    ("Uploaded picture: ", "when a vendor picks a picture, the client shrinks it to at most 1400 pixels, encodes "
     "it as base64 JPEG and sends it in the JSON body. The server checks it (JPEG, at most 4 MB) and writes it "
     "as a file."),
    ("Receipt PDF: ", "booking_pdf.py writes Rihla_Booking_<transaction id>.pdf to the user's Downloads folder. "
     "It never overwrites an older file. It adds (1), (2) and so on to the name."),
    ("Test databases: ", "the unit tests point DB_PATH to a temporary file, so server/users.db is never touched "
     "by tests."),
    ("Demo seed table: ", "dummy_data.ps1 records every row it adds in a demo_seed table, so the next run (or "
     "-Clear) can remove exactly those rows."),
])

h(2, "2.4 Database description")
para("Rihla uses one SQLite database. The function init_db in database_core.py creates all tables with CREATE "
     "TABLE IF NOT EXISTS, adds missing columns to older databases with ALTER TABLE, and inserts default data "
     "(vehicle types, two venues, categories, two demo events, seven vehicles, the demo ticket and the six demo "
     "accounts). The reviews table is created the first time it is needed. Figure 2 shows the entities and "
     "their relationships. Many links use an email address (for example customer_email or vendor_email) "
     "instead of a foreign key, because the users table has no integer id.")
uml("06_er_diagram", "Entity relationship diagram of server/users.db", width=6.4, max_height=8.2)

DB_TABLES = [
    ("users", "One row per account.", [
        ["email", "TEXT", "UNIQUE. Compared without letter case."],
        ["password", "TEXT", "pbkdf2$200000$salt$hash (salted PBKDF2-SHA256)"],
        ["role", "TEXT", "NOT NULL, default 'Customer'"],
        ["phone", "TEXT", "UAE mobile number"],
        ["currency", "TEXT", "AED, USD, EUR or GBP, default AED"],
        ["created_at", "TEXT", "sign-up time (server local time)"],
        ["banned, banned_at, banned_by", "INTEGER, TEXT, TEXT", "banned is 0 or 1, default 0"],
        ["ssn_hash, ssn_last4", "TEXT, TEXT", "only for non-customer roles"],
        ["venue_id", "INTEGER", "REFERENCES venues(id), staff only"],
        ["manager_email", "TEXT", "staff only, stored text, no account"],
    ]),
    ("venues", "Places where events happen.", [
        ["id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"],
        ["name, address", "TEXT", "name NOT NULL"],
        ["vendor_email", "TEXT", "owner vendor"],
        ["maps_url", "TEXT", "NOT NULL default '', Google Maps https link"],
    ]),
    ("events", "Experiences that can be booked.", [
        ["id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"],
        ["title", "TEXT", "NOT NULL"],
        ["category, price, description", "TEXT", "price text such as '240 AED'"],
        ["vendor_email", "TEXT", "owner vendor"],
        ["venue_id", "INTEGER", "FOREIGN KEY venues(id)"],
        ["event_datetime", "TEXT", "'YYYY-MM-DD HH:MM' for one-time events"],
        ["is_recurring, recur_day, recur_time", "TEXT", "'Recurring' or 'One-Time', weekdays such as 'Tuesday, Thursday'"],
        ["capacity", "INTEGER", "NOT NULL default 20, 1 to 5000"],
    ]),
    ("bookings", "One row per paid booking.", [
        ["id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"],
        ["customer_email", "TEXT", "NOT NULL, the customer or partner who booked"],
        ["event_id", "INTEGER", "FOREIGN KEY events(id)"],
        ["event_title, venue_name", "TEXT", "copies kept for history"],
        ["booking_date, event_time", "TEXT", "booking_date NOT NULL"],
        ["guests", "INTEGER", "NOT NULL default 1"],
        ["total_price", "INTEGER", "NOT NULL, AED including VAT"],
        ["ticket_code", "TEXT", "UNIQUE NOT NULL, 16 digits"],
        ["status", "TEXT", "'Confirmed' or 'Cancelled'"],
        ["client_name", "TEXT", "partner's client group"],
        ["created_at", "TEXT", "default CURRENT_TIMESTAMP"],
        ["cancelled_at, cancelled_by, cancelled_by_role, cancel_reason", "TEXT", "cancellation audit trail"],
        ["refund_percent, refund_amount", "INTEGER, REAL", "100 or 50, amount in AED"],
    ]),
    ("tickets", "Entry tickets checked by staff.", [
        ["id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"],
        ["ticket_code", "TEXT", "UNIQUE"],
        ["event_title, customer_email", "TEXT", ""],
        ["status", "TEXT", "'Valid', 'Used' or 'Cancelled'"],
    ]),
    ("reviews", "Ratings of past experiences.", [
        ["id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"],
        ["booking_id", "INTEGER", "NOT NULL UNIQUE, FOREIGN KEY bookings(id)"],
        ["event_id, customer_email", "INTEGER, TEXT", "index on event_id"],
        ["rating", "REAL", "0 to 5 in steps of 0.5"],
        ["comment", "TEXT", "at most 500 characters"],
        ["created_at, updated_at", "TEXT", "default CURRENT_TIMESTAMP"],
    ]),
    ("support_tickets", "Questions from customers to venue staff.", [
        ["id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"],
        ["customer_email, subject, message", "TEXT", "NOT NULL"],
        ["event_title", "TEXT", "the event the question is about"],
        ["status", "TEXT", "'Open' or 'Resolved'"],
        ["created_at, resolved_by, resolved_at", "TEXT", ""],
    ]),
    ("reports", "Problems reported to the admin.", [
        ["id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"],
        ["reporter_email, reporter_role", "TEXT", "NOT NULL"],
        ["category, offender_type, offender_email", "TEXT", "what happened and who it is about"],
        ["subject, description", "TEXT", "NOT NULL"],
        ["status, resolution", "TEXT", "'Open' or 'Resolved', resolution text"],
        ["created_at, resolved_by, resolved_at", "TEXT", ""],
    ]),
    ("vehicle_types", "Seats per vehicle type.", [
        ["id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"],
        ["name", "TEXT", "UNIQUE NOT NULL, for example 'desert buggy'"],
        ["capacity", "INTEGER", "NOT NULL seats (2, 6, 20, 4, 50 by default)"],
    ]),
    ("vehicles", "The dispatcher's fleet.", [
        ["id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"],
        ["license_number", "TEXT", "UNIQUE NOT NULL"],
        ["vehicle_type, location", "TEXT", "NOT NULL"],
        ["status", "TEXT", "'Available', 'Assigned' or 'Maintenance'"],
        ["dispatcher_email", "TEXT", "owner dispatcher"],
        ["auto_reassign_recurring", "INTEGER", "0 or 1"],
    ]),
    ("event_vehicles", "Which vehicles serve which event.", [
        ["id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"],
        ["event_id, vehicle_id", "INTEGER", "FOREIGN KEYs events(id), vehicles(id)"],
        ["status", "TEXT", "'Assigned' or 'Concluded'"],
    ]),
    ("partner_cart", "A partner's shopping list.", [
        ["id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"],
        ["partner_email", "TEXT", "NOT NULL, indexed"],
        ["event_id", "INTEGER", "NOT NULL, FOREIGN KEY events(id)"],
        ["booking_date, guests, client_name", "TEXT, INTEGER, TEXT", ""],
        ["created_at", "TEXT", "default CURRENT_TIMESTAMP"],
    ]),
    ("vendor_categories", "Categories a vendor can choose for events.", [
        ["id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"],
        ["vendor_email, name", "TEXT", "NOT NULL, no duplicate name per vendor"],
    ]),
]
for name, purpose, rows in DB_TABLES:
    para(purpose, bold_lead=f"Table {name}. ")
    table(["Column", "Type", "Constraint or meaning"], rows, f"Table {name}", widths=[2.4, 1.2, 2.9], font=9)
para("Indexes: idx_bookings_customer on bookings(customer_email), idx_bookings_event on bookings(event_id, "
     "booking_date), idx_cart_partner on partner_cart(partner_email) and idx_reviews_event on reviews(event_id).")
page_break()

# ===========================================================================
# 3.0 Architecture and components
# ===========================================================================
h(1, "3.0 Architectural and component-level design")
para("Rihla uses a layered client and server architecture with three layers:")
bullets([
    ("Presentation layer (client, src/): ", "Tkinter screens. navigate.py moves between the login, sign-up and "
     "password screens. screens/routing.py opens the home screen that belongs to the user's role. Every home "
     "screen extends BaseWelcomeScreen, which draws the side menu, the top bar with the clock, the Report, "
     "Settings and Log Out buttons, and a scrollable content area."),
    ("Service layer (server/server.py): ", "a Flask REST API. Each endpoint reads the JSON body, checks the "
     "caller with _blocked (unknown, banned or wrong role gives HTTP 403), calls one database function and "
     "returns JSON."),
    ("Data layer (database_core.py, database_events.py): ", "all SQL and all business rules: password hashing, "
     "SSN rules, capacity, VAT, ticket codes, refunds, venue scope and bans."),
])
para("The client never trusts its own checks alone. For example, the event page checks the remaining seats "
     "before it opens the payment window, but the server checks them again inside a BEGIN IMMEDIATE "
     "transaction when the booking is saved. This is how double booking is prevented without the 15-minute "
     "seat lock that we planned in Phase 1.")

h(2, "3.1 System Structure")
para("The client is organised by screen, and the server by data area. The client package welcome/ has one "
     "module per role plus shared views (ReportView, VehicleView, DispatchView, cancellation helpers and the "
     "shared table style). The server has one API module and two data modules. database_core.py handles "
     "users, SSN, staff venues, support tickets and reports. database_events.py handles venues, categories, "
     "events, capacity, bookings, VAT, cancellations, tickets, vehicles, dispatch, the partner cart and "
     "reviews.")
h(3, "3.1.1 Architecture diagram")
para("Figure 3 shows the class hierarchy of the client screens. Figure 4 shows how the client modules, the "
     "Flask server and the data modules depend on each other. Python modules that are not classes are shown "
     "with the stereotype <<module>>.")
uml("05a_class_client_screens", "Design class diagram, part 1: client home screens and shared views")
uml("05b_class_modules_server", "Design class diagram, part 2: client modules, Flask server and data modules")
para("The use case diagrams in Figures 5, 6 and 7 show which functions each role can use. They are the base "
     "for the components described in section 3.2.")
uml("01_use_case_customer_partner", "Use case diagram for Customer and Partner", width=5.2, max_height=7.5)
uml("02_use_case_vendor_dispatcher", "Use case diagram for Vendor and Dispatcher", width=5.2, max_height=7.5)
uml("03_use_case_staff_admin", "Use case diagram for Staff and Admin", width=5.2, max_height=7.0)

h(2, "3.2 Description of components (overview)")
para("We describe eight components. For each one we give its responsibilities, its interface, its classes, "
     "its limits and the processing of its main operations. PDL means Program Design Language: short, "
     "structured pseudocode that follows the real code.")

COMPONENTS = [
    {
        "name": "Authentication and Accounts",
        "pspec": "This component creates accounts and signs users in. It keeps passwords as salted PBKDF2 "
                 "hashes with 200,000 rounds and upgrades any old plain-text password after a successful login. "
                 "Sign-up has an account type picker with five roles. Admin is not in the list, so nobody can "
                 "register as an admin. Every role except Customer must give a 16-digit SSN. Staff must also "
                 "choose an existing venue and enter the email of the venue manager. The component also handles "
                 "the forgot-password flow, the preferred currency and the login refusal for banned accounts.",
        "interface": [
            ["POST /api/auth/login", "email, password", "email as stored and role, or 401 (wrong) or 403 (banned)"],
            ["POST /api/users/register", "email, password, role, phone, ssn, venue_id, manager_email", "success, or a message explaining the problem"],
            ["PUT /api/users/password", "email, new_password", "success"],
            ["GET/PUT /api/users/currency", "email, currency", "currency code"],
            ["GET/PUT /api/staff/venue", "email, venue_id, manager_email", "venue with manager email"],
            ["GET /api/users/email_exists, phone_exists", "email or phone", "exists flag"],
        ],
        "classes": "Screens: login.show_login_screen, create_account.show_create_account_screen, "
                   "forgot_password.show_forgot_password_screen, reset_password.show_reset_password_window, "
                   "social_login.open_social_login and the DigitBoxes widget for the SSN. Server: database_core "
                   "functions register_user, login_status, ssn_error, staff_venue_error, hash_password, "
                   "verify_password, set_currency and set_staff_venue.",
        "restrictions": "There is no session token. After login the client only remembers the email. Email and "
                        "phone verification use the fixed code 000000. The Google and Apple buttons open a normal "
                        "email and password form, not a real OAuth login. PUT /api/users/password does not check "
                        "the old password.",
        "performance": "PBKDF2 with 200,000 rounds takes a short but noticeable time on purpose. It runs once per "
                       "login or sign-up, so it does not slow down normal use.",
        "constraints": "Passwords need at least 8 characters. The SSN must be exactly 16 digits (0 to 9) and not "
                       "the same digit 16 times. The phone is a UAE number with 9 digits after +971.",
        "ops": [
            ("login_status(email, password)", "Finds the user without letter case, verifies the password, upgrades an "
             "old plain-text password, and returns 'ok', 'invalid' or 'banned'.",
             """
FUNCTION login_status(email, password) RETURNS text
  row = SELECT email, password, banned FROM users WHERE lower(email) = lower(email)
  IF row is empty OR NOT verify_password(password, row.password) THEN RETURN 'invalid'
  IF row.password does not start with 'pbkdf2$' THEN
     UPDATE users SET password = hash_password(password)
  IF row.banned THEN RETURN 'banned'
  RETURN 'ok'
"""),
            ("register_user(email, password, role, phone, ssn, venue_id, manager_email)",
             "Saves a new account when the email is free and the role rules pass. Stores only the SSN hash and its "
             "last 4 digits.",
             """
FUNCTION register_user(...) RETURNS boolean
  IF role NOT IN SIGNUP_ROLES THEN role = 'Customer'
  IF email empty OR password empty OR email_exists(email) OR ssn_error(role, ssn) THEN RETURN false
  IF role = 'Staff' THEN
     IF staff_venue_error(venue_id, manager_email) THEN RETURN false
  ELSE venue_id = NULL, manager_email = NULL
  INSERT INTO users (email, hash_password(password), role, phone, now,
                     hash(ssn), last 4 digits of ssn, venue_id, manager_email)
  RETURN true
"""),
            ("ssn_error(role, ssn)", "Returns None when the SSN is fine for the role, otherwise the message to show.",
             """
FUNCTION ssn_error(role, ssn)
  IF role = 'Customer' THEN RETURN None
  ssn = ssn without spaces and dashes
  IF ssn empty THEN RETURN 'A 16-digit SSN is required'
  IF length(ssn) <> 16 OR ssn has a non-digit THEN RETURN 'must be exactly 16 digits'
  IF all digits are the same THEN RETURN 'Please enter your real SSN.'
  RETURN None
"""),
        ],
    },
    {
        "name": "Event and Venue Management",
        "pspec": "This component lets a vendor publish and maintain experiences. A vendor creates events with "
                 "title, category, price in AED, description, venue, a one-time date or weekly days, a time, a "
                 "capacity (1 to 5000, default 20) and an optional JPEG picture. The vendor also manages venues "
                 "(with an optional Google Maps link) and categories. Renaming an event also renames it in the "
                 "bookings and tickets. Deleting an event frees its vehicles, cancels its upcoming unused bookings "
                 "with a full refund and deletes the picture.",
        "interface": [
            ["GET /api/events, /api/events/vendor/<email>", "none or vendor email", "list of events"],
            ["POST /api/events", "event fields, image_b64", "success (Vendor role checked)"],
            ["PUT /api/events/<id>", "event fields, image_b64 or remove_image", "success"],
            ["DELETE /api/events/<id>", "event id", "success"],
            ["GET /api/events/<id>/image", "event id", "JPEG bytes or 404"],
            ["POST /api/venues, DELETE /api/venues/<id>", "name, address, vendor_email, maps_url", "success or 'in use'"],
            ["PUT /api/venues/<id>/maps_url", "vendor_email, maps_url", "cleaned link or error"],
            ["GET/POST/DELETE /api/vendor_categories", "vendor_email, name", "categories"],
        ],
        "classes": "VendorWelcomeScreen (My Events, Bookings, Manage Venues, Manage Categories, Add New Event) with "
                   "open_event_form for create and edit. event_images.py (load, encode, CoverImage). Server: "
                   "create_event, update_event, delete_event, create_venue, delete_venue, validate_maps_url, "
                   "update_venue_maps_url, add_vendor_category.",
        "restrictions": "Update and delete of events and delete of venues do not check that the caller owns them. "
                        "A venue cannot be deleted while events use it or staff work there. Prices are stored as "
                        "text and only the digits are used, so decimal prices are not supported.",
        "performance": "Pictures are shrunk to 1400 pixels on the client before upload and limited to 4 MB on the "
                       "server, so lists with many pictures still load quickly.",
        "constraints": "Only https links on Google Maps hosts are accepted for venues. Pictures must be JPEG.",
        "ops": [
            ("delete_event(event_id)", "Frees vehicles, cancels upcoming bookings with 100% refund, cancels their "
             "tickets and deletes the event.",
             """
PROCEDURE delete_event(event_id)
  vendor = owner of event
  UPDATE vehicles SET status = 'Available' WHERE assigned to this event
  DELETE FROM event_vehicles WHERE event_id = event_id
  UPDATE bookings SET status = 'Cancelled', cancelled_by = vendor, cancelled_by_role = 'Vendor',
         cancel_reason = 'The vendor removed this event.', refund_percent = 100,
         refund_amount = total_price
     WHERE event_id = event_id AND status = 'Confirmed' AND booking_date >= today
       AND ticket is still 'Valid'
  UPDATE tickets SET status = 'Cancelled' for those bookings
  DELETE FROM events WHERE id = event_id
"""),
            ("validate_maps_url(url)", "Accepts an empty link or an https Google Maps link and returns the cleaned "
             "link or an error message.",
             """
FUNCTION validate_maps_url(url) RETURNS (clean_url, error)
  url = trimmed url
  IF url empty THEN RETURN ('', None)
  IF length > 500 OR url contains spaces THEN RETURN error
  add 'https://' when there is no scheme, change 'http://' to 'https://'
  IF host is maps.app.goo.gl OR goo.gl/maps OR a google domain with path /maps THEN RETURN (url, None)
  RETURN ('', 'Please use a Google Maps link')
"""),
        ],
    },
    {
        "name": "Booking, Pricing and Payment",
        "pspec": "This component turns a choice of event, date and guests into a paid booking. The event page shows "
                 "a calendar with only the allowed dates, the capacity bar ('N of TOTAL remaining', 'Hurry up!' "
                 "when few seats are left) and the price. The payment window shows the base price, VAT (5%) and "
                 "total in the currency the user picks. After a demo payment is approved the server saves the "
                 "booking and a new ticket. The Booking Details window then shows every detail and can save a "
                 "PDF. Customers book 1 to 10 guests. Partners have no per-booking guest limit and can collect "
                 "several events in a shopping list and pay for all of them at once.",
        "interface": [
            ["GET /api/events/<id>/capacity?date=", "event id, date", "total, source, vehicles, booked, remaining"],
            ["POST /api/bookings", "customer_email, event_id, booking_date, guests, client_name", "booking with base_price, vat, total_price, ticket_code"],
            ["GET /api/bookings/customer/<email>", "email", "list of bookings with status and refund info"],
            ["POST /api/cart, GET /api/cart/<email>", "partner_email, event_id, booking_date, guests, client_name", "success, cart items"],
            ["POST /api/cart/<email>/checkout", "partner email", "list of bookings, or nothing booked"],
        ],
        "classes": "screens/event_screen.show_event_screen, CustomerWelcomeScreen, PartnerWelcomeScreen, "
                   "payment.py (verify_demo_payment, show_demo_payment_modal, show_booking_details_window), "
                   "pricing.py (vat_breakdown, convert, format_money), booking_pdf.py (build_pdf, save_pdf) and "
                   "the CapacityBar widget. Server: create_booking, _book, _capacity_info, add_vat, "
                   "_new_ticket_code, add_to_cart, checkout_cart.",
        "restrictions": "Payment is a demo. It only checks that the form still holds the fixed demo card or bank "
                        "details. Currency rates are fixed numbers, not live rates, and every amount is charged in "
                        "AED. The payment is approved on the client before the server saves the booking, so if the "
                        "booking then fails the Booking Details window says 'NOT CONFIRMED' and asks the user to "
                        "contact support.",
        "performance": "A booking is one short write transaction. BEGIN IMMEDIATE takes the write lock at the start, "
                       "so two bookings for the last seats are handled one after the other.",
        "constraints": "The date must be today or later and allowed by the event (the right weekday for recurring "
                       "events, the exact date for one-time events). Guests must not be more than the seats left on "
                       "that date.",
        "ops": [
            ("_book(conn, email, event_id, date, guests, is_partner, client_name)",
             "Validates the request, checks capacity for that date, adds VAT, creates a unique 16-digit ticket and "
             "saves the booking, all inside the caller's transaction.",
             """
FUNCTION _book(conn, email, event_id, date, guests, is_partner, client_name)
  IF date or guests invalid THEN REFUSE 'Invalid date or number of guests.'
  IF guests < 1 THEN REFUSE
  IF NOT is_partner AND guests > 10 THEN REFUSE 'You can book 1 to 10 guests at a time.'
  IF date < today THEN REFUSE
  event = SELECT event with venue
  IF event missing OR NOT _event_allows_date(event, date) THEN REFUSE
  cap = _capacity_info(conn, event_id, date)
  IF guests > cap.remaining THEN REFUSE 'fully booked' or 'Not enough seats'
  code = _new_ticket_code(conn)        -- random 16 digits not used before
  (base, vat, total) = add_vat(price_to_int(event.price) * guests)
  INSERT INTO tickets (code, title, email, 'Valid')
  INSERT INTO bookings (..., total, code, 'Confirmed', client_name)
  RETURN success with booking, base and vat
"""),
            ("_capacity_info(conn, event_id, day)", "Total seats come from the assigned vehicles when there are any, "
             "otherwise from the event capacity. Booked seats are the confirmed guests on that date.",
             """
FUNCTION _capacity_info(conn, event_id, day)
  groups = assigned vehicles of the event grouped by type, with seats per type
  IF groups not empty THEN total = SUM(count * seats_per_type), source = 'vehicles'
  ELSE total = events.capacity (or 20), source = 'event'
  booked = SUM(guests) of 'Confirmed' bookings for event_id on day
  remaining = MAX(0, total - booked)
  RETURN total, source, booked, remaining
"""),
            ("checkout_cart(partner_email)", "Books every cart item in one transaction. If one item fails, none is "
             "kept and the cart stays as it was.",
             """
FUNCTION checkout_cart(partner_email)
  items = get_cart_items(partner_email)
  IF items empty THEN REFUSE 'Shopping list is empty.'
  BEGIN IMMEDIATE
  FOR EACH item IN items
     result = _book(conn, partner_email, item..., is_partner = true)
     IF NOT result.success THEN ROLLBACK and REFUSE 'No booking was made'
  COMMIT
  clear_cart(partner_email)
  RETURN all bookings
"""),
            ("vat_breakdown(base) and format_money(amount, currency)", "Client helpers used by the payment window "
             "and the receipt.",
             """
FUNCTION vat_breakdown(base)
  base = round(base, 2), vat = round(base * 0.05, 2)
  RETURN (base, vat, round(base + vat, 2))
FUNCTION format_money(amount_aed, currency)
  RETURN round(amount_aed * CURRENCY_RATES[currency], 2) formatted with the currency code
"""),
        ],
    },
    {
        "name": "Cancellation and Refund",
        "pspec": "This component cancels bookings under one policy. A customer or partner can cancel their own "
                 "booking and gets 100% back 48 hours or more before the start, 50% between 48 and 24 hours, "
                 "and cannot cancel in the last 24 hours. A vendor (for bookings on their own events) and an admin "
                 "(for any booking) can cancel until the event starts, always with a full refund, and must give "
                 "a reason of at most 300 characters. VAT is refunded in the same proportion. Every cancellation "
                 "stores when, who, which role, why, the percent and the amount. Cancelling frees the seats at once.",
        "interface": [
            ["POST /api/bookings/<id>/cancel", "customer_email, reason", "refund percent, base, vat, total"],
            ["POST /api/bookings/<id>/vendor_cancel", "vendor_email, reason", "refund (Vendor role checked)"],
            ["POST /api/admin/bookings/<id>/cancel", "admin_email, reason", "refund (admin checked)"],
            ["GET /api/admin/bookings", "admin_email", "every booking"],
        ],
        "classes": "welcome/cancellation.py (policy_line, cancelled_line, confirm_own_cancel, ask_reason), "
                   "pricing.refund_breakdown and the cancel buttons in the customer, partner, vendor and admin "
                   "screens. Server: _cancel, cancel_booking, vendor_cancel_booking, admin_cancel_booking, "
                   "refund_percent_for, split_refund, _event_start.",
        "restrictions": "Refunds are recorded only. No money is sent anywhere. A booking without a time counts "
                        "from midnight of its date.",
        "performance": "One short transaction per cancellation (BEGIN IMMEDIATE).",
        "constraints": "A used (checked-in) ticket cannot be cancelled. A started event cannot be cancelled by anyone.",
        "ops": [
            ("_cancel(booking_id, actor_email, actor_role, reason, owner_check, by_operator)",
             "Shared logic for all three kinds of cancellation. Figure 14 shows the same decision as an activity "
             "diagram.",
             """
FUNCTION _cancel(booking_id, actor, role, reason, owner_check, by_operator)
  IF length(reason) > 300 THEN REFUSE
  IF by_operator AND reason empty THEN REFUSE 'Please give the customer a reason'
  BEGIN IMMEDIATE
  row = booking joined with its event
  IF row missing OR owner_check(row) fails THEN REFUSE
  IF row.status <> 'Confirmed' THEN REFUSE
  start = _event_start(row.date, row.time)
  IF now >= start THEN REFUSE 'already started'
  percent = 100 IF by_operator ELSE refund_percent_for(start)
  IF percent is None THEN REFUSE 'Cancellations close 24 hours before'
  IF UPDATE tickets SET status = 'Cancelled' WHERE code AND status = 'Valid' changed no row
     THEN REFUSE 'ticket was already used'
  (base, vat, refund) = split_refund(row.total_price, percent)
  UPDATE bookings SET status = 'Cancelled', cancelled_at = now, cancelled_by = actor,
         cancelled_by_role = role, cancel_reason = reason, refund_percent = percent,
         refund_amount = refund
  RETURN success with refund
"""),
            ("refund_percent_for(start) and split_refund(total, percent)", "The policy steps and the VAT split of "
             "a refund.",
             """
FUNCTION refund_percent_for(start)
  hours_left = (start - now) in hours
  IF hours_left >= 48 THEN RETURN 100
  IF hours_left >= 24 THEN RETURN 50
  RETURN None
FUNCTION split_refund(total, percent)
  refund = round(total * percent / 100, 2)
  base = round(refund / 1.05, 2)
  RETURN (base, refund - base, refund)
"""),
        ],
    },
    {
        "name": "Venue Operations (Staff)",
        "pspec": "Every staff account works at one venue. The Venue Operations page shows the venue, its manager "
                 "email, a ticket check-in card and the schedule of the day for that venue (bookings, guests and "
                 "guests already checked in). The server enforces the venue scope: a ticket for another venue is "
                 "refused, the schedule never includes other venues, and the Support Tickets page lists only "
                 "questions about the staff member's venue (old tickets that name no event are shown to all staff). "
                 "A ticket can be checked in only once.",
        "interface": [
            ["POST /api/tickets/verify", "staff_email, ticket_code, expected_event_title", "access granted with guest count, or refusal"],
            ["GET /api/events/today?staff_email=", "staff email", "today's events of the venue, or 403"],
            ["GET /api/support/open?staff_email=", "staff email", "open tickets of the venue, or 403"],
            ["POST /api/support/<id>/resolve", "staff_email", "resolved, or not for your venue"],
        ],
        "classes": "StaffWelcomeScreen (build_operations_content, build_checkin_card, render_today_schedule, "
                   "build_support_content), DigitBoxes for the 16-digit code. Server: staff_verify_ticket, "
                   "verify_ticket_code, _ticket_venue_id, get_staff_schedule, get_events_today, "
                   "get_staff_support_tickets, staff_resolve_support_ticket.",
        "restrictions": "Check-in uses a typed code. There is no QR scanner. Staff see only the schedule of today.",
        "performance": "get_events_today runs two small queries per event of the venue, which is fine for the number "
                       "of events one venue has in a day.",
        "constraints": "The update to 'Used' has the condition status = 'Valid', so two staff members cannot admit the "
                       "same ticket twice even at the same moment.",
        "ops": [
            ("staff_verify_ticket(staff_email, code, expected_title)", "Finds the staff venue and checks the ticket in "
             "only if it belongs to that venue.",
             """
FUNCTION staff_verify_ticket(staff_email, code, expected_title)
  venue = get_staff_venue(staff_email)     -- role Staff, not banned
  IF venue is None THEN REFUSE 'Only staff assigned to a venue can check tickets in.'
  ticket = SELECT event_title, customer_email, status FROM tickets WHERE ticket_code = code
  IF ticket missing THEN REFUSE 'Invalid ticket code.'
  IF venue of the ticket's event <> venue.id THEN REFUSE 'not for an event at your venue'
  IF expected_title given AND differs THEN REFUSE 'Wrong event.'
  IF status = 'Cancelled' OR status = 'Used' THEN REFUSE
  UPDATE tickets SET status = 'Used' WHERE ticket_code = code AND status = 'Valid'
  IF no row changed THEN REFUSE 'just used or cancelled'
  RETURN 'Access granted' with the number of guests and a note if the date is not today
"""),
        ],
    },
    {
        "name": "Fleet and Dispatch",
        "pspec": "The dispatcher registers vehicles (license number, type, location), keeps their status "
                 "(Available, Assigned, Maintenance) and assigns a combination of available vehicles to an event. "
                 "When an event has assigned vehicles, its capacity becomes the sum of their seats (for example two "
                 "4x4 Land Cruisers give 12 seats). Freeing a vehicle or setting it Available or Maintenance ends "
                 "its assignment, and the event capacity goes back to the vendor's number.",
        "interface": [
            ["GET /api/vehicle_types", "none", "types with seats"],
            ["GET /api/vehicles/<dispatcher_email>", "email", "vehicles of that dispatcher"],
            ["POST /api/vehicles, DELETE /api/vehicles/<id>", "vehicle fields", "success"],
            ["PUT /api/vehicles/<id>/status, POST /api/vehicles/<id>/free", "status", "success"],
            ["POST /api/dispatch", "event_id, vehicle_assignments", "number assigned"],
            ["GET /api/dispatch/<event_id>/vehicles", "event id", "assigned vehicles"],
        ],
        "classes": "DispatcherWelcomeScreen with VehicleView (Register Vehicles, Fleet Maintenance) and DispatchView "
                   "(Event Dispatch). Both use table_style.py for filterable tables. Server: create_vehicle, "
                   "update_vehicle_status, free_vehicle, dispatch_vehicle_combination, get_dispatches_by_event.",
        "restrictions": "The vehicle and dispatch endpoints do not check the caller's role or ownership. Vehicles are "
                        "assigned to an event as a whole, not to a single date. The auto_reassign_recurring flag is "
                        "stored and shown but no scheduler uses it yet.",
        "performance": "Capacity is computed with one grouped query, so it stays fast with many vehicles.",
        "constraints": "Only vehicles with status 'Available' can be assigned. The UPDATE has this condition, so a "
                       "vehicle cannot be assigned twice.",
        "ops": [
            ("dispatch_vehicle_combination(event_id, assignments)", "Assigns each available vehicle and records the "
             "link.",
             """
FUNCTION dispatch_vehicle_combination(event_id, assignments)
  assigned = 0
  FOR EACH item IN assignments
     changed = UPDATE vehicles SET status = 'Assigned', auto_reassign_recurring = item.flag
               WHERE id = item.vehicle_id AND status = 'Available'
     IF changed THEN
        INSERT INTO event_vehicles (event_id, item.vehicle_id, 'Assigned')
        assigned = assigned + 1
  RETURN assigned
"""),
            ("update_vehicle_status(vehicle_id, status)", "Ends the assignment when the vehicle leaves 'Assigned'.",
             """
PROCEDURE update_vehicle_status(vehicle_id, status)
  IF status <> 'Assigned' THEN
     UPDATE event_vehicles SET status = 'Concluded' WHERE vehicle_id AND status = 'Assigned'
  UPDATE vehicles SET status = status WHERE id = vehicle_id
"""),
        ],
    },
    {
        "name": "Administration and Reports",
        "pspec": "The admin keeps the platform safe. The User Accounts page lists every account with role, sign-up "
                 "date, account age, status and, for staff, venue and manager email. The admin can ban and restore "
                 "accounts, but not their own account or another admin. A banned user cannot log in (HTTP 403) and "
                 "every write request from that email is refused by _blocked. Every other role has a Report button. "
                 "A report has a role-specific category, who it is about, an optional offender email, a summary and "
                 "details. The admin reads open reports first, resolves them or bans the offender (which also "
                 "resolves the report). The admin also sees and can cancel every booking.",
        "interface": [
            ["GET /api/admin/users?admin_email=", "admin email", "all accounts, or 403"],
            ["POST /api/admin/users/ban", "admin_email, email, banned", "success or reason"],
            ["POST /api/reports", "reporter_email, category, offender_type, offender_email, subject, description", "report id"],
            ["GET /api/admin/reports", "admin_email", "reports, open first"],
            ["POST /api/admin/reports/<id>/resolve", "admin_email, resolution", "success"],
        ],
        "classes": "AdminWelcomeScreen (build_users_content, build_reports_content, build_bookings_content, "
                   "_open_ban_picker), ReportView with REPORT_OPTIONS per role. Server: is_admin, active_role, "
                   "get_all_users, set_user_banned, create_report, get_reports, resolve_report, _blocked.",
        "restrictions": "Admin requests are trusted by the admin_email they carry. The server checks that this email "
                        "belongs to an active admin, but there is no token that proves who sent the request.",
        "performance": "The user and report lists are read in one query each.",
        "constraints": "A user can have at most 5 open reports and cannot report their own account. Admins cannot file "
                       "reports.",
        "ops": [
            ("set_user_banned(admin_email, email, banned)", "Bans or restores one account.",
             """
FUNCTION set_user_banned(admin_email, email, banned)
  IF NOT is_admin(admin_email) THEN REFUSE 'Only an admin can do this.'
  IF email = admin_email THEN REFUSE 'You cannot ban your own account.'
  row = role of email
  IF row missing THEN REFUSE
  IF row.role = 'Admin' THEN REFUSE 'Admin accounts cannot be banned.'
  IF banned THEN UPDATE users SET banned = 1, banned_at = now, banned_by = admin_email
  ELSE UPDATE users SET banned = 0, banned_at = NULL, banned_by = NULL
"""),
            ("_blocked(email, *roles)", "Guard used by the write endpoints of server.py.",
             """
FUNCTION _blocked(email, roles)
  role = active_role(email)        -- None when unknown or banned
  IF role is None THEN RETURN HTTP 403 'unknown or banned'
  IF roles given AND role NOT IN roles THEN RETURN HTTP 403 'Only <roles> accounts can do this.'
  RETURN None
"""),
        ],
    },
    {
        "name": "Reviews and Support Tickets",
        "pspec": "After an experience a customer opens My Experiences, which lists bookings that were checked in or "
                 "whose date has passed. The customer gives a rating from 0 to 5 in steps of 0.5 and an optional "
                 "comment. A second review of the same booking updates the first one. The explore page shows the "
                 "average rating per event, rounded to one decimal. Customers can also open support tickets about "
                 "an event, and venue staff answer them (see the Venue Operations component).",
        "interface": [
            ["GET /api/experiences/customer/<email>", "email", "past bookings with their review"],
            ["POST /api/reviews", "customer_email, booking_id, rating, comment", "thank you message"],
            ["GET /api/events/ratings", "none", "average and count per event"],
            ["POST /api/support", "customer_email, event_title, subject, message", "ticket id"],
            ["GET /api/support/customer/<email>", "email", "the customer's tickets"],
        ],
        "classes": "CustomerWelcomeScreen (build_experiences_content, open_review_window, build_support_content). "
                   "Server: get_my_experiences, submit_review, get_event_ratings, _ensure_reviews_table, "
                   "create_support_ticket.",
        "restrictions": "Staff can mark a ticket resolved but cannot write an answer inside the app.",
        "performance": "Ratings for all events are computed with one GROUP BY query.",
        "constraints": "A support ticket must name an event that is listed or that the customer booked before. Subject "
                       "needs 3 characters, message 10 characters, and a customer can have at most 3 open tickets.",
        "ops": [
            ("submit_review(email, booking_id, rating, comment)", "Saves or updates a review of an attended booking.",
             """
FUNCTION submit_review(email, booking_id, rating, comment)
  IF rating < 0 OR rating > 5 OR rating * 2 is not whole THEN REFUSE
  IF length(comment) > 500 THEN REFUSE
  allowed = bookings of email with status 'Checked in' or 'Expired'
  IF booking_id NOT IN allowed THEN REFUSE 'only experiences that you already attended'
  INSERT INTO reviews ... ON CONFLICT(booking_id) DO UPDATE rating, comment, updated_at
"""),
        ],
    },
]

for n, comp in enumerate(COMPONENTS, start=1):
    # Numbering follows the template: section 3.2 is repeated for each component.
    name = comp["name"]
    h(2, f"3.2 Description for Component {n}: {name}")
    h(3, f"3.2.1 Processing narrative (PSPEC) for {name}")
    para(comp["pspec"])
    h(3, f"3.2.2 {name} interface description")
    para("The client calls these REST endpoints through api_client.py. All bodies and answers are JSON.")
    table(["Endpoint", "Input", "Output"], comp["interface"], f"Interface of the {name} component",
          widths=[2.3, 2.2, 2.0], font=8.5)
    h(3, f"3.2.3 {name} processing detail")
    h(4, f"3.2.3.1 Design class hierarchy for {name}")
    para(comp["classes"])
    h(4, f"3.2.3.2 Restrictions and limitations for {name}")
    para(comp["restrictions"])
    h(4, f"3.2.3.3 Performance issues for {name}")
    para(comp["performance"])
    h(4, f"3.2.3.4 Design constraints for {name}")
    para(comp["constraints"])
    h(4, f"3.2.3.5 Processing detail for each operation of {name}")
    h(4, "3.2.3.5.1 Processing narrative (PSPEC) for each operation")
    for i, (op, narrative, _) in enumerate(comp["ops"], start=1):
        para(narrative, bold_lead=f"{i}. {op}: ")
    h(4, "3.2.3.5.2 Algorithmic model (PDL) for each operation")
    for i, (op, _, pdl) in enumerate(comp["ops"], start=1):
        para("", bold_lead=f"{i}. {op}").paragraph_format.keep_with_next = True
        code(pdl)

h(2, "3.3 Dynamic behavior of the components")
para("This section shows how the classes and modules work together at run time. Each sequence diagram "
     "follows the real function calls in the code. The state and activity diagrams show the life of a booking, "
     "the life of a vehicle and the refund decision.")
h(3, "3.3.1 Interaction diagrams")
para("Booking with VAT and currency (component 3). The capacity is read first for the chosen date. The payment "
     "window adds VAT and converts the display currency. Only after the demo payment is approved does the "
     "client send the booking, and the server checks capacity again inside its transaction.",
     bold_lead=None)
uml("07_seq_booking_vat", "Sequence diagram: customer books an event and pays", max_height=8.0)
para("Cancellation with refund (component 4). The client shows the refund the user would get before they "
     "confirm. The server decides the real percent and marks the ticket as cancelled only if it is still valid.")
uml("08_seq_cancel_refund", "Sequence diagram: booker cancels a booking and gets a refund", max_height=8.0)
para("Ticket check-in (component 5). The venue of the staff member is found on the server. A ticket for another "
     "venue is refused without giving details about it.")
uml("09_seq_staff_checkin", "Sequence diagram: staff checks a ticket in", max_height=8.0)
para("Partner checkout (component 3). All cart items are booked inside one transaction, so the partner never "
     "gets half a cart.")
uml("10_seq_partner_checkout", "Sequence diagram: partner pays the whole shopping list at once", max_height=8.0)
para("Report and ban (component 7). A report reaches the admin, who bans the offender and resolves the report.")
uml("11_seq_admin_report_ban", "Sequence diagram: report and ban", max_height=8.0)
h(3, "3.3.2 State and activity diagrams")
uml("12_state_booking", "State diagram of a booking and its ticket", width=5.6)
uml("13_state_vehicle", "State diagram of a vehicle", width=4.2)
uml("14_activity_refund_policy", "Activity diagram of the refund decision in _cancel()", max_height=8.4)
page_break()

# ===========================================================================
# 4.0 User interface design
# ===========================================================================
h(1, "4.0 User interface design")
para("Rihla is a desktop program that opens maximised. The login, sign-up and password screens use a split "
     "layout: a picture of Dubai with the Rihla logo on the left and the form on the right. After login every "
     "role gets the same frame: a dark side menu on the left with the role name, the role's pages, and the "
     "Report, Settings and Log Out buttons at the bottom. A white top bar shows who is signed in and a live "
     "clock. The main area scrolls.")

h(2, "4.1 Description of the user interface")
h(3, "4.1.1 Screen images")
para("The screenshots below were taken from the running application with the demo data from dummy_data.ps1.")
SCREEN_LIST = [
    ("01_login", "Login screen with Google and Apple buttons and quick demo account chips"),
    ("02_create_account", "Create Account screen with the account type picker"),
    ("03_customer_explore", "Customer home: Explore Tours with categories, search, ratings and capacity bars"),
    ("04_event_page", "Event page with picture, details, capacity, calendar of allowed dates and price summary"),
    ("05_payment", "Payment window with currency picker, VAT line and prefilled demo card"),
    ("06_booking_details", "Booking Details window after payment with Download PDF"),
    ("07_customer_bookings", "My Bookings with ticket codes, statuses and Copy code buttons"),
    ("08_vendor_events", "Vendor home: My Events with pictures, Edit and Delete"),
    ("09_vendor_bookings", "Vendor Bookings table with filterable columns and cancelled rows"),
    ("10_staff_operations", "Staff Venue Operations: venue, ticket check-in and the schedule of the day"),
    ("11_partner_cart", "Partner shopping list with one payment for all events"),
    ("12_dispatch", "Dispatcher Event Dispatch panel with available and assigned vehicles"),
    ("13_admin_users", "Admin User Accounts with account type counts, sign-up date, age and status"),
    ("14_admin_reports", "Admin Reports inbox with Resolve and Ban offender buttons"),
    ("15_report_form", "Report form used by every non-admin role"),
]
for name, caption in SCREEN_LIST:
    small = name in ("05_payment", "06_booking_details")
    shot(name, caption, width=3.6 if small else 6.3)

h(3, "4.1.2 Objects and actions")
table(["Screen", "Objects", "Actions"], [
    ["Login", "Email and password fields, eye button, Sign In, Google and Apple buttons, demo chips, links",
     "Sign in, show password, fill a demo account, open sign-up or Forgot password"],
    ["Create Account", "Account type menu, SSN digit boxes, venue menu and manager email (staff), email and phone with "
     "Verify buttons, password strength label, Terms check box", "Pick role, verify email and phone with code 000000, "
     "register"],
    ["Forgot / Reset password", "Email field, Send Code, 6-digit code, new password fields", "Send code, verify, save new password"],
    ["Explore Tours (Customer, Partner)", "Search box, category chips, Filter window with price slider, event cards "
     "with picture, rating, capacity bar and View Details", "Search, filter, open event"],
    ["Event page", "Cover picture, venue link with Open in Google Maps, capacity bar, calendar, guests spinner, "
     "client name (partner), price summary", "Choose date and guests, Proceed to Booking, Add to List, Pay Now"],
    ["Payment window", "Order summary, currency box, Base Price, VAT and Total, Visa, Mastercard and Bank Transfer "
     "options, prefilled fields, Reset Details", "Change currency, change method, Pay, Cancel"],
    ["Booking Details", "Read-only receipt text", "Download PDF, Close"],
    ["My Bookings / Partner Bookings", "Booking cards with status, ticket code, refund policy line, Refresh",
     "Copy code, Cancel booking"],
    ["My Experiences", "Past bookings with stars", "Rate and comment"],
    ["Support (Customer)", "Event menu, subject, message, list of own tickets", "Send ticket"],
    ["Vendor pages", "Event cards, event form (picture, recurrence days, capacity), bookings table with gear filters, "
     "venues list, categories list", "Add, edit, delete events, venues and categories, cancel a booking with a reason"],
    ["Venue Operations (Staff)", "Venue and manager line, event menu, 16 digit boxes, Validate, schedule table",
     "Check a ticket in, refresh"],
    ["Support Tickets (Staff)", "List of open tickets of the venue", "Resolve"],
    ["Dispatcher pages", "Vehicle form, fleet table with filters and check boxes, event menu, type and location "
     "filters, assigned list", "Register, set Maintenance or Available, delete, assign, free"],
    ["Admin pages", "Account type counts, users table, reports inbox, bookings table", "Ban, restore, resolve, "
     "ban offender, cancel any booking"],
    ["Settings (all roles)", "Preferred currency, staff venue and manager email, change password",
     "Save settings"],
    ["Report (non-admin)", "Category, about whom, offender email, summary, details", "Submit report"],
], "Screen objects and actions", widths=[1.4, 2.9, 2.2], font=8.5)

h(2, "4.2 Interface design rules")
para("We followed Shneiderman's eight golden rules. The table shows where each rule appears in Rihla.")
table(["Golden rule", "How Rihla follows it"], [
    ["1. Strive for consistency", "One frame (BaseWelcomeScreen) for all roles, one colour and font file (theme.py), "
     "one table style (table_style.py) with bold headings and a gear on filterable columns."],
    ["2. Seek universal usability", "Quick demo account chips for new users, prefilled demo payment details for "
     "experts and testers, prices in four currencies."],
    ["3. Offer informative feedback", "Capacity bar with 'N of TOTAL remaining' and 'Hurry up!', strength label for "
     "passwords, payment declines shown inside the payment window, clear server messages."],
    ["4. Design dialogs to yield closure", "After payment the Booking Details window sums up the whole booking with "
     "the ticket code and a PDF button."],
    ["5. Prevent errors", "The calendar only allows valid dates, DigitBoxes only accept digits, the role picker hides "
     "fields that do not apply, the server checks everything again."],
    ["6. Permit easy reversal of actions", "Bookings can be cancelled under a clear policy, cart items can be "
     "removed, banned accounts can be restored, Reset Details restores the payment form."],
    ["7. Keep users in control", "Cancellation shows the refund before the user confirms. Pages that show other "
     "people's changes have a Refresh button."],
    ["8. Reduce short-term memory load", "Ticket codes are grouped in four blocks of four digits with a Copy code "
     "button. The top bar always shows the signed-in email."],
], "Eight golden rules in Rihla", widths=[2.0, 4.5])

h(2, "4.3 Components available")
para("The interface is built only with the standard Tkinter toolkit and two small libraries:")
bullets([
    ("tkinter: ", "Tk, Toplevel, Frame, Label, Button, Entry, Text, Canvas, Scrollbar, Scale, Radiobutton, "
     "Checkbutton, OptionMenu and messagebox, filedialog."),
    ("tkinter.ttk: ", "Combobox (currency and other choices) and Treeview (all tables)."),
    ("Custom widgets: ", "DigitBoxes (digit-per-box input for SSN and ticket codes), CapacityBar (seat bar), "
     "CoverImage and build_card_shell (event cards with pictures), venue_label (map link)."),
    ("Pillow: ", "loading, resizing and showing event pictures."),
    ("tksvg (optional): ", "draws the Lucide SVG icons. Without it the app still runs with fewer icons."),
])

h(2, "4.4 UIDS description")
para("We did not use a user interface development system or a GUI builder. All screens are written by hand in "
     "Python with Tkinter. To keep the code tidy we use shared modules instead: theme.py for colours and fonts, "
     "table_style.py for tables, ui.clear_window to swap screens, navigate.py to move between screens and "
     "routing.py to pick the home screen of a role. Adding a role needs one new welcome module and one line in "
     "routing.py.")
page_break()

# ===========================================================================
# 5.0 Restrictions
# ===========================================================================
h(1, "5.0 Restrictions, limitations, and constraints")
para("The following design issues limit the current version. We list them openly because they matter for anyone "
     "who wants to run Rihla outside a classroom demo.")
bullets([
    ("No login tokens: ", "the server does not give the client a session token. Requests carry an email, and the "
     "server trusts it. The server does check that the email belongs to an active account with the right role "
     "(_blocked, is_admin), but a person who sends hand-made HTTP requests could act as another user."),
    ("Missing ownership checks: ", "PUT /api/users/password has no check, and event update and delete, venue delete, "
     "and the vehicle and dispatch endpoints do not check that the caller owns the record."),
    ("Local only: ", "the server listens on 127.0.0.1 port 5000 with plain HTTP and the Flask development server. It "
     "is meant for one machine. It is not ready for the internet (no HTTPS, no production server)."),
    ("Demo payments and refunds: ", "payments only compare the form with fixed demo details. Refunds are stored in "
     "the database but no money moves."),
    ("Fixed currency rates: ", "USD, EUR and GBP use fixed rates in pricing.py. Everything is charged and stored in AED."),
    ("Fake verification: ", "email, phone and password reset codes are always 000000. Google and Apple login is a "
     "normal email login."),
    ("SQLite: ", "one database file is simple and needs no setup, but it allows only one writer at a time. BEGIN "
     "IMMEDIATE makes bookings safe, but many parallel users would wait for each other."),
    ("Prices as text: ", "prices are saved as text such as '240 AED' and only the digits are used, so prices with "
     "decimals are not supported."),
    ("Email as link: ", "many tables point to users by email instead of a numeric key, so an email cannot be changed "
     "without updating other tables."),
    ("Server time: ", "all times use the local time of the server machine, not a fixed time zone."),
    ("Features from Phase 1 that were not built: ", "QR codes, an offline driver app, live vehicle tracking, email "
     "and SMS messages, the 15-minute seat lock (replaced by the transaction check) and Arabic language support."),
    ("Platform: ", "the client is tested on Windows. Some parts (Downloads folder lookup, zoomed window) have "
     "fallbacks for other systems but were not tested there."),
])
page_break()

# ===========================================================================
# 6.0 Testing issues
# ===========================================================================
h(1, "6.0 Testing Issues")
para("Rihla has an automated test suite in the tests/ folder that uses Python's unittest. The tests point the "
     "database to a temporary file, so they never change server/users.db. They import the server modules directly "
     "(tests/db_test_helpers.py) and some tests call the Flask API through app.test_client(). A few tests open "
     "Tkinter windows for a short time. There are 70 tests. On 31 October 2026 all 70 passed in about five "
     "minutes on a team laptop. The whole suite runs with:")
code("python -m unittest discover -s tests")

h(2, "6.1 Classes of tests")
table(["Test class (file)", "Type", "What it covers"], [
    ["BookingTests (test_booking.py)", "Black-box unit", "Price with VAT and ticket code, refusals, booking the same "
     "event again, single check-in, cancel stops a ticket, rename and delete event, vendor view, schedule, support "
     "tickets"],
    ["CancellationTests (test_booking.py)", "White-box unit", "Refund steps at 48 h and 24 h, VAT in proportion, audit "
     "trail, vendor and admin cancellation, no cancel after start, event delete refunds, cart rollback"],
    ["CapacityTests (test_booking.py)", "White-box unit", "Event capacity, vehicle seats, same vehicle type adds up, "
     "freeing a vehicle, capacity per date, bad capacity values, old database upgrade"],
    ["PartnerAndPaymentTests (test_partner_and_payment.py)", "Unit and GUI", "CapacityBar text, partner bookings above "
     "10 guests, shopping list and checkout, remove from cart, demo payment success and failure"],
    ["AdminTests and ReportTests (test_admin.py)", "Black-box unit", "Admin demo account, no admin sign-up, sign-up "
     "time, ban and restore, admin limits, reports flow and rules, old database upgrade"],
    ["ApiAccountGuardTests (test_admin.py)", "Integration (Flask test client)", "Banned and unknown accounts cannot "
     "book or open tickets, cart and vendor actions need the right role"],
    ["StaffVenueTests (test_staff_venue.py)", "Integration", "Staff sign-up rules, venue-scoped check-in, schedule and "
     "support tickets, changing venue, banned staff, venue delete protection, admin columns"],
], "Classes of automated tests", widths=[2.2, 1.2, 3.1], font=9)
para("Black-box tests call a public function or endpoint with inputs and check only the result, for example that "
     "a booking of 3 guests at 240 AED stores a total of 756 AED. White-box tests are written with the code paths in mind, for "
     "example the boundaries of refund_percent_for at exactly 48 and 24 hours and the rollback branch of "
     "checkout_cart. Integration tests go through server.py with the Flask test client to check the role guards. "
     "Next to the automated tests we ran manual system tests with the per-role demo script in README.md, after "
     "seeding with dummy_data.ps1.")

h(2, "6.2 Expected software response")
table(["Test case", "Input", "Expected response"], [
    ["Booking price", "3 guests, event price 240 AED", "Base 720, VAT 36, total 756 AED stored, 16-digit code"],
    ["Too many guests (customer)", "11 guests", "Refused: 'You can book 1 to 10 guests at a time.'"],
    ["Partner group", "Partner books more than 10 guests", "Accepted while seats remain"],
    ["Past date", "booking_date yesterday", "Refused: date is in the past"],
    ["Wrong weekday", "Recurring Tue and Thu event on a Monday", "Refused: not available on that date"],
    ["Full event", "guests more than remaining seats", "Refused with remaining and total seats"],
    ["Vehicle capacity", "Two 4x4 Land Cruisers assigned", "Total capacity 12, source 'vehicles'"],
    ["Check-in twice", "Same valid code two times", "First: access granted, admit N guests. Second: already used"],
    ["Other venue", "Staff of Al Qudra checks the Burj Khalifa demo ticket", "Refused: not for an event at your venue"],
    ["Cancel 3 days before", "Customer cancels", "100% refund, ticket Cancelled, seats free"],
    ["Cancel 30 hours before", "Customer cancels", "50% refund, VAT refunded in proportion"],
    ["Cancel 10 hours before", "Customer cancels", "Refused: cancellations close 24 hours before"],
    ["Vendor cancel without reason", "Empty reason", "Refused: please give the customer a reason"],
    ["Cart with one bad item", "Checkout where one item has no seats", "No booking kept, cart unchanged"],
    ["Changed card number", "Payment form edited", "Payment declined, shown in the payment window"],
    ["Sign-up as Admin", "role = Admin", "Saved as Customer at most, never as Admin"],
    ["SSN rules", "Vendor with 15 digits or 16 equal digits", "Refused with a clear message"],
    ["Banned user", "Login and booking after ban", "Login 403, booking request 403"],
    ["Admin ban self", "Admin bans own email", "Refused: you cannot ban your own account"],
    ["Review rating", "rating 4.3", "Refused: steps of 0.5"],
], "Expected responses for the main test cases", widths=[1.6, 2.1, 2.8], font=8.5)

h(2, "6.3 Performance bounds")
bullets([
    "One booking, cancellation or check-in is a single short SQLite transaction. On the team's laptops the answer "
    "appears without a visible delay.",
    "The client waits at most 10 seconds for any HTTP request (timeout in api_client.py) and then tells the user that "
    "the server cannot be reached.",
    "Event pictures are at most 1400 pixels on the long side after upload and at most 4 MB on the server.",
    "Limits that protect the system: 10 guests per customer booking, 5000 seats per event, 3 open support tickets per "
    "customer, 5 open reports per user, 300 characters per cancel reason, 500 per review comment.",
    "The full test suite takes about five minutes because some tests open Tkinter windows and PBKDF2 hashing is slow "
    "on purpose.",
])

h(2, "6.4 Identification of critical components")
para("These parts need the most attention in testing because a mistake there costs money, seats or trust:")
bullets([
    ("_book and _capacity_info: ", "they decide if a seat can be sold. A bug here means double booking or empty seats."),
    ("_cancel, refund_percent_for and split_refund: ", "they decide how much money a customer gets back. The hour "
     "boundaries (48 and 24) and the VAT split must be exact."),
    ("checkout_cart: ", "it must keep all bookings of a cart or none of them."),
    ("staff_verify_ticket: ", "it must admit a ticket once and only at the right venue."),
    ("login_status, _blocked and set_user_banned: ", "they keep banned and unknown accounts out."),
    ("ssn_error and register_user: ", "they enforce the SSN rule and keep the raw SSN out of the database."),
    ("init_db: ", "it upgrades older databases. The tests create an old database on purpose and check the upgrade."),
])

page_numbers()
doc.save(OUT_DOCX)
print("saved", OUT_DOCX, "figures:", FIG[0], "tables:", TAB[0])

# Refresh the table of contents and export a PDF with Word (Windows only).
if sys.platform == "win32" and "--no-pdf" not in sys.argv:
    try:
        import win32com.client
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        d = word.Documents.Open(OUT_DOCX)
        d.TablesOfContents(1).Update()
        d.Fields.Update()
        d.Save()
        d.ExportAsFixedFormat(OUT_PDF, 17)
        d.Close(False)
        word.Quit()
        print("saved", OUT_PDF)
    except Exception as exc:
        print("PDF export skipped:", exc)
