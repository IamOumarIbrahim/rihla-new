// dispatcher: send vehicles to an event
// when an event has vehicles, its capacity is the seats of those vehicles
import { useEffect, useState } from "react";
import { Card, Select, Table, Button, Typography, Space, Statistic, Checkbox, App, Empty } from "antd";
import { Truck } from "pulsoicon-react";
import { getAllEvents, getAllVehicles, getAssignedVehicles, dispatchVehicles, freeVehicle, getEventCapacity, getEventDemand } from "../api.js";
import { scheduleText } from "../components/booking.jsx";

export default function Dispatch(props) {
  const email = props.user.email;
  const [events, setEvents] = useState([]);
  const [eventId, setEventId] = useState(null);
  const [vehicles, setVehicles] = useState([]);
  const [assigned, setAssigned] = useState([]);
  const [capacity, setCapacity] = useState(null);
  const [demand, setDemand] = useState(null);
  const [chosen, setChosen] = useState([]);
  const [repeat, setRepeat] = useState(false);
  const { message } = App.useApp();

  useEffect(function () {
    getAllEvents().then(function (r) {
      if (r.success) {
        setEvents(r.events);
        if (r.events.length > 0) pick(r.events[0].id);
      }
    });
  }, []);

  async function pick(id) {
    setEventId(id);
    setChosen([]);
    const v = await getAllVehicles(email);
    if (v.success) setVehicles(v.vehicles);
    const a = await getAssignedVehicles(id);
    if (a.success) setAssigned(a.vehicles);
    const c = await getEventCapacity(id);
    if (c.success) setCapacity(c.capacity);
    const d = await getEventDemand(id);
    if (d.success) setDemand(d);
  }

  async function send() {
    const list = [];
    for (let i = 0; i < chosen.length; i++) {
      list.push({ vehicle_id: chosen[i], auto_reassign_recurring: repeat ? 1 : 0 });
    }
    const r = await dispatchVehicles(eventId, list);
    if (r.success) {
      message.success(r.assigned + " vehicle(s) sent to the event");
      pick(eventId);
    } else {
      message.error(r.message);
    }
  }

  async function free(v) {
    await freeVehicle(v.id);
    pick(eventId);
  }

  const free_list = [];
  for (let i = 0; i < vehicles.length; i++) {
    if (vehicles[i].status === "Available") free_list.push(vehicles[i]);
  }
  let chosenSeats = 0;
  for (let i = 0; i < free_list.length; i++) {
    if (chosen.indexOf(free_list[i].id) !== -1) chosenSeats = chosenSeats + free_list[i].capacity;
  }

  let current = null;
  for (let i = 0; i < events.length; i++) {
    if (events[i].id === eventId) current = events[i];
  }

  return (
    <Space direction="vertical" size={16} style={{ width: "100%" }}>
      <Card>
        <Space size={24} wrap>
          <div>
            <Typography.Text strong>Event</Typography.Text>
            <Select
              style={{ width: 380, display: "block", marginTop: 4 }}
              value={eventId}
              onChange={pick}
              options={events.map((ev) => ({ value: ev.id, label: ev.title + " | " + scheduleText(ev) }))}
            />
          </div>
          <Statistic title="Seats per day now" value={capacity ? capacity.total : 0} suffix={capacity && capacity.source === "vehicles" ? "(from vehicles)" : "(event capacity)"} />
          <Statistic title="Upcoming guests" value={demand ? demand.guests : 0} />
        </Space>
        {current ? <Typography.Paragraph type="secondary" style={{ marginTop: 8, marginBottom: 0 }}>{current.venue_name} at {current.recur_time}</Typography.Paragraph> : null}
      </Card>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, alignItems: "start" }}>
        <Card title="Available vehicles">
          {free_list.length === 0 ? <Empty description="No free vehicles" /> : null}
          <Checkbox.Group value={chosen} onChange={setChosen} style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {free_list.map(function (v) {
              return (
                <Checkbox key={v.id} value={v.id}>
                  {v.license_number} | {v.vehicle_type} | {v.capacity} seats | {v.location}
                </Checkbox>
              );
            })}
          </Checkbox.Group>
          <div style={{ marginTop: 16 }}>
            <Checkbox checked={repeat} onChange={(e) => setRepeat(e.target.checked)}>Keep them on this event every week</Checkbox>
          </div>
          <Button type="primary" icon={<Truck size={16} />} disabled={chosen.length === 0} onClick={send} style={{ marginTop: 16 }}>
            Send {chosen.length} vehicle(s), {chosenSeats} seats
          </Button>
        </Card>
        <Card title="On this event">
          <Table
            rowKey="id"
            size="small"
            pagination={false}
            dataSource={assigned}
            locale={{ emptyText: "No vehicles yet, the event uses its own capacity" }}
            columns={[
              { title: "License", dataIndex: "license_number" },
              { title: "Type", dataIndex: "vehicle_type" },
              { title: "", key: "free", render: (v) => <Button size="small" onClick={() => free(v)}>Free</Button> },
            ]}
          />
        </Card>
      </div>
    </Space>
  );
}
