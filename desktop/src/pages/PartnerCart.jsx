// partner: the shopping list, pay once for all of it
// the server books everything in one go: if one event is full, nothing is booked
import { useEffect, useState } from "react";
import { Card, Table, Button, Typography, Space, Empty, Popconfirm, Alert, App } from "antd";
import { Trash2, Wallet } from "pulsoicon-react";
import { getCartItems, removeFromCart, checkoutCart, getCurrency } from "../api.js";
import { vatBreakdown, formatMoney } from "../money.js";
import { PaymentModal, ConfirmModal } from "../components/booking.jsx";

export default function PartnerCart(props) {
  const email = props.user.email;
  const [items, setItems] = useState(null);
  const [currency, setCurrency] = useState("AED");
  const [paying, setPaying] = useState(false);
  const [confirmed, setConfirmed] = useState(null);
  const [problem, setProblem] = useState("");
  const { message } = App.useApp();

  useEffect(function () {
    load();
  }, []);

  async function load() {
    const r = await getCartItems(email);
    const list = r.success ? r.items : [];
    setItems(list);
    props.setCartCount(list.length);
    const c = await getCurrency(email);
    if (c.success) setCurrency(c.currency);
  }

  async function remove(item) {
    const r = await removeFromCart(item.id, email);
    if (r.success) {
      message.success("Removed");
      load();
    } else {
      message.error(r.message);
    }
  }

  async function onPaid(payment) {
    const r = await checkoutCart(email);
    setPaying(false);
    if (!r.success) {
      setProblem(r.message);
      return;
    }
    const entries = [];
    for (let i = 0; i < r.bookings.length; i++) {
      const b = r.bookings[i];
      entries.push({
        title: b.event_title, venue: b.venue_name, date: b.booking_date, time: b.event_time,
        guests: b.guests, client_name: b.client_name, ticket_code: b.ticket_code, base: b.base_price,
      });
    }
    setConfirmed({ payment: payment, entries: entries });
    load();
  }

  if (items === null) {
    return null;
  }
  if (items.length === 0 && confirmed === null) {
    return <Empty description="Your shopping list is empty. Add tours from Explore tours." />;
  }

  // the list prices are before VAT
  let base = 0;
  for (let i = 0; i < items.length; i++) {
    base = base + Number(items[i].total_price || 0);
  }
  const price = vatBreakdown(base);

  const columns = [
    { title: "Event", dataIndex: "title", key: "title" },
    { title: "Client", dataIndex: "client_name", key: "client_name" },
    { title: "Date", dataIndex: "booking_date", key: "booking_date" },
    { title: "Guests", dataIndex: "guests", key: "guests", align: "right" },
    { title: "Price", key: "price", align: "right", render: (r) => formatMoney(r.total_price, currency) },
    {
      title: "",
      key: "remove",
      render: (r) => (
        <Popconfirm title="Remove from the list?" onConfirm={() => remove(r)}>
          <Button size="small" type="text" danger icon={<Trash2 size={14} />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 16, alignItems: "start" }}>
      <Card title="Shopping list">
        <Table rowKey="id" columns={columns} dataSource={items} pagination={false} />
      </Card>
      <Card title="Total">
        <Space direction="vertical" style={{ width: "100%" }}>
          <Row label="Price" value={formatMoney(price.base, currency)} />
          <Row label="VAT (5%)" value={formatMoney(price.vat, currency)} />
          <Row label={<b>Total</b>} value={<b>{formatMoney(price.total, currency)}</b>} />
          {problem ? <Alert type="error" showIcon message={problem} /> : null}
          <Button type="primary" size="large" block icon={<Wallet size={16} />} onClick={() => { setProblem(""); setPaying(true); }}>
            Pay and book all
          </Button>
        </Space>
      </Card>

      <PaymentModal open={paying} baseAed={price.base} currency={currency} onCancel={() => setPaying(false)} onPaid={onPaid} />
      <ConfirmModal
        open={confirmed !== null}
        entries={confirmed ? confirmed.entries : []}
        payment={confirmed ? confirmed.payment : null}
        email={email}
        onClose={() => setConfirmed(null)}
      />
    </div>
  );
}

function Row(props) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between" }}>
      <Typography.Text type="secondary">{props.label}</Typography.Text>
      <Typography.Text>{props.value}</Typography.Text>
    </div>
  );
}
