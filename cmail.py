import smtplib
from email.message import EmailMessage
def sendmail(to,subject,body):
    server=smtplib.SMTP_SSL('smtp.gmail.com',465)
    server.login('sksalma9977@gmail.com','nuvo tnaj wyjf gydg')
    msg=EmailMessage()
    msg['FROM']='sksalma9977@gmail.com'
    msg['TO']=to
    msg['SUBJECT']=subject
    msg.set_content(body)
    server.send_message(msg)
    server.close()