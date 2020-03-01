
import pymysql
import pandas as pd


# 5.4.3 从数据库汇总每日评分
companies = ['平安银行','万科','国农科技','世纪星源']
date_list = pd.date_range('2019-06-01','2019-11-26')
date_list = list(date_list)
for i in range(len(date_list)):
    date_list[i] = date_list[i].strftime('%Y-%m-%d')

db = pymysql.connect(host='localhost',port=3306,user='root',password='forjun598',database='pacong',charset='utf8')
cur = db.cursor()
order = 'select score from baidu where company=%s and date=%s'
print('开始汇总分数'+'\n')
for i in companies:
    score_dict = {}
    for j in date_list:
        total_score = 100
        cur.execute(order,(i,j))
        score_data = cur.fetchall()
        for k in range(len(score_data)):
            total_score += score_data[k][0]
        score_dict[j] = total_score
        print(i+''+j+' 舆论总评分为'+str(total_score)+'\n')

    data = pd.DataFrame(list(score_dict.items()),columns=['date','score'])
    data.to_excel(r'E:\PycharmProjects\python_fin\myPractice\data\1\%s_score.xlsx'%i , index=False)
print('结束汇总分数' + '\n')
cur.close()
db.close()