// Renders a .dot file to SVG with Graphviz (wasm) and then to PNG with headless Chrome.
import { instance } from "@viz-js/viz";
import puppeteer from "puppeteer";
import fs from "fs";

const [, , input, output, engine = "neato"] = process.argv;
const viz = await instance();
const svg = viz.renderString(fs.readFileSync(input, "utf8"), { format: "svg", engine });
fs.writeFileSync(output.replace(/\.png$/, ".svg"), svg);

const browser = await puppeteer.launch({
  executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
  args: ["--no-sandbox"],
});
const page = await browser.newPage();
await page.setViewport({ width: 800, height: 600, deviceScaleFactor: 2 });
await page.setContent(`<html><body style="margin:0;background:#fff">${svg}</body></html>`);
const el = await page.$("svg");
const box = await el.boundingBox();
await page.setViewport({ width: Math.ceil(box.width) + 4, height: Math.ceil(box.height) + 4, deviceScaleFactor: 2 });
await el.screenshot({ path: output, omitBackground: false, captureBeyondViewport: true });
await browser.close();
console.log("rendered", output, Math.round(box.width), "x", Math.round(box.height));
