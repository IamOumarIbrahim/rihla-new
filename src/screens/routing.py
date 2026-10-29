from database import get_role
from welcome.users_welcome import BaseWelcomeScreen
from welcome.customer_welcome import show_customer_welcome
from welcome.vendor_welcome import show_vendor_welcome
from welcome.staff_welcome import show_staff_welcome
from welcome.partner_welcome import show_partner_welcome
from welcome.dispatcher_welcome import show_dispatcher_welcome

# To add a role: create welcome/<role>_welcome.py and add one line here.
WELCOME_SCREENS = {
    "Customer": show_customer_welcome,
    "Vendor": show_vendor_welcome,
    "Staff": show_staff_welcome,
    "Partner": show_partner_welcome,
    "Dispatcher": show_dispatcher_welcome,
}


def show_welcome_screen(root, email):
    role = get_role(email)
    show_fn = WELCOME_SCREENS.get(role)
    if show_fn:
        show_fn(root, email)
    else:
        BaseWelcomeScreen(root, email, role)