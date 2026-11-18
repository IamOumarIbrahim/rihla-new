// demo payment check (same rules as src/payment.py)
// there is no real payment, the form is filled with these details and fails if one is changed

export const DEMO_PAYMENT_DETAILS = {
  visa: { card_type: "Visa", card_number: "4532 0123 4567 8910", cardholder: "RIHLA DEMO USER", expiry: "12/28", cvv: "789" },
  mastercard: { card_type: "Mastercard", card_number: "5425 2334 4556 6778", cardholder: "RIHLA DEMO USER", expiry: "11/27", cvv: "321" },
  bank: { bank_name: "Emirates NBD", account_name: "Rihla Tourism LLC", iban: "AE120260001234567890123", swift: "EBBDAEAD" },
};

// keeps only the digits
function onlyDigits(text) {
  let result = "";
  const value = String(text || "");
  for (let i = 0; i < value.length; i++) {
    if (value[i] >= "0" && value[i] <= "9") {
      result = result + value[i];
    }
  }
  return result;
}

// keeps only letters and numbers, in capitals
function onlyLettersAndDigits(text) {
  let result = "";
  const value = String(text || "").toUpperCase();
  for (let i = 0; i < value.length; i++) {
    const c = value[i];
    if ((c >= "A" && c <= "Z") || (c >= "0" && c <= "9")) {
      result = result + c;
    }
  }
  return result;
}

// gives back { ok, message }
export function verifyDemoPayment(method, details) {
  if (method === "visa" || method === "mastercard") {
    const expected = DEMO_PAYMENT_DETAILS[method];
    if (onlyDigits(details.card_number) !== onlyDigits(expected.card_number)) {
      return { ok: false, message: "Card number does not match the demo " + expected.card_type + " card." };
    }
    if ((details.cardholder || "").trim().toUpperCase() !== expected.cardholder) {
      return { ok: false, message: "Cardholder name does not match the demo card." };
    }
    if ((details.expiry || "").trim() !== expected.expiry) {
      return { ok: false, message: "Expiry date does not match the demo card." };
    }
    if ((details.cvv || "").trim() !== expected.cvv) {
      return { ok: false, message: "CVV does not match the demo card." };
    }
    return { ok: true, message: "Payment authorized." };
  }

  if (method === "bank") {
    const expected = DEMO_PAYMENT_DETAILS.bank;
    if ((details.bank_name || "").trim().toLowerCase() !== expected.bank_name.toLowerCase()) {
      return { ok: false, message: "Bank name does not match the demo account." };
    }
    if ((details.account_name || "").trim().toLowerCase() !== expected.account_name.toLowerCase()) {
      return { ok: false, message: "Account holder does not match the demo account." };
    }
    if (onlyLettersAndDigits(details.iban) !== onlyLettersAndDigits(expected.iban)) {
      return { ok: false, message: "IBAN does not match the demo account." };
    }
    if (onlyLettersAndDigits(details.swift) !== onlyLettersAndDigits(expected.swift)) {
      return { ok: false, message: "SWIFT code does not match the demo account." };
    }
    return { ok: true, message: "Bank transfer authorized." };
  }

  return { ok: false, message: "Please choose a payment method." };
}

// a made up transaction id like TXN-8F3A2C1B
export function newTransactionId() {
  const letters = "0123456789ABCDEF";
  let id = "TXN-";
  for (let i = 0; i < 8; i++) {
    id = id + letters[Math.floor(Math.random() * 16)];
  }
  return id;
}
