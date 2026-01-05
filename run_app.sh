#!/bin/bash

echo "========================================"
echo "高雄新市鎮空氣污染分析系統"
echo "Kaohsiung Air Quality Analysis System"
echo "========================================"
echo ""

# 定義顏色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 函數：檢查 Python 版本是否為 3.8.x
check_python_version() {
    local python_cmd=$1
    if command -v "$python_cmd" &> /dev/null; then
        local version=$($python_cmd --version 2>&1 | grep -o "Python 3\.8\.[0-9]*")
        if [[ -n "$version" ]]; then
            echo "$python_cmd"
            return 0
        fi
    fi
    return 1
}

echo -e "${BLUE}[1/3]${NC} 尋找 Python 3.8..."

# 尋找 Python 3.8 的可能命令
PYTHON_CANDIDATES=(
    "python3.8"
    "python3"
    "python"
    "/usr/bin/python3.8"
    "/usr/local/bin/python3.8"
    "/opt/python3.8/bin/python3.8"
    "$HOME/.pyenv/versions/3.8.*/bin/python"
    "/usr/bin/python3"
    "/usr/local/bin/python3"
)

PYTHON_EXE=""
PYTHON_FOUND=0

# 逐一檢查候選命令
for candidate in "${PYTHON_CANDIDATES[@]}"; do
    # 處理通配符路徑
    if [[ "$candidate" == *"*"* ]]; then
        for path in $candidate; do
            if [[ -f "$path" ]]; then
                if PYTHON_EXE=$(check_python_version "$path"); then
                    PYTHON_FOUND=1
                    echo -e "${GREEN}[找到]${NC} $path"
                    break 2
                fi
            fi
        done
    else
        if PYTHON_EXE=$(check_python_version "$candidate"); then
            PYTHON_FOUND=1
            echo -e "${GREEN}[找到]${NC} $candidate"
            break
        fi
    fi
done

# 如果還沒找到，嘗試使用 pyenv
if [[ $PYTHON_FOUND -eq 0 ]] && command -v pyenv &> /dev/null; then
    echo -e "${BLUE}[搜尋]${NC} 檢查 pyenv..."
    pyenv versions --bare | grep "^3\.8\." | head -1 | while read version; do
        if [[ -n "$version" ]]; then
            PYTHON_EXE="$HOME/.pyenv/versions/$version/bin/python"
            if [[ -f "$PYTHON_EXE" ]]; then
                PYTHON_FOUND=1
                echo -e "${GREEN}[找到]${NC} pyenv Python $version"
                break
            fi
        fi
    done
fi

# 如果還沒找到，嘗試使用 conda
if [[ $PYTHON_FOUND -eq 0 ]] && command -v conda &> /dev/null; then
    echo -e "${BLUE}[搜尋]${NC} 檢查 conda..."
    conda_envs=$(conda env list | grep "python3.8\|py38" | head -1)
    if [[ -n "$conda_envs" ]]; then
        env_name=$(echo "$conda_envs" | awk '{print $1}')
        PYTHON_EXE="conda run -n $env_name python"
        PYTHON_FOUND=1
        echo -e "${GREEN}[找到]${NC} conda environment: $env_name"
    fi
fi

if [[ $PYTHON_FOUND -eq 0 ]]; then
    echo -e "${RED}[錯誤]${NC} 找不到 Python 3.8"
    echo ""
    echo "請安裝 Python 3.8.x 版本："
    echo ""
    echo "Ubuntu/Debian:"
    echo "  sudo apt update"
    echo "  sudo apt install python3.8 python3.8-pip python3.8-venv"
    echo ""
    echo "CentOS/RHEL/Fedora:"
    echo "  sudo dnf install python38 python38-pip"
    echo ""
    echo "macOS (使用 Homebrew):"
    echo "  brew install python@3.8"
    echo ""
    echo "或使用 pyenv:"
    echo "  pyenv install 3.8.12"
    echo "  pyenv local 3.8.12"
    echo ""
    exit 1
fi

# 顯示找到的 Python 版本
echo ""
$PYTHON_EXE --version
echo -e "${GREEN}[成功]${NC} 已找到 Python 3.8"
echo ""

# 檢查 pip
echo -e "${BLUE}[2/3]${NC} 檢查套件管理器..."
if ! $PYTHON_EXE -m pip --version &> /dev/null; then
    echo -e "${YELLOW}[警告]${NC} pip 未安裝，嘗試安裝..."
    if command -v curl &> /dev/null; then
        curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
        $PYTHON_EXE get-pip.py
        rm get-pip.py
    else
        echo -e "${RED}[錯誤]${NC} 無法安裝 pip，請手動安裝"
        exit 1
    fi
fi

# 檢查並安裝必要套件
echo -e "${BLUE}[檢查]${NC} 驗證必要套件..."
if ! $PYTHON_EXE -c "import streamlit, pandas, numpy, matplotlib, scipy" &> /dev/null; then
    echo -e "${YELLOW}[安裝]${NC} 正在安裝必要套件，請稍候..."
    echo ""
    
    # 升級 pip
    $PYTHON_EXE -m pip install --upgrade pip
    
    # 安裝套件
    if [[ -f "requirements.txt" ]]; then
        $PYTHON_EXE -m pip install -r requirements.txt
    else
        $PYTHON_EXE -m pip install streamlit pandas numpy matplotlib scipy contextily pillow
    fi
    
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}[錯誤]${NC} 套件安裝失敗"
        echo "請檢查網路連線或手動執行："
        echo "  $PYTHON_EXE -m pip install streamlit pandas numpy matplotlib scipy contextily pillow"
        exit 1
    fi
fi
echo -e "${GREEN}[成功]${NC} 所有套件已安裝"
echo ""

# 檢查資料檔案
echo -e "${BLUE}[檢查]${NC} 驗證資料檔案..."
if [[ ! -d "data" ]]; then
    echo -e "${YELLOW}[警告]${NC} 找不到 data 資料夾"
    echo "請確認已下載資料檔案並放置在 data 資料夾中"
    echo "資料下載: https://drive.google.com/drive/folders/1ak6yl8A6AlYswMBxFxrKyeyh3iU-YXUA"
    echo ""
    read -p "按 Enter 繼續啟動系統 (可能會出現錯誤)..."
elif [[ ! $(ls data/kaohsiung_airbox_hourly_with_wind*.csv 2>/dev/null) ]]; then
    echo -e "${YELLOW}[警告]${NC} data 資料夾中找不到必要的 CSV 檔案"
    echo "請確認已下載: kaohsiung_airbox_hourly_with_wind_*.csv"
    echo ""
else
    echo -e "${GREEN}[成功]${NC} 找到資料檔案"
fi
echo ""

# 啟動應用程式
echo -e "${BLUE}[3/3]${NC} 啟動系統..."
echo "========================================"
echo "系統啟動中，請稍候..."
echo "瀏覽器將自動開啟 http://localhost:8501"
echo ""
echo -e "${YELLOW}*** 重要提醒 ***${NC}"
echo "- 關閉此終端將停止系統"
echo "- 如需停止，請按 Ctrl+C"
echo "========================================"
echo ""

# 啟動 Streamlit
$PYTHON_EXE -m streamlit run app.py --server.headless true --server.port 8501

echo ""
echo "系統已關閉"
