#!/bin/python
import requests, json, os, logging, datetime, smtplib
import pandas as pd
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from requests.auth import HTTPBasicAuth



def get_mft_status(logger, ip, user, password):
    """
    Use REST API to get Heap Memory Used, GET http://[server URL]:[port]/goanywhere/rest/gacmd/v1/system/status
    Return 3 str: heapMemoryUsed, nonHeapMemoryUsed, heapMemoryMaximum
    :param ip: str, IP addres of server
    :param user: str, username to authenticate
    :param password: str, passwort for authentication
    :return: heapMemoryUsed, nonHeapMemoryUsed, heapMemoryMaximum
    """
    flag = 0
    status = 'STARTED'
    url = str('').join(['http://', ip, ':8000/goanywhere/rest/gacmd/v1/services/status?services=8'])
    try:
        respond = requests.get(url, auth=HTTPBasicAuth(user, password), timeout=3.0)
        respond = json.loads(respond.text)
        for i in range(len(respond["data"])):
            if respond["data"][i]["status"] != 'STARTED':
                status = respond["data"][i]["status"]
                flag = 1
    except requests.exceptions.Timeout:
        logger.info('Get timeout of 3 sec for request %s', url,)
        flag = 1
        status = 'Get timeout of 3 sec'
    except requests.exceptions.TooManyRedirects:
        logger.info('Get Too Many Redirects for request %s', url, )
        flag = 1
        status = 'Get Too Many Redirects'
    except requests.exceptions.RequestException as e:
        logger.info('Get Error for url %s', url, )
        flag = 1
        status = 'Get Error'
    return ip, flag, status



def script_log(script_dir, log_name, date='20210101'):
    '''
    Create and conf the log file
    :param script_dir: base script location
    :return: obj logger
    '''
    if not os.path.isdir(str('/'.join([script_dir, 'logs']))):  # If no logs dir, creating log dir
        try:
            os.makedirs(str('/'.join([script_dir, 'logs'])))
            log_file = str(''.join([script_dir, '/', 'logs', '/', log_name, '.log', '_', date]))
        except OSError:
            print("Creation of the directory %s failed, log file will be in the /tmp directory " + str(
                '/'.join([script_dir, 'logs'])))
            log_file = str(''.join(['/tmp/', log_name, '.log']))
    else:
        log_file = str(''.join([script_dir, '/', 'logs', '/', log_name, '.log', '_', date]))

    logging.basicConfig(filename=log_file,
                        format='%(asctime)s %(message)s',
                        filemode='a')
    # Creating an object
    logger = logging.getLogger()
    # Setting the threshold of logger to INFO, DEBUG
    logger.setLevel(logging.INFO)

    return (logger)

def send_email(logger, html_data, send_to, email_subject="Goanyware monitor"):
    '''
    The function send email via dedicated email server
    :param html_data: str, body of the email
    :param distribution_list: str, destination email
    :param mail_server: str, smtp server to send email, for example 'smtp.office365.com'
    :param mail_user: str, user to authenticat to smtp server
    :param mail_password: str, password to authenticat to smtp server
    :param send_user: str, user who send the email
    :param subject: str, email subject
    :return: none
    '''
    smtpsrv = 'koss01-oss01-mta01-app.int.oss.mykronos.com'
    send_from = 'Cloud-Notifications@kronos.net'
    smtpport = 25
    smtpserver = smtplib.SMTP(smtpsrv, smtpport)
    msg = MIMEMultipart()
    msg['Subject'] = email_subject
    msg['From'] = send_from
    msg['To'] = send_to
    msg.attach(MIMEText(html_data, 'html'))
    try:
        # smtpserver.starttls()
        # smtpserver.login(user, password)
        smtpserver.sendmail(send_from, [send_to], msg.as_string())
        smtpserver.close()
        logger.info("Mail sent to %s", send_to,)
    except Exception as e:
        logger.info('Something went wrong with sending the email...')
        logger.error(e)
    return ()



def main():
    script_folder = os.path.dirname(__file__)
    today_date = date.today().strftime('%Y%m%d')

    logger = script_log(script_folder, os.path.basename(__file__).split('.')[0], today_date)
    logger.setLevel(logging.INFO)
    f = open('/home/evgeniy.kravets/goanyware_rest/cred.txt', 'r')
    user = f.readline().strip()
    password = f.readline().strip()
    f.close()
    df = pd.read_csv('/home/evgeniy.kravets/goanyware_rest/mft.csv')
    df_obj = df.select_dtypes(['object'])
    df[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())
    for i in range(len(df)):
        ip = df.iloc[i]['server_ip']
        server_name = df.iloc[i]['server_hostname']
        ip, alert, status = get_mft_status(logger, ip, user, password)
        logger.info('For IP: %s, the status: %s', server_name, status)
        if alert >= 1:
            subject = str(' ').join(['MFT server', server_name])
            html_data = str('').join(['<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"> \
                        <title>MFT Status</title></head><body><table><tr><th>Server</th><th>Status</th></tr> \
                        <tr><td>', server_name, '</td><td>', status, '</td></tr></table></body></html>'])
            send_email(logger, html_data, send_to='evgeniy.kravets@ukg.com', email_subject=subject)

if __name__ == "__main__":
    main()
