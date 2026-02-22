#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双均线策略回测 - 沪银2025年全年（自动换月）
支持主力合约自动切换
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ==================== 参数配置 ====================
INITIAL_CAPITAL = 100000   # 初始资金
SHORT_MA = 5               # 短期均线
LONG_MA = 20               # 长期均线
MULTIPLIER = 15            # 沪银15千克/手
MARGIN_RATE = 0.12         # 保证金率12%
ROLL_DAYS = 5              # 到期前5天换月

# ==================== 生成2025年全年模拟数据 ====================
np.random.seed(2025)

# 生成2025年全年交易日（约250天）
dates = []
current_date = datetime(2025, 1, 2)
while current_date.year == 2025:
    if current_date.weekday() < 5:  # 周一到周五
        dates.append(current_date)
    current_date += timedelta(days=1)

# 生成模拟价格（考虑换月价差）
n_days = len(dates)
base_price = 7500
trend = np.sin(np.linspace(0, 8*np.pi, n_days)) * 0.05  # 更大周期
noise = np.random.normal(0, 0.012, n_days)
returns = trend + noise
prices = base_price * np.exp(np.cumsum(returns))

# 添加换月跳价（模拟不同合约价差）
for i in range(len(prices)):
    # 每月15号附近模拟换月跳价
    day = dates[i].day
    if 12 <= day <= 18:
        prices[i] *= (1 + np.random.normal(0, 0.005))

# 创建DataFrame
df = pd.DataFrame({
    'date': dates,
    'close': prices,
    'open': prices * (1 + np.random.normal(0, 0.008, n_days)),
    'high': prices * (1 + np.abs(np.random.normal(0.015, 0.005, n_days))),
    'low': prices * (1 - np.abs(np.random.normal(0.015, 0.005, n_days))),
})

# 生成合约代码（模拟主力换月）
contracts = []
for i, date in enumerate(dates):
    # 根据月份确定主力合约
    # 1-2月: 2502, 2-3月: 2504, 4-5月: 2506, 6-7月: 2508, 8-9月: 2510, 10-12月: 2512
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

