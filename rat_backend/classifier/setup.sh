#!/bin/bash
# RAT Classifier - Setup Script

echo "🔧 Starting setup for RAT Classifier..."

# 1. Setup Virtual Environment
echo "🐍 Creating virtual environment (venv_classifier)..."
python3 -m venv venv_classifier
source venv_classifier/bin/activate

# 2. Install Dependencies
echo "📦 Installing packages..."
pip install --upgrade pip
pip install sqlalchemy psycopg2-binary apscheduler beautifulsoup4 lxml requests psutil

echo ""
echo "✅ Classifier Setup complete!"
echo "-------------------------------------------------------"
echo "Next steps:"
echo "1. Place your classification modules in the 'classifiers/' directory."
echo "2. Ensure 'config/config_db.ini' and 'config/config_sources.ini' are configured."
echo "3. Start the module: 'python classifier_controller_start.py'."
echo "-------------------------------------------------------"