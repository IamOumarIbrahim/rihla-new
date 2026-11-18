// the whole app: sign-in screens when nobody is signed in,
// otherwise the side menu of the role and the chosen page
import { useState } from "react";
import { ConfigProvider, Layout, Menu, Typography, Avatar, Space, Badge, App as AntApp } from "antd";
import { MotionConfig } from "motion/react";
import {
  Compass, Ticket, Star, LifeBuoy, TriangleAlert, Settings as SettingsIcon, LogOut, CalendarDays,
  Building2, Tags, ScanLine, ShoppingCart, ClipboardList, Car, Truck, Users, Flag,
} from "pulsoicon-react";
import { antTheme } from "./theme.js";
import { PageEnter } from "./components/motion.jsx";
import { isDemoMode } from "./api.js";

import Login from "./pages/Login.jsx";
import CreateAccount from "./pages/CreateAccount.jsx";
import ForgotPassword from "./pages/ForgotPassword.jsx";
import Explore from "./pages/Explore.jsx";
import MyBookings from "./pages/MyBookings.jsx";
import MyExperiences from "./pages/MyExperiences.jsx";
import Support from "./pages/Support.jsx";
import Report from "./pages/Report.jsx";
import Settings from "./pages/Settings.jsx";
import VendorEvents from "./pages/VendorEvents.jsx";
import VendorBookings from "./pages/VendorBookings.jsx";
import VendorVenues from "./pages/VendorVenues.jsx";
import VendorCategories from "./pages/VendorCategories.jsx";
import StaffCheckIn from "./pages/StaffCheckIn.jsx";
import StaffSupport from "./pages/StaffSupport.jsx";
import PartnerCart from "./pages/PartnerCart.jsx";
import Vehicles from "./pages/Vehicles.jsx";
import Dispatch from "./pages/Dispatch.jsx";
import AdminUsers from "./pages/AdminUsers.jsx";
import AdminReports from "./pages/AdminReports.jsx";
import AdminBookings from "./pages/AdminBookings.jsx";

const { Sider, Header, Content } = Layout;

// the menu of every role: [key, label, icon]
const MENUS = {
  Customer: [
    ["explore", "Explore", Compass],
    ["bookings", "My bookings", Ticket],
    ["experiences", "My experiences", Star],
    ["support", "Support", LifeBuoy],
  ],
  Vendor: [
    ["events", "My events", CalendarDays],
    ["vendor-bookings", "Bookings", Ticket],
    ["venues", "Venues", Building2],
    ["categories", "Categories", Tags],
  ],
  Staff: [
    ["check-in", "Venue check-in", ScanLine],
    ["staff-support", "Support tickets", LifeBuoy],
  ],
  Partner: [
    ["explore", "Explore tours", Compass],
    ["cart", "Shopping list", ShoppingCart],
    ["bookings", "Partner bookings", ClipboardList],
  ],
  Dispatcher: [
    ["vehicles", "Vehicles", Car],
    ["dispatch", "Dispatch", Truck],
  ],
  Admin: [
    ["users", "User accounts", Users],
    ["reports", "Reports", Flag],
    ["admin-bookings", "Bookings", Ticket],
  ],
};

export default function App() {
  // who is signed in: { email, role } or null
  const [user, setUser] = useState(null);
  // sign-in screens: "login", "create", "forgot"
  const [authScreen, setAuthScreen] = useState("login");
  const [page, setPage] = useState("");
  // the partner's shopping list count, shown on the menu
  const [cartCount, setCartCount] = useState(0);

  function signIn(email, role) {
    setUser({ email: email, role: role });
    setPage(MENUS[role][0][0]);
  }

  function signOut() {
    setUser(null);
    setAuthScreen("login");
    setCartCount(0);
  }

  let screen = null;
  if (user === null) {
    if (authScreen === "create") {
      screen = <CreateAccount onBack={() => setAuthScreen("login")} />;
    } else if (authScreen === "forgot") {
      screen = <ForgotPassword onBack={() => setAuthScreen("login")} />;
    } else {
      screen = (
        <Login
          onSignIn={signIn}
          onCreate={() => setAuthScreen("create")}
          onForgot={() => setAuthScreen("forgot")}
        />
      );
    }
  } else {
    screen = (
      <SignedIn
        user={user}
        page={page}
        setPage={setPage}
        cartCount={cartCount}
        setCartCount={setCartCount}
        onSignOut={signOut}
      />
    );
  }

  return (
    <ConfigProvider theme={antTheme}>
      <AntApp>
        <MotionConfig reducedMotion="user">{screen}</MotionConfig>
      </AntApp>
    </ConfigProvider>
  );
}

