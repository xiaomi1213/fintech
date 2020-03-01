"""
Python金融数据分析
1 舆情分析
通过爬虫在百度上批量爬取某个公司的资讯，针对爬取的内容根据关键词给出评分，从数据库汇总每日评分，匹配舆情数据评分与股价数据，并可视化和求取相关系数。
2 解析上市公司理财公告
批量爬取巨潮资讯网的上市公司理财公告PDF文件，并通过PDF文件解析技术分析获取到的理财公告，从中识别潜在的机构投资者。
3 基于评级报告的投资决策分析
爬取和讯研报网的券商分析师评级报告信息，获取股票历史行情数据，以分析每只股票在被预测后的行情走势，从而计算出股票一段时间内的收益率，最后根据该收益率评估券商分析师的预测准确度。
4 基于股票信息及其衍生变量的数据分析
通过Tushare库获取股票的基本信息，从而进行相关的量化金融数据分析，并通过程序推导计算10分钟成交量涨跌幅数据。
5 构建评分卡模型
使用python数据分析包构筑一个贷款评分卡模型，根据评分卡可以评估用户的信用分数。
6 定时发送邮件
将以上四个模块的内容整合成附件，通过QQ邮箱，定期自动发送邮件。

"""

import requests
import re
import time
import pymysql
import pandas as pd
import datetime
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
import tushare as ts
import numpy as np
from selenium import webdriver
import pdfplumber
import os
import warnings
import xlwings as xw
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
warnings.filterwarnings('ignore')


plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_mnus'] = False

def baidu(company, page):
    #page = (page+1)*10

    url = 'https://www.baidu.com/s?rtt=4&bsst=1&cl=2&tn=news&word='+company+'&pn='+str((page+1)*10)
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36'}

    print('baidu' + "开始爬取 " + company + '第' + str(page+1) + '页' + '\n')
    html = requests.get(url,headers=headers,timeout=10).text
    try:
        html = html.encode('ISO-8859-1').decode('utf-8')
    except:
        try:
            html = html.encode('ISO-8859-1').decode('gbk')
        except:
            html = html


    p_title = '<h3 class="c-title">.*?>(.*?)</a>'
    titles = re.findall(p_title, html, re.S)

    p_href = '<h3 class="c-title">.*?<a href="(.*?)"'
    hrefs = re.findall(p_href, html, re.S)

    p_info = '<p class="c-author">(.*?)</p>'
    infos = re.findall(p_info, html, re.S)


    source = []
    date = []
    for i in range(len(infos)):
        titles[i] = titles[i].strip()
        titles[i] = re.sub('<.*?>', '', titles[i])

        infos[i] = re.sub('<.*?>','',infos[i])
        infos[i] = infos[i].strip()
        source.append(infos[i].split('&nbsp;&nbsp;')[0])
        date.append(infos[i].split('&nbsp;&nbsp;')[1].strip())

        date[i] = date[i].split(' ')[0]
        date[i] = re.sub('年','-',date[i])
        date[i] = re.sub('月','-',date[i])
        date[i] = re.sub('日','',date[i])
        if ('小时' in date[i]) or ('分钟' in date[i]):
            date[i] = time.strftime('%Y-%m-%d')
        else:
            date[i] = date[i]



    # 4.正文爬取及数据深度清洗,舆情评分系统
    score=[]
    keywords = ['违约','诉讼','不善','裁员','缩减','欠债','欺诈','压榨','加班','倒闭','破产','重组']
    for i in range(len(titles)):
        num = 0
        try:
            article = requests.get(hrefs[i],headers=headers,timeout=10).text
        except:
            article = '单个新闻爬取失败'

        try:
            article = article.encode('ISO-8859-1').decode('utf-8')
        except:
            try:
                article = article.encode('ISO-8859-1').decode('gbk')
            except:
                article = article

        p_article = '<p>(.*?)</p>'
        article_main = re.findall(p_article,article,re.S)
        article = ''.join(article_main)
        for key in keywords:
            if (key in article) or (key in titles[i]):
                num -= 5
        score.append(str(num))



        p_company = company[0]+'.{0,5}'+company[-1]
        if len(re.findall(p_company,article,re.S))<1:
            titles[i] = ' '
            hrefs[i] = ' '
            source[i] = ' '
            date[i] = ' '
    while ' ' in titles:
        titles.remove(' ')
    while ' ' in hrefs:
        hrefs.remove(' ')
    while ' ' in source:
        source.remove(' ')
    while ' ' in date:
        date.remove(' ')



    for i in range(len(titles)):
        print(str(i+1)+' '+titles[i]+' '+source[i]+' '+date[i]+' '+score[i]+'\n'+hrefs[i]+'\n')

    print('baidu' + "结束爬取 " + company + '第' + str(page + 1) + '页' + '\n')



    #存到数据库

    db = pymysql.connect(host='localhost',port=3306,user='root',password='forjun598',database='pacong',charset='utf8')
    cur = db.cursor()

    order1 = 'SELECT title from baidu where company=%s'
    cur.execute(order1, company)
    titles_all = cur.fetchall()

    order2 = 'INSERT INTO baidu VALUES(%s,%s,%s,%s,%s,%s)'
    for i in range(len(titles)):
        if titles[i] not in titles_all:
            cur.execute(order2,(company,titles[i],source[i],date[i],score[i],hrefs[i]))
    db.commit()
    cur.close()
    db.close()
    print(company + '第' + str(page + 1) + '页内容已存储到数据库表baidu' + '\n')


