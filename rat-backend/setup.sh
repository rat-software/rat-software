#!/bin/bash
# RAT Unified Backend - Setup Script

echo "🔧 Starting setup for the RAT Unified Backend..."


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

# 2. System Dependencies (mostly for the Scraper)
echo "📦 Installing system dependencies..."
sudo apt update
sudo apt install -y chromium-browser chromium-chromedriver python3-venv python3-psutil

# 3. Setup Unified Virtual Environment
echo "🐍 Creating virtual environment (venv_rat_backend)..."
python3 -m venv venv_rat_backend
source venv_rat_backend/bin/activate

# 4. Install All Backend Dependencies
echo "📦 Installing combined requirements..."
pip install --upgrade pip
# This assumes you have a unified requirements.txt in the backend root
pip install -r requirements_rat_backend.txt

echo ""
echo "✅ Unified Backend Setup complete!"
echo "-------------------------------------------------------"
echo "Next steps:"
echo "1. Configure 'config/config_db.ini' and 'config/config_sources.ini'."
echo "2. Add your 'google-ads.yaml' to the 'query_sampler/' folder."
echo "3. Start all services: 'nohup python backend_controller_start.py &'"
echo "-------------------------------------------------------"