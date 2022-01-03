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
import watson.db_factory as db
sys.path.append(r'C:\ProgramData\Anaconda3\envs\Waver\DLLs')

def getConfig():
    import configparser
    global path, django_path, main_path, dart_auth_key
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
    path = config['COMMON']['PROJECT_PATH']
    django_path = path + r'\MainBoard'
    main_path = django_path + r'\MainBoard'
    dart_auth_key = config['DART']['SEARCH-API-KEY']


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
    print(response)
    dic = dataCleansing(response)
    db.dataInit()
    db.dataStore(dic)
    # df = pd.read_csv(BytesIO(r.content), header=0, thousands=',')
    # print(df)


def getStockInfoNew():
    import json
    getConfig()
    print("[Crawler] Requesting Stock Information...")
    down_url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
    down_data = {
        'bld': 'dbms/MDC/STAT/standard/MDCSTAT03402',
        'mktTpCd': '0',
        'tboxisuSrtCd_finder_listisu0_0': '전체',
        'isuSrtCd': 'ALL',
        'isuSrtCd2': 'ALL',
        'codeNmisuSrtCd_finder_listisu0_0': '',
        'param1isuSrtCd_finder_listisu0_0': '',
        'sortType': 'A',
        'stdIndCd': 'ALL',
        'sectTpCd': 'ALL',
        'parval': 'ALL',
        'mktcap': 'ALL',
        'acntclsMm': 'ALL',
        'tboxmktpartcNo_finder_designadvser0_0': '',
        'mktpartcNo': '',
        'mktpartcNo2': '',
        'codeNmmktpartcNo_finder_designadvser0_0': '',
        'param1mktpartcNo_finder_designadvser0_0': '',
        'condListShrs': '1',
        'listshrs': '',
        'listshrs2': '',
        'condCap': '1',
        'cap': '',
        'cap2': '',
        'share': '1',
        'money': '1',
        'csvxls_isNo': 'false',
    }
    down_header = {'User-Agent': 'User-Agent: Mozilla/5.0'
                   , 'Accept': 'gzip, deflate'
                   , 'Referer': 'http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020201'
                   , 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
                   }

    response = httpRequest(down_url, down_data, down_header)
    # print(response.decode('utf-8'))
    retDict = {}
    tmpList = json.loads(response.decode('utf-8'))["block1"]
    dart_info = get_corpcode(dart_auth_key)
    for da in tmpList:
        if da["REP_ISU_SRT_CD"] not in dart_info.keys():
            continue
        retDict[da["REP_ISU_SRT_CD"]] = {
            '종목명': da["COM_ABBRV"],
            '업종코드': da["STD_IND_CD"],
            '업종명': da["IND_NM"],
            '상장주식수': da["LIST_SHRS"],
            '자본금': da["CAP"],
            '액면가': da["PARVAL"],
            '통화': da["ISO_CD"][da["ISO_CD"].find('(') + 1:da["ISO_CD"].find(')')],
            '전화번호': da["TEL_NO"],
            '주소': da["ADDR"],
            'DART코드': dart_info[da["REP_ISU_SRT_CD"]]
        }
    db.dataInit()
    db.dataStore(retDict)

def getSnP500StockInfo():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    response = httpRequest(url)
    dic = wikiDataCleansing(response)
    db.USDataInit()
    db.USDataStore(dic)


def getNasdaq100StockInfo():
    url = 'https://en.wikipedia.org/wiki/NASDAQ-100'
    response = httpRequest(url)
    dic = wikiDataCleansing2(response)
    db.USNasdaqDataInit()
    db.USNasdaqDataStore(dic)


def getNasdaqStockInfo():
    import string
    alphabets = string.ascii_uppercase
    targets = {}
    for code in alphabets:
        #NASDAQ
        url = 'http://eoddata.com/stocklist/NASDAQ/{}.htm'.format(code)
        print("Processing USStocks(NASDAQ) information starts with {} => {}".format(code, url))
        response = httpRequest(url)
        targets = stocklistCleansing(targets, response)
    for code in alphabets:
        # NYSE
        url = 'http://eoddata.com/stocklist/NYSE/{}.htm'.format(code)
        print("Processing USStocks(NYSE) information starts with {} => {}".format(code, url))
        response = httpRequest(url)
        targets = stocklistCleansing(targets, response)
    url = 'https://stockanalysis.com/stocks'
    res = requests.get(url=url)
    soup = BeautifulSoup(res.content.decode(encoding='utf-8'), 'lxml')
    targets = stocklistCleansing2(targets, str(soup.find(id="__NEXT_DATA__").contents[0]))

    db.USNasdaqDataInit()
    db.USNasdaqDataStore(targets)


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


