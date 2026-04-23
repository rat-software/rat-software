#!/bin/bash
# RAT Frontend - Setup Script

echo "🔧 Starting setup for RAT Frontend..."

# 1. Create temporary upload directory
# This matches the path used in study.py for CSV/ZIP processing
echo "📁 Preparing temporary upload directories..."
mkdir -p app/static/tmp_uploads
chmod -R 775 app/static/tmp_uploads

# 2. Setup Virtual Environment
echo "🐍 Creating virtual environment (venv_rat_frontend)..."
python3 -m venv venv_rat_frontend
source venv_rat_frontend/bin/activate

# 3. Install Dependencies
echo "📦 Installing packages..."
pip install --upgrade pip
if [ -f "requirements_rat_frontend.txt" ]; then
    pip install -r requirements_rat_frontend.txt
else
    echo "⚠️ requirements.txt not found. Skipping package installation."
fi

echo ""
echo "✅ Setup complete!"
echo "-------------------------------------------------------"
echo "Next steps:"
echo "1. Edit 'config.py' with your database and API credentials."
echo "2. Run 'source venv_rat_frontend/bin/activate'"
echo "3. Initialize the database with 'export FLASK_APP=rat.py && flask db upgrade'"
echo "-------------------------------------------------------"