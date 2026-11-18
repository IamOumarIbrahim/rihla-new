// admin: every account, with ban and restore
// a banned account cannot sign in or book, admins cannot be banned
import { useEffect, useState } from "react";
import { Card, Table, Tag, Button, Statistic, Space, Input, Popconfirm, App } from "antd";
import { Search } from "pulsoicon-react";
import { getAllUsers, setUserBanned } from "../api.js";

export default function AdminUsers(props) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const { message } = App.useApp();

  useEffect(function () {
    load();
  }, []);

  async function load() {
    setLoading(true);
    const r = await getAllUsers(props.user.email);
    setUsers(r.success ? r.users : []);
    setLoading(false);
  }

  async function setBanned(u, banned) {
    const r = await setUserBanned(props.user.email, u.email, banned);
    if (r.success) {
      message.success(banned ? u.email + " is banned" : u.email + " is restored");
      load();
    } else {
      message.error(r.message);
    }
  }

  let banned = 0;
  for (let i = 0; i < users.length; i++) {
    if (users[i].banned) banned = banned + 1;
  }
  let bannedPercent = 0;
  if (users.length > 0) bannedPercent = Math.round((banned / users.length) * 100);

  const shown = [];
  for (let i = 0; i < users.length; i++) {
    const text = (users[i].email + " " + users[i].role + " " + users[i].venue_name).toLowerCase();
    if (!search || text.indexOf(search.toLowerCase()) !== -1) shown.push(users[i]);
  }

  // one filter button per role in the role column
  const roles = [];
  for (let i = 0; i < users.length; i++) {
    if (roles.indexOf(users[i].role) === -1) roles.push(users[i].role);
  }

  const columns = [
    { title: "Email", dataIndex: "email", key: "email" },
    {
      title: "Role", dataIndex: "role", key: "role",
      filters: roles.map((r) => ({ text: r, value: r })),
      onFilter: (value, u) => u.role === value,
    },
    { title: "Signed up", dataIndex: "created_at", key: "created_at", sorter: (a, b) => (a.created_at < b.created_at ? -1 : 1) },
    { title: "Venue", dataIndex: "venue_name", key: "venue_name" },
    { title: "Manager", dataIndex: "manager_email", key: "manager_email" },
    { title: "Status", key: "status", render: (u) => (u.banned ? <Tag color="red">Banned</Tag> : <Tag color="green">Active</Tag>) },
    {
      title: "",
      key: "actions",
      render: function (u) {
        if (u.role === "Admin") return null;
        if (u.banned) {
          return <Button size="small" onClick={() => setBanned(u, false)}>Restore</Button>;
        }
        return (
          <Popconfirm title={"Ban " + u.email + "?"} description="They will not be able to sign in or book." okText="Ban" okButtonProps={{ danger: true }} onConfirm={() => setBanned(u, true)}>
            <Button size="small" danger>Ban</Button>
          </Popconfirm>
        );
      },
    },
  ];

  return (
    <Space direction="vertical" size={16} style={{ width: "100%" }}>
      <Space size={16}>
        <Card size="small"><Statistic title="Accounts" value={users.length} /></Card>
        <Card size="small"><Statistic title="Active" value={users.length - banned} /></Card>
        <Card size="small"><Statistic title="Banned" value={bannedPercent} suffix="%" /></Card>
      </Space>
      <Input prefix={<Search size={16} />} placeholder="Search email, role or venue" value={search} onChange={(e) => setSearch(e.target.value)} allowClear style={{ maxWidth: 420 }} />
      <Table rowKey="email" columns={columns} dataSource={shown} loading={loading} pagination={{ pageSize: 12 }} />
    </Space>
  );
}
