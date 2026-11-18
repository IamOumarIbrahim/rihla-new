// support: ask the venue staff a question about an event you booked (up to 3 open at a time)
import { useEffect, useState } from "react";
import { Card, Form, Input, Select, Button, Typography, Tag, List, App } from "antd";
import { Send } from "pulsoicon-react";
import { createSupportTicket, getSupportTicketsByCustomer, getBookingsByCustomer } from "../api.js";

export default function Support(props) {
  const [tickets, setTickets] = useState([]);
  const [events, setEvents] = useState([]);
  const [form] = Form.useForm();
  const { message } = App.useApp();

  useEffect(function () {
    load();
  }, []);

  async function load() {
    const t = await getSupportTicketsByCustomer(props.user.email);
    if (t.success) setTickets(t.tickets);
    // only events the customer booked can get a question
    const b = await getBookingsByCustomer(props.user.email);
    if (b.success) {
      const titles = [];
      for (let i = 0; i < b.bookings.length; i++) {
        if (titles.indexOf(b.bookings[i].event_title) === -1) titles.push(b.bookings[i].event_title);
      }
      setEvents(titles);
    }
  }

  async function send(values) {
    const r = await createSupportTicket(props.user.email, values.subject, values.message, values.event_title);
    if (r.success) {
      message.success("Sent to the venue team");
      form.resetFields();
      load();
    } else {
      message.error(r.message);
    }
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "420px 1fr", gap: 16, alignItems: "start" }}>
      <Card title="Ask the venue team">
        <Form form={form} layout="vertical" onFinish={send} requiredMark={false}>
          <Form.Item label="Event" name="event_title" rules={[{ required: true, message: "Choose the event" }]}>
            <Select options={events.map((t) => ({ value: t, label: t }))} placeholder="Choose one of your bookings" />
          </Form.Item>
          <Form.Item label="Subject" name="subject" rules={[{ required: true, message: "Write a short subject" }]}>
            <Input maxLength={100} />
          </Form.Item>
          <Form.Item label="Message" name="message" rules={[{ required: true, message: "Write your question" }]}>
            <Input.TextArea rows={4} maxLength={1000} />
          </Form.Item>
          <Button type="primary" htmlType="submit" icon={<Send size={14} />}>Send</Button>
        </Form>
      </Card>
      <Card title="Your questions">
        <List
          dataSource={tickets}
          locale={{ emptyText: "No questions yet" }}
          renderItem={function (t) {
            return (
              <List.Item extra={<Tag color={t.status === "Open" ? "blue" : "green"}>{t.status}</Tag>}>
                <List.Item.Meta
                  title={t.subject}
                  description={<span>{t.event_title} | {t.created_at}<br />{t.message}</span>}
                />
              </List.Item>
            );
          }}
        />
      </Card>
    </div>
  );
}
