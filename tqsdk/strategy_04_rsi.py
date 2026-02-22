#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略4: RSI超买超卖策略
RSI > 70 超买区域卖出，RSI < 30 超卖区域买入
"""

from tqsdk import TqApi, TqSim
from tqsdk.ta import RSI

# 创建API实例
api = TqApi(TqSim())

# 订阅合约
symbol = "SHFE.cu2503"
klines = api.get_kline_serial(symbol, 300)  # 5分钟K线

# RSI参数
rsi_period = 14
overbought = 70   # 超买线
oversold = 30     # 超卖线

print(f"🚀 RSI策略启动 - 合约: {symbol}")
print(f"📊 RSI周期: {rsi_period} | 超买: {overbought} | 超卖: {oversold}")
print("-" * 50)

while True:
    api.wait_update()
    
    if len(klines) < rsi_period + 1:
        continue
    
    # 计算RSI
    rsi_values = RSI(klines, rsi_period)
    current_rsi = rsi_values.iloc[-1]
    
    # 获取持仓和价格
    position = api.get_position(symbol)
    current_pos = position.pos_long - position.pos_short
    quote = api.get_quote(symbol)
    
    # 超卖买入
    if current_rsi < oversold and current_pos == 0:
        api.insert_order(symbol=symbol, direction="BUY", offset="OPEN",
                        volume=1, limit_price=quote.ask_price1)
        print(f"🟢 超卖买入 | RSI: {current_rsi:.2f} | 价格: {quote.last_price}")
    
    # 超买卖出
    elif current_rsi > overbought and current_pos > 0:
        api.insert_order(symbol=symbol, direction="SELL", offset="CLOSE",
                        volume=current_pos, limit_price=quote.bid_price1)
        print(f"🔴 超买卖出 | RSI: {current_rsi:.2f} | 价格: {quote.last_price}")
    
    # 定期打印RSI值
    if klines.close.iloc[-1] != klines.close.iloc[-2]:
        print(f"📊 当前RSI: {current_rsi:.2f} | 价格: {quote.last_price}")

api.close()
