#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双均线策略回测 - 沪银2025年全年（标准连续合约）
换月逻辑：平仓老合约 → 按原方向开新合约 → 继续执行双均线
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ==================== 参数配置 ====================
INITIAL_CAPITAL = 100000   # 初始资金
SHORT_MA = 5               # 短期均线
LONG_MA = 20               # 长期均线
MULTIPLIER = 15            # 沪银15千克/手

# ==================== 生成2025年真实风格数据 ====================
np.random.seed(42)

# 生成交易日
dates = []
current_date = datetime(2025, 1, 2)
while current_date.year == 2025:
    if current_date.weekday() < 5:
        dates.append(current_date)
    current_date += timedelta(days=1)

n_days = len(dates)

# 生成更真实的价格走势（类似2024年白银震荡行情）
base_price = 6000
returns = np.random.normal(0.0003, 0.012, n_days)  # 日收益0.03%，波动1.2%
prices = base_price * np.exp(np.cumsum(returns))

# 限制价格在合理范围（白银实际波动区间5000-8000）
prices = np.clip(prices, 5000, 8000)

# 创建DataFrame
df = pd.DataFrame({
    'date': dates,
    'close': prices,
    'open': prices * (1 + np.random.normal(0, 0.005, n_days)),
    'high': prices * (1 + np.abs(np.random.normal(0.008, 0.003, n_days))),
    'low': prices * (1 - np.abs(np.random.normal(0.008, 0.003, n_days))),
})

# 生成合约代码（主力换月：1-2月2502, 3-4月2504, 5-6月2506, 7-8月2508, 9-10月2510, 11-12月2512）
contracts = []
for date in dates:
    month = date.month
    if month <= 2:
        contract = "ag2502"
    elif month <= 4:
        contract = "ag2504"
    elif month <= 6:
        contract = "ag2506"
    elif month <= 8:
        contract = "ag2508"
    elif month <= 10:
        contract = "ag2510"
    else:
        contract = "ag2512"
    contracts.append(contract)

df['contract'] = contracts

# 计算均线
df['short_ma'] = df['close'].rolling(window=SHORT_MA).mean()
df['long_ma'] = df['close'].rolling(window=LONG_MA).mean()

# ==================== 回测主逻辑 ====================
print("=" * 80)
print("🚀 双均线策略回测 - 沪银2025年全年（标准连续合约）")
print("=" * 80)
print(f"📅 回测区间: {df['date'].iloc[0].strftime('%Y-%m-%d')} ~ {df['date'].iloc[-1].strftime('%Y-%m-%d')}")
print(f"📈 均线参数: 短期{SHORT_MA}日 | 长期{LONG_MA}日")
print(f"💰 初始资金: {INITIAL_CAPITAL:,}元")
print(f"📦 合约规格: {MULTIPLIER}千克/手")
print("=" * 80)

# 状态变量
capital = INITIAL_CAPITAL
position = 0          # 0=空仓, 1=多头
entry_price = 0
entry_contract = None
current_contract = None

trades = []
daily_records = []

for i in range(LONG_MA, len(df)):
    row = df.iloc[i]
    prev_row = df.iloc[i-1]
    
    date = row['date']
    price = row['close']
    contract = row['contract']
    
    # ============ 换月处理 ============
    if current_contract is None:
        current_contract = contract
    elif contract != current_contract and position != 0:
        # 换月：平老仓 → 开新仓（同方向）
        old_contract = current_contract
        
        # 平老合约
        profit = (price - entry_price) * MULTIPLIER * position
        capital += profit
        trades.append({
            'date': date,
            'action': '换月平仓',
            'contract': old_contract,
            'price': price,
            'volume': position,
            'profit': profit,
            'capital': capital,
            'note': f'换月至{contract}'
        })
        print(f"🔄 [{date.strftime('%Y-%m-%d')}] 换月: {old_contract} → {contract} | 平仓盈亏: {profit:+,.2f}元")
        
        # 开新合约（同方向同数量）
        current_contract = contract
        entry_price = price
        entry_contract = contract
        trades.append({
            'date': date,
            'action': '换月开仓',
            'contract': contract,
            'price': price,
            'volume': position,
            'note': f'延续原持仓'
        })
        print(f"   新合约开仓: {contract} 价格: {price:.2f} 持仓: {position}手")
    
    # ============ 双均线交易逻辑 ============
    # 检测金叉死叉
    golden_cross = prev_row['short_ma'] <= prev_row['long_ma'] and row['short_ma'] > row['long_ma']
    dead_cross = prev_row['short_ma'] >= prev_row['long_ma'] and row['short_ma'] < row['long_ma']
    
    if golden_cross and position == 0:
        # 金叉买入（开多）
        position = 1
        entry_price = price
        entry_contract = contract
        margin = price * MULTIPLIER * 0.12
        trades.append({
            'date': date,
            'action': '金叉买入',
            'contract': contract,
            'price': price,
            'volume': 1,
            'margin': margin
        })
        print(f"🟢 [{date.strftime('%Y-%m-%d')}] 金叉买入 {contract} | 价格: {price:.2f} | 保证金: {margin:,.0f}元")
    
    elif dead_cross and position > 0:
        # 死叉卖出（平多）
        profit = (price - entry_price) * MULTIPLIER * position
        capital += profit
        trades.append({
            'date': date,
            'action': '死叉卖出',
            'contract': contract,
            'price': price,
            'volume': position,
            'profit': profit,
            'capital': capital
        })
        print(f"🔴 [{date.strftime('%Y-%m-%d')}] 死叉卖出 {contract} | 价格: {price:.2f} | 盈亏: {profit:+,.2f}元")
        position = 0
        entry_price = 0
        entry_contract = None
    
    # 记录每日状态
    unrealized = 0
    if position > 0:
        unrealized = (price - entry_price) * MULTIPLIER * position
    
    daily_records.append({
        'date': date,
        'contract': contract,
        'close': price,
        'short_ma': row['short_ma'],
        'long_ma': row['long_ma'],
        'position': position,
        'capital': capital,
        'unrealized': unrealized,
        'equity': capital + unrealized
    })

