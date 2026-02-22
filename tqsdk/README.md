# 天勤 TqSdk 交易策略集合

## 📁 文件说明

| 文件名 | 策略名称 | 核心逻辑 | 难度 |
|--------|----------|----------|------|
| `strategy_01_double_ma.py` | 双均线策略 | 金叉买入，死叉卖出 | ⭐ 入门 |
| `strategy_02_breakout.py` | 突破策略 | 突破前高买入，跌破前低卖出 | ⭐ 入门 |
| `strategy_03_grid.py` | 网格策略 | 在价格区间内低买高卖 | ⭐⭐ 进阶 |
| `strategy_04_rsi.py` | RSI策略 | 超卖买入，超买卖出 | ⭐ 入门 |
| `strategy_05_complete_system.py` | 完整交易系统 | 包含风控、仓位管理、日志 | ⭐⭐⭐ 高级 |

---

## 🚀 快速开始

### 1. 运行策略（模拟盘）
```bash
# 进入目录
cd /root/.openclaw/workspace/tqsdk

# 运行双均线策略
python3 strategy_01_double_ma.py

# 运行突破策略
python3 strategy_02_breakout.py
```

### 2. 切换合约
修改策略文件中的 `symbol` 变量：
```python
symbol = "SHFE.cu2503"  # 沪铜
symbol = "CFFEX.IF2503" # 沪深300股指
symbol = "DCE.m2505"    # 豆粕
```

### 3. 修改K线周期
```python
klines = api.get_kline_serial(symbol, 60)   # 1分钟
klines = api.get_kline_serial(symbol, 300)  # 5分钟
klines = api.get_kline_serial(symbol, 900)  # 15分钟
klines = api.get_kline_serial(symbol, 3600) # 1小时
```

---

## 📊 策略详解

### 策略1: 双均线 (Double MA)
```
原理：短期均线上穿长期均线(金叉)买入，下穿(死叉)卖出
参数：short_period=5, long_period=20
适用：趋势行情
```

### 策略2: 突破 (Breakout)
```
原理：突破前N根K线最高价买入，跌破最低价卖出
参数：lookback_period=20
适用：波动较大的品种
```

### 策略3: 网格 (Grid)
```
原理：在设定价格区间内设置多个档位，自动低买高卖
参数：upper_price, lower_price, grid_num
适用：震荡行情
```

### 策略4: RSI超买超卖
```
原理：RSI<30超卖区买入，RSI>70超买区卖出
参数：rsi_period=14, overbought=70, oversold=30
适用：震荡行情，判断反转点
```

### 策略5: 完整交易系统
```
功能：
- 信号生成（MACD金叉死叉）
- 仓位管理（限制最大持仓）
- 风险控制（止损止盈）
- 日志记录（带时间戳）
```

---

## 🔧 实盘交易配置

### 快期账户
```python
from tqsdk import TqApi, TqAccount

# 实盘账户
api = TqApi(TqAccount("你的快期账户", "密码"))
```

### 天勤实盘
```python
from tqsdk import TqApi, TqAuth

# 天勤实盘（需要申请）
api = TqApi(auth=TqAuth("用户名", "密码"))
```

---

## 📚 常用API速查

### 获取行情
```python
quote = api.get_quote(symbol)
print(quote.last_price)      # 最新价
print(quote.ask_price1)      # 卖一价
print(quote.bid_price1)      # 买一价
```

### 获取K线
```python
klines = api.get_kline_serial(symbol, 60)  # 1分钟K线
print(klines.close.iloc[-1])  # 最新收盘价
print(klines.high.iloc[-1])   # 最新最高价
```

### 获取持仓
```python
position = api.get_position(symbol)
print(position.pos_long)      # 多头持仓
print(position.pos_short)     # 空头持仓
print(position.open_price_long)  # 多头开仓均价
```

### 下单
```python
# 限价单
order = api.insert_order(
    symbol=symbol,
    direction="BUY",        # BUY/SELL
    offset="OPEN",          # OPEN/CLOSE
    volume=1,               # 手数
    limit_price=70000       # 限价
)

# 市价单
order = api.insert_order(
    symbol=symbol,
    direction="SELL",
    offset="CLOSE",
    volume=1
)
```

### 技术指标
```python
from tqsdk.ta import MA, MACD, RSI, BOLL

# 均线
ma5 = MA(klines, 5)
ma20 = MA(klines, 20)

# MACD
macd = MACD(klines, 12, 26, 9)

# RSI
rsi = RSI(klines, 14)

# 布林带
boll = BOLL(klines, 20, 2)
```

---

## ⚠️ 风险提示

1. **所有策略仅供学习，实盘使用前请充分测试**
2. **模拟盘和实盘有差异，滑点、延迟可能影响策略表现**
3. **建议先用模拟盘跑1-2周观察效果**
4. **实盘时设置严格的止损，控制风险**

---

## 📖 学习资源

- 官方文档: https://doc.shinnytech.com/tqsdk/latest/
- GitHub: https://github.com/shinnytech/tqsdk
- 快期官网: https://www.shinnytech.com/

---

## 💡 进阶建议

1. **回测**: 使用 `TqBacktest` 在历史数据上测试策略
2. **多品种**: 同时监控多个合约，分散风险
3. **优化参数**: 使用网格搜索找到最优参数组合
4. **组合策略**: 多个策略信号组合，提高胜率