def extract(companies):
    # 从数据库汇总每日评分
    companies = companies
    date_list = pd.date_range('2019-06-01', '2019-11-26')
    date_list = list(date_list)
    for i in range(len(date_list)):
        date_list[i] = date_list[i].strftime('%Y-%m-%d')

    db = pymysql.connect(host='localhost', port=3306, user='root', password='forjun598', database='pacong',
                         charset='utf8')
    cur = db.cursor()
    order = 'select score from baidu where company=%s and date=%s'
    print('开始汇总分数' + '\n')
    for i in companies:
        score_dict = {}
        for j in date_list:
            total_score = 100
            cur.execute(order, (i, j))
            score_data = cur.fetchall()
            for k in range(len(score_data)):
                total_score += score_data[k][0]
            score_dict[j] = total_score
            print(i + '' + j + ' 舆论总评分为' + str(total_score) + '\n')

        data = pd.DataFrame(list(score_dict.items()), columns=['date', 'score'])
        data.to_excel(r'E:\PycharmProjects\python_fin\myPractice\data\1\%s_score.xlsx' % i, index=False)
    print('结束汇总分数' + '\n')
    cur.close()
    db.close()


def show(companies_codes):
    companies_codes = companies_codes

    # 获取股价数据，并与舆情得分合并为一个文件
    for key, value in companies_codes.items():
        try:
            data = ts.get_hist_data(value, start='2019-06-01', end='2019-11-26')
        except:
            data = pd.DataFrame(np.arange(338).reshape(26, 13))
        data.to_excel(r'E:\PycharmProjects\python_fin\myPractice\data\1' + key + '_share.xlsx')
        print(key + '股价数据保存成功')

        score = pd.read_excel(r'E:\PycharmProjects\python_fin\myPractice\data\1' + key + '_score.xlsx')
        share = pd.read_excel(r'E:\PycharmProjects\python_fin\myPractice\data\1' + key + '_share.xlsx')
        share = share[['date', 'close']]
        merge_data = pd.merge(score, share, on='date', how='inner')
        merge_data = merge_data.rename(columns={'close': 'price'})
        merge_data.to_excel(r'E:\PycharmProjects\python_fin\myPractice\data\1' + key + '_merge_data.xlsx', index=False)
        print(key + '股价数据合并成功')

    # 绘制舆情得分与股价 的相关系数和关系图
    for key, value in companies_codes.items():
        merge_data = pd.read_excel(r'E:\PycharmProjects\python_fin\myPractice\data\1' + key + '_merge_data.xlsx')

        corr = pearsonr(merge_data['score'], merge_data['price'])
        print('相关系数r值为' + str(corr[0]) + '，显著性水平P值为' + str(corr[1]))

        for i in range(len(merge_data['date'])):
            merge_data['date'][i] = datetime.datetime.strptime(merge_data['date'][i], '%Y-%m-%d')

        plt.plot(merge_data['date'], merge_data['score'], color='blue', label=key + '_score')
        plt.xticks(rotation=45)
        plt.legend(loc='upper left')
        plt.twinx()
        plt.plot(merge_data['date'], merge_data['price'], color='red', label=key + '_price')
        plt.xticks(rotation=45)
        plt.legend(loc='upper right')
        plt.show()


