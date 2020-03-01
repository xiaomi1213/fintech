#
# # coding: utf-8
#
# # # 1 提出问题
#
# # 构建申请评分卡模型
#
# # # 2 获取数据
#
# # ## 2.1 下载数据
#
# # 从kaggle上获取Give me some credit数据集https://www.kaggle.com/brycecf/give-me-some-credit-dataset
#
# # ## 2.2 导入数据
#
# # In[1]:
#
#
# # 导入相关函数包
# import numpy as np
# import pandas as pd
#
#
# # In[2]:
#
#
# # 将数据集导入为DataFrame
# trainDf = pd.read_csv(r'E:\Jupyter\Projects\Card\cs-training.csv',index_col=0)
# testDf = pd.read_csv(r'E:\Jupyter\Projects\Card\cs-test.csv',index_col=0)
# target = pd.read_csv(r'E:\Jupyter\Projects\Card\sampleEntry.csv',index_col=0)
#
#
# # # 3 理解数据
#
# # ## 3.1 字段类型与取值
#
# # In[3]:
#
#
# # 训练数据集信息
# trainDf.info()
#
#
# # In[4]:
#
#
# trainDf.head()
#
#
# # * 此数据集有150000行，11列
# # * 字段SeriousDlqin2yrs表示目标变量，1为不良贷款，0为良性贷款
# # * 其他字段为用户的信息
# # * 数据类型及缺失值如上表
#
# # In[5]:
#
#
# # 测试数据集信息
# testDf.info()
#
#
# # In[6]:
#
#
# testDf.head()
#
#
# # * 测试数据集有101503行，11列
# # * 可以看到测试数据集中SeriousDlqin2yrs字段的值为全为空，这是需要我们建立模型去预测的
# # * 其他变量同trainDf类似
#
# # In[7]:
#
#
# # 查看target文件
# target.head()
#
#
# # In[8]:
#
#
# # 将sampleEntry里的数值映射为二分类，大于0.5映射为1，小于0.5映射为0
# targetMap = target.applymap(lambda x : 1 if x > 0.5 else 0)
# targetMap.head()
#
#
# # In[9]:
#
#
# # 将映射后的sampleEntry与testDf合并，便于后续数据处理
# testDf['target'] = targetMap['Probability']
# testDf.head()
#
#
# # In[10]:
#
#
# # 为了方便处理数据，将trainDf和testDf合并为一个大的数据集
# totalDf = pd.concat([trainDf, testDf], axis=0)
# totalDf.head()
#
#
# # In[11]:
#
#
# totalDf.info()
#
#
# # In[12]:
#
#
# # 重新整理totalDf索引号
# totalDf = totalDf.reset_index(drop=True)
#
#
# # In[13]:
#
#
# totalDf.info()
#
#
# # # 4 处理数据
#
# # ## 4.1 选择子集
#
# # 这里每个字段都可能用到，所以保留所有字段
#
# # ## 4.2 列名重命名
#
# # In[14]:
#
#
# # 列名过于长，不方便处理
# # 列名重命名字典，中文名根据英文名翻译，并非专业术语
# # target字段不做处理
# renameDict = {'DebtRatio':'负债率',
#               'MonthlyIncome':'月收入',
#               'NumberOfDependents':'家属数量',
#               'NumberOfOpenCreditLinesAndLoans':'信贷数量',
#               'NumberOfTime30-59DaysPastDueNotWorse':'逾期30-59天次数',
#               'NumberOfTime60-89DaysPastDueNotWorse':'逾期60-89天次数',
#               'NumberOfTimes90DaysLate':'逾期90天次数',
#               'NumberRealEstateLoansOrLines':'固定资产贷款数',
#               'RevolvingUtilizationOfUnsecuredLines':'循环额度率',
#               'SeriousDlqin2yrs':'优劣贷款',
#               'age':'年龄',
#             }
# totalDf.rename(columns=renameDict, inplace=True)
# totalDf.head()
#
#
# # ## 4.3 删除重复值
#
# # In[15]:
#
#
# print('删除重复值之前的行数：',totalDf.shape[0])
# totalDf.drop_duplicates(inplace=True)
# print('删除重复值之后的行数：',totalDf.shape[0])
#
#
# # ## 4.4 字段分析处理
#
# # ### 4.4.1 一致化处理
#
# # 这里不需要进行一致化处理
#
# # ### 4.4.2 异常值处理
#
# # * 优劣贷款分布
#
# # In[16]:
#
#
# badNum = totalDf['优劣贷款'].sum()
# goodNum = totalDf[totalDf['优劣贷款'].notnull()].shape[0] - badNum
# print('好坏贷款之比：' ,badNum/goodNum)
#
#
# # In[17]:
#
#
# #导入图像分析工具包
# import matplotlib.pyplot as plt
# import seaborn as sns
#
#
# # In[18]:
#
#
# f, ax = plt.subplots(figsize=(20,10))
# sns.countplot('优劣贷款',data=totalDf)
# plt.show()
#
#
# # 好坏贷款数量差别较大，属于类不平衡的问题，这留在后面处理
#
# # * 循环额度率
#
# # In[19]:
#
#
# f, [ax1, ax2] = plt.subplots(1,2,figsize=(20,10))
# sns.distplot(totalDf['循环额度率'],ax=ax1)
# sns.boxplot(y='循环额度率',data=totalDf, ax=ax2)
# plt.show()
#
#
# # In[20]:
#
#
# totalDf['循环额度率'].describe()
#
#
# # 使用seaborn.distplot和boxplot画出该字段的分布，并且调用describe()查看数据的统计信息，
# #
# # 数据分布及其不正常，中位数和四分之三位数都小于1，但是最大值确达到了50708，
# #
# # 可用额度比值应该小于1，这里将大于1的值当做异常值剔除。
#
# # In[21]:
#
#
# # 异常值剔除
# totalDf = totalDf[totalDf['循环额度率']<1]
#
#
# # * 年龄
#
# # In[22]:
#
#
# f,[ax1,ax2] = plt.subplots(1,2,figsize=(20,10))
# sns.distplot(totalDf['年龄'], ax=ax1)
# sns.boxplot(y='年龄',data=totalDf, ax=ax2)
# plt.show()
#
#
# # In[23]:
#
#
# totalDf['年龄'].describe()
#
#
# # 初步觉得年龄小于18和大于90的都是异常值，进行详细的查看：
#
# # In[24]:
#
#
# totalDf[totalDf['年龄']<18]
#
#
# # In[25]:
#
#
# totalDf[totalDf['年龄']>90].head()
#
#
# # 通过筛选查看可发现一个年龄为0的客户，这显然不合常理，故作为异常值进行剔除；而年龄大于90岁的用户较多，
# #
# # 因此我们有理由相信这些是正常值，后续得以保留。
#
# # In[26]:
#
#
# # 异常值剔除
# totalDf = totalDf[totalDf['年龄']>18]
#
#
# # * 逾期天数
# #
# # 逾期30-59天次数
# #
# # 逾期60-89天次数
# #
# # 逾期90天次数
#
# # 这三个字段放到一起进行查看分布
#
# # In[27]:
#
#
# f,[[ax1,ax2],[ax3,ax4],[ax5,ax6]] = plt.subplots(3,2,figsize=(20,10))
# sns.distplot(totalDf['逾期30-59天次数'],ax=ax1)
# sns.boxplot(y='逾期30-59天次数',data=totalDf, ax=ax2)
# sns.distplot(totalDf['逾期60-89天次数'],ax=ax3)
# sns.boxplot(y='逾期60-89天次数',data=totalDf, ax=ax4)
# sns.distplot(totalDf['逾期90天次数'],ax=ax5)
# sns.boxplot(y='逾期90天次数',data=totalDf, ax=ax6)
# plt.show()
#
#
# # In[28]:
#
#
# totalDf.loc[:,['逾期30-59天次数','逾期60-89天次数','逾期90天次数']].describe()
#
#
# # 通过箱线图我们明显看到数据的上界存在异常值，再结合分位数我们将大于80的值作为异常值进行剔除。
#
# # In[29]:
#
#
# # 异常值剔除
# totalDf = totalDf[totalDf['逾期30-59天次数']<80]
# totalDf = totalDf[totalDf['逾期60-89天次数']<80]
# totalDf = totalDf[totalDf['逾期90天次数']<80]
#
#
# # * 负债率
#
# # In[30]:
#
#
# f,[ax1,ax2] = plt.subplots(1,2,figsize=(20,10))
# sns.distplot(totalDf['负债率'], ax=ax1)
# sns.boxplot(y='负债率',data=totalDf, ax=ax2)
# plt.show()
#
#
# # In[31]:
#
#
# totalDf['负债率'].describe()
#
#
# # 该字段分布与上面的数据相似，应该将最大值剔除，再仔细查看一下大于1的值，
# #
# # 发现有三万多笔，所以猜测可能是正常值。
#
# # In[32]:
#
#
# totalDf[totalDf['负债率']>1].count()
#
#
# # * 月收入
#
# # In[33]:
#
#
# f,[ax1,ax2] = plt.subplots(1,2,figsize=(20,10))
# sns.kdeplot(totalDf['月收入'], ax=ax1)
# sns.boxplot(y='月收入',data=totalDf, ax=ax2)
# plt.show()
#
#
# # In[34]:
#
#
# totalDf['月收入'].describe()
#
#
# # 月收入字段的值并没有明显的异常，所以不做处理
#
# # * 信贷数量
#
# # In[35]:
#
#
# f,[ax1,ax2] = plt.subplots(1,2,figsize=(20,10))
# sns.distplot(totalDf['信贷数量'], ax=ax1)
# sns.boxplot(y='信贷数量',data=totalDf, ax=ax2)
# plt.show()
#
#
# # In[36]:
#
#
# totalDf['信贷数量'].describe()
#
#
# # 并无明显异常，不过最大值为85，需要注意是否存在借款还贷的可能
#
# # * 固定资产贷款数
#
# # In[37]:
#
#
# f,[ax1,ax2] = plt.subplots(1,2,figsize=(20,10))
# sns.distplot(totalDf['固定资产贷款数'], ax=ax1)
# sns.boxplot(y='固定资产贷款数',data=totalDf, ax=ax2)
# plt.show()
#
#
# # In[38]:
#
#
# totalDf['固定资产贷款数'].describe()
#
#
# # 并无明显异常
#
# # * 家属数量
#
# # In[39]:
#
#
# f,[ax1,ax2] = plt.subplots(1,2,figsize=(20,10))
# sns.kdeplot(totalDf['家属数量'], ax=ax1)
# sns.boxplot(y='家属数量',data=totalDf, ax=ax2)
# plt.show()
#
#
# # In[40]:
#
#
# totalDf['家属数量'].describe()
#
#
# # In[41]:
#
#
# # 家属数量最大值为43，此为可能异常值，所以将家属数量大于10的记录剔除
# totalDf = totalDf[totalDf['家属数量']<=10]
#
#
# # ### 4.4.3 填补缺失值
#
# # In[42]:
#
#
# totalDf.isnull().sum()
#
#
# # * 优劣贷款字段的缺失值是testDf的缺失值，而target字段缺失值是trainDf的缺失值，所以不用处理。
# # * 月收入字段缺失值数量为49047
# # * 其他字段没有缺失值
#
# # * 填补月收入字段缺失值
#
# # In[43]:
#
#
# # 查看月收入字段缺失值占总记录数的比例
# IncomeRatio = totalDf['月收入'].isnull().sum()/totalDf.shape[0]
# print('月收入字段缺失值占总记录数的比例:',IncomeRatio)
#
#
# # 月收入字段缺失值占到总记录数将近20%，不适合使用简单的统计量填补，所以改用模型预测填充
#
# # In[44]:
#
#
# # 使用随机森林模型对月收入字段进行填补
# from sklearn.ensemble import RandomForestClassifier
#
# known = totalDf[totalDf['月收入'].notnull()]
# unknown = totalDf[totalDf['月收入'].isnull()]
# X_train = known.iloc[:10000,[0,2,3,4,5,6,7,8,10]]
# y_train = known.iloc[:10000,1]
# X_test = unknown.iloc[:,[0,2,3,4,5,6,7,8,10]]
#
# model = RandomForestClassifier(n_estimators=3, random_state=0)
# model.fit(X_train, y_train)
# y_test = model.predict(X_test)
#
# totalDf.loc[totalDf['月收入'].isnull(),'月收入'] = y_test
#
#
# # In[45]:
#
#
# # 检查是否填补上了
# totalDf.isnull().sum()
#
#
# # * 家属数量缺失值填补
#
# # In[46]:
#
#
# # 查看家属数量字段信息
# #totalDf['家属数量'].describe()
#
#
# # In[47]:
#
#
# # 使用中位数填补
# #totalDf['家属数量'].fillna(0,inplace=True)
# #totalDf.isnull().sum()
#
#
# # ### 4.4数据排序
#
# # 这里不需要排序
#
# # # 5 特征选择
#
# # ## 5.1 相关性分析
#
# # In[48]:
#
#
# corrDf = totalDf.corr()
# corrDf
#
#
# # In[49]:
#
#
# corrDf['优劣贷款'].sort_values(ascending=False)
#
#
# # 各个字段与优劣贷款字段的相关性差异不大，所以都可保留作为特征
#
# # ## 5.2 特征分箱处理
#
# # 对连续特征进行分箱处理，用于特征的筛选，降低模型过拟合的可能性，并构造评分卡模型
#
# # In[50]:
#
#
# import scipy.stats.stats as stats
# def mono_bin(Y, X, n=10):
#     r = 0
#     badNum = Y.sum()
#     goodNum = Y.count() - Y.sum()
#     while abs(r) < 1:
#         d1 = pd.DataFrame({'X':X, 'Y':Y, 'Bucket':pd.qcut(X,n)})
#         d2 = d1.groupby('Bucket', as_index=True)
#         r,p = stats.spearmanr(d2.mean().X, d2.mean().Y)
#         n = n-1
#     d3 = pd.DataFrame()
#     d3['min'] = d2.min().X
#     d3['max'] = d2.max().X
#     d3['badcostum'] = d2.sum().Y
#     d3['goodcostum'] = d2.count().Y - d2.sum().Y
#     d3['total'] = d2.count().Y
#     d3['bad_rate'] = d2.sum().Y/d2.count().Y
#     d3['woe'] = np.log(d3['badcostum']/d3['goodcostum']*(goodNum/badNum))
#     iv = ((d3['badcostum']/badNum)-d3['goodcostum']/goodNum)*d3['woe']
#     d3['iv'] = iv
#     woe = list(d3['woe'].round(6))
#     cut = list(d3['max'].round(6))#使得后面变换woe后是单一的值而不是区间，也可以取区间平均值
#     cut.insert(0,float('-inf'))
#     cut[-1] = float('inf')
#     return d3, cut, woe, iv
#
#
# # In[51]:
#
#
# dfx1, cut1, x1_woe, iv1 = mono_bin(totalDf['优劣贷款'],totalDf['循环额度率'], 5)
# dfx2, cut2, x2_woe, iv2 = mono_bin(totalDf['优劣贷款'],totalDf['年龄'], 5)
# dfx4, cut4, x4_woe, iv4 = mono_bin(totalDf['优劣贷款'],totalDf['负债率'], 5)
# dfx5, cut5, x5_woe, iv5 = mono_bin(totalDf['优劣贷款'],totalDf['月收入'], 5)
#
#
# # 并且对于其中不能使用自动分箱的特征进行手动分箱：
#
# # In[52]:
#
#
# def hand_bin(Y, X, cut):
#     badNum = Y.sum()
#     goodNum = Y.count() - Y.sum()
#
#     d1 = pd.DataFrame({'X':X, 'Y':Y, 'Bucket':pd.cut(X,cut)})
#     d2 = d1.groupby('Bucket', as_index=True)
#
#
#     d3 = pd.DataFrame()
#     d3['min'] = d2.min().X
#     d3['max'] = d2.max().X
#     d3['badcostum'] = d2.sum().Y
#     d3['goodcostum'] = d2.count().Y - d2.sum().Y
#     d3['total'] = d2.count().Y
#     d3['bad_rate'] = d2.sum().Y/d2.count().Y
#     d3['woe'] = np.log(d3['badcostum']/d3['goodcostum']*(goodNum/badNum))
#     iv = ((d3['badcostum']/badNum)-d3['goodcostum']/goodNum)*d3['woe']
#     d3['iv'] = iv
#     woe = list(d3['woe'].round(6))
#
#     return d3, cut, woe, iv
#
#
# # In[53]:
#
#
# ninf = float('-inf')
# pinf = float('inf')
# cut3 = [ninf, 0, 1, 3, 5, pinf]
# cut6 = [ninf, 1, 2, 3, 5, pinf]
# cut7 = [ninf, 0, 1, 3, 5, pinf]
# cut8 = [ninf, 0, 1, 2, 3, pinf]
# cut9 = [ninf, 0, 1, 3, pinf]
# cut10 = [ninf, 0, 1, 3, 5, pinf]
#
#
# # In[54]:
#
#
# dfx3, cut3, x3_woe, iv3 = hand_bin(totalDf['优劣贷款'],totalDf['逾期30-59天次数'], cut3)
# dfx6, cut6, x6_woe, iv6 = hand_bin(totalDf['优劣贷款'],totalDf['信贷数量'], cut6)
# dfx7, cut7, x7_woe, iv7 = hand_bin(totalDf['优劣贷款'],totalDf['逾期90天次数'], cut7)
# dfx8, cut8, x8_woe, iv8 = hand_bin(totalDf['优劣贷款'],totalDf['固定资产贷款数'], cut8)
# dfx9, cut9, x9_woe, iv9 = hand_bin(totalDf['优劣贷款'],totalDf['逾期60-89天次数'], cut9)
# dfx10, cut10, x10_woe, iv10 = hand_bin(totalDf['优劣贷款'],totalDf['家属数量'], cut10)
#
#
# # In[55]:
#
#
# dfx3
#
#
# # In[56]:
#
#
# iv1.sum()
#
#
# # In[57]:
#
#
# # 计算完所有特征后，统一查看：
# IV = pd.DataFrame([iv1.sum(), iv2.sum(), iv3.sum(), iv4.sum(), iv5.sum(),
# iv6.sum(), iv7.sum(), iv8.sum(), iv9.sum(), iv10.sum()],
#               index=['循环额度率','年龄','逾期30-59天次数','负债率',\
#                    '月收入','信贷数量','逾期90天次数','固定资产贷款数',\
#                    '逾期60-89天次数','家属数量'])
# IV
#
#
# # 我们看到各个特征的iv值都不是太小，所以在建模时这些特征都保留。
#
# # 现在我们有了各个特征区间的woe值，接下来我们将训练数据和测试数据用woe值替换，用replace_woe函数来进行该操作。
#
# # In[58]:
#
#
# def replace_woe(X, cut, woe):
#     x_woe = pd.cut(X, cut, labels=woe)
#     return x_woe
#
#
# # In[59]:
#
#
# woed_x1 = replace_woe(totalDf['循环额度率'], cut1, x1_woe)
# woed_x2 = replace_woe(totalDf['年龄'], cut2, x2_woe)
# woed_x3 = replace_woe(totalDf['逾期30-59天次数'], cut3, x3_woe)
# woed_x4 = replace_woe(totalDf['负债率'], cut4, x4_woe)
# woed_x5 = replace_woe(totalDf['月收入'], cut5, x5_woe)
# woed_x6 = replace_woe(totalDf['信贷数量'], cut6, x6_woe)
# woed_x7 = replace_woe(totalDf['逾期90天次数'], cut7, x7_woe)
# woed_x8 = replace_woe(totalDf['固定资产贷款数'], cut8, x8_woe)
# woed_x9 = replace_woe(totalDf['逾期60-89天次数'], cut9, x9_woe)
# woed_x10 = replace_woe(totalDf['家属数量'], cut10, x10_woe)
#
#
# # In[60]:
#
#
# woed_x10.isnull().sum()
#
#
# # In[61]:
#
#
# woeDf = pd.DataFrame({'循环额度率':woed_x1,
#                         '年龄':woed_x2,
#                         '逾期30-59天次数':woed_x3,
#                         '负债率':woed_x4,
#                         '月收入':woed_x5,
#                         '信贷数量':woed_x6,
#                         '逾期90天次数':woed_x7,
#                         '固定资产贷款数':woed_x8,
#                         '逾期60-89天次数':woed_x9,
#                         '家属数量':woed_x10})
#
#
# # In[62]:
#
#
# # 将替换好的训练集和测试集数据保存下来，生成新的csv文件，方便后面建模。
# woeDf.to_csv(r'./woeDf.csv')
#
#
# # # 6 选择模型
#
# # ## 6.1 分割数据集
#
# # In[63]:
#
#
# # 计算训练数据集记录数
# trainNum = totalDf[totalDf['优劣贷款'].notnull()].shape[0]
# trainNum
#
#
# # In[64]:
#
#
# # 分割数据集
# train_woe_X = woeDf.iloc[:trainNum,:] #剔除target字段
# print('训练数据集大小：',train_woe_X.shape)
# test_woe_X = woeDf.iloc[trainNum:,:]
# print('测试集大小：',test_woe_X.shape)
#
#
# # In[65]:
#
#
# # 重新设置索引
# test_woe_X = test_woe_X.reset_index(drop=True)
# test_woe_X.head()
#
#
# # In[66]:
#
#
# # 训练目标
# train_y = totalDf[totalDf['优劣贷款'].notnull()]['优劣贷款']
# print('训练目标大小：',train_y.shape)
# # 测试目标
# test_y = totalDf[totalDf['target'].notnull()]['target']
# print('测试目标大小：',test_y.shape)
#
#
# # ## 6.2 交叉验证
#
# # In[67]:
#
#
# # 导入备选模型
# from sklearn.ensemble import RandomForestClassifier
# from sklearn.ensemble.gradient_boosting import GradientBoostingClassifier
# from sklearn.linear_model import LogisticRegression
#
# #导入交叉验证所需要的包
# from sklearn.model_selection import StratifiedKFold
# from sklearn.model_selection import GridSearchCV
# from sklearn.model_selection import cross_val_score
#
# import numpy as np
#
#
# # In[68]:
#
#
# # 定义函数，根据给定的指标得到交叉验证的平均得分
# def compute_score(model, X, y, scoring='accuracy'):
#     cv_score = cross_val_score(model, X, y, cv=5, scoring=scoring)
#     return np.mean(cv_score)
#
#
# # In[69]:
#
#
# #实例化各个模型
# rfc = RandomForestClassifier()
# gbc = GradientBoostingClassifier()
# lr = LogisticRegression()
#
# model_list = [rfc, gbc, lr]
#
#
# # In[70]:
#
#
# # 多个模型进行交叉验证
# for model in model_list:
#     score = compute_score(model=model, X=train_woe_X, y=train_y, scoring='accuracy')
#     print('验证的模型是：',model.__class__)
#     print('验证的分数是：',score)
#     print('************')
#
#
# # 由交叉验证的结果可见，gradient_boosting的得分最高，其他两个模型的得分也差不多，
# #
# # 但是为了便于构造评分卡模型，所以下面使用逻辑回归模型来构造评分卡
#
# # # 7 训练模型
#
# # In[71]:
#
#
# #不做最优超参数选择，直接使用默认参数
# model = LogisticRegression()
# model.fit(train_woe_X, train_y)
#
#
# # 模型训练完，我们得到预测的数据以及模型各个特征的权重
#
# # In[72]:
#
#
# coe = model.coef_
# coe
#
#
# # # 8 验证模型
#
# # 由于我们在之前查看样本目标变量分布观察到样本及其不均衡，所以我们不能使用预测准确率来判断模型的好坏。假设我们有一批样本，其中的正负样本的比例为90：10，如果我们全部预测为正样本，那我们的准确率也达到了90%，但是这种模型没有什么作用，所以预测准确率并不能完全反映模型的性能。
# #
# # 那针对不平衡的样本我们应该使用什么样的评估指标呢？
# #
# # 一般使用ROC（Receiver Operating Characteristic ）和 AUC （Area Under Curve）指标来评价训练不均衡样本的模型泛化能力，关于这两个指标如果要详细解释估计要写一篇文章了，所以这里不做赘述，简单的介绍一下。
# #
# # ROC曲线是有一系列（FPR,TPR）的点组成的一条曲线，而AUC值是计算的这条曲线下面的面积。FPR（False Postive Rate）; TPR (True Positive Rate)
# #
# # 我们可以直接使用sklearn的里面的roc_curve计算fpr，tpr；auc直接计算AUC值。具体实现代码如下：
#
# # In[73]:
#
#
# #使用训练好的模型和预测数据集进行预测
# pred_y = model.predict_proba(test_woe_X)[:,1]
#
# import matplotlib.pyplot as plt
# get_ipython().run_line_magic('matplotlib', 'inline')
# from sklearn.metrics import roc_curve, auc
# fpr, tpr, threshold = roc_curve(test_y, pred_y)
# auc_score = auc(fpr, tpr)
# plt.figure(figsize=(10,8))
# plt.plot(fpr, tpr, linewidth=2, label='AUC = %.2f'%auc_score)
# plt.plot([0,1],[0,1],'k--')
# plt.axis([0,1,0,1])
# plt.xlabel('False Positive Rate')
# plt.ylabel('True Positive Rate')
# plt.legend()
#
#
# # In[74]:
#
#
# fig, ax = plt.subplots()
# ax.plot(1 - threshold, tpr, label='tpr')
# ax.plot(1 - threshold, fpr, label='fpr')
# ax.plot(1 - threshold, tpr-fpr, label='KS')
# plt.xlabel('score')
# plt.title('KS Curve')
# plt.xlim([0.0, 1.0])
# plt.ylim([0.0, 1.0])
# plt.figure(figsize=(20,20))
# legend = ax.legend(loc='upper left')
# plt.show()
#
#
# # In[75]:
#
#
# max(tpr-fpr)
#
#
# # # 9 构建评分卡
#
# # In[76]:
#
#
# # 模型结果转评分函数
# factor = 20/np.log(2)
# offset = 600 - 20*np.log(20)/np.log(2)
#
# def get_score(coe, woe, factor):
#     scores = []
#     for w in woe:
#         score = round(coe*w*factor, 0)
#         scores.append(score)
#     return scores
#
#
# # In[77]:
#
#
# x1 = get_score(coe[0][0], x1_woe, factor)
# x2 = get_score(coe[0][1], x2_woe, factor)
# x3 = get_score(coe[0][2], x3_woe, factor)
# x4 = get_score(coe[0][3], x4_woe, factor)
# x5 = get_score(coe[0][4], x5_woe, factor)
# x6 = get_score(coe[0][5], x6_woe, factor)
# x7 = get_score(coe[0][6], x7_woe, factor)
# x8 = get_score(coe[0][7], x8_woe, factor)
# x9 = get_score(coe[0][8], x9_woe, factor)
# x10 = get_score(coe[0][9], x10_woe, factor)
# print('循环额度率 对应的分数:',x1)
# print('年龄 对应的分数:',x2)
# print('逾期30-59天次数 对应的分数:',x3)
# print('负债率 对应的分数:',x4)
# print('月收入 对应的分数:',x5)
# print('信贷数量 对应的分数:',x6)
# print('逾期90天次数 对应的分数:',x7)
# print('固定资产贷款数 对应的分数:',x8)
# print('逾期60-89天次数 对应的分数:',x9)
# print('家属数量 对应的分数:',x10)
#
#
# # In[79]:
#
#
# x5_woe
#
#
# # 我们然后根据评分卡，算出每个特征的分数，最后所有特征的分数相加再加上基准分数就是用户的总得分了。
#
# # In[78]:
#
#
# def calsumscore(woe_list, coe):
#     n = coe.shape[1]
#     series = 0
#     for i in range(n):
#         series += coe[0][1]*np.array(woe_list.iloc[:,i])
#         #series1 = series1 + series
#     score = series*factor + offset
#     return series
#
