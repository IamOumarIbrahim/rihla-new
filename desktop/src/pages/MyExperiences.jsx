// my experiences: past trips, with a review of 0 to 5 stars in half steps
import { useEffect, useState } from "react";
import { Card, Rate, Input, Button, Typography, Empty, Skeleton, Space, App } from "antd";
import { submitReview, getMyExperiences } from "../api.js";
import { StaggerItem } from "../components/motion.jsx";
import { EventPicture } from "./Explore.jsx";

export default function MyExperiences(props) {
  const [items, setItems] = useState(null);
  // what the customer typed, per booking id
  const [drafts, setDrafts] = useState({});
  const { message } = App.useApp();

  useEffect(function () {
    load();
  }, []);

  async function load() {
    const r = await getMyExperiences(props.user.email);
    const list = r.success ? r.experiences : [];
    setItems(list);
    const start = {};
    for (let i = 0; i < list.length; i++) {
      start[list[i].id] = { rating: list[i].review_rating || 0, comment: list[i].review_comment || "" };
    }
    setDrafts(start);
  }

  function change(id, field, value) {
    const copy = Object.assign({}, drafts);
    copy[id] = Object.assign({}, copy[id]);
    copy[id][field] = value;
    setDrafts(copy);
  }

  async function save(item) {
    const d = drafts[item.id];
    const r = await submitReview(props.user.email, item.id, d.rating, d.comment);
    if (r.success) {
      message.success("Thank you, your review is saved");
      load();
    } else {
      message.error(r.message);
    }
  }

  if (items === null) {
    return <Skeleton active paragraph={{ rows: 6 }} />;
  }
  if (items.length === 0) {
    return <Empty description="Your past trips show up here, so you can review them" />;
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(360px, 1fr))", gap: 16 }}>
      {items.map(function (item, index) {
        const d = drafts[item.id] || { rating: 0, comment: "" };
        return (
          <StaggerItem key={item.id} index={index}>
            <Card cover={<EventPicture eventId={item.event_id} category={item.event_title} />}>
              <Typography.Title level={5} style={{ marginTop: 0 }}>{item.event_title}</Typography.Title>
              <Typography.Text type="secondary">{item.booking_date} | {item.venue_name} | {item.guests} guest(s)</Typography.Text>
              <div style={{ marginTop: 12 }}>
                <Rate allowHalf value={d.rating} onChange={(v) => change(item.id, "rating", v)} />
              </div>
              <Input.TextArea
                rows={2}
                maxLength={500}
                placeholder="How was it?"
                value={d.comment}
                onChange={(e) => change(item.id, "comment", e.target.value)}
                style={{ marginTop: 8 }}
              />
              <Space style={{ marginTop: 8 }}>
                <Button type="primary" onClick={() => save(item)}>
                  {item.review_rating !== null && item.review_rating !== undefined ? "Update review" : "Save review"}
                </Button>
              </Space>
            </Card>
          </StaggerItem>
        );
      })}
    </div>
  );
}
