// vendor: my events, with create, edit and delete
// an event is one-time (one date) or recurring (some week days), it has a venue, a price in AED,
// a capacity (1 to 5000) and maybe a picture
import { useEffect, useState } from "react";
import {
  Card, Button, Modal, Form, Input, InputNumber, Select, Radio, Checkbox, DatePicker, TimePicker, Upload,
  Typography, Tag, Space, Popconfirm, Empty, Skeleton, App,
} from "antd";
import { Plus, Pencil, Trash2, ImagePlus } from "pulsoicon-react";
import dayjs from "dayjs";
import {
  getEventsByVendor, getVenuesByVendor, getVendorCategories, createEvent, updateEvent, deleteEvent, getEventDemand,
} from "../api.js";
import { priceToNumber, formatMoney } from "../money.js";
import { StaggerItem } from "../components/motion.jsx";
import { scheduleText } from "../components/booking.jsx";
import { EventPicture } from "./Explore.jsx";

const WEEK_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

// any picture -> JPEG in base64 (the server only takes JPEG, at most 4 MB)
function pictureToJpegBase64(file) {
  return new Promise(function (resolve, reject) {
    const reader = new FileReader();
    reader.onload = function () {
      const img = new Image();
      img.onload = function () {
        // not wider than 1280 px, so the file stays small
        let w = img.width;
        let h = img.height;
        if (w > 1280) {
          h = Math.round((h * 1280) / w);
          w = 1280;
        }
        const canvas = document.createElement("canvas");
        canvas.width = w;
        canvas.height = h;
        canvas.getContext("2d").drawImage(img, 0, 0, w, h);
        const dataUrl = canvas.toDataURL("image/jpeg", 0.85);
        resolve(dataUrl.split(",")[1]);
      };
      img.onerror = function () {
        reject(new Error("This picture could not be read."));
      };
      img.src = reader.result;
    };
    reader.readAsDataURL(file);
  });
}

export default function VendorEvents(props) {
  const email = props.user.email;
  const [events, setEvents] = useState(null);
  const [demand, setDemand] = useState({});
  const [venues, setVenues] = useState([]);
  const [categories, setCategories] = useState([]);
  // the event being edited, "new" for a new one, or null when the window is closed
  const [editing, setEditing] = useState(null);
  const { message } = App.useApp();

  useEffect(function () {
    load();
  }, []);

  async function load() {
    const r = await getEventsByVendor(email);
    const list = r.success ? r.events : [];
    setEvents(list);
    const v = await getVenuesByVendor(email);
    if (v.success) setVenues(v.venues);
    const c = await getVendorCategories(email);
    if (c.success) setCategories(c.categories);
    const d = {};
    for (let i = 0; i < list.length; i++) {
      const dr = await getEventDemand(list[i].id);
      if (dr.success) d[list[i].id] = dr;
    }
    setDemand(d);
  }

  async function remove(ev) {
    const r = await deleteEvent(ev.id);
    if (r.success) {
      message.success("Event deleted. Upcoming bookings were cancelled with a full refund.");
      load();
    } else {
      message.error(r.message);
    }
  }

  if (events === null) {
    return <Skeleton active paragraph={{ rows: 6 }} />;
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>My events</Typography.Title>
        <Button type="primary" icon={<Plus size={14} />} onClick={() => setEditing("new")}>New event</Button>
      </Space>

      {events.length === 0 ? <Empty description="You have no events yet" /> : null}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 16 }}>
        {events.map(function (ev, index) {
          const d = demand[ev.id];
          return (
            <StaggerItem key={ev.id} index={index}>
              <Card
                cover={<EventPicture eventId={ev.id} category={ev.category} />}
                actions={[
                  <Button type="text" key="e" icon={<Pencil size={14} />} onClick={() => setEditing(ev)}>Edit</Button>,
                  <Popconfirm
                    key="d"
                    title="Delete this event?"
                    description="Upcoming bookings are cancelled with a full refund and their tickets stop working."
                    okText="Delete"
                    okButtonProps={{ danger: true }}
                    onConfirm={() => remove(ev)}
                  >
                    <Button type="text" danger icon={<Trash2 size={14} />}>Delete</Button>
                  </Popconfirm>,
                ]}
              >
                <Space>
                  <Tag color="blue">{ev.category}</Tag>
                  <Typography.Text strong>{formatMoney(priceToNumber(ev.price), "AED")}</Typography.Text>
                </Space>
                <Typography.Title level={5} style={{ margin: "8px 0 2px" }}>{ev.title}</Typography.Title>
                <Typography.Text type="secondary" style={{ fontSize: 13 }}>
                  {ev.venue_name} | {scheduleText(ev)} at {ev.recur_time} | {ev.capacity} guests per day
                </Typography.Text>
                {d ? (
                  <div style={{ marginTop: 8 }}>
                    <Typography.Text type="secondary" style={{ fontSize: 13 }}>
                      Upcoming: {d.bookings} booking(s), {d.guests} guest(s)
                    </Typography.Text>
                  </div>
                ) : null}
              </Card>
            </StaggerItem>
          );
        })}
      </div>

      <EventForm
        editing={editing}
        email={email}
        venues={venues}
        categories={categories}
        onClose={() => setEditing(null)}
        onSaved={function () {
          setEditing(null);
          load();
        }}
        goToVenues={() => props.setPage("venues")}
      />
    </div>
  );
}

