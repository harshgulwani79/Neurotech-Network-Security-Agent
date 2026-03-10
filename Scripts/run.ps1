# Network Operations Center - PowerShell Startup Script
# Simply right-click this file and select "Run with PowerShell"

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "███████████████████████████████████████████████████████" -ForegroundColor Cyan
Write-Host "   Network Operations Center (NOC) Dashboard" -ForegroundColor Cyan
Write-Host "███████████████████████████████████████████████████████" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "🔍 Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found! Install from https://www.python.org" -ForegroundColor Red
    Write-Host "   Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    pause
    exit 1
}

# Install dependencies
Write-Host ""
Write-Host "📦 Installing/Updating dependencies..." -ForegroundColor Yellow
Write-Host "   (flask, flask-cors, pandas, numpy, scikit-learn, groq)" -ForegroundColor Gray

python -m pip install -q flask flask-cors pandas numpy scikit-learn groq 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    pause
    exit 1
}

# Generate data if needed
Write-Host ""
Write-Host "📊 Checking sample data..." -ForegroundColor Yellow

if (Test-Path "telemetry_stream.csv") {
    Write-Host "✅ Sample data found" -ForegroundColor Green
} else {
    Write-Host "   Generating 9,990 telemetry records..." -ForegroundColor Gray
    python generate_data.py
    Write-Host "✅ Sample data generated" -ForegroundColor Green
}

# Start server
Write-Host ""
Write-Host "███████████████████████████████████████████████████████" -ForegroundColor Cyan
Write-Host ""
Write-Host "🚀 STARTING FLASK SERVER" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Dashboard URL: http://localhost:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Open the link above in your web browser" -ForegroundColor Yellow
Write-Host ""
Write-Host "📝 Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""
Write-Host "███████████████████████████████████████████████████████" -ForegroundColor Cyan
Write-Host ""

# Run Flask
python app.py
