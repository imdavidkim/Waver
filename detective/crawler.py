# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import requests
from io import BytesIO
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import csv


def getStockInfo():
    gen_otp_url = "http://marketdata.krx.co.kr/contents/COM/GenerateOTP.jspx"
    gen_otp_data = {
        'name': 'fileDown',
        'filetype': 'csv',
        'url': 'MKD/04/0406/04060100/mkd04060100_01',
        'market_gubun': 'ALL',
        'isu_cdnm': '전체',
        'isu_cd': '',
        'isu_nm': '',
        'isu_srt_cd': '',
        'sort_type': 'A',
        'std_ind_cd': '01',
        'par_pr': '',
        'cpta_scl': '',
        'sttl_trm': '',
        'lst_stk_vl': '1',
        'in_lst_stk_vl': '',
        'in_lst_stk_vl2': '',
        'cpt': '1',
        'in_cpt': '',
        'in_cpt2': '',
        'isu_cdnm': '전체',
        'isu_cd': '',
        'mktpartc_no': '',
        'isu_srt_cd': '',
        'pagePath': '/contents/MKD/04/0406/04060100/MKD04060100.jsp',
    }
    code = httpRequest(gen_otp_url, gen_otp_data)
    # r = requests.post(gen_otp_url, gen_otp_data)
    # code = r.content

    down_url = 'http://file.krx.co.kr/download.jspx'
    down_data = {
        'code': code,
    }

    # r = requests.post(down_url, down_data)
    response = httpRequest(down_url, down_data)
    dic = dataCleansing(response)
    dataStore(dic)
    # df = pd.read_csv(BytesIO(r.content), header=0, thousands=',')
    # print(df)


def dataCleansing(content):
    import re
    retDict = {}
    tmpList = []
    temp = content.decode('utf-8')
    for idx, strLine in enumerate(temp.split('\n')):
        if idx == 0:
            continue

        cStr = csv.reader([strLine.replace('&nbsp', '')], quotechar='"', delimiter=',' \
                               , quoting=csv.QUOTE_ALL, skipinitialspace=True)
        dataArray = []
        for s in cStr:
            dataArray.extend(s)
        # dataArray.remove(',')
        # dataArray.remove('')
        # print(dataArray)
        try:
            if int(dataArray[0]) > 0:
                tmpList.append(dataArray)
            else:
                # tmpArr = strLine.split(',')
                try:
                    # print("*" * 2 + str(tmpList[-1]))
                    if int(dataArray[-1]) > 0:
                        tmpList[-1][-1] += ' '.join(dataArray[:-1])
                        tmpList[-1].append(dataArray[-1])
                except ValueError:
                    # print("*" * 4 + str(tmpList[-1]))
                    tmpList[-1][-1] += ' '.join(dataArray)
        except ValueError:
            try:
                # print("*" * 6 + str(tmpList[-1]))
                if int(dataArray[-1]) > 0:
                    tmpList[-1][-1] += ' '.join(dataArray[:-1])
                    tmpList[-1].append(dataArray[-1])
            except ValueError:
                # print("*" * 8 + str(tmpList[-1]))
                tmpList[-1][-1] += ' '.join(dataArray)
            # print(tmpList[-1])
            # print("* " * 10 + strLine)
    for da in tmpList:
        retDict[da[1]] = {
            '종목명': da[2],
            '업종코드': da[3],
            '업종명': da[4],
            '상장주식수': da[5],
            '자본금': da[6],
            '액면가': da[7],
            '전화번호': da[9],
            '주소': da[10]
        }

    return retDict


def dataStore(retDict):
    import sys
    import os
    import django
    sys.path.append(r'E:\Github\\Waver\MainBoard')
    sys.path.append(r'E:\Github\\Waver\MainBoard\MainBoard')
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    try:
        for key in retDict.keys():
            info = detective_db.Stocks.objects.update_or_create(code=key,
                                                                defaults={
                                                                    'name': retDict[key]['종목명'],
                                                                    'category_code': retDict[key]['업종코드'],
                                                                    'category_name': retDict[key]['업종명'],
                                                                    'issued_shares': float(
                                                                        retDict[key]['상장주식수'].replace(',', '')),
                                                                    'capital': float(
                                                                        retDict[key]['자본금'].replace(',', '')),
                                                                    'par_value': float(
                                                                        retDict[key]['액면가'].replace(',', '')),
                                                                    'tel': retDict[key]['전화번호'].replace(' ', ''),
                                                                    'address': retDict[key]['주소']
                                                                }
                                                                )
            # 기존에 했다가 에러난 코드
            # info = detective_db.Stocks.objects.update_or_create(code=key,
            #                                                     name=retDict[key]['종목명'],
            #                                                     category_code=retDict[key]['업종코드'],
            #                                                     category_name=retDict[key]['업종명'],
            #                                                     issued_shares=float(
            #                                                               retDict[key]['상장주식수'].replace(',', '')),
            #                                                     capital=float(retDict[key]['자본금'].replace(',', '')),
            #                                                     par_value=float(retDict[key]['액면가'].replace(',', '')),
            #                                                     tel=retDict[key]['전화번호'],
            #                                                     address=retDict[key]['주소'])
            # info.save()
            print("[%s][%s] Successfully saved!!" % (key, retDict[key]['종목명']))
    except:
        print(key, retDict[key])


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
    getStockInfo()