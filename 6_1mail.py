import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

user = '421751563@qq.com'
pwd = 'qecctnbkamuabiie'
to = 'chenjunhang2013@163.com'

msg = MIMEMultipart()

mail_msg = """
<p>这是一个常规段落</p>
<p><a href="https://www.baidu.com">这是一个包含连接的段落</a></p>
"""
msg.attach(MIMEText(mail_msg, 'plain', 'utf-8'))


att1 = MIMEText(open("H:\\DIBS\\tenders\\tenders.xlsx",'rb').read(), 'base64', 'utf-8')
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
