// demo mode for the online preview: there is no server, so the answers come from
// demo_data.json (a copy of the real server's answers for the demo accounts).
// Sign in, booking, the ticket check and the shopping list behave like the real rules,
// other changes only say they were saved (nothing is stored, a reload starts fresh).
import DATA from "./demo_data.json";

const ACCOUNTS = {
  "customer@email.com": ["customer1234", "Customer"],
  "vendor@email.com": ["vendor1234", "Vendor"],
  "staff@email.com": ["staff1234", "Staff"],
  "partner@email.com": ["partner1234", "Partner"],
  "dispatcher@email.com": ["dispatcher1234", "Dispatcher"],
  "admin@email.com": ["admin1234", "Admin"],
};
const DEMO_TICKET = "1234567890123456";

// small things the demo remembers until the page is reloaded
const usedTickets = {};
const cart = DATA["/cart/partner%40email.com"] ? DATA["/cart/partner%40email.com"].items.slice() : [];
let nextId = 9000;

function ok(extra) {
  return Object.assign({ success: true }, extra || {});
}
function fail(message) {
  return { success: false, message: message };
}

function findEvent(id) {
  const events = DATA["/events"].events;
  for (let i = 0; i < events.length; i++) {
    if (events[i].id === Number(id)) return events[i];
  }
  return null;
}

// '240 AED' -> 240
function priceOf(text) {
  let digits = "";
  const s = String(text || "");
  for (let i = 0; i < s.length; i++) if (s[i] >= "0" && s[i] <= "9") digits = digits + s[i];
  return digits ? parseInt(digits, 10) : 0;
}

// a made up 16-digit ticket code, different every time
function newCode() {
  nextId = nextId + 1;
  let code = String(4000000000000000 + nextId * 7919);
  return code.slice(0, 16);
}

function handleGet(path) {
  if (DATA[path]) return DATA[path];
  // capacity for a chosen date: the event's capacity minus a few seats
  const cap = path.match(/^\/events\/(\d+)\/capacity/);
  if (cap) {
    // the copy has no date, so make a believable seat count from the event's own capacity
    const base = DATA["/events/" + cap[1] + "/capacity"];
    const ev = findEvent(cap[1]);
    let total = ev ? ev.capacity : 20;
    if (base && base.capacity && base.capacity.total) total = base.capacity.total;
    const booked = (Number(cap[1]) * 7) % Math.max(1, Math.floor(total / 2));
    return ok({ capacity: { total: total, remaining: total - booked, booked: booked, source: "event", vehicles: [] } });
  }
  if (path.indexOf("/cart/partner") === 0) return ok({ items: cart, count: cart.length });
  if (path.indexOf("/users/email_exists/") === 0) {
    const email = decodeURIComponent(path.split("/").pop());
    return ok({ exists: ACCOUNTS[email.toLowerCase()] !== undefined });
  }
  if (path.indexOf("/users/phone_exists/") === 0) return ok({ exists: false });
  if (path.indexOf("/users/currency/") === 0) return ok({ currency: "AED" });
  if (path.indexOf("/bookings/customer/") === 0 || path.indexOf("/experiences/") === 0 || path.indexOf("/support/customer/") === 0) {
    return ok({ bookings: [], experiences: [], tickets: [] });
  }
  return ok({ events: [], bookings: [], users: [], reports: [], items: [], vehicles: [], venues: [], categories: [], tickets: [] });
}

function handlePost(path, body) {
  if (path === "/auth/login") {
    const email = (body.email || "").toLowerCase();
    const acc = ACCOUNTS[email];
    if (acc && acc[0] === body.password) return ok({ email: email, role: acc[1] });
    return fail("Invalid email or password. In the demo, use the demo account buttons.");
  }
  if (path === "/bookings") {
    const ev = findEvent(body.event_id);
    if (!ev) return fail("Event not found.");
    const guests = Number(body.guests || 1);
    if (guests < 1 || guests > 10) return fail("You can book 1 to 10 guests at a time.");
    const base = priceOf(ev.price) * guests;
    const vat = Math.round(base * 0.05 * 100) / 100;
    return ok({
      message: "Booking confirmed.",
      booking: {
        id: ++nextId, event_title: ev.title, venue_name: ev.venue_name, booking_date: body.booking_date,
        event_time: ev.recur_time, guests: guests, total_price: base + vat, base_price: base, vat: vat, ticket_code: newCode(),
      },
    });
  }
  if (path === "/tickets/verify") {
    const code = String(body.ticket_code || "");
    if (code !== DEMO_TICKET) return fail("Invalid ticket code. Not found in system.");
    if (usedTickets[code]) return fail("Ticket already used! Checked in previously.");
    usedTickets[code] = true;
    return ok({ message: "Access granted! Ticket valid for New year dinner (customer@email.com). Admit 2 guest(s)." });
  }
  if (path === "/cart") {
    const ev = findEvent(body.event_id);
    if (!ev) return fail("Event not found.");
    cart.push({
      id: ++nextId, event_id: ev.id, title: ev.title, venue_name: ev.venue_name, booking_date: body.booking_date,
      guests: body.guests, client_name: body.client_name, price: ev.price, unit_price: priceOf(ev.price),
      total_price: priceOf(ev.price) * Number(body.guests),
    });
    return ok({ message: "Added." });
  }
  if (path.indexOf("/cart/") === 0 && path.endsWith("/checkout")) {
    const bookings = [];
    for (let i = 0; i < cart.length; i++) {
      const c = cart[i];
      bookings.push({
        id: ++nextId, event_title: c.title, venue_name: c.venue_name, booking_date: c.booking_date, event_time: "",
        guests: c.guests, client_name: c.client_name, base_price: c.total_price, ticket_code: newCode(),
      });
    }
    cart.length = 0;
    return ok({ message: "Successfully confirmed " + bookings.length + " event booking(s)!", bookings: bookings });
  }
  if (path.indexOf("/cart/") === 0 && path.endsWith("/remove")) {
    const id = Number(path.split("/")[2]);
    for (let i = 0; i < cart.length; i++) if (cart[i].id === id) cart.splice(i, 1);
    return ok({ message: "Removed." });
  }
  return ok({ message: "Saved (demo mode: nothing is stored)." , assigned: 1, refund: { percent: 100 } });
}

export function demoRequest(method, path, body) {
  let answer;
  if (method === "GET") {
    answer = handleGet(path);
  } else if (method === "POST") {
    answer = handlePost(path, body || {});
  } else {
    answer = ok({ message: "Saved (demo mode: nothing is stored)." });
  }
  // a short wait, so loading states and animations look like the real app
  return new Promise(function (done) {
    setTimeout(function () {
      done(JSON.parse(JSON.stringify(answer)));
    }, 120);
  });
}
