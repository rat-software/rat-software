#!/bin/bash
# RAT Sources Scraper - Setup Script

echo "🔧 Starting setup for RAT Sources Scraper..."

# 1. Setup Virtual Environment
echo "🐍 Creating virtual environment..."
python -m venv venv_sources
source venv_sources/bin/activate

# 2. Install Dependencies
echo "📦 Installing packages..."
pip install --upgrade pip
pip install -r requirements_rat_sources.txt

echo "✅ Setup complete! Use 'source venv_sources/bin/activate' to start."