def financial_announcement():
    executable_path = r'D:\Anaconda3\Scripts\chromedriver.exe'
    # executable_path=r'E:\ProgramData\Anaconda3\Scripts\chromedriver.exe'
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    prefs = {'profile.default_content_settings.popups': 0,
             'download.default_directory': r'E:\PycharmProjects\python_fin\myPractice\data\2'}  # 这边你可以修改文件储存的位置
    chrome_options.add_experimental_option('prefs', prefs)
    browser = webdriver.Chrome(executable_path=executable_path)

    url = 'http://www.cninfo.com.cn/'
    browser.get(url)
    time.sleep(5)
    browser.maximize_window()

    # browser.find_element_by_xpath('//*[@id="common_top_input_obj"]').clear()
    browser.find_element_by_xpath('//*[@id="common_top_input_obj"]').send_keys('理财')
    browser.find_element_by_xpath('//*[@id="common_top_button"]').click()
    time.sleep(3)
    html0 = browser.page_source
    p_page = 'id="page-info-title"><span>合计约(.*?)条</span>'
    page_num = re.findall(p_page, html0, re.S)[0]
    pages = int(int(page_num) / 10)

    htmls = []
    htmls.append(html0)
    for i in range(pages):
        browser.find_element_by_xpath('//*[@id="pagination_title"]/ul/li[12]')
        time.sleep(3)
        html = browser.page_source
        htmls.append(html)
        time.sleep(1)
    all_html = ''.join(htmls)
    browser.quit()

    p_title = '<td class="sub-title">.*?>(.*?)</a>'
    p_href = '<td class="sub-title"><a href="(.*?)"'
    p_date = '<div class="sub-time-time">(.*?)</div>'
    titles = re.findall(p_title, all_html, re.S)
    hrefs = re.findall(p_href, all_html, re.S)
    dates = re.findall(p_date, all_html, re.S)

    for i in range(len(titles)):
        titles[i] = re.sub('<.*?>', '', titles[i])
        hrefs[i] = 'http://www.cninfo.com.cn' + hrefs[i]
        hrefs[i] = re.sub('amp;', '', hrefs[i])
        dates[i] = dates[i].split(' ')[0]

    for i in range(len(titles)):
        if '2018' not in dates[i] or '2019' not in dates[i]:
            titles[i] = ''
            hrefs[i] = ''
            dates[i] = ''
    while '' in titles:
        titles.remove('')
    while '' in hrefs:
        hrefs.remove('')
    while '' in dates:
        dates.remove('')

    for i in range(len(hrefs)):

        browser.get(hrefs[i])

        try:
            browser.find_element_by_xpath('/html/body/div/div[1]/div[2]/div[1]/div/a[4]').click()

            time.sleep(8)  # 等待文件下载时间

            print(str(i + 1) + '.' + titles[i] + '是PDF文件')
        except:
            print(titles[i] + '不是PDF文件')
    browser.quit()

    # 1.遍历文件夹中的所有PDF文件
    file_dir = r'E:\PycharmProjects\python_fin\myPractice\data\2'
    file_list = []
    for files in os.walk(file_dir):
        for file in files[2]:
            if os.path.splitext(file)[1] == '.pdf' or os.path.splitext(file)[1] == '.PDF':
                file_list.append(file_dir + file)

    # 2.PDF文本解析和内容筛选
    pdf_all = []
    for i in range(len(file_list)):
        pdf = pdfplumber.open(file_list[i])
        pages = pdf.pages
        text_list = []
        for page in pages:
            text = page.extract_text()  # 提取当页的文本内容
            text_list.append(text)
        text_all = ''.join(text_list)  # 把列表转换成字符串
        pdf.close()

        # 通过正文进行筛选
        if ('自有' in text_all) or ('议案' in text_all) or ('理财' in text_all) or ('现金管理' in text_all):
            pdf_all.append(file_list[i])

        # 3.筛选后文件的移动
        for pdf_i in pdf_all:
            newpath = r'E:PycharmProjects\python_fin\myPractice\data\2\筛选后的文件夹'\
                      + pdf_i.split('\\')[-1]  # 这边这个移动到的文件夹一定要提前就创建好！
            os.rename(pdf_i, newpath)  # 执行移动操作

        print('PDF文本解析及筛选完毕！')


def analysist():
    # crawlding analysis data
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    executable_path = r'D:\Anaconda3\Scripts\chromedriver.exe'
    browser = webdriver.Chrome(executable_path=executable_path, chrome_options=chrome_options)

    page = 170
    data_all = pd.DataFrame()
    for pg in range(1, page):
        url = 'http://yanbao.stock.hexun.com/ybsj5_' + str(pg) + '.shtml'
        browser.get(url)
        html = browser.page_source
        table = pd.read_html(html)[0]  # 读取网页中的表格
        df = table.iloc[1:]  # 第1行以下为表格内容
        df.columns = table.iloc[0]  # 第1行为标题

        p_code = '<a href="yb_(.*?).shtml'
        code = re.findall(p_code, html)
        df['股票代码'] = code

        data_all = pd.concat([data_all, df], ignore_index=True)

    print(data_all)
    print('分析师评级报告获取成功')
    data_all.to_excel(r'E:\PycharmProjects\python_fin\myPractice\data\3\分析师评级报告.xlsx')

    # Analysising
    df = pd.read_excel(r'E:\PycharmProjects\python_fin\myPractice\data\3\分析师评级报告.xlsx', dtype={'股票代码': str})
    df = df.drop_duplicates()
    df = df.dropna(thresh=5)

    df['研究机构-分析师'] = df['研究机构'] + '-' + df['分析师']
    columns = ['股票名称', '股票代码', '研究机构-分析师', '最新评级', '评级调整', '报告日期']
    df = df[columns]

    def fenxi(length):  # 其中length代表时长，如果length=10，则表示10天前
        df_use = df  # 可选取数据的行数

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

            # 2.获取结束日期，也即第length天
            end_date = datetime.datetime.strptime(analysist_date, '%Y-%m-%d')
            end_date = end_date + datetime.timedelta(days=length)  # 这里设置相隔的时间
            end_date = end_date.strftime('%Y-%m-%d')

            # 3.通过Tushare库计算股票收益率
            ts_result = ts.get_hist_data(code, begin_date, end_date)
            if ts_result is None or len(ts_result) < 10:  # 防止股票没有数据
                return_rate = 0
            else:
                # 防止出现一字涨停现象
                if ts_result.iloc[-1]['low'] == ts_result.iloc[-1]['high'] and abs(
                        ts_result.iloc[-1]['p_change'] - 10.0) < 0.1:
                    return_rate = 0
                else:
                    start_price = ts_result.iloc[-1]['open']
                    end_price = ts_result.iloc[0]['close']
                    return_rate = (end_price / start_price) - 1.0
            rate.append(return_rate)

        df_use[str(length) + '天收益率'] = rate  # 这里设置要添加的列

        # print(df_use)
        means = df_use.groupby('研究机构-分析师')[[str(length) + '天收益率']].mean()
        counts = df_use.groupby('研究机构-分析师')[[str(length) + '天收益率']].count()
        counts = counts.rename(columns={str(length) + '天收益率': '预测次数'})

        df_final = pd.merge(means, counts, on='研究机构-分析师', how='inner')
        df_final.sort_values(by=str(length) + '天收益率', ascending='True', inplace=True)

        df_final.to_excel(r'E:\PycharmProjects\python_fin\myPractice\data\3' + str(length) + '天收益率.xlsx')

    length = [30, 60, 90, 120]
    for i in length:
        fenxi(i)
        print(str(i) + '天收益率分析完成')


