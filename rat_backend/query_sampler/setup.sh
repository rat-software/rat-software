#!/bin/bash
# RAT Query Sampler - Setup Script

echo "🔧 Starting setup for RAT Query Sampler..."

# 1. Setup Virtual Environment
echo "🐍 Creating virtual environment..."
python3 -m venv venv_query_sampler
source venv_query_sampler/bin/activate

# 2. Install Dependencies
echo "📦 Installing packages..."
pip install --upgrade pip
pip install -r requirements_rat_query_sampler.txt

echo "✅ Setup complete! Use 'source venv_query_sampler/bin/activate' to start."