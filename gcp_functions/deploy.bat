@echo off
REM Deploy script for Google Cloud Functions - Windows version

echo 🚀 Deploying Crypto Trading Bot to Google Cloud Functions...

REM Check if gcloud is installed
gcloud --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ gcloud CLI not found. Please install Google Cloud SDK first.
    echo    https://cloud.google.com/sdk/docs/install
    pause
    exit /b 1
)

REM Check if .env.yaml exists
if not exist ".env.yaml" (
    echo ❌ .env.yaml file not found
    echo    Please create .env.yaml from .env.yaml.template
    pause
    exit /b 1
)

REM Check authentication
echo 🔐 Checking authentication...
for /f "tokens=*" %%i in ('gcloud config get-value project 2^>nul') do set PROJECT_ID=%%i
if "%PROJECT_ID%"=="" (
    echo ❌ Not authenticated with gcloud
    echo    Please run: gcloud auth login
    echo    Then run: gcloud config set project YOUR_PROJECT_ID
    pause  
    exit /b 1
)

echo ✅ Project ID: %PROJECT_ID%

REM Deploy function
echo 📦 Deploying function...
gcloud functions deploy crypto-trading-bot ^
  --runtime python39 ^
  --trigger-http ^
  --allow-unauthenticated ^
  --memory 512MB ^
  --timeout 540s ^
  --env-vars-file .env.yaml ^
  --region asia-southeast1 ^
  --entry-point crypto_trading_main

if %errorlevel% equ 0 (
    echo ✅ Function deployed successfully!
    
    REM Get trigger URL
    for /f "tokens=*" %%i in ('gcloud functions describe crypto-trading-bot --region=asia-southeast1 --format="value(httpsTrigger.url)"') do set TRIGGER_URL=%%i
    echo 🔗 Function URL: %TRIGGER_URL%
    
    echo.
    echo 🧪 Test your function:
    echo curl -X POST %TRIGGER_URL% -H "Content-Type: application/json" -d "{\"action\": \"get_balance\"}"
    
    echo.
    echo ⏰ Next steps:
    echo 1. Setup Cloud Scheduler with URL: %TRIGGER_URL%
    echo 2. Monitor function logs in GCP Console
    echo 3. Check Firestore for trading data
) else (
    echo ❌ Deployment failed!
)

pause