def stock(stock_code, stock_name, start_date, end_date):
    stock_code = stock_code
    stock_name = stock_name
    start_date = start_date
    end_date = end_date

    stock_k = ts.get_hist_data(stock_code, start_date, end_date)

    stock_table = pd.DataFrame()

    for current_date in stock_k.index:
        current_k_line = stock_k.loc[current_date]

        df = ts.get_tick_data(stock_code, date=current_date, src='tt')
        df['time'] = pd.to_datetime(current_date + ' ' + df['time'])
        t = pd.to_datetime(current_date).replace(hour=9, minute=40)
        df_10 = df[df.time <= t]
        vol = df_10.volume.sum()

        current_stock_info = {
            '名称': stock_name,
            '日期': pd.to_datetime(current_date),
            '开盘价': current_k_line.open,
            '收盘价': current_k_line.close,
            '股价涨跌幅(%)': current_k_line.p_change,
            '10分钟成交量': vol
        }

        stock_table = stock_table.append(current_stock_info, ignore_index=True)

    stock_table = stock_table.set_index('日期')

    order = ['名称', '开盘价', '收盘价', '股价涨跌幅(%)', '10分钟成交量']
    stock_table = stock_table[order]

    '''2.下面开始获得股票衍生变量数据'''
    # 通过公式1获取成交量涨跌幅
    stock_table['昨日10分钟成交量'] = stock_table['10分钟成交量'].shift(-1)
    stock_table['成交量涨跌幅1(%)'] = (stock_table['10分钟成交量'] - stock_table['昨日10分钟成交量']) / stock_table['昨日10分钟成交量'] * 100

    # 通过公式2获得成交量涨跌幅
    ten_mean = stock_table['10分钟成交量'].sort_index().rolling(10, min_periods=1).mean()
    stock_table['10分钟成交量10日均值'] = ten_mean
    stock_table['成交量涨跌幅2(%)'] = (stock_table['10分钟成交量'] - stock_table['10分钟成交量10日均值']) / stock_table[
        '10分钟成交量10日均值'] * 100

    # print(stock_table)

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
    plt.plot(stock_table.index, stock_table['成交量涨跌幅2(%)'].apply(lambda x: abs(x)), label='10分钟成交量涨跌幅(%)',
             linestyle='--')
    plt.legend(loc='upper right')

    plt.title(stock_name)
    plt.gcf().autofmt_xdate()

    sht.pictures.add(fig, name='图1', update=True, left=500)
    wb.save(r'E:\PycharmProjects\python_fin\myPractice\data\4' + stock_name + '_股票量化分析.xlsx')
    wb.close()
    app.quit()

    print('股票策略分析及Excel生成完毕')


