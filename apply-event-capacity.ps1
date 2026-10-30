<#
.SYNOPSIS
  Adds event capacity to Rihla: customers see it when booking, and bookings above it are refused.

.DESCRIPTION
  Run this in:  C:\Dev\repos\Public repos\rihla_manual\
  It looks for the project in the current folder, then in .\rihla-new, and clones it into .\rihla-new if it is missing.

  What it changes:
    - events get a capacity (the vendor types it when creating or editing an event)
    - an event with vehicles takes as many guests as the seats of its vehicles (any mix of types)
    - an event with no vehicles uses the capacity the vendor typed
    - the booking screen shows the capacity, the vehicles and the seats left for the chosen date
    - a booking that is bigger than the seats left is refused (the check is also in the database layer)
    - old databases get the new column by themselves the next time the app starts

  Safe to run: every edit is checked first, nothing is written if one check fails, changed files are
  copied to .fix-backup\ (already ignored by git), and running it twice does nothing the second time.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\apply-event-capacity.ps1
#>

$ErrorActionPreference = 'Stop'
$RepoUrl = 'https://github.com/IamOumarIbrahim/rihla-new'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

# ---------------------------------------------------------------- find (or clone) the project
$here = (Get-Location).Path
if (Test-Path -LiteralPath (Join-Path $here 'src\database.py')) {
    $repo = $here
}
elseif (Test-Path -LiteralPath (Join-Path $here 'rihla-new\src\database.py')) {
    $repo = Join-Path $here 'rihla-new'
}
else {
    Write-Host "Project not found here. Cloning $RepoUrl ..." -ForegroundColor Cyan
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'git is not installed or not in PATH.' }
    & git clone $RepoUrl (Join-Path $here 'rihla-new')
    if ($LASTEXITCODE -ne 0) { throw 'git clone failed.' }
    $repo = Join-Path $here 'rihla-new'
}
Write-Host "Project folder: $repo" -ForegroundColor Cyan

$dbFile = Join-Path $repo 'src\database.py'
if ((Get-Content -LiteralPath $dbFile -Raw) -match 'def get_event_capacity') {
    Write-Host 'Event capacity is already installed. Nothing to do.' -ForegroundColor Yellow
    return
}

# ---------------------------------------------------------------- the edits (exact find and replace)
$edits = New-Object System.Collections.Generic.List[object]
function Add-Edit($path, $old, $new) {
    $edits.Add([pscustomobject]@{ Path = $path; Old = $old; New = $new }) | Out-Null
}

$old = @'
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db")

'@
$new = @'
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db")

# Guests an event can take on one date when no vehicles are assigned to it.
DEFAULT_EVENT_CAPACITY = 20
MAX_EVENT_CAPACITY = 5000

'@
Add-Edit 'src/database.py' $old $new

$old = @'
                recur_time TEXT,
                FOREIGN KEY(venue_id) REFERENCES venues(id)
'@
$new = @'
                recur_time TEXT,
                capacity INTEGER NOT NULL DEFAULT 20,
                FOREIGN KEY(venue_id) REFERENCES venues(id)
'@
Add-Edit 'src/database.py' $old $new

$old = @'
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM vehicle_types")
'@
$new = @'
        # Databases made before event capacity existed get the new column (old events start at 20).
        event_columns = [row[1] for row in conn.execute("PRAGMA table_info(events)")]
        if "capacity" not in event_columns:
            conn.execute(f"ALTER TABLE events ADD COLUMN capacity INTEGER NOT NULL DEFAULT {DEFAULT_EVENT_CAPACITY}")

        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM vehicle_types")
'@
Add-Edit 'src/database.py' $old $new

$old = @'
"One-Time", "N/A", "23:00"),
'@
$new = @'
"One-Time", "N/A", "23:00", 40),
'@
Add-Edit 'src/database.py' $old $new

$old = @'
"Recurring", "Tuesday, Thursday", "15:30")
            ]
            conn.executemany("INSERT INTO events (title, category, price, description, vendor_email, venue_id, event_datetime, is_recurring, recur_day, recur_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", demo_events)
'@
$new = @'
"Recurring", "Tuesday, Thursday", "15:30", 30)
            ]
            conn.executemany("INSERT INTO events (title, category, price, description, vendor_email, venue_id, event_datetime, is_recurring, recur_day, recur_time, capacity) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", demo_events)
'@
Add-Edit 'src/database.py' $old $new

$old = @'
def create_event(title, category, price, description, vendor_email, venue_id, event_datetime, is_recurring, recur_day, recur_time):
    with _connect() as conn:
        conn.execute(
            "INSERT INTO events (title, category, price, description, vendor_email, venue_id, event_datetime, is_recurring, recur_day, recur_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (title, category, price, description, vendor_email, venue_id, event_datetime, is_recurring, recur_day, recur_time)
        )
