import pandas as pd
import datetime
import tushare as ts
from selenium import webdriver
import re
import warnings
warnings.filterwarnings('ignore')

# crawlding analysis data
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
executable_path = r'D:\Anaconda3\Scripts\chromedriver.exe'
browser = webdriver.Chrome(executable_path=executable_path, chrome_options=chrome_options)

page = 170
data_all = pd.DataFrame()
for pg in range(1,page):
    url = 'http://yanbao.stock.hexun.com/ybsj5_' + str(pg) + '.shtml'
    browser.get(url)
    html = browser.page_source
    table = pd.read_html(html)[0] # 读取网页中的表格
    df = table.iloc[1:] # 第1行以下为表格内容
    df.columns = table.iloc[0] # 第1行为标题

    p_code = '<a href="yb_(.*?).shtml'
    code = re.findall(p_code, html)
    df['股票代码'] = code

    data_all = pd.concat([data_all, df], ignore_index=True)

print(data_all)
print('分析师评级报告获取成功')
data_all.to_excel('data/4/分析师评级报告.xlsx')


# Analysising
df = pd.read_excel(r'E:\PycharmProjects\python_fin\myPractice\data\分析师评级报告.xlsx', dtype={'股票代码':str})
df = df.drop_duplicates()
df = df.dropna(thresh=5)

df['研究机构-分析师'] = df['研究机构'] + '-' + df['分析师']
columns = ['股票名称','股票代码','研究机构-分析师','最新评级','评级调整','报告日期']
df = df[columns]


def fenxi(length):  # 其中length代表时长，如果length=10，则表示10天前
    df_use = df  # 这里为了演示，选取了100行数据，如果想获取全部内容，可以改成df_use = df

    # 日期筛选
    today = datetime.datetime.now()
    t = today - datetime.timedelta(days=length)  # 这里设置选取日期的阈值
    t = t.strftime('%Y-%m-%d')
    df_use = df_use[df_use['报告日期'] < t]

    rate = []
    for i, row in df_use.iterrows():
        code = row['股票代码']
        analysist_date = row['报告日期']

        # 1.获取开始日期，也即第二天
        begin_date = datetime.datetime.strptime(analysist_date, '%Y-%m-%d')
        begin_date = begin_date + datetime.timedelta(days=1)
        begin_date = begin_date.strftime('%Y-%m-%d')

        # 2.获取结束日期，也即第三十天
        end_date = datetime.datetime.strptime(analysist_date, '%Y-%m-%d')
        end_date = end_date + datetime.timedelta(days=length)  # 这里设置相隔的时间
        end_date = end_date.strftime('%Y-%m-%d')

        # 3.通过Tushare库计算股票收益率
        ts_result = ts.get_hist_data(code, begin_date, end_date)
        if ts_result is None or len(ts_result) < 10:  # 防止股票没有数据
            return_rate = 0
        else:
            # 防止出现一字涨停现象
            if ts_result.iloc[-1]['low'] == ts_result.iloc[-1]['high'] and abs(ts_result.iloc[-1]['p_change'] - 10.0) < 0.1:
                return_rate = 0
            else:
                start_price = ts_result.iloc[-1]['open']
                end_price = ts_result.iloc[0]['close']
                return_rate = (end_price / start_price) - 1.0
        rate.append(return_rate)

    df_use[str(length) + '天收益率'] = rate  # 这里设置要添加的列

    print(df_use)
    means = df_use.groupby('研究机构-分析师')[[str(length)+'天收益率']].mean()
    counts = df_use.groupby('研究机构-分析师')[[str(length)+'天收益率']].count()
    counts = counts.rename(columns={str(length)+'天收益率':'预测次数'})

    df_final = pd.merge(means, counts, on='研究机构-分析师', how='inner')
    df_final.sort_values(by=str(length)+'天收益率',ascending='True',inplace=True)


    df_final.to_excel(r'E:\PycharmProjects\python_fin\myPractice\data\4'+str(length)+'天收益率.xlsx')

length=[30,60,90,120]
for i in length:
    fenxi(i)
    print(str(i)+'天收益率分析完成')









