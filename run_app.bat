@echo off
chcp 65001 >nul
cls
echo ========================================
echo 高雄新市鎮空氣污染分析系統
echo Kaohsiung Air Quality Analysis System
echo ========================================
echo.

REM 啟用延遲變數展開
setlocal enabledelayedexpansion

REM 設定 Python 可執行檔變數
set PYTHON_CMD=
set PYTHON_FOUND=0

echo [1/3] 搜尋 Python 3.8...

REM 1. 先檢查 python 指令
python --version >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do (
        echo 檢查 python 指令: %%i
        echo %%i | findstr "3\.8\." >nul
        if not errorlevel 1 (
            echo [找到] Python 3.8: %%i ^(指令: python^)
            set PYTHON_CMD=python
            set PYTHON_FOUND=1
            goto :python_found
        ) else (
            echo [跳過] %%i 不是 Python 3.8
        )
    )
)

REM 2. 檢查 python3 指令
python3 --version >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=2" %%i in ('python3 --version 2^>^&1') do (
        echo 檢查 python3 指令: %%i
        echo %%i | findstr "3\.8\." >nul
        if not errorlevel 1 (
            echo [找到] Python 3.8: %%i ^(指令: python3^)
            set PYTHON_CMD=python3
            set PYTHON_FOUND=1
            goto :python_found
        ) else (
            echo [跳過] %%i 不是 Python 3.8
        )
    )
)

REM 3. 檢查 py launcher 的 3.8 版本
py -3.8 --version >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=2" %%i in ('py -3.8 --version 2^>^&1') do (
        echo [找到] Python 3.8: %%i ^(指令: py -3.8^)
        set PYTHON_CMD=py -3.8
        set PYTHON_FOUND=1
        goto :python_found
    )
)

REM 4. 檢查常見的 Python 3.8 安裝路徑
echo 在常見路徑中搜尋 Python 3.8...
for %%P in (
    "C:\Python38\python.exe"
    "C:\Python38-32\python.exe"
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python38\python.exe"
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python38-32\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python38\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python38-32\python.exe"
    "%PROGRAMFILES%\Python38\python.exe"
    "%PROGRAMFILES(X86)%\Python38\python.exe"
) do (
    if exist %%P (
        for /f "tokens=2" %%i in ('%%P --version 2^>^&1') do (
            echo 檢查路徑 %%P: %%i
            echo %%i | findstr "3\.8\." >nul
            if not errorlevel 1 (
                echo [找到] Python 3.8: %%i ^(路徑: %%P^)
                set PYTHON_CMD=%%P
                set PYTHON_FOUND=1
                goto :python_found
            ) else (
                echo [跳過] %%i 不是 Python 3.8
            )
        )
    )
)

REM 如果都找不到 Python 3.8，顯示錯誤訊息
echo.
echo [錯誤] 找不到 Python 3.8
echo.
echo *** 重要提醒 ***
echo 本系統僅支援 Python 3.8.x 版本
echo 其他版本（如 3.9, 3.10, 3.11 等）可能無法正常運作
echo.
echo 請下載並安裝 Python 3.8：
echo https://www.python.org/downloads/release/python-3812/
echo.
echo 安裝時請記得：
echo 1. 勾選 "Add Python to PATH"
echo 2. 選擇 "Install for all users" ^(建議^)
echo.
pause
exit /b 1

:python_found
if !PYTHON_FOUND! equ 0 (
    goto :eof
)

echo [成功] 將使用 Python 3.8: !PYTHON_CMD!
echo.

REM 顯示完整版本資訊
!PYTHON_CMD! --version
echo.

REM 檢查 Streamlit 和其他必要套件
echo [2/3] 檢查必要套件...
!PYTHON_CMD! -c "import streamlit, pandas, numpy, matplotlib, scipy" >nul 2>&1
if errorlevel 1 (
    echo [安裝] 找不到必要套件，正在安裝...
    echo.
    echo 正在安裝: streamlit pandas numpy matplotlib scipy contextily pillow
    echo 請稍候，這可能需要幾分鐘...
    echo.
    
    REM 先升級 pip
    !PYTHON_CMD! -m pip install --upgrade pip
    
    REM 安裝套件
    !PYTHON_CMD! -m pip install streamlit pandas numpy matplotlib scipy contextily pillow
    
    if errorlevel 1 (
        echo.
        echo [錯誤] 套件安裝失敗
        echo.
        echo 請嘗試手動安裝：
        echo !PYTHON_CMD! -m pip install streamlit pandas numpy matplotlib scipy contextily pillow
        echo.
        echo 或檢查：
        echo 1. 網路連線是否正常
        echo 2. Python 3.8 是否正確安裝
        echo 3. pip 是否可正常使用
        pause
        exit /b 1
    )
    echo.
    echo [成功] 套件安裝完成
) else (
    echo [成功] 所有必要套件已安裝
)
echo.

REM 檢查資料目錄和檔案
echo [檢查] 驗證資料檔案...
if not exist "data" (
    echo [警告] 找不到 data 資料夾
    echo.
    echo 請先建立 data 資料夾並下載必要檔案：
    echo https://drive.google.com/drive/folders/1ak6yl8A6AlYswMBxFxrKyeyh3iU-YXUA
    echo.
    echo 是否仍要繼續啟動系統？ ^(可能會出現錯誤^)
    set /p choice=請輸入 Y 繼續或 N 取消: 
    if /i not "!choice!"=="Y" (
        echo 已取消啟動
        pause
        exit /b 0
    )
) else (
    REM 檢查是否有必要的 CSV 檔案
    dir /b "data\kaohsiung_airbox_hourly_with_wind*.csv" >nul 2>&1
    if errorlevel 1 (
        echo [警告] data 資料夾中找不到空污資料檔案
        echo 請確認已下載 kaohsiung_airbox_hourly_with_wind_*.csv 檔案
        echo.
    ) else (
        echo [成功] 找到空污資料檔案
    )
    
    if exist "data\Kaohsiung_iot_station.csv" (
        echo [成功] 找到測站座標檔案
    ) else (
        echo [警告] 找不到測站座標檔案 Kaohsiung_iot_station.csv
    )
)
echo.

REM 啟動應用程式
echo [3/3] 啟動系統...
echo ========================================
echo 系統啟動中，請稍候...
echo.
echo 使用 Python 版本: 
!PYTHON_CMD! --version
echo.
echo 瀏覽器將自動開啟 http://localhost:8501
echo 若未自動開啟，請手動前往上述網址
echo.
echo *** 重要提醒 ***
echo - 關閉此視窗將停止系統
echo - 如需停止系統，請按 Ctrl+C
echo ========================================
echo.

REM 啟動 Streamlit
!PYTHON_CMD! -m streamlit run app.py --server.headless true --server.port 8501

echo.
echo 系統已關閉
pause
