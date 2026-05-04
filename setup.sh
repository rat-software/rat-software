#!/bin/bash
# RAT - Setup Script

echo "🔧 Starting setup for RAT ..."

# 1. Setup Virtual Environment
echo "🐍 Creating virtual environment..."
python -m venv venv_rat
source venv_rat/bin/activate

# 2. Install Dependencies
echo "📦 Installing packages..."
pip install --upgrade pip
pip install -r requirements_rat.txt

echo "✅ Setup complete! Use 'source venv_rat/bin/activate' to start."
echo "Next, you can deploy a RAT modules as services (see README.md)."