function EventForm(props) {
  const [form] = Form.useForm();
  const kind = Form.useWatch("is_recurring", form);
  const [picture, setPicture] = useState(null);
  const [removePicture, setRemovePicture] = useState(false);
  const [busy, setBusy] = useState(false);
  const { message } = App.useApp();
  const ev = props.editing && props.editing !== "new" ? props.editing : null;

  // fill the form when the window opens
  useEffect(
    function () {
      if (!props.editing) return;
      setPicture(null);
      setRemovePicture(false);
      if (ev) {
        const days = [];
        const parts = (ev.recur_day || "").split(",");
        for (let i = 0; i < parts.length; i++) {
          if (WEEK_DAYS.indexOf(parts[i].trim()) !== -1) days.push(parts[i].trim());
        }
        form.setFieldsValue({
          title: ev.title, category: ev.category, price: priceToNumber(ev.price), description: ev.desc,
          venue_id: ev.venue_id, capacity: ev.capacity, is_recurring: ev.is_recurring,
          date: dayjs(ev.event_datetime.slice(0, 10)), time: dayjs(ev.recur_time, "HH:mm"), days: days,
        });
      } else {
        form.resetFields();
        form.setFieldsValue({ is_recurring: "One-Time", capacity: 20, time: dayjs("18:00", "HH:mm") });
      }
    },
    [props.editing]
  );

  async function choosePicture(file) {
    try {
      const b64 = await pictureToJpegBase64(file);
      setPicture({ name: file.name, b64: b64 });
      setRemovePicture(false);
    } catch (err) {
      message.error(err.message);
    }
    // false: do not let Ant Design upload it, we send it with the form
    return false;
  }

  async function save(values) {
    const time = values.time.format("HH:mm");
    let recurDay = "N/A";
    let date = values.date;
    if (values.is_recurring === "Recurring") {
      // the days in week order, joined like "Tuesday, Thursday"
      const chosen = [];
      for (let i = 0; i < WEEK_DAYS.length; i++) {
        if (values.days.indexOf(WEEK_DAYS[i]) !== -1) chosen.push(WEEK_DAYS[i]);
      }
      recurDay = chosen.join(", ");
      if (!date) date = dayjs();
    }
    const data = {
      title: values.title.trim(),
      category: values.category,
      price: values.price + " AED",
      description: values.description.trim(),
      vendor_email: props.email,
      venue_id: values.venue_id,
      event_datetime: date.format("YYYY-MM-DD") + " " + time,
      is_recurring: values.is_recurring,
      recur_day: recurDay,
      recur_time: time,
      capacity: values.capacity,
    };
    if (picture) data.image_b64 = picture.b64;
    if (removePicture) data.remove_image = true;

    setBusy(true);
    let r;
    if (ev) {
      r = await updateEvent(ev.id, data);
    } else {
      r = await createEvent(data);
    }
    setBusy(false);
    if (r.success) {
      message.success(ev ? "Event updated" : "Event created");
      props.onSaved();
    } else {
      message.error(r.message || "The event could not be saved.");
    }
  }

  return (
    <Modal
      open={props.editing !== null}
      title={ev ? "Edit event" : "New event"}
      okText="Save"
      onOk={() => form.submit()}
      confirmLoading={busy}
      onCancel={props.onClose}
      width={640}
      destroyOnHidden
    >
      {props.venues.length === 0 ? (
        <Typography.Paragraph type="warning">
          You need a venue first. <a onClick={props.goToVenues}>Add a venue</a>
        </Typography.Paragraph>
      ) : null}
      <Form form={form} layout="vertical" onFinish={save} requiredMark={false} preserve={false}>
        <Form.Item label="Title" name="title" rules={[{ required: true, min: 3, message: "At least 3 characters" }]}>
          <Input maxLength={100} />
        </Form.Item>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <Form.Item label="Category" name="category" rules={[{ required: true, message: "Choose a category" }]}>
            <Select options={props.categories.map((c) => ({ value: c.name, label: c.name }))} />
          </Form.Item>
          <Form.Item label="Venue" name="venue_id" rules={[{ required: true, message: "Choose a venue" }]}>
            <Select options={props.venues.map((v) => ({ value: v.id, label: v.name }))} />
          </Form.Item>
          <Form.Item label="Price per guest (AED, before VAT)" name="price" rules={[{ required: true, message: "Enter a price" }]}>
            <InputNumber min={1} max={100000} precision={0} style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item label="Guests per day (1 to 5000)" name="capacity" rules={[{ required: true, message: "Enter the capacity" }]}>
            <InputNumber min={1} max={5000} precision={0} style={{ width: "100%" }} />
          </Form.Item>
        </div>
        <Form.Item label="Description" name="description" rules={[{ required: true, min: 10, message: "At least 10 characters" }]}>
          <Input.TextArea rows={3} maxLength={1000} />
        </Form.Item>
        <Form.Item label="How often" name="is_recurring">
          <Radio.Group options={[{ value: "One-Time", label: "One time" }, { value: "Recurring", label: "Every week" }]} />
        </Form.Item>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          {kind === "Recurring" ? (
            <Form.Item label="Start date" name="date">
              <DatePicker style={{ width: "100%" }} />
            </Form.Item>
          ) : (
            <Form.Item label="Date" name="date" rules={[{ required: true, message: "Choose the date" }]}>
              <DatePicker style={{ width: "100%" }} />
            </Form.Item>
          )}
          <Form.Item label="Start time" name="time" rules={[{ required: true, message: "Choose the time" }]}>
            <TimePicker format="HH:mm" minuteStep={5} style={{ width: "100%" }} />
          </Form.Item>
        </div>
        {kind === "Recurring" ? (
          <Form.Item label="Days" name="days" rules={[{ required: true, message: "Pick at least one day" }]}>
            <Checkbox.Group options={WEEK_DAYS} />
          </Form.Item>
        ) : null}
        <Form.Item label="Picture (optional)">
          <Space>
            <Upload beforeUpload={choosePicture} showUploadList={false} accept="image/*">
              <Button icon={<ImagePlus size={14} />}>Choose picture</Button>
            </Upload>
            <Typography.Text type="secondary">{picture ? picture.name : removePicture ? "Picture will be removed" : ev ? "Current picture kept" : "No picture"}</Typography.Text>
            {ev ? <Button type="link" danger onClick={() => { setPicture(null); setRemovePicture(true); }}>Remove</Button> : null}
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
}
