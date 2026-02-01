#!/bin/bash
set -e
echo "Building for macOS..."
cd frontend && npm install && npm run build && cd ..
cd backend && pip install -r requirements.txt && pyinstaller --onefile run.py && cd ..
npm install && npm run electron:build
echo "Complete!"
