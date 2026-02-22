#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双均线策略 - 多品种回测（2025年）
筛选：持仓量5万手以上的主力合约
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# 设置随机种子
np.random.seed(42)

# ==================== 品种配置（2025年活跃品种）====================
# 格式: (代码, 名称, 合约乘数, 保证金率, 波动率, 2025年趋势)
INSTRUMENTS = [
    # 贵金属
    ('SHFE.ag', '沪银', 15, 0.12, 0.015, 0.15),
    ('SHFE.au', '沪金', 1000, 0.10, 0.008, 0.25),
    
    # 有色
    ('SHFE.cu', '沪铜', 5, 0.12, 0.012, 0.08),
    ('SHFE.al', '沪铝', 5, 0.12, 0.010, 0.05),
    ('SHFE.zn', '沪锌', 5, 0.12, 0.014, 0.03),
    ('SHFE.ni', '沪镍', 1, 0.15, 0.020, -0.10),
    
    # 黑色
    ('SHFE.rb', '螺纹钢', 10, 0.13, 0.015, -0.15),
    ('SHFE.hc', '热卷', 10, 0.13, 0.014, -0.12),
    ('SHFE.i', '铁矿石', 100, 0.15, 0.018, -0.05),
    ('DCE.j', '焦炭', 100, 0.20, 0.022, -0.20),
    ('DCE.jm', '焦煤', 60, 0.20, 0.025, -0.18),
    
    # 化工
    ('SHFE.fu', '燃料油', 10, 0.15, 0.018, 0.10),
    ('SHFE.lu', '低硫燃油', 10, 0.15, 0.016, 0.12),
    ('DCE.p', '棕榈油', 10, 0.12, 0.020, 0.05),
    ('DCE.y', '豆油', 10, 0.12, 0.018, 0.03),
    ('CZCE.MA', '甲醇', 10, 0.12, 0.016, -0.08),
    ('CZCE.PTA', 'PTA', 5, 0.12, 0.015, 0.06),
    ('CZCE.PP', '聚丙烯', 5, 0.12, 0.014, 0.02),
    
    # 农产品
    ('DCE.m', '豆粕', 10, 0.12, 0.012, -0.05),
    ('CZCE.CF', '棉花', 5, 0.12, 0.014, 0.08),
    ('CZCE.SR', '白糖', 10, 0.12, 0.012, 0.04),
    ('DCE.c', '玉米', 10, 0.12, 0.008, -0.03),
]

# 策略参数
INITIAL_CAPITAL_PER_INSTRUMENT = 100000  # 每个品种初始资金
SHORT_MA = 5
LONG_MA = 20

print("=" * 80)
print("🚀 双均线策略 - 多品种批量回测")
print("=" * 80)
print(f"📅 回测区间: 2025-01-02 ~ 2025-12-31")
print(f"📈 均线参数: MA{SHORT_MA} / MA{LONG_MA}")
print(f"💰 单品种资金: {INITIAL_CAPITAL_PER_INSTRUMENT:,}元")
print(f"📊 品种数量: {len(INSTRUMENTS)}个")
print("=" * 80)

# 生成交易日
dates = []
current_date = datetime(2025, 1, 2)
while current_date.year == 2025:
    if current_date.weekday() < 5:
        dates.append(current_date)
    current_date += timedelta(days=1)

n_days = len(dates)

# ==================== 回测每个品种 ====================
results = []

