---
name: agent-browser-stealth
description: Stealth browser automation with anti-detection. Launches Chromium with fingerprint randomization, webdriver flag removal, Canvas/WebGL spoofing, and permissions API masking. Use for web scraping, login automation, and session persistence on bot-protected sites. Triggers on "stealth browser", "anti-detection", "undetectable browser", "hide automation", "stealth login", "bot protection bypass".
metadata: {"openclaw":{"emoji":"🎭","os":["darwin","linux","win32"]}}
---

# agent-browser-stealth

Anti-detection browser automation built on Playwright. Launches Chromium with layered stealth to evade bot detection on protected sites.

## Architecture

```
agent-browser-stealth
└── stealth-launch.js    # Playwright + CDP stealth wrapper
    ├── Removes navigator.webdriver
    ├── Spoofs Canvas/WebGL fingerprints
    ├── Masks chrome.runtime
    ├── Patches Permissions API
    ├── Hides automation CSS flags
    └── Preserves full Playwright functionality
```

## Commands

```bash
# Launch and navigate
node scripts/stealth-launch.js open https://example.com

# Get interactive elements (ref-based)
node scripts/stealth-launch.js snapshot
# → Returns refs e1, e2, e3... with element metadata

# Interact
node scripts/stealth-launch.js click e3
node scripts/stealth-launch.js fill e2 "text to fill"
node scripts/stealth-launch.js type e2 "typed slowly"
node scripts/stealth-launch.js press Enter

# Inspect
node scripts/stealth-launch.js screenshot [path]
node scripts/stealth-launch.js get text e1
node scripts/stealth-launch.js get attr e5 href
node scripts/stealth-launch.js get value e2

# Close
node scripts/stealth-launch.js close
```

## Snapshot Refs

`snapshot` returns numbered refs (`e1`, `e2`, ...) — use these for subsequent interactions:

```
1. [a] "Sign In" → /login
2. [input] placeholder="Email"
3. [input] type=password
4. [button] "Submit"
```

Then:
```bash
node scripts/stealth-launch.js click e1    # click Sign In
node scripts/stealth-launch.js fill e2 "user@example.com"
node scripts/stealth-launch.js fill e3 "password"
node scripts/stealth-launch.js click e4      # Submit
```

## Stealth Layers

| Layer | Technique |
|-------|-----------|
| WebDriver Flag | `Object.defineProperty(navigator, 'webdriver', { get: () => undefined })` |
| Chrome Runtime | `chrome.runtime` nullified |
| Canvas Fingerprint | `getImageData` returns noise instead of real data |
| WebGL Vendor/Renderer | Spoofed to Intel Iris OpenGL Engine |
| Permissions API | Returns `granted` for notifications/geolocation |
| getComputedStyle | Animations/transition stripped |
| Viewport | Randomized within 1280-1330 × 900-950 |

## Installation

```bash
npm install -g playwright
npx playwright install chromium
```

The skill uses Playwright as a local dependency via `npx` — no global install of stealth plugins needed.

## Session Persistence

For login persistence, use Playwright's built-in storageState:

```javascript
// In scripts/stealth-session.js — save auth after login
import { chromium } from 'playwright';

const browser = await chromium.launch({ 
  headless: true,
  args: ['--disable-blink-features=AutomationControlled', '--no-sandbox']
});
const page = await browser.newPage();
// ... perform login ...
await page.context().storageState({ path: 'auth.json' });
// Next run:
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ storageState: 'auth.json' });
```

## Anti-Detection Testing

Test stealth effectiveness:
```bash
node scripts/stealth-launch.js open https://bot.sannysoft.com
node scripts/stealth-launch.js snapshot
# All checks should show green/undetected
```

## Limitations

- Cloudflare JS Challenge: May require headed mode + manual solve
- CAPTCHAs: Requires external solver (2Captcha, etc.) — not built in
- Very aggressive sites: May need proxy rotation (residential proxies)

## Examples

### Login to a Protected Site

```bash
node scripts/stealth-launch.js open https://target-site.com/login
node scripts/stealth-launch.js snapshot
node scripts/stealth-launch.js fill e1 "email@example.com"
node scripts/stealth-launch.js fill e2 "password"
node scripts/stealth-launch.js click e3
node scripts/stealth-launch.js screenshot
node scripts/stealth-launch.js close
```

### Scrape Dynamic Content

```bash
node scripts/stealth-launch.js open https://news.site.com
node scripts/stealth-launch.js snapshot
# Identify article refs, then extract
node scripts/stealth-launch.js get html e5
node scripts/stealth-launch.js close
```

### Stealth vs agent-browser

| Feature | agent-browser | agent-browser-stealth |
|---------|--------------|-----------------------|
| Anti-detection | ❌ None | ✅ 8 layers |
| Fingerprint spoofing | ❌ None | ✅ Canvas + WebGL |
| CDP-based | ✅ Native Rust | ✅ Playwright |
| Session isolation | ✅ | ✅ |
| Complexity | Lightweight | Slightly heavier |
| Best for | General automation | Protected sites |
