# -*- coding: utf-8 -*-
import requests
import bs4
import xml.etree.ElementTree as ET
import watson.db_factory as db
from bs4 import BeautifulSoup
import xmltodict
import datetime

# "3006"	"국고채권(1년)"	        "1"
# "3000"	"국고채권(3년)"	        "2"
# "3007"	"국고채권(5년)"	        "3"
# "3013"	"국고채권(10년)"	    "4"
# "3014"	"국고채권(20년)"	    "5"
# "3017"	"국고채권(30년)"	    "6"
# "3018"	"국고채권(50년)"	    "7"
# "3008"	"국민주택1종(5년)"	    "8"
# "3015"	"통안증권(91일)"	    "9"
# "3016"	"통안증권(1년)"	        "10"
# "3003"	"통안증권(2년)"	        "11"
# "3002"	"한전채(3년)"	        "12"
# "3004"	"산금채(1년)"	        "13"
# "3009"	"회사채(무보증3년)AA-"	"14"
# "3010"	"회사채(무보증3년)BBB-"	"15"
# "4000"	"CD(91일)"	            "16"
# "5000"	"CP(91일)"	            "17"

def getConfig():
    import configparser
    global path, filename, yyyymmdd, django_path, main_path
    config = configparser.ConfigParser()
    config.read('config.ini')
    path = config['COMMON']['REPORT_PATH']
    proj_path = config['COMMON']['PROJECT_PATH']
    django_path = proj_path + r'\MainBoard'
    main_path = django_path + r'\MainBoard'
    filename = r'\financeData_%s_%s_%s.%s'

def get_beautiful_soup(url, headers, xml):
 return bs4.BeautifulSoup(requests.post(url, data=xml, headers=headers).text, "html5lib")


def get_date(url):
    return bs4.BeautifulSoup(requests.get(url).text, "html5lib")

def get_list_day():
    import sys
    import os
    import django
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    url = 'http://www.kofiabond.or.kr/proframeWeb/XMLSERVICES/'

    url_date = 'http://www.kofiabond.or.kr/websquare//serverTime.wq?pattern=yyyyMMdd'

    server_date = ET.fromstring(str(get_date(url_date)))
    target_date = server_date[1].text
    xml = """<?xml version='1.0' encoding='utf-8'?>
    <message>
      <proframeHeader>
        <pfmAppName>BIS-KOFIABOND</pfmAppName>
        <pfmSvcName>BISLastAskPrcROPSrchSO</pfmSvcName>
        <pfmFnName>listDay</pfmFnName>
      </proframeHeader>
      <systemHeader></systemHeader>
    <BISComDspDatDTO><val1>"""
    xml = xml + target_date
    # xml = xml + '20190703'
    xml = xml + """</val1></BISComDspDatDTO></message>"""
    headers = {'Content-Type': 'application/xml'}
    print("Making request Done...")
    soup = get_beautiful_soup(url, headers, xml)
    print("Request sent OKAY...")
    dbio_total_count = soup.find_all('dbio_total_count_')
    while int(dbio_total_count[0].text) < 1:
        yesterday = datetime.datetime.strptime(target_date, "%Y%m%d") - datetime.timedelta(days=1)
        print(yesterday.strftime("%Y%m%d"))
        xml = xml.replace(target_date, yesterday.strftime("%Y%m%d"))
        target_date = yesterday.strftime("%Y%m%d")
        print("Remake request for %s..." % target_date)
        soup = get_beautiful_soup(url, headers, xml)
        print("Request sent OKAY...")
        # print(soup)
        dbio_total_count = soup.find_all('dbio_total_count_')
    print("Response parsing Start...")
    try:
        obj = xmltodict.parse(str(soup))
        obj_structure = obj['html']['body']['root']['message']['biscomdspdatlistdto']['biscomdspdatdto']
    except Exception as e:
        print(e)
        print(str(soup))
    ins_info = db.getInstrumentInfo()
    mkt_info = db.getMarketInfo()
    val_info = {}
    val_info[target_date] = {}
    if "1130" not in mkt_info.keys():
        db.KofiaBondMarketStore("1130")
    if "1530" not in mkt_info.keys():
        db.KofiaBondMarketStore("1530")
    mkt_info = db.getMarketInfo()
    for o in obj_structure:
        # 15:30 전에 이 함수를 실행하면 val4 가 닫히지 않은 상태로 데이터가 와서 에러발생
        val20 = o['val13']['val14']['val15']['val16']['val17']['val18']['val19']['val20']
        # print(val20, type(val20))
        if val20 in ins_info.keys():
            pass
        else:
            ins_info[val20] = {'id': val20
                               , 'name': o['val1']
                               , 'new': True
                               }
        # print(target_date, val20, o['val3'], o['val4'])
        val_info[target_date][val20] = {"1130": o['val3'], "1530": o['val4']}
    print("Response parsing Done...")
    # print(val_info)
    for key in ins_info.keys():
        if ins_info[key]['new']:
            db.InstrumentResister(ins_info[key])
    ins_info = db.getInstrumentInfo()
    # print(ins_info)
    # print(mkt_info)
    # print(val_info)
    for ins_id in val_info[target_date].keys():
        print("Inserting %s information..." % ins_id)
        # print(ins_id, ins_info[ins_id]['id'])
        db.KofiaBondDataStore(datetime.datetime.strptime(target_date, "%Y%m%d")
                              , detective_db.Instrument.objects.get(id=ins_info[ins_id]['id'])
                              , detective_db.Market.objects.get(id=mkt_info['1130'])
                              , val_info[target_date][ins_id]['1130'])
        db.KofiaBondDataStore(datetime.datetime.strptime(target_date, "%Y%m%d")
                              , detective_db.Instrument.objects.get(id=ins_info[ins_id]['id'])
                              , detective_db.Market.objects.get(id=mkt_info['1530'])
                              , val_info[target_date][ins_id]['1530'])
    # print(val_info)

