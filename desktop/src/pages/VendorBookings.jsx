// vendor: bookings on my events, a vendor can cancel any upcoming one with a full refund but needs a reason
import { useEffect, useState } from "react";
import { Table, Tag, Button, Modal, Input, Typography, Card, Statistic, Space, App } from "antd";
import { getBookingsByVendor, vendorCancelBooking } from "../api.js";
import { formatMoney } from "../money.js";
import { formatCode } from "../components/booking.jsx";

export default function VendorBookings(props) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(null);
  const [reason, setReason] = useState("");
  const { message } = App.useApp();

  useEffect(function () {
    load();
  }, []);

  async function load() {
    setLoading(true);
    const r = await getBookingsByVendor(props.user.email);
    setRows(r.success ? r.bookings : []);
    setLoading(false);
  }

  async function confirmCancel() {
    const r = await vendorCancelBooking(cancelling.id, props.user.email, reason.trim());
    if (r.success) {
      message.success("Booking cancelled with a full refund");
      setCancelling(null);
      setReason("");
      load();
    } else {
      message.error(r.message);
    }
  }

  // money from bookings that were not cancelled
  let earned = 0;
  let guests = 0;
  for (let i = 0; i < rows.length; i++) {
    if (rows[i].status !== "Cancelled") {
      earned = earned + Number(rows[i].total_price || 0);
      guests = guests + Number(rows[i].guests || 0);
    }
  }

  const columns = [
    { title: "Event", dataIndex: "event_title", key: "event_title" },
    { title: "Date", dataIndex: "booking_date", key: "booking_date", sorter: (a, b) => (a.booking_date < b.booking_date ? -1 : 1) },
    { title: "Customer", dataIndex: "customer_email", key: "customer_email" },
    { title: "Guests", dataIndex: "guests", key: "guests", align: "right" },
    { title: "Total", key: "total", align: "right", render: (r) => formatMoney(r.total_price, "AED") },
    { title: "Ticket", key: "code", render: (r) => <span className="ticket-code">{formatCode(r.ticket_code)}</span> },
    { title: "Status", dataIndex: "status", key: "status", render: (s) => <Tag color={s === "Confirmed" ? "blue" : s === "Cancelled" ? "default" : "green"}>{s}</Tag> },
    {
      title: "",
      key: "actions",
      render: function (r) {
        const today = new Date().toISOString().slice(0, 10);
        if (r.status !== "Confirmed" || r.booking_date < today) return null;
        return <Button size="small" danger onClick={() => setCancelling(r)}>Cancel</Button>;
      },
    },
  ];

  return (
    <div>
      <Space size={16} style={{ marginBottom: 16 }}>
        <Card size="small"><Statistic title="Bookings" value={rows.length} /></Card>
        <Card size="small"><Statistic title="Guests (not cancelled)" value={guests} /></Card>
        <Card size="small"><Statistic title="Earned (with VAT)" value={formatMoney(earned, "AED")} /></Card>
      </Space>
      <Table rowKey="id" columns={columns} dataSource={rows} loading={loading} pagination={{ pageSize: 10 }} />

      <Modal
        open={cancelling !== null}
        title="Cancel this booking"
        okText="Cancel booking"
        okButtonProps={{ danger: true, disabled: reason.trim() === "" }}
        onOk={confirmCancel}
        onCancel={() => setCancelling(null)}
      >
        <Typography.Paragraph>
          The customer gets a full refund. Please tell them why (up to 300 characters).
        </Typography.Paragraph>
        <Input.TextArea rows={3} maxLength={300} showCount value={reason} onChange={(e) => setReason(e.target.value)} />
      </Modal>
    </div>
  );
}
