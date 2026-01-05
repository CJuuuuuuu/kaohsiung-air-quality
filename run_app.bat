@echo off
chcp 65001 >nul
cls
echo ========================================
echo 高雄新市鎮空氣污染分析系統
echo Kaohsiung Air Quality Analysis System
echo ========================================
echo.

REM 檢查 Python 是否安裝
echo [1/3] 檢查 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 找不到 Python
    echo.
    echo 請先安裝 Python 3.8 或以上版本
    echo 下載網址: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo [成功] Python 已安裝
echo.

REM 檢查 Streamlit
echo [2/3] 檢查 Streamlit...
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo [警告] 找不到 Streamlit，正在安裝...
    pip install streamlit pandas numpy matplotlib scipy contextily pillow
    echo.
)
echo [成功] Streamlit 已安裝
echo.

REM 啟動應用程式
echo [3/3] 啟動系統...
echo ========================================
echo 系統啟動中，請稍候...
echo 瀏覽器將自動開啟
echo 若未開啟請手動前往: http://localhost:8501
echo.
echo 關閉此視窗將停止系統
echo ========================================
echo.

REM 使用 python -m streamlit 而不是直接呼叫 streamlit
python -m streamlit run app.py

echo.
echo 系統已關閉
pause
