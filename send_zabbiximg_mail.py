#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import time
import shutil
import MySQLdb
import smtplib
import requests
import datetime
 
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
from email.MIMEMultipart import MIMEMultipart
 
sendmai_dict={'ads-sdk':['收件人'],'playable':['收件人']} 
# based on zabbix 2.4.4
ZABBIX_HOST = 'zabbix地址'
ZABBIX_USER = 'zabbix账号'
ZABBIX_PWD = 'zabbix密码'
 
ZABBIX_DB_HOST = 'zabbix数据库地址'
ZABBIX_DB_USER = 'zabbix数据库账号'
ZABBIX_DB_PWD = 'zabbix数据库密码'
ZABBIX_DB_NAME = 'zabbix数据库名'
 
GRAPH_PATH = '/data/check_resouce/'
GRAPH_PERIOD = 604800  # seven day
 
EMAIL_USERNAME = '邮件地址'
EMAIL_PASSWORD = '邮件密码'

t = time.localtime(time.time() - 604800)
befor_week = time.strftime("%Y%m%d%H%M%S", t)

title_befor_week = time.strftime("%Y%m%d", t)
now_date = time.strftime("%Y%m%d", time.localtime()) 

def query_screens(screen_name):
    conn = MySQLdb.connect(host=ZABBIX_DB_HOST, user=ZABBIX_DB_USER, passwd=ZABBIX_DB_PWD,
                           db=ZABBIX_DB_NAME, charset='utf8', connect_timeout=20)
    cur = conn.cursor()
    count = cur.execute("""
            select a.name, a.screenid, b.resourceid, b.width, b.height
                from screens a, screens_items as b
                where a.screenid=b.screenid and a.templateid<=>NULL and a.name='%s'
                order by a.screenid;
            """ % screen_name)
    if count == 0:
        result = 0
    else:
        result = cur.fetchall()
 
    cur.close()
    conn.close()
 
    return result
 
 
def generate_graphs(screens):
    login_resp = requests.post('http://%s/index.php' % ZABBIX_HOST, data={
        'name': ZABBIX_USER,
        'password': ZABBIX_PWD,
        'enter': 'Sign in',
        'autologin': 1,
    })
    session_id = login_resp.cookies['zbx_sessionid']
 
    graphs = []
    for i, (screen_name, screen_id, graph_id, width, height) in enumerate(screens):
        params = {
            'screenid': screen_id,
            'graphid': graph_id,
            'width': width * 2,
            'height': height * 2,
            'period': GRAPH_PERIOD,
            'stime': befor_week,
        }
        resp = requests.get('http://%s/chart2.php' % ZABBIX_HOST, params=params,
                            cookies={'zbx_sessionid': session_id})
        file_name = '_'.join(map(str, screens[i][:3])).replace(' ', '_') + '.png'
        with open(os.path.join(GRAPH_PATH, file_name), 'wb') as fp:
            fp.write(resp.content)
        graphs.append(file_name)
 
    return graphs
 
 
def send_mail(screen_name, graphs, to_list):
    me =  EMAIL_USERNAME
 
    def _create_msg():
        msg = MIMEMultipart('related')
        msg['Subject'] = '%s %s----->%s resource Reports' %(screen_name,title_befor_week,now_date)
        msg['From'] = me
        msg['To'] = ';'.join(to_list)
        msg.preamble = 'This is a multi-part message in MIME format.'
 
        contents = "" 
        contents += "<table>"
        for g_name in graphs:
            with open(os.path.join(GRAPH_PATH, g_name), 'rb') as fp:
                msg_image = MIMEImage(fp.read())
                msg_image.add_header('Content-ID', "<%s>" % g_name)
                msg.attach(msg_image)
 
            contents += ''
            contents += "<tr><td><img src='cid:%s'></td></tr>" % g_name
        contents += "</table>"
 
        msg_text = MIMEText(contents, 'html')
        msg_alternative = MIMEMultipart('alternative')
        msg_alternative.attach(msg_text)
        msg.attach(msg_alternative)
 
        return msg
 
    try:
        server = smtplib.SMTP('smtp.gmail.com:587')
	server.starttls()
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.sendmail(me, to_list, _create_msg().as_string())
        server.close()
    except Exception, e:
        print e
 
 
if __name__ == '__main__':
    # remove old dirs
    if os.path.exists(GRAPH_PATH):
        shutil.rmtree(GRAPH_PATH)
    os.makedirs(GRAPH_PATH)
 
    for srn_name in sendmai_dict.keys():
        # get screens
        all_screens = query_screens(srn_name)
        # generate graphs
        graphs = generate_graphs(all_screens)
        send_mail(srn_name, graphs, sendmai_dict[srn_name])
