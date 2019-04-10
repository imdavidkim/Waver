# -*- coding: utf-8 -*-
import requests
import bs4
import xml.etree.ElementTree as ET


def get_beautiful_soup(url):
 return bs4.BeautifulSoup(requests.post(url, data=xml, headers=headers).text, "html5lib")


def get_date(url):
    return bs4.BeautifulSoup(requests.get(url).text, "html5lib")


url = 'http://www.kofiabond.or.kr/proframeWeb/XMLSERVICES/'

url_date = 'http://www.kofiabond.or.kr/websquare//serverTime.wq?pattern=yyyyMMdd'

server_date = ET.fromstring(str(get_date(url_date)))
# server_date = ET.fromstring('20190401')
print('_' + server_date[1].text + '_')

xml = """<?xml version='1.0' encoding='utf-8'?>
<message>
  <proframeHeader>
    <pfmAppName>BIS-KOFIABOND</pfmAppName>
    <pfmSvcName>BISLastAskPrcROPSrchSO</pfmSvcName>
    <pfmFnName>listDay</pfmFnName>
  </proframeHeader>
  <systemHeader></systemHeader>
<BISComDspDatDTO><val1>"""
# xml = xml + server_date[1].text
xml = xml + '20190401'
xml = xml + """</val1></BISComDspDatDTO></message>"""
headers = {'Content-Type': 'application/xml'}

soup = get_beautiful_soup(url)
# title = soup.find_all('biscomdspdatdto')
# print(str(soup))
root = ET.fromstring(str(soup))
# print(root[1][0][0][2][4])
print(root[0].tag, root[0].attrib)
idx = 0
for itm in root[1][0][0][2]:
    idx1 = 0
    if idx == 5 or idx == 7 or idx == 17 or idx == 18:
        for itm1 in itm:
            if idx1 == 0 or idx1 == 2 or idx1 == 3:
                print(itm1.text.replace(' ',''))
            idx1 = idx1 + 1
    idx = idx + 1
