// settings: change password, choose the currency prices are shown in,
// and for staff: change the venue they work at
import { useEffect, useState } from "react";
import { Card, Form, Input, Select, Button, Space, Typography, App } from "antd";
import { login, updatePassword, getCurrency, setCurrency, getAllVenues, getStaffVenue, setStaffVenue } from "../api.js";
import { CURRENCIES } from "../money.js";

export default function Settings(props) {
  const email = props.user.email;
  const isStaff = props.user.role === "Staff";
  const [currency, setCurrencyValue] = useState("AED");
  const [venues, setVenues] = useState([]);
  const [venueForm] = Form.useForm();
  const [passwordForm] = Form.useForm();
  const { message } = App.useApp();

  useEffect(function () {
    load();
  }, []);

  async function load() {
    const c = await getCurrency(email);
    if (c.success) setCurrencyValue(c.currency);
    if (isStaff) {
      const v = await getAllVenues();
      if (v.success) setVenues(v.venues);
      const mine = await getStaffVenue(email);
      if (mine.success) venueForm.setFieldsValue({ venue_id: mine.venue.id, manager_email: mine.venue.manager_email });
    }
  }

  async function changePassword(values) {
    // the old password has to be right first
    const check = await login(email, values.current);
    if (!check.success) {
      message.error("Your current password is not right.");
      return;
    }
    const r = await updatePassword(email, values.password);
    if (r.success) {
      message.success("Password changed");
      passwordForm.resetFields();
    } else {
      message.error(r.message);
    }
  }

  async function changeCurrency(value) {
    const r = await setCurrency(email, value);
    if (r.success) {
      setCurrencyValue(value);
      message.success("Prices are now shown in " + value);
    } else {
      message.error(r.message);
    }
  }

  async function changeVenue(values) {
    const r = await setStaffVenue(email, values.venue_id, values.manager_email);
    if (r.success) {
      message.success("Your venue is updated. Check-in and the schedule follow it.");
    } else {
      message.error(r.message);
    }
  }

  return (
    <Space direction="vertical" size={16} style={{ width: "100%", maxWidth: 640 }}>
      <Card title="Currency">
        <Space>
          <Typography.Text>Show prices in</Typography.Text>
          <Select value={currency} onChange={changeCurrency} style={{ width: 120 }} options={CURRENCIES.map((c) => ({ value: c, label: c }))} />
        </Space>
        <Typography.Paragraph type="secondary" style={{ marginTop: 8, marginBottom: 0, fontSize: 12 }}>
          Payments are always charged in AED. Other currencies use fixed rates and are only for showing.
        </Typography.Paragraph>
      </Card>

      <Card title="Password">
        <Form form={passwordForm} layout="vertical" onFinish={changePassword} requiredMark={false}>
          <Form.Item label="Current password" name="current" rules={[{ required: true, message: "Enter your current password" }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item label="New password" name="password" rules={[{ required: true, message: "Choose a password" }, { min: 8, message: "At least 8 characters" }]}>
            <Input.Password />
          </Form.Item>
          <Button type="primary" htmlType="submit">Change password</Button>
        </Form>
      </Card>

      {isStaff ? (
        <Card title="Your venue">
          <Form form={venueForm} layout="vertical" onFinish={changeVenue} requiredMark={false}>
            <Form.Item label="Venue" name="venue_id" rules={[{ required: true }]}>
              <Select options={venues.map((v) => ({ value: v.id, label: v.name + ", " + v.address }))} />
            </Form.Item>
            <Form.Item label="Manager's email" name="manager_email" rules={[{ required: true, message: "Enter your manager's email" }]}>
              <Input />
            </Form.Item>
            <Button type="primary" htmlType="submit">Save venue</Button>
          </Form>
        </Card>
      ) : null}
    </Space>
  );
}
