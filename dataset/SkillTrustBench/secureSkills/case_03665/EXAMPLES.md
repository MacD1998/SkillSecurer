# agent-browser-stealth Examples

## Quick Start

```bash
# Open a site and get interactive elements
node scripts/stealth-launch.js open https://example.com

# Screenshot
node scripts/stealth-launch.js screenshot
```

## Full Workflow

```bash
# 1. Open target site
node scripts/stealth-launch.js open https://github.com/login

# 2. See all interactive elements (with refs)
node scripts/stealth-launch.js snapshot
# → e1 [input] "Username or email address" placeholder="Username or email address"
# → e2 [input] type=password placeholder="Password"
# → e3 [button] "Sign in"

# 3. Interact
node scripts/stealth-launch.js fill e1 "myuser"
node scripts/stealth-launch.js fill e2 "mypassword"
node scripts/stealth-launch.js click e3

# 4. Verify
node scripts/stealth-launch.js screenshot

# 5. Close
node scripts/stealth-launch.js close
```

## Login with Session Persistence

```bash
# After logging in once, save the auth state:
# (Create a session-persist script that calls storageState)

# On next run, load saved session to skip login:
# See SKILL.md → Session Persistence section
```

## Anti-Detection Testing

```bash
node scripts/stealth-launch.js open https://bot.sannysoft.com
node scripts/stealth-launch.js snapshot
# All rows should show green = undetected
```

## Stealth vs Plain agent-browser

| Feature | agent-browser | agent-browser-stealth |
|---------|--------------|---------------------|
| navigator.webdriver | Exposed | ✅ Hidden |
| Canvas fingerprint | Real | ✅ Spoofed |
| WebGL vendor/renderer | Real | ✅ Spoofed |
| Permissions API | Real | ✅ Returns granted |
| Automation headers | Present | ✅ Stripped |
| CSS automation flags | Present | ✅ Hidden |
| Session isolation | ✅ | ✅ |
| CDP-based | ✅ | ✅ |

## Installation Verification

```bash
# Verify stealth is working:
node scripts/stealth-launch.js open https://browserleaks.com/canvas
node scripts/stealth-launch.js screenshot
# Check screenshot — canvas fingerprint should show Intel, not real GPU
```
