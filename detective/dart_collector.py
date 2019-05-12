# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import requests
from io import BytesIO
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import csv
import xmltodict
from detective.settings import config


def getDartInfo():
    dartSearchDict = {
        'auth': config.dart.search_key,
        'crp_cd': '',
        'end_dt': '20180113',
        'start_dt': '20180101',
        'fin_rpt': '',
        'dsp_tp': '',
        'bsn_tp': '',
        'sort': '',
        'series': 'desc',
        'page_no': '',
        'page_set': 100,
    }

    response = httpRequest(config.dart.search_url, dartSearchDict)
    result = xmltodict.parse(response.decode('utf-8'))
    IndexDataStore(result['result'])
    if result['result']['err_code'] == '000':
        ResultDataStore(result['result']['list'])
        if int(result['result']['total_page']) > 1:
            for page in range(int(result['result']['page_no']) + 1, int(result['result']['total_page']) + 1):
                dartSearchDict['page_no'] = page
                response = httpRequest(config.dart.search_url, dartSearchDict)
                result = xmltodict.parse(response.decode('utf-8'))
                IndexDataStore(result['result'])
                if result['result']['err_code'] == '000':
                    ResultDataStore(result['result']['list'])
    else:
        pass

    print(result['result']['total_page'], result['result']
    ['total_count'], result['result']['page_no'])


def IndexDataStore(retDict):
    import os
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    try:
        info = detective_db.DartRequestIndex.objects.update_or_create(err_code=retDict['err_code'],
                                                                      err_msg=retDict['err_msg'],
                                                                      page_no=int(
                                                                          retDict['page_no']),
                                                                      total_page=int(
                                                                          retDict['total_page']),
                                                                      total_count=int(
                                                                          retDict['total_count']),
                                                                      req_time=datetime.now(),
                                                                      )
        print("%s / %s request stored successfully" %
              (retDict['page_no'], retDict['total_page']))
    except Exception as e:
        print('[Error on IndexDataStore]\n', '*' * 50, e)


def ResultDataStore(retDict):
    import sys
    import os
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    try:
        for dicData in retDict:
            info = detective_db.DartRequestResult.objects.update_or_create(rcp_no=dicData['rcp_no'],
                                                                           defaults={
                                                                               'crp_cls': dicData['crp_cls'],
                                                                               'crp_nm': dicData['crp_nm'],
                                                                               'crp_cd': dicData['crp_cd'],
                                                                               'rpt_nm': dicData['rpt_nm'],
                                                                               'flr_nm': dicData['flr_nm'],
                                                                               'rcp_dt': dicData['rcp_dt'],
                                                                               'rmk': dicData['rmk'],
                                                                           }
                                                                           )
            print("[%s][%s][%s] information stored successfully" %
                  (dicData['rcp_no'], dicData['crp_nm'], dicData['rpt_nm']))
    except Exception as e:
        print('[Error on ResultDataStore]\n', '*' * 50, e)


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
    getDartInfo()