def scorecard():
    # 将数据集导入为DataFrame
    trainDf = pd.read_csv(r'E:\PycharmProjects\python_fin\myPractice\data\4\cs-training.csv',index_col=0)
    testDf = pd.read_csv(r'E:\PycharmProjects\python_fin\myPractice\data\4\cs-test.csv',index_col=0)
    target = pd.read_csv(r'E:\PycharmProjects\python_fin\myPractice\data\4\sampleEntry.csv',index_col=0)

    # 将sampleEntry里的数值映射为二分类，大于0.5映射为1，小于0.5映射为0
    targetMap = target.applymap(lambda x : 1 if x > 0.5 else 0)


    # 将映射后的sampleEntry与testDf合并，便于后续数据处理
    testDf['target'] = targetMap['Probability']

    # 为了方便处理数据，将trainDf和testDf合并为一个大的数据集
    totalDf = pd.concat([trainDf, testDf], axis=0)

    # 重新整理totalDf索引号
    totalDf = totalDf.reset_index(drop=True)

    # 处理数据
    # 1 列名重命名
    # # 列名过于长，不方便处理
    # # 列名重命名字典，中文名根据英文名翻译，并非专业术语
    # # target字段不做处理
    renameDict = {'DebtRatio':'负债率',
                  'MonthlyIncome':'月收入',
                  'NumberOfDependents':'家属数量',
                  'NumberOfOpenCreditLinesAndLoans':'信贷数量',
                  'NumberOfTime30-59DaysPastDueNotWorse':'逾期30-59天次数',
                  'NumberOfTime60-89DaysPastDueNotWorse':'逾期60-89天次数',
                  'NumberOfTimes90DaysLate':'逾期90天次数',
                  'NumberRealEstateLoansOrLines':'固定资产贷款数',
                  'RevolvingUtilizationOfUnsecuredLines':'循环额度率',
                  'SeriousDlqin2yrs':'优劣贷款',
                  'age':'年龄',
                }
    totalDf.rename(columns=renameDict, inplace=True)

    # 2 删除重复值

    print('删除重复值之前的行数：',totalDf.shape[0])
    totalDf.drop_duplicates(inplace=True)
    print('删除重复值之后的行数：',totalDf.shape[0])


    # 3 异常值处理

    # 循环额度率应该小于1，这里将大于1的值当做异常值剔除。
    totalDf = totalDf[totalDf['循环额度率']<1]


    # 年龄
    # 初步觉得年龄小于18和大于90的都是异常值，进行详细的查看：
    # 通过筛选查看可发现一个年龄为0的客户，这显然不合常理，故作为异常值进行剔除；而年龄大于90岁的用户较多，
    # 因此我们有理由相信这些是正常值，后续得以保留。
    # 异常值剔除
    totalDf = totalDf[totalDf['年龄']>18]


    # 逾期天数
    # 逾期30-59天次数,逾期60-89天次数,逾期90天次数
    # 将大于80的值作为异常值进行剔除。
    totalDf = totalDf[totalDf['逾期30-59天次数']<80]
    totalDf = totalDf[totalDf['逾期60-89天次数']<80]
    totalDf = totalDf[totalDf['逾期90天次数']<80]


    # 负债率
    # 该字段分布与上面的数据相似，应该将最大值剔除，再仔细查看一下大于1的值，
    # 发现有三万多笔，所以猜测可能是正常值。
    totalDf[totalDf['负债率']>1].count()


    # 家属数量
    # 家属数量最大值为43，此为可能异常值，所以将家属数量大于10的记录剔除
    totalDf = totalDf[totalDf['家属数量']<=10]



    # 4 填补缺失值
    totalDf.isnull().sum()

    # 优劣贷款字段的缺失值是testDf的缺失值，而target字段缺失值是trainDf的缺失值，所以不用处理。
    # 月收入字段缺失值数量为49047
    # 其他字段没有缺失值
    # 填补月收入字段缺失值


    # 查看月收入字段缺失值占总记录数的比例
    IncomeRatio = totalDf['月收入'].isnull().sum()/totalDf.shape[0]
    print('月收入字段缺失值占总记录数的比例:',IncomeRatio)


    # 月收入字段缺失值占到总记录数将近20%，不适合使用简单的统计量填补，所以改用模型预测填充
    # 使用随机森林模型对月收入字段进行填补
    from sklearn.ensemble import RandomForestClassifier

    known = totalDf[totalDf['月收入'].notnull()]
    unknown = totalDf[totalDf['月收入'].isnull()]
    X_train = known.iloc[:10000,[0,2,3,4,5,6,7,8,10]]
    y_train = known.iloc[:10000,1]
    X_test = unknown.iloc[:,[0,2,3,4,5,6,7,8,10]]

    model = RandomForestClassifier(n_estimators=3, random_state=0)
    model.fit(X_train, y_train)
    y_test = model.predict(X_test)

    totalDf.loc[totalDf['月收入'].isnull(),'月收入'] = y_test


    # 家属数量缺失值填补
    # 使用中位数填补
    totalDf['家属数量'].fillna(0,inplace=True)


    # 特征选择
    # 1 相关性分析
    corrDf = totalDf.corr()
    corrDf['优劣贷款'].sort_values(ascending=False)
    # 各个字段与优劣贷款字段的相关性差异不大，所以都可保留作为特征



    # 2 特征分箱处理
    # 对连续特征进行分箱处理，用于特征的筛选，降低模型过拟合的可能性，并构造评分卡模型
    import scipy.stats.stats as stats
    def mono_bin(Y, X, n=10):
        r = 0
        badNum = Y.sum()
        goodNum = Y.count() - Y.sum()
        while abs(r) < 1:
            d1 = pd.DataFrame({'X':X, 'Y':Y, 'Bucket':pd.qcut(X,n)})
            d2 = d1.groupby('Bucket', as_index=True)
            r,p = stats.spearmanr(d2.mean().X, d2.mean().Y)
            n = n-1
        d3 = pd.DataFrame()
        d3['min'] = d2.min().X
        d3['max'] = d2.max().X
        d3['badcostum'] = d2.sum().Y
        d3['goodcostum'] = d2.count().Y - d2.sum().Y
        d3['total'] = d2.count().Y
        d3['bad_rate'] = d2.sum().Y/d2.count().Y
        d3['woe'] = np.log(d3['badcostum']/d3['goodcostum']*(goodNum/badNum))
        iv = ((d3['badcostum']/badNum)-d3['goodcostum']/goodNum)*d3['woe']
        d3['iv'] = iv
        woe = list(d3['woe'].round(6))
        cut = list(d3['max'].round(6))#使得后面变换woe后是单一的值而不是区间，也可以取区间平均值
        cut.insert(0,float('-inf'))
        cut[-1] = float('inf')
        return d3, cut, woe, iv



    dfx1, cut1, x1_woe, iv1 = mono_bin(totalDf['优劣贷款'],totalDf['循环额度率'], 5)
    dfx2, cut2, x2_woe, iv2 = mono_bin(totalDf['优劣贷款'],totalDf['年龄'], 5)
    dfx4, cut4, x4_woe, iv4 = mono_bin(totalDf['优劣贷款'],totalDf['负债率'], 5)
    dfx5, cut5, x5_woe, iv5 = mono_bin(totalDf['优劣贷款'],totalDf['月收入'], 5)


    # 并且对于其中不能使用自动分箱的特征进行手动分箱：
    def hand_bin(Y, X, cut):
        badNum = Y.sum()
        goodNum = Y.count() - Y.sum()

        d1 = pd.DataFrame({'X':X, 'Y':Y, 'Bucket':pd.cut(X,cut)})
        d2 = d1.groupby('Bucket', as_index=True)


        d3 = pd.DataFrame()
        d3['min'] = d2.min().X
        d3['max'] = d2.max().X
        d3['badcostum'] = d2.sum().Y
        d3['goodcostum'] = d2.count().Y - d2.sum().Y
        d3['total'] = d2.count().Y
        d3['bad_rate'] = d2.sum().Y/d2.count().Y
        d3['woe'] = np.log(d3['badcostum']/d3['goodcostum']*(goodNum/badNum))
        iv = ((d3['badcostum']/badNum)-d3['goodcostum']/goodNum)*d3['woe']
        d3['iv'] = iv
        woe = list(d3['woe'].round(6))

        return d3, cut, woe, iv

    ninf = float('-inf')
    pinf = float('inf')
    cut3 = [ninf, 0, 1, 3, 5, pinf]
    cut6 = [ninf, 1, 2, 3, 5, pinf]
    cut7 = [ninf, 0, 1, 3, 5, pinf]
    cut8 = [ninf, 0, 1, 2, 3, pinf]
    cut9 = [ninf, 0, 1, 3, pinf]
    cut10 = [ninf, 0, 1, 3, 5, pinf]


    dfx3, cut3, x3_woe, iv3 = hand_bin(totalDf['优劣贷款'],totalDf['逾期30-59天次数'], cut3)
    dfx6, cut6, x6_woe, iv6 = hand_bin(totalDf['优劣贷款'],totalDf['信贷数量'], cut6)
    dfx7, cut7, x7_woe, iv7 = hand_bin(totalDf['优劣贷款'],totalDf['逾期90天次数'], cut7)
    dfx8, cut8, x8_woe, iv8 = hand_bin(totalDf['优劣贷款'],totalDf['固定资产贷款数'], cut8)
    dfx9, cut9, x9_woe, iv9 = hand_bin(totalDf['优劣贷款'],totalDf['逾期60-89天次数'], cut9)
    dfx10, cut10, x10_woe, iv10 = hand_bin(totalDf['优劣贷款'],totalDf['家属数量'], cut10)



    # 计算完所有特征后，统一查看：
    IV = pd.DataFrame([iv1.sum(), iv2.sum(), iv3.sum(), iv4.sum(), iv5.sum(),
    iv6.sum(), iv7.sum(), iv8.sum(), iv9.sum(), iv10.sum()],
                  index=['循环额度率','年龄','逾期30-59天次数','负债率',\
                       '月收入','信贷数量','逾期90天次数','固定资产贷款数',\
                       '逾期60-89天次数','家属数量'])
    print(IV)
    # 我们看到各个特征的iv值都不是太小，所以在建模时这些特征都保留。
    # 现在我们有了各个特征区间的woe值，接下来我们将训练数据和测试数据用woe值替换，用replace_woe函数来进行该操作。
    def replace_woe(X, cut, woe):
        x_woe = pd.cut(X, cut, labels=woe)
        return x_woe


    woed_x1 = replace_woe(totalDf['循环额度率'], cut1, x1_woe)
    woed_x2 = replace_woe(totalDf['年龄'], cut2, x2_woe)
    woed_x3 = replace_woe(totalDf['逾期30-59天次数'], cut3, x3_woe)
    woed_x4 = replace_woe(totalDf['负债率'], cut4, x4_woe)
    woed_x5 = replace_woe(totalDf['月收入'], cut5, x5_woe)
    woed_x6 = replace_woe(totalDf['信贷数量'], cut6, x6_woe)
    woed_x7 = replace_woe(totalDf['逾期90天次数'], cut7, x7_woe)
    woed_x8 = replace_woe(totalDf['固定资产贷款数'], cut8, x8_woe)
    woed_x9 = replace_woe(totalDf['逾期60-89天次数'], cut9, x9_woe)
    woed_x10 = replace_woe(totalDf['家属数量'], cut10, x10_woe)



    woeDf = pd.DataFrame({'循环额度率':woed_x1,
                            '年龄':woed_x2,
                            '逾期30-59天次数':woed_x3,
                            '负债率':woed_x4,
                            '月收入':woed_x5,
                            '信贷数量':woed_x6,
                            '逾期90天次数':woed_x7,
                            '固定资产贷款数':woed_x8,
                            '逾期60-89天次数':woed_x9,
                            '家属数量':woed_x10})


    # 将替换好的训练集和测试集数据保存下来，生成新的csv文件，方便后面建模。
    woeDf.to_csv(r'E:\PycharmProjects\python_fin\myPractice\data\4\woeDf.csv')


    # 选择模型
    # 1 分割数据集

    # 计算训练数据集记录数
    trainNum = totalDf[totalDf['优劣贷款'].notnull()].shape[0]

    # 分割数据集
    train_woe_X = woeDf.iloc[:trainNum,:] #剔除target字段
    print('训练数据集大小：',train_woe_X.shape)
    test_woe_X = woeDf.iloc[trainNum:,:]
    print('测试集大小：',test_woe_X.shape)


    # 重新设置索引
    test_woe_X = test_woe_X.reset_index(drop=True)


    # 训练目标
    train_y = totalDf[totalDf['优劣贷款'].notnull()]['优劣贷款']
    print('训练目标大小：',train_y.shape)
    # 测试目标
    test_y = totalDf[totalDf['target'].notnull()]['target']
    print('测试目标大小：',test_y.shape)


    # 2 交叉验证
    # 导入备选模型
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.ensemble.gradient_boosting import GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression

    #导入交叉验证所需要的包
    from sklearn.model_selection import StratifiedKFold
    from sklearn.model_selection import GridSearchCV
    from sklearn.model_selection import cross_val_score

    # 定义函数，根据给定的指标得到交叉验证的平均得分
    def compute_score(model, X, y, scoring='accuracy'):
        cv_score = cross_val_score(model, X, y, cv=5, scoring=scoring)
        return np.mean(cv_score)


    #实例化各个模型
    rfc = RandomForestClassifier()
    gbc = GradientBoostingClassifier()
    lr = LogisticRegression()

    model_list = [rfc, gbc, lr]

    # 多个模型进行交叉验证
    for model in model_list:
        score = compute_score(model=model, X=train_woe_X, y=train_y, scoring='accuracy')
        print('验证的模型是：',model.__class__)
        print('验证的分数是：',score)
        print('************')

    # 由交叉验证的结果可见，gradient_boosting的得分最高，其他两个模型的得分也差不多，
    #
    # 但是为了便于构造评分卡模型，所以下面使用逻辑回归模型来构造评分卡

    # 训练模型
    #不做最优超参数选择，直接使用默认参数
    model = LogisticRegression()
    model.fit(train_woe_X, train_y)


    # 模型训练完，我们得到预测的数据以及模型各个特征的权重
    coe = model.coef_

    # 验证模型
    #使用训练好的模型和预测数据集进行预测
    pred_y = model.predict_proba(test_woe_X)[:,1]

    from sklearn.metrics import roc_curve, auc
    fpr, tpr, threshold = roc_curve(test_y, pred_y)
    auc_score = auc(fpr, tpr)
    plt.figure(figsize=(10,8))
    plt.plot(fpr, tpr, linewidth=2, label='AUC = %.2f'%auc_score)
    plt.plot([0,1],[0,1],'k--')
    plt.axis([0,1,0,1])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.legend()

    fig, ax = plt.subplots()
    ax.plot(1 - threshold, tpr, label='tpr')
    ax.plot(1 - threshold, fpr, label='fpr')
    ax.plot(1 - threshold, tpr-fpr, label='KS')
    plt.xlabel('score')
    plt.title('KS Curve')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.0])
    plt.figure(figsize=(20,20))
    legend = ax.legend(loc='upper left')
    plt.show()


    # 构建评分卡
    # 模型结果转评分函数
    factor = 20/np.log(2)
    offset = 600 - 20*np.log(20)/np.log(2)

    def get_score(coe, woe, factor):
        scores = []
        for w in woe:
            score = round(coe*w*factor, 0)
            scores.append(score)
        return scores

    x1 = get_score(coe[0][0], x1_woe, factor)
    x2 = get_score(coe[0][1], x2_woe, factor)
    x3 = get_score(coe[0][2], x3_woe, factor)
    x4 = get_score(coe[0][3], x4_woe, factor)
    x5 = get_score(coe[0][4], x5_woe, factor)
    x6 = get_score(coe[0][5], x6_woe, factor)
    x7 = get_score(coe[0][6], x7_woe, factor)
    x8 = get_score(coe[0][7], x8_woe, factor)
    x9 = get_score(coe[0][8], x9_woe, factor)
    x10 = get_score(coe[0][9], x10_woe, factor)
    print('循环额度率 对应的分数:',x1)
    print('年龄 对应的分数:',x2)
    print('逾期30-59天次数 对应的分数:',x3)
    print('负债率 对应的分数:',x4)
    print('月收入 对应的分数:',x5)
    print('信贷数量 对应的分数:',x6)
    print('逾期90天次数 对应的分数:',x7)
    print('固定资产贷款数 对应的分数:',x8)
    print('逾期60-89天次数 对应的分数:',x9)
    print('家属数量 对应的分数:',x10)

    # 根据评分卡，算出每个特征的分数，最后所有特征的分数相加再加上基准分数就是用户的总得分了。
    def calsumscore(woe_list, coe):
        n = coe.shape[1]
        series = 0
        for i in range(n):
            series += coe[0][1]*np.array(woe_list.iloc[:,i])
            #series1 = series1 + series
        score = series*factor + offset
        return series


