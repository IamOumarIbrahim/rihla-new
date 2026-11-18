// sign up: role, email and phone (both checked with a code), password, SSN for team accounts,
// and for staff the venue they work at and their manager's email
import { useEffect, useState } from "react";
import { Form, Input, Select, Button, Typography, Space, Modal, Progress, App, Card } from "antd";
import { ArrowLeft, MailCheck, Smartphone } from "pulsoicon-react";
import { registerUser, emailExists, phoneExists, getAllVenues } from "../api.js";
import { PageEnter } from "../components/motion.jsx";

const ROLES = ["Customer", "Vendor", "Staff", "Partner", "Dispatcher"];
// the demo sends no real email or sms, the code is always 000000
const DEMO_CODE = "000000";

// how strong a password looks: 0 to 4 points
function passwordScore(pwd) {
  let score = 0;
  let hasUpper = false;
  let hasDigit = false;
  let hasSymbol = false;
  for (let i = 0; i < pwd.length; i++) {
    const c = pwd[i];
    if (c >= "A" && c <= "Z") hasUpper = true;
    if (c >= "0" && c <= "9") hasDigit = true;
    if ("!@#$%^&*()".indexOf(c) !== -1) hasSymbol = true;
  }
  if (pwd.length >= 8) score = score + 1;
  if (hasUpper) score = score + 1;
  if (hasDigit) score = score + 1;
  if (hasSymbol) score = score + 1;
  return score;
}

// 9 digits after +971 (spaces are ok)
function validPhone(value) {
  let digits = "";
  for (let i = 0; i < value.length; i++) {
    if (value[i] !== " ") digits = digits + value[i];
  }
  if (digits.length !== 9) return false;
  for (let i = 0; i < digits.length; i++) {
    if (digits[i] < "0" || digits[i] > "9") return false;
  }
  return true;
}

