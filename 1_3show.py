import datetime
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
import tushare as ts
import numpy as np


plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_mnus'] = False


companies_codes = {'平安银行':'000001','万科':'000002','国农科技':'000004','世纪星源':'000005'}


# 获取股价数据，并与舆情得分合并为一个文件
for key,value in companies_codes.items():
    try:
        data = ts.get_hist_data(value, start='2019-06-01', end='2019-11-26')
    except:
        data = pd.DataFrame(np.arange(338).reshape(26,13))
    data.to_excel(r'E:\PycharmProjects\python_fin\myPractice\data\1'+key+'_share.xlsx')
    print(key+'股价数据保存成功')

    score = pd.read_excel(r'E:\PycharmProjects\python_fin\myPractice\data\1'+key+'_score.xlsx')
    share = pd.read_excel(r'E:\PycharmProjects\python_fin\myPractice\data\1'+key+'_share.xlsx')
    share = share[['date','close']]
    merge_data = pd.merge(score,share,on='date',how='inner')
    merge_data = merge_data.rename(columns={'close':'price'})
    merge_data.to_excel('data/'+key+'_merge_data.xlsx',index=False)
    print(key+'股价数据合并成功')



# 绘制舆情得分与股价 的相关系数和关系图
for key,value in companies_codes.items():
    merge_data = pd.read_excel('data/'+key+'_merge_data.xlsx')

    corr = pearsonr(merge_data['score'],merge_data['price'])
    print('相关系数r值为' + str(corr[0]) + '，显著性水平P值为' + str(corr[1]))


    for i in range(len(merge_data['date'])):
        merge_data['date'][i] = datetime.datetime.strptime(merge_data['date'][i], '%Y-%m-%d')

    plt.plot(merge_data['date'], merge_data['score'], color='blue', label=key+'_score')
    plt.xticks(rotation=45)
    plt.legend(loc='upper left')
    plt.twinx()
    plt.plot(merge_data['date'], merge_data['price'], color='red', label=key+'_price')
    plt.xticks(rotation=45)
    plt.legend(loc='upper right')
    plt.show()






