# coding : utf-8
# create by htb on 2020

### 简易金融量化框架

import pandas as pd
import matplotlib.pyplot as plt
import tushare as ts
import datetime

# 交易日历
try:
    f = open('./data2local/trade_cal.csv', 'r')
    # trade_cal = pd.read_csv(f, parse_dates=['calendarDate']) # 将“calendarDate”列解析为时间索引
    trade_cal = pd.read_csv(f)
except FileNotFoundError:
    trade_cal = ts.trade_cal()

# trade_cal = ts.trade_cal()

class G:
    """
    存储用户自定义的全局变量
    """
    pass


class Contex:
    """
    框架全局变量
    """
    def __init__(self, cash, start_date, end_date):
        self.cash = cash                # 账户余额
        self.start_date = start_date    # 起始时间
        self.end_date = end_date        # 终止时间
        self.positions = {}             # 持仓数据：持仓股票代码：持股数目
        self.benchmark = None           # 基准
        self.date_range = trade_cal[(trade_cal.calendarDate >= start_date)\
                                    & (trade_cal.calendarDate <= end_date)\
                                    & (trade_cal.isOpen == 1)]['calendarDate'].values # 执行回测时间范围

# 用户需要根据自身需求自定义的全局变量
cash = 100000.0         # 起始现金
s_date = '2019-01-01'   # 起始时间
e_date = '2020-01-01'   # 终止时间
# 框架全局变量初始化
context = Contex(cash, s_date, e_date)
# 用户全局变量初始化
g = G()


def attribute_history(security, count,
                      fields=('open', 'close', 'high', 'low', 'volume')):
    """
    获取股票指定数量（天数）的历史数据
    :param security: 股票
    :param count:   获取多少天的历史数据
    :param fields:  返回数据列索引
    :return: dataframe格式数据
    """
    # 运行策略日期为context.dt, 历史数据截止日期为昨天：end_date
    end_date = (context.dt - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    start_date = trade_cal[(trade_cal.calendarDate <= end_date) & (trade_cal.isOpen == 1)]\
                            [-count:].iloc[0]['calendarDate'] # 起始交易日
    return attrbute_daterange_history(security, start_date, end_date, fields)


def attrbute_daterange_history(security, start_date, end_date,
                               fields=('open', 'close', 'high', 'low', 'volume')):
    """
    获取股票指定日期范围内日的历史数据
    :param security: 股票代码
    :param start_date: 起始时间
    :param end_date:   结束时间
    :param fields:     需要数据类型
    :return: dataframe格式数据
    """
    try:
        f = open('./data2local/' + security + '.csv', 'r')
        df = pd.read_csv(f, index_col='date', parse_dates=['date']).loc[start_date:end_date, :]
    except FileNotFoundError:
        df = ts.get_h_data(security, start=start_date, end=end_date, autype=None) # 获取历史无复权数据
    return df[list(fields)].sort_index() # 返回索引升序排序后的数据


def get_today_data(security):
    """
    获取当日股票无复权数据
    :param security: 股票代码
    :return: 当日（回测执行日期）无复权数据
    """
    today = context.dt.strftime('%Y-%m-%d')
    try: # 行情数据本地化
        f = open('./data2local/' + security + '.csv', 'r')
        df = pd.read_csv(f, index_col='date', parse_dates=['date']).loc[today:today]
    except FileNotFoundError:
        df = ts.get_h_data(security, start=today, end=today, autype=None) # 获取历史无复权数据
    return df


def set_benchmark(benchmark):
    """
    设置基准
    :param benchmark: 基准股票代码
    :return:
    """
    context.benchmark = benchmark


def _order(today_data, security, amount):
    """
    交易函数
    :param today_data:当天日期
    :param security:股票代码
    :param amount:数量（多少股）
    :return:
    """
    if today_data.empty:
        print("股市今天停牌，无法买卖")
        return False

    if security not in context.positions:
        context.positions[security] = 0

    # 最低佣金：5元（不做判断）
    if context.cash - amount * today_data['close'][0] * 1.0003 < 0:
        amount = int(context.cash / today_data['close'][0] / 1.0003)
        print("现金不足，已调整为%d" % amount)

    if amount % 100 != 0:
        # if amount != -context.positions[security]:
        amount = int(amount / 100) * 100
        print("交易必须为100的整数倍，已调整为%d" % amount)

    if context.positions[security] + amount < 0:
        amount = -context.positions[security]
        print("卖出股票必须不超过持仓数，已调整为%d" % amount)

    action = "买入" if amount > 0 else "卖出"
    print("%s: %s%s股票%d股，价格%.2f" % (context.dt.strftime('%Y-%m-%d'), action, security, amount, today_data['close'][0]))
    new_amount = context.positions[security] + amount
    context.positions[security] = new_amount
    if amount > 0:
        context.cash -= amount * today_data['close'][0] * 1.0003
    else:
        """
        佣金：万3
        印花税：千分之一
        最低佣金：5元（不做处理）
        """
        context.cash -= amount * today_data['close'][0] * 0.9987

    if context.positions[security] == 0:
        del context.positions[security]


def order(security, amount):
    """
    买|卖多少股票
    :param security: 股票代码
    :param amount:   买入|卖出数量
    :return:
    """
    today_data = get_today_data(security)
    return _order(today_data, security, amount)


def order_value(security, value):
    """
    买|卖多少钱的股票
    :param security: 股票代码
    :param value: 买入|卖出 金额
    :return:
    """
    today_data = get_today_data(security)
    commission_ratio = 0.9987 if value < 0 else 1.0003 # 不考虑最低佣金限制
    amount = int(value / today_data['close'][0] / commission_ratio) # 根据买入|卖出计算对应金额的股票数量
    return _order(today_data, security, amount)


def order_target(security, amount):
    """
    买|卖到多少股股票
    :param security: 股票代码
    :param amount:   买入|卖出 数量
    :return:
    """
    if amount < 0:
        print("目标股数不能为负，已调整为0")
        amount = 0
    today_data = get_today_data(security)
    hold_amount = context.positions[security] if security in context.positions else 0
    delta_amount = amount - hold_amount
    return _order(today_data, security, delta_amount)


def order_target_value(security, value):
    """
    买|卖到多少钱的股票
    :param security: 股票代码
    :param value:    买入|卖出 金额
    :return:
    """
    if value < 0:
        print("目标价值不能为负，已调整为0")
        value = 0
    today_data = get_today_data(security)
    hold_value = context.positions[security] * today_data['close'][0]
    delta_value = value - hold_value
    commission_ratio = 0.9987 if delta_value < 0 else 1.0003
    delta_amount = int(delta_value / today_data['close'][0] / commission_ratio)
    return _order(today_data, security, delta_amount)