export default function CreateAccount(props) {
  const [form] = Form.useForm();
  const role = Form.useWatch("role", form) || "Customer";
  const password = Form.useWatch("password", form) || "";
  const [venues, setVenues] = useState([]);
  // which email and phone were checked with the code
  const [verifiedEmail, setVerifiedEmail] = useState("");
  const [verifiedPhone, setVerifiedPhone] = useState("");
  // the code window: what is being checked ("email" or "phone")
  const [codeFor, setCodeFor] = useState("");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const { message } = App.useApp();

  useEffect(function () {
    getAllVenues().then(function (r) {
      if (r.success) setVenues(r.venues);
    });
  }, []);

  async function startEmailCheck() {
    const email = (form.getFieldValue("email") || "").trim().toLowerCase();
    if (email.indexOf("@") < 1 || email.indexOf(".") === -1) {
      message.error("Please enter a valid email address.");
      return;
    }
    const r = await emailExists(email);
    if (r.exists) {
      message.error("This email already has an account. Please sign in.");
      return;
    }
    setCode("");
    setCodeFor("email");
  }

  async function startPhoneCheck() {
    const phone = form.getFieldValue("phone") || "";
    if (!validPhone(phone)) {
      message.error("Enter a valid UAE mobile number (9 digits after +971).");
      return;
    }
    const r = await phoneExists("+971 " + phone.trim());
    if (r.exists) {
      message.error("This phone number is already used.");
      return;
    }
    setCode("");
    setCodeFor("phone");
  }

  function checkCode() {
    if (code !== DEMO_CODE) {
      message.error("Wrong code. In the demo the code is 000000.");
      return;
    }
    if (codeFor === "email") {
      setVerifiedEmail((form.getFieldValue("email") || "").trim().toLowerCase());
      message.success("Email verified");
    } else {
      setVerifiedPhone((form.getFieldValue("phone") || "").trim());
      message.success("Phone verified");
    }
    setCodeFor("");
  }

  async function submit(values) {
    const email = values.email.trim().toLowerCase();
    if (email !== verifiedEmail || values.phone.trim() !== verifiedPhone) {
      message.error("Please verify both your email and your phone first.");
      return;
    }
    const data = {
      email: email,
      password: values.password,
      role: values.role,
      phone: "+971 " + values.phone.trim(),
      ssn: values.ssn || null,
      venue_id: values.venue_id || null,
      manager_email: values.manager_email || null,
    };
    setBusy(true);
    const r = await registerUser(data);
    setBusy(false);
    if (r.success) {
      message.success("Account created. You can sign in now.");
      props.onBack();
    } else {
      message.error(r.message || "The account could not be created.");
    }
  }

  const score = passwordScore(password);
  let strength = "Weak";
  let strengthColor = "#dc2626";
  if (score >= 4) {
    strength = "Strong";
    strengthColor = "#16a34a";
  } else if (score >= 2) {
    strength = "Medium";
    strengthColor = "#d97706";
  }

  const venueOptions = venues.map(function (v) {
    return { value: v.id, label: v.name + ", " + v.address };
  });

  return (
    <div style={{ minHeight: "100vh", background: "#f5f5f5", display: "flex", justifyContent: "center", padding: "40px 16px" }}>
      <PageEnter style={{ width: 560 }}>
        <Button type="link" icon={<ArrowLeft size={16} />} onClick={props.onBack} style={{ padding: 0 }}>
          Back to sign in
        </Button>
        <Card style={{ marginTop: 12 }}>
          <Typography.Title level={3} style={{ marginTop: 0 }}>Create your account</Typography.Title>
          <Form form={form} layout="vertical" onFinish={submit} initialValues={{ role: "Customer", phone: "50 1234567" }} requiredMark={false}>
            <Form.Item label="Account type" name="role">
              <Select options={ROLES.map((r) => ({ value: r, label: r }))} />
            </Form.Item>

            <Form.Item label="Email" required>
              <Space.Compact style={{ width: "100%" }}>
                <Form.Item name="email" noStyle rules={[{ required: true, message: "Enter your email" }]}>
                  <Input placeholder="name@example.com" />
                </Form.Item>
                <Button icon={<MailCheck size={16} />} onClick={startEmailCheck}>
                  {verifiedEmail ? "Verified" : "Verify"}
                </Button>
              </Space.Compact>
            </Form.Item>

            <Form.Item label="Mobile number" required>
              <Space.Compact style={{ width: "100%" }}>
                <Input value="+971" disabled style={{ width: 70 }} />
                <Form.Item name="phone" noStyle rules={[{ required: true, message: "Enter your mobile number" }]}>
                  <Input />
                </Form.Item>
                <Button icon={<Smartphone size={16} />} onClick={startPhoneCheck}>
                  {verifiedPhone ? "Verified" : "Verify"}
                </Button>
              </Space.Compact>
            </Form.Item>

            <Form.Item
              label="Password"
              name="password"
              rules={[
                { required: true, message: "Choose a password" },
                { min: 8, message: "At least 8 characters" },
              ]}
            >
              <Input.Password />
            </Form.Item>
            {password ? (
              <div style={{ marginTop: -16, marginBottom: 16 }}>
                <Progress percent={score * 25} showInfo={false} strokeColor={strengthColor} size="small" />
                <Typography.Text style={{ color: strengthColor, fontSize: 12 }}>{strength} password</Typography.Text>
              </div>
            ) : null}
            <Form.Item
              label="Confirm password"
              name="confirm"
              dependencies={["password"]}
              rules={[
                { required: true, message: "Type the password again" },
                function ({ getFieldValue }) {
                  return {
                    validator: function (rule, value) {
                      if (!value || getFieldValue("password") === value) return Promise.resolve();
                      return Promise.reject(new Error("The passwords do not match"));
                    },
                  };
                },
              ]}
            >
              <Input.Password />
            </Form.Item>

            {role !== "Customer" ? (
              <Form.Item
                label="SSN (16 digits)"
                name="ssn"
                extra="Team accounts need an SSN. Only the last 4 digits are shown later."
                rules={[{ required: true, message: "Enter your 16-digit SSN" }]}
              >
                <Input maxLength={19} placeholder="4000 1000 2000 3001" />
              </Form.Item>
            ) : null}

            {role === "Staff" ? (
              <>
                <Form.Item label="Your venue" name="venue_id" rules={[{ required: true, message: "Choose the venue you work at" }]}>
                  <Select options={venueOptions} placeholder="Choose your venue" />
                </Form.Item>
                <Form.Item label="Your manager's email" name="manager_email" rules={[{ required: true, message: "Enter your manager's email" }]}>
                  <Input placeholder="manager@venue.ae" />
                </Form.Item>
              </>
            ) : null}

            <Button type="primary" htmlType="submit" block size="large" loading={busy}>
              Create account
            </Button>
          </Form>
        </Card>
      </PageEnter>

      <Modal
        open={codeFor !== ""}
        title={codeFor === "email" ? "Check your email" : "Check your phone"}
        okText="Verify"
        onOk={checkCode}
        onCancel={() => setCodeFor("")}
      >
        <Typography.Paragraph type="secondary">We sent a 6-digit code. In the demo the code is 000000.</Typography.Paragraph>
        <Input.OTP length={6} value={code} onChange={setCode} />
      </Modal>
    </div>
  );
}
