"""Shared configuration: roles and demo accounts live here only."""

DEMO_ACCOUNTS = {
    "Customer": ("customer@email.com", "customer1234"),
    "Vendor": ("vendor@email.com", "vendor1234"),
    "Staff": ("staff@email.com", "staff1234"),
    "Partner": ("partner@email.com", "partner1234"),
    "Dispatcher": ("dispatcher@email.com", "dispatcher1234"),
    "Admin": ("admin@email.com", "admin1234"),
}

ROLES = list(DEMO_ACCOUNTS)
ADMIN_ROLE = "Admin"
# Roles a new account may be registered with; admins only come from DEMO_ACCOUNTS.
SIGNUP_ROLES = [r for r in ROLES if r != ADMIN_ROLE]
MIN_PASSWORD_LENGTH = 8
DEFAULT_LOGIN = DEMO_ACCOUNTS["Customer"]