def stocklistCleansing(targets, content):
    import detective.fnguide_collector as fnguide
    import json
    stocks = targets
    if isinstance(content, bytes):
        soup = BeautifulSoup(content, 'lxml')

        usstocks = fnguide.select_by_attr(soup, 'div', 'id', 'ctl00_cph1_divSymbols')  # Snapshot FinancialHighlight
        dd = usstocks.find_all('tr')
        for idx, d in enumerate(dd):
            if idx == 0:
                # hh = d.find_all('th')
                # print(idx, len(hh), hh)
                # for h in hh:
                #     print(h.text)
                pass
            else:
                ss = d.find_all('td')
                # [code, name, high, low, close, volume, change, direction, pct, down]
                if ss[0].text in ['ERI', 'ENT']: continue
                if "-" in ss[0].text or "." in ss[0].text: continue
                if 'ETF' in ss[1].text \
                    or 'Ishares' in ss[1].text \
                    or 'Proshares' in ss[1].text \
                    or 'Global X' in ss[1].text \
                    or 'G-X' in ss[1].text \
                    or 'Nasdaq' in ss[1].text \
                    or 'Victoryshares' in ss[1].text \
                    or 'Vanguard' in ss[1].text \
                    or 'Warrents' in ss[1].text \
                    or 'Bulletshares' in ss[1].text \
                    or 'Advisorshares' in ss[1].text \
                    or 'Dividend' in ss[1].text \
                    or ' WT' in ss[1].text \
                    or ' Index' in ss[1].text \
                    or ' Fund' in ss[1].text \
                    or 'Yield' in ss[1].text \
                    or ' Bond' in ss[1].text: continue
                stocks[ss[0].text] = {'Ticker': ss[0].text
                                      , 'Security': ss[1].text
                                      , 'TickerLink': "http://www.nasdaq.com/symbol/{}".format(ss[0].text.lower())
                                      , 'SecurityLink': None}
    elif isinstance(content, dict):
        usstocks = json.loads(content)
        for ss in usstocks['pageProps']['stocks']:
            stocks[ss['s']] = {'Ticker': ss['s']
                               , 'Security': ss['n']
                               , 'TickerLink': "http://www.nasdaq.com/symbol/{}".format(ss['s'].lower())
                               , 'SecurityLink': None}
    return stocks


def stocklistCleansing2(targets, content):
    import json
    stocks = targets
    usstocks = json.loads(content)
    for ss in usstocks['props']['pageProps']['stocks']:
        stocks[ss['s']] = {'Ticker': ss['s']
                           , 'Security': ss['n']
                           , 'TickerLink': "http://www.nasdaq.com/symbol/{}".format(ss['s'].lower())
                           , 'SecurityLink': None}
    return stocks

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
    getConfig()
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
    dart_info = get_corpcode(dart_auth_key)
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
            '주소': da[10],
            'DART코드': dart_info[da[1]]
        }

    return retDict


def get_corpcode(crtfc_key):
    import io
    import zipfile
    import xml.etree.ElementTree as et
    print("Gathering DART CorporationCode...")
    params = {'crtfc_key': crtfc_key}
    url = "https://opendart.fss.or.kr/api/corpCode.xml"
    res = requests.get(url, params=params)
    zfile = zipfile.ZipFile(io.BytesIO(res.content))
    fin = zfile.open(zfile.namelist()[0])
    # print(fin.read().decode('utf-8'))
    root = et.fromstring(fin.read().decode('utf-8'))
    data = {}
    for child in root:
        if len(child.find('stock_code').text.strip()) > 1: # 종목코드가 있는 경우
            data[child.find('stock_code').text.strip()] = child.find('corp_code').text.strip()
    print("{} CorpCode returned".format(len(data)))
    return data


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
    # getNasdaq100StockInfo()
    getNasdaqStockInfo()
    # getStockInfoNew()
