// staff: open customer questions about events at my venue
import { useEffect, useState } from "react";
import { Card, List, Button, Typography, Empty, App } from "antd";
import { CircleCheck } from "pulsoicon-react";
import { getOpenSupportTickets, resolveSupportTicket } from "../api.js";

export default function StaffSupport(props) {
  const [tickets, setTickets] = useState(null);
  const { message } = App.useApp();

  useEffect(function () {
    load();
  }, []);

  async function load() {
    const r = await getOpenSupportTickets(props.user.email);
    setTickets(r.success ? r.tickets : []);
  }

  async function resolve(t) {
    const r = await resolveSupportTicket(t.id, props.user.email);
    if (r.success) {
      message.success("Marked as resolved");
      load();
    } else {
      message.error(r.message);
    }
  }

  if (tickets !== null && tickets.length === 0) {
    return <Empty description="No open questions for your venue" />;
  }

  return (
    <Card title="Open questions for your venue">
      <List
        loading={tickets === null}
        dataSource={tickets || []}
        renderItem={function (t, index) {
          return (
            <div>
              <List.Item actions={[<Button key="r" icon={<CircleCheck size={14} />} onClick={() => resolve(t)}>Resolve</Button>]}>
                <List.Item.Meta
                  title={t.subject}
                  description={
                    <span>
                      {t.customer_email} | {t.event_title || "General"} | {t.created_at}
                      <br />
                      <Typography.Text>{t.message}</Typography.Text>
                    </span>
                  }
                />
              </List.Item>
            </div>
          );
        }}
      />
    </Card>
  );
}
