from .users_welcome import BaseWelcomeScreen
from .vehicle_view import VehicleView
from .dispatch_view import DispatchView


class DispatcherWelcomeScreen(BaseWelcomeScreen):
    def __init__(self, root, email):
        super().__init__(root, email, "Dispatcher")
        self.root = root
        self.email = email

        self.vehicle_view = VehicleView(self)
        self.dispatch_view = DispatchView(self)

        self.add_nav_button("Register Vehicles", self.vehicle_view.build_register_content, icon="car")
        self.add_nav_button("Fleet Maintenance", self.vehicle_view.build_fleet_management_content, icon="wrench")
        self.add_nav_button("Event Dispatch", self.dispatch_view.build_dispatch_content, icon="truck")

        self.vehicle_view.build_register_content()


def show_dispatcher_welcome(root, email):
    DispatcherWelcomeScreen(root, email)