def get_list_term(start_date, end_date):
    import sys
    import os
    import django

    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    ins_info = db.getInstrumentInfo()
    mkt_info = db.getMarketInfo()
    url = 'http://www.kofiabond.or.kr/proframeWeb/XMLSERVICES/'

    # url_date = 'http://www.kofiabond.or.kr/websquare//serverTime.wq?pattern=yyyyMMdd'
    #
    # server_date = ET.fromstring(str(get_date(url_date)))
    # # server_date = ET.fromstring('20190401')
    # print('_' + server_date[1].text + '_')
    ext_id_1 = 3006  # "국고채권(1년)"	        "1"
    ext_id_2 = 3000  # "국고채권(3년)"	        "2"
    ext_id_3 = 3013  # "국고채권(10년)"	        "4"
    ext_id_4 = 3009  # "회사채(무보증3년)AA-"	"14"
    ext_id_5 = 3010  # "회사채(무보증3년)BBB-"	"15"
    ext_id_6 = 4000  # "CD(91일)"	            "16"
    xml = """<?xml version="1.0" encoding="utf-8"?>
    <message>
      <proframeHeader>
        <pfmAppName>BIS-KOFIABOND</pfmAppName>
        <pfmSvcName>BISLastAskPrcROPSrchSO</pfmSvcName>
        <pfmFnName>listTrm</pfmFnName>
      </proframeHeader>
      <systemHeader></systemHeader>
    <BISComDspDatDTO><val1>DD</val1><val2>{}</val2><val3>{}</val3><val4>1530</val4><val5>{}</val5><val6>{}</val6><val7>{}</val7><val8>{}</val8><val9>{}</val9><val10>{}</val10></BISComDspDatDTO></message>""".format(start_date, end_date, ext_id_1, ext_id_2, ext_id_3, ext_id_4, ext_id_5, ext_id_6)
    # print(xml)
    headers = {'Content-Type': 'application/xml'}
    print("Making request Done...")
    soup = get_beautiful_soup(url, headers, xml)
    print("Request sent OKAY...")
    # title = soup.find_all('biscomdspdatdto')
    # print(str(soup))
    ins_order = xmltodict.parse(xml)
    req_info = [ins_order['message']['BISComDspDatDTO'][o] for o in ins_order['message']['BISComDspDatDTO']]
    market = req_info[3]
    ins_order_structure = req_info[4:]
    # print(market)
    # print(ins_order_structure)
    obj = xmltodict.parse(str(soup))
    obj_structure = obj['html']['body']['root']['message']['biscomdspdatlistdto']['biscomdspdatdto'][2:]
    # print(obj_structure)
    ins_dict = {}
    print("Response parsing Start...")
    for obj in obj_structure:
        idx = 1
        for ins in ins_order_structure:
            if ins not in ins_dict.keys():
                ins_dict[ins] = {}
            else:
                ins_dict[ins][obj['val1']] = obj['val{}'.format(idx+1)]
            idx += 1
            if idx > 6:
                break
    print("Response parsing Done...")
    for ins_id in ins_dict.keys():
        print("Inserting %s information..." % ins_id)
        for date in ins_dict[ins_id].keys():
            db.KofiaBondDataStore(datetime.datetime.strptime(date.replace('-',''), "%Y%m%d")
                                  , detective_db.Instrument.objects.get(external_id=ins_id)
                                  , detective_db.Market.objects.get(name=market)
                                  , ins_dict[ins_id][date])
            # print(ins_id, market, date, ins_dict[ins_id][date])


if __name__ == '__main__':
    start_date = '20150101'
    end_date = '20190612'
    # get_list_term(start_date, end_date)
    get_list_day()
