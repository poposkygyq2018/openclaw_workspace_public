#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并版图表：K线图 + 资金曲线 + 交易节点标注
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ==================== 重新生成数据 ====================
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

df = pd.DataFrame({
    'date': dates,
    'close': prices,
    'open': prices * (1 + np.random.normal(0, 0.005, n_days)),
    'high': prices * (1 + np.abs(np.random.normal(0.008, 0.003, n_days))),
    'low': prices * (1 - np.abs(np.random.normal(0.008, 0.003, n_days))),
})

df['short_ma'] = df['close'].rolling(window=5).mean()
df['long_ma'] = df['close'].rolling(window=20).mean()

# 计算资金曲线
INITIAL_CAPITAL = 100000
capital = INITIAL_CAPITAL
equity_curve = []
position = 0
entry_price = 0
trade_points = []  # 记录交易点

for i in range(20, len(df)):
    row = df.iloc[i]
    prev_row = df.iloc[i-1]
    price = row['close']
    date = row['date']
    
    golden_cross = prev_row['short_ma'] <= prev_row['long_ma'] and row['short_ma'] > row['long_ma']
    dead_cross = prev_row['short_ma'] >= prev_row['long_ma'] and row['short_ma'] < row['long_ma']
    
    action = None
    if golden_cross and position == 0:
        position = 1
        entry_price = price
        action = 'BUY'
        trade_points.append({'date': date, 'price': price, 'action': 'BUY', 'idx': i})
    elif dead_cross and position > 0:
        profit = (price - entry_price) * 15 * position
        capital += profit
        position = 0
        action = 'SELL'
        trade_points.append({'date': date, 'price': price, 'action': 'SELL', 'idx': i, 'profit': profit})
    
    unrealized = 0
    if position > 0:
        unrealized = (price - entry_price) * 15 * position
    
    equity_curve.append({
        'date': date,
        'price': price,
        'short_ma': row['short_ma'],
        'long_ma': row['long_ma'],
        'equity': capital + unrealized,
        'action': action
    })

equity_df = pd.DataFrame(equity_curve)

# ==================== 绘制合并图表 ====================
fig = plt.figure(figsize=(16, 10))
gs = fig.add_gridspec(3, 1, height_ratios=[2, 1, 1], hspace=0.05)

# 颜色定义
color_up = '#e74c3c'    # 红色（涨）
color_down = '#27ae60'  # 绿色（跌）
color_ma5 = '#3498db'   # 蓝色
color_ma20 = '#e67e22'  # 橙色
color_equity = '#2c3e50' # 深灰

# ========== 子图1: K线 + 均线 + 交易点 ==========
ax1 = fig.add_subplot(gs[0:2])
df_plot = df[df['date'] >= equity_df['date'].iloc[0]].copy()

# 绘制K线
for i in range(len(df_plot)):
    row = df_plot.iloc[i]
    color = color_up if row['close'] >= row['open'] else color_down
    
    # 实体
    height = abs(row['close'] - row['open'])
    bottom = min(row['close'], row['open'])
    rect = Rectangle((mdates.date2num(row['date']) - 0.3, bottom), 0.6, height,
                      facecolor=color, edgecolor=color, alpha=0.8)
    ax1.add_patch(rect)
    
    # 影线
    ax1.plot([row['date'], row['date']], [row['low'], row['high']], 
             color=color, linewidth=0.8)

# 绘制均线
ax1.plot(df_plot['date'], df_plot['short_ma'], linewidth=1.5, 
         color=color_ma5, label=f'MA5', alpha=0.9)
ax1.plot(df_plot['date'], df_plot['long_ma'], linewidth=1.5, 
         color=color_ma20, label=f'MA20', alpha=0.9)

# 标注交易点
for trade in trade_points:
    if trade['action'] == 'BUY':
        ax1.scatter(trade['date'], trade['price'], marker='^', s=150, 
                   color='green', edgecolors='white', linewidth=2, zorder=5)
        ax1.annotate('BUY', xy=(trade['date'], trade['price']),
                    xytext=(0, 15), textcoords='offset points',
                    ha='center', fontsize=8, color='green', fontweight='bold')
    else:
        ax1.scatter(trade['date'], trade['price'], marker='v', s=150, 
                   color='red', edgecolors='white', linewidth=2, zorder=5)
        profit_str = f"{trade.get('profit', 0):+.0f}"
        ax1.annotate(f'SELL\n{profit_str}', xy=(trade['date'], trade['price']),
                    xytext=(0, -25), textcoords='offset points',
                    ha='center', fontsize=7, color='red', fontweight='bold')

