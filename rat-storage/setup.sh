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
python -m venv venv_rat_stoarge
source venv_rat_stoarge/bin/activate

# 3. Install Dependencies
echo "📦 Installing packages..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Setup complete! Use 'source venv_rat_stoarge/bin/activate' to start."