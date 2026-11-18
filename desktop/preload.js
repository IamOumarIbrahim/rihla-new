// gives the screens one safe function from Electron: saving a receipt as PDF
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("rihla", {
  saveReceipt: function (html, fileName) {
    return ipcRenderer.invoke("save-receipt", html, fileName);
  },
});
