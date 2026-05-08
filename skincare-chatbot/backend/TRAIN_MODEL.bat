@echo off
REM Train XGBoost Skin Model with Real or Synthetic Data
REM Navigate to backend and run training

echo ========================================
echo XGBoost Skin Model Training
echo ========================================
echo.

cd /d "%~dp0skincare-chatbot\backend"

if not exist "model\train_xgboost_model.py" (
    echo Error: Training script not found
    cd /d "%~dp0"
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -q xgboost scikit-learn pandas joblib numpy opencv-python 2>nul

echo.
echo Starting training...
python -m model.train_xgboost_model

cd /d "%~dp0"
echo.
echo Training complete!
pause
