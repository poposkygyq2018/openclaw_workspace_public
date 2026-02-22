#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双均线策略回测 - 沪银主力合约 2025年
"""

from tqsdk import TqApi, TqBacktest, TqAuth
from tqsdk.ta import MA
from datetime import date
import pandas as pd

# ==================== 回测配置 ====================
SYMBOL = "SHFE.ag2502"        # 沪银2502合约
START_DATE = date(2024, 10, 1)  # 从2024年10月开始（合约上市时间）
END_DATE = date(2025, 2, 28)   # 到2月底
SHORT_MA = 5                   # 短期均线
LONG_MA = 20                   # 长期均线
INITIAL_CAPITAL = 100000       # 初始资金

# 创建回测API
api = TqApi(
    backtest=TqBacktest(start_dt=START_DATE, end_dt=END_DATE),
    auth=TqAuth("13585505816", "02123276"),
    web_gui=False
)

# 订阅行情
klines = api.get_kline_serial(SYMBOL, 86400)  # 日K线
quote = api.get_quote(SYMBOL)
account = api.get_account()

# 记录
trades = []
position_history = []

print("=" * 70)
print(f"🚀 双均线策略回测 - 沪银主力")
print(f"📊 合约: {SYMBOL}")
print(f"📅 回测区间: {START_DATE} ~ {END_DATE}")
print(f"📈 均线参数: 短期{SHORT_MA}日 | 长期{LONG_MA}日")
print(f"💰 初始资金: {INITIAL_CAPITAL:,}元")
print("=" * 70)

# 回测主循环
while True:
    api.wait_update()
    
    if api.is_changing(klines, "close"):
        current_date = pd.Timestamp(klines.datetime.iloc[-1], unit='ns')
        
        # 确保数据足够
        if len(klines) < LONG_MA + 5:
            continue
        
        # 计算均线
        short_ma = MA(klines, SHORT_MA).iloc[-1]
        long_ma = MA(klines, LONG_MA).iloc[-1]
        prev_short = MA(klines, SHORT_MA).iloc[-2]
        prev_long = MA(klines, LONG_MA).iloc[-2]
        
        # 当前价格和持仓
        close_price = klines.close.iloc[-1]
        position = api.get_position(SYMBOL)
        current_pos = position.pos_long - position.pos_short
        
        # 检测金叉死叉
        golden_cross = prev_short <= prev_long and short_ma > long_ma
        dead_cross = prev_short >= prev_long and short_ma < long_ma
        
        # 交易逻辑
        if golden_cross and current_pos == 0:
            # 金叉买入（1手，白银保证金较高）
            volume = 1
            api.insert_order(symbol=SYMBOL, direction="BUY", offset="OPEN",
                            volume=volume, limit_price=close_price)
            trades.append({
                'date': current_date,
                'action': '买入',
                'price': close_price,
                'volume': volume,
                'ma_short': short_ma,
                'ma_long': long_ma
            })
            print(f"🟢 [{current_date.strftime('%Y-%m-%d')}] 金叉买入 | 价格: {close_price:.2f} | 数量: {volume}手")
        
        elif dead_cross and current_pos > 0:
            # 死叉卖出
            api.insert_order(symbol=SYMBOL, direction="SELL", offset="CLOSE",
                            volume=current_pos, limit_price=close_price)
            trades.append({
                'date': current_date,
                'action': '卖出',
                'price': close_price,
                'volume': current_pos,
                'ma_short': short_ma,
                'ma_long': long_ma
            })
            print(f"🔴 [{current_date.strftime('%Y-%m-%d')}] 死叉卖出 | 价格: {close_price:.2f} | 数量: {current_pos}手")
        
        # 记录持仓
        position_history.append({
            'date': current_date,
            'close': close_price,
            'short_ma': short_ma,
            'long_ma': long_ma,
            'position': current_pos,
            'equity': account.balance + position.float_profit_long
        })

# 回测结束
api.close()

print("\n" + "=" * 70)
print("📊 回测结果报告")
print("=" * 70)

df_trades = pd.DataFrame(trades)
df_position = pd.DataFrame(position_history)

if len(df_position) > 0:
    final_equity = df_position['equity'].iloc[-1]
    total_return = (final_equity - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
    
    # 计算交易次数
    num_trades = len(df_trades[df_trades['action'] == '卖出'])
    
    # 计算盈亏
    profits = []
    buy_price = None
    for _, row in df_trades.iterrows():
        if row['action'] == '买入':
            buy_price = row['price']
        elif row['action'] == '卖出' and buy_price:
            profit = (row['price'] - buy_price) * 15  # 沪银1手=15kg
            profits.append(profit)
            buy_price = None
    
    if profits:
        win_rate = len([p for p in profits if p > 0]) / len(profits) * 100
        total_profit = sum(profits)
        avg_profit = total_profit / len(profits)
        max_profit = max(profits)
        max_loss = min(profits)
    else:
        win_rate = total_profit = avg_profit = max_profit = max_loss = 0
    
    print(f"💰 最终权益: {final_equity:,.2f}元")
    print(f"📈 总收益率: {total_return:.2f}%")
    print(f"🔄 交易次数: {num_trades}次")
    print(f"🎯 胜率: {win_rate:.1f}%")
    print(f"📊 总盈亏: {total_profit:+,.2f}元")
    print(f"📊 平均盈亏: {avg_profit:+,.2f}元/笔")
    print(f"📈 最大盈利: {max_profit:+,.2f}元")
    print(f"📉 最大亏损: {max_loss:+,.2f}元")
    
    print("\n📝 详细交易记录:")
    print(df_trades.to_string(index=False))
else:
    print("⚠️ 无交易数据，请检查合约代码和时间范围")

print("=" * 70)
