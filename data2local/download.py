# coding : utf-8
# create by htb on 2020

### 数据本地化

import tushare as ts

# print(tushare.__version__)

# 保存茅台酒 K 线数据至本地
df_stock = ts.get_k_data('600519', start='2010-01-01', end='2020-01-01', autype=None)
df_stock.to_csv('600519.csv', index=False)
print(df_stock.head(10))

# 保存交易日历至本地
df_trade_cal = ts.trade_cal()
df_trade_cal.to_csv('trade_cal.csv', index=False)
print(df_trade_cal.head(10))

