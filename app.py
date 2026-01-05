#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高雄新市鎮空氣污染時空分布分析系統
Kaohsiung Air Quality Spatial-Temporal Analysis System

版本: 12.0 (Fix Download Button Style)
配色: #F0EFE7 (米白), #CD4F31 (橘紅), #11142B (深藍)
修正: 下拉選單文字顏色、下載按鈕樣式美化(與打包按鈕一致)、讀檔邏輯
作者: Urban Innofix Lab
"""

import os
import warnings
import tempfile
import zipfile
from datetime import datetime, date
from pathlib import Path
from io import BytesIO

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap
from scipy.ndimage import gaussian_filter

warnings.filterwarnings('ignore')

# 設定 Matplotlib 字型
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# ========================================
# 頁面配置
# ========================================
st.set_page_config(
    page_title="高雄新市鎮空氣污染分析系統",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================================
# 定義選項映射
# ========================================
TIME_AGG_MAPPING = {
    'hourly': '每小時',
    'daily': '每日',
    'weekly': '每週',
    'monthly': '每月',
    'seasonal': '每季',
    'yearly': '每年'
}

# ========================================
# CSS 樣式設計
# ========================================
st.markdown("""
<style>
    /* 引入字體 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&display=swap');

    :root {
        --bg-color: #F0EFE7;         /* 米白色背景 */
        --primary-color: #11142B;    /* 深藍色 (文字、側邊欄) */
        --accent-color: #CD4F31;     /* 橘紅色 (按鈕、強調) */
        --input-bg: #FFFFFF;         /* 輸入框背景 (純白) */
    }

    /* 全域設定 */
    .stApp {
        background-color: var(--bg-color);
        color: var(--primary-color);
        font-family: 'Noto Sans TC', sans-serif !important;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Noto Sans TC', sans-serif !important;
        color: var(--primary-color) !important;
        font-weight: 700;
    }

    /* =========================================
       側邊欄樣式
       ========================================= */
    [data-testid="stSidebar"] {
        background-color: var(--primary-color);
    }
    
    [data-testid="stSidebar"] * {
        color: #F0EFE7 !important;
    }

    [data-testid="stSidebar"] .stElementContainer {
        margin-bottom: 0.5rem !important;
    }
    
    .sidebar-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #F0EFE7;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        border-bottom: 1px solid rgba(255,255,255,0.2);
        padding-bottom: 0.2rem;
    }

    /* =========================================
       輸入框與下拉選單樣式修正
       ========================================= */
    
    /* 標題 Label */
    .stTextInput label, .stDateInput label, .stSelectbox label, .stMultiSelect label {
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        margin-bottom: 0.2rem !important;
    }

    /* 一般輸入框 */
    .stTextInput input, .stDateInput input {
        background-color: var(--input-bg) !important;
        color: var(--primary-color) !important;
        border: 1px solid #F0EFE7 !important;
        border-radius: 4px;
    }
    
    /* 下拉選單 (Selectbox) & 多選框 (MultiSelect) 容器 */
    .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div {
        background-color: var(--input-bg) !important;
        border: 1px solid #F0EFE7 !important;
        border-radius: 4px;
    }
    
    /* 強制將框框內的文字改成深藍色 */
    .stSelectbox div[data-baseweb="select"] span,
    .stMultiSelect div[data-baseweb="select"] span,
    .stSelectbox div[data-baseweb="select"] div,
    .stMultiSelect div[data-baseweb="select"] div {
        color: var(--primary-color) !important;
        -webkit-text-fill-color: var(--primary-color) !important;
    }
    
    /* 下拉選單展開後的列表背景 */
    ul[data-baseweb="menu"] {
        background-color: #FFFFFF !important;
    }
    ul[data-baseweb="menu"] li span {
        color: var(--primary-color) !important;
    }

    /* =========================================
       顏色設定 (橘紅色 #CD4F31)
       ========================================= */
       
    /* Checkbox & Radio */
    div[data-baseweb="checkbox"] div[aria-checked="true"],
    div[role="radiogroup"] div[aria-checked="true"] div:first-child {
        background-color: var(--accent-color) !important;
        border-color: var(--accent-color) !important;
    }
    
    /* MultiSelect Tags */
    .stMultiSelect span[data-baseweb="tag"] {
        background-color: var(--accent-color) !important;
    }
    .stMultiSelect span[data-baseweb="tag"] span {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    /* 按鈕樣式 (包含一般按鈕與下載按鈕) */
    .stButton > button, .stDownloadButton > button {
        width: 100%;
        background-color: var(--accent-color) !important;
        color: #F0EFE7 !important;
        font-weight: 700;
        padding: 0.8rem 1rem;
        border-radius: 0px;
        border: none;
        box-shadow: 4px 4px 0px rgba(17, 20, 43, 0.2);
        transition: all 0.2s ease;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        background-color: #D65A3F !important;
        transform: translate(-2px, -2px);
        box-shadow: 6px 6px 0px rgba(17, 20, 43, 0.3);
    }

    /* 標題區塊 */
    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        color: var(--primary-color);
        text-align: center;
        padding-top: 2rem;
        margin-bottom: 0.5rem;
        letter-spacing: 0.05em;
    }

    .sub-header {
        font-size: 1.1rem;
        color: var(--accent-color);
        text-align: center;
        margin-bottom: 3rem;
        font-weight: 500;
        letter-spacing: 0.15em;
        text-transform: uppercase;
    }

    /* 訊息框樣式 */
    .custom-box {
        padding: 1rem;
        background-color: white;
        border: 1px solid var(--primary-color);
        color: var(--primary-color);
        margin-bottom: 1rem;
    }
    .box-success { border-left: 5px solid var(--accent-color); }
    .box-error { border-left: 5px solid #C0392B; background-color: #FDEDEC; }
    
    /* 模型解釋區塊 */
    .model-explanation {
        background-color: #FFFFFF;
        border-left: 4px solid var(--primary-color);
        padding: 2rem;
        margin-top: 3rem;
        border-radius: 0 4px 4px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .model-explanation h4 {
        color: var(--accent-color) !important;
        margin-bottom: 1.2rem;
        font-size: 1.3rem;
        font-weight: 700;
    }
    .model-explanation p, .model-explanation li {
        font-size: 1rem;
        color: var(--primary-color);
        line-height: 1.8;
        margin-bottom: 0.8rem;
    }
    .model-explanation strong {
        color: var(--primary-color);
        font-weight: 700;
    }

    /* 頁尾 */
    .footer {
        text-align: center;
        padding: 2rem 0;
        margin-top: 5rem;
        border-top: 1px solid rgba(17, 20, 43, 0.1);
        color: var(--primary-color);
    }
    .footer-logo { font-weight: 700; font-size: 1.4rem; letter-spacing: 1px; }
    .footer-ver { font-size: 0.85rem; color: var(--accent-color); margin-top: 0.3rem; }

</style>
""", unsafe_allow_html=True)

# ========================================
# 標題區塊
# ========================================
st.markdown('<div class="main-header">高雄新市鎮空氣污染分析系統</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Kaohsiung Air Quality Spatial-Temporal Analysis System</div>', unsafe_allow_html=True)

# ========================================
# 時段定義
# ========================================
TIME_PERIODS = {
    'all': {'name': '全時段 (00:00-23:00)', 'hours': list(range(24))},
    'dawn': {'name': '清晨 (05:00-07:00)', 'hours': [5, 6]},
    'morning_peak': {'name': '早上 (07:00-09:00)', 'hours': [7, 8]},
    'noon': {'name': '午間 (12:00-14:00)', 'hours': [12, 13]},
    'evening_peak': {'name': '傍晚 (17:00-19:00)', 'hours': [17, 18]},
    'night': {'name': '夜間 (20:00-22:00)', 'hours': [20, 21]},
    'midnight': {'name': '深夜 (22:00-05:00)', 'hours': [22, 23, 0, 1, 2, 3, 4]}
}

# ========================================
# 圖表配置
# ========================================
PLOT_CONFIGS = {
    'pm25': {
        'value_col': 'pm25_mean',
        'title': 'PM2.5 空間分布',
        'unit': 'μg/m³',
        'colors': ['#00e400', '#92d050', '#ffff00', '#ff9900', '#ff0000', '#990033'],
        'levels': [0, 12, 24, 36, 48, 60, 80],
        'use_wind': True,
    },
    'temperature': {
        'value_col': 'temperature_mean',
        'title': '溫度空間分布',
        'unit': '°C',
        'colors': ['#0000ff', '#00ffff', '#00ff00', '#ffff00', '#ff0000'],
        'levels': [15, 20, 25, 30, 35, 40],
        'use_wind': False,
    },
    'humidity': {
        'value_col': 'humidity_mean',
        'title': '濕度空間分布',
        'unit': '%',
        'colors': ['#8B4513', '#D2691E', '#F4A460', '#87CEEB', '#4682B4', '#000080'],
        'levels': [30, 40, 50, 60, 70, 80, 90],
        'use_wind': False,
    },
    'pm25_variability': {
        'value_col': 'pm25_cv',
        'title': 'PM2.5 變異係數',
        'unit': '%',
        'colors': ['#00ff00', '#ffff00', '#ff9900', '#ff0000'],
        'levels': [0, 10, 20, 30, 40, 50],
        'use_wind': False,
    },
    'pm25_exceed': {
        'value_col': 'pm25_exceeds_35_pct',
        'title': 'PM2.5 超標比例',
        'unit': '%',
        'colors': ['#00ff00', '#ffff00', '#ff9900', '#ff0000', '#990033'],
        'levels': [0, 10, 25, 50, 75, 100],
        'use_wind': False,
    },
    'wind_field': {
        'value_col': 'pm25_mean',
        'title': '風場向量圖',
        'unit': '',
        'colors': ['#00e400', '#92d050', '#ffff00', '#ff9900', '#ff0000', '#990033'],
        'levels': [0, 12, 24, 36, 48, 60, 80],
        'use_wind': True,
    }
}

# ========================================
# 側邊欄 - 參數設定
# ========================================
with st.sidebar:
    st.markdown('<div class="sidebar-header">1. 資料來源</div>', unsafe_allow_html=True)
    data_dir = st.text_input("資料目錄", value="data")
    station_file = st.text_input("測站檔案", value="data/Kaohsiung_iot_station.csv")
    
    st.markdown('<div class="sidebar-header">2. 時間範圍</div>', unsafe_allow_html=True)
    
    time_filter_mode = st.radio(
        "篩選模式",
        ["依年份/月份", "自訂日期區間"],
        horizontal=True
    )
    
    selected_years_to_load = []
    filter_criteria = {}
    
    if time_filter_mode == "依年份/月份":
        available_years = list(range(2020, 2026))
        selected_years = st.multiselect(
            "選擇年份",
            options=available_years,
            default=[2020]
        )
        
        selected_months = st.multiselect(
            "選擇月份",
            options=list(range(1, 13)),
            default=list(range(1, 13)),
            format_func=lambda x: f"{x}月"
        )
        
        selected_years_to_load = selected_years
        filter_criteria = {
            'mode': 'year_month',
            'years': selected_years,
            'months': selected_months
        }
        
    else:  # 自訂日期區間
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("開始日期", value=date(2020, 1, 1))
        with col2:
            end_date = st.date_input("結束日期", value=date(2020, 1, 31))
        
        if start_date > end_date:
            st.error("開始日期不能晚於結束日期")
        
        selected_years_to_load = list(range(start_date.year, end_date.year + 1))
        filter_criteria = {
            'mode': 'date_range',
            'start': start_date,
            'end': end_date
        }
    
    time_aggregation = st.selectbox(
        "時間聚合方式",
        options=list(TIME_AGG_MAPPING.keys()),
        index=3,
        format_func=lambda x: TIME_AGG_MAPPING[x]
    )
    
    st.markdown('<div class="sidebar-header">3. 時段分析</div>', unsafe_allow_html=True)
    enable_period_analysis = st.checkbox("啟用時段分析", value=False)
    
    if enable_period_analysis:
        selected_periods = st.multiselect(
            "選擇時段",
            options=list(TIME_PERIODS.keys()),
            default=['all'],
            format_func=lambda x: TIME_PERIODS[x]['name']
        )
    else:
        selected_periods = ['all']
    
    st.markdown('<div class="sidebar-header">4. 圖表類型</div>', unsafe_allow_html=True)
    selected_plot_types = st.multiselect(
        "選擇圖表",
        options=list(PLOT_CONFIGS.keys()),
        default=['pm25'],
        format_func=lambda x: PLOT_CONFIGS[x]['title']
    )
    
    # 進階設定
    with st.expander("進階設定"):
        basemap_style = st.selectbox(
            "底圖風格",
            options=['Standard', 'Satellite', 'Light', 'Dark', 'None'],
            index=0
        )
        
        layer_alpha = st.slider("圖層透明度", 0.1, 1.0, 0.6, 0.1)
        grid_resolution = st.slider("網格解析度", 100, 500, 300, 50)
        diffusion_radius = st.slider("擴散半徑", 0.01, 0.2, 0.05, 0.01)
        wind_influence = st.slider("風向係數", 0.0, 1.0, 0.3, 0.1)
        png_dpi = st.slider("圖片 DPI", 72, 300, 150, 10)

# ========================================
# 擴散模型
# ========================================
class DenseDiffusionModel:
    def __init__(self, radius=0.05, wind_influence=0.3, distance_decay=3.0, sigma=0.5):
        self.radius = radius
        self.wind_influence = wind_influence
        self.distance_decay = distance_decay
        self.sigma = sigma
    
    def interpolate(self, sites_data, grid_lon, grid_lat, value_col='pm25_mean', use_wind=False):
        grid_values = np.zeros_like(grid_lon)
        total_weights = np.zeros_like(grid_lon)
        
        for _, site in sites_data.iterrows():
            if pd.isna(site[value_col]):
                continue
            
            dx = grid_lon - site['lon']
            dy = grid_lat - site['lat']
            distance = np.sqrt(dx**2 + dy**2)
            
            weights = np.where(distance < self.radius,
                              1 / (distance + 0.0001)**self.distance_decay,
                              0)
            
            if use_wind and 'WindDirection_Mean' in site and 'WindSpeed_Mean' in site:
                if not np.isnan(site['WindDirection_Mean']) and not np.isnan(site['WindSpeed_Mean']):
                    angle_to_grid = np.degrees(np.arctan2(dy, dx)) % 360
                    pollution_direction = (site['WindDirection_Mean'] + 180) % 360
                    angle_diff = np.abs(angle_to_grid - pollution_direction)
                    angle_diff = np.minimum(angle_diff, 360 - angle_diff)
                    
                    wind_factor = np.cos(np.deg2rad(angle_diff))
                    wind_factor = (wind_factor + 1) / 2
                    speed_factor = np.tanh(site['WindSpeed_Mean'] / 5)
                    wind_influence_matrix = 1 + self.wind_influence * wind_factor * speed_factor
                    
                    weights *= wind_influence_matrix
            
            grid_values += site[value_col] * weights
            total_weights += weights
        
        grid_values = np.where(total_weights > 0, 
                              grid_values / total_weights, 
                              np.nan)
        
        grid_values = gaussian_filter(grid_values, sigma=self.sigma)
        
        return grid_values

# ========================================
# 時間聚合函數
# ========================================
def aggregate_by_time(df, aggregation='daily'):
    if aggregation == 'hourly':
        groups = df.groupby('timestamp')
        time_periods = sorted(df['timestamp'].unique())
        label_format = lambda t: t.strftime('%Y-%m-%d %H:00')
    elif aggregation == 'daily':
        groups = df.groupby('date')
        time_periods = sorted(df['date'].unique())
        label_format = lambda d: d.strftime('%Y-%m-%d')
    elif aggregation == 'weekly':
        df['year_week'] = df['year'].astype(str) + '-W' + df['week'].astype(str).str.zfill(2)
        groups = df.groupby('year_week')
        time_periods = sorted(df['year_week'].unique())
        label_format = lambda w: w
    elif aggregation == 'monthly':
        df['year_month'] = df['year'].astype(str) + '-' + df['month'].astype(str).str.zfill(2)
        groups = df.groupby('year_month')
        time_periods = sorted(df['year_month'].unique())
        label_format = lambda m: m
    elif aggregation == 'seasonal':
        groups = df.groupby('year_season')
        time_periods = sorted(df['year_season'].unique())
        label_format = lambda s: s
    elif aggregation == 'yearly':
        groups = df.groupby('year')
        time_periods = sorted(df['year'].unique())
        label_format = lambda y: str(y)
    else:
        raise ValueError(f"Unknown aggregation: {aggregation}")
    
    return groups, time_periods, label_format

# ========================================
# 產生圖表函數
# ========================================
def generate_plot(period_data, plot_type, plot_config, period_label, 
                 time_period_key='all', grid_lon_mesh=None, grid_lat_mesh=None,
                 lon_min=None, lon_max=None, lat_min=None, lat_max=None,
                 model=None, dpi=150, basemap_style='Standard', alpha=0.6):
    
    value_col = plot_config['value_col']
    
    # 聚合測站資料
    agg_dict = {
        'lon': 'first',
        'lat': 'first',
        value_col: 'mean',
    }
    
    if plot_config['use_wind']:
        if 'WindDirection_Mean' in period_data.columns:
            agg_dict['WindDirection_Mean'] = lambda x: x.mode()[0] if len(x.mode()) > 0 else x.mean()
        if 'WindSpeed_Mean' in period_data.columns:
            agg_dict['WindSpeed_Mean'] = 'mean'
    
    site_avg = period_data.groupby('deviceId').agg(agg_dict).reset_index()
    site_avg = site_avg.dropna(subset=[value_col])
    
    if len(site_avg) == 0:
        return None
    
    # 執行插值
    grid_values = model.interpolate(site_avg, grid_lon_mesh, grid_lat_mesh, 
                                   value_col=value_col, 
                                   use_wind=plot_config['use_wind'])
    
    # 建立色階
    cmap = LinearSegmentedColormap.from_list(plot_type, plot_config['colors'], N=256)
    norm = BoundaryNorm(plot_config['levels'], cmap.N)
    
    # 繪圖
    fig, ax = plt.subplots(figsize=(14, 12))
    
    # 處理風場向量圖
    if plot_type == 'wind_field':
        contourf = ax.contourf(grid_lon_mesh, grid_lat_mesh, grid_values,
                              levels=plot_config['levels'], cmap=cmap, norm=norm, 
                              extend='both', alpha=alpha, zorder=1)
        
        u = site_avg['WindSpeed_Mean'] * np.sin(np.deg2rad(site_avg['WindDirection_Mean']))
        v = site_avg['WindSpeed_Mean'] * np.cos(np.deg2rad(site_avg['WindDirection_Mean']))
        
        quiver = ax.quiver(site_avg['lon'], site_avg['lat'], u, v,
                          site_avg['WindSpeed_Mean'],
                          cmap='cool',
                          scale=50,
                          width=0.003,
                          headwidth=4,
                          headlength=5,
                          alpha=0.8,
                          zorder=5)
        
        cbar1 = plt.colorbar(contourf, ax=ax, fraction=0.046, pad=0.04, shrink=0.4, location='left')
        cbar1.set_label('PM2.5 (μg/m³)', fontsize=10, fontweight='bold')
        
        cbar2 = plt.colorbar(quiver, ax=ax, fraction=0.046, pad=0.04, shrink=0.4)
        cbar2.set_label('風速 (m/s)', fontsize=10, fontweight='bold')
    else:
        contourf = ax.contourf(grid_lon_mesh, grid_lat_mesh, grid_values,
                              levels=plot_config['levels'], cmap=cmap, norm=norm, 
                              extend='both', alpha=alpha, zorder=2)
        
        scatter = ax.scatter(site_avg['lon'], site_avg['lat'],
                            c=site_avg[value_col],
                            s=80,
                            cmap=cmap,
                            norm=norm,
                            marker='o',
                            edgecolors='black',
                            linewidth=0.8,
                            alpha=0.9,
                            zorder=5)
        
        cbar = plt.colorbar(contourf, ax=ax, fraction=0.046, pad=0.04, shrink=0.8)
        cbar.set_label(f'{plot_config["title"]} ({plot_config["unit"]})', 
                      fontsize=12, fontweight='bold')
        cbar.ax.tick_params(labelsize=10)
    
    ax.set_xlim(lon_min, lon_max)
    ax.set_ylim(lat_min, lat_max)
    ax.set_aspect('equal', adjustable='box')
    
    # 底圖處理
    if basemap_style != 'None':
        try:
            import contextily as ctx
            
            source = ctx.providers.OpenStreetMap.Mapnik
            if basemap_style == 'Light':
                source = ctx.providers.CartoDB.Positron
            elif basemap_style == 'Dark':
                source = ctx.providers.CartoDB.DarkMatter
            elif basemap_style == 'Satellite':
                source = ctx.providers.Esri.WorldImagery
                
            ctx.add_basemap(ax, crs='EPSG:4326', 
                           source=source, 
                           zoom='auto', alpha=0.8, zorder=1)
        except:
            ax.set_facecolor('#f0f0f0')
            ax.grid(True, alpha=0.3, linestyle='--', color='white', linewidth=1.5)
    else:
        ax.set_facecolor('#f0f0f0')
        ax.grid(True, alpha=0.3, linestyle='--', color='white', linewidth=1.5)
    
    ax.set_xlabel('經度 (°E)', fontsize=11, fontweight='bold')
    ax.set_ylabel('緯度 (°N)', fontsize=11, fontweight='bold')
    
    # 標題
    avg_val = site_avg[value_col].mean()
    time_period_name = TIME_PERIODS[time_period_key]['name']
    
    title_text = f'{plot_config["title"]}'
    if time_period_key != 'all':
        title_text += f' - {time_period_name}'
    title_text += f'\n{period_label}\n'
    
    if plot_type == 'wind_field':
        title_text += f'平均風速: {site_avg["WindSpeed_Mean"].mean():.1f} m/s'
    else:
        title_text += f'平均: {avg_val:.1f} {plot_config["unit"]} | 測站數: {len(site_avg)}'
    
    ax.set_title(title_text, fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    
    # 儲存到記憶體
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', 
               facecolor='white', edgecolor='none')
    buf.seek(0)
    plt.close()
    
    return buf

# ========================================
# 主要分析流程
# ========================================

# 按鈕
if st.button("開始分析"):
    if not selected_plot_types:
        st.markdown('<div class="custom-box box-error">請至少選擇一種圖表類型</div>', unsafe_allow_html=True)
    else:
        # 進度條
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 步驟 1: 讀取資料
            status_text.text("讀取資料中...")
            progress_bar.progress(10)
            
            data_path = Path(data_dir)
            all_dataframes = []
            
            # 讀取所有符合 kaohsiung_airbox_hourly_with_wind*.csv 的檔案
            target_files = list(data_path.glob("kaohsiung_airbox_hourly_with_wind*.csv"))
            
            if not target_files:
                st.markdown(f'<div class="custom-box box-error">找不到符合 kaohsiung_airbox_hourly_with_wind*.csv 的資料檔案</div>', unsafe_allow_html=True)
                st.stop()
                
            for file_path in target_files:
                try:
                    df_temp = pd.read_csv(file_path)
                    all_dataframes.append(df_temp)
                except Exception as e:
                    st.warning(f"無法讀取檔案 {file_path.name}: {e}")
            
            if not all_dataframes:
                st.markdown(f'<div class="custom-box box-error">無法從檔案中讀取有效資料</div>', unsafe_allow_html=True)
                st.stop()
            
            df = pd.concat(all_dataframes, ignore_index=True)
            progress_bar.progress(25)
            
            # 步驟 2: 資料清理與篩選
            status_text.text("資料清理與篩選...")
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df = df.dropna(subset=['timestamp'])
            
            df['date'] = df['timestamp'].dt.date
            df['hour'] = df['timestamp'].dt.hour
            df['year'] = df['timestamp'].dt.year
            df['month'] = df['timestamp'].dt.month
            df['week'] = df['timestamp'].dt.isocalendar().week
            
            # 執行時間篩選
            if filter_criteria['mode'] == 'year_month':
                target_years = filter_criteria['years']
                target_months = filter_criteria['months']
                df = df[df['year'].isin(target_years) & df['month'].isin(target_months)]
                
            elif filter_criteria['mode'] == 'date_range':
                start = filter_criteria['start']
                end = filter_criteria['end']
                df = df[(df['date'] >= start) & (df['date'] <= end)]
            
            if len(df) == 0:
                st.markdown('<div class="custom-box box-error">篩選後的資料為空，請檢查時間條件</div>', unsafe_allow_html=True)
                st.stop()
            
            def get_season(month):
                if month in [3, 4, 5]:
                    return 'Spring'
                elif month in [6, 7, 8]:
                    return 'Summer'
                elif month in [9, 10, 11]:
                    return 'Autumn'
                else:
                    return 'Winter'
            
            df['season'] = df['month'].apply(get_season)
            df['year_season'] = df['year'].astype(str) + '-' + df['season']
            
            numeric_cols = ['pm25_mean', 'pm25_std', 'pm25_cv', 'pm25_exceeds_35_pct', 
                           'temperature_mean', 'humidity_mean', 'discomfort_index_mean',
                           'WindSpeed_Mean', 'WindDirection_Mean']
            
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df['deviceId'] = df['deviceId'].astype(str)
            
            # 過濾異常值
            if 'pm25_mean' in df.columns:
                df = df[(df['pm25_mean'].isna()) | 
                       ((df['pm25_mean'] >= 0) & (df['pm25_mean'] <= 500))]
            
            progress_bar.progress(40)
            
            # 步驟 3: 建立測站座標
            status_text.text("建立空間座標系統...")
            
            df_stations = pd.read_csv(station_file)
            station_coords = df_stations[['deviceId', 'lat', 'lon']].copy()
            station_coords['deviceId'] = station_coords['deviceId'].astype(str)
            df = df.merge(station_coords, on='deviceId', how='left', suffixes=('', '_station'))
            
            if 'lat_station' in df.columns:
                df['lat'] = df['lat_station'].fillna(df.get('lat', np.nan))
                df['lon'] = df['lon_station'].fillna(df.get('lon', np.nan))
                df = df.drop(columns=['lat_station', 'lon_station'], errors='ignore')
            
            df = df.dropna(subset=['lat', 'lon'])
            
            progress_bar.progress(50)
            
            # 步驟 4: 產生圖表
            status_text.text("正在繪製圖表...")
            
            # 建立網格
            lat_min, lat_max = df['lat'].min() - 0.02, df['lat'].max() + 0.02
            lon_min, lon_max = df['lon'].min() - 0.02, df['lon'].max() + 0.02
            
            grid_lat = np.linspace(lat_min, lat_max, grid_resolution)
            grid_lon = np.linspace(lon_min, lon_max, grid_resolution)
            grid_lon_mesh, grid_lat_mesh = np.meshgrid(grid_lon, grid_lat)
            
            # 建立模型
            model = DenseDiffusionModel(
                radius=diffusion_radius,
                wind_influence=wind_influence,
                distance_decay=3.0,
                sigma=0.5
            )
            
            # 時間聚合
            groups, time_periods_list, label_format = aggregate_by_time(df, time_aggregation)
            
            # 產生圖表
            generated_images = {}
            total_tasks = len(time_periods_list) * len(selected_plot_types) * len(selected_periods)
            current_task = 0
            
            for period in time_periods_list:
                period_data = groups.get_group(period)
                period_label = label_format(period)
                
                for plot_type in selected_plot_types:
                    plot_config = PLOT_CONFIGS[plot_type]
                    value_col = plot_config['value_col']
                    
                    if value_col not in df.columns:
                        continue
                    
                    for period_key in selected_periods:
                        if period_key == 'all':
                            filtered_data = period_data
                        else:
                            target_hours = TIME_PERIODS[period_key]['hours']
                            filtered_data = period_data[period_data['hour'].isin(target_hours)]
                        
                        if len(filtered_data) == 0:
                            current_task += 1
                            continue
                        
                        # 產生圖表
                        img_buf = generate_plot(
                            filtered_data, plot_type, plot_config, period_label,
                            time_period_key=period_key,
                            grid_lon_mesh=grid_lon_mesh,
                            grid_lat_mesh=grid_lat_mesh,
                            lon_min=lon_min, lon_max=lon_max,
                            lat_min=lat_min, lat_max=lat_max,
                            model=model,
                            dpi=png_dpi,
                            basemap_style=basemap_style,
                            alpha=layer_alpha
                        )
                        
                        if img_buf:
                            time_period_suffix = '' if period_key == 'all' else f'_{period_key}'
                            filename = f"kaohsiung_{plot_type}_{period_label.replace(':', '-').replace(' ', '_')}{time_period_suffix}.png"
                            generated_images[filename] = img_buf
                        
                        current_task += 1
                        progress = 50 + int((current_task / total_tasks) * 50)
                        progress_bar.progress(progress)
            
            progress_bar.progress(100)
            status_text.empty()
            
            # 預先產生 ZIP 檔案
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for filename, img_buf in generated_images.items():
                    zip_file.writestr(filename, img_buf.getvalue())
            zip_buffer.seek(0)
            
            # 儲存到 session state
            st.session_state['generated_images'] = generated_images
            st.session_state['zip_buffer'] = zip_buffer
            
            # 強制刷新頁面以更新 UI
            st.rerun()
            
        except Exception as e:
            st.markdown(f'<div class="custom-box box-error">分析過程發生錯誤: {str(e)}</div>', unsafe_allow_html=True)
            import traceback
            st.code(traceback.format_exc())

# ========================================
# 模型解釋區塊 (只有在未產生圖表時顯示)
# ========================================
if 'generated_images' not in st.session_state:
    st.markdown("""<div class="model-explanation">
    <h4>模型原理與風場處理說明</h4>
    <p>本系統採用 <strong>Dense Diffusion Model (密集擴散模型)</strong> 進行空氣污染時空分布推估，核心技術如下：</p>
    <ul>
    <li><strong>基礎插值</strong>：採用改進型反距離權重法 (IDW)，基礎權重隨距離衰減。</li>
    <li><strong>風向修正</strong>：計算測站風向與網格向量的<strong>餘弦相似度 (Cosine Similarity)</strong>，結合<strong>雙曲正切函數 (tanh)</strong> 轉換風速強度，動態調整權重，模擬污染物隨風飄移的物理特性。</li>
    <li><strong>高斯平滑</strong>：對插值網格進行高斯濾波，消除數值邊界的鋸齒狀，確保視覺呈現的連續性。</li>
    </ul>
    <hr style="border-top: 1px dashed #11142B; opacity: 0.2; margin: 1.5rem 0;">
    <h4>關鍵參數定義</h4>
    <ul>
    <li><strong>擴散半徑 (Diffusion Radius)</strong>：
    <br>定義單一測站資料能影響的最大地理範圍（單位：經緯度）。半徑越大，測站影響範圍越廣，圖形越平滑；半徑越小，則更能呈現局部的污染熱點。
    </li>
    <li><strong>風向係數 (Wind Influence Coefficient)</strong>：
    <br>控制風向對污染物擴散的權重（範圍 0.0 ~ 1.0）。
    <br><strong>0.0</strong>：代表無風狀態，污染物呈同心圓擴散。
    <br><strong>1.0</strong>：代表強烈受風影響，污染物主要向下風處飄移，上風處濃度迅速遞減。
    </li>
    </ul>
    </div>""", unsafe_allow_html=True)

# ========================================
# 顯示和下載結果
# ========================================
if 'generated_images' in st.session_state:
    st.markdown("---")
    st.markdown("### 分析結果")
    
    generated_images = st.session_state['generated_images']
    
    # 統計資訊
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("總圖表數", len(generated_images))
    with col2:
        total_size = sum(len(img.getvalue()) for img in generated_images.values()) / (1024 * 1024)
        st.metric("總檔案大小", f"{total_size:.2f} MB")
    with col3:
        st.metric("格式", "PNG / ZIP")
    
    st.markdown("---")
    
    # 圖表預覽和下載
    st.markdown("#### 圖表預覽與下載")
    
    # 選擇顯示的圖表
    selected_image = st.selectbox(
        "選擇要預覽的圖表",
        options=list(generated_images.keys())
    )
    
    if selected_image:
        # 顯示圖片
        try:
            st.image(generated_images[selected_image], use_column_width=True)
        except:
            st.image(generated_images[selected_image], width=800)
        
        # 單張下載
        st.download_button(
            label="下載此圖表",
            data=generated_images[selected_image],
            file_name=selected_image,
            mime="image/png"
        )
    
    st.markdown("---")
    
    # 批次下載 (直接下載)
    st.markdown("#### 批次下載")
    
    if 'zip_buffer' in st.session_state:
        st.download_button(
            label="下載所有圖表 (ZIP)",
            data=st.session_state['zip_buffer'],
            file_name=f"kaohsiung_air_quality_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip"
        )

# ========================================
# 頁尾
# ========================================
st.markdown("""
<div class="footer">
    <div class="footer-logo">Urban Innofix Lab</div>
    <div class="footer-ver">高雄新市鎮空氣污染時空分布分析系統 v12.0</div>
</div>
""", unsafe_allow_html=True)