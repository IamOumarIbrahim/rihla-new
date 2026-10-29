"""Single place to move between screens.

Imports are done lazily inside each function so screens can call each other
without circular-import problems.
"""


def show_login(root, prefilled_email=None, prefilled_password=None):
    from screens.login import show_login_screen
    show_login_screen(root, prefilled_email, prefilled_password)


def show_create_account(root):
    from screens.create_account import show_create_account_screen
    show_create_account_screen(root)


def show_forgot_password(root):
    from screens.forgot_password import show_forgot_password_screen
    show_forgot_password_screen(root)


def show_welcome(root, email):
    from screens.routing import show_welcome_screen
    show_welcome_screen(root, email)