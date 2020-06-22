# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import requests
from io import BytesIO
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import csv
import sys
import time
sys.path.append(r'C:\ProgramData\Anaconda3\envs\Waver\DLLs')

def getConfig():
    import configparser
    global path, django_path, main_path
    config = configparser.ConfigParser()
    config.read('config.ini')
    path = config['COMMON']['PROJECT_PATH']
    django_path = path + r'\MainBoard'
    main_path = django_path + r'\MainBoard'


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
       'std_ind_cd': '',
       'par_pr': '',
       'cpta_scl': '',
       'sttl_trm': '',
       'lst_stk_vl': '1',
       'in_lst_stk_vl': '',
       'in_lst_stk_vl2': '',
       'cpt': '1',
       'in_cpt': '',
       'in_cpt2': '',
       'mktpartc_no': '',
       'pagePath': '/contents/MKD/04/0406/04060100/MKD04060100.jsp',
    }
    down_header = {'User-Agent': 'User-Agent: Mozilla/5.0'
                   , 'Accept-Encoding': 'gzip, deflate'
                   , 'Referer': 'http://marketdata.krx.co.kr/mdi'
                   , 'Content-Type': 'application/x-www-form-urlencoded'
                   }
    # code = httpRequest(gen_otp_url, gen_otp_data)
    code = httpRequest(gen_otp_url, gen_otp_data, down_header)
    fail_count = 0
    while True:
        if code is not b'':
            print("[Crawler] OTP Code generate success!!")
            break
        elif fail_count == 10:
            print("[Crawler] OTP Code generate Failed 10 times!!")
            break
        fail_count += 1
        time.sleep(5)
        print("[Crawler] Try again OTP Code generation. {}".format(fail_count))
        code = httpRequest(gen_otp_url, gen_otp_data, down_header)
    print("[Crawler] Requesting Stock Information...")
    # print("code : ", code)
    # r = requests.post(gen_otp_url, gen_otp_data)
    # code = r.content

    down_url = 'http://file.krx.co.kr/download.jspx'
    down_data = {
        'code': code,
    }

    # r = requests.post(down_url, down_data)
    # down_header = {'User-Agent': 'User-Agent: Mozilla/5.0'
    #                , 'Accept-Encoding': 'gzip, deflate'
    #                , 'Referer': 'http://marketdata.krx.co.kr/mdi'
    #                , 'Content-Type': 'application/x-www-form-urlencoded'
    #                }
    response = httpRequest(down_url, down_data, down_header)
    # print(response)
    dic = dataCleansing(response)
    dataInit()
    dataStore(dic)
    # df = pd.read_csv(BytesIO(r.content), header=0, thousands=',')
    # print(df)


def getSnP500StockInfo():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    response = httpRequest(url)
    dic = wikiDataCleansing(response)
    USDataInit()
    USDataStore(dic)


def getNasdaq100StockInfo():
    url = 'https://en.wikipedia.org/wiki/NASDAQ-100'
    response = httpRequest(url)
    dic = wikiDataCleansing2(response)
    USNasdaqDataInit()
    USNasdaqDataStore(dic)


def getYieldCurveInfo():
    import detective.fnguide_collector as fnguide
    url = 'http://www.worldgovernmentbonds.com'
    response = httpRequest(url)
    # print(response.decode())

    soup = BeautifulSoup(response.decode(), 'lxml')
    # print(soup)
    for i in soup.select('thead tr th'):
        print(i)
    # print(soup.find_all('tbody'))
    # url = 'https://tradingeconomics.com/bonds'
    # ycinfo_nation = fnguide.select_by_attr(soup, 'div', 'class', 'table-responsive')
    # print(ycinfo_nation)


def wikiDataCleansing2(content):
    import detective.fnguide_collector as fnguide
    retDict = {}
    soup = BeautifulSoup(content, 'lxml')
    # print(soup)
    nasdaq100_companies = fnguide.select_by_attr(soup, 'table', 'id', 'constituents')  # Snapshot FinancialHighlight
    if nasdaq100_companies:
        header = fnguide.get_table_contents(nasdaq100_companies, 'tr th')
        datas = fnguide.get_table_contents(nasdaq100_companies, 'tr td')
        for i in range(0, len(datas)-1, len(header)):
            retDict[datas[i][:datas[i].find('(')].strip()] = {
                'Security': datas[i][:datas[i].find('(')].strip(),
                'SecurityLink': datas[i][datas[i].find('(')+1:datas[i].find(')')].strip(),
                'Ticker': datas[i+1].strip(),
                'TickerLink': 'http://www.nasdaq.com/symbol/{}'.format(datas[i+1].strip().lower())
            }
    return retDict


def wikiDataCleansing(content):
    import detective.fnguide_collector as fnguide
    retDict = {}
    soup = BeautifulSoup(content, 'lxml')
    snp500_companies = fnguide.select_by_attr(soup, 'table', 'class', 'wikitable sortable')  # Snapshot FinancialHighlight
    # print(snp500_companies)
    if snp500_companies:
        header = fnguide.get_table_contents(snp500_companies, 'tr th')
        datas = fnguide.get_table_contents(snp500_companies, 'tr td')
        for d in range(0, len(datas), 9):
            retDict[datas[d+7].strip()] = {
                'CIK': datas[d+7].strip(),
                'Ticker': datas[d][:datas[d].find('(')].strip(),
                'TickerLink': datas[d][datas[d].find('(')+1:datas[d].find(')')].strip(),
                'Security': datas[d+1][:datas[d+1].find('(')].strip(),
                'SecurityLink': datas[d+1][datas[d+1].find('(')+1:datas[d+1].find(')')].strip(),
                'CategoryName': datas[d+3].strip(),
                'CategoryDetail': datas[d+4].strip(),
                'SecurityFiling': datas[d+2][datas[d+2].find('(')+1:datas[d+2].find(')')].strip(),
                'Address': datas[d+5][:datas[d+5].find('(')].strip(),
                'AddressLink': datas[d+5][datas[d+5].find('(')+1:datas[d+5].find(')')].strip(),
                'DateFirstAdded': '' if datas[d+6].strip() == '' else datas[d+6].strip(),
                'Founded': datas[d+8].strip()}

    return retDict


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
            '통화': da[8][da[8].find('(')+1:da[8].find(')')],
            '전화번호': da[9],
            '주소': da[10]
        }

    return retDict


