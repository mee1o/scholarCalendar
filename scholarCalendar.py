# -*- coding: utf-8 -*-
"""
Created on Sat Oct  3 11:41:25 2015

@author: hamin
"""

from lxml import etree
import requests

class Event(object):
    def __init__(self, title, href):
        self.title = title
        self.href = href

def parseList():
    url = 'http://gr.uestc.edu.cn/articleList.shtml?categoryID=112'
    rsp = requests.get(url)
    parser = etree.HTMLParser()
    doc = etree.fromstring(rsp.text, parser)
    items = doc.xpath('//div[@id="right"]/ul/li/a')
    return [(item.attrib['title'], item.attrib['href']) for item in items]


#url = 'http://gr.uestc.edu.cn/article.shtml?zxh=2015233'
def parseArticle(url):
    rsp = requests.get(url)
    parser = etree.HTMLParser()
    doc = etree.fromstring(rsp.text, parser)
    #开始时间 地点 主办 承办 范围 序号 报告题目 报告人 职称 报告人简介
    
    info1 = doc.xpath('//table[@class="grid1"]//tr/td[2]//text()')
    i = 2
    while True:
        info2 = doc.xpath('//table[@class="grid2"]//tr[{}]/td//text()'.format(i))
        if info2:
            yield info1 + info2
            i += 1
        else:
            break
        
import sqlite3
from datetime import datetime, timedelta
def saveToDB(info):
    conn = sqlite3.connect('xueshu.sqlite3')
    c = conn.cursor()
#    print(info[1],info[8])
    exist = c.execute('select url from xueshu where url=? and seq=?',(info[2],info[8]))
    if exist.fetchall():
        return 'Already exist.'
    info[3] = datetime.strptime(info[3], '%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO xueshu VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", tuple(info))
    conn.commit()
    conn.close()
    return 'Successfully saved to database'



from ics import Calendar, Event

l = parseList()
for item in l:
    info = [str(datetime.now())]
    info.extend(item)
    for row in parseArticle('http://gr.uestc.edu.cn/'+item[1]):
        row[-1] = row[-1].replace('\n','').replace('\r','')
#        print(len(info+row))
        print(saveToDB(info+row))
        
#from dateutil import tz
import arrow
def writeICS():
    conn = sqlite3.connect('xueshu.sqlite3', detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    now = datetime.now()
    future = now + timedelta(days=60)
    items = c.execute('select * from xueshu where startdate>=? and startdate<=?', (now.date(), future.date()))
    c = Calendar()
    c.creator = 'meelo'
    for item in items:
        e = Event()
        e.name = item[1].replace(' ','') + '【{}】'.format(item[10]) + item[9]
#        e.begin = arrow.get(item[3], 'YYYY-MM-DD HH:mm:ss').replace(tzinfo=tz.gettz('Asia/Chongqing'))
        e.begin = arrow.get(item[3], 'YYYY-MM-DD HH:mm:ss').replace(tzinfo='+08:00')
        e.duration = timedelta(hours=2)
        e.location = item[4]
        e.description = item[12]
        c.events.append(e)
#    print(c.events)
    conn.close()
    with open('xueshu.ics', 'w', encoding='utf-8') as f:
        f.writelines(c)
    
writeICS()