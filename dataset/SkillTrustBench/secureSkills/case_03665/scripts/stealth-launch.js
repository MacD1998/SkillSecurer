#!/usr/bin/env node
/**
 * stealth-launch.js
 * Stealth browser automation via Playwright CDP.
 * 
 * Single invocation = one complete workflow (open → interact → output → close)
 * For multi-step flows, use --continue flag to reuse browser instance.
 * 
 * Usage:
 *   node stealth-launch.js open <url>                    # Open and get snapshot
 *   node stealth-launch.js <cmd> [args] --continue      # Use existing browser
 *   node stealth-launch.js close                        # Close and cleanup
 */

import { chromium } from 'playwright';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SESSION_FILE = resolve(__dirname, '../.session.json');

const STEALTH_ARGS = [
  '--disable-blink-features=AutomationControlled',
  '--disable-dev-shm-usage',
  '--no-sandbox',
  '--disable-setuid-sandbox',
  '--disable-infobars',
  '--disable-browser-side-navigation',
  '--window-size=1280,900',
];

const STEALTH_INIT = `
() => {
  Object.defineProperty(navigator, 'webdriver', { get: () => undefined, configurable: true });
  window.chrome = window.chrome || {};
  try { Object.defineProperty(window.chrome, 'runtime', { get: () => undefined }); } catch(e) {}
  
  const origQuery = window.navigator.permissions?.query;
  if (origQuery) {
    window.navigator.permissions.query = function(query) {
      if (['notifications','geolocation','midi','camera','microphone'].includes(query.name)) {
        return Promise.resolve({ state: 'granted', onchange: null });
      }
      return origQuery.apply(this, arguments);
    };
  }
  
  const gp = HTMLCanvasElement.prototype.getContext.getOwnPropertyDescriptor(WebGLRenderingContext.prototype, 'getParameter').get;
  if (gp) {
    HTMLCanvasElement.prototype.getContext.getOwnPropertyDescriptor(WebGLRenderingContext.prototype, 'getParameter').get = function(p) {
      if (p === 37445) return 'Intel Inc.';
      if (p === 37446) return 'Intel Iris OpenGL Engine';
      return gp.call(this, p);
    };
  }
  
  const origImgData = CanvasRenderingContext2D.prototype.getImageData;
  if (origImgData) {
    CanvasRenderingContext2D.prototype.getImageData = function(...args) {
      try { return origImgData.apply(this, args); } catch(e) { return { data: { length: 0 } }; }
    };
  }
  
  try { delete Navigator.prototype.webdriver; } catch(e) {}
}
`;

// --- Session State ---
let browser = null;
let page = null;
let refs = {};

function saveSession() {
  writeFileSync(SESSION_FILE, JSON.stringify({ active: true }));
}
function clearSession() {
  if (existsSync(SESSION_FILE)) {
    try { require('fs').unlinkSync(SESSION_FILE); } catch(e) {}
  }
}

async function ensureBrowser() {
  if (!browser) {
    browser = await chromium.launch({ headless: true, args: STEALTH_ARGS });
    browser.on('disconnected', () => { browser = null; page = null; clearSession(); });
  }
  if (!page) {
    page = await browser.newPage();
    await page.addInitScript(`(${STEALTH_INIT})()`);
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.setExtraHTTPHeaders({ 'Accept-Language': 'en-US,en;q=0.9' });
    saveSession();
  }
  return page;
}

function buildLocator(p, el) {
  if (el.id) return p.locator(`#${CSS.escape(el.id)}`).first();
  if (el.tag === 'a' && el.href) return p.locator(`a[href="${el.href}"]`).first();
  if (el.placeholder) return p.locator(`[placeholder="${el.placeholder}"]`).first();
  if (el.tag === 'input' && el.type && el.type !== 'submit') return p.locator(`input[type="${el.type}"]`).first();
  if (el.tag === 'button' || el.tag === 'a') return p.getByText(el.name || el.id || '', { exact: false }).first();
  if (el.role) return p.locator(`[role="${el.role}"]`).filter({ hasText: el.name || '' }).first();
  return p.locator(el.tag).filter({ hasText: el.name || '' }).first();
}

function resolveRef(ref) {
  if (!ref || !refs[ref]) return null;
  return refs[ref];
}

// --- Commands ---

async function cmdOpen(url) {
  const p = await ensureBrowser();
  await p.goto(url, { waitUntil: 'domcontentloaded', timeout: 20000 });
  await p.waitForTimeout(500);
  return JSON.stringify({ success: true, url: p.url(), title: await p.title() });
}