def dataInit():
    import sys
    import os
    import django
    # sys.path.append(r'E:\Github\\Waver\MainBoard')
    # sys.path.append(r'E:\Github\\Waver\MainBoard\MainBoard')
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    try:
        detective_db.Stocks.objects.update(listing='N')
    except Exception as e:
        print("Stock data initialization Failed with", e)


def USDataInit():
    import sys
    import os
    import django
    # sys.path.append(r'E:\Github\\Waver\MainBoard')
    # sys.path.append(r'E:\Github\\Waver\MainBoard\MainBoard')
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    try:
        detective_db.USStocks.objects.update(listing='N')
    except Exception as e:
        print("USStocks data initialization Failed with", e)


def USNasdaqDataInit():
    import sys
    import os
    import django
    # sys.path.append(r'E:\Github\\Waver\MainBoard')
    # sys.path.append(r'E:\Github\\Waver\MainBoard\MainBoard')
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    try:
        detective_db.USNasdaqStocks.objects.update(listing='N')
    except Exception as e:
        print("USNasdaqStocks data initialization Failed with", e)


def dataStore(retDict):
    import sys
    import os
    import django
    # sys.path.append(r'E:\Github\\Waver\MainBoard')
    # sys.path.append(r'E:\Github\\Waver\MainBoard\MainBoard')
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    try:
        count = 0
        print("Stock Information crawling started")
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
                                                                    'address': retDict[key]['주소'],
                                                                    'curr': retDict[key]['통화'],
                                                                    'listing': 'Y'
                                                                }
                                                                )
            count += 1
            if count % 100 == 0:
                print("%d Stock Information on processing..." % count)
        print("Total %d" % count)
    except Exception as e:
        print(count, key, retDict[key])
        print(e)


def USDataStore(retDict):
    import sys
    import os
    import django
    # sys.path.append(r'E:\Github\\Waver\MainBoard')
    # sys.path.append(r'E:\Github\\Waver\MainBoard\MainBoard')
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    try:
        count = 0
        print("USStock Information crawled data storing started!!")
        for key in retDict.keys():
            # print(retDict[key])
            info = detective_db.USStocks.objects.update_or_create(cik=retDict[key]['CIK'],
                                                                  defaults={
                                                                      'security': retDict[key]['Security'],
                                                                      'ticker': retDict[key]['Ticker'],
                                                                      'ticker_symbol_link': retDict[key]['TickerLink'],
                                                                      'security_wiki_link': retDict[key]['SecurityLink'],
                                                                      'category_name': retDict[key]['CategoryName'],
                                                                      'category_detail': retDict[key]['CategoryDetail'],
                                                                      'sec_filing': retDict[key]['SecurityFiling'],
                                                                      'location': retDict[key]['Address'],
                                                                      'location_link': retDict[key]['AddressLink'],
                                                                      'date_first_added': retDict[key]['DateFirstAdded'],
                                                                      'founded': retDict[key]['Founded'],
                                                                      'listing': 'Y'
                                                                }
                                                                )
            count += 1
            if count % 100 == 0:
                print("%d USStock Information on processing..." % count)
        print("Total %d" % count)
    except Exception as e:
        print(e, key, retDict[key])


def USNasdaqDataStore(retDict):
    import sys
    import os
    import django
    # sys.path.append(r'E:\Github\\Waver\MainBoard')
    # sys.path.append(r'E:\Github\\Waver\MainBoard\MainBoard')
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    try:
        count = 0
        print("USNasdaqStock Information crawled data storing started!!")
        for key in retDict.keys():
            # print(retDict[key])
            info = detective_db.USNasdaqStocks.objects.update_or_create(security=retDict[key]['Security'],
                                                                        defaults={
                                                                      'ticker': retDict[key]['Ticker'],
                                                                      'ticker_symbol_link': retDict[key]['TickerLink'],
                                                                      'security_wiki_link': retDict[key]['SecurityLink'],
                                                                      'listing': 'Y'
                                                                }
                                                                )
            count += 1
            if count % 100 == 0:
                print("%d USNasdaqStock Information on processing..." % count)
        print("Total %d" % count)
    except Exception as e:
        print(e, key, retDict[key])


def httpRequest(url, data=None, header=None, method='POST'):
    try:
        if method == 'POST':
            if data is None:
                r = requests.post(url)
            elif header is not None:
                session = requests.session()
                session.headers.update(header)
                r = session.post(url, data)
            else:
                r = requests.post(url, data)
            return r.content
        else:
            if data is None:
                r = requests.get(url)
            elif header is not None:
                session = requests.session()
                session.headers.update(header)
                r = session.get(url, data)
            else:
                r = requests.get(url, data)
            return r.content
    except:
        return None

if __name__ == '__main__':
    # getStockInfo()
    # getSnP500StockInfo()
    # getYieldCurveInfo()
    getNasdaq100StockInfo()

