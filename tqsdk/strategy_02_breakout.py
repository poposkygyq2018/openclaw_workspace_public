#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略2: 突破策略 (Breakout Strategy)
当价格突破前N根K线的最高价时买入，突破最低价时卖出
"""

from tqsdk import TqApi, TqSim

# 创建API实例
api = TqApi(TqSim())

# 订阅合约
symbol = "SHFE.cu2503"
klines = api.get_kline_serial(symbol, 300)  # 5分钟K线

# 设置参数
lookback_period = 20  # 回看周期

print(f"🚀 突破策略启动 - 合约: {symbol}")
print(f"📊 回看周期: {lookback_period}根K线")
print("-" * 50)

while True:
    api.wait_update()
    
    if len(klines) < lookback_period + 1:
        continue
    
    # 计算前N根K线的最高/最低价
    high_prices = klines.high.iloc[-lookback_period-1:-1]
    low_prices = klines.low.iloc[-lookback_period-1:-1]
    
    highest = high_prices.max()
    lowest = low_prices.min()
    
    # 当前价格
    current_high = klines.high.iloc[-1]
    current_low = klines.low.iloc[-1]
    close_price = klines.close.iloc[-1]
    
    # 获取持仓
    position = api.get_position(symbol)
    current_pos = position.pos_long - position.pos_short
    
    quote = api.get_quote(symbol)
    
    # 突破买入
    if current_high > highest and current_pos == 0:
        api.insert_order(symbol=symbol, direction="BUY", offset="OPEN",
                        volume=1, limit_price=quote.ask_price1)
        print(f"🟢 突破买入 | 价格: {close_price:.2f} | 突破: {highest:.2f}")
    
    # 跌破卖出
    elif current_low < lowest and current_pos > 0:
        api.insert_order(symbol=symbol, direction="SELL", offset="CLOSE",
                        volume=current_pos, limit_price=quote.bid_price1)
        print(f"🔴 跌破卖出 | 价格: {close_price:.2f} | 跌破: {lowest:.2f}")

api.close()