async function cmdSnapshot() {
  const p = await ensureBrowser();
  await p.waitForLoadState('domcontentloaded');
  const selectors = ['a[href]','button','input:not([type="hidden"])','textarea','select','[role="button"]','[role="link"]','[role="textbox"]','[role="menuitem"]'];
  const elements = [];
  for (const sel of selectors) {
    try {
      const els = await p.locator(sel).all();
      for (const el of els) {
        try {
          const visible = await el.isVisible();
          if (!visible) continue;
          const tag = await el.evaluate(e => e.tagName.toLowerCase());
          const role = await el.evaluate(e => e.getAttribute('role') || '');
          let name = await el.evaluate(e => e.getAttribute('aria-label') || e.textContent?.trim().slice(0, 60).replace(/\s+/g, ' ') || '');
          const id = await el.evaluate(e => e.id || '');
          const href = await el.evaluate(e => e.getAttribute('href') || '');
          const type = await el.evaluate(e => e.type || '');
          const placeholder = await el.evaluate(e => e.getAttribute('placeholder') || '');
          const value = await el.evaluate(e => (e.value || '').slice(0, 30));
          if (name || href || placeholder) {
            elements.push({ tag, role, name, id, href, type, placeholder, value });
          }
        } catch(e) {}
      }
    } catch(e) {}
  }
  refs = {};
  elements.forEach((el, i) => { refs[`e${i + 1}`] = el; });
  const lines = elements.map((el, i) => {
    let s = `  e${i+1}. [${el.tag}]`;
    if (el.role) s += ` @role=${el.role}`;
    if (el.name) s += ` "${el.name}"`;
    if (el.id) s += ` #${el.id}`;
    if (el.href) s += ` →${el.href.slice(0, 40)}`;
    if (el.placeholder) s += ` placeholder="${el.placeholder}"`;
    if (el.type && el.type !== 'submit') s += ` type=${el.type}`;
    return s;
  });
  return JSON.stringify({ success: true, count: elements.length, refs: Object.fromEntries(Object.entries(refs).map(([k,v]) => [k, v.name || v.tag || v.tag])), lines });
}

async function cmdClick(ref) {
  const p = await ensureBrowser();
  const el = resolveRef(ref);
  if (!el) throw new Error(`Ref ${ref} not found. Run 'snapshot' first.`);
  await buildLocator(p, el).click();
  await p.waitForTimeout(800);
  return JSON.stringify({ success: true });
}

async function cmdFill(ref, text) {
  const p = await ensureBrowser();
  const el = resolveRef(ref);
  if (!el) throw new Error(`Ref ${ref} not found. Run 'snapshot' first.`);
  await buildLocator(p, el).fill(text);
  return JSON.stringify({ success: true });
}

async function cmdType(ref, text) {
  const p = await ensureBrowser();
  const el = resolveRef(ref);
  if (!el) throw new Error(`Ref ${ref} not found. Run 'snapshot' first.`);
  await buildLocator(p, el).type(text, { delay: 60 });
  return JSON.stringify({ success: true });
}

async function cmdPress(key) {
  const p = await ensureBrowser();
  await p.keyboard.press(key);
  return JSON.stringify({ success: true });
}

async function cmdScreenshot(filepath) {
  const p = await ensureBrowser();
  const path = filepath || `stealth-screenshot-${Date.now()}.png`;
  await p.screenshot({ path, fullPage: false });
  return JSON.stringify({ success: true, path });
}

async function cmdGet(prop, ref) {
  const p = await ensureBrowser();
  const el = resolveRef(ref);
  if (!el) throw new Error(`Ref ${ref} not found. Run 'snapshot' first.`);
  const loc = buildLocator(p, el);
  let data;
  switch (prop) {
    case 'text': data = await loc.textContent().catch(() => ''); break;
    case 'html': data = await loc.innerHTML().catch(() => ''); break;
    case 'value': data = await loc.inputValue().catch(() => ''); break;
    case 'attr': data = await loc.getAttribute('href').catch(() => ''); break;
    default: data = await loc.textContent().catch(() => '');
  }
  return JSON.stringify({ success: true, data: data?.slice(0, 500) });
}

async function cmdClose() {
  if (page) { await page.close().catch(() => {}); page = null; }
  if (browser) { await browser.close().catch(() => {}); browser = null; }
  refs = {};
  clearSession();
  return JSON.stringify({ success: true, message: 'Browser closed' });
}

async function main() {
  const [node, script, cmd, ...rawArgs] = process.argv;
  
  // Parse --continue flag
  const continueFlag = rawArgs.includes('--continue');
  const args = rawArgs.filter(a => !a.startsWith('--'));
  
  if (cmd === 'close') {
    const result = await cmdClose();
    console.log(result);
    return;
  }
  
  // Try to resume existing session
  if (continueFlag && existsSync(SESSION_FILE)) {
    try {
      browser = await chromium.connectOverCDP('http://localhost:9222');
      const targets = browser.contexts()[0]?.pages();
      if (targets && targets.length > 0) {
        page = targets[0];
      }
    } catch(e) {
      // Can't connect, start fresh
    }
  }
  
  let result;
  try {
    switch (cmd) {
      case 'open': result = await cmdOpen(args[0]); break;
      case 'snapshot': result = await cmdSnapshot(); break;
      case 'click': result = await cmdClick(args[0]); break;
      case 'fill': result = await cmdFill(args[0], args.slice(1).join(' ')); break;
      case 'type': result = await cmdType(args[0], args.slice(1).join(' ')); break;
      case 'press': result = await cmdPress(args[0]); break;
      case 'screenshot': result = await cmdScreenshot(args[0]); break;
      case 'get': result = await cmdGet(args[0], args[1]); break;
      default:
        result = JSON.stringify({
          success: false,
          usage: 'node stealth-launch.js <open|snapshot|click|fill|type|press|screenshot|get|close> [args]',
          example: 'node stealth-launch.js open https://example.com && node stealth-launch.js snapshot'
        });
    }
    console.log(result);
  } catch (err) {
    console.error(JSON.stringify({ success: false, error: err.message }));
    process.exit(1);
  }
}

main();
