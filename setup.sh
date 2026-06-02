#!/bin/bash
# RAT - Setup Script

echo "🔧 Starting setup for RAT ..."

# 1. Check if Python 3.12 is installed
if ! command -v python3.12 &> /dev/null; then
    echo "❌ Python 3.12 is not installed."
    echo "Please install it first."
    echo "On Ubuntu/Debian, you can typically use:"
    echo "  sudo apt update && sudo apt install python3.12 python3.12-venv"
    exit 1
else
    echo "✅ Python 3.12 found."
fi

# 2. Setup Virtual Environment
echo "🐍 Creating virtual environment..."
python3.12 -m venv venv_rat
source venv_rat/bin/activate

# 3. Install Dependencies
echo "📦 Installing packages..."
pip install --upgrade pip
pip install -r requirements_rat.txt

echo "✅ Setup complete! Use 'source venv_rat/bin/activate' to start."
echo "Next, you can deploy a RAT modules as services (see README.md)."