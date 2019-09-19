from email.mime.text import MIMEText
import smtplib


def send_email(email, Hits):
    from_email = "webappstest2019@gmail.com"
    from_password = "shosperm"
    to_email = email

    subject = "Restaurants Data"
    message = "Hey there, Your Requested Data : Number of people Who Have Searched for your place  <strong>{}</strong>".format(
        Hits)

    msg = MIMEText(message, 'html')
    msg['Subject'] = subject
    msg['To'] = to_email
    msg['From'] = from_email

    gmail = smtplib.SMTP('smtp.gmail.com', 587)
    gmail.ehlo()
    gmail.starttls()
    gmail.login(from_email, from_password)
    gmail.send_message(msg)