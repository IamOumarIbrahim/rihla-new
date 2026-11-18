// talks to the Rihla server over http
// the names are the same as in the old Python client (src/api_client.py)
// every function gives back the JSON from the server, it always has "success"
// and "message" when something went wrong
import { demoRequest } from "./demo.js";

const BASE_URL = "http://127.0.0.1:5000/api";

// demo mode: no server, the answers come from demo.js (used for the online preview)
// on when built with "npm run build:demo", or when the address has ?demo=1
let demoMode = import.meta.env.MODE === "demo";
if (typeof window !== "undefined" && window.location.search.indexOf("demo=1") !== -1) {
  demoMode = true;
}

export function isDemoMode() {
  return demoMode;
}

async function request(method, path, body) {
  if (demoMode) {
    return demoRequest(method, path, body);
  }
  const options = { method: method, headers: {} };
  if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  try {
    const response = await fetch(BASE_URL + path, options);
    return await response.json();
  } catch (error) {
    return { success: false, message: "Cannot connect to the Rihla server. Is it running? (python server/server.py)" };
  }
}

function get(path) {
  return request("GET", path);
}
function post(path, body) {
  return request("POST", path, body || {});
}
function put(path, body) {
  return request("PUT", path, body || {});
}
function del(path) {
  return request("DELETE", path);
}

// the email goes in the address, so characters like + have to be escaped
function e(text) {
  return encodeURIComponent(text || "");
}

// ---- accounts ----
export function login(email, password) {
  return post("/auth/login", { email: email, password: password });
}
export function registerUser(data) {
  return post("/users/register", data);
}
export function updatePassword(email, newPassword) {
  return put("/users/password", { email: email, new_password: newPassword });
}
export function emailExists(email) {
  return get("/users/email_exists/" + e(email));
}
export function phoneExists(phone) {
  return get("/users/phone_exists/" + e(phone));
}
export function getCurrency(email) {
  return get("/users/currency/" + e(email));
}
export function setCurrency(email, currency) {
  return put("/users/currency", { email: email, currency: currency });
}
export function getStaffVenue(email) {
  return get("/staff/venue/" + e(email));
}
export function setStaffVenue(email, venueId, managerEmail) {
  return put("/staff/venue", { email: email, venue_id: venueId, manager_email: managerEmail });
}

// ---- admin ----
export function getAllUsers(adminEmail) {
  return get("/admin/users?admin_email=" + e(adminEmail));
}
export function setUserBanned(adminEmail, email, banned) {
  return post("/admin/users/ban", { admin_email: adminEmail, email: email, banned: banned });
}
export function getReports(adminEmail) {
  return get("/admin/reports?admin_email=" + e(adminEmail));
}
export function resolveReport(adminEmail, reportId, resolution) {
  return post("/admin/reports/" + reportId + "/resolve", { admin_email: adminEmail, resolution: resolution });
}
export function getAllBookings(adminEmail) {
  return get("/admin/bookings?admin_email=" + e(adminEmail));
}
export function adminCancelBooking(bookingId, adminEmail, reason) {
  return post("/admin/bookings/" + bookingId + "/cancel", { admin_email: adminEmail, reason: reason });
}
export function createReport(data) {
  return post("/reports", data);
}

// ---- venues and categories ----
export function getAllVenues() {
  return get("/venues");
}
export function getVenuesByVendor(vendorEmail) {
  return get("/venues/vendor/" + e(vendorEmail));
}
export function createVenue(name, address, vendorEmail, mapsUrl) {
  return post("/venues", { name: name, address: address, vendor_email: vendorEmail, maps_url: mapsUrl });
}
export function updateVenueMapsUrl(venueId, vendorEmail, mapsUrl) {
  return put("/venues/" + venueId + "/maps_url", { vendor_email: vendorEmail, maps_url: mapsUrl });
}
export function deleteVenue(venueId) {
  return del("/venues/" + venueId);
}
export function getVendorCategories(vendorEmail) {
  return get("/vendor_categories/" + e(vendorEmail));
}
export function addVendorCategory(vendorEmail, name) {
  return post("/vendor_categories", { vendor_email: vendorEmail, name: name });
}
export function deleteVendorCategory(categoryId) {
  return del("/vendor_categories/" + categoryId);
}

