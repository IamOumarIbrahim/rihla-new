// prices, VAT and currency (same rules as src/pricing.py)
// all prices are saved in AED, the other currencies are only for showing

export const VAT_RATE = 0.05;
export const DEFAULT_CURRENCY = "AED";

// what 1 AED is in each currency (fixed rates)
export const CURRENCY_RATES = { AED: 1.0, USD: 0.2723, EUR: 0.251, GBP: 0.215 };
export const CURRENCIES = ["AED", "USD", "EUR", "GBP"];

// rounds to 2 decimals
function round2(value) {
  return Math.round(value * 100) / 100;
}

export function normalizeCurrency(code) {
  let text = (code || "").trim().toUpperCase();
  if (CURRENCY_RATES[text] === undefined) {
    text = DEFAULT_CURRENCY;
  }
  return text;
}

// '240 AED' -> 240
export function priceToNumber(priceText) {
  let digits = "";
  const text = String(priceText || "");
  for (let i = 0; i < text.length; i++) {
    if (text[i] >= "0" && text[i] <= "9") {
      digits = digits + text[i];
    }
  }
  if (digits === "") {
    return 0;
  }
  return parseInt(digits, 10);
}

// { base, vat, total } in AED
export function vatBreakdown(baseAed) {
  const base = round2(Number(baseAed || 0));
  const vat = round2(base * VAT_RATE);
  const total = round2(base + vat);
  return { base: base, vat: vat, total: total };
}

export function convert(amountAed, currency) {
  const rate = CURRENCY_RATES[normalizeCurrency(currency)];
  return round2(Number(amountAed || 0) * rate);
}

// 1234.5 -> "1,234.50 AED"
export function formatMoney(amountAed, currency) {
  const code = normalizeCurrency(currency);
  const amount = convert(amountAed, code);
  const text = amount.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return text + " " + code;
}

// refund rules shown to the customer (the server makes the real decision)
// 48 hours or more: 100%, 24 to 48 hours: 50%, under 24 hours: no cancel
export function refundText(percent) {
  if (percent === 100) {
    return "Full refund (100%)";
  }
  if (percent === 50) {
    return "Half refund (50%)";
  }
  return "Cannot be cancelled (less than 24 hours left)";
}
