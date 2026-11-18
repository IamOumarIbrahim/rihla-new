// sign in screen: picture on the left, form on the right, one button per demo account
import { useState } from "react";
import { Form, Input, Button, Typography, Divider, App } from "antd";
import { LogIn } from "pulsoicon-react";
import { motion } from "motion/react";
import { login } from "../api.js";
import { Shake } from "../components/motion.jsx";
import loginPhoto from "../images/login-bg.jpg";
import logoPicture from "../images/logo.png";

// same accounts as server/config.py
const DEMO_ACCOUNTS = [
  ["Customer", "customer@email.com", "customer1234"],
  ["Vendor", "vendor@email.com", "vendor1234"],
  ["Staff", "staff@email.com", "staff1234"],
  ["Partner", "partner@email.com", "partner1234"],
  ["Dispatcher", "dispatcher@email.com", "dispatcher1234"],
  ["Admin", "admin@email.com", "admin1234"],
];

export default function Login(props) {
  const [form] = Form.useForm();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [shakeCount, setShakeCount] = useState(0);
  const { message } = App.useApp();

  async function signIn(values) {
    setBusy(true);
    setError("");
    const result = await login(values.email.trim(), values.password);
    setBusy(false);
    if (result.success) {
      message.success("Signed in as " + result.role);
      props.onSignIn(result.email, result.role);
    } else {
      setError(result.message || "Invalid email or password.");
      setShakeCount(shakeCount + 1);
    }
  }

  function fillDemo(email, password) {
    form.setFieldsValue({ email: email, password: password });
    setError("");
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", height: "100vh", background: "#fff" }}>
      <div style={{ position: "relative", overflow: "hidden" }}>
        <img src={loginPhoto} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        <img src={logoPicture} alt="Rihla" style={{ position: "absolute", top: "12%", left: "50%", transform: "translateX(-50%)", width: 300 }} />
      </div>

      <div style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: "spring", duration: 0.35, bounce: 0 }}
          style={{ width: 400 }}
        >
          <Typography.Title level={3} style={{ marginBottom: 4 }}>Sign in to Rihla</Typography.Title>
          <Typography.Text type="secondary">Book desert and city trips in Dubai</Typography.Text>

          <Form
            form={form}
            layout="vertical"
            onFinish={signIn}
            initialValues={{ email: "customer@email.com", password: "customer1234" }}
            style={{ marginTop: 24 }}
            requiredMark={false}
          >
            <Form.Item label="Email" name="email" rules={[{ required: true, message: "Enter your email" }]}>
              <Input size="large" autoComplete="username" />
            </Form.Item>
            <Form.Item label="Password" name="password" rules={[{ required: true, message: "Enter your password" }]}>
              <Input.Password size="large" autoComplete="current-password" />
            </Form.Item>

            <Shake trigger={shakeCount}>
              {error ? <Typography.Text type="danger">{error}</Typography.Text> : null}
            </Shake>

            <Button type="primary" htmlType="submit" size="large" block loading={busy} icon={<LogIn size={16} />} style={{ marginTop: 8 }}>
              Sign in
            </Button>
          </Form>

          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 12 }}>
            <Button type="link" style={{ padding: 0 }} onClick={props.onCreate}>Create an account</Button>
            <Button type="link" style={{ padding: 0 }} onClick={props.onForgot}>Forgot password?</Button>
          </div>

          <Divider plain>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>Demo accounts</Typography.Text>
          </Divider>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
            {DEMO_ACCOUNTS.map(function (a) {
              return (
                <Button key={a[0]} onClick={() => fillDemo(a[1], a[2])}>
                  {a[0]}
                </Button>
              );
            })}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