'@
$new = @'
def _capacity_or_default(value):
    """None -> the default capacity. Anything else must be a whole number from 1 to MAX_EVENT_CAPACITY."""
    if value is None:
        return DEFAULT_EVENT_CAPACITY
    value = int(value)
    if not 1 <= value <= MAX_EVENT_CAPACITY:
        raise ValueError(f"Capacity must be between 1 and {MAX_EVENT_CAPACITY}.")
    return value

def create_event(title, category, price, description, vendor_email, venue_id, event_datetime, is_recurring, recur_day, recur_time, capacity=None):
    capacity = _capacity_or_default(capacity)
    with _connect() as conn:
        conn.execute(
            "INSERT INTO events (title, category, price, description, vendor_email, venue_id, event_datetime, is_recurring, recur_day, recur_time, capacity) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (title, category, price, description, vendor_email, venue_id, event_datetime, is_recurring, recur_day, recur_time, capacity)
        )
'@
Add-Edit 'src/database.py' $old $new

$old = @'
def update_event(event_id, title, category, price, description, venue_id, event_datetime, is_recurring, recur_day, recur_time):
    with _connect() as conn:
'@
$new = @'
def update_event(event_id, title, category, price, description, venue_id, event_datetime, is_recurring, recur_day, recur_time, capacity=None):
    """capacity=None keeps the capacity the event already has."""
    new_capacity = None if capacity is None else _capacity_or_default(capacity)
    with _connect() as conn:
        if new_capacity is not None:
            conn.execute("UPDATE events SET capacity = ? WHERE id = ?", (new_capacity, event_id))
'@
Add-Edit 'src/database.py' $old $new

$old = @'
            SELECT e.id, e.title, e.category, e.price, e.description, e.vendor_email, v.name, e.event_datetime, e.is_recurring, e.recur_day, e.recur_time, e.venue_id
            FROM events e LEFT JOIN venues v ON e.venue_id = v.id
        ''').fetchall()
    return [{"id": r[0], "title": r[1], "category": r[2], "price": r[3], "desc": r[4], "vendor_email": r[5], "venue_name": r[6], "event_datetime": r[7], "is_recurring": r[8], "recur_day": r[9], "recur_time": r[10], "venue_id": r[11]} for r in rows]
'@
$new = @'
            SELECT e.id, e.title, e.category, e.price, e.description, e.vendor_email, v.name, e.event_datetime, e.is_recurring, e.recur_day, e.recur_time, e.venue_id, e.capacity
            FROM events e LEFT JOIN venues v ON e.venue_id = v.id
        ''').fetchall()
    return [{"id": r[0], "title": r[1], "category": r[2], "price": r[3], "desc": r[4], "vendor_email": r[5], "venue_name": r[6], "event_datetime": r[7], "is_recurring": r[8], "recur_day": r[9], "recur_time": r[10], "venue_id": r[11], "capacity": r[12]} for r in rows]
'@
Add-Edit 'src/database.py' $old $new

$old = @'
            SELECT e.id, e.title, e.category, e.price, e.description, e.vendor_email, v.name, e.event_datetime, e.is_recurring, e.recur_day, e.recur_time, e.venue_id
            FROM events e LEFT JOIN venues v ON e.venue_id = v.id WHERE e.vendor_email = ?
        ''', (vendor_email,)).fetchall()
    return [{"id": r[0], "title": r[1], "category": r[2], "price": r[3], "desc": r[4], "vendor_email": r[5], "venue_name": r[6], "event_datetime": r[7], "is_recurring": r[8], "recur_day": r[9], "recur_time": r[10], "venue_id": r[11]} for r in rows]
'@
$new = @'
            SELECT e.id, e.title, e.category, e.price, e.description, e.vendor_email, v.name, e.event_datetime, e.is_recurring, e.recur_day, e.recur_time, e.venue_id, e.capacity
            FROM events e LEFT JOIN venues v ON e.venue_id = v.id WHERE e.vendor_email = ?
        ''', (vendor_email,)).fetchall()
    return [{"id": r[0], "title": r[1], "category": r[2], "price": r[3], "desc": r[4], "vendor_email": r[5], "venue_name": r[6], "event_datetime": r[7], "is_recurring": r[8], "recur_day": r[9], "recur_time": r[10], "venue_id": r[11], "capacity": r[12]} for r in rows]
'@
Add-Edit 'src/database.py' $old $new

