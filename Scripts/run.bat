@echo off
title Network Operations Center - Startup

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║   Network Operations Center ^(NOC^) - Startup Script        ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org
    pause
    exit /b 1
)

echo ✅ Python detected
echo.

REM Check if required files exist
if not exist "generate_data.py" (
    echo ❌ Error: generate_data.py not found
    pause
    exit /b 1
)

if not exist "app.py" (
    echo ❌ Error: app.py not found
    pause
    exit /b 1
)

if not exist "templates\dashboard.html" (
    echo ❌ Error: templates\dashboard.html not found
    pause
    exit /b 1
)

echo ✅ All required files found
echo.

REM Install dependencies
echo 📦 Installing/Updating dependencies...
echo This may take a minute on first run...
echo.
python -m pip install -q flask flask-cors pandas numpy scikit-learn groq
if errorlevel 1 (
    echo ❌ Error installing dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed
echo.

REM Generate sample data if not exists
if not exist "telemetry_stream.csv" (
    echo 📊 Generating sample telemetry data ^(9,990 records^)...
    python generate_data.py
    if errorlevel 1 (
        echo ❌ Error generating data
        pause
        exit /b 1
    )
    echo ✅ Data generated successfully
) else (
    echo ℹ️  Using existing telemetry_stream.csv
)

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║   🚀 Starting Flask Server...                              ║
echo ║                                                            ║
echo ║   🌐 Dashboard: http://localhost:5000                      ║
echo ║   📂 Open dashboard at the URL above in your browser       ║
echo ║                                                            ║
echo ║   Press Ctrl+C to stop the server                         ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

python app.py

