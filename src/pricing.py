# prices, VAT and currency
# all prices in the database are in AED, the other currencies are only for showing
# with the fixed rates below

VAT_RATE = 0.05

DEFAULT_CURRENCY = "AED"

# what 1 AED is in each currency (fixed rates)
CURRENCY_RATES = {
    "AED": 1.0,
    "USD": 0.2723,
    "EUR": 0.2510,
    "GBP": 0.2150,
}

CURRENCIES = []
for c in CURRENCY_RATES:
    CURRENCIES.append(c)


def normalize_currency(code):
    if code:
        code = code.strip().upper()
    else:
        code = ""
    if code in CURRENCY_RATES:
        return code
    return DEFAULT_CURRENCY


# (base, vat, total) in AED rounded to 2 decimals
def vat_breakdown(base_aed):
    if not base_aed:
        base_aed = 0
    base = round(float(base_aed), 2)
    vat = round(base * VAT_RATE, 2)
    total = round(base + vat, 2)
    return base, vat, total


# (base, vat, total) of a refund of percent% of a total that has VAT in it
# vat = total - base
def refund_breakdown(total_aed, percent):
    if not total_aed:
        total_aed = 0
    total = round(float(total_aed) * percent / 100, 2)
    base = round(total / (1 + VAT_RATE), 2)
    vat = round(total - base, 2)
    return base, vat, total


def convert(amount_aed, currency):
    if not amount_aed:
        amount_aed = 0
    rate = CURRENCY_RATES[normalize_currency(currency)]
    return round(float(amount_aed) * rate, 2)


def format_money(amount_aed, currency=DEFAULT_CURRENCY):
    currency = normalize_currency(currency)
    amount = convert(amount_aed, currency)
    return format(amount, ",.2f") + " " + currency
