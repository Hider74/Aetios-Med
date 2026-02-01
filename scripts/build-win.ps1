Write-Host "Building for Windows..."
Set-Location frontend; npm install; npm run build; Set-Location ..
Set-Location backend; pip install -r requirements.txt; pyinstaller --onefile run.py; Set-Location ..
npm install; npm run electron:build
Write-Host "Complete!"
