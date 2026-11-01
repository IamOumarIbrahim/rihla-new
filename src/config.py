# roles and demo accounts (only kept here)

DEMO_ACCOUNTS = {
    "Customer": ("customer@email.com", "customer1234"),
    "Vendor": ("vendor@email.com", "vendor1234"),
    "Staff": ("staff@email.com", "staff1234"),
    "Partner": ("partner@email.com", "partner1234"),
    "Dispatcher": ("dispatcher@email.com", "dispatcher1234"),
    "Admin": ("admin@email.com", "admin1234"),
}

ROLES = []
for r in DEMO_ACCOUNTS:
    ROLES.append(r)
ADMIN_ROLE = "Admin"

# roles you can sign up with, admins only come from DEMO_ACCOUNTS
SIGNUP_ROLES = []
for r in ROLES:
    if r != ADMIN_ROLE:
        SIGNUP_ROLES.append(r)
MIN_PASSWORD_LENGTH = 8
DEFAULT_LOGIN = DEMO_ACCOUNTS["Customer"]
