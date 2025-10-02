#!/bin/bash
# Demo script to show the Bio Clean Agent capabilities

echo "========================================="
echo "🧬 Bio Clean Agent Demo"
echo "========================================="
echo ""

echo "1. Available Models:"
bio-clean-agent models
echo ""

echo "2. Viewing Example Configuration:"
cat examples/configs/example.yaml
echo ""

echo "3. Running Pipeline in Dry-Run Mode:"
bio-clean-agent run examples/configs/example.yaml --dry-run
echo ""

echo "========================================="
echo "✅ Demo Complete!"
echo ""
echo "Try these commands:"
echo "  bio-clean-agent chat --dry-run"
echo "  bio-clean-agent init /path/to/your/data"
echo "========================================="
