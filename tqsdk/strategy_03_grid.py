#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略3: 网格策略 (Grid Trading)
在价格区间内设置多个买卖档位，自动低买高卖
"""

from tqsdk import TqApi, TqSim
import time

# 创建API实例
api = TqApi(TqSim())

# 订阅合约
symbol = "SHFE.cu2503"
quote = api.get_quote(symbol)

# 网格参数
upper_price = 75000    # 区间上限
lower_price = 65000    # 区间下限
grid_num = 10          # 网格数量
grid_size = (upper_price - lower_price) / grid_num  # 每格大小

print(f"🚀 网格策略启动 - 合约: {symbol}")
print(f"📊 价格区间: {lower_price} - {upper_price}")
print(f"📊 网格数量: {grid_num} | 每格大小: {grid_size:.2f}")
print("-" * 50)

# 生成网格价格
grid_prices = [lower_price + i * grid_size for i in range(grid_num + 1)]
print(f"网格档位: {[f'{p:.0f}' for p in grid_prices]}")

# 记录已下单的档位
placed_orders = {}

while True:
    api.wait_update()
    
    current_price = quote.last_price
    position = api.get_position(symbol)
    current_pos = position.pos_long - position.pos_short
    
    # 检查每个网格档位
    for i, price in enumerate(grid_prices):
        # 买入档位（低于当前价的档位）
        if price < current_price and price not in placed_orders:
            # 检查是否已经有这个档位的持仓
            if current_pos < 3:  # 限制最大持仓
                order = api.insert_order(symbol=symbol, direction="BUY", offset="OPEN",
                                        volume=1, limit_price=price)
                placed_orders[price] = "BUY"
                print(f"🟢 网格买入挂单 | 档位: {price:.2f} | 当前价: {current_price}")
                time.sleep(0.5)
        
        # 卖出档位（有持仓且价格高于成本）
        elif price > current_price and price in placed_orders and placed_orders[price] == "BUY":
            if current_pos > 0:
                order = api.insert_order(symbol=symbol, direction="SELL", offset="CLOSE",
                                        volume=1, limit_price=price)
                del placed_orders[price]
                print(f"🔴 网格卖出 | 档位: {price:.2f} | 当前价: {current_price}")
                time.sleep(0.5)

api.close()
