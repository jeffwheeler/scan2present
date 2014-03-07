import smtplib

from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart

from email import Encoders

SERVER_EMAIL = 'jeffwheeler@stanford.edu'

def send_pdf(to_addr):
    message = MIMEMultipart()

    message['Subject'] = 'Your PDF'
    message['From'] = SERVER_EMAIL
    message['To'] = to_addr

    pdf = MIMEBase('application', 'pdf')

    fp = open('./tikz_gen/slides.pdf', 'rb')
    pdf.set_payload(fp.read())
    fp.close()

    Encoders.encode_base64(pdf)
    pdf.add_header('Content-Disposition', 'attachment', filename='slides.pdf')

    message.attach(pdf)

    s = smtplib.SMTP('localhost')
    s.sendmail(SERVER_EMAIL, to_addr, message.as_string())
    s.quit()

if __name__ == '__main__':
    send_pdf()
