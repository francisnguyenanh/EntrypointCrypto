@echo off
REM Cleanup script - Remove unnecessary files to reduce project size

echo 🧹 Cleaning up unnecessary files...

REM Remove __pycache__ directories
echo Removing Python cache...
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "lambda_version\__pycache__" rmdir /s /q "lambda_version\__pycache__"

REM Remove .pyc files
echo Removing .pyc files...
del /s /q *.pyc 2>nul

REM Remove log files
echo Removing log files...
del /q *.log 2>nul
del /q trading_log.txt 2>nul

REM Remove temporary files
echo Removing temporary files...
del /q *.tmp 2>nul
del /q *.temp 2>nul

REM Remove large documentation files that aren't needed for deployment
echo Removing large documentation files...
del /q EMAIL_ISSUE_RESOLVED.md 2>nul
del /q FINAL_SUMMARY.py 2>nul
del /q LIQUIDITY_DOCS.md 2>nul
del /q OPTIMIZATION_COMPLETE.md 2>nul

REM Remove lambda_version directory if it exists (we're using gcp_functions now)
if exist "lambda_version" (
    echo Removing old lambda_version directory...
    rmdir /s /q "lambda_version"
)

REM Remove build artifacts
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.egg-info" rmdir /s /q "*.egg-info"

REM Remove IDE files
if exist ".vscode" rmdir /s /q ".vscode"
if exist ".idea" rmdir /s /q ".idea"

echo ✅ Cleanup completed!
echo 📁 Remaining files for GCP deployment:
echo    - gcp_functions/ (deployment files)
echo    - app.py (original reference)
echo    - trading_config.py (reference config)
echo    - requirements.txt (original requirements)

pause
