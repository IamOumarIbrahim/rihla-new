// admin: every booking, an admin can cancel any upcoming one with a full refund and a reason
import { useEffect, useState } from "react";
import { Table, Tag, Button, Modal, Input, Typography, Space, App } from "antd";
import { Search } from "pulsoicon-react";
import { getAllBookings, adminCancelBooking } from "../api.js";
import { formatMoney } from "../money.js";
import { formatCode } from "../components/booking.jsx";

export default function AdminBookings(props) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [cancelling, setCancelling] = useState(null);
  const [reason, setReason] = useState("");
  const { message } = App.useApp();

  useEffect(function () {
    load();
  }, []);

  async function load() {
    setLoading(true);
    const r = await getAllBookings(props.user.email);
    setRows(r.success ? r.bookings : []);
    setLoading(false);
  }

  async function confirmCancel() {
    const r = await adminCancelBooking(cancelling.id, props.user.email, reason.trim());
    if (r.success) {
      message.success("Booking cancelled with a full refund");
      setCancelling(null);
      setReason("");
      load();
    } else {
      message.error(r.message);
    }
  }

  const shown = [];
  for (let i = 0; i < rows.length; i++) {
    const text = (rows[i].event_title + " " + rows[i].customer_email + " " + rows[i].ticket_code).toLowerCase();
    if (!search || text.indexOf(search.toLowerCase().replace(/ /g, "")) !== -1 || text.indexOf(search.toLowerCase()) !== -1) shown.push(rows[i]);
  }

  const today = new Date().toISOString().slice(0, 10);
  const columns = [
    { title: "Event", dataIndex: "event_title", key: "event_title" },
    { title: "Booked by", dataIndex: "customer_email", key: "customer_email" },
    { title: "Date", dataIndex: "booking_date", key: "booking_date", sorter: (a, b) => (a.booking_date < b.booking_date ? -1 : 1) },
    { title: "Guests", dataIndex: "guests", key: "guests", align: "right" },
    { title: "Total", key: "total", align: "right", render: (r) => formatMoney(r.total_price, "AED") },
    { title: "Ticket", key: "code", render: (r) => <span className="ticket-code">{formatCode(r.ticket_code)}</span> },
    { title: "Status", dataIndex: "status", key: "status", render: (s) => <Tag color={s === "Confirmed" ? "blue" : s === "Cancelled" ? "default" : "green"}>{s}</Tag> },
    {
      title: "",
      key: "actions",
      render: (r) => (r.status === "Confirmed" && r.booking_date >= today ? <Button size="small" danger onClick={() => setCancelling(r)}>Cancel</Button> : null),
    },
  ];

  return (
    <Space direction="vertical" size={16} style={{ width: "100%" }}>
      <Input prefix={<Search size={16} />} placeholder="Search event, email or ticket code" value={search} onChange={(e) => setSearch(e.target.value)} allowClear style={{ maxWidth: 420 }} />
      <Table rowKey="id" columns={columns} dataSource={shown} loading={loading} pagination={{ pageSize: 12 }} />
      <Modal
        open={cancelling !== null}
        title="Cancel this booking"
        okText="Cancel booking"
        okButtonProps={{ danger: true, disabled: reason.trim() === "" }}
        onOk={confirmCancel}
        onCancel={() => setCancelling(null)}
      >
        <Typography.Paragraph>The customer gets a full refund. A reason is required (up to 300 characters).</Typography.Paragraph>
        <Input.TextArea rows={3} maxLength={300} showCount value={reason} onChange={(e) => setReason(e.target.value)} />
      </Modal>
    </Space>
  );
}
