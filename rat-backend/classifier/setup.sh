#!/bin/bash
# RAT Classifier - Setup Script

echo "🔧 Starting setup for RAT Classifier..."

# 1. Setup Virtual Environment
echo "🐍 Creating virtual environment..."
python -m venv venv_classifier
source venv_classifier/bin/activate

# 2. Install Dependencies
echo "📦 Installing packages..."
pip install --upgrade pip
pip install -r requirements_rat_classifier.txt

echo "✅ Setup complete! Use 'source venv_classifier/bin/activate' to start."

echo ""
echo "✅ Classifier Setup complete!"
echo "-------------------------------------------------------"
echo "Next steps:"
echo "1. Place your classification modules in the 'classifiers/' directory."
echo "2. Ensure 'config/config_db.ini' and 'config/config_sources.ini' are configured."
echo "3. Start the module: 'python classifier_controller_start.py'."
echo "-------------------------------------------------------"