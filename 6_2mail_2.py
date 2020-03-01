import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

from email.mime.application import MIMEApplication

if __name__ == '__main__':
    fromaddr = ''
    password = ''
    toaddrs = ['','']


    content = 'hello, this is a email content'
    textApart = MIMEText(content)

    imageFile = '1.png'
    imageApart = MIMEImage(open(imageFile,'rb').read())
    imageApart.add_header('Contentd-Disposition','attachment',filename=imageFile)

    pdfFile = ''
    pdfApart = MIMEApplication(open(pdfFile,'rb').read())
    pdfApart.add_header('Content-Disposition','attachment',filename=pdfFile)


    zipFile = ''
    zipApart = MIMEApplication(open(zipFile,'rb').read())
    zipApart.add_header('Content-Disposition','attachment',filename=zipFile)

    m = MIMEMultipart()
    m.attach(textApart)
    m.attach(imageApart)
    m.attach(pdfApart)
    m.attach(zipApart)
    m['Subject'] = 'title'


    try:
        server = smtplib.SMTP_SSL('smtp.qq.com',465)
        server.login(fromaddr,password)
        server.sendmail(fromaddr, toaddrs, m.as_string())
        print('success')
        server.quit()
    except smtplib.SMTPException as e:
        print('error',e)