def mail(user,pwd,to,companies_codes,length):
    user = user
    pwd = pwd
    to = to

    length = length

    msg = MIMEMultipart()

    mail_msg = """
    <p>这是分析结果，详情请看附件！</p>
    """
    msg.attach(MIMEText(mail_msg, 'plain', 'utf-8'))

    for key in companies_codes.keys:
        att1 = MIMEText(open(r'E:\PycharmProjects\python_fin\myPractice\data\1' + key + '_merge_data.xlsx', 'rb').read(), 'base64', 'utf-8')
        msg.attach(att1)
        att2 = MIMEText(open(r'E:PycharmProjects\python_fin\myPractice\data\2\筛选后的文件夹'+ key + '_data.xlsx', 'rb').read(), 'base64', 'utf-8')
        msg.attach(att2)
        att3 = MIMEText(open(r'E:\PycharmProjects\python_fin\myPractice\data\3' + str(length) + '天收益率.xlsx', 'rb').read(), 'base64', 'utf-8')
        msg.attach(att3)
        att4 = MIMEText(open(r'E:\PycharmProjects\python_fin\myPractice\data\4' + key + '_股票量化分析.xlsx', 'rb').read(), 'base64', 'utf-8')
        msg.attach(att4)
    # att1['Content-Type'] = 'application/octet-stream'
    # att1['Content-Disposition'] = 'attachment; filename="test.doc"'


    msg['Subject'] = '金融数据分析'
    msg['From'] = user
    msg['To'] = to

    s = smtplib.SMTP_SSL('smtp.qq.com', 465)
    s.login(user, pwd)
    s.send_message(msg)
    s.quit()
    print('Susses')


