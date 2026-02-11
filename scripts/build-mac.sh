#!/bin/bash
set -e
echo "Building for macOS..."
cd frontend && npm install && npm run build && cd ..
cd backend
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --onefile run.py
deactivate
cd ..
npm install && npm run electron:build
echo "Complete!"
