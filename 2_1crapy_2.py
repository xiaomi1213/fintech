from selenium import webdriver
import re
import time
import pdfplumber
import os

executable_path=r'D:\Anaconda3\Scripts\chromedriver.exe'
#executable_path=r'E:\ProgramData\Anaconda3\Scripts\chromedriver.exe'
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
prefs = {'profile.default_content_settings.popups': 0,
         'download.default_directory': r'E:\PycharmProjects\python_fin\myPractice\data\2'} #这边你可以修改文件储存的位置
chrome_options.add_experimental_option('prefs', prefs)
browser = webdriver.Chrome(executable_path=executable_path)

url = 'http://www.cninfo.com.cn/'
browser.get(url)
time.sleep(5)
browser.maximize_window()

#browser.find_element_by_xpath('//*[@id="common_top_input_obj"]').clear()
browser.find_element_by_xpath('//*[@id="common_top_input_obj"]').send_keys('理财')
browser.find_element_by_xpath('//*[@id="common_top_button"]').click()
time.sleep(3)
html0 = browser.page_source
p_page = 'id="page-info-title"><span>合计约(.*?)条</span>'
page_num = re.findall(p_page, html0, re.S)[0]
pages = int(int(page_num)/10)


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
hrefs = re.findall(p_href,all_html,re.S)
dates = re.findall(p_date, all_html, re.S)


for i in range(len(titles)):
    titles[i] = re.sub('<.*?>','',titles[i])
    hrefs[i] = 'http://www.cninfo.com.cn'+hrefs[i]
    hrefs[i] = re.sub('amp;','',hrefs[i])
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

        time.sleep(8) # 等待文件下载时间

        print(str(i + 1) + '.' + titles[i] + '是PDF文件')
    except:
        print(titles[i] + '不是PDF文件')
browser.quit()




# 1.遍历文件夹中的所有PDF文件
file_dir = r'E:\PycharmProjects\python_fin\myPractice\data\2'
file_list =[]
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
        text = page.extract_text()# 提取当页的文本内容
        text_list.append(text)
    text_all = ''.join(text_list)# 把列表转换成字符串
    pdf.close()

    # 通过正文进行筛选
    if ('自有' in text_all) or ('议案' in text_all) or ('理财' in text_all) or ('现金管理' in text_all):
        pdf_all.append(file_list[i])

# # 3.筛选后文件的移动
# for pdf_i in pdf_all:
#     newpath = 'E:\\筛选后的文件夹\\' + pdf_i.split('\\')[-1]  # 这边这个移动到的文件夹一定要提前就创建好！
#     os.rename(pdf_i, newpath)  # 执行移动操作

    print('PDF文本解析及筛选完毕！')