// the frame after sign in: dark menu on the left, header on top, page in the middle
function SignedIn(props) {
  const user = props.user;
  const role = user.role;

  const items = [];
  const menu = MENUS[role];
  for (let i = 0; i < menu.length; i++) {
    const key = menu[i][0];
    const Icon = menu[i][2];
    let label = menu[i][1];
    if (key === "cart" && props.cartCount > 0) {
      label = (
        <Space>
          {menu[i][1]}
          <Badge count={props.cartCount} size="small" />
        </Space>
      );
    }
    items.push({ key: key, label: label, icon: <Icon size={16} /> });
  }
  // admins are the ones who read reports, so they do not send them
  const bottomItems = [];
  if (role !== "Admin") {
    bottomItems.push({ key: "report", label: "Report a problem", icon: <TriangleAlert size={16} /> });
  }
  bottomItems.push({ key: "settings", label: "Settings", icon: <SettingsIcon size={16} /> });
  bottomItems.push({ key: "logout", label: "Log out", icon: <LogOut size={16} /> });

  function onMenu(info) {
    if (info.key === "logout") {
      props.onSignOut();
      return;
    }
    props.setPage(info.key);
  }

  const pageProps = { user: user, setPage: props.setPage, setCartCount: props.setCartCount };

  return (
    <Layout style={{ height: "100vh" }}>
      <Sider width={220} style={{ display: "flex", flexDirection: "column" }}>
        <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
          <div style={{ height: 64, display: "flex", alignItems: "center", gap: 10, padding: "0 24px" }}>
            <Typography.Text style={{ color: "#fff", fontSize: 18, fontWeight: 600 }}>Rihla</Typography.Text>
          </div>
          <Menu theme="dark" mode="inline" selectedKeys={[props.page]} items={items} onClick={onMenu} />
          <div style={{ flex: 1 }} />
          <Menu theme="dark" mode="inline" selectedKeys={[props.page]} items={bottomItems} onClick={onMenu} />
          <div style={{ height: 12 }} />
        </div>
      </Sider>
      <Layout>
        <Header style={{ display: "flex", alignItems: "center", borderBottom: "1px solid #f0f0f0" }}>
          <Typography.Text type="secondary">
            {role} / <span style={{ color: "#111827" }}>{pageTitle(role, props.page)}</span>
          </Typography.Text>
          <div style={{ flex: 1 }} />
          <Space size={16}>
            {isDemoMode() ? <Typography.Text type="warning">Demo mode (no server)</Typography.Text> : null}
            <Typography.Text type="secondary">{user.email}</Typography.Text>
            <Avatar style={{ background: "#e6f4ff", color: "#1677ff" }}>{user.email[0].toUpperCase()}</Avatar>
          </Space>
        </Header>
        <Content style={{ padding: 24, overflow: "auto" }}>
          {/* the key makes the enter animation run again when the page changes */}
          <PageEnter key={props.page}>{choosePage(role, props.page, pageProps)}</PageEnter>
        </Content>
      </Layout>
    </Layout>
  );
}

function pageTitle(role, page) {
  if (page === "report") {
    return "Report a problem";
  }
  if (page === "settings") {
    return "Settings";
  }
  const menu = MENUS[role];
  for (let i = 0; i < menu.length; i++) {
    if (menu[i][0] === page) {
      return menu[i][1];
    }
  }
  return "";
}

function choosePage(role, page, p) {
  if (page === "report") return <Report {...p} />;
  if (page === "settings") return <Settings {...p} />;
  if (page === "explore") return <Explore {...p} />;
  if (page === "bookings") return <MyBookings {...p} />;
  if (page === "experiences") return <MyExperiences {...p} />;
  if (page === "support") return <Support {...p} />;
  if (page === "events") return <VendorEvents {...p} />;
  if (page === "vendor-bookings") return <VendorBookings {...p} />;
  if (page === "venues") return <VendorVenues {...p} />;
  if (page === "categories") return <VendorCategories {...p} />;
  if (page === "check-in") return <StaffCheckIn {...p} />;
  if (page === "staff-support") return <StaffSupport {...p} />;
  if (page === "cart") return <PartnerCart {...p} />;
  if (page === "vehicles") return <Vehicles {...p} />;
  if (page === "dispatch") return <Dispatch {...p} />;
  if (page === "users") return <AdminUsers {...p} />;
  if (page === "reports") return <AdminReports {...p} />;
  if (page === "admin-bookings") return <AdminBookings {...p} />;
  return null;
}
