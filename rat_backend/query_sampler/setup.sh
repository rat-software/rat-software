#!/bin/bash
# RAT Storage Service - Setup Script

echo "🔧 Starting setup for RAT Query Sampler..."

# 1. Setup Virtual Environment
echo "🐍 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 2. Install Dependencies
echo "📦 Installing packages..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Setup complete! Use 'source venv/bin/activate' to start."