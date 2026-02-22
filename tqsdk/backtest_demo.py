#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双均线策略 - 模拟数据回测演示
使用随机生成的价格数据演示策略逻辑
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ==================== 参数配置 ====================
INITIAL_CAPITAL = 100000  # 初始资金
SHORT_MA = 5              # 短期均线
LONG_MA = 20              # 长期均线
SYMBOL = "DEMO_CONTRACT"  # 模拟合约

# ==================== 生成模拟数据 ====================
np.random.seed(42)  # 固定随机种子，结果可复现

# 生成100天的模拟价格数据
n_days = 100
dates = [datetime(2024, 6, 1) + timedelta(days=i) for i in range(n_days)]

# 生成随机游走价格（带趋势）
returns = np.random.normal(0.001, 0.02, n_days)  # 日均收益0.1%，波动2%
prices = 3000 * np.exp(np.cumsum(returns))  # 从3000点开始

# 创建DataFrame
df = pd.DataFrame({
    'date': dates,
    'close': prices,
    'open': prices * (1 + np.random.normal(0, 0.005, n_days)),
    'high': prices * (1 + np.abs(np.random.normal(0.01, 0.005, n_days))),
    'low': prices * (1 - np.abs(np.random.normal(0.01, 0.005, n_days))),
})

# 计算均线
df['short_ma'] = df['close'].rolling(window=SHORT_MA).mean()
df['long_ma'] = df['close'].rolling(window=LONG_MA).mean()

# ==================== 回测逻辑 ====================
capital = INITIAL_CAPITAL
position = 0
trades = []

print("=" * 70)
print("🚀 双均线策略回测 - 模拟数据")
print("=" * 70)
print(f"📊 合约: {SYMBOL}")
print(f"📅 回测区间: {df['date'].iloc[0].strftime('%Y-%m-%d')} ~ {df['date'].iloc[-1].strftime('%Y-%m-%d')}")
print(f"📈 均线参数: 短期{SHORT_MA}日 | 长期{LONG_MA}日")
print(f"💰 初始资金: {INITIAL_CAPITAL:,}元")
print("=" * 70)

for i in range(LONG_MA, len(df)):
    row = df.iloc[i]
    prev_row = df.iloc[i-1]
    
    price = row['close']
    date = row['date']
    
    # 检测金叉死叉
    golden_cross = prev_row['short_ma'] <= prev_row['long_ma'] and row['short_ma'] > row['long_ma']
    dead_cross = prev_row['short_ma'] >= prev_row['long_ma'] and row['short_ma'] < row['long_ma']
    
    # 交易逻辑
    if golden_cross and position == 0:
        # 金叉买入（半仓）
        volume = int(capital / price / 2 / 10) * 10  # 整数手数
        if volume >= 1:
            position = volume
            entry_price = price
            trades.append({
                'date': date,
                'action': '买入',
                'price': price,
                'volume': volume,
                'value': price * volume,
                'capital': capital
            })
            print(f"🟢 [{date.strftime('%Y-%m-%d')}] 金叉买入 | 价格: {price:.2f} | 数量: {volume}手 | 金额: {price*volume:,.2f}")
    
    elif dead_cross and position > 0:
        # 死叉卖出
        profit = (price - entry_price) * position
        capital += profit
        trades.append({
            'date': date,
            'action': '卖出',
            'price': price,
            'volume': position,
            'value': price * position,
            'profit': profit,
            'capital': capital
        })
        print(f"🔴 [{date.strftime('%Y-%m-%d')}] 死叉卖出 | 价格: {price:.2f} | 数量: {position}手 | 盈亏: {profit:+,.2f}")
        position = 0

# 回测结束，计算最终权益
final_price = df['close'].iloc[-1]
if position > 0:
    unrealized = (final_price - entry_price) * position
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
    avg_profit = np.mean(profits)
    max_profit = np.max(profits)
    max_loss = np.min(profits)
    total_profit = np.sum(profits)
    
    print(f"🎯 胜率: {win_rate:.1f}%")
    print(f"📊 总盈亏: {total_profit:+,.2f}元")
    print(f"📊 平均盈亏: {avg_profit:+,.2f}元/笔")
    print(f"📈 最大盈利: {max_profit:+,.2f}元")
    print(f"📉 最大亏损: {max_loss:+,.2f}元")

# 持仓情况
if position > 0:
    print(f"\n📦 持仓情况: {position}手 | 持仓均价: {entry_price:.2f}")
    print(f"💵 浮动盈亏: {unrealized:+,.2f}元")

print("\n" + "=" * 70)
print("📝 详细交易记录")
print("=" * 70)
print(trades_df.to_string(index=False))
print("=" * 70)

# 生成价格走势和均线图的数据摘要
print("\n📈 价格走势摘要:")
print(f"   起始价格: {df['close'].iloc[0]:.2f}")
print(f"   结束价格: {df['close'].iloc[-1]:.2f}")
print(f"   最高价: {df['high'].max():.2f}")
print(f"   最低价: {df['low'].min():.2f}")
print(f"   价格变动: {((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100:.2f}%")
