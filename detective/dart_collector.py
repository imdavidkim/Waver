# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import requests
from io import BytesIO
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import csv
import xmltodict
import json
import OpenDartReader


def getConfig():
    import configparser
    global path, django_path, main_path, search_api_key, company_api_key, search_url, company_url, dart
    config = configparser.ConfigParser()
    config.read('config.ini')
    path = config['COMMON']['REPORT_PATH']
    proj_path = config['COMMON']['PROJECT_PATH']
    django_path = proj_path + r'\MainBoard'
    main_path = django_path + r'\MainBoard'
    search_api_key = config['DART']['SEARCH-API-KEY']
    company_api_key = config['DART']['COMPANY-API-KEY']
    search_url = config['DART']['SEARCH-URL']
    company_url = config['DART']['COMPANY-URL']
    dart = OpenDartReader(search_api_key)


# def getDartInfo():
#     getConfig()
#
#     dartSearchDict = {
#         'auth': search_api_key,
#         'crp_cd': '',
#         'end_dt': '20180113',
#         'start_dt': '20180101',
#         'fin_rpt': '',
#         'dsp_tp': '',
#         'bsn_tp': '',
#         'sort': '',
#         'series': 'desc',
#         'page_no': '',
#         'page_set': 100,
#     }
#
#     response = httpRequest(search_url, dartSearchDict)
#     result = xmltodict.parse(response.decode('utf-8'))
#     IndexDataStore(result['result'])
#     if result['result']['err_code'] == '000':
#         ResultDataStore(result['result']['list'])
#         if int(result['result']['total_page']) > 1:
#             for page in range(int(result['result']['page_no'])+1, int(result['result']['total_page'])+1):
#                 dartSearchDict['page_no'] = page
#                 response = httpRequest(search_url, dartSearchDict)
#                 result = xmltodict.parse(response.decode('utf-8'))
#                 IndexDataStore(result['result'])
#                 if result['result']['err_code'] == '000':
#                     ResultDataStore(result['result']['list'])
#     else:
#         pass
#
#     print(result['result']['total_page'], result['result']['total_count'], result['result']['page_no'])


def IndexDataStore(retDict):
    import sys
    import os
    import django
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    try:
        info = detective_db.DartRequestIndex.objects.update_or_create(err_code=retDict['err_code'],
                                                                      err_msg=retDict['err_msg'],
                                                                      page_no=int(retDict['page_no']),
                                                                      total_page=int(retDict['total_page']),
                                                                      total_count=int(retDict['total_count']),
                                                                      req_time=datetime.now(),
                                                                      )
        print("%s / %s request stored successfully" % (retDict['page_no'], retDict['total_page']))
    except Exception as e:
        print('[Error on IndexDataStore]\n', '*'*50, e)





def httpRequest(url, data, method='POST'):
    try:
        if method == 'POST':
            r = requests.post(url, data)
            return r.content
        else:
            r = requests.get(url, data)
            return r.content
    except:
        return None


if __name__ == '__main__':
    getConfig()
    import watson.db_factory as db
    # result = dart.list(start='20201101', kind='A') # 정기공시
    # result = dart.list(start='20201101', kind='D') # 지분공시

    # print(result.to_json(orient="table"))
    # db.ResultListDataStore(json.loads(result.to_json(orient="table")))


    date = "20201116"
    corp_code_list = db.getMajorShareholderReportingInfo(date)
    for corp_code in corp_code_list:
        result = dart.major_shareholders(corp_code)
        db.ResultMajorShareholderDataStore(json.loads(result.to_json(orient="table")))