ax1.set_ylabel('Silver Price (CNY/kg)', fontsize=12)
ax1.set_title('Shanghai Silver 2025 Backtest - Price Chart with Trading Signals', 
              fontsize=14, fontweight='bold', pad=10)
ax1.legend(loc='upper left', fontsize=10)
ax1.grid(True, alpha=0.3, linestyle='--')
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
ax1.xaxis.set_major_locator(mdates.MonthLocator())

# 添加Y轴价格标签
ax1.set_ylim(df_plot['low'].min() * 0.98, df_plot['high'].max() * 1.02)

# ========== 子图2: 资金曲线（与上图共享X轴） ==========
ax2 = fig.add_subplot(gs[2], sharex=ax1)

# 绘制资金曲线
ax2.fill_between(equity_df['date'], INITIAL_CAPITAL, equity_df['equity'], 
                 alpha=0.3, color=color_equity)
ax2.plot(equity_df['date'], equity_df['equity'], linewidth=2.5, 
         color=color_equity, label='Strategy Equity')

# 初始资金线
ax2.axhline(y=INITIAL_CAPITAL, color='gray', linestyle='--', 
            linewidth=1, alpha=0.5)

# 盈亏区域着色
ax2.fill_between(equity_df['date'], INITIAL_CAPITAL, equity_df['equity'], 
                 where=(equity_df['equity'] >= INITIAL_CAPITAL), 
                 alpha=0.4, color='green')
ax2.fill_between(equity_df['date'], INITIAL_CAPITAL, equity_df['equity'], 
                 where=(equity_df['equity'] < INITIAL_CAPITAL), 
                 alpha=0.4, color='red')

# 标注关键点
max_equity = equity_df['equity'].max()
min_equity = equity_df['equity'].min()
max_date = equity_df[equity_df['equity'] == max_equity]['date'].iloc[0]
min_date = equity_df[equity_df['equity'] == min_equity]['date'].iloc[0]

ax2.annotate(f'Peak: {max_equity:,.0f}', xy=(max_date, max_equity), 
             xytext=(10, 10), textcoords='offset points',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='lightgreen', alpha=0.8),
             arrowprops=dict(arrowstyle='->', color='green'), fontsize=9)

ax2.annotate(f'Valley: {min_equity:,.0f}', xy=(min_date, min_equity), 
             xytext=(10, -20), textcoords='offset points',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='lightcoral', alpha=0.8),
             arrowprops=dict(arrowstyle='->', color='red'), fontsize=9)

ax2.set_ylabel('Equity (CNY)', fontsize=12)
ax2.set_xlabel('Date', fontsize=12)
ax2.legend(loc='upper left', fontsize=10)
ax2.grid(True, alpha=0.3, linestyle='--')

# 添加统计信息框
stats_text = f"""Backtest Summary:
• Initial Capital: {INITIAL_CAPITAL:,} CNY
• Final Equity: {equity_df['equity'].iloc[-1]:,.0f} CNY  
• Total Return: +{((equity_df['equity'].iloc[-1]/INITIAL_CAPITAL)-1)*100:.1f}%
• Max Drawdown: {((min_equity/INITIAL_CAPITAL)-1)*100:.1f}%
• Trades: {len([t for t in trade_points if t['action']=='SELL'])} completed"""

ax2.text(0.02, 0.95, stats_text, transform=ax2.transAxes, 
         verticalalignment='top', horizontalalignment='left',
         bbox=dict(boxstyle='round,pad=0.8', facecolor='lightyellow', 
                  edgecolor='orange', alpha=0.9),
         fontsize=10, family='monospace')

plt.tight_layout()
plt.savefig('/root/.openclaw/workspace/tqsdk/silver_merged_chart.png', 
            dpi=200, bbox_inches='tight', facecolor='white')
print("✅ 合并图表已保存: silver_merged_chart.png")

# 保存交易明细
print("\n📊 交易明细:")
for i, trade in enumerate(trade_points):
    if trade['action'] == 'SELL':
        profit = trade.get('profit', 0)
        print(f"   {i//2+1}. {trade['date'].strftime('%Y-%m-%d')} SELL @ {trade['price']:.2f} | Profit: {profit:+.2f}")
    else:
        print(f"   {i//2+1}. {trade['date'].strftime('%Y-%m-%d')} BUY  @ {trade['price']:.2f}")
