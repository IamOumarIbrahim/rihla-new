// the pieces of a booking that customers and partners share:
// which dates an event runs on, the demo payment window, and the confirmation with the receipt
import { useState } from "react";
import { Modal, Radio, Form, Input, Typography, Descriptions, Button, Result, Space, App } from "antd";
import { CreditCard, Landmark, Download, CircleCheck } from "pulsoicon-react";
import { DEMO_PAYMENT_DETAILS, verifyDemoPayment, newTransactionId } from "../payment.js";
import { vatBreakdown, formatMoney, normalizeCurrency } from "../money.js";
import { Burst } from "./motion.jsx";

// true when the event takes place on this day (dayjs date)
// recurring events run on the week days in recur_day, one-time events on their own date
export function eventRunsOn(event, day) {
  if (event.is_recurring === "Recurring") {
    const weekday = day.format("dddd");
    const days = (event.recur_day || "").split(",");
    for (let i = 0; i < days.length; i++) {
      if (days[i].trim() === weekday) {
        return true;
      }
    }
    return false;
  }
  return (event.event_datetime || "").slice(0, 10) === day.format("YYYY-MM-DD");
}

// "Every day", "Tue, Thu" or "31 Dec 2026"
export function scheduleText(event) {
  if (event.is_recurring === "Recurring") {
    const days = (event.recur_day || "").split(",");
    if (days.length === 7) {
      return "Every day";
    }
    const short = [];
    for (let i = 0; i < days.length; i++) {
      short.push(days[i].trim().slice(0, 3));
    }
    return short.join(", ");
  }
  return (event.event_datetime || "").slice(0, 10);
}

// the demo payment window, the form starts filled with the demo card
export function PaymentModal(props) {
  const [method, setMethod] = useState("visa");
  const [form] = Form.useForm();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  function chooseMethod(value) {
    setMethod(value);
    setError("");
    form.setFieldsValue(DEMO_PAYMENT_DETAILS[value]);
  }

  async function pay() {
    const values = form.getFieldsValue(true);
    const check = verifyDemoPayment(method, values);
    if (!check.ok) {
      setError(check.message);
      return;
    }
    setBusy(true);
    let methodName = "Bank transfer";
    if (method === "visa") methodName = "Visa";
    if (method === "mastercard") methodName = "Mastercard";
    await props.onPaid({ txn_id: newTransactionId(), method: methodName, currency: normalizeCurrency(props.currency) });
    setBusy(false);
  }

  const price = vatBreakdown(props.baseAed);

  return (
    <Modal
      open={props.open}
      title="Payment"
      okText={"Pay " + formatMoney(price.total, props.currency)}
      onOk={pay}
      confirmLoading={busy}
      onCancel={props.onCancel}
      afterClose={function () {
        setMethod("visa");
        setError("");
      }}
      destroyOnHidden
    >
      <Descriptions size="small" column={1} bordered style={{ marginBottom: 16 }}>
        <Descriptions.Item label="Price">{formatMoney(price.base, props.currency)}</Descriptions.Item>
        <Descriptions.Item label="VAT (5%)">{formatMoney(price.vat, props.currency)}</Descriptions.Item>
        <Descriptions.Item label="Total">
          <b>{formatMoney(price.total, props.currency)}</b>
        </Descriptions.Item>
      </Descriptions>

      <Radio.Group value={method} onChange={(e) => chooseMethod(e.target.value)} style={{ marginBottom: 16 }}>
        <Radio.Button value="visa"><Space><CreditCard size={14} />Visa</Space></Radio.Button>
        <Radio.Button value="mastercard"><Space><CreditCard size={14} />Mastercard</Space></Radio.Button>
        <Radio.Button value="bank"><Space><Landmark size={14} />Bank transfer</Space></Radio.Button>
      </Radio.Group>

      {/* the form starts filled with the demo visa card */}
      <Form form={form} layout="vertical" preserve={false} initialValues={DEMO_PAYMENT_DETAILS.visa}>
        {method === "bank" ? (
          <>
            <Form.Item label="Bank" name="bank_name"><Input /></Form.Item>
            <Form.Item label="Account holder" name="account_name"><Input /></Form.Item>
            <Form.Item label="IBAN" name="iban"><Input /></Form.Item>
            <Form.Item label="SWIFT" name="swift"><Input /></Form.Item>
          </>
        ) : (
          <>
            <Form.Item label="Card number" name="card_number"><Input /></Form.Item>
            <Form.Item label="Cardholder" name="cardholder"><Input /></Form.Item>
            <Space>
              <Form.Item label="Expiry (MM/YY)" name="expiry"><Input style={{ width: 120 }} /></Form.Item>
              <Form.Item label="CVV" name="cvv"><Input style={{ width: 90 }} /></Form.Item>
            </Space>
          </>
        )}
      </Form>
      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
        Demo payment: the details are filled in for you. Changing any of them makes the payment fail.
      </Typography.Text>
      {error ? <div><Typography.Text type="danger">{error}</Typography.Text></div> : null}
    </Modal>
  );
}

