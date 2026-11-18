// admin: reports sent by users, open ones first, resolve with a short note
import { useEffect, useState } from "react";
import { Card, List, Tag, Button, Modal, Input, Segmented, Space, Typography, App } from "antd";
import { getReports, resolveReport } from "../api.js";

export default function AdminReports(props) {
  const [reports, setReports] = useState([]);
  const [filter, setFilter] = useState("Open");
  const [resolving, setResolving] = useState(null);
  const [note, setNote] = useState("");
  const { message } = App.useApp();

  useEffect(function () {
    load();
  }, []);

  async function load() {
    const r = await getReports(props.user.email);
    if (r.success) setReports(r.reports);
  }

  async function resolve() {
    const r = await resolveReport(props.user.email, resolving.id, note.trim() || "Resolved");
    if (r.success) {
      message.success("Report resolved");
      setResolving(null);
      setNote("");
      load();
    } else {
      message.error(r.message);
    }
  }

  const shown = [];
  for (let i = 0; i < reports.length; i++) {
    if (filter === "All" || reports[i].status === filter) shown.push(reports[i]);
  }

  return (
    <div>
      <Segmented options={["Open", "Resolved", "All"]} value={filter} onChange={setFilter} style={{ marginBottom: 16 }} />
      <Card>
        <List
          dataSource={shown}
          locale={{ emptyText: "No reports here" }}
          renderItem={function (r, index) {
            return (
              <div>
                <List.Item
                  actions={r.status === "Open" ? [<Button key="r" type="primary" size="small" onClick={() => setResolving(r)}>Resolve</Button>] : []}
                >
                  <List.Item.Meta
                    title={
                      <Space>
                        {r.subject}
                        <Tag color={r.status === "Open" ? "orange" : "green"}>{r.status}</Tag>
                        <Tag>{r.category}</Tag>
                      </Space>
                    }
                    description={
                      <span>
                        From {r.reporter_email} ({r.reporter_role}) about {r.offender_type}
                        {r.offender_email ? " " + r.offender_email : ""} | {r.created_at}
                        <br />
                        <Typography.Text>{r.description}</Typography.Text>
                        {r.resolution ? <><br />Resolution: {r.resolution} ({r.resolved_by})</> : null}
                      </span>
                    }
                  />
                </List.Item>
              </div>
            );
          }}
        />
      </Card>
      <Modal open={resolving !== null} title="Resolve report" okText="Resolve" onOk={resolve} onCancel={() => setResolving(null)}>
        <Input.TextArea rows={3} maxLength={300} placeholder="What was done (optional)" value={note} onChange={(e) => setNote(e.target.value)} />
      </Modal>
    </div>
  );
}
