// opens the real app, does the steps of a script and saves screenshots
// usage: npx electron tools/capture.js <steps.json> <out folder>
// a step is one of:
//   { "click": "text on a button or menu item" }       clicks the first visible element with that text
//   { "type": ["css selector", "text"] }               types into an input
//   { "wait": 600 }                                    waits (ms)
//   { "shot": "name" }                                 saves out/name.png
//   { "js": "code" }                                   runs code in the page
const { app, BrowserWindow } = require("electron");
const path = require("path");
const fs = require("fs");

const args = process.argv.slice(-2);
const steps = JSON.parse(fs.readFileSync(args[0], "utf8"));
const outDir = args[1];
fs.mkdirSync(outDir, { recursive: true });

// finds a visible element whose own text is exactly the label and clicks it
const CLICK_CODE = function (label) {
  return `(function () {
    const want = ${JSON.stringify(label)};
    // buttons first, then menu items and tabs, then anything else with that text
    const groups = ['button', 'a, [role=menuitem], [role=tab], .ant-select-item, label', '.ant-card, .ant-picker-cell, h1, h2, h3, h4, h5, span, div, td'];
    let all = [];
    for (const g of groups) all = all.concat(Array.from(document.querySelectorAll(g)));
    for (const el of all) {
      const text = (el.innerText || '').trim();
      const r = el.getBoundingClientRect();
      if (text === want && r.width > 0 && r.height > 0) {
        const target = el.closest('button, a, [role=menuitem], [role=tab], .ant-card, .ant-select-item, label') || el;
        target.click();
        return true;
      }
    }
    return false;
  })()`;
};

// types like a person, so React sees the change
const TYPE_CODE = function (selector, text) {
  return `(function () {
    const el = document.querySelector(${JSON.stringify(selector)});
    if (!el) return false;
    const setter = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el), 'value').set;
    setter.call(el, ${JSON.stringify(text)});
    el.dispatchEvent(new Event('input', { bubbles: true }));
    return true;
  })()`;
};

function sleep(ms) {
  return new Promise(function (done) {
    setTimeout(done, ms);
  });
}

app.whenReady().then(async function () {
  // off-screen rendering: the page draws 60 frames a second without a visible window,
  // so animations finish like they do for a real user
  const win = new BrowserWindow({
    width: 1440, height: 900, show: false, useContentSize: true,
    webPreferences: { offscreen: true, backgroundThrottling: false },
  });
  win.webContents.setFrameRate(60);
  // print errors from the page, so a broken screen shows up here
  win.webContents.on("console-message", function (event) {
    if (event.level === "error" || event.level === "warning") {
      console.log("[page " + event.level + "]", String(event.message).slice(0, 300));
    }
  });
  await win.loadFile(path.join(__dirname, "..", "dist", "index.html"));
  await sleep(1200);
  for (const step of steps) {
    if (step.click !== undefined) {
      const ok = await win.webContents.executeJavaScript(CLICK_CODE(step.click));
      if (!ok) console.log("not found:", step.click);
      await sleep(step.after || 500);
    } else if (step.type !== undefined) {
      const ok = await win.webContents.executeJavaScript(TYPE_CODE(step.type[0], step.type[1]));
      if (!ok) console.log("no input:", step.type[0]);
      await sleep(200);
    } else if (step.wait !== undefined) {
      await sleep(step.wait);
    } else if (step.js !== undefined) {
      try {
        await win.webContents.executeJavaScript(step.js);
      } catch (err) {
        console.log("step failed:", step.js.slice(0, 80));
      }
      await sleep(step.after || 300);
    } else if (step.shot !== undefined) {
      const image = await win.webContents.capturePage();
      fs.writeFileSync(path.join(outDir, step.shot + ".png"), image.toPNG());
      console.log("saved", step.shot);
    }
  }
  app.quit();
});
