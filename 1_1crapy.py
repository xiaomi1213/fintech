import requests
import re
import time
import pymysql


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




if __name__ == "__main__":
    # 爬取并存储数据
    companies = ['平安银行', '万科', '国农科技', '世纪星源']
    page_num = 50
    for i in companies:
        for j in range(page_num):
            baidu(i,j)
            print('百度'+'爬取'+i+'第'+str(j+1)+'页'+'成功'+'\n')


