// staff: check tickets in at my venue, and today's schedule
// a ticket only works once, only at its own venue, and only for the chosen event
import { useEffect, useRef, useState } from "react";
import { Card, Select, Input, Button, Table, Typography, Space, Alert, App } from "antd";
import { ScanLine, CircleCheck, CircleX, RefreshCw } from "pulsoicon-react";
import { motion, AnimatePresence } from "motion/react";
import { getStaffVenue, getStaffSchedule, getAllEvents, verifyTicket } from "../api.js";
import { Shake } from "../components/motion.jsx";
import { formatCode } from "../components/booking.jsx";

export default function StaffCheckIn(props) {
  const email = props.user.email;
  const [venue, setVenue] = useState(null);
  const [venueEvents, setVenueEvents] = useState([]);
  const [schedule, setSchedule] = useState([]);
  const [eventTitle, setEventTitle] = useState(null);
  const [code, setCode] = useState("");
  const [result, setResult] = useState(null);
  const [checks, setChecks] = useState(0);
  const [busy, setBusy] = useState(false);
  const codeInput = useRef(null);

  useEffect(function () {
    load();
  }, []);

  async function load() {
    const v = await getStaffVenue(email);
    if (!v.success) {
      setVenue(false);
      return;
    }
    setVenue(v.venue);
    // the events that take place at this venue
    const all = await getAllEvents();
    const mine = [];
    if (all.success) {
      for (let i = 0; i < all.events.length; i++) {
        if (all.events[i].venue_id === v.venue.id) mine.push(all.events[i]);
      }
    }
    setVenueEvents(mine);
    if (mine.length > 0) setEventTitle(mine[0].title);
    loadSchedule();
  }

  async function loadSchedule() {
    const s = await getStaffSchedule(email);
    if (s.success) setSchedule(s.events);
  }

  // keep digits only and show them in groups of 4
  function changeCode(text) {
    let digits = "";
    for (let i = 0; i < text.length; i++) {
      if (text[i] >= "0" && text[i] <= "9") digits = digits + text[i];
    }
    setCode(digits.slice(0, 16));
  }

  async function check() {
    if (code.length !== 16) {
      setResult({ success: false, message: "A ticket code has 16 digits." });
      setChecks(checks + 1);
      return;
    }
    setBusy(true);
    const r = await verifyTicket(email, code, eventTitle);
    setBusy(false);
    setResult(r);
    setChecks(checks + 1);
    if (r.success) {
      setCode("");
      loadSchedule();
    }
    if (codeInput.current) codeInput.current.focus();
  }

  if (venue === false) {
    return <Alert type="warning" showIcon message="This account is not staff at a venue. Choose your venue in Settings." />;
  }

  const columns = [
    { title: "Event", dataIndex: "title", key: "title" },
    { title: "Time", dataIndex: "time", key: "time" },
    { title: "Bookings", dataIndex: "bookings", key: "bookings", align: "right" },
    { title: "Expected guests", dataIndex: "guests", key: "guests", align: "right" },
    { title: "Checked in", dataIndex: "checked_in", key: "checked_in", align: "right" },
  ];

  return (
    <Space direction="vertical" size={16} style={{ width: "100%" }}>
      <div>
        <Typography.Title level={4} style={{ margin: 0 }}>{venue ? venue.name : ""}</Typography.Title>
        <Typography.Text type="secondary">{venue ? venue.address + " | Manager: " + venue.manager_email : ""}</Typography.Text>
      </div>

      <Card title="Ticket check-in">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div>
            <Typography.Text strong>Event</Typography.Text>
            <Select
              style={{ width: "100%", marginTop: 4 }}
              value={eventTitle}
              onChange={setEventTitle}
              options={venueEvents.map((ev) => ({ value: ev.title, label: ev.title }))}
            />
          </div>
          <div>
            <Typography.Text strong>16-digit ticket code</Typography.Text>
            <Input
              ref={codeInput}
              style={{ marginTop: 4, fontFamily: "'Noto Sans Mono', monospace", fontSize: 18, letterSpacing: 2 }}
              value={formatCode(code)}
              onChange={(e) => changeCode(e.target.value)}
              onPressEnter={check}
              placeholder="1234 5678 9012 3456"
              prefix={<ScanLine size={18} />}
            />
          </div>
        </div>
        <Button type="primary" size="large" block style={{ marginTop: 16 }} onClick={check} loading={busy}>
          Check ticket
        </Button>
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
          Demo ticket for Burj Khalifa staff: 1234 5678 9012 3456 (New year dinner)
        </Typography.Text>

        <AnimatePresence mode="wait">
          {result ? (
            <motion.div
              key={checks}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ type: "spring", duration: 0.2, bounce: 0 }}
              style={{ marginTop: 16 }}
            >
              <Shake trigger={result.success ? 0 : checks}>
                <Alert
                  type={result.success ? "success" : "error"}
                  showIcon
                  icon={result.success ? <CircleCheck size={22} play /> : <CircleX size={22} play />}
                  message={result.success ? "Access granted" : "Entry refused"}
                  description={result.message}
                />
              </Shake>
            </motion.div>
          ) : null}
        </AnimatePresence>
      </Card>

      <Card title="Today's schedule" extra={<Button icon={<RefreshCw size={14} />} onClick={loadSchedule}>Refresh</Button>}>
        <Table rowKey="id" columns={columns} dataSource={schedule} pagination={false} locale={{ emptyText: "No events at your venue today" }} />
      </Card>
    </Space>
  );
}
