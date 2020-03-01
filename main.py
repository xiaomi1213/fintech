"""
2.4 Python金融数据分析
2.4.1 舆情分析
通过爬虫在百度上批量爬取某个公司的资讯，针对爬取的内容根据关键词给出评分，从数据库汇总每日评分，匹配舆情数据评分与股价数据，并可视化和求取相关系数。（3-7章、11章）
2.4.2 解析上市公司理财公告
批量爬取巨潮资讯网的上市公司理财公告PDF文件，并通过PDF文件解析技术分析获取到的理财公告，从中识别潜在的机构投资者，即合适的资金方。（8-11章）
2.4.3 基于评级报告的投资决策分析
爬取和讯研报网的券商分析师评级报告信息，获取股票历史行情数据，以分析每只股票在被预测后的行情走势，从而计算出股票一段时间内的收益率，最后根据该收益率评估券商分析师的预测准确度。
2.4.4 基于股票信息及其衍生变量的数据分析
通过Tushare库获取股票的基本信息并生成相关的衍生变量，从而进行相关的量化金融数据分析，并通过程序推导计算股价涨跌幅数据以及5日均线数据（ma5）等。
2.4.5 构建评分卡模型
使用python数据分析包构筑一个贷款评分卡模型,ROC-AUC能达到1，根据评分卡可以评估用户的信用分数。
知乎专栏：https://zhuanlan.zhihu.com/p/62827645
2.4.6 定时发送邮件
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
    # 5.4.3 从数据库汇总每日评分
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
        merge_data.to_excel('data/' + key + '_merge_data.xlsx', index=False)
        print(key + '股价数据合并成功')

    # 绘制舆情得分与股价 的相关系数和关系图
    for key, value in companies_codes.items():
        merge_data = pd.read_excel('data/' + key + '_merge_data.xlsx')

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
    for i in range(2):
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

        # # 3.筛选后文件的移动
        # for pdf_i in pdf_all:
        #     newpath = 'E:\\筛选后的文件夹\\' + pdf_i.split('\\')[-1]  # 这边这个移动到的文件夹一定要提前就创建好！
        #     os.rename(pdf_i, newpath)  # 执行移动操作

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
    data_all.to_excel('data/4/分析师评级报告.xlsx')

    # Analysising
    df = pd.read_excel(r'E:\PycharmProjects\python_fin\myPractice\data\分析师评级报告.xlsx', dtype={'股票代码': str})
    df = df.drop_duplicates()
    df = df.dropna(thresh=5)

    df['研究机构-分析师'] = df['研究机构'] + '-' + df['分析师']
    columns = ['股票名称', '股票代码', '研究机构-分析师', '最新评级', '评级调整', '报告日期']
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
                if ts_result.iloc[-1]['low'] == ts_result.iloc[-1]['high'] and abs(
                        ts_result.iloc[-1]['p_change'] - 10.0) < 0.1:
                    return_rate = 0
                else:
                    start_price = ts_result.iloc[-1]['open']
                    end_price = ts_result.iloc[0]['close']
                    return_rate = (end_price / start_price) - 1.0
            rate.append(return_rate)

        df_use[str(length) + '天收益率'] = rate  # 这里设置要添加的列

        print(df_use)
        means = df_use.groupby('研究机构-分析师')[[str(length) + '天收益率']].mean()
        counts = df_use.groupby('研究机构-分析师')[[str(length) + '天收益率']].count()
        counts = counts.rename(columns={str(length) + '天收益率': '预测次数'})

        df_final = pd.merge(means, counts, on='研究机构-分析师', how='inner')
        df_final.sort_values(by=str(length) + '天收益率', ascending='True', inplace=True)

        df_final.to_excel(r'E:\PycharmProjects\python_fin\myPractice\data\4' + str(length) + '天收益率.xlsx')

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
    plt.plot(stock_table.index, stock_table['成交量涨跌幅2(%)'].apply(lambda x: abs(x)), label='10分钟成交量涨跌幅(%)',
             linestyle='--')
    plt.legend(loc='upper right')

    plt.title(stock_name)
    plt.gcf().autofmt_xdate()

    sht.pictures.add(fig, name='图1', update=True, left=500)
    wb.save(r'E:\PycharmProjects\python_fin\myPractice\data\3' + stock_name + '_股票量化分析.xlsx')
    wb.close()
    app.quit()

    print('股票策略分析及Excel生成完毕')


def scorecard():
    pass

def mail(user,pwd,to):
    user = user
    pwd = pwd
    to = to

    msg = MIMEMultipart()

    mail_msg = """
    <p>这是一个常规段落</p>
    <p><a href="https://www.baidu.com">这是一个包含连接的段落</a></p>
    """
    msg.attach(MIMEText(mail_msg, 'plain', 'utf-8'))

    att1 = MIMEText(open("H:\\DIBS\\tenders\\tenders.xlsx", 'rb').read(), 'base64', 'utf-8')
    att1['Content-Type'] = 'application/octet-stream'
    att1['Content-Disposition'] = 'attachment; filename="test.doc"'
    msg.attach(att1)

    msg['Subject'] = '测试邮件主题'
    msg['From'] = user
    msg['To'] = to

    s = smtplib.SMTP_SSL('smtp.qq.com', 465)
    s.login(user, pwd)
    s.send_message(msg)
    s.quit()
    print('Susses')


if __name__ == "__main__":
    # 2.4.1 舆情分析
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


    # 2.4.2 解析上市公司理财公告
    # 批量爬取巨潮资讯网的上市公司理财公告PDF文件，并通过PDF文件解析技术分析获取到的理财公告
    financial_announcement()



    # 2.4.3 基于评级报告的投资决策分析
    # 爬取和讯研报网的券商分析师评级报告信息，获取股票历史行情数据
    analysist()


    #2.4.4 基于股票信息及其衍生变量的数据分析
    # 通过Tushare库获取股票的基本信息并生成相关的衍生变量，从而进行相关的量化金融数据分析，并通过程序推导计算股价涨跌幅数据以及5日均线数据（ma5）等。
    stock_code = '000002'
    stock_name = '万科A'
    start_date = '2019-02-01'
    end_date = '2019-04-01'
    stock(stock_code, stock_name, start_date, end_date)

    # 2.4.5 构建评分卡模型
    # 使用python数据分析包构筑一个贷款评分卡模型,ROC-AUC能达到1，根据评分卡可以评估用户的信用分数。
    scorecard()


    # 2.4.6 定时发送邮件
    # 将以上五个模块的内容整合成附件，通过QQ邮箱，定期自动发送邮件。
    user = '421751563@qq.com'
    pwd = 'qecctnbkamuabiie'
    to = 'chenjunhang2013@163.com'
    mail(user, pwd, to)
