$old = @'
def create_booking(customer_email, event_id, booking_date, guests):
'@
$new = @'
def _capacity_info(conn, event_id, day=None):
    """How many guests an event can take on one date.

    With vehicles assigned, the seats of those vehicles are the limit (any mix of types).
    Without vehicles, the capacity the vendor typed in is the limit.
    With a day, 'booked' and 'remaining' count the confirmed guests of that date.
    """
    row = conn.execute("SELECT capacity FROM events WHERE id = ?", (event_id,)).fetchone()
    event_capacity = row[0] if row and row[0] is not None else DEFAULT_EVENT_CAPACITY
    rows = conn.execute(
        "SELECT v.vehicle_type, COUNT(*), COALESCE(vt.capacity, 4) FROM event_vehicles ev "
        "JOIN vehicles v ON v.id = ev.vehicle_id LEFT JOIN vehicle_types vt ON vt.name = v.vehicle_type "
        "WHERE ev.event_id = ? AND ev.status = 'Assigned' GROUP BY v.vehicle_type ORDER BY v.vehicle_type",
        (event_id,),
    ).fetchall()
    vehicles = [{"vehicle_type": r[0], "count": r[1], "seats_each": r[2]} for r in rows]
    if vehicles:
        total = sum(v["count"] * v["seats_each"] for v in vehicles)
        source = "vehicles"
    else:
        total = event_capacity
        source = "event"
    info = {"total": total, "source": source, "vehicles": vehicles, "booked": None, "remaining": None}
    if day is not None:
        booked = conn.execute(
            "SELECT COALESCE(SUM(guests), 0) FROM bookings WHERE event_id = ? AND booking_date = ? AND status = 'Confirmed'",
            (event_id, day.isoformat()),
        ).fetchone()[0]
        info["booked"] = booked
        info["remaining"] = max(0, total - booked)
    return info


def get_event_capacity(event_id, booking_date=None):
    """Capacity of one event: {"total", "source" ("vehicles" or "event"), "vehicles", "booked", "remaining"}.

    'booked' and 'remaining' are None unless a booking_date (date or 'YYYY-MM-DD') is given.
    """
    day = None
    if booking_date is not None:
        day = booking_date if isinstance(booking_date, date) else date.fromisoformat(str(booking_date))
    with _connect() as conn:
        return _capacity_info(conn, event_id, day)


def create_booking(customer_email, event_id, booking_date, guests):
'@
Add-Edit 'src/database.py' $old $new

