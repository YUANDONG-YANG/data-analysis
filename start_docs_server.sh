#!/bin/bash

echo "========================================"
echo "📚 Documentation Server Launcher"
echo "========================================"
echo ""

# Check if markdown is installed
python3 -c "import markdown" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  markdown library not installed, installing..."
    pip3 install markdown>=3.4.0
    echo ""
fi

echo "🚀 Starting server..."
echo ""
python3 docs_server.py
