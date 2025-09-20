#!/bin/bash
# Code Quality Check Script for Financial Document Analyzer

echo "🔍 Running Code Quality Assessment..."
echo "================================="

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

echo ""
echo "📋 Running PEP 8 Style Check (flake8)..."
echo "----------------------------------------"
if command -v flake8 &> /dev/null; then
    flake8 --config .flake8 main.py agents.py task.py tools.py
    if [ $? -eq 0 ]; then
        echo "✅ All PEP 8 style checks passed!"
    else
        echo "❌ PEP 8 style violations found"
    fi
else
    echo "⚠️  flake8 not installed. Install with: pip install flake8"
fi

echo ""
echo "🔒 Running Security Check (bandit)..."
echo "-------------------------------------"
if command -v bandit &> /dev/null; then
    bandit -r . --exclude ./venv -ll
    if [ $? -eq 0 ]; then
        echo "✅ No high-severity security issues found!"
    else
        echo "⚠️  Security issues detected - review above"
    fi
else
    echo "⚠️  bandit not installed. Install with: pip install bandit"
fi

echo ""
echo "🏗️  Running Code Quality Check (pylint)..."
echo "------------------------------------------"
if command -v pylint &> /dev/null; then
    pylint --max-line-length=120 --disable=C0114,C0115,C0116,E0401 main.py agents.py task.py tools.py
    echo "Code quality check completed."
else
    echo "⚠️  pylint not installed. Install with: pip install pylint"
fi

echo ""
echo "✅ Code quality assessment completed!"
echo "📊 Check the output above for any issues that need attention."