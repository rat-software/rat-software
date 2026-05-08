#!/bin/bash
# RAT Storage Service - Setup Script

echo "🔧 Starting setup for RAT Storage Service..."

# 1. Create storage directory (using sudo only where needed)
echo "📁 Setting up storage directory..."
sudo mkdir -p /var/www/rat/storage/sources/
sudo chown -R $USER:www-data /var/www/rat/storage/
sudo chmod -R 775 /var/www/rat/storage/

# 2. Setup Virtual Environment
echo "🐍 Creating virtual environment..."
python3 -m venv venv_rat_storage

# 3. Install Dependencies
echo "📦 Installing packages..."
# Use the direct path to the venv python to ensure it doesn't use system python
./venv_rat_storage/bin/pip install --upgrade pip
./venv_rat_storage/bin/pip install -r requirements_rat_storage.txt

echo "✅ Setup complete! Use 'source venv_rat_storage/bin/activate' to start."