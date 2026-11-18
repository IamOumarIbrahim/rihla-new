// forgot password: email, then the 6-digit code (000000 in the demo), then a new password
import { useState } from "react";
import { Card, Form, Input, Button, Typography, Steps, App } from "antd";
import { ArrowLeft } from "pulsoicon-react";
import { emailExists, updatePassword } from "../api.js";
import { PageEnter } from "../components/motion.jsx";

export default function ForgotPassword(props) {
  const [step, setStep] = useState(0);
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const { message } = App.useApp();

  async function sendCode(values) {
    const r = await emailExists(values.email.trim());
    if (!r.exists) {
      message.error("There is no account with this email.");
      return;
    }
    setEmail(values.email.trim());
    setStep(1);
  }

  function checkCode() {
    if (code !== "000000") {
      message.error("Wrong code. In the demo the code is 000000.");
      return;
    }
    setStep(2);
  }

  async function savePassword(values) {
    setBusy(true);
    const r = await updatePassword(email, values.password);
    setBusy(false);
    if (r.success) {
      message.success("Password changed. Please sign in.");
      props.onBack();
    } else {
      message.error(r.message || "The password could not be changed.");
    }
  }

  return (
    <div style={{ minHeight: "100vh", background: "#f5f5f5", display: "flex", justifyContent: "center", padding: "60px 16px" }}>
      <PageEnter style={{ width: 480 }}>
        <Button type="link" icon={<ArrowLeft size={16} />} onClick={props.onBack} style={{ padding: 0 }}>
          Back to sign in
        </Button>
        <Card style={{ marginTop: 12 }}>
          <Typography.Title level={3} style={{ marginTop: 0 }}>Reset your password</Typography.Title>
          <Steps current={step} size="small" style={{ margin: "16px 0 24px" }} items={[{ title: "Email" }, { title: "Code" }, { title: "New password" }]} />

          {step === 0 ? (
            <Form layout="vertical" onFinish={sendCode} requiredMark={false}>
              <Form.Item label="Email" name="email" rules={[{ required: true, message: "Enter your email" }]}>
                <Input />
              </Form.Item>
              <Button type="primary" htmlType="submit" block>Send code</Button>
            </Form>
          ) : null}

          {step === 1 ? (
            <PageEnter key="code">
              <Typography.Paragraph type="secondary">Enter the 6-digit code sent to {email}. In the demo it is 000000.</Typography.Paragraph>
              <Input.OTP length={6} value={code} onChange={setCode} />
              <Button type="primary" block style={{ marginTop: 16 }} onClick={checkCode}>Verify code</Button>
            </PageEnter>
          ) : null}

          {step === 2 ? (
            <PageEnter key="new">
              <Form layout="vertical" onFinish={savePassword} requiredMark={false}>
                <Form.Item label="New password" name="password" rules={[{ required: true, message: "Choose a password" }, { min: 8, message: "At least 8 characters" }]}>
                  <Input.Password />
                </Form.Item>
                <Button type="primary" htmlType="submit" block loading={busy}>Save new password</Button>
              </Form>
            </PageEnter>
          ) : null}
        </Card>
      </PageEnter>
    </div>
  );
}
