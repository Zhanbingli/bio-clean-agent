#!/bin/bash
# Quick start script for DeepSeek-powered Bio Clean Agent

echo "🧬 Bio Clean Agent - DeepSeek Edition"
echo "======================================"
echo ""

# Check if API key is set
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "⚠️  DEEPSEEK_API_KEY not found!"
    echo ""
    echo "Please set your DeepSeek API key:"
    echo "  export DEEPSEEK_API_KEY='sk-your-key-here'"
    echo ""
    echo "Get your key at: https://platform.deepseek.com"
    echo ""
    read -p "Enter your DeepSeek API key (or press Enter to skip): " key

    if [ ! -z "$key" ]; then
        export DEEPSEEK_API_KEY="$key"
        echo "✓ API key set for this session"
        echo ""
    else
        echo "Starting in rule-based mode (no LLM)..."
        python bio-clean-cli.py --no-llm
        exit 0
    fi
fi

# Check dependencies
echo "Checking dependencies..."
python -c "import openai" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing openai package..."
    pip install openai -q
fi

python -c "import rich" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing rich package..."
    pip install rich -q
fi

echo "✓ Dependencies ready"
echo ""

# Start the agent
echo "🚀 Starting DeepSeek-powered AI Agent..."
echo ""
python bio-clean-cli.py --llm deepseek
