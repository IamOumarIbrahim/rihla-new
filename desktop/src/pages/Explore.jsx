// explore: all events as cards with search, category tabs and a price filter
// clicking a card opens the booking drawer (customers pay, partners add to the shopping list)
import { useEffect, useState } from "react";
import {
  Card, Input, Select, Tabs, Tag, Rate, Typography, Drawer, DatePicker, InputNumber, Button,
  Descriptions, Space, Empty, Skeleton, App, Alert,
} from "antd";
import { Search, MapPin, CalendarDays, Users, ShoppingCart, Ticket } from "pulsoicon-react";
import dayjs from "dayjs";
import {
  getAllEvents, getEventRatings, getEventCapacity, eventImageUrl, createBooking, addToCart, getCurrency, getCartItems,
} from "../api.js";
import { priceToNumber, vatBreakdown, formatMoney } from "../money.js";
import { StaggerItem, SeatMeter, CountUp } from "../components/motion.jsx";
import { eventRunsOn, scheduleText, PaymentModal, ConfirmModal } from "../components/booking.jsx";
import dinnerPhoto from "../images/dinner.jpg";
import marinaPhoto from "../images/marina.jpg";
import desertPhoto from "../images/desert.jpg";

const MAX_GUESTS_PER_BOOKING = 10;

// the first day from today that the event runs on (looks 60 days ahead)
function nextRunDay(event) {
  let day = dayjs().startOf("day");
  for (let i = 0; i < 60; i++) {
    if (eventRunsOn(event, day)) {
      return day;
    }
    day = day.add(1, "day");
  }
  return null;
}

export default function Explore(props) {
  const isPartner = props.user.role === "Partner";
  const [events, setEvents] = useState(null);
  const [ratings, setRatings] = useState({});
  // seats on the next day each event runs: { eventId: {remaining, total} }
  const [seats, setSeats] = useState({});
  const [currency, setCurrencyCode] = useState("AED");
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [maxPrice, setMaxPrice] = useState(0);
  const [open, setOpen] = useState(null);

  useEffect(function () {
    loadAll();
  }, []);

  async function loadAll() {
    const r = await getAllEvents();
    const list = r.success ? r.events : [];
    setEvents(list);
    const rr = await getEventRatings();
    if (rr.success) setRatings(rr.ratings);
    const cr = await getCurrency(props.user.email);
    if (cr.success) setCurrencyCode(cr.currency);

    const found = {};
    for (let i = 0; i < list.length; i++) {
      const day = nextRunDay(list[i]);
      if (day) {
        const c = await getEventCapacity(list[i].id, day.format("YYYY-MM-DD"));
        if (c.success) found[list[i].id] = c.capacity;
      }
    }
    setSeats(found);
  }

  if (events === null) {
    return <Skeleton active paragraph={{ rows: 8 }} />;
  }

  // the category tabs come from the events themselves
  const categories = ["All"];
  for (let i = 0; i < events.length; i++) {
    if (categories.indexOf(events[i].category) === -1) {
      categories.push(events[i].category);
    }
  }

  const shown = [];
  for (let i = 0; i < events.length; i++) {
    const ev = events[i];
    const text = (ev.title + " " + ev.venue_name + " " + ev.category).toLowerCase();
    if (search && text.indexOf(search.toLowerCase()) === -1) continue;
    if (category !== "All" && ev.category !== category) continue;
    if (maxPrice > 0 && priceToNumber(ev.price) > maxPrice) continue;
    shown.push(ev);
  }

  return (
    <div>
      <Card styles={{ body: { padding: 16 } }}>
        <Space.Compact style={{ width: "100%" }}>
          <Input
            size="large"
            prefix={<Search size={16} />}
            placeholder="Search safaris, yacht cruises, dinners"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            allowClear
          />
          <Select
            size="large"
            style={{ width: 200 }}
            value={maxPrice}
            onChange={setMaxPrice}
            options={[
              { value: 0, label: "Any price" },
              { value: 200, label: "Up to 200 AED" },
              { value: 400, label: "Up to 400 AED" },
              { value: 700, label: "Up to 700 AED" },
            ]}
          />
        </Space.Compact>
      </Card>

      <Tabs
        activeKey={category}
        onChange={setCategory}
        items={categories.map((c) => ({ key: c, label: c === "All" ? "All experiences" : c }))}
        style={{ marginTop: 8 }}
      />

      {shown.length === 0 ? <Empty description="No experiences match your search" /> : null}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 16 }}>
        {shown.map(function (ev, index) {
          const rating = ratings[String(ev.id)];
          const cap = seats[ev.id];
          let bookedPercent = 0;
          if (cap && cap.total > 0) {
            bookedPercent = Math.round(((cap.total - cap.remaining) / cap.total) * 100);
          }
          return (
            <StaggerItem key={ev.id} index={index}>
              <Card
                hoverable
                onClick={() => setOpen(ev)}
                cover={<EventPicture eventId={ev.id} category={ev.category} />}
                styles={{ body: { padding: 16 } }}
                actions={[
                  <Typography.Text strong key="p" style={{ fontSize: 16 }}>
                    {formatMoney(priceToNumber(ev.price), currency)}
                  </Typography.Text>,
                  <Button type="primary" key="b" icon={isPartner ? <ShoppingCart size={14} /> : <Ticket size={14} />}>
                    {isPartner ? "Add to list" : "Book"}
                  </Button>,
                ]}
              >
                <Tag color="blue">{ev.category}</Tag>
                <Typography.Title level={5} style={{ margin: "8px 0 2px" }}>{ev.title}</Typography.Title>
                <Typography.Text type="secondary" style={{ fontSize: 13 }}>
                  {ev.venue_name} | {scheduleText(ev)}
                </Typography.Text>
                <div style={{ marginTop: 6 }}>
                  {rating ? (
                    <Space size={6}>
                      <Rate disabled allowHalf value={rating.average} style={{ fontSize: 12 }} />
                      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                        {rating.average} ({rating.count})
                      </Typography.Text>
                    </Space>
                  ) : (
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>No reviews yet</Typography.Text>
                  )}
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 10 }}>
                  <div style={{ flex: 1 }}>
                    <SeatMeter total={cap ? cap.total : 0} remaining={cap ? cap.remaining : 0} />
                  </div>
                  <Typography.Text type="secondary" style={{ fontSize: 12 }}>{bookedPercent}% booked</Typography.Text>
                </div>
              </Card>
            </StaggerItem>
          );
        })}
      </div>

      <BookingDrawer
        event={open}
        user={props.user}
        currency={currency}
        isPartner={isPartner}
        onClose={() => setOpen(null)}
        onDone={loadAll}
        setCartCount={props.setCartCount}
      />
    </div>
  );
}

