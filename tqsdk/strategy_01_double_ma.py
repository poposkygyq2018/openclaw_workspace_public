#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略1: 双均线策略 (Double MA Crossover)
当短期均线上穿长期均线时买入，下穿时卖出
"""

from tqsdk import TqApi, TqSim
from tqsdk.ta import MA

# 创建API实例（模拟盘）
api = TqApi(TqSim())

# 订阅合约 - 以沪铜为例
symbol = "SHFE.cu2503"  # 可以根据需要修改合约
klines = api.get_kline_serial(symbol, 60)  # 1分钟K线

# 设置均线周期
short_period = 5   # 短期均线
long_period = 20   # 长期均线

print(f"🚀 双均线策略启动 - 合约: {symbol}")
print(f"📊 短期均线: {short_period}周期 | 长期均线: {long_period}周期")
print("-" * 50)

while True:
    api.wait_update()
    
    # 确保K线数据足够
    if len(klines) < long_period:
        continue
    
    # 计算均线
    short_ma = MA(klines, short_period).iloc[-1]
    long_ma = MA(klines, long_period).iloc[-1]
    
    # 获取当前持仓
    position = api.get_position(symbol)
    current_pos = position.pos_long - position.pos_short
    
    # 获取最新价格
    quote = api.get_quote(symbol)
    
    # 交易逻辑
    if short_ma > long_ma and current_pos == 0:
        # 金叉 - 买入
        api.insert_order(symbol=symbol, direction="BUY", offset="OPEN", 
                        volume=1, limit_price=quote.ask_price1)
        print(f"🟢 金叉买入 | 价格: {quote.last_price} | 短均:{short_ma:.2f} 长均:{long_ma:.2f}")
    
    elif short_ma < long_ma and current_pos > 0:
        # 死叉 - 卖出
        api.insert_order(symbol=symbol, direction="SELL", offset="CLOSE", 
                        volume=current_pos, limit_price=quote.bid_price1)
        print(f"🔴 死叉卖出 | 价格: {quote.last_price} | 短均:{short_ma:.2f} 长均:{long_ma:.2f}")

api.close()
