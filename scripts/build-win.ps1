Write-Host "Building for Windows..."
Set-Location frontend; npm install; npm run build; Set-Location ..
Set-Location backend
python -m venv venv 2>$null
& .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --onefile run.py
deactivate
Set-Location ..
npm install; npm run electron:build
Write-Host "Complete!"
