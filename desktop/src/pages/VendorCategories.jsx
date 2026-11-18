// vendor: the categories my events can use (like Evening Safari)
import { useEffect, useState } from "react";
import { Card, Input, Button, Tag, Space, Typography, App } from "antd";
import { Plus } from "pulsoicon-react";
import { getVendorCategories, addVendorCategory, deleteVendorCategory } from "../api.js";

export default function VendorCategories(props) {
  const email = props.user.email;
  const [categories, setCategories] = useState([]);
  const [name, setName] = useState("");
  const { message } = App.useApp();

  useEffect(function () {
    load();
  }, []);

  async function load() {
    const r = await getVendorCategories(email);
    if (r.success) setCategories(r.categories);
  }

  async function add() {
    if (name.trim().length < 2) {
      message.error("Please enter a category name.");
      return;
    }
    const r = await addVendorCategory(email, name.trim());
    if (r.success) {
      setName("");
      load();
    } else {
      message.error("You already have a category with this name.");
    }
  }

  async function remove(c) {
    await deleteVendorCategory(c.id);
    load();
  }

  return (
    <Card title="Categories" style={{ maxWidth: 720 }}>
      <Space.Compact style={{ width: "100%", marginBottom: 16 }}>
        <Input value={name} onChange={(e) => setName(e.target.value)} onPressEnter={add} placeholder="New category, like Dhow Cruise" />
        <Button type="primary" icon={<Plus size={14} />} onClick={add}>Add</Button>
      </Space.Compact>
      {categories.length === 0 ? <Typography.Text type="secondary">No categories yet</Typography.Text> : null}
      <Space wrap>
        {categories.map(function (c) {
          return (
            <Tag key={c.id} closable onClose={(e) => { e.preventDefault(); remove(c); }} style={{ padding: "4px 10px", fontSize: 14 }}>
              {c.name}
            </Tag>
          );
        })}
      </Space>
    </Card>
  );
}
