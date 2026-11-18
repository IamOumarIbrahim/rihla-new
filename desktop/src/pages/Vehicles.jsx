// dispatcher: my vehicles (add, change status, free from an event, delete)
import { useEffect, useState } from "react";
import { Card, Form, Input, Select, Switch, Button, Table, Tag, Popconfirm, Space, App } from "antd";
import { Plus } from "pulsoicon-react";
import { getAllVehicles, getVehicleTypes, createVehicle, updateVehicleStatus, freeVehicle, deleteVehicle } from "../api.js";

const STATUSES = ["Available", "Maintenance", "Out of service"];
const STATUS_COLOR = { Available: "green", Assigned: "blue", Maintenance: "orange", "Out of service": "default" };

export default function Vehicles(props) {
  const email = props.user.email;
  const [vehicles, setVehicles] = useState([]);
  const [types, setTypes] = useState([]);
  const [form] = Form.useForm();
  const { message } = App.useApp();

  useEffect(function () {
    load();
  }, []);

  async function load() {
    const r = await getAllVehicles(email);
    if (r.success) setVehicles(r.vehicles);
    const t = await getVehicleTypes();
    if (t.success) setTypes(t.vehicle_types);
  }

  async function add(values) {
    const r = await createVehicle({
      license_number: values.license_number.trim(),
      vehicle_type: values.vehicle_type,
      location: values.location.trim(),
      dispatcher_email: email,
      auto_reassign_recurring: values.auto ? 1 : 0,
    });
    if (r.success) {
      message.success("Vehicle added");
      form.resetFields();
      load();
    } else {
      message.error(r.message);
    }
  }

  async function changeStatus(v, status) {
    await updateVehicleStatus(v.id, status);
    load();
  }

  async function free(v) {
    await freeVehicle(v.id);
    message.success("Vehicle is available again");
    load();
  }

  async function remove(v) {
    await deleteVehicle(v.id);
    load();
  }

  const columns = [
    { title: "License", dataIndex: "license_number", key: "license_number" },
    { title: "Type", dataIndex: "vehicle_type", key: "vehicle_type" },
    { title: "Seats", dataIndex: "capacity", key: "capacity", align: "right" },
    { title: "Location", dataIndex: "location", key: "location" },
    { title: "Status", dataIndex: "status", key: "status", render: (s) => <Tag color={STATUS_COLOR[s] || "default"}>{s}</Tag> },
    { title: "Repeats weekly", key: "auto", render: (v) => (v.auto_reassign_recurring ? "Yes" : "No") },
    {
      title: "",
      key: "actions",
      render: function (v) {
        return (
          <Space>
            {v.status === "Assigned" ? (
              <Button size="small" onClick={() => free(v)}>Free</Button>
            ) : (
              <Select size="small" value={v.status} style={{ width: 140 }} onChange={(s) => changeStatus(v, s)} options={STATUSES.map((s) => ({ value: s, label: s }))} />
            )}
            <Popconfirm title="Delete this vehicle?" okText="Delete" okButtonProps={{ danger: true }} onConfirm={() => remove(v)}>
              <Button size="small" danger>Delete</Button>
            </Popconfirm>
          </Space>
        );
      },
    },
  ];

  return (
    <Space direction="vertical" size={16} style={{ width: "100%" }}>
      <Card title="Add a vehicle">
        <Form form={form} layout="inline" onFinish={add} requiredMark={false} initialValues={{ auto: false }}>
          <Form.Item name="license_number" rules={[{ required: true, message: "License" }]}>
            <Input placeholder="License number" style={{ width: 160 }} />
          </Form.Item>
          <Form.Item name="vehicle_type" rules={[{ required: true, message: "Type" }]}>
            <Select placeholder="Type" style={{ width: 240 }} options={types.map((t) => ({ value: t.name, label: t.name + " (" + t.capacity + " seats)" }))} />
          </Form.Item>
          <Form.Item name="location" rules={[{ required: true, message: "Location" }]}>
            <Input placeholder="Where it is parked" style={{ width: 220 }} />
          </Form.Item>
          <Form.Item name="auto" label="Repeats weekly" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Button type="primary" htmlType="submit" icon={<Plus size={14} />}>Add</Button>
        </Form>
      </Card>
      <Table rowKey="id" columns={columns} dataSource={vehicles} pagination={{ pageSize: 10 }} />
    </Space>
  );
}
