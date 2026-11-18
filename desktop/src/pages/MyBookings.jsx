// my bookings (customers and partners): upcoming and past bookings with the ticket code,
// and cancel with the refund the rules give (48 h or more 100%, 24 to 48 h 50%, under 24 h none)
import { useEffect, useState } from "react";
import { Card, Tag, Typography, Button, Popconfirm, Segmented, Empty, Skeleton, Space, App } from "antd";
import { CalendarDays, MapPin, Users, Undo2 } from "pulsoicon-react";
import { getBookingsByCustomer, cancelBooking, getCurrency } from "../api.js";
import { formatMoney } from "../money.js";
import { formatCode } from "../components/booking.jsx";

// colour of each booking status
const STATUS_COLOR = { Confirmed: "blue", "Checked in": "green", Cancelled: "default", Expired: "default", Used: "green" };

export default function MyBookings(props) {
  const [bookings, setBookings] = useState(null);
  const [currency, setCurrency] = useState("AED");
  const [filter, setFilter] = useState("Upcoming");
  const { message } = App.useApp();

  useEffect(function () {
    load();
  }, []);

  async function load() {
    const r = await getBookingsByCustomer(props.user.email);
    setBookings(r.success ? r.bookings : []);
    const c = await getCurrency(props.user.email);
    if (c.success) setCurrency(c.currency);
  }

  async function cancel(booking) {
    const r = await cancelBooking(booking.id, props.user.email, "");
    if (r.success) {
      message.success(r.message || "Booking cancelled");
      load();
    } else {
      message.error(r.message);
    }
  }

  if (bookings === null) {
    return <Skeleton active paragraph={{ rows: 6 }} />;
  }

  const today = new Date().toISOString().slice(0, 10);
  const shown = [];
  for (let i = 0; i < bookings.length; i++) {
    const b = bookings[i];
    const upcoming = b.booking_date >= today && b.status === "Confirmed";
    if (filter === "Upcoming" && !upcoming) continue;
    if (filter === "Past and cancelled" && upcoming) continue;
    shown.push(b);
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>
          {props.user.role === "Partner" ? "Partner bookings" : "My bookings"}
        </Typography.Title>
        <Segmented options={["Upcoming", "Past and cancelled", "All"]} value={filter} onChange={setFilter} />
      </Space>

      {shown.length === 0 ? <Empty description="No bookings here yet" /> : null}

      <Space direction="vertical" style={{ width: "100%" }} size={12}>
        {shown.map(function (b, index) {
          let refundNote = "";
          if (b.can_cancel && b.refund_if_cancelled) {
            refundNote = "Cancel now for a " + b.refund_if_cancelled + "% refund.";
          }
          if (b.status === "Cancelled" && b.refund_percent !== null) {
            refundNote = "Refunded " + b.refund_percent + "% (" + formatMoney(b.refund_amount, currency) + ")";
            if (b.cancel_reason) refundNote = refundNote + " | Reason: " + b.cancel_reason;
          }
          return (
            <div key={b.id}>
              <Card styles={{ body: { display: "flex", gap: 24, alignItems: "center" } }}>
                <div style={{ flex: 1 }}>
                  <Space>
                    <Typography.Title level={5} style={{ margin: 0 }}>{b.event_title}</Typography.Title>
                    <Tag color={STATUS_COLOR[b.status] || "default"}>{b.status}</Tag>
                  </Space>
                  <div style={{ marginTop: 6 }}>
                    <Space size={16} wrap>
                      <Typography.Text type="secondary"><Space size={4}><CalendarDays size={14} />{b.booking_date} at {b.event_time}</Space></Typography.Text>
                      <Typography.Text type="secondary"><Space size={4}><MapPin size={14} />{b.venue_name}</Space></Typography.Text>
                      <Typography.Text type="secondary"><Space size={4}><Users size={14} />{b.guests} guest(s)</Space></Typography.Text>
                      {b.client_name ? <Typography.Text type="secondary">Client: {b.client_name}</Typography.Text> : null}
                    </Space>
                  </div>
                  <div style={{ marginTop: 8 }}>
                    <Typography.Text type="secondary">Ticket </Typography.Text>
                    <span className="ticket-code">{formatCode(b.ticket_code)}</span>
                  </div>
                  {refundNote ? <Typography.Text type="secondary" style={{ fontSize: 12 }}>{refundNote}</Typography.Text> : null}
                </div>
                <div style={{ textAlign: "right" }}>
                  <Typography.Title level={5} style={{ margin: 0 }}>{formatMoney(b.total_price, currency)}</Typography.Title>
                  {b.can_cancel ? (
                    <Popconfirm
                      title="Cancel this booking?"
                      description={"You get " + b.refund_if_cancelled + "% back: " + formatMoney((b.total_price * b.refund_if_cancelled) / 100, currency)}
                      okText="Cancel booking"
                      cancelText="Keep it"
                      onConfirm={() => cancel(b)}
                    >
                      <Button danger icon={<Undo2 size={14} />} style={{ marginTop: 8 }}>Cancel</Button>
                    </Popconfirm>
                  ) : null}
                </div>
              </Card>
            </div>
          );
        })}
      </Space>
    </div>
  );
}