// the receipt as a small html page, Electron prints it to a PDF
export function receiptHtml(entries, payment, payerEmail) {
  const cur = normalizeCurrency(payment ? payment.currency : "AED");
  let rows = "";
  let grandBase = 0;
  for (let i = 0; i < entries.length; i++) {
    const item = entries[i];
    grandBase = grandBase + Number(item.base || 0);
    rows = rows + "<h3>" + escapeHtml(item.title) + "</h3><table>";
    if (item.venue) rows = rows + "<tr><td>Venue</td><td>" + escapeHtml(item.venue) + "</td></tr>";
    if (item.date) rows = rows + "<tr><td>Date</td><td>" + escapeHtml(item.date) + "</td></tr>";
    if (item.time) rows = rows + "<tr><td>Time</td><td>" + escapeHtml(item.time) + "</td></tr>";
    if (item.guests) rows = rows + "<tr><td>Guests</td><td>" + item.guests + "</td></tr>";
    if (item.client_name) rows = rows + "<tr><td>Group / client</td><td>" + escapeHtml(item.client_name) + "</td></tr>";
    if (item.ticket_code) rows = rows + "<tr><td>Ticket code</td><td><b>" + formatCode(item.ticket_code) + "</b></td></tr>";
    rows = rows + "</table>";
  }
  const price = vatBreakdown(grandBase);
  let charged = "";
  if (cur !== "AED") {
    charged = "<p class='muted'>Charged in AED: " + formatMoney(price.total, "AED") + "</p>";
  }
  return (
    "<html><head><meta charset='utf-8'><style>" +
    "body{font-family:'Noto Sans','Segoe UI',sans-serif;color:#111827;padding:40px;font-size:13px}" +
    "h1{font-size:22px;margin:0}h3{margin:20px 0 6px;font-size:15px}td{padding:3px 16px 3px 0}" +
    ".muted{color:#6b7280}.status{color:#16a34a;font-weight:700}.total{font-size:16px;font-weight:700}" +
    "</style></head><body>" +
    "<h1>Rihla | Booking details</h1>" +
    "<p class='muted'>Issued " + new Date().toLocaleString("en-GB") + "</p>" +
    "<p class='status'>Status: CONFIRMED</p>" +
    "<table><tr><td>Booked by</td><td>" + escapeHtml(payerEmail) + "</td></tr>" +
    "<tr><td>Transaction</td><td>" + escapeHtml(payment.txn_id) + "</td></tr>" +
    "<tr><td>Payment method</td><td>" + escapeHtml(payment.method) + "</td></tr></table>" +
    rows +
    "<h3>Price</h3><table>" +
    "<tr><td>Base price</td><td>" + formatMoney(price.base, cur) + "</td></tr>" +
    "<tr><td>VAT (5%)</td><td>" + formatMoney(price.vat, cur) + "</td></tr>" +
    "<tr><td class='total'>Total</td><td class='total'>" + formatMoney(price.total, cur) + "</td></tr></table>" +
    charged +
    "</body></html>"
  );
}

function escapeHtml(text) {
  return String(text || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// '1234567890123456' -> '1234 5678 9012 3456'
export function formatCode(code) {
  const clean = String(code || "").replace(/ /g, "");
  let result = "";
  for (let i = 0; i < clean.length; i++) {
    if (i > 0 && i % 4 === 0) {
      result = result + " ";
    }
    result = result + clean[i];
  }
  return result;
}

// after a booking: the result, the ticket code(s) and the receipt button
export function ConfirmModal(props) {
  const { message } = App.useApp();

  async function download() {
    const html = receiptHtml(props.entries, props.payment, props.email);
    if (window.rihla && window.rihla.saveReceipt) {
      const r = await window.rihla.saveReceipt(html, "Rihla_booking_" + props.payment.txn_id + ".pdf");
      if (r.saved) {
        message.success("Receipt saved");
      }
    } else {
      // in the online preview there is no Electron, so we open the receipt in a new tab
      const win = window.open("", "_blank");
      if (win) {
        win.document.write(html);
      }
    }
  }

  return (
    <Modal open={props.open} footer={null} onCancel={props.onClose} width={520} destroyOnHidden>
      <Result
        status="success"
        icon={
          <Burst play={props.open}>
            <CircleCheck size={64} color="#16a34a" strokeWidth={1.5} play={props.open} />
          </Burst>
        }
        title="Booking confirmed"
        subTitle={"Payment " + (props.payment ? props.payment.txn_id : "") + " | " + (props.payment ? props.payment.method : "")}
        extra={[
          <Button key="pdf" icon={<Download size={16} />} onClick={download}>
            Download receipt
          </Button>,
          <Button key="close" type="primary" onClick={props.onClose}>
            Done
          </Button>,
        ]}
      >
        {props.entries.map(function (item, i) {
          return (
            <div key={i} style={{ marginBottom: 8 }}>
              <Typography.Text strong>{item.title}</Typography.Text>
              <div>
                <Typography.Text type="secondary">{item.date} | {item.guests} guest(s)</Typography.Text>
              </div>
              <div>
                <Typography.Text type="secondary">Ticket </Typography.Text>
                <span className="ticket-code">{formatCode(item.ticket_code)}</span>
              </div>
            </div>
          );
        })}
      </Result>
    </Modal>
  );
}
