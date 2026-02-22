#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略5: 完整交易框架示例
包含：行情监控、仓位管理、风险控制、日志记录
"""

from tqsdk import TqApi, TqSim
from tqsdk.ta import MA, MACD
import datetime

class TradingSystem:
    def __init__(self, symbol, api):
        self.symbol = symbol
        self.api = api
        self.klines = api.get_kline_serial(symbol, 300)  # 5分钟K线
        
        # 交易参数
        self.max_position = 3      # 最大持仓
        self.stop_loss_pct = 0.02  # 止损比例 2%
        self.take_profit_pct = 0.05  # 止盈比例 5%
        
        # 记录
        self.entry_price = 0
        self.trade_count = 0
        
    def log(self, message):
        """打印日志"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def get_signal(self):
        """获取交易信号"""
        if len(self.klines) < 30:
            return None
            
        # 计算MACD
        macd = MACD(self.klines, 12, 26, 9)
        diff = macd["diff"].iloc[-1]
        dea = macd["dea"].iloc[-1]
        
        # MACD金叉
        if diff > dea and macd["diff"].iloc[-2] <= macd["dea"].iloc[-2]:
            return "BUY"
        # MACD死叉
        elif diff < dea and macd["diff"].iloc[-2] >= macd["dea"].iloc[-2]:
            return "SELL"
        
        return None
    
    def check_risk(self, position, quote):
        """风险控制检查"""
        if position.pos_long == 0:
            return True
            
        # 计算盈亏
        profit_pct = (quote.last_price - self.entry_price) / self.entry_price
        
        # 止损
        if profit_pct < -self.stop_loss_pct:
            self.log(f"⚠️ 触发止损 | 亏损: {profit_pct*100:.2f}%")
            return False
            
        # 止盈
        if profit_pct > self.take_profit_pct:
            self.log(f"🎯 触发止盈 | 盈利: {profit_pct*100:.2f}%")
            return False
            
        return True
    
    def run(self):
        """主循环"""
        self.log(f"🚀 交易系统启动 - {self.symbol}")
        self.log(f"📊 最大持仓: {self.max_position} | 止损: {self.stop_loss_pct*100}% | 止盈: {self.take_profit_pct*100}%")
        
        while True:
            self.api.wait_update()
            
            position = self.api.get_position(self.symbol)
            quote = self.api.get_quote(self.symbol)
            
            current_pos = position.pos_long - position.pos_short
            
            # 风险控制
            if not self.check_risk(position, quote):
                # 平仓
                if current_pos > 0:
                    self.api.insert_order(symbol=self.symbol, direction="SELL", 
                                        offset="CLOSE", volume=current_pos)
                    self.log(f"🔴 风险平仓 | 价格: {quote.last_price}")
                continue
            
            # 获取交易信号
            signal = self.get_signal()
            
            if signal == "BUY" and current_pos < self.max_position:
                # 买入
                self.api.insert_order(symbol=self.symbol, direction="BUY",
                                    offset="OPEN", volume=1, 
                                    limit_price=quote.ask_price1)
                self.entry_price = quote.last_price
                self.trade_count += 1
                self.log(f"🟢 买入开仓 | 价格: {quote.last_price} | 持仓: {current_pos + 1}")
                
            elif signal == "SELL" and current_pos > 0:
                # 卖出
                self.api.insert_order(symbol=self.symbol, direction="SELL",
                                    offset="CLOSE", volume=current_pos,
                                    limit_price=quote.bid_price1)
                self.log(f"🔴 卖出平仓 | 价格: {quote.last_price} | 交易次数: {self.trade_count}")

# 运行系统
if __name__ == "__main__":
    api = TqApi(TqSim())
    system = TradingSystem("SHFE.cu2503", api)
    
    try:
        system.run()
    except KeyboardInterrupt:
        print("\n👋 系统停止")
        api.close()
