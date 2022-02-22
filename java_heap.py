#!/bin/python
from datetime import date
import requests, json, os, logging, datetime
from requests.auth import HTTPBasicAuth
import pandas as pd


def get_java_heap(logger, ip, user, password):
    """
    Use REST API to get Heap Memory Used, GET http://[server URL]:[port]/goanywhere/rest/gacmd/v1/system/status
    Return 3 str: heapMemoryUsed, nonHeapMemoryUsed, heapMemoryMaximum
    :param ip: str, IP addres of server
    :param user: str, username to authenticate
    :param password: str, passwort for authentication
    :return: heapMemoryUsed, nonHeapMemoryUsed, heapMemoryMaximum
    """
    url = str('').join(['http://', ip, ':8000/goanywhere/rest/gacmd/v1/system/status'])
    respond = requests.get(url, auth=HTTPBasicAuth(user, password))
    respond = json.loads(respond.text)
    heapMemoryUsed = respond["data"]["heapMemoryUsed"]
    heapMemoryCommitted = respond["data"]["heapMemoryCommitted"]
    heapMemoryMaximum = respond["data"]["heapMemoryMaximum"]
    return heapMemoryUsed, heapMemoryCommitted, heapMemoryMaximum


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
        heapMemoryUsed, heapMemoryCommitted, heapMemoryMaximum = get_java_heap(logger, ip, user, password)
        logger.debug('%s %s %s %s', df.iloc[i]['server_hostname'], heapMemoryMaximum, heapMemoryUsed,
                    heapMemoryCommitted)
        try:
            cmd_bq = str('').join(['echo \'{"date": "', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), \
                               '" , "heapMemoryMaximum": ', str(heapMemoryMaximum), \
                               ', "heapMemoryCommitted": ', str(heapMemoryCommitted), \
                               ', "heapMemoryUsed": ', str(heapMemoryUsed), \
                               ', "Server_Hostname": "', str(df.iloc[i]["server_hostname"]), \
                               '"}\' | bq insert ftp.java_heap'])
        except Exception as e:
            logger.info(e)
            logger.info("Execute command: %s", cmd_bq, )
        os.system(cmd_bq)


if __name__ == "__main__":
    main()
