// vendor: my venues (name, address and a Google Maps link)
// a venue cannot be deleted while it has events or staff
import { useEffect, useState } from "react";
import { Card, Form, Input, Button, Table, Popconfirm, Modal, Space, App } from "antd";
import { Plus, MapPin } from "pulsoicon-react";
import { getVenuesByVendor, createVenue, updateVenueMapsUrl, deleteVenue } from "../api.js";

export default function VendorVenues(props) {
  const email = props.user.email;
  const [venues, setVenues] = useState([]);
  const [editing, setEditing] = useState(null);
  const [link, setLink] = useState("");
  const [form] = Form.useForm();
  const { message } = App.useApp();

  useEffect(function () {
    load();
  }, []);

  async function load() {
    const r = await getVenuesByVendor(email);
    if (r.success) setVenues(r.venues);
  }

  async function add(values) {
    const r = await createVenue(values.name.trim(), values.address.trim(), email, (values.maps_url || "").trim());
    if (r.success) {
      message.success("Venue added");
      form.resetFields();
      load();
    } else {
      message.error(r.message);
    }
  }

  async function saveLink() {
    const r = await updateVenueMapsUrl(editing.id, email, link.trim());
    if (r.success) {
      message.success("Map link saved");
      setEditing(null);
      load();
    } else {
      message.error(r.message);
    }
  }

  async function remove(v) {
    const r = await deleteVenue(v.id);
    if (r.success) {
      message.success("Venue deleted");
      load();
    } else {
      message.error(r.message);
    }
  }

  const columns = [
    { title: "Venue", dataIndex: "name", key: "name" },
    { title: "Address", dataIndex: "address", key: "address" },
    {
      title: "Map",
      key: "map",
      render: (v) => (v.maps_url ? <a href={v.maps_url} target="_blank" rel="noreferrer">Open map</a> : "No link"),
    },
    {
      title: "",
      key: "actions",
      render: function (v) {
        return (
          <Space>
            <Button size="small" icon={<MapPin size={14} />} onClick={() => { setEditing(v); setLink(v.maps_url || ""); }}>Map link</Button>
            <Popconfirm title="Delete this venue?" okText="Delete" okButtonProps={{ danger: true }} onConfirm={() => remove(v)}>
              <Button size="small" danger>Delete</Button>
            </Popconfirm>
          </Space>
        );
      },
    },
  ];

  return (
    <Space direction="vertical" size={16} style={{ width: "100%" }}>
      <Card title="Add a venue">
        <Form form={form} layout="inline" onFinish={add} requiredMark={false}>
          <Form.Item name="name" rules={[{ required: true, min: 2, message: "Name" }]}>
            <Input placeholder="Venue name" style={{ width: 220 }} />
          </Form.Item>
          <Form.Item name="address" rules={[{ required: true, min: 3, message: "Address" }]}>
            <Input placeholder="Address" style={{ width: 260 }} />
          </Form.Item>
          <Form.Item name="maps_url">
            <Input placeholder="Google Maps link (optional)" style={{ width: 300 }} />
          </Form.Item>
          <Button type="primary" htmlType="submit" icon={<Plus size={14} />}>Add venue</Button>
        </Form>
      </Card>
      <Table rowKey="id" columns={columns} dataSource={venues} pagination={false} />

      <Modal open={editing !== null} title="Map link" okText="Save" onOk={saveLink} onCancel={() => setEditing(null)}>
        <Input value={link} onChange={(e) => setLink(e.target.value)} placeholder="https://maps.app.goo.gl/..." />
      </Modal>
    </Space>
  );
}
