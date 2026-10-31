"""Writes the EER diagram of server/users.db (Chen notation) as Graphviz files in report/uml/.

06b_eer_overview.dot  all entities, relationships, cardinalities and the role specialization (keys only)
06c_eer_accounts.dot  users, roles, venues for staff, support tickets, reports and bans, with all attributes
06d_eer_bookings.dot  venues, events, bookings, tickets, reviews and the partner cart, with all attributes
06e_eer_fleet.dot     vehicles, vehicle types and their link to events, with all attributes
"""
import os

U = r"C:\Dev\repos\Public repos\rihla_manual\report\uml"

ENT = {
    "USER": ["email:key", "password", "role", "phone", "currency", "created_at", "banned", "banned_at",
             "account_age:derived"],
    "CUSTOMER": [],
    "SSN_HOLDER": ["ssn_hash", "ssn_last4"],
    "VENDOR": [], "STAFF": ["manager_email"], "PARTNER": [], "DISPATCHER": [], "ADMIN": [],
    "VENUE": ["id:key", "name", "address", "maps_url"],
    "EVENT": ["id:key", "title", "category", "price", "description", "event_datetime", "is_recurring",
              "recur_day:multi", "recur_time", "capacity", "seats_left:derived", "average_rating:derived"],
    "VENDOR_CATEGORY": ["id:key", "name"],
    "BOOKING": ["id:key", "booking_date", "event_time", "guests", "total_price", "status", "client_name",
                "created_at", "cancelled_at", "cancelled_by_role", "cancel_reason", "refund_percent",
                "refund_amount", "shown_status:derived"],
    "TICKET": ["id:key", "ticket_code", "status"],
    "REVIEW": ["id:key", "rating", "comment", "created_at", "updated_at"],
    "SUPPORT_TICKET": ["id:key", "subject", "message", "status", "created_at", "resolved_at"],
    "REPORT": ["id:key", "reporter_role", "category", "offender_type", "subject", "description", "status",
               "created_at", "resolved_at", "resolution"],
    "VEHICLE_TYPE": ["id:key", "name", "capacity"],
    "VEHICLE": ["id:key", "license_number", "location", "status", "auto_reassign_recurring"],
    "CART_ITEM": ["id:key", "booking_date", "guests", "client_name", "created_at"],
}

REL = [
    ("OWNS", [("VENDOR", "1", False), ("VENUE", "N", True)], []),
    ("CREATES", [("VENDOR", "1", False), ("EVENT", "N", True)], []),
    ("DEFINES", [("VENDOR", "1", False), ("VENDOR_CATEGORY", "N", True)], []),
    ("WORKS_AT", [("STAFF", "N", True), ("VENUE", "1", False)], []),
    ("HOSTS", [("VENUE", "1", False), ("EVENT", "N", True)], []),
    ("MAKES", [("USER", "1", False), ("BOOKING", "N", True)], []),
    ("BOOKED_FOR", [("EVENT", "1", False), ("BOOKING", "N", False)], []),
    ("CANCELS", [("USER", "1", False), ("BOOKING", "N", False)], []),
    ("HAS", [("BOOKING", "1", True), ("TICKET", "1", False)], []),
    ("RATES", [("BOOKING", "1", False), ("REVIEW", "1", True)], []),
    ("OPENS", [("USER", "1", False), ("SUPPORT_TICKET", "N", True)], []),
    ("ASKS_ABOUT", [("SUPPORT_TICKET", "N", False), ("EVENT", "1", False)], []),
    ("RESOLVES", [("STAFF", "1", False), ("SUPPORT_TICKET", "N", False)], []),
    ("FILES", [("USER", "1", False), ("REPORT", "N", True)], []),
    ("CONCERNS", [("REPORT", "N", False), ("USER", "1", False)], []),
    ("HANDLES", [("ADMIN", "1", False), ("REPORT", "N", False)], []),
    ("BANS", [("ADMIN", "1", False), ("USER", "N", False)], []),
    ("REGISTERS", [("DISPATCHER", "1", False), ("VEHICLE", "N", True)], []),
    ("OF_TYPE", [("VEHICLE_TYPE", "1", False), ("VEHICLE", "N", True)], []),
    ("ASSIGNED_TO", [("EVENT", "M", False), ("VEHICLE", "N", False)], ["status"]),
    ("PLANS", [("PARTNER", "1", False), ("CART_ITEM", "N", True)], []),
    ("LISTS", [("EVENT", "1", False), ("CART_ITEM", "N", True)], []),
]

SPEC = [("USER", "spec_role", ["CUSTOMER", "SSN_HOLDER"]),
        ("SSN_HOLDER", "spec_ssn", ["VENDOR", "STAFF", "PARTNER", "DISPATCHER", "ADMIN"])]

TOTAL = 'color="black:white:black"'
HEADER = [
    "// EER diagram of server/users.db in Chen notation.",
    "// Rectangles: entities. Diamonds: relationships. Ovals: attributes.",
    "// Underlined: key. Double oval: multi-valued. Dashed oval: derived (worked out, not stored).",
    "// Double line: total participation. Circle with d: disjoint, total specialization (one role per user).",
    "// Grey entities are shown in full in another part of the diagram.",
]


