# sends the user to the welcome screen of their role
from database import get_role
from welcome.users_welcome import BaseWelcomeScreen
from welcome.customer_welcome import show_customer_welcome
from welcome.vendor_welcome import show_vendor_welcome
from welcome.staff_welcome import show_staff_welcome
from welcome.partner_welcome import show_partner_welcome
from welcome.dispatcher_welcome import show_dispatcher_welcome
from welcome.admin_welcome import show_admin_welcome


def show_welcome_screen(root, email):
    role = get_role(email)
    if role == "Customer":
        show_customer_welcome(root, email)
    elif role == "Vendor":
        show_vendor_welcome(root, email)
    elif role == "Staff":
        show_staff_welcome(root, email)
    elif role == "Partner":
        show_partner_welcome(root, email)
    elif role == "Dispatcher":
        show_dispatcher_welcome(root, email)
    elif role == "Admin":
        show_admin_welcome(root, email)
    else:
        BaseWelcomeScreen(root, email, role)
