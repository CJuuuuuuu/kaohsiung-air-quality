#!/bin/bash

echo "========================================"
echo "高雄新市鎮空氣污染分析系統"
echo "Kaohsiung Air Quality Analysis System"
echo "========================================"
echo ""
echo "正在啟動系統..."
echo ""

# 檢查 Python 是否安裝
if ! command -v python3 &> /dev/null; then
    echo "[錯誤] 找不到 Python，請先安裝 Python 3.8 或以上版本"
    exit 1
fi

# 檢查 Streamlit 是否安裝
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "[警告] 找不到 Streamlit，正在安裝必要套件..."
    pip3 install -r requirements.txt
fi

# 啟動應用程式
echo ""
echo "系統啟動中，請稍候..."
echo "瀏覽器將自動開啟，若未開啟請手動前往: http://localhost:8501"
echo ""
streamlit run app.py