def build(title, full, refs, rels, specs, rankdir="LR", attrs=True):
    shown = set(full) | set(refs)
    out = HEADER + [f"// Part: {title}", "graph EER {",
                    (f'  layout=dot; rankdir={rankdir}; nodesep=0.15; ranksep=0.45; splines=true; '
                     if attrs is not None else '  layout=neato; overlap=prism; sep="+12"; splines=true; ')
                    + 'outputorder=edgesfirst; newrank=true;',
                    '  node [fontname="Helvetica", fontsize=16];',
                    '  edge [fontname="Helvetica", fontsize=15, color="#2C3E50"];']
    for e in full:
        out.append(f'  {e} [shape=box, style="filled,bold", fillcolor="#D6E4F0", fontsize=18];')
        for a in (ENT[e] if attrs else []):
            name, _, kind = a.partition(":")
            nid = f"{e}__{name}"
            style = {"key": f'label=<<U>{name}</U>>', "multi": f'label="{name}", peripheries=2',
                     "derived": f'label="{name}", style="dashed"'}.get(kind, f'label="{name}"')
            out.append(f"  {nid} [shape=ellipse, {style}];")
            out.append(f"  {e} -- {nid};")
    for e in refs:
        out.append(f'  {e} [shape=box, style="filled", fillcolor="#ECEFF1", color="#7F8C8D", fontsize=18];')
    for name, ends, rattrs in REL:
        if name not in rels:
            continue
        out.append(f'  R_{name} [shape=diamond, style=filled, fillcolor="#F9E4B7", label="{name}", fontsize=14];')
        for ent, card, total in ends:
            extra = (", " + TOTAL) if total else ""
            out.append(f'  R_{name} -- {ent} [label="{card}"{extra}];')
        for a in rattrs:
            nid = f"R_{name}__{a}"
            out.append(f'  {nid} [shape=ellipse, label="{a}"];')
            out.append(f"  R_{name} -- {nid};")
    for sup, cid, subs in SPEC:
        if sup not in specs:
            continue
        out.append(f'  {cid} [shape=circle, label="d", width=0.35, fixedsize=true];')
        out.append(f"  {sup} -- {cid} [{TOTAL}];")
        for s in subs:
            if s in shown:
                out.append(f'  {cid} -- {s} [label="\u2283", fontsize=18];')
    out.append("}")
    text = "\n".join(out) + "\n"
    if attrs is None:
        # The overview has no attributes, so bigger text keeps it readable on a page.
        for small, big in (("fontsize=18", "fontsize=30"), ("fontsize=16", "fontsize=26"),
                           ("fontsize=15", "fontsize=26"), ("fontsize=14", "fontsize=24"),
                           ("width=0.35", "width=0.6")):
            text = text.replace(small, big)
        text = text.replace('sep="+12"', 'sep="+6"')
    return text


ROLES = ["USER", "CUSTOMER", "SSN_HOLDER", "VENDOR", "STAFF", "PARTNER", "DISPATCHER", "ADMIN"]
PARTS = {
    "06b_eer_overview": ("Overview (no attributes)", list(ENT), [], [r[0] for r in REL], ["USER", "SSN_HOLDER"], "TB", None),
    "06c_eer_users": ("Users and roles", ROLES, ["VENUE"], ["WORKS_AT", "BANS"], ["USER", "SSN_HOLDER"], "LR", True),
    "06d_eer_support": ("Support tickets and reports", ["SUPPORT_TICKET", "REPORT"], ["USER", "STAFF", "ADMIN", "EVENT"],
                        ["OPENS", "ASKS_ABOUT", "RESOLVES", "FILES", "CONCERNS", "HANDLES"], [], "LR", True),
    "06e_eer_events": ("Venues and events", ["VENUE", "EVENT", "VENDOR_CATEGORY"], ["VENDOR"],
                       ["OWNS", "CREATES", "DEFINES", "HOSTS"], [], "LR", True),
    "06f_eer_bookings": ("Bookings, tickets, reviews and the partner cart", ["BOOKING", "TICKET", "REVIEW", "CART_ITEM"],
                         ["USER", "EVENT", "PARTNER"], ["MAKES", "BOOKED_FOR", "CANCELS", "HAS", "RATES", "PLANS", "LISTS"],
                         [], "LR", True),
    "06g_eer_fleet": ("Fleet", ["VEHICLE", "VEHICLE_TYPE"], ["DISPATCHER", "EVENT"],
                      ["REGISTERS", "OF_TYPE", "ASSIGNED_TO"], [], "LR", True),
}
for fname, (title, full, refs, rels, specs, rd, attrs) in PARTS.items():
    with open(os.path.join(U, fname + ".dot"), "w", encoding="utf-8", newline="\n") as f:
        f.write(build(title, full, refs, rels, specs, rd, attrs))
    print("wrote", fname)
