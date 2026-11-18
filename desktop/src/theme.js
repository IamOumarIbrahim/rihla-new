// Ant Design settings for the whole app (design C)
// colours come from the Ant design system in OpenDesign (design-systems/ant)

export const antTheme = {
  token: {
    colorPrimary: "#1677ff",
    colorSuccess: "#16a34a",
    colorWarning: "#d97706",
    colorError: "#dc2626",
    colorText: "#111827",
    colorBgLayout: "#f5f5f5",
    fontFamily: "'Noto Sans', 'Segoe UI', sans-serif",
    fontSize: 14,
    borderRadius: 6,
    borderRadiusLG: 8,
    // Ant Design's own short animations (modals, drawers, messages)
    motionDurationMid: "0.2s",
    motionDurationSlow: "0.25s",
  },
  components: {
    Layout: { siderBg: "#001529", headerBg: "#ffffff", headerHeight: 64, headerPadding: "0 24px" },
    Menu: { darkItemBg: "#001529", darkItemSelectedBg: "#1677ff", itemBorderRadius: 8, itemMarginInline: 8 },
  },
};