$old = @'
    with _connect() as conn:
        event = conn.execute(
            "SELECT e.title, e.price, e.is_recurring, e.recur_day, e.event_datetime, e.recur_time, v.name "
'@
$new = @'
    with _connect() as conn:
        # Lock now, so two customers cannot both take the last seats.
        conn.execute("BEGIN IMMEDIATE")
        event = conn.execute(
            "SELECT e.title, e.price, e.is_recurring, e.recur_day, e.event_datetime, e.recur_time, v.name "
'@
Add-Edit 'src/database.py' $old $new

$old = @'
            return refuse("You already have a booking for this event on that date. See My Bookings.")

        code = _new_ticket_code(conn)
'@
$new = @'
            return refuse("You already have a booking for this event on that date. See My Bookings.")

        capacity = _capacity_info(conn, event_id, day)
        if guests > capacity["remaining"]:
            if capacity["remaining"] == 0:
                return refuse(f"Sorry, this event is fully booked on that date (capacity {capacity['total']}).")
            return refuse(
                f"Not enough seats. Only {capacity['remaining']} of {capacity['total']} seats are left "
                f"on that date, and you asked for {guests}."
            )

        code = _new_ticket_code(conn)
'@
Add-Edit 'src/database.py' $old $new

$old = @'
from database import create_booking, format_ticket_code, price_to_int, MAX_GUESTS_PER_BOOKING

'@
$new = @'
from database import create_booking, format_ticket_code, price_to_int, get_event_capacity, MAX_GUESTS_PER_BOOKING

'@
Add-Edit 'src/screens/event_screen.py' $old $new

$old = @'
def show_event_screen(root, email, tour):
    clear_window(root)

'@
$new = @'
def show_event_screen(root, email, tour):
    clear_window(root)
    # Read capacity fresh from the database, because vehicles can change after the list was loaded.
    capacity = get_event_capacity(tour["id"])

'@
Add-Edit 'src/screens/event_screen.py' $old $new

$old = @'
    for item in details:
        tk.Label(left_frame, text=item, font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=2)

'@
$new = @'
    for item in details:
        tk.Label(left_frame, text=item, font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=2)

    tk.Label(left_frame, text="Capacity and Vehicles", font=(t.FONT, 14, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", pady=(20, 5))
    capacity_lines = [f"- Capacity: {capacity['total']} guests per date"]
    if capacity["vehicles"]:
        for vehicle in capacity["vehicles"]:
            capacity_lines.append(f"- Vehicles: {vehicle['count']} x {vehicle['vehicle_type']} ({vehicle['seats_each']} seats each)")
        capacity_lines.append("- The seats of these vehicles set the limit for this event.")
    else:
        capacity_lines.append("- Vehicles: none for this event")
    for item in capacity_lines:
        tk.Label(left_frame, text=item, font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT_MUTED, wraplength=600, justify="left").pack(anchor="w", pady=2)

'@
Add-Edit 'src/screens/event_screen.py' $old $new

$old = @'
    selected_label.pack(anchor="w", pady=(10, 5))

    # ----- guests and total price -----
'@
$new = @'
    selected_label.pack(anchor="w", pady=(10, 5))

    seats_label = tk.Label(right_sidebar, text=f"Capacity: {capacity['total']} guests per date. Pick a date to see the seats left.",
                           font=(t.FONT, 10, "bold"), bg=t.FIELD_BG, fg=t.TEXT_MUTED, wraplength=260, justify="left")
    seats_label.pack(anchor="w", pady=(0, 5))

    # ----- guests and total price -----
'@
Add-Edit 'src/screens/event_screen.py' $old $new

$old = @'
    tk.Spinbox(guests_row, from_=1, to=MAX_GUESTS_PER_BOOKING, width=4, textvariable=guests_var, state="readonly",
               readonlybackground=t.CARD_BG, font=(t.FONT, 10)).pack(side=tk.LEFT, padx=8)

'@
$new = @'
    guests_spin = tk.Spinbox(guests_row, from_=1, to=max(1, min(MAX_GUESTS_PER_BOOKING, capacity["total"])), width=4,
                             textvariable=guests_var, state="readonly", readonlybackground=t.CARD_BG, font=(t.FONT, 10))
    guests_spin.pack(side=tk.LEFT, padx=8)

'@
Add-Edit 'src/screens/event_screen.py' $old $new

$old = @'
    guests_var.trace_add("write", update_total)
    update_total()

'@
$new = @'
    guests_var.trace_add("write", update_total)
    update_total()

    def refresh_capacity():
        """Shows the seats left on the chosen date and stops the guests box from going above them."""
        chosen = cal_state["selected"]
        info = get_event_capacity(tour["id"], chosen)
        fully_booked = False
        if chosen is None:
            limit = min(MAX_GUESTS_PER_BOOKING, info["total"])
        else:
            left = info["remaining"]
            fully_booked = left <= 0
            limit = min(MAX_GUESTS_PER_BOOKING, left)
            if fully_booked:
                seats_label.config(text=f"Fully booked on {chosen.strftime('%b %d, %Y')} (capacity {info['total']}).", fg="#e74c3c")
            else:
                seats_label.config(text=f"Seats left on {chosen.strftime('%b %d, %Y')}: {left} of {info['total']}",
                                   fg="#e67e22" if left <= 3 else "#27ae60")
        limit = max(1, limit)
        guests_spin.config(to=limit)
        if current_guests() > limit:
            guests_var.set(limit)
        if fully_booked:
            book_btn.config(state=tk.DISABLED, text="Fully booked")
        else:
            book_btn.config(state=tk.NORMAL, text="Proceed to Booking")
        return info

'@
Add-Edit 'src/screens/event_screen.py' $old $new

$old = @'
        selected_label.config(text=f"Selected: {d_obj.strftime('%b %d, %Y')}", fg="#27ae60")
        draw_calendar()

'@
$new = @'
        selected_label.config(text=f"Selected: {d_obj.strftime('%b %d, %Y')}", fg="#27ae60")
        refresh_capacity()
        draw_calendar()

'@
Add-Edit 'src/screens/event_screen.py' $old $new

$old = @'
        chosen_date = cal_state["selected"]
        guests = current_guests()
        if not messagebox.askyesno(
'@
$new = @'
        chosen_date = cal_state["selected"]
        guests = current_guests()
        # Check the seats again now, because other customers may have booked since the date was picked.
        info = refresh_capacity()
        if guests > info["remaining"]:
            if info["remaining"] <= 0:
                messagebox.showerror("Fully booked", "This event is fully booked on that date. Please choose another date.")
            else:
                messagebox.showerror("Not enough seats", f"Only {info['remaining']} seat(s) are left on that date. Please lower the number of guests or choose another date.")
            return
        if not messagebox.askyesno(
'@
Add-Edit 'src/screens/event_screen.py' $old $new

$old = @'
        if not result["success"]:
            messagebox.showerror("Booking failed", result["message"])
            return

'@
$new = @'
        if not result["success"]:
            messagebox.showerror("Booking failed", result["message"])
            refresh_capacity()
            return

'@
Add-Edit 'src/screens/event_screen.py' $old $new

$old = @'
    create_support_ticket, get_support_tickets_by_customer
)
'@
$new = @'
    create_support_ticket, get_support_tickets_by_customer, get_event_capacity
)
'@
Add-Edit 'src/welcome/customer_welcome.py' $old $new

$old = @'
            tk.Label(card, text=schedule_info, font=(t.FONT, 8, "italic"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=1)

'@
$new = @'
            tk.Label(card, text=schedule_info, font=(t.FONT, 8, "italic"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=1)
            tk.Label(card, text=f"👥 Capacity: {get_event_capacity(tour['id'])['total']} guests per date", font=(t.FONT, 8, "italic"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=1)

'@
Add-Edit 'src/welcome/customer_welcome.py' $old $new

$old = @'
    get_venues_by_vendor, create_venue, delete_venue, count_active_bookings,
    get_bookings_by_vendor
)
'@
$new = @'
    get_venues_by_vendor, create_venue, delete_venue, count_active_bookings,
    get_bookings_by_vendor, get_event_capacity, DEFAULT_EVENT_CAPACITY, MAX_EVENT_CAPACITY
)
'@
Add-Edit 'src/welcome/vendor_welcome.py' $old $new

$old = @'
            tk.Label(card, text=event['desc'], font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT_MUTED, wraplength=600, justify="left").pack(anchor="w", padx=15, pady=5)

'@
$new = @'
            cap = get_event_capacity(event['id'])
            if cap['vehicles']:
                vehicle_count = sum(v['count'] for v in cap['vehicles'])
                capacity_text = f"👥 Capacity: {cap['total']} guests (seats of {vehicle_count} assigned vehicle(s))"
            else:
                capacity_text = f"👥 Capacity: {cap['total']} guests (no vehicles assigned)"
            tk.Label(card, text=capacity_text, font=(t.FONT, 9), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=15, pady=2)
            tk.Label(card, text=event['desc'], font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT_MUTED, wraplength=600, justify="left").pack(anchor="w", padx=15, pady=5)

'@
Add-Edit 'src/welcome/vendor_welcome.py' $old $new

$old = @'
        # Price
        tk.Label(form_frame, text="PRICE", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(8, 2))
        price_row = tk.Frame(form_frame, bg=t.CARD_BG)
        price_row.pack(fill=tk.X)
        price_entry = tk.Entry(price_row, font=(t.FONT, 11), bg=t.FIELD_BG, relief="solid", bd=1)
        price_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        if event:
            raw_price = str(event["price"]).replace(" AED", "").strip()
            price_entry.insert(0, raw_price)
        tk.Label(price_row, text="AED", font=(t.FONT, 11, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(side=tk.LEFT, padx=(8, 0))

'@
$new = @'
        # Price and capacity share one row, so the form keeps its height
        price_cap_row = tk.Frame(form_frame, bg=t.CARD_BG)
        price_cap_row.pack(fill=tk.X, pady=(8, 0))

        price_col = tk.Frame(price_cap_row, bg=t.CARD_BG)
        price_col.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        tk.Label(price_col, text="PRICE (AED)", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(0, 2))
        price_entry = tk.Entry(price_col, font=(t.FONT, 11), bg=t.FIELD_BG, relief="solid", bd=1)
        price_entry.pack(fill=tk.X, ipady=4)
        if event:
            raw_price = str(event["price"]).replace(" AED", "").strip()
            price_entry.insert(0, raw_price)

        capacity_col = tk.Frame(price_cap_row, bg=t.CARD_BG)
        capacity_col.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(capacity_col, text="CAPACITY (GUESTS)", font=(t.FONT, 9, "bold"), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", pady=(0, 2))
        capacity_entry = tk.Entry(capacity_col, font=(t.FONT, 11), bg=t.FIELD_BG, relief="solid", bd=1)
        capacity_entry.pack(fill=tk.X, ipady=4)
        capacity_entry.insert(0, str(event.get("capacity") or DEFAULT_EVENT_CAPACITY) if event else str(DEFAULT_EVENT_CAPACITY))

'@
Add-Edit 'src/welcome/vendor_welcome.py' $old $new

$old = @'
            price_val = price_entry.get().strip()
            desc = desc_text.get("1.0", tk.END).strip()

'@
$new = @'
            price_val = price_entry.get().strip()
            capacity_val = capacity_entry.get().strip()
            desc = desc_text.get("1.0", tk.END).strip()

'@
Add-Edit 'src/welcome/vendor_welcome.py' $old $new

$old = @'
                messagebox.showerror("Error", "Price must contain numbers only.", parent=modal)
                return

'@
$new = @'
                messagebox.showerror("Error", "Price must contain numbers only.", parent=modal)
                return
            if not (capacity_val.isascii() and capacity_val.isdigit()) or not 1 <= int(capacity_val) <= MAX_EVENT_CAPACITY:
                messagebox.showerror("Error", f"Capacity must be a whole number from 1 to {MAX_EVENT_CAPACITY}.", parent=modal)
                return

'@
Add-Edit 'src/welcome/vendor_welcome.py' $old $new

$old = @'
update_event(event["id"], title, category, formatted_price, desc, venue_id, event_datetime, is_recurring, recur_day, recur_time)
'@
$new = @'
update_event(event["id"], title, category, formatted_price, desc, venue_id, event_datetime, is_recurring, recur_day, recur_time, capacity=int(capacity_val))
'@
Add-Edit 'src/welcome/vendor_welcome.py' $old $new

$old = @'
create_event(title, category, formatted_price, desc, self.email, venue_id, event_datetime, is_recurring, recur_day, recur_time)
'@
$new = @'
create_event(title, category, formatted_price, desc, self.email, venue_id, event_datetime, is_recurring, recur_day, recur_time, capacity=int(capacity_val))
'@
Add-Edit 'src/welcome/vendor_welcome.py' $old $new

$old = @'
from database import get_all_vehicles, get_all_events, dispatch_vehicle_combination, free_vehicle, _connect, get_event_demand

'@
$new = @'
from database import get_all_vehicles, get_all_events, dispatch_vehicle_combination, free_vehicle, _connect, get_event_demand, get_event_capacity

'@
Add-Edit 'src/welcome/dispatch_view.py' $old $new

$old = @'
        tk.Label(sel_card, text=f"Upcoming bookings: {bookings_count}   |   Guests booked: {guests_count}", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=10, pady=(0, 5))

'@
$new = @'
        tk.Label(sel_card, text=f"Upcoming bookings: {bookings_count}   |   Guests booked: {guests_count}", font=(t.FONT, 10, "bold"), bg=t.CARD_BG, fg=t.TEXT).pack(anchor="w", padx=10, pady=(0, 5))
        event_capacity = get_event_capacity(current_event_id)
        if event_capacity["source"] == "vehicles":
            capacity_text = f"Capacity: {event_capacity['total']} guests per date (total seats of the assigned vehicles)"
        else:
            capacity_text = f"Capacity: {event_capacity['total']} guests per date (set by the vendor, no vehicles assigned)"
        tk.Label(sel_card, text=capacity_text, font=(t.FONT, 10), bg=t.CARD_BG, fg=t.TEXT_MUTED).pack(anchor="w", padx=10, pady=(0, 5))

'@
Add-Edit 'src/welcome/dispatch_view.py' $old $new

$old = @'


if __name__ == "__main__":
    unittest.main()

'@
$new = @'


class CapacityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d.DB_PATH = os.path.join(self.tmp.name, "test.db")
        d.init_db()
        self.day = datetime.date.today() + datetime.timedelta(days=3)
        d.create_event("Small dinner", "General", "100 AED", "a long enough description", "vendor@email.com", 1,
                       self.day.isoformat() + " 19:00", "One-Time", "N/A", "19:00", capacity=5)
        self.dinner = [e for e in d.get_all_events() if e["title"] == "Small dinner"][0]

    def tearDown(self):
        self.tmp.cleanup()

    def book(self, email, guests, event=None, day=None):
        return d.create_booking(email, (event or self.dinner)["id"], (day or self.day).isoformat(), guests)

    def assign(self, event_id, vehicle_type, how_many):
        fleet = [v for v in d.get_all_vehicles("dispatcher@email.com") if v["vehicle_type"] == vehicle_type and v["status"] == "Available"]
        chosen = fleet[:how_many]
        self.assertEqual(len(chosen), how_many)
        d.dispatch_vehicle_combination(event_id, [{"vehicle_id": v["id"], "auto_reassign_recurring": 0} for v in chosen])

    def test_event_without_vehicles_uses_its_own_capacity(self):
        info = d.get_event_capacity(self.dinner["id"], self.day)
        self.assertEqual((info["total"], info["source"], info["vehicles"]), (5, "event", []))
        self.assertEqual((info["booked"], info["remaining"]), (0, 5))

    def test_cannot_book_more_than_capacity(self):
        self.assertTrue(self.book("a@email.com", 3)["success"])
        too_many = self.book("b@email.com", 3)
        self.assertFalse(too_many["success"])
        self.assertIn("Only 2 of 5 seats", too_many["message"])
        self.assertTrue(self.book("b@email.com", 2)["success"])
        full = self.book("c@email.com", 1)
        self.assertFalse(full["success"])
        self.assertIn("fully booked", full["message"])
        self.assertEqual(d.get_event_capacity(self.dinner["id"], self.day)["remaining"], 0)

    def test_one_booking_cannot_be_larger_than_the_whole_event(self):
        self.assertFalse(self.book("a@email.com", 6)["success"])
        self.assertTrue(self.book("a@email.com", 5)["success"])

    def test_cancelling_frees_the_seats(self):
        booking = self.book("a@email.com", 5)["booking"]
        self.assertFalse(self.book("b@email.com", 1)["success"])
        d.cancel_booking(booking["id"], "a@email.com")
        self.assertEqual(d.get_event_capacity(self.dinner["id"], self.day)["remaining"], 5)
        self.assertTrue(self.book("b@email.com", 1)["success"])

    def test_capacity_counts_each_date_on_its_own(self):
        d.create_event("Daily tour", "General", "50 AED", "a long enough description", "vendor@email.com", 1,
                       self.day.isoformat() + " 09:00", "Recurring",
                       "Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday", "09:00", capacity=2)
        tour = [e for e in d.get_all_events() if e["title"] == "Daily tour"][0]
        next_day = self.day + datetime.timedelta(days=1)
        self.assertTrue(self.book("a@email.com", 2, tour)["success"])
        self.assertFalse(self.book("b@email.com", 1, tour)["success"])
        self.assertTrue(self.book("b@email.com", 1, tour, next_day)["success"])

    def test_vehicle_combination_sets_the_capacity(self):
        self.assign(self.dinner["id"], "desert buggy", 1)
        self.assign(self.dinner["id"], "4x4 toyota landcrusier", 1)
        info = d.get_event_capacity(self.dinner["id"])
        self.assertEqual((info["total"], info["source"]), (8, "vehicles"))
        self.assertEqual(sorted((v["vehicle_type"], v["count"], v["seats_each"]) for v in info["vehicles"]),
                         [("4x4 toyota landcrusier", 1, 6), ("desert buggy", 1, 2)])
        self.assertTrue(self.book("a@email.com", 6)["success"])
        self.assertFalse(self.book("b@email.com", 3)["success"])
        self.assertTrue(self.book("b@email.com", 2)["success"])

    def test_two_vehicles_of_the_same_type_add_up(self):
        self.assign(self.dinner["id"], "desert buggy", 2)
        self.assertEqual(d.get_event_capacity(self.dinner["id"])["total"], 4)

    def test_freeing_a_vehicle_goes_back_to_vendor_capacity(self):
        self.assign(self.dinner["id"], "RTA bus", 1)
        self.assertEqual(d.get_event_capacity(self.dinner["id"])["total"], 50)
        bus = [v for v in d.get_all_vehicles("dispatcher@email.com") if v["vehicle_type"] == "RTA bus"][0]
        d.free_vehicle(bus["id"])
        info = d.get_event_capacity(self.dinner["id"])
        self.assertEqual((info["total"], info["source"]), (5, "event"))

    def test_edit_event_capacity(self):
        e = self.dinner
        d.update_event(e["id"], e["title"], e["category"], e["price"], e["desc"], e["venue_id"], e["event_datetime"],
                       e["is_recurring"], e["recur_day"], e["recur_time"], capacity=8)
        self.assertEqual(d.get_event_capacity(e["id"])["total"], 8)
        # No capacity given: the event keeps the one it has.
        d.update_event(e["id"], e["title"], e["category"], e["price"], e["desc"], e["venue_id"], e["event_datetime"],
                       e["is_recurring"], e["recur_day"], e["recur_time"])
        self.assertEqual(d.get_event_capacity(e["id"])["total"], 8)

    def test_bad_capacity_is_rejected(self):
        for bad in (0, -3, d.MAX_EVENT_CAPACITY + 1):
            with self.assertRaises(ValueError):
                d.create_event("Bad", "General", "10 AED", "a long enough description", "vendor@email.com", 1,
                               "2030-01-01 10:00", "One-Time", "N/A", "10:00", capacity=bad)

    def test_demo_events_have_capacity(self):
        titles = {e["title"]: e["capacity"] for e in d.get_all_events()}
        self.assertEqual(titles["New year dinner"], 40)
        self.assertEqual(titles["Red Dune Sunset Safari and Royal BBQ Dinner"], 30)

    def test_old_database_gets_the_capacity_column(self):
        import sqlite3
        old_path = os.path.join(self.tmp.name, "old.db")
        conn = sqlite3.connect(old_path)
        conn.execute("CREATE TABLE events (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, category TEXT, price TEXT, "
                     "description TEXT, vendor_email TEXT, venue_id INTEGER, event_datetime TEXT, is_recurring TEXT, recur_day TEXT, recur_time TEXT)")
        conn.execute("INSERT INTO events (title, price, event_datetime, is_recurring) VALUES ('Old event', '10 AED', '2030-01-01 10:00', 'One-Time')")
        conn.commit()
        conn.close()
        d.DB_PATH = old_path
        d.init_db()
        d.init_db()
        old_event = [e for e in d.get_all_events() if e["title"] == "Old event"][0]
        self.assertEqual(old_event["capacity"], d.DEFAULT_EVENT_CAPACITY)


if __name__ == "__main__":
    unittest.main()

'@
Add-Edit 'tests/test_booking.py' $old $new

$old = @'
- **Customer**: browse events, pick a date and number of guests, book and get a 16-digit ticket code.

'@
$new = @'
- **Customer**: browse events, see the capacity and vehicles of each event, pick a date and number of guests, book and get a 16-digit ticket code.
  The booking screen shows the seats left on the chosen date. A booking that is bigger than the seats left is refused.

'@
Add-Edit 'readME.md' $old $new

$old = @'
- **Vendor**: create events, venues and categories.
'@
$new = @'
- **Vendor**: create events (with a capacity), venues and categories.
'@
Add-Edit 'readME.md' $old $new

$old = @'
- **Dispatcher**: register and assign vehicles. The dispatch screen shows the guests booked for the chosen event.

'@
$new = @'
- **Dispatcher**: register and assign vehicles. The dispatch screen shows the guests booked and the capacity of the chosen event.

'@
Add-Edit 'readME.md' $old $new

$old = @'
- **Every role**: *Dashboard*
'@
$new = @'
- **Event capacity**: an event with vehicles can take as many guests as the seats of its vehicles (any mix of types).
  An event with no vehicles uses the capacity the vendor typed in. Seats are counted per date, and cancelled bookings free their seats.
- **Every role**: *Dashboard*
'@
Add-Edit 'readME.md' $old $new


# ---------------------------------------------------------------- read files, apply every edit in memory
function Read-ProjectFile($path) {
    $bytes = [System.IO.File]::ReadAllBytes($path)
    $hasBom = ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
    $text = $utf8NoBom.GetString($bytes)
    if ($hasBom) { $text = $text.Substring(1) }
    $crlf = $text.Contains("`r`n")
    return [pscustomobject]@{ Text = $text.Replace("`r`n", "`n"); Crlf = $crlf; Bom = $hasBom }
}

$files = [ordered]@{}
$number = 0
foreach ($e in $edits) {
    $number++
    $full = Join-Path $repo $e.Path
    if (-not (Test-Path -LiteralPath $full)) { throw "Edit $number : file not found: $($e.Path)" }
    if (-not $files.Contains($e.Path)) { $files[$e.Path] = Read-ProjectFile $full }

    $old = $e.Old.Replace("`r`n", "`n")
    $new = $e.New.Replace("`r`n", "`n")
    $text = $files[$e.Path].Text

    $first = $text.IndexOf($old, [System.StringComparison]::Ordinal)
    if ($first -lt 0) {
        throw "Edit $number : the expected code was not found in $($e.Path). The file was changed after this script was made, so nothing was written."
    }
    if ($text.IndexOf($old, $first + 1, [System.StringComparison]::Ordinal) -ge 0) {
        throw "Edit $number : the expected code appears more than once in $($e.Path). Nothing was written."
    }
    $files[$e.Path].Text = $text.Substring(0, $first) + $new + $text.Substring($first + $old.Length)
}

# ---------------------------------------------------------------- back up, then write
$backupRoot = Join-Path $repo ('.fix-backup\event-capacity-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
foreach ($relative in $files.Keys) {
    $source = Join-Path $repo $relative
    $target = Join-Path $backupRoot $relative
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
    Copy-Item -LiteralPath $source -Destination $target
}
foreach ($relative in $files.Keys) {
    $item = $files[$relative]
    $out = $item.Text
    if ($item.Crlf) { $out = $out.Replace("`n", "`r`n") }
    $encoding = New-Object System.Text.UTF8Encoding($item.Bom)
    [System.IO.File]::WriteAllText((Join-Path $repo $relative), $out, $encoding)
    Write-Host "  updated $relative" -ForegroundColor Green
}
Write-Host ("Done: {0} edits in {1} files. Backups: {2}" -f $edits.Count, $files.Count, $backupRoot) -ForegroundColor Green

# ---------------------------------------------------------------- run the tests (they use a temporary database)
$python = $null
foreach ($name in 'python', 'py') {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) { continue }
    # The Microsoft Store "python" shortcut exists even when Python is not installed, so really try it.
    try {
        & $name -c "import sys" *> $null
        if ($LASTEXITCODE -eq 0) { $python = $name; break }
    }
    catch { }
}
if ($python) {
    Write-Host 'Running the tests ...' -ForegroundColor Cyan
    $ErrorActionPreference = 'Continue'   # unittest writes its progress to stderr
    Push-Location $repo
    try {
        & $python -m unittest discover -s tests
        if ($LASTEXITCODE -ne 0) { Write-Host 'Some tests failed. Your files are in .fix-backup if you want to go back.' -ForegroundColor Red }
    }
    finally { Pop-Location }
}
else {
    Write-Host 'Python was not found in PATH, so the tests were skipped.' -ForegroundColor Yellow
}

Write-Host ''
Write-Host 'Next: python src\main.py' -ForegroundColor Cyan
Write-Host 'Vendor: Add or edit an event and set CAPACITY. Dispatcher: assigned vehicles replace it with their total seats.'
Write-Host 'Old events keep working and start with a capacity of 20.'