# ==================== 回测逻辑（带换月）====================
class BacktestEngine:
    def __init__(self):
        self.capital = INITIAL_CAPITAL
        self.position = 0
        self.entry_price = 0
        self.current_contract = None
        self.trades = []
        self.daily_records = []
        
    def check_rollover(self, date, contract):
        """检查是否需要换月"""
        # 获取合约到期月份
        contract_month = int(contract[-2:])
        
        # 如果合约即将到期，需要换月
        if date.month >= contract_month - 1 and date.day >= 25:
            return True
        
        # 如果合约变了
        if self.current_contract and contract != self.current_contract:
            return True
            
        return False
    
    def rollover_position(self, date, old_contract, new_contract, price):
        """执行换月"""
        if self.position > 0:
            # 平旧仓
            profit = (price - self.entry_price) * MULTIPLIER * self.position
            self.trades.append({
                'date': date,
                'action': '换月平仓',
                'contract': old_contract,
                'price': price,
                'volume': self.position,
                'profit': profit
            })
            print(f"🔄 [{date.strftime('%Y-%m-%d')}] 换月: {old_contract} → {new_contract} | 盈亏: {profit:+,.2f}元")
            
            # 开新仓（保持持仓）
            self.entry_price = price
            self.trades.append({
                'date': date,
                'action': '换月开仓',
                'contract': new_contract,
                'price': price,
                'volume': self.position
            })
        
        self.current_contract = new_contract
    
    def run(self, df):
        print("=" * 75)
        print("🚀 双均线策略回测 - 沪银2025年全年（自动换月）")
        print("=" * 75)
        print(f"📅 回测区间: {df['date'].iloc[0].strftime('%Y-%m-%d')} ~ {df['date'].iloc[-1].strftime('%Y-%m-%d')}")
        print(f"📈 均线参数: 短期{SHORT_MA}日 | 长期{LONG_MA}日")
        print(f"💰 初始资金: {INITIAL_CAPITAL:,}元")
        print(f"📦 合约规格: {MULTIPLIER}千克/手 | 保证金: {MARGIN_RATE*100:.0f}%")
        print("=" * 75)
        
        for i in range(LONG_MA, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i-1]
            
            date = row['date']
            price = row['close']
            contract = row['contract']
            
            # 检查换月
            if self.current_contract is None:
                self.current_contract = contract
            elif self.check_rollover(date, contract):
                self.rollover_position(date, self.current_contract, contract, price)
                self.current_contract = contract
            
            # 检测金叉死叉
            golden_cross = prev_row['short_ma'] <= prev_row['long_ma'] and row['short_ma'] > row['long_ma']
            dead_cross = prev_row['short_ma'] >= prev_row['long_ma'] and row['short_ma'] < row['long_ma']
            
            # 交易逻辑
            if golden_cross and self.position == 0:
                margin = price * MULTIPLIER * MARGIN_RATE
                if self.capital >= margin:
                    self.position = 1
                    self.entry_price = price
                    self.trades.append({
                        'date': date,
                        'action': '金叉买入',
                        'contract': contract,
                        'price': price,
                        'volume': 1,
                        'margin': margin
                    })
                    print(f"🟢 [{date.strftime('%Y-%m-%d')}] 金叉买入 {contract} | 价格: {price:.2f} | 保证金: {margin:,.0f}元")
            
            elif dead_cross and self.position > 0:
                profit = (price - self.entry_price) * MULTIPLIER * self.position
                self.capital += profit
                self.trades.append({
                    'date': date,
                    'action': '死叉卖出',
                    'contract': contract,
                    'price': price,
                    'volume': self.position,
                    'profit': profit,
                    'capital': self.capital
                })
                print(f"🔴 [{date.strftime('%Y-%m-%d')}] 死叉卖出 {contract} | 价格: {price:.2f} | 盈亏: {profit:+,.2f}元")
                self.position = 0
            
            # 记录每日
            unrealized = 0
            if self.position > 0:
                unrealized = (price - self.entry_price) * MULTIPLIER * self.position
            
            self.daily_records.append({
                'date': date,
                'contract': contract,
                'close': price,
                'position': self.position,
                'capital': self.capital,
                'unrealized': unrealized,
                'equity': self.capital + unrealized
            })
        
        self.report()
    
    def report(self):
        # 计算最终权益
        final_record = self.daily_records[-1]
        final_capital = final_record['equity']
        
        trades_df = pd.DataFrame(self.trades)
        daily_df = pd.DataFrame(self.daily_records)
        
        print("\n" + "=" * 75)
        print("📊 回测结果报告")
        print("=" * 75)
        
        total_return = (final_capital - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
        
        # 统计交易
        buy_trades = trades_df[trades_df['action'] == '金叉买入']
        sell_trades = trades_df[trades_df['action'] == '死叉卖出']
        rollover_trades = trades_df[trades_df['action'].str.contains('换月', na=False)]
        
        num_rounds = len(sell_trades)
        
        print(f"💰 初始资金: {INITIAL_CAPITAL:,.2f}元")
        print(f"💰 最终权益: {final_capital:,.2f}元")
        print(f"📈 总收益率: {total_return:.2f}%")
        print(f"🔄 完整交易: {num_rounds}次")
        print(f"🔄 换月次数: {len(rollover_trades)//2}次")
        
        if num_rounds > 0:
            profits = sell_trades['profit'].values
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
        
        # 当前持仓
        if self.position > 0:
            unrealized = (daily_df['close'].iloc[-1] - self.entry_price) * MULTIPLIER
            print(f"\n📦 持仓情况: {self.position}手 {self.current_contract}")
            print(f"💵 浮动盈亏: {unrealized:+,.2f}元")
        
        print("\n" + "=" * 75)
        print("📝 详细交易记录")
        print("=" * 75)
        
        display_df = trades_df.copy()
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
        display_df['price'] = display_df['price'].apply(lambda x: f"{x:.2f}")
        if 'profit' in display_df.columns:
            display_df['profit'] = display_df['profit'].apply(lambda x: f"{x:+,.2f}" if pd.notna(x) else "")
        if 'capital' in display_df.columns:
            display_df['capital'] = display_df['capital'].apply(lambda x: f"{x:,.2f}" if pd.notna(x) else "")
        
        print(display_df.to_string(index=False))
        
        print("\n" + "=" * 75)
        print("📈 价格走势摘要")
        print("=" * 75)
        print(f"   起始价格: {daily_df['close'].iloc[0]:.2f}元/千克")
        print(f"   结束价格: {daily_df['close'].iloc[-1]:.2f}元/千克")
        print(f"   最高价: {daily_df['close'].max():.2f}元/千克")
        print(f"   最低价: {daily_df['close'].min():.2f}元/千克")
        print(f"   价格变动: {((daily_df['close'].iloc[-1] / daily_df['close'].iloc[0]) - 1) * 100:.2f}%")
        print("=" * 75)
        
        # 保存CSV
        csv_data = []
        for _, row in trades_df.iterrows():
            csv_data.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'action': row['action'],
                'contract': row['contract'],
                'price': f"{row['price']:.2f}",
                'volume': row['volume'],
                'profit': row.get('profit', '')
            })
        pd.DataFrame(csv_data).to_csv('/root/.openclaw/workspace/tqsdk/trades_ag2025_full.csv', index=False)
        print("\n💾 交易数据已保存: trades_ag2025_full.csv")

# 运行回测
engine = BacktestEngine()
engine.run(df)
