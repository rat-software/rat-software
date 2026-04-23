#!/bin/bash
# RAT Sources Scraper - Setup Script

echo "🔧 Starting setup for RAT ..."

# 1. Setup Virtual Environment
echo "🐍 Creating virtual environment..."
python3 -m venv venv_rat
source venv_rat/bin/activate

# 2. Install Dependencies
echo "📦 Installing packages..."
pip install --upgrade pip
pip install -r requirements_rat.txt

echo "✅ Setup complete! Use 'source venv_rat/bin/activate' to start."
echo "Or deploy a RAT service (see README.md)."