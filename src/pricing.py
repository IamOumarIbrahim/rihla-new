"""Prices, VAT and currency conversion.

Every price in the database is stored in AED. Other currencies are only used
for display, using the fixed rates below.
"""

VAT_RATE = 0.05

DEFAULT_CURRENCY = "AED"

# How much 1 AED is worth in each currency (indicative fixed rates).
CURRENCY_RATES = {
    "AED": 1.0,
    "USD": 0.2723,
    "EUR": 0.2510,
    "GBP": 0.2150,
}

CURRENCIES = list(CURRENCY_RATES)


def normalize_currency(code):
    code = (code or "").strip().upper()
    return code if code in CURRENCY_RATES else DEFAULT_CURRENCY


def vat_breakdown(base_aed):
    """Returns (base, vat, total) in AED, rounded to 2 decimals."""
    base = round(float(base_aed or 0), 2)
    vat = round(base * VAT_RATE, 2)
    return base, vat, round(base + vat, 2)


def convert(amount_aed, currency):
    return round(float(amount_aed or 0) * CURRENCY_RATES[normalize_currency(currency)], 2)


def format_money(amount_aed, currency=DEFAULT_CURRENCY):
    currency = normalize_currency(currency)
    return f"{convert(amount_aed, currency):,.2f} {currency}"