// when an event has no picture of its own, a real photo that fits its category
export function fallbackPicture(category) {
  const text = (category || "").toLowerCase();
  if (text.indexOf("dinner") !== -1 || text.indexOf("dining") !== -1) {
    return dinnerPhoto;
  }
  if (text.indexOf("yacht") !== -1 || text.indexOf("cruise") !== -1) {
    return marinaPhoto;
  }
  return desertPhoto;
}

// the event picture from the server, or the fallback photo
export function EventPicture(props) {
  const [failed, setFailed] = useState(false);
  let src = eventImageUrl(props.eventId);
  if (failed) {
    src = fallbackPicture(props.category);
  }
  return <img className="event-img" style={props.style} alt="" src={src} onError={() => setFailed(true)} />;
}

// the drawer to choose a date and the guests, then pay (customer) or add to the list (partner)
function BookingDrawer(props) {
  const ev = props.event;
  const [day, setDay] = useState(null);
  const [guests, setGuests] = useState(1);
  const [clientName, setClientName] = useState("");
  const [capacity, setCapacity] = useState(null);
  const [paying, setPaying] = useState(false);
  const [confirmed, setConfirmed] = useState(null);
  const [problem, setProblem] = useState("");
  const { message } = App.useApp();

  // a new event: start on its next day
  useEffect(
    function () {
      if (ev) {
        const first = nextRunDay(ev);
        setDay(first);
        setGuests(1);
        setClientName("");
        setProblem("");
        loadCapacity(first);
      }
    },
    [ev ? ev.id : null]
  );

  async function loadCapacity(d) {
    setCapacity(null);
    if (!ev || !d) return;
    const r = await getEventCapacity(ev.id, d.format("YYYY-MM-DD"));
    if (r.success) setCapacity(r.capacity);
  }

  function changeDay(d) {
    setDay(d);
    loadCapacity(d);
  }

  if (!ev) {
    return <Drawer open={false} />;
  }

  const unit = priceToNumber(ev.price);
  const price = vatBreakdown(unit * (guests || 0));
  let maxGuests = MAX_GUESTS_PER_BOOKING;
  if (props.isPartner && capacity) {
    maxGuests = capacity.remaining;
  }

  async function onPaid(payment) {
    const r = await createBooking(props.user.email, ev.id, day.format("YYYY-MM-DD"), guests, "");
    setPaying(false);
    if (!r.success) {
      setProblem(r.message);
      return;
    }
    const b = r.booking;
    setConfirmed({
      payment: payment,
      entries: [{ title: b.event_title, venue: b.venue_name, date: b.booking_date, time: b.event_time, guests: b.guests, ticket_code: b.ticket_code, base: b.base_price }],
    });
    loadCapacity(day);
  }

  async function addToList() {
    if (!clientName.trim()) {
      setProblem("Please enter the group or client name.");
      return;
    }
    const r = await addToCart(props.user.email, ev.id, day.format("YYYY-MM-DD"), guests, clientName.trim());
    if (!r.success) {
      setProblem(r.message);
      return;
    }
    message.success("Added to your shopping list");
    const c = await getCartItems(props.user.email);
    if (c.success) props.setCartCount(c.items.length);
    props.onClose();
  }

  function start() {
    setProblem("");
    if (!day) {
      setProblem("Please choose a date.");
      return;
    }
    if (!guests || guests < 1) {
      setProblem("You must book at least 1 guest.");
      return;
    }
    if (props.isPartner) {
      addToList();
    } else {
      setPaying(true);
    }
  }

  let seatsText = "";
  if (capacity) {
    seatsText = capacity.remaining + " seats left on this day";
  }

  return (
    <Drawer open={props.event !== null} onClose={props.onClose} width={520} title={ev.title} destroyOnHidden>
      <EventPicture eventId={ev.id} category={ev.category} style={{ height: 220, borderRadius: 8 }} />
      <Typography.Paragraph style={{ marginTop: 16 }}>{ev.desc}</Typography.Paragraph>

      <Descriptions column={1} size="small">
        <Descriptions.Item label={<Space><MapPin size={14} />Venue</Space>}>
          {ev.venue_name}
          {ev.maps_url ? (
            <a href={ev.maps_url} target="_blank" rel="noreferrer" style={{ marginLeft: 8 }}>Open map</a>
          ) : null}
        </Descriptions.Item>
        <Descriptions.Item label={<Space><CalendarDays size={14} />When</Space>}>
          {scheduleText(ev)} at {ev.recur_time}
        </Descriptions.Item>
      </Descriptions>

      <Card size="small" style={{ marginTop: 12 }}>
        <Space direction="vertical" style={{ width: "100%" }} size={12}>
          <div>
            <Typography.Text strong>Date</Typography.Text>
            <DatePicker
              style={{ width: "100%", marginTop: 4 }}
              value={day}
              onChange={changeDay}
              allowClear={false}
              disabledDate={(d) => d.isBefore(dayjs().startOf("day")) || !eventRunsOn(ev, d)}
            />
          </div>
          <div>
            <Typography.Text strong><Space><Users size={14} />Guests</Space></Typography.Text>
            <InputNumber min={1} max={maxGuests} value={guests} onChange={setGuests} style={{ width: "100%", marginTop: 4 }} />
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              {props.isPartner ? "Partners can book more than 10 guests while seats are left." : "Customers can book 1 to 10 guests at a time."}
            </Typography.Text>
          </div>
          {props.isPartner ? (
            <div>
              <Typography.Text strong>Group or client name</Typography.Text>
              <Input value={clientName} onChange={(e) => setClientName(e.target.value)} placeholder="Desert Rose Holidays" style={{ marginTop: 4 }} />
            </div>
          ) : null}
          <div>
            <SeatMeter total={capacity ? capacity.total : 0} remaining={capacity ? capacity.remaining : 0} />
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>{seatsText}</Typography.Text>
          </div>
        </Space>
      </Card>

      <Descriptions column={1} size="small" bordered style={{ marginTop: 16 }}>
        <Descriptions.Item label={"Price (" + (guests || 0) + " x " + formatMoney(unit, props.currency) + ")"}>
          <CountUp value={price.base} format={(v) => formatMoney(v, props.currency)} />
        </Descriptions.Item>
        <Descriptions.Item label="VAT (5%)">
          <CountUp value={price.vat} format={(v) => formatMoney(v, props.currency)} />
        </Descriptions.Item>
        <Descriptions.Item label="Total">
          <b><CountUp value={price.total} format={(v) => formatMoney(v, props.currency)} /></b>
        </Descriptions.Item>
      </Descriptions>

      {problem ? <Alert type="error" showIcon message={problem} style={{ marginTop: 12 }} /> : null}

      <Button type="primary" size="large" block style={{ marginTop: 16 }} onClick={start}
        icon={props.isPartner ? <ShoppingCart size={16} /> : <Ticket size={16} />}>
        {props.isPartner ? "Add to shopping list" : "Book and pay"}
      </Button>
      <Typography.Paragraph type="secondary" style={{ fontSize: 12, marginTop: 8 }}>
        Cancel 48 hours or more before the start for a full refund, 24 to 48 hours for half. Less than 24 hours: no cancel.
      </Typography.Paragraph>

      <PaymentModal
        open={paying}
        baseAed={price.base}
        currency={props.currency}
        onCancel={() => setPaying(false)}
        onPaid={onPaid}
      />
      <ConfirmModal
        open={confirmed !== null}
        entries={confirmed ? confirmed.entries : []}
        payment={confirmed ? confirmed.payment : null}
        email={props.user.email}
        onClose={function () {
          setConfirmed(null);
          props.onClose();
          props.onDone();
        }}
      />
    </Drawer>
  );
}