# ==================== 最终结算 ====================
final_price = df['close'].iloc[-1]
final_contract = df['contract'].iloc[-1]

if position > 0:
    # 强制平仓（回测结束）
    profit = (final_price - entry_price) * MULTIPLIER * position
    capital += profit
    trades.append({
        'date': df['date'].iloc[-1],
        'action': '期末平仓',
        'contract': final_contract,
        'price': final_price,
        'volume': position,
        'profit': profit,
        'capital': capital
    })
    print(f"\n🔚 [{df['date'].iloc[-1].strftime('%Y-%m-%d')}] 期末平仓 {final_contract} | 价格: {final_price:.2f} | 盈亏: {profit:+,.2f}元")
    position = 0

# ==================== 绩效报告 ====================
final_capital = capital
trades_df = pd.DataFrame(trades)
daily_df = pd.DataFrame(daily_records)

print("\n" + "=" * 80)
print("📊 回测结果报告")
print("=" * 80)

total_return = (final_capital - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100

# 统计完整交易（一买一卖）
buy_trades = trades_df[trades_df['action'] == '金叉买入']
sell_trades = trades_df[trades_df['action'].isin(['死叉卖出', '期末平仓'])]
rollover_close = trades_df[trades_df['action'] == '换月平仓']

num_rounds = len(buy_trades)
num_rollovers = len(rollover_close)

print(f"💰 初始资金: {INITIAL_CAPITAL:,.2f}元")
print(f"💰 最终权益: {final_capital:,.2f}元")
print(f"📈 总收益率: {total_return:+.2f}%")
print(f"🔄 完整交易次数: {num_rounds}次")
print(f"🔄 换月次数: {num_rollovers}次")

# 计算盈亏统计（只统计完整交易的盈亏）
complete_profits = []
for _, sell_row in sell_trades.iterrows():
    if pd.notna(sell_row.get('profit')):
        complete_profits.append(sell_row['profit'])

# 加上换月盈亏
for _, roll_row in rollover_close.iterrows():
    if pd.notna(roll_row.get('profit')):
        complete_profits.append(roll_row['profit'])

if complete_profits:
    profits_array = np.array(complete_profits)
    win_rate = len(profits_array[profits_array > 0]) / len(profits_array) * 100
    total_profit = np.sum(profits_array)
    avg_profit = np.mean(profits_array)
    max_profit = np.max(profits_array)
    max_loss = np.min(profits_array)
    
    print(f"🎯 胜率: {win_rate:.1f}%")
    print(f"📊 总盈亏: {total_profit:+,.2f}元")
    print(f"📊 平均盈亏: {avg_profit:+,.2f}元/笔")
    print(f"📈 最大单笔盈利: {max_profit:+,.2f}元")
    print(f"📉 最大单笔亏损: {max_loss:+,.2f}元")
else:
    print("⚠️ 无完整交易记录")

# 显示明细
print("\n" + "=" * 80)
print("📝 详细交易记录")
print("=" * 80)

display_df = trades_df[['date', 'action', 'contract', 'price', 'profit']].copy()
display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
display_df['price'] = display_df['price'].apply(lambda x: f"{x:.2f}")
display_df['profit'] = display_df['profit'].apply(lambda x: f"{x:+,.2f}" if pd.notna(x) else "")

for _, row in display_df.iterrows():
    print(f"{row['date']} | {row['action']:8s} | {row['contract']} | 价格: {row['price']:>8s} | 盈亏: {row['profit']:>12s}")

print("\n" + "=" * 80)
print("📈 价格走势摘要")
print("=" * 80)
print(f"   起始价格: {daily_df['close'].iloc[0]:.2f}元/千克")
print(f"   结束价格: {daily_df['close'].iloc[-1]:.2f}元/千克")
print(f"   最高价: {daily_df['close'].max():.2f}元/千克")
print(f"   最低价: {daily_df['close'].min():.2f}元/千克")
print(f"   价格变动: {((daily_df['close'].iloc[-1] / daily_df['close'].iloc[0]) - 1) * 100:+.2f}%")
print("=" * 80)

# 保存CSV
csv_data = []
for _, row in trades_df.iterrows():
    csv_data.append({
        'date': row['date'].strftime('%Y-%m-%d'),
        'action': row['action'],
        'contract': row['contract'],
        'price': f"{row['price']:.2f}",
        'profit': f"{row.get('profit', 0):.2f}" if pd.notna(row.get('profit')) else ""
    })
pd.DataFrame(csv_data).to_csv('/root/.openclaw/workspace/tqsdk/trades_ag2025_std.csv', index=False)
print("\n💾 交易数据已保存: trades_ag2025_std.csv")
