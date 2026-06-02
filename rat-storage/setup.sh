#!/bin/bash
# RAT Storage Service - Setup Script

echo "🔧 Starting setup for RAT Storage Service..."

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

# 2. Create storage directory (using sudo only where needed)
echo "📁 Setting up storage directory..."
sudo mkdir -p /var/www/rat/storage/sources/
sudo chown -R $USER:www-data /var/www/rat/storage/
sudo chmod -R 775 /var/www/rat/storage/

# 3. Setup Virtual Environment
echo "🐍 Creating virtual environment..."
python3.12 -m venv venv_rat_storage

# 4. Install Dependencies
echo "📦 Installing packages..."
# Use the direct path to the venv python to ensure it doesn't use system python
./venv_rat_storage/bin/pip install --upgrade pip
./venv_rat_storage/bin/pip install -r requirements_rat_storage.txt

echo "✅ Setup complete! Use 'source venv_rat_storage/bin/activate' to start."