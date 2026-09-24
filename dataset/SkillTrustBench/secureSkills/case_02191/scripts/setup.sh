#!/bin/bash
# visa-itinerary-gen setup script
# Automatically installs all dependencies

set -e

echo "=== visa-itinerary-gen setup ==="
echo ""

# 1. Check node
if ! command -v node &> /dev/null; then
  echo "ERROR: Node.js is required. Install from https://nodejs.org/"
  exit 1
fi
echo "✓ Node.js found"

# 2. Check/install flyai-cli
if ! command -v flyai &> /dev/null; then
  echo "Installing flyai-cli..."
  npm i -g @fly-ai/flyai-cli
fi
echo "✓ flyai-cli ready"

# 3. Check/install flyai skill
if [ ! -d "$HOME/.claude/skills/flyai" ]; then
  echo ""
  echo "flyai skill not found. Please install it first:"
  echo "  clawhub install flyai"
  echo "  or: npx skills add alibaba-flyai/flyai-skill"
  echo ""
  echo "After installing flyai, run this setup again."
  exit 1
fi
echo "✓ flyai skill found"

# 4. Install Python dependencies (playwright for PDF generation)
if ! python3 -c "import playwright" &> /dev/null 2>&1; then
  echo "Installing playwright..."
  pip3 install playwright -q
  python3 -m playwright install chromium
fi
echo "✓ playwright + chromium ready"

# 5. Verify flyai works
echo ""
echo "Verifying flyai..."
flyai fliggy-fast-search --query "test" > /dev/null 2>&1 && echo "✓ flyai verified" || echo "⚠ flyai returned error (may still work)"

echo ""
echo "=== Setup complete ==="
echo ""
echo "Usage: Ask your AI assistant:"
echo '  "帮我生成一份签证行程单，4个人4月底从杭州去意大利和法国"'
echo ""
