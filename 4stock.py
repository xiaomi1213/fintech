import tushare as ts
import pandas as pd
import matplotlib.pyplot as plt
import xlwings as xw

stock_code = '000002'
stock_name = '万科A'
start_date = '2019-02-01'
end_date = '2019-04-01'

stock_k = ts.get_hist_data(stock_code, start_date, end_date)

stock_table = pd.DataFrame()

for current_date in stock_k.index:
    current_k_line = stock_k.loc[current_date]

    df = ts.get_tick_data(stock_code, date=current_date, src='tt')
    df['time'] = pd.to_datetime(current_date+' ' + df['time'])
    t = pd.to_datetime(current_date).replace(hour=9, minute=40)
    df_10 = df[df.time <= t]
    vol = df_10.volume.sum()

    current_stock_info = {
        '名称':stock_name,
        '日期':pd.to_datetime(current_date),
        '开盘价':current_k_line.open,
        '收盘价':current_k_line.close,
        '股价涨跌幅(%)':current_k_line.p_change,
        '10分钟成交量':vol
    }

    stock_table = stock_table.append(current_stock_info,ignore_index=True)

stock_table = stock_table.set_index('日期')

order = ['名称','开盘价','收盘价','股价涨跌幅(%)','10分钟成交量']
stock_table = stock_table[order]


'''2.下面开始获得股票衍生变量数据'''
# 通过公式1获取成交量涨跌幅
stock_table['昨日10分钟成交量'] = stock_table['10分钟成交量'].shift(-1)
stock_table['成交量涨跌幅1(%)'] = (stock_table['10分钟成交量']-stock_table['昨日10分钟成交量'])/stock_table['昨日10分钟成交量']*100


# 通过公式2获得成交量涨跌幅
ten_mean = stock_table['10分钟成交量'].sort_index().rolling(10, min_periods=1).mean()
stock_table['10分钟成交量10日均值'] = ten_mean
stock_table['成交量涨跌幅2(%)'] = (stock_table['10分钟成交量']-stock_table['10分钟成交量10日均值'])/stock_table['10分钟成交量10日均值']*100

print(stock_table)

'''3.通过相关性分析选取合适的衍生变量'''
from scipy.stats import pearsonr
# 通过公式1计算的相关性
corr = pearsonr(abs(stock_table['股价涨跌幅(%)'][:-1]), abs(stock_table['成交量涨跌幅1(%)'][:-1]))
print('通过公式1计算的相关系数r值为' + str(corr[0]) + '，显著性水平P值为' + str(corr[1]))

# 通过公式2计算的相关性
corr = pearsonr(abs(stock_table['股价涨跌幅(%)']), abs(stock_table['成交量涨跌幅2(%)']))
print('通过公式2相关系数r值为' + str(corr[0]) + '，显著性水平P值为' + str(corr[1]))


'''2.将数据导入到Excel中并可视化呈现'''
app = xw.App(visible=False)
wb = app.books.add()

sht = wb.sheets.add(stock_name)
sht.range('A1').value = stock_table

fig = plt.figure()
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

plt.plot(stock_table.index, stock_table['股价涨跌幅(%)'].apply(lambda x: abs(x)), label='股价涨跌幅(%)', color='red')
plt.legend(loc='upper left')

plt.twinx()
plt.plot(stock_table.index, stock_table['成交量涨跌幅2(%)'].apply(lambda x: abs(x)),label='10分钟成交量涨跌幅(%)', linestyle='--')
plt.legend(loc='upper right')

plt.title(stock_name)
plt.gcf().autofmt_xdate()

sht.pictures.add(fig, name='图1', update=True, left=500)
wb.save(r'E:\PycharmProjects\python_fin\myPractice\data\3'+ stock_name + '_股票量化分析.xlsx')
wb.close()
app.quit()

print('股票策略分析及Excel生成完毕')





















