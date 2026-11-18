// opens each mockup in a hidden window and saves a picture of it
const { app, BrowserWindow } = require("electron");
const path = require("path");
const fs = require("fs");

const out = process.argv[process.argv.length - 1];
let pages = ["design_a", "design_b", "design_c"];
if (process.env.ONLY) { pages = [process.env.ONLY]; }

app.whenReady().then(async function () {
  for (let i = 0; i < pages.length; i++) {
    const win = new BrowserWindow({ width: 1440, height: 900, show: false, useContentSize: true });
    try {
      await win.loadFile(path.join(__dirname, pages[i] + ".html"));
    } catch (err) {
      console.log("load problem", pages[i], err.message);
    }
    await new Promise(function (done) { setTimeout(done, 800); });
    const image = await win.webContents.capturePage();
    fs.writeFileSync(path.join(out, pages[i] + ".png"), image.toPNG());
    win.destroy();
  }
  app.quit();
});