// ---- events ----
export function getAllEvents() {
  return get("/events");
}
export function getEventsByVendor(vendorEmail) {
  return get("/events/vendor/" + e(vendorEmail));
}
export function getEventRatings() {
  return get("/events/ratings");
}
export function getStaffSchedule(staffEmail) {
  return get("/events/today?staff_email=" + e(staffEmail));
}
export function createEvent(data) {
  return post("/events", data);
}
export function updateEvent(eventId, data) {
  return put("/events/" + eventId, data);
}
export function deleteEvent(eventId) {
  return del("/events/" + eventId);
}
export function getEventCapacity(eventId, date) {
  let path = "/events/" + eventId + "/capacity";
  if (date) {
    path = path + "?date=" + e(date);
  }
  return get(path);
}
export function getEventDemand(eventId) {
  return get("/events/" + eventId + "/demand");
}
export function eventImageUrl(eventId) {
  // the demo has no server: this address fails on purpose, so the picture falls back to the category photo
  if (demoMode) {
    return "no-server-picture.jpg";
  }
  return BASE_URL + "/events/" + eventId + "/image";
}

// ---- bookings ----
export function createBooking(customerEmail, eventId, bookingDate, guests, clientName) {
  return post("/bookings", {
    customer_email: customerEmail, event_id: eventId, booking_date: bookingDate,
    guests: guests, client_name: clientName || "",
  });
}
export function getBookingsByCustomer(email) {
  return get("/bookings/customer/" + e(email));
}
export function getBookingsByVendor(vendorEmail) {
  return get("/bookings/vendor/" + e(vendorEmail));
}
export function cancelBooking(bookingId, customerEmail, reason) {
  return post("/bookings/" + bookingId + "/cancel", { customer_email: customerEmail, reason: reason || "" });
}
export function vendorCancelBooking(bookingId, vendorEmail, reason) {
  return post("/bookings/" + bookingId + "/vendor_cancel", { vendor_email: vendorEmail, reason: reason });
}

// ---- tickets and support ----
export function verifyTicket(staffEmail, ticketCode, eventTitle) {
  return post("/tickets/verify", { staff_email: staffEmail, ticket_code: ticketCode, expected_event_title: eventTitle });
}
export function createSupportTicket(customerEmail, subject, message, eventTitle) {
  return post("/support", { customer_email: customerEmail, subject: subject, message: message, event_title: eventTitle });
}
export function getSupportTicketsByCustomer(email) {
  return get("/support/customer/" + e(email));
}
export function getOpenSupportTickets(staffEmail) {
  return get("/support/open?staff_email=" + e(staffEmail));
}
export function resolveSupportTicket(ticketId, staffEmail) {
  return post("/support/" + ticketId + "/resolve", { staff_email: staffEmail });
}

// ---- vehicles and dispatch ----
export function getVehicleTypes() {
  return get("/vehicle_types");
}
export function getAllVehicles(dispatcherEmail) {
  return get("/vehicles/" + e(dispatcherEmail));
}
export function createVehicle(data) {
  return post("/vehicles", data);
}
export function deleteVehicle(vehicleId) {
  return del("/vehicles/" + vehicleId);
}
export function updateVehicleStatus(vehicleId, status) {
  return put("/vehicles/" + vehicleId + "/status", { status: status });
}
export function freeVehicle(vehicleId) {
  return post("/vehicles/" + vehicleId + "/free");
}
export function getAssignedVehicles(eventId) {
  return get("/dispatch/" + eventId + "/vehicles");
}
export function dispatchVehicles(eventId, vehicleAssignments) {
  return post("/dispatch", { event_id: eventId, vehicle_assignments: vehicleAssignments });
}

// ---- partner shopping list ----
export function getCartItems(partnerEmail) {
  return get("/cart/" + e(partnerEmail));
}
export function addToCart(partnerEmail, eventId, bookingDate, guests, clientName) {
  return post("/cart", {
    partner_email: partnerEmail, event_id: eventId, booking_date: bookingDate,
    guests: guests, client_name: clientName || "",
  });
}
export function removeFromCart(cartId, partnerEmail) {
  return post("/cart/" + cartId + "/remove", { partner_email: partnerEmail });
}
export function checkoutCart(partnerEmail) {
  return post("/cart/" + e(partnerEmail) + "/checkout");
}

// ---- reviews ----
export function getMyExperiences(email) {
  return get("/experiences/customer/" + e(email));
}
export function submitReview(customerEmail, bookingId, rating, comment) {
  return post("/reviews", { customer_email: customerEmail, booking_id: bookingId, rating: rating, comment: comment });
}
