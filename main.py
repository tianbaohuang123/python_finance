# coding : utf-8
# create by htb on 2020

### 用户策略代码

from api_frame import *


def initialize(context):
    """
    用户初始化函数
    :param context: 框架全局变量
    :return:
    """
    g.security = ['600519']  # 需要进行回测的股票代码，这里填写的是贵州茅台的股票代码
    g.p1 = 5
    g.p2 = 60
    set_benchmark('600519') # 设置基准股票，从回测起始时间买入后持续持有


def handle_data(context):
    """
    用户策略函数 --- 双均线策略
    :param context:
    :return:
    """
    n = len(g.security)
    for stock in g.security:
        hist = attribute_history(stock, count=g.p2)
        ma5 = hist['close'][-5:].mean()
        ma60 = hist['close'].mean()

        if ma5 > ma60 and stock not in context.positions: # 金叉 - 买入
            order_value(stock, context.cash / n)
        elif ma5 < ma60 and stock in context.positions: # 死叉 - 卖出
            order_target(stock, 0)


def run(context):
    """
    框架运行函数
    :param context:
    :return:
    """
    init_value = cash   # 起始资金
    plt_df = pd.DataFrame(index=pd.to_datetime(context.date_range), columns=['value', 'ratio'])
    last_prize = {} # 为停牌使用

    for dt in context.date_range: # 每天做一次遍历
        context.dt = datetime.datetime.strptime(dt, '%Y-%m-%d')
        handle_data(context)    # 执行策略函数
        value = context.cash    # 股票账户资金
        for stock in context.positions:
            today_data = get_today_data(stock)
            if not today_data.empty:
                # 股票未停牌
                prize = today_data['close'][0]
                last_prize[stock] = prize
            else:
                # 股票停牌
                print("%s 股票%s今日停牌" % (context.dt.strftime('%Y-%m-%d'),stock))
                prize = last_prize[stock]
            value += prize * context.positions[stock]
        plt_df.loc[dt,'value'] = value  # 填充每日股票账户资产总额
    plt_df['ratio'] = (plt_df['value'] - init_value) / init_value # 计算回测期间每天的收益率


    # 计算基准
    if context.benchmark:
        benchmark_df = attrbute_daterange_history(context.benchmark, context.start_date, context.end_date)
        benchmark_init = benchmark_df['close'][0]
        plt_df['benchmark_ratio'] = (benchmark_df['close'] - benchmark_init) / benchmark_df['close']
    # 绘图
    plt_df[['ratio', 'benchmark_ratio']].plot()
    plt.show()


if __name__ == '__main__':
    # 初始化框架全局变量
    initialize(context)
    # 运行策略
    run(context)