if __name__ == "__main__":
    # 1 舆情分析
    # 爬取并存储数据
    companies = ['平安银行', '万科', '国农科技', '世纪星源']
    companies_codes = {companies[0]:'000001',companies[1]:'000002',
                       [2]:'000004',companies[3]:'000005'}
    page_num = 50
    for i in companies:
        for j in range(page_num):
            baidu(i,j)
            print('百度'+'爬取'+i+'第'+str(j+1)+'页'+'成功'+'\n')

    # 从数据库汇总每日评分
    extract(companies)

    # 匹配舆情数据评分与股价数据，并可视化和求取相关系数
    show(companies_codes)


    # 2 解析上市公司理财公告
    # 批量爬取巨潮资讯网的上市公司理财公告PDF文件，并通过PDF文件解析技术分析获取到理财公告
    financial_announcement()



    # 3 基于评级报告的投资决策分析
    # 爬取和讯研报网的券商分析师评级报告信息，获取股票历史行情数据
    analysist()


    # 4 基于股票信息及其衍生变量的数据分析
    # 通过Tushare库获取股票的基本信息，从而进行相关的量化金融数据分析，并通过程序推导计算10分钟成交量涨跌幅数据。
    stock_code = '000002'
    stock_name = '万科A'
    start_date = '2019-02-01'
    end_date = '2019-04-01'
    stock(stock_code, stock_name, start_date, end_date)

    # 5 构建评分卡模型
    # 使用python数据分析包构筑一个贷款评分卡模型，根据评分卡可以评估用户的信用分数。
    # scorecard()


    # 6 定时发送邮件
    # 将以上四个模块的内容整合成附件，通过QQ邮箱，定期自动发送邮件。
    user = '421751563@qq.com'
    pwd = 'qecctnbkamuabiie'
    to = 'chenjunhang2013@163.com'
    mail(user, pwd, to, companies_codes, 30)
