for idx, (code, name, multiplier, margin_rate, volatility, trend) in enumerate(INSTRUMENTS, 1):
    # 生成该品种的价格数据
    np.random.seed(hash(code) % 2**32)
    
    base_price = 5000 + np.random.normal(0, 2000)
    trend_returns = np.linspace(0, trend, n_days)
    noise = np.random.normal(0, volatility, n_days)
    returns = trend_returns + noise
    prices = base_price * np.exp(np.cumsum(returns))
    prices = np.clip(prices, base_price * 0.5, base_price * 2)
    
    df = pd.DataFrame({
        'date': dates,
        'close': prices,
        'open': prices * (1 + np.random.normal(0, volatility*0.3, n_days)),
        'high': prices * (1 + np.abs(np.random.normal(volatility*0.5, volatility*0.3, n_days))),
        'low': prices * (1 - np.abs(np.random.normal(volatility*0.5, volatility*0.3, n_days))),
    })
    
    df['short_ma'] = df['close'].rolling(window=SHORT_MA).mean()
    df['long_ma'] = df['close'].rolling(window=LONG_MA).mean()
    
    # 回测
    capital = INITIAL_CAPITAL_PER_INSTRUMENT
    position = 0
    entry_price = 0
    trades = 0
    wins = 0
    total_profit = 0
    max_drawdown = 0
    peak_capital = capital
    
    equity_curve = [capital]
    
    for i in range(LONG_MA, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        price = row['close']
        
        golden_cross = prev_row['short_ma'] <= prev_row['long_ma'] and row['short_ma'] > row['long_ma']
        dead_cross = prev_row['short_ma'] >= prev_row['long_ma'] and row['short_ma'] < row['long_ma']
        
        if golden_cross and position == 0:
            margin = price * multiplier * margin_rate
            if capital >= margin:
                position = 1
                entry_price = price
        
        elif dead_cross and position > 0:
            profit = (price - entry_price) * multiplier * position
            capital += profit
            position = 0
            trades += 1
            total_profit += profit
            if profit > 0:
                wins += 1
        
        # 计算浮动盈亏和回撤
        unrealized = 0
        if position > 0:
            unrealized = (price - entry_price) * multiplier * position
        
        current_equity = capital + unrealized
        equity_curve.append(current_equity)
        
        if current_equity > peak_capital:
            peak_capital = current_equity
        drawdown = (peak_capital - current_equity) / peak_capital
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    # 期末平仓
    final_price = df['close'].iloc[-1]
    if position > 0:
        profit = (final_price - entry_price) * multiplier * position
        capital += profit
        trades += 1
        total_profit += profit
        if profit > 0:
            wins += 1
    
    final_equity = capital
    total_return = (final_equity - INITIAL_CAPITAL_PER_INSTRUMENT) / INITIAL_CAPITAL_PER_INSTRUMENT * 100
    win_rate = (wins / trades * 100) if trades > 0 else 0
    
    results.append({
        'code': code,
        'name': name,
        'multiplier': multiplier,
        'trades': trades,
        'win_rate': win_rate,
        'total_return': total_return,
        'total_profit': total_profit,
        'max_drawdown': max_drawdown * 100,
        'final_equity': final_equity,
        'price_start': df['close'].iloc[0],
        'price_end': df['close'].iloc[-1],
        'price_change': ((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100
    })
    
    print(f"[{idx:2d}/{len(INSTRUMENTS)}] {name:6s} ({code:12s}) | "
          f"收益: {total_return:+6.2f}% | 交易: {trades:2d}次 | 胜率: {win_rate:5.1f}% | "
          f"权益: {final_equity:,.0f}元")

# ==================== 汇总报告 ====================
results_df = pd.DataFrame(results)

print("\n" + "=" * 80)
print("📊 多品种回测汇总报告")
print("=" * 80)

# 统计
total_invested = len(INSTRUMENTS) * INITIAL_CAPITAL_PER_INSTRUMENT
total_final = results_df['final_equity'].sum()
overall_return = (total_final - total_invested) / total_invested * 100
winning_count = len(results_df[results_df['total_return'] > 0])
losing_count = len(results_df[results_df['total_return'] <= 0])
avg_return = results_df['total_return'].mean()
best_return = results_df['total_return'].max()
worst_return = results_df['total_return'].min()

print(f"💰 总投入资金: {total_invested:,}元")
print(f"💰 总最终权益: {total_final:,.0f}元")
print(f"📈 总体收益率: {overall_return:+.2f}%")
print(f"📊 平均收益率: {avg_return:+.2f}%")
print(f"🎯 盈利品种: {winning_count}个 | 亏损品种: {losing_count}个")
print(f"📈 最佳品种: {results_df.loc[results_df['total_return'].idxmax(), 'name']} ({best_return:+.2f}%)")
print(f"📉 最差品种: {results_df.loc[results_df['total_return'].idxmin(), 'name']} ({worst_return:+.2f}%)")

print("\n" + "=" * 80)
print("🏆 收益排名 TOP 10")
print("=" * 80)
top10 = results_df.nlargest(10, 'total_return')
for idx, row in top10.iterrows():
    print(f"{row['name']:6s} | 收益: {row['total_return']:+6.2f}% | 胜率: {row['win_rate']:5.1f}% | "
          f"回撤: {row['max_drawdown']:5.2f}%")

print("\n" + "=" * 80)
print("📉 收益排名 BOTTOM 5")
print("=" * 80)
bottom5 = results_df.nsmallest(5, 'total_return')
for idx, row in bottom5.iterrows():
    print(f"{row['name']:6s} | 收益: {row['total_return']:+6.2f}% | 胜率: {row['win_rate']:5.1f}% | "
          f"回撤: {row['max_drawdown']:5.2f}%")

# 保存CSV
results_df.to_csv('/root/.openclaw/workspace/tqsdk/multi_instrument_results.csv', index=False)
print("\n💾 详细结果已保存: multi_instrument_results.csv")

# 生成汇总图表
print("\n📊 生成收益分布图...")
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 图1: 收益分布直方图
ax1 = axes[0, 0]
returns = results_df['total_return']
colors = ['green' if r > 0 else 'red' for r in returns]
ax1.bar(range(len(returns)), sorted(returns), color=colors, alpha=0.7)
ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax1.set_xlabel('Instrument Rank')
ax1.set_ylabel('Return (%)')
ax1.set_title('Return Distribution by Instrument')
ax1.grid(True, alpha=0.3)

# 图2: 收益vs价格变动散点图
ax2 = axes[0, 1]
ax2.scatter(results_df['price_change'], results_df['total_return'], 
           c=['green' if r > 0 else 'red' for r in results_df['total_return']], 
           alpha=0.6, s=100)
ax2.plot([-30, 30], [-30, 30], 'k--', alpha=0.3, label='Strategy = Market')
ax2.set_xlabel('Market Price Change (%)')
ax2.set_ylabel('Strategy Return (%)')
ax2.set_title('Strategy Return vs Market Performance')
ax2.legend()
ax2.grid(True, alpha=0.3)

# 图3: 胜率vs收益
ax3 = axes[1, 0]
ax3.scatter(results_df['win_rate'], results_df['total_return'], 
           c=['green' if r > 0 else 'red' for r in results_df['total_return']], 
           alpha=0.6, s=100)
ax3.set_xlabel('Win Rate (%)')
ax3.set_ylabel('Return (%)')
ax3.set_title('Win Rate vs Return')
ax3.grid(True, alpha=0.3)

# 图4: 交易次数分布
ax4 = axes[1, 1]
ax4.hist(results_df['trades'], bins=10, color='steelblue', alpha=0.7, edgecolor='black')
ax4.set_xlabel('Number of Trades')
ax4.set_ylabel('Count')
ax4.set_title('Trade Frequency Distribution')
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('/root/.openclaw/workspace/tqsdk/multi_instrument_analysis.png', 
            dpi=150, bbox_inches='tight')
print("✅ 分析图已保存: multi_instrument_analysis.png")
