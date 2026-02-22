#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双均线策略回测 - 沪银主力 2025年（模拟数据）
使用模拟的白银价格数据演示策略效果
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ==================== 参数配置 ====================
INITIAL_CAPITAL = 100000  # 初始资金
SHORT_MA = 5              # 短期均线
LONG_MA = 20              # 长期均线
SYMBOL = "SHFE.ag"        # 沪银
MULTIPLIER = 15           # 沪银1手=15千克

# ==================== 生成模拟沪银数据（2025年1-2月）====================
np.random.seed(2025)

# 生成60天的数据（2025年1月-2月）
n_days = 60
dates = []
current_date = datetime(2025, 1, 2)
while len(dates) < n_days:
    # 跳过周末
    if current_date.weekday() < 5:
        dates.append(current_date)
    current_date += timedelta(days=1)

# 生成模拟价格（沪银约6000-8000元/千克波动）
base_price = 7500
trend = np.sin(np.linspace(0, 4*np.pi, n_days)) * 0.03  # 波动趋势
noise = np.random.normal(0, 0.015, n_days)  # 随机噪声
returns = trend + noise
prices = base_price * np.exp(np.cumsum(returns))

# 创建DataFrame
df = pd.DataFrame({
    'date': dates,
    'close': prices,
    'open': prices * (1 + np.random.normal(0, 0.008, n_days)),
    'high': prices * (1 + np.abs(np.random.normal(0.012, 0.005, n_days))),
    'low': prices * (1 - np.abs(np.random.normal(0.012, 0.005, n_days))),
})

# 计算均线
df['short_ma'] = df['close'].rolling(window=SHORT_MA).mean()
df['long_ma'] = df['close'].rolling(window=LONG_MA).mean()

# ==================== 回测逻辑 ====================
capital = INITIAL_CAPITAL
position = 0
entry_price = 0
trades = []

print("=" * 70)
print("🚀 双均线策略回测 - 沪银主力（模拟数据）")
print("=" * 70)
print(f"📊 合约: {SYMBOL}")
print(f"📅 回测区间: {df['date'].iloc[0].strftime('%Y-%m-%d')} ~ {df['date'].iloc[-1].strftime('%Y-%m-%d')}")
print(f"📈 均线参数: 短期{SHORT_MA}日 | 长期{LONG_MA}日")
print(f"💰 初始资金: {INITIAL_CAPITAL:,}元")
print(f"📦 合约规格: {MULTIPLIER}千克/手")
print("=" * 70)

for i in range(LONG_MA, len(df)):
    row = df.iloc[i]
    prev_row = df.iloc[i-1]
    
    price = row['close']
    date = row['date']
    
    # 检测金叉死叉
    golden_cross = prev_row['short_ma'] <= prev_row['long_ma'] and row['short_ma'] > row['long_ma']
    dead_cross = prev_row['short_ma'] >= prev_row['long_ma'] and row['short_ma'] < row['long_ma']
    
    # 交易逻辑（沪银保证金约12%，1手约13500元）
    if golden_cross and position == 0:
        # 金叉买入（1手）
        volume = 1
        margin = price * MULTIPLIER * 0.12  # 12%保证金
        if capital >= margin:
            position = volume
            entry_price = price
            trades.append({
                'date': date,
                'action': '买入',
                'price': price,
                'volume': volume,
                'margin': margin
            })
            print(f"🟢 [{date.strftime('%Y-%m-%d')}] 金叉买入 | 价格: {price:.2f}元/千克 | 保证金: {margin:,.2f}元")
    
    elif dead_cross and position > 0:
        # 死叉卖出
        profit = (price - entry_price) * MULTIPLIER * position
        capital += profit
        margin_return = entry_price * MULTIPLIER * 0.12
        trades.append({
            'date': date,
            'action': '卖出',
            'price': price,
            'volume': position,
            'profit': profit,
            'capital': capital
        })
        print(f"🔴 [{date.strftime('%Y-%m-%d')}] 死叉卖出 | 价格: {price:.2f}元/千克 | 盈亏: {profit:+,.2f}元")
        position = 0

# 计算最终权益
final_price = df['close'].iloc[-1]
if position > 0:
    unrealized = (final_price - entry_price) * MULTIPLIER * position
    final_capital = capital + unrealized
else:
    final_capital = capital
    unrealized = 0

# ==================== 绩效报告 ====================
trades_df = pd.DataFrame(trades)

print("\n" + "=" * 70)
print("📊 回测结果报告")
print("=" * 70)

total_return = (final_capital - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
num_trades = len(trades_df[trades_df['action'] == '卖出'])

print(f"💰 初始资金: {INITIAL_CAPITAL:,.2f}元")
print(f"💰 最终权益: {final_capital:,.2f}元")
print(f"📈 总收益率: {total_return:.2f}%")
print(f"🔄 交易次数: {num_trades}次")

if num_trades > 0:
    profits = trades_df[trades_df['action'] == '卖出']['profit'].values
    win_rate = len([p for p in profits if p > 0]) / len(profits) * 100
    total_profit = np.sum(profits)
    avg_profit = np.mean(profits)
    max_profit = np.max(profits)
    max_loss = np.min(profits)
    
    print(f"🎯 胜率: {win_rate:.1f}%")
    print(f"📊 总盈亏: {total_profit:+,.2f}元")
    print(f"📊 平均盈亏: {avg_profit:+,.2f}元/笔")
    print(f"📈 最大盈利: {max_profit:+,.2f}元")
    print(f"📉 最大亏损: {max_loss:+,.2f}元")
else:
    print("⚠️ 未产生完整交易（无卖出记录）")

# 持仓情况
if position > 0:
    print(f"\n📦 持仓情况: {position}手 | 持仓均价: {entry_price:.2f}元/千克")
    print(f"💵 浮动盈亏: {unrealized:+,.2f}元")

print("\n" + "=" * 70)
print("📝 详细交易记录")
print("=" * 70)

# 格式化输出
display_df = trades_df.copy()
display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
display_df['price'] = display_df['price'].apply(lambda x: f"{x:.2f}")
if 'profit' in display_df.columns:
    display_df['profit'] = display_df['profit'].apply(lambda x: f"{x:+,.2f}" if pd.notna(x) else "")
if 'capital' in display_df.columns:
    display_df['capital'] = display_df['capital'].apply(lambda x: f"{x:,.2f}" if pd.notna(x) else "")

print(display_df.to_string(index=False))

print("\n" + "=" * 70)
print("📈 价格走势摘要")
print("=" * 70)
print(f"   起始价格: {df['close'].iloc[0]:.2f}元/千克")
print(f"   结束价格: {df['close'].iloc[-1]:.2f}元/千克")
print(f"   最高价: {df['high'].max():.2f}元/千克")
print(f"   最低价: {df['low'].min():.2f}元/千克")
print(f"   价格变动: {((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100:.2f}%")
print("=" * 70)

# 保存CSV
csv_data = []
for _, row in trades_df.iterrows():
    csv_data.append({
        'date': row['date'].strftime('%Y-%m-%d'),
        'action': row['action'],
        'price': f"{row['price']:.2f}",
        'volume': row['volume'],
        'profit': row.get('profit', '')
    })
pd.DataFrame(csv_data).to_csv('/root/.openclaw/workspace/tqsdk/trades_ag2025.csv', index=False)
print("\n💾 交易数据已保存: trades_ag2025.csv")
