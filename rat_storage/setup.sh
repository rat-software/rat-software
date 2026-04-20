#!/bin/bash
# RAT Storage Service - Setup Script

echo "🔧 Starting setup for RAT Storage Service..."

# 1. Create storage directory and set permissions
echo "📁 Setting up storage directory..."
sudo mkdir -p /var/www/rat/storage/sources/
sudo chown -R $USER:www-data /var/www/rat/storage/
sudo chmod -R 775 /var/www/rat/storage/

# 2. Setup Virtual Environment
echo "🐍 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 3. Install Dependencies
echo "📦 Installing packages..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Setup complete! Use 'source venv/bin/activate' to start."