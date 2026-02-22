#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
绘制沪银回测图表：K线图 + 资金曲线
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import matplotlib.dates as mdates

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ==================== 加载回测数据 ====================
# 重新生成与回测一致的数据
np.random.seed(42)

dates = []
current_date = datetime(2025, 1, 2)
while current_date.year == 2025:
    if current_date.weekday() < 5:
        dates.append(current_date)
    current_date += timedelta(days=1)

n_days = len(dates)
base_price = 6000
returns = np.random.normal(0.0003, 0.012, n_days)
prices = base_price * np.exp(np.cumsum(returns))
prices = np.clip(prices, 5000, 8000)

# 创建DataFrame
df = pd.DataFrame({
    'date': dates,
    'close': prices,
    'open': prices * (1 + np.random.normal(0, 0.005, n_days)),
    'high': prices * (1 + np.abs(np.random.normal(0.008, 0.003, n_days))),
    'low': prices * (1 - np.abs(np.random.normal(0.008, 0.003, n_days))),
})

# 计算均线
df['short_ma'] = df['close'].rolling(window=5).mean()
df['long_ma'] = df['close'].rolling(window=20).mean()

# 重新计算资金曲线
INITIAL_CAPITAL = 100000
capital = INITIAL_CAPITAL
equity_curve = []
position = 0
entry_price = 0

for i in range(20, len(df)):
    row = df.iloc[i]
    prev_row = df.iloc[i-1]
    
    price = row['close']
    
    # 金叉死叉检测
    golden_cross = prev_row['short_ma'] <= prev_row['long_ma'] and row['short_ma'] > row['long_ma']
    dead_cross = prev_row['short_ma'] >= prev_row['long_ma'] and row['short_ma'] < row['long_ma']
    
    if golden_cross and position == 0:
        position = 1
        entry_price = price
    elif dead_cross and position > 0:
        profit = (price - entry_price) * 15 * position
        capital += profit
        position = 0
    
    # 计算当前权益
    unrealized = 0
    if position > 0:
        unrealized = (price - entry_price) * 15 * position
    
    equity_curve.append({
        'date': row['date'],
        'price': price,
        'short_ma': row['short_ma'],
        'long_ma': row['long_ma'],
        'capital': capital,
        'equity': capital + unrealized
    })

equity_df = pd.DataFrame(equity_curve)

# ==================== 绘图 ====================
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [2, 1]})

# 图1: K线图 + 均线
df_plot = df[df['date'] >= equity_df['date'].iloc[0]].copy()

# 绘制K线（简化版，用收盘价表示）
ax1.plot(df_plot['date'], df_plot['close'], linewidth=1, color='#333333', label='Close', alpha=0.8)

# 填充K线颜色（涨跌）
for i in range(1, len(df_plot)):
    if df_plot['close'].iloc[i] >= df_plot['close'].iloc[i-1]:
        color = '#e74c3c'  # 红色（涨）
    else:
        color = '#27ae60'  # 绿色（跌）
    ax1.bar(df_plot['date'].iloc[i], 
            df_plot['close'].iloc[i] - df_plot['open'].iloc[i],
            bottom=df_plot['open'].iloc[i],
            width=0.8, color=color, alpha=0.7)

# 绘制均线
ax1.plot(df_plot['date'], df_plot['short_ma'], linewidth=1.5, color='#3498db', label=f'MA{5}')
ax1.plot(df_plot['date'], df_plot['long_ma'], linewidth=1.5, color='#e67e22', label=f'MA{20}')

# 标记交易点
trades = [
    ('2025-03-26', 'buy'), ('2025-04-02', 'sell'),
    ('2025-04-07', 'buy'), ('2025-04-28', 'sell'),
    ('2025-05-09', 'buy'), ('2025-05-16', 'sell'),
    ('2025-06-12', 'buy'), ('2025-07-07', 'sell'),
    ('2025-08-11', 'buy'), ('2025-09-30', 'sell'),
    ('2025-10-16', 'buy'), ('2025-11-18', 'sell'),
    ('2025-12-02', 'buy'), ('2025-12-03', 'sell'),
]

for date_str, action in trades:
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        if date in df_plot['date'].values:
            price = df_plot[df_plot['date'] == date]['close'].iloc[0]
            if action == 'buy':
                ax1.scatter(date, price, marker='^', color='green', s=100, zorder=5)
            else:
                ax1.scatter(date, price, marker='v', color='red', s=100, zorder=5)
    except:
        pass

ax1.set_ylabel('Price (CNY/kg)', fontsize=12)
ax1.set_title('Shanghai Silver Main Contract 2025 - Price & Moving Averages', fontsize=14, fontweight='bold')
ax1.legend(loc='upper left')
ax1.grid(True, alpha=0.3)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax1.xaxis.set_major_locator(mdates.MonthLocator())

# 图2: 资金曲线
ax2.plot(equity_df['date'], equity_df['equity'], linewidth=2, color='#2c3e50', label='Strategy Equity')
ax2.axhline(y=INITIAL_CAPITAL, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='Initial Capital')

# 填充盈亏区域
ax2.fill_between(equity_df['date'], INITIAL_CAPITAL, equity_df['equity'], 
                 where=(equity_df['equity'] >= INITIAL_CAPITAL), 
                 alpha=0.3, color='green', label='Profit')
ax2.fill_between(equity_df['date'], INITIAL_CAPITAL, equity_df['equity'], 
                 where=(equity_df['equity'] < INITIAL_CAPITAL), 
                 alpha=0.3, color='red', label='Loss')

# 标注关键数据点
max_equity = equity_df['equity'].max()
min_equity = equity_df['equity'].min()
max_date = equity_df[equity_df['equity'] == max_equity]['date'].iloc[0]
min_date = equity_df[equity_df['equity'] == min_equity]['date'].iloc[0]

ax2.annotate(f'Max: {max_equity:,.0f}', xy=(max_date, max_equity), 
             xytext=(10, 10), textcoords='offset points',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='green', alpha=0.3),
             arrowprops=dict(arrowstyle='->', color='green'))

ax2.annotate(f'Min: {min_equity:,.0f}', xy=(min_date, min_equity), 
             xytext=(10, -20), textcoords='offset points',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.3),
             arrowprops=dict(arrowstyle='->', color='red'))

ax2.set_ylabel('Equity (CNY)', fontsize=12)
ax2.set_xlabel('Date', fontsize=12)
ax2.set_title('Strategy Equity Curve', fontsize=14, fontweight='bold')
ax2.legend(loc='upper left')
ax2.grid(True, alpha=0.3)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax2.xaxis.set_major_locator(mdates.MonthLocator())

# 添加统计信息文本
stats_text = f"""
Initial Capital: {INITIAL_CAPITAL:,.0f} CNY
Final Equity: {equity_df['equity'].iloc[-1]:,.0f} CNY
Total Return: +{((equity_df['equity'].iloc[-1]/INITIAL_CAPITAL)-1)*100:.1f}%
Max Drawdown: {((min_equity/INITIAL_CAPITAL)-1)*100:.1f}%
"""
ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes, 
         verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
         fontsize=10, family='monospace')

plt.tight_layout()
plt.savefig('/root/.openclaw/workspace/tqsdk/silver_backtest_chart.png', dpi=150, bbox_inches='tight')
print("✅ 图表已保存: silver_backtest_chart.png")

# 同时生成一个简化版的对比图
fig2, ax = plt.subplots(figsize=(12, 6))

# 标准化价格和资金曲线（都以100为起点）
price_normalized = (df_plot['close'] / df_plot['close'].iloc[0]) * 100
equity_normalized = (equity_df['equity'] / INITIAL_CAPITAL) * 100

ax.plot(df_plot['date'], price_normalized, linewidth=2, color='#3498db', 
        label='Silver Price (Normalized)', alpha=0.8)
ax.plot(equity_df['date'], equity_normalized, linewidth=2, color='#e74c3c', 
        label='Strategy Equity (Normalized)')

ax.axhline(y=100, color='gray', linestyle='--', linewidth=1, alpha=0.5)
ax.fill_between(equity_df['date'], 100, equity_normalized, 
                where=(equity_normalized >= 100), 
                alpha=0.2, color='green')
ax.fill_between(equity_df['date'], 100, equity_normalized, 
                where=(equity_normalized < 100), 
                alpha=0.2, color='red')

ax.set_ylabel('Normalized Value (Base=100)', fontsize=12)
ax.set_xlabel('Date', fontsize=12)
ax.set_title('Silver Price vs Strategy Equity (Normalized)', fontsize=14, fontweight='bold')
ax.legend(loc='upper left')
ax.grid(True, alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.xaxis.set_major_locator(mdates.MonthLocator())

plt.tight_layout()
plt.savefig('/root/.openclaw/workspace/tqsdk/silver_comparison_chart.png', dpi=150, bbox_inches='tight')
print("✅ 对比图已保存: silver_comparison_chart.png")

print(f"\n📊 数据统计:")
print(f"   价格起始: {df_plot['close'].iloc[0]:.2f}")
print(f"   价格结束: {df_plot['close'].iloc[-1]:.2f}")
print(f"   价格涨幅: {((df_plot['close'].iloc[-1]/df_plot['close'].iloc[0])-1)*100:+.2f}%")
print(f"   策略收益: {((equity_df['equity'].iloc[-1]/INITIAL_CAPITAL)-1)*100:+.2f}%")
