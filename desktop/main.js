// Electron: opens the Rihla window and saves PDF receipts
// the screens themselves are in src/ (React), they talk to the Python server on localhost:5000
const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const path = require("path");
const fs = require("fs");

function createWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1100,
    minHeight: 700,
    title: "Rihla",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
    },
  });
  win.removeMenu();

  // npm run dev uses the Vite server, npm start uses the built files
  if (process.env.RIHLA_DEV_URL) {
    win.loadURL(process.env.RIHLA_DEV_URL);
  } else {
    win.loadFile(path.join(__dirname, "dist", "index.html"));
  }
}

// the receipt: the screen sends the receipt as html, we print it to a pdf file
ipcMain.handle("save-receipt", async function (event, html, fileName) {
  const owner = BrowserWindow.fromWebContents(event.sender);
  const choice = await dialog.showSaveDialog(owner, {
    title: "Save receipt",
    defaultPath: fileName,
    filters: [{ name: "PDF", extensions: ["pdf"] }],
  });
  if (choice.canceled || !choice.filePath) {
    return { saved: false };
  }

  const hidden = new BrowserWindow({ show: false });
  await hidden.loadURL("data:text/html;charset=utf-8," + encodeURIComponent(html));
  const pdf = await hidden.webContents.printToPDF({ pageSize: "A4", printBackground: true });
  hidden.destroy();
  fs.writeFileSync(choice.filePath, pdf);
  return { saved: true, path: choice.filePath };
});

app.whenReady().then(createWindow);

app.on("window-all-closed", function () {
  app.quit();
});
