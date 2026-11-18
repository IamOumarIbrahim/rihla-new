// report a problem to the admin team, the choices depend on the role (same as src/welcome/report_view.py)
import { Card, Form, Input, Select, Button, Typography, App } from "antd";
import { Flag } from "pulsoicon-react";
import { createReport } from "../api.js";

// for every role: [subtitle, what you can report, who it is about, hint for the details box]
const REPORT_OPTIONS = {
  Customer: [
    "Something went wrong on an experience or booking? Tell the admin team.",
    ["Rude or unprofessional behaviour", "Safety concern", "Scam or fraud", "Experience not as described", "Payment or refund problem", "Other"],
    ["Staff member", "Vendor (event organiser)", "OTA partner", "Driver / dispatcher", "Another customer", "Other / not sure"],
    "Which event and date was it, what happened, and your booking or ticket code if you have it.",
  ],
  Vendor: [
    "Report a problem with a customer, partner or the Rihla team.",
    ["Customer misconduct", "Fraudulent or fake booking", "Partner booking problem", "Staff problem", "Transport problem", "Other"],
    ["Customer", "OTA partner", "Staff member", "Driver / dispatcher", "Other"],
    "Which event and date, who was involved, and the booking or ticket code if relevant.",
  ],
  Staff: [
    "Report an incident from check-in, an event, or a support case.",
    ["Customer misconduct", "Fake or reused ticket", "Vendor problem", "Safety concern", "Abusive support message", "Other"],
    ["Customer", "Vendor", "OTA partner", "Driver / dispatcher", "Other"],
    "Where and when it happened, the ticket code if scanned, and what you saw.",
  ],
  Partner: [
    "Report a problem with a booking you made for your clients.",
    ["Booking or payment problem", "Experience not as described", "Vendor problem", "Unprofessional behaviour", "Client safety concern", "Other"],
    ["Vendor", "Staff member", "Driver / dispatcher", "Customer", "Other"],
    "Which booking, event and date, your client's name, and what went wrong.",
  ],
  Dispatcher: [
    "Report a problem with vehicles, schedules or people at an event.",
    ["Vehicle misuse or damage", "Unsafe behaviour", "Vendor schedule problem", "Customer misconduct", "Other"],
    ["Vendor", "Staff member", "Customer", "OTA partner", "Other"],
    "Which vehicle (license number), event and date, and what happened.",
  ],
};

export default function Report(props) {
  const [form] = Form.useForm();
  const { message } = App.useApp();
  let options = REPORT_OPTIONS[props.user.role];
  if (!options) {
    options = REPORT_OPTIONS.Customer;
  }

  async function send(values) {
    const r = await createReport({
      reporter_email: props.user.email,
      category: values.category,
      offender_type: values.offender_type,
      subject: values.subject,
      description: values.description,
      offender_email: values.offender_email || "",
    });
    if (r.success) {
      message.success(r.message || "Report sent to the admin team");
      form.resetFields();
    } else {
      message.error(r.message);
    }
  }

  return (
    <Card style={{ maxWidth: 720 }}>
      <Typography.Title level={4} style={{ marginTop: 0 }}>Report a problem</Typography.Title>
      <Typography.Paragraph type="secondary">{options[0]}</Typography.Paragraph>
      <Form form={form} layout="vertical" onFinish={send} requiredMark={false}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <Form.Item label="What are you reporting?" name="category" rules={[{ required: true, message: "Choose one" }]}>
            <Select options={options[1].map((c) => ({ value: c, label: c }))} />
          </Form.Item>
          <Form.Item label="Who is it about?" name="offender_type" rules={[{ required: true, message: "Choose one" }]}>
            <Select options={options[2].map((c) => ({ value: c, label: c }))} />
          </Form.Item>
        </div>
        <Form.Item label="Their email (if you know it)" name="offender_email">
          <Input placeholder="optional" />
        </Form.Item>
        <Form.Item label="Short summary" name="subject" rules={[{ required: true, min: 3, message: "At least 3 characters" }]}>
          <Input maxLength={120} />
        </Form.Item>
        <Form.Item label="What happened?" name="description" extra={options[3]} rules={[{ required: true, min: 10, message: "At least 10 characters" }]}>
          <Input.TextArea rows={5} maxLength={2000} />
        </Form.Item>
        <Button type="primary" htmlType="submit" icon={<Flag size={14} />}>Send report</Button>
      </Form>
    </Card>
  );
}
