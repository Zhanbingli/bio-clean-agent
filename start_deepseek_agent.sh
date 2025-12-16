#!/bin/bash
# Quick start script for DeepSeek-powered Bio Clean Agent

echo "🧬 Bio Clean Agent - DeepSeek Edition"
echo "======================================"
echo ""

# Check if API key is set
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "⚠️  DEEPSEEK_API_KEY not found!"
    echo ""
    echo "Please set your DeepSeek API key first:"
    echo "  export DEEPSEEK_API_KEY='sk-your-key-here'"
    echo ""
    echo "Get your key at: https://platform.deepseek.com"
    echo ""
    echo "Tip: run rule-based mode without LLM if you prefer offline:"
    echo "  python bio-clean-cli.py --no-llm"
    exit 1
fi

# Check dependencies
echo "Checking dependencies..."
python - <<'PY'
missing = []
for pkg in ("openai", "rich"):
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)

if missing:
    print("Missing packages: %s" % ", ".join(missing))
    print("Install them with: pip install -e .[openai]")
    raise SystemExit(1)
print("✓ Dependencies ready")
PY

# Start the agent
echo ""
echo "🚀 Starting DeepSeek-powered AI Agent..."
echo ""
python -m bio_clean_agent.cli chat --model deepseek "$@"
