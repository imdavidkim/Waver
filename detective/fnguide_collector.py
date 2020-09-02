# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import requests
from io import BytesIO
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import pprint
import csv
import xmltodict
import os
import detective.chromecrawler as cc
import time
from detective.messenger import err_messeage_to_telegram

marketTxt = None


class jobs:
    jobtype = ''
    workDir = ''
    url = ''
    filetype = ''
    reqdata = None
    # driver = None


def getConfig():
    import configparser
    global path, django_path, main_path, chrome_path  #, phantomjs_path
    config = configparser.ConfigParser()
    config.read('config.ini')
    path = config['COMMON']['REPORT_PATH']
    proj_path = config['COMMON']['PROJECT_PATH']
    django_path = proj_path + r'\MainBoard'
    main_path = django_path + r'\MainBoard'
    chrome_path = config['COMMON']['CHROME_PATH']
    # phantomjs_path = config['COMMON']['PHANTOMJS_PATH']


def fileCheck(workDir, code, name, type, ext):
    filename = r"%s\financeData_%s_%s_%s.%s" % (workDir,
                                                name,
                                                code,
                                                type,
                                                ext)
    # print(filename)
    # print(os.path.isfile(filename))
    # if os.path.isfile(filename):
    #     print(os.stat(filename).st_size, os.stat(filename).st_size > 0)
    return os.path.isfile(filename) and os.stat(filename).st_size > 0


def saveFile(workDir, name, code, type, xml, mode='wb', encoding='utf8'):
    if mode[-1] == 'b':
        file = open(r"%s\financeData_%s_%s_%s.html" % (workDir,
                                                       name,
                                                       code,
                                                       type), mode=mode)
    else:
        file = open(r"%s\financeData_%s_%s_%s.html" % (workDir,
                                                       name,
                                                       code,
                                                       type), mode=mode, encoding=encoding)
    # print(file.name)
    file.write(xml)
    file.close()

def generateEncCode():
    import numpy as np
    yyyymmdd = str(datetime.now())[:10]
    mm = yyyymmdd[5:7]
    dd = yyyymmdd[-2:]
    en = ''
    n = 5
    en += ''.join(["{}".format(np.random.randint(0, 9)) for num in range(0, n)])
    en += mm
    en += ''.join(["{}".format(np.random.randint(0, 9)) for num in range(0, n)])
    en += dd
    return en


def dictfetchall(cursor):
    # "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def getTargetFile(j, c):
    import json
    from watson.db_factory import UpdateFnguideExist
    retResult = ''
    ticker = ""
    sec_name = ""
    url_info = None
    try:
        if j.jobtype.startswith('Global'):
            ticker = c['ticker']
            sec_name = str(c['security']).replace(' ', '').replace('&', 'AND').replace(',', '').replace('.',
                                                                                                     '').replace(
                '!', '').replace('*', '').replace('/', '')
        else:
            ticker = c['code']
            sec_name = c['name']

        if fileCheck(j.workDir, ticker, sec_name, j.jobtype, j.filetype):
            retResult = '[{}][{}][{}]|Skipped'.format(j.jobtype, ticker, sec_name)
            print(retResult)
            pass
        else:
            print('[{}][{}][{}] File is on process...'.format(j.jobtype, ticker, sec_name))
            if j.jobtype.startswith('Global'):
                if j.jobtype == 'GlobalCompanyProfile':
                    urls = j.url.format(ticker, ticker).split('|')

                    url_info = urls[1]
                    res = httpRequest(urls[1], None, 'GET', None)
                    json_msg = json.loads(res.decode('utf-8'))

                    if json_msg['data'] is not None:
                        category_code = json_msg['data']['exchange']
                        if json_msg['data']['keyStats']['MarketCap']['value'] != 'N/A':
                            issued_shares = round(
                                float(str(json_msg['data']['keyStats']['MarketCap']['value']).replace(',', '')) / float(
                                    str(json_msg['data']['primaryData']['lastSalePrice']).replace('$', '')), 1)
                        else:
                            issued_shares = 0.0
                        url_info = urls[0]
                        res = httpRequest(urls[0], None, 'GET', None)
                        json_msg2 = json.loads(res.decode('utf-8'))
                        if json_msg2['data'] is not None:
                            category_name = json_msg2['data']['Sector']['value']
                            category_detail = json_msg2['data']['Industry']['value']
                            tel = json_msg2['data']['Phone']['value']
                            address = json_msg2['data']['Address']['value']
                            location = json_msg2['data']['Region']['value']
                            description = json_msg2['data']['CompanyDescription']['value']
                            for key in json_msg2['data'].keys():
                                json_msg['data'][key] = json_msg2['data'][key]
                        else:
                            category_name = ''
                            category_detail = ''
                            tel = ''
                            address = ''
                            location = ''
                            description = ''

                        retResult = "{}|{}|{}|{}|{}|{}|{}|{}|{}|{}".format(j.jobtype,
                                                                           ticker,
                                                                           category_code,
                                                                           category_name,
                                                                           category_detail,
                                                                           tel,
                                                                           address,
                                                                           location,
                                                                           description,
                                                                           issued_shares)
                        with open(r'{}\financeData_{}_{}_{}.{}'.format(j.workDir, sec_name, ticker, j.jobtype,
                                                                       j.filetype),
                                  'w') as fp:
                            json.dump(json_msg, fp)
                    else:
                        retResult = '[{}][{}][{}]|Update Failed'.format(j.jobtype, ticker, sec_name)
                        print(retResult)
                        with open(r'{}\financeData_{}_{}_{}.{}'.format(j.workDir, sec_name, ticker, j.jobtype,
                                                                       j.filetype),
                                  'w') as fp:
                            json.dump(json_msg, fp)
                elif j.jobtype in ['GlobalFinancialSummary', 'GlobalConsensus']:
                    try:
                        url = j.url.format(ticker, generateEncCode())
                        url_info = url
                        response = httpRequest(url, None, 'GET')
                        with open(r'{}\financeData_{}_{}_{}.{}'.format(j.workDir, sec_name, ticker, j.jobtype,
                                                                       j.filetype),
                                  'w') as fp:
                            json.dump(json.loads(response), fp)
                        retResult = "[{}][{}][{}]|Done".format(j.jobtype, ticker, sec_name)
                    except Exception as e:
                        # qry_url = 'http://compglobal.wisereport.co.kr/Common/CompanySearchGlobal?q={}-US&q1={}-US&etf_yn=1&iso_str=US%2CCN%2CHK%2CJP%2CVN%2CID%2CS6&limit=10'.format(ticker, ticker)
                        qry_url = "http://compglobal.wisereport.co.kr/Lookup/GetGlobalCompany?iso_typ=13&category_typ=W&ntt_cd=WI000&order_mkt=1&order_iso=0&kr_use_yn=1&search_str={}&curpage=1&iso_cd=&perpage=100".format(
                            ticker)
                        url_info = qry_url
                        res = httpRequest(qry_url, None, 'GET')
                        if res.decode('utf-8') == '[]':
                            with open(r'{}\financeData_{}_{}_{}.{}'.format(j.workDir, sec_name, ticker, j.jobtype,
                                                                           j.filetype),
                                      'w') as fp:
                                json.dump("", fp)
                            UpdateFnguideExist(ticker)
                            retResult = '[{}][{}][{}]|NotExist'.format(j.jobtype, ticker, sec_name)
                        else:
                            obj = json.loads(res)
                            matched = False
                            for d in obj:
                                if d['TICKER'] == '{}-US'.format(ticker): matched = True
                                break
                            if not matched:
                                with open(r'{}\financeData_{}_{}_{}.{}'.format(j.workDir, sec_name, ticker, j.jobtype,
                                                                               j.filetype),
                                          'w') as fp:
                                    json.dump("", fp)
                                UpdateFnguideExist(ticker)
                                retResult = '[{}][{}][{}]|NotExist'.format(j.jobtype, ticker, sec_name)
            elif j.url:
                if j.reqdata is None:
                    url = j.url.format(ticker)
                    url_info = url
                    response = httpRequest(url, None, 'GET')
                    # 20200803 파일명 변경  c['name'], c['code'] => ticker, sec_name
                    with open(r'{}\financeData_{}_{}_{}.{}'.format(j.workDir, sec_name, ticker, j.jobtype, j.filetype),
                              'w') as fp:
                        json.dump(json.loads(response), fp)
                    retResult = "[{}][{}][{}]|Done".format(j.jobtype, ticker, sec_name)
                else:
                    url = j.url
                    url_info = url
                    j.reqdata['gicode'] = 'A{}'.format(ticker)
                    response = httpRequestWithDriver(None, url, j.reqdata)
                    # print(response)
                    soup = BeautifulSoup(response.decode('utf-8'), "lxml")
                    # File 처리
                    xml = soup.prettify(encoding='utf-8').replace(b'&', b'&amp;')
                    saveFile(j.workDir, sec_name, ticker, j.jobtype, xml)

                    # File 처리 끝
                    # DB 처리
                    marketTxt = select_by_attr(soup, 'span', 'class', 'stxt stxt1').text
                    marketTxtDetail = select_by_attr(soup, 'span', 'class', 'stxt stxt2').text
                    settlementMonth = select_by_attr(soup, 'span', 'class', 'stxt stxt3').text
                    retResult = "{}|{}|{}|{}|{}|{}".format(j.jobtype, ticker, sec_name, marketTxt, marketTxtDetail,
                                                               settlementMonth)
    except Exception as e:
        errmsg = '{}\n{}\n{}'.format('getTargetFile', str(e), url_info)
        err_messeage_to_telegram(errmsg)
    return retResult


def getTargetFileTest(j, c):
    import json
    from watson.db_factory import UpdateFnguideExist
    retResult = ''
    ticker = ""
    sec_name = ""
    url_info = None
    try:
        if j.jobtype.startswith('Global'):
            ticker = c['ticker']
            sec_name = str(c['security']).replace(' ', '').replace('&', 'AND').replace(',', '').replace('.',
                                                                                                     '').replace(
                '!', '').replace('*', '').replace('/', '')
        else:
            ticker = c['code']
            sec_name = c['name']

        if fileCheck(j.workDir, ticker, sec_name, j.jobtype, j.filetype):
            retResult = '[{}][{}][{}]|Skipped'.format(j.jobtype, ticker, sec_name)
            print(retResult)
            pass
        else:
            print('[{}][{}][{}] File is on process...'.format(j.jobtype, ticker, sec_name))
            if j.jobtype.startswith('Global'):
                if j.jobtype == 'GlobalCompanyProfile':
                    urls = j.url.format(ticker, ticker).split('|')

                    url_info = urls[1]
                    print(url_info)
                    res = httpRequest(urls[1], None, 'GET', None)
                    json_msg = json.loads(res.decode('utf-8'))

                    if json_msg['data'] is not None:
                        category_code = json_msg['data']['exchange']
                        if json_msg['data']['keyStats']['MarketCap']['value'] != 'N/A':
                            issued_shares = round(
                                float(str(json_msg['data']['keyStats']['MarketCap']['value']).replace(',', '')) / float(
                                    str(json_msg['data']['primaryData']['lastSalePrice']).replace('$', '')), 1)
                        else:
                            issued_shares = 0.0
                        url_info = urls[0]
                        print(url_info)
                        res = httpRequest(urls[0], None, 'GET', None)
                        print(res)
                        json_msg2 = json.loads(res.decode('utf-8'))
                        if json_msg2['data'] is not None:
                            category_name = json_msg2['data']['Sector']['value']
                            category_detail = json_msg2['data']['Industry']['value']
                            tel = json_msg2['data']['Phone']['value']
                            address = json_msg2['data']['Address']['value']
                            location = json_msg2['data']['Region']['value']
                            description = json_msg2['data']['CompanyDescription']['value']
                            for key in json_msg2['data'].keys():
                                json_msg['data'][key] = json_msg2['data'][key]
                        else:
                            category_name = ''
                            category_detail = ''
                            tel = ''
                            address = ''
                            location = ''
                            description = ''

                        retResult = "{}|{}|{}|{}|{}|{}|{}|{}|{}|{}".format(j.jobtype,
                                                                           ticker,
                                                                           category_code,
                                                                           category_name,
                                                                           category_detail,
                                                                           tel,
                                                                           address,
                                                                           location,
                                                                           description,
                                                                           issued_shares)
                        with open(r'{}\financeData_{}_{}_{}.{}'.format(j.workDir, sec_name, ticker, j.jobtype,
                                                                       j.filetype),
                                  'w') as fp:
                            json.dump(json_msg, fp)
                    else:
                        retResult = '[{}][{}][{}]|Update Failed'.format(j.jobtype, ticker, sec_name)
                        print(retResult)
                        with open(r'{}\financeData_{}_{}_{}.{}'.format(j.workDir, sec_name, ticker, j.jobtype,
                                                                       j.filetype),
                                  'w') as fp:
                            json.dump(json_msg, fp)
                elif j.jobtype in ['GlobalFinancialSummary', 'GlobalConsensus']:
                    try:
                        url = j.url.format(ticker, generateEncCode())
                        url_info = url
                        print(url_info)
                        response = httpRequest(url, None, 'GET')
                        with open(r'{}\financeData_{}_{}_{}.{}'.format(j.workDir, sec_name, ticker, j.jobtype,
                                                                       j.filetype),
                                  'w') as fp:
                            json.dump(json.loads(response), fp)
                        retResult = "[{}][{}][{}]|Done".format(j.jobtype, ticker, sec_name)
                    except Exception as e:
                        # qry_url = 'http://compglobal.wisereport.co.kr/Common/CompanySearchGlobal?q={}-US&q1={}-US&etf_yn=1&iso_str=US%2CCN%2CHK%2CJP%2CVN%2CID%2CS6&limit=10'.format(ticker, ticker)
                        qry_url = "http://compglobal.wisereport.co.kr/Lookup/GetGlobalCompany?iso_typ=13&category_typ=W&ntt_cd=WI000&order_mkt=1&order_iso=0&kr_use_yn=1&search_str={}&curpage=1&iso_cd=&perpage=100".format(
                            ticker)
                        url_info = qry_url
                        print(url_info)
                        res = httpRequest(qry_url, None, 'GET')
                        if res.decode('utf-8') == '[]':
                            with open(r'{}\financeData_{}_{}_{}.{}'.format(j.workDir, sec_name, ticker, j.jobtype,
                                                                           j.filetype),
                                      'w') as fp:
                                json.dump("", fp)
                            UpdateFnguideExist(ticker)
                            retResult = '[{}][{}][{}]|NotExist'.format(j.jobtype, ticker, sec_name)
                        else:
                            obj = json.loads(res)
                            matched = False
                            for d in obj:
                                if d['TICKER'] == '{}-US'.format(ticker): matched = True
                                break
                            if not matched:
                                with open(r'{}\financeData_{}_{}_{}.{}'.format(j.workDir, sec_name, ticker, j.jobtype,
                                                                               j.filetype),
                                          'w') as fp:
                                    json.dump("", fp)
                                UpdateFnguideExist(ticker)
                                retResult = '[{}][{}][{}]|NotExist'.format(j.jobtype, ticker, sec_name)
            elif j.url:
                if j.reqdata is None:
                    url = j.url.format(ticker)
                    url_info = url
                    print(url_info)
                    response = httpRequest(url, None, 'GET')
                    # 20200803 파일명 변경  c['name'], c['code'] => ticker, sec_name
                    with open(r'{}\financeData_{}_{}_{}.{}'.format(j.workDir, sec_name, ticker, j.jobtype, j.filetype),
                              'w') as fp:
                        json.dump(json.loads(response), fp)
                    retResult = "[{}][{}][{}]|Done".format(j.jobtype, ticker, sec_name)
                else:
                    url = j.url
                    url_info = url
                    print(url_info)
                    j.reqdata['gicode'] = 'A{}'.format(ticker)
                    response = httpRequestWithDriver(None, url, j.reqdata)
                    # print(response)
                    soup = BeautifulSoup(response.decode('utf-8'), "lxml")
                    # File 처리
                    xml = soup.prettify(encoding='utf-8').replace(b'&', b'&amp;')
                    saveFile(j.workDir, sec_name, ticker, j.jobtype, xml)

                    # File 처리 끝
                    # DB 처리
                    marketTxt = select_by_attr(soup, 'span', 'class', 'stxt stxt1').text
                    marketTxtDetail = select_by_attr(soup, 'span', 'class', 'stxt stxt2').text
                    settlementMonth = select_by_attr(soup, 'span', 'class', 'stxt stxt3').text
                    retResult = "{}|{}|{}|{}|{}|{}".format(j.jobtype, ticker, sec_name, marketTxt, marketTxtDetail,
                                                               settlementMonth)
    except Exception as e:
        errmsg = '{}\n{}\n{}'.format('getTargetFile', str(e), url_info)
        err_messeage_to_telegram(errmsg)
    return retResult


def getUSFinanceData(j_type, t_url):
    import sys
    import os
    import django
    from multiprocessing import Pool
    from concurrent.futures import ThreadPoolExecutor
    from functools import partial
    getConfig()
    # from selenium import webdriver

    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()

    yyyymmdd = str(datetime.now())[:10]
    workDir = r'{}\{}\{}'.format(path, j_type, yyyymmdd)
    if not os.path.exists(workDir):
        os.makedirs(workDir)
    try:

        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
            select ticker as 'code', max(replace(replace(replace(replace(replace(replace(security, ' ', ''), '&', 'AND'), ',', ''), '.', ''), '!', ''), '*', '')) as 'name'
            from (
                select security, ticker from detective_app_usstocks where listing = 'Y'
                union
                select security, ticker from detective_app_usnasdaqstocks where listing = 'Y'
            )
            group by ticker
            order by ticker""")
            s = dictfetchall(cursor)

            agents = 3
            j = jobs()
            j.workDir = workDir
            j.url = t_url
            j.jobtype = j_type

            if j.jobtype == 'GlobalSnapshot':
                # agents = 2
                j.filetype = 'html'
            elif j.jobtype == 'GlobalSummary':
                # agents = 3
                j.filetype = 'json'

            func = partial(getTargetFile, j)
            # with Pool(processes=agents) as pool:
            with ThreadPoolExecutor(max_workers=agents) as pool:
                result = pool.map(func, iter(s))
            print(result)
    except Exception as e:
        errmsg = '{}\n{}'.format('getUSFinanceData', str(e))
        err_messeage_to_telegram(errmsg)


def getUSFinanceDataStandalone(j_type, t_url):
    import sys
    import os
    import django
    import time
    import json
    import detective_app.models as detective_db

    getConfig()

    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()

    yyyymmdd = str(datetime.now())[:10]
    workDir = r'{}\{}\{}'.format(path, j_type, yyyymmdd)
    if not os.path.exists(workDir):
        os.makedirs(workDir)

    try:
        drv = None
        # from django.db import connection
        # with connection.cursor() as cursor:
        #     cursor.execute("""
        #     select ticker as 'code', max(replace(replace(replace(replace(replace(replace(security, ' ', ''), '&', 'AND'), ',', ''), '.', ''), '!', ''), '*', '')) as 'name'
        #     from (
        #         select security, ticker from detective_app_usstocks where listing = 'Y'
        #         union
        #         select security, ticker from detective_app_usnasdaqstocks where listing = 'Y'
        #     )
        #     group by ticker
        #     order by ticker""")
        stockInfo = detective_db.USNasdaqStocks.objects.filter(listing='Y')
        url_info = None
        if j_type == 'GlobalSnapshot':
            filetype = 'html'
            drv = cc.ChromeDriver()
            drv.set_path()
            drv.set_option()
            drv.set_user_agent()
            drv.set_driver()
            drv.set_waiting()
            ck = None
            for i in stockInfo:
                sec_name = str(i.security).replace(' ', '').replace('&', 'AND').replace(',', '').replace('.',
                                                                                                         '').replace(
                    '!', '').replace('*', '').replace('/', '')
                if fileCheck(workDir, i.ticker, sec_name, j_type, filetype):
                    retResult = '[{}][{}][{}]|Skipped'.format(j_type, i.ticker, sec_name)
                    print(retResult)
                    pass
                else:
                    data = {}
                    print('[{}][{}][{}] File is on process...'.format(j_type, i.ticker, sec_name))
                    url = t_url.format(i.ticker, generateEncCode())
                    url_info = url
                    if ck is not None:
                        for c in ck:
                            drv.driver.add_cookie(c)
                    drv.set_url(url)
                    response = drv.driver.page_source
                    soup = BeautifulSoup(response, "lxml")
                    xml = soup.prettify(encoding='utf-8').replace(b'&', b'&amp;')
                    saveFile(workDir, sec_name, i.ticker, j_type, xml)
                    ck = drv.driver.get_cookies()
                    # File 처리 끝
                    # DB 처리
                    tmp = select_by_attr(soup, 'ul', 'class', 'row2').find_all('li')
                    marketCd = tmp[1].text
                    marketTxt = tmp[2].text
                    marketTxtDetail = tmp[3].text
                    settlementMonth = tmp[4].text
                    issued_shares = int(
                        select_by_attr(soup, 'div', 'class', 'row02').find_all('tr')[5].find_all('td')[1].text
                            .replace('\n', '')
                            .replace('\t', '')
                            .replace('천주', '')
                            .replace(',', '')
                            .replace(' ', '')
                    ) * 1000
                    # 0: [주가 / 전일대비 / 수익률]
                    # 1: [52주 최고 / 최저]
                    # 2: [거래량 / 거래대금]
                    # 3: [시가총액 / 순위]
                    # 4: [52주 베타]
                    # 5: [상장주식수]
                    # 6: [수익률(1M / 3M / 6M / 1Y)]
                    USStockMarketTextUpdate(i.ticker, marketCd, marketTxt, marketTxtDetail, settlementMonth,
                                            issued_shares)
                    # tmp = select_by_attr(soup, 'ul', 'class', 'row1').find_all('li')
                    # for t in tmp:
                    #     print(t.text)
                    time.sleep(1)

            drv.driverClose()
            drv.driverQuit()
        elif j_type == 'GlobalFinancialSummary':
            filetype = 'json'
            for i in stockInfo:
                sec_name = str(i.security).replace(' ', '').replace('&', 'AND').replace(',', '').replace('.',
                                                                                                         '').replace(
                    '!', '').replace('*', '').replace('/', '')
                url = t_url.format(i.ticker, generateEncCode())
                url_info = url
                response = httpRequest(url, None, 'GET')
                with open(r'{}\financeData_{}_{}_{}.{}'.format(workDir, sec_name, i.ticker, j_type,
                                                               filetype),
                          'w') as fp:
                    json.dump(json.loads(response), fp)
        elif j_type == 'GlobalCompanyProfile':
            import math
            filetype = 'json'
            # drv = cc.ChromeDriver()
            # drv.set_path()
            # drv.set_option()
            # drv.set_user_agent()
            # drv.set_driver()
            # drv.set_waiting()
            for idx, i in enumerate(stockInfo):
                sec_name = str(i.security).replace(' ', '').replace('&', 'AND').replace(',', '').replace('.',
                                                                                                         '').replace(
                    '!', '').replace('*', '').replace('/', '')
                if fileCheck(workDir, i.ticker, sec_name, j_type, filetype):
                    retResult = '[{}/{}][{}][{}][{}]|Skipped'.format(idx+1, len(stockInfo), j_type, i.ticker, sec_name)
                    print(retResult)
                    pass
                else:
                    urls = t_url.format(i.ticker, i.ticker)
                    url_split = urls.split('|')
                    url_info = url_split[0]
                    drv.set_url(url_split[0])
                    soup = BeautifulSoup(drv.driver.page_source, "lxml")
                    response = soup.find("body").text
                    json_msg = json.loads(response)
                    if json_msg['data'] is not None:
                        category_name = json_msg['data']['Sector']['value']
                        category_detail = json_msg['data']['Industry']['value']
                        tel = json_msg['data']['Phone']['value']
                        address = json_msg['data']['Address']['value']
                        location = json_msg['data']['Region']['value']
                        description = json_msg['data']['CompanyDescription']['value']
                        url_info = url_split[1]
                        drv.set_url(url_split[1])
                        soup = BeautifulSoup(drv.driver.page_source, "lxml")
                        response = soup.find("body").text
                        json_msg = json.loads(response)
                        category_code = json_msg['data']['exchange']
                        if json_msg['data']['keyStats']['MarketCap']['value'] != 'N/A':
                            issued_shares = round(float(str(json_msg['data']['keyStats']['MarketCap']['value']).replace(',', '')) / float(
                                str(json_msg['data']['primaryData']['lastSalePrice']).replace('$', '')), 1)
                        else:
                            issued_shares = 0.0
                        print("[{}/{}]Updating market info...{}-{}-{}-{}-{}".format(idx + 1, len(stockInfo), i.ticker,
                                                                                    category_code, category_name,
                                                                                    category_detail, issued_shares))
                        USStockMarketTextUpdateAdvcd(i.ticker, category_code, category_name, category_detail, tel, address,
                                                     location, description,
                                                     issued_shares)
                        with open(r'{}\financeData_{}_{}_{}.{}'.format(workDir, sec_name, i.ticker, j_type,
                                                                       filetype),
                                  'w') as fp:
                            json.dump(json_msg, fp)
                    else:
                        print("[{}/{}]Failed update market info...{}".format(idx + 1, len(stockInfo), i.ticker))
                        with open(r'{}\financeData_{}_{}_{}.{}'.format(workDir, sec_name, i.ticker, j_type,
                                                                       filetype),
                                  'w') as fp:
                            json.dump(json_msg, fp)
                        continue
    except Exception as e:
        if drv is not None:
            drv.driverClose()
            drv.driverQuit()
        errmsg = '{}\n{}\n{}'.format('getUSFinanceDataStandalone', str(e), url_info)
        err_messeage_to_telegram(errmsg)


def getFinanceData(cmd=None):
    import sys
    import os
    import django
    from multiprocessing import Pool
    from functools import partial
    getConfig()
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    # CHROMEDRIVER_PATH = chrome_path
    options = Options()
    options.headless = True
    # driver = webdriver.Chrome(CHROMEDRIVER_PATH, chrome_options=options)
    # driver.implicitly_wait(3)

    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    from django.db.models import Q
    global marketTxt

    yyyymmdd = str(datetime.now())[:10]
    url = "http://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp"
    reportType = {
        101: 'snapshot',
        103: 'financeReport',
        104: 'financeRatio',
        108: 'consensus',
        200: 'ROE',
        300: 'GlobalCompanyProfile',
        301: 'GlobalFinancialSummary',
        302: 'GlobalConsensus',

    }  # 101 : snapshot, 103 : financeReport, 104 : financeRatio
    urlInfo = {
        101: 'http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp',
        103: 'http://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp',
        104: 'http://comp.fnguide.com/SVO2/ASP/SVD_FinanceRatio.asp',
        108: 'http://comp.fnguide.com/SVO2/ASP/SVD_Consensus.asp',
        200: 'http://comp.fnguide.com/SVO2/json/chart/01_04/chart_A{}_D.json',
        300: 'https://api.nasdaq.com/api/company/{}/company-profile|https://api.nasdaq.com/api/quote/{}/info?assetclass=stocks',
        301: 'http://compglobal.wisereport.co.kr/miraeassetdaewoo/company/get_snap_financial_summary?ticker={}-US&freq_typ=A&en={}',
        302: 'http://compglobal.wisereport.co.kr/Company/GetConsensusData1?cmp_cd={}-US&curr=USD&en={}'
    }

    fileInfo = {
        101: 'html',
        103: 'html',
        104: 'html',
        108: 'html',
        200: 'json',
        300: 'json',
        301: 'json',
        302: 'json',
    }
    # 'http://compglobal.wisereport.co.kr/miraeassetdaewoo/Company/Snap?cmp_cd={}-US&en={}'

    data = {
        'pGB': 1,
        'gicode': '',
        'cID': '',
        'MenuYn': 'Y',
        'ReportGB': 'D',  # D: 연결, B: 별도
        'NewMenuID': 0,
        'stkGb': 701,
    }

    xmlString = ''
    result = None

    try:
        for key in reportType.keys():
            # print(cmd, cmd and key != cmd)
            if cmd and key != cmd:
                continue
            if cmd >= 300:
                stockInfo = detective_db.USNasdaqStocks.objects.filter(listing='Y', fnguide_exist='Y')
            else:
                stockInfo = detective_db.Stocks.objects.filter(listing='Y')
            #     jobtype = reportType[key]
            #     url = urlInfo[key]
            #     # getUSFinanceData(jobtype, url)
            #     getUSFinanceDataStandalone(jobtype, url)
            #     continue

            # stockInfo = detective_db.Stocks.objects.filter(code='005930', listing='Y')
            workDir = r'%s\%s\%s' % (path, reportType[key], yyyymmdd)
            if not os.path.exists(workDir):
                os.makedirs(workDir)

            data['NewMenuID'] = key
            # ext = 'json' if cmd == 200 else 'html'
            # 신규코드(multiprocessing) 시작
            if cmd == 200:
                agents = 2
                j = jobs()
                j.filetype = fileInfo[key]
                j.workDir = workDir
                j.jobtype = reportType[key]
                j.url = urlInfo[key]
                s = stockInfo.values()
                func = partial(getTargetFile, j)
                with Pool(processes=agents) as pool:
                    result = pool.map(func, s)
            elif cmd == 300:
                agents = 5
                j = jobs()
                j.filetype = fileInfo[key]
                j.workDir = workDir
                j.jobtype = reportType[key]
                j.url = urlInfo[key]
                s = stockInfo.values()
                func = partial(getTargetFile, j)
                with Pool(processes=agents) as pool:
                    result = pool.map(func, s)

                for r in result:
                    retArr = r.split('|')
                    if len(retArr) < 3: continue

                    if retArr[2] != '' and retArr[0] == 'GlobalCompanyProfile':
                        USStockMarketTextUpdateAdvcd(retArr[1], retArr[2], retArr[3], retArr[4], retArr[5],
                                                     retArr[6], retArr[7], retArr[8], retArr[9])
                        # 0 j.jobtype,
                        # 1 ticker,
                        # 2 category_code,
                        # 3 category_name,
                        # 4 category_detail,
                        # 5 tel,
                        # 6 address,
                        # 7 location,
                        # 8 description,
                        # 9 issued_shares
                if len(stockInfo) != len(result):
                    print(
                        "Total target stocks : {}\n requested stocks : {}\nPlease check out the process.\nTerminating this program.".format(
                            len(stockInfo), len(result)))
                    # exit(0)
            elif cmd == 301 or cmd == 302:
                agents = 2
                j = jobs()
                j.filetype = fileInfo[key]
                j.workDir = workDir
                j.jobtype = reportType[key]
                j.url = urlInfo[key]
                s = stockInfo.values()
                func = partial(getTargetFile, j)
                with Pool(processes=agents) as pool:
                    result = pool.map(func, s)
            else:
                agents = 5
                j = jobs()
                j.filetype = fileInfo[key]
                j.workDir = workDir
                j.jobtype = reportType[key]
                j.url = urlInfo[key]
                j.reqdata = data
                # j.driver = driver
                s = stockInfo.values()
                # j.driver = cc.ChromeDriver()
                func = partial(getTargetFile, j)
                with Pool(processes=agents) as pool:
                    result = pool.map(func, s)

                for r in result:
                    retArr = r.split('|')
                    if len(retArr) < 3: continue
                    if retArr[3] != '' and retArr[0] == 'snapshot':
                        StockMarketTextUpdate(retArr[1], retArr[3].replace('\xa0', ' '), retArr[4].replace('\xa0', ' '),
                                              retArr[5].replace('\xa0', ' '))
                if len(stockInfo) != len(result):
                    print(
                        "Total target stocks : {}\n requested stocks : {}\nPlease check out the process.\nTerminating this program.".format(
                            len(stockInfo), len(result)))
                    # exit(0)

                # j.driver.driverQuit()
            # 신규코드(multiprocessing) 끝

            # 20200622 원래 코드임 - 위 코드 자꾸 에러나면 원복필요
            # for idx, s in enumerate(stockInfo):
            #     # print(fileCheck(workDir, s.code, s.name, reportType[key]))
            #
            #     if fileCheck(workDir, s.code, s.name, reportType[key], ext):
            #         print('[%d/%d][%s][%s][%s] File is already exist. Skipped...' % (idx+1, len(stockInfo), reportType[key], s.code, s.name))
            #         continue
            #     print('[%d/%d][%s][%s][%s] File is on process...' % (idx+1, len(stockInfo), reportType[key], s.code, s.name))
            #     data['gicode'] = 'A%s' % s.code
            #     # response = httpRequest(urlInfo[key], data)
            #     if cmd == 200:
            #         url = urlInfo[key] % s.code
            #         response = httpRequest(url, None, 'GET')
            #         with open(r'%s\financeData_%s_%s_%s.json' % (workDir, s.name, s.code, reportType[key]), 'w') as fp:
            #             json.dump(json.loads(response), fp)
            #     else:
            #         response = httpRequestWithDriver(driver, urlInfo[key], data)
            #         # print(response)
            #         soup = BeautifulSoup(response.decode('utf-8'), "lxml")
            #         # File 처리
            #         xml = soup.prettify(encoding='utf-8').replace(b'&', b'&amp;')
            #         # p = Process(target=saveFile, args=(workDir, s, reportType[key], xml))
            #         # p = Process(target=saveFile, args=(workDir, s.code, s.name, reportType[key], xml))
            #         # p.start()
            #         # p.join()
            #         saveFile(workDir, s.code, s.name, reportType[key], xml)
            #
            #         # File 처리 끝
            #         # DB 처리
            #         marketTxt = select_by_attr(soup, 'span', 'class', 'stxt stxt1').text
            #         marketTxtDetail = select_by_attr(soup, 'span', 'class', 'stxt stxt2').text
            #         settlementMonth = select_by_attr(soup, 'span', 'class', 'stxt stxt3').text
            #
            #         if marketTxt and reportType[key] == 'snapshot':
            #             StockMarketTextUpdate(s.code, marketTxt, marketTxtDetail, settlementMonth)
            #             print('[%d/%d][%s][%s][%s] MarketInformation Updated to %s | %s | %s' % (
            #             idx + 1, len(stockInfo), reportType[key], s.code, s.name, marketTxt, marketTxtDetail, settlementMonth))
            #             marketTxt = None

            # FinanceReport 성공 끝

        print("FnGuideDataCollection job finished")
        # driver.close()
        # driver.quit()
    except Exception as e:
        errmsg = '{}\n{}'.format('getFinanceData', str(e))
        err_messeage_to_telegram(errmsg)
        # driver.close()
        # driver.quit()


def dynamic_parse_table(table_id, table, crp_cd, crp_nm, t_hierarchy=None, c_hierarchy=None):
    n_columns = 0
    n_rows = 0

    prev_column = ''
    prev_column_no = None
    prev_row = ''
    prev_row_no = None

    report_name = ''
    categorizing = ''

    data_information = {}
    column_names = []
    data_pipe = []

    if table_id[-1:] in ['Y', 'Q']:
        if table_id[-1:] == 'Y':
            categorizing = 'YEARLY'
        elif table_id[-1:] == 'Q':
            categorizing = 'QUARTERLY'
        if table_id.find('Sonik') > -1:
            report_name = '포괄손익계산서'
        elif table_id.find('Daecha') > -1:
            report_name = '재무상태표'
        elif table_id.find('Cash') > -1:
            report_name = '현금흐름표'
        elif table_id.find('highlight') > -1:
            report_name = 'FinancialHighlight'

    else:
        if table_id.find('svdMainGrid') > -1:
            report_name = table_id
        else:
            pass
    table_hierarchy = {
        'HorizonHeader': 'thead-tr-th',
        'VerticalHeader': 'tbody-tr-th-div-span',
        'Data': 'tbody-tr-td'
    }
    content_hierarchy = {
        'column': {'TargetTag': 'tr',
                   'Attribute': 'class',
                   'Hierarchy': ['acd_dep_start_close', 'acd_dep2_sub']
                   },
        'row': []
    }

    if t_hierarchy is None:
        pass
    else:
        table_hierarchy = t_hierarchy

    if c_hierarchy is None:
        pass
    else:
        content_hierarchy = t_hierarchy

    tmpHierarchy = table_hierarchy['HorizonHeader'].split('-')

    for tag1 in table.find_all(tmpHierarchy[0]):  # thead
        if tag1.text == '' or tag1.text == '\n':
            pass
        for tag2 in tag1.find_all(tmpHierarchy[1]):  # tr
            for tag3 in tag2.find_all(tmpHierarchy[2]):  # th
                if tag3.text == '전년동기':
                    temp = column_names[-1]
                    period = temp.split('/')
                    column_names.append('%d/%s' % (int(period[0]) - 1, period[1]))
                elif tag3.text in ['Annual', 'Net Quarter']:
                    pass
                elif '(E)' in tag3.text:
                    tmpTag = tag3.text.replace('\n', '').replace('(E) : Estimate컨센서스, 추정치', '')
                    column_names.append(tmpTag)
                elif '(P)' in tag3.text:
                    tmpTag = tag3.text.replace('\n', '').replace('(P) : Provisional잠정실적', '')
                    column_names.append(tmpTag)
                else:
                    column_names.append(tag3.text.replace('\n', '').strip())

    tmpHierarchy = table_hierarchy['VerticalHeader'].split('-')
    dataHierarchy = table_hierarchy['Data'].split('-')

    get_table_row_header(table, tmpHierarchy, dataHierarchy, content_hierarchy, data_information, prev_column,
                         data_pipe)
    if report_name.startswith('svdMainGrid'):
        # print(report_name)
        caption = report_name.replace('svdMainGrid', get_table_contents(table, 'caption')[0])
        column_names, keys, values = setting(get_table_contents(table, 'thead tr th'),
                                             get_table_contents(table, 'tbody tr th'),
                                             get_table_contents(table, 'tbody tr td'))
        if len(keys) == 0:
            # print("[%s][%s][%s] Data is on Processing" % (crp_cd, crp_nm, report_name))
            # if report_name == 'svdMainGrid10D':
            # print(column_names)
            # print(keys)
            # print(values)
            DailySnapShotDataStore(report_name, crp_cd, crp_nm, caption, column_names, '', values)
        else:
            # if report_name == 'svdMainGrid10D':
            # print(column_names)
            # print(keys)
            # print(values)
            # print("[%s][%s][%s] Data is on Processing" % (crp_cd, crp_nm, report_name))
            for idx1, key in enumerate(keys):
                DailySnapShotDataStore(report_name, crp_cd, crp_nm, caption, column_names, key, values[idx1])
    else:
        # print("[%s][%s][%s][%s] Data is on Processing" % (crp_cd, crp_nm, report_name, categorizing))
        return column_names, data_information  # DB저장 빼고 파일에서 직접 읽어오기위해 처리
        # for di in data_information.keys():
        #     # print(categorizing, column_names)
        #     # print(di, data_information[di])
        #     ## 20180504
        #     if report_name == 'FinancialHighlight':
        #         # print(table.text)
        #         # get_table_contents(table, 'tbody tr th')
        #         # get_table_contents(table, 'tbody tr td')
        #         # print("FinancialHighlight")
        #         SnapShotDataStore(report_name, crp_cd, crp_nm, categorizing, column_names, di, data_information[di])
        #     else:
        #         # print(report_name)
        #         # get_table_contents(table, 'tbody tr th')
        #         # get_table_contents(table, 'tbody tr td')
        #         # print("FinancialReportDataStore")
        #         FinancialReportDataStore(report_name, crp_cd, crp_nm, categorizing, column_names, di, data_information[di])
        #     ## 20180504
        #     # for idx, column_name in enumerate(column_names[1:]):
        #     #     period_info = column_name.split('/')
        #     #     if len(period_info) < 2:
        #     #         continue
        #     #     print(report_name, crp_cd, crp_nm, categorizing, period_info[0], period_info[1],
        #     #           str(int(period_info[1])/3)[0]+'Q', di, data_information[di][idx])


def get_table_row_header(rs, hierarchy, hierarchy2, c_hierarchy, data_information, prev_column, data_pipe, level=0):
    # print(('~~~~~~~~~~~~~~~~~~~~~~~' + prev_column) * 1)
    # print(level, '*' * 20)
    # if level > 0:
    #     print(level, len(rs))
    i = level
    isTarget = False
    isUpper = False
    # data = data_pipe
    try:
        if len(hierarchy) < i + 1:
            pass
        else:
            # print(('~~~~~~~~~~~~~~~~~~~~~~~' + prev_column) * 2)
            if hierarchy[i] == c_hierarchy['column']['TargetTag']:
                isTarget = True
            for tag in rs.find_all(hierarchy[i]):
                isUpper = False
                if isTarget and c_hierarchy['column']['Attribute'] in tag.attrs.keys():
                    for attr in tag.attrs[c_hierarchy['column']['Attribute']]:
                        if c_hierarchy['column']['Hierarchy'][0] == attr:
                            isUpper = True
                # print('else4', hierarchy[i+1])
                # if len(tag.find_all(hierarchy[i+1])):
                if hierarchy[i] == 'tr' and len(tag.find_all(hierarchy2[len(hierarchy2) - 1])):
                    data_pipe = get_data_content(tag, hierarchy2, len(hierarchy2) - 1)
                if is_exist_more_information(tag, hierarchy, i + 1):
                    # print(tag)
                    if isTarget and isUpper:
                        # print('if isTarget and isUpper:' * 5)
                        prev_column = get_text_content(tag, hierarchy, prev_column, len(hierarchy) - 1).replace(u'\xa0',
                                                                                                                '')
                        # print('if isTarget and isUpper:' * 5)
                        # print(('~~~~~~~~~~~~~~~~~~~~~~~' + prev_column) * 3)
                    # if 'class' in tag.attrs.keys(): print(tag.attrs['class'])
                    if 'class' in tag.attrs.keys() and \
                            tag.attrs[c_hierarchy['column']['Attribute']] in [['rwf', 'rowBold'], ['rwf', '']]:
                        prev_column = ''
                    get_table_row_header(tag,
                                         hierarchy,
                                         hierarchy2,
                                         c_hierarchy,
                                         data_information,
                                         prev_column,
                                         data_pipe,
                                         i + 1)
                else:
                    # print(tag)
                    # print(get_data_content(tag, hierarchy2, len(hierarchy2)-1))
                    # print(('~~~~~~~~~~~~~~~~~~~~~~~' + prev_column) * 4)
                    if prev_column == '' or tag.text.replace(u'\xa0', '') == prev_column:
                        data_information[tag.text.replace(u'\xa0', '').replace('\n', '').strip()] = data_pipe
                    else:
                        data_information[
                            prev_column + '-' + tag.text.replace(u'\xa0', '').replace('\n', '').strip()] = data_pipe
                    # print(data_information)
                    break
    except Exception as e:
        print(e)


def get_data_content(rs, hierarchy, level):
    retResult = []
    for tag in rs.find_all(hierarchy[level]):
        retResult.append(tag.text.replace(u'\xa0', 'None').replace('\n', '').strip())
    return retResult


def get_text_content(rs, hierarchy, prev_column, level):
    # print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n', prev_column, '\n$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
    retStr = prev_column
    if len(hierarchy) < level + 1:
        return None
    for tag in rs.find_all(hierarchy[level]):
        # print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n', tag, '\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
        if is_exist_more_information(tag, hierarchy, level + 1):
            get_text_content(tag, hierarchy, prev_column, level + 1)
        else:
            # print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%', tag, '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
            # print(tag.attrs['class'], tag.attrs)
            if tag.attrs['class'] in [['tcr'], ['blind']]:
                pass
            else:
                if tag.text == retStr:
                    pass
                else:
                    retStr = tag.text.replace('\n', '').strip()
        # print('*'*20)
        # print(retStr)
        # print('*' * 20)
    return retStr


def is_exist_more_information(rs, hierarchy, level):
    if len(hierarchy) < level + 1:
        return 0
    return len(rs.find_all(hierarchy[level]))


def StockMarketTextUpdate(crp_cd, market_text, market_text_detail, sttl_month):
    import sys
    import os
    import django
    from datetime import datetime
    # sys.path.append(r'D:\Waver\MainBoard')
    # sys.path.append(r'D:\Waver\MainBoard\MainBoard')
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    try:
        print("Updating market info...{}-{}-{}-{}".format(crp_cd, market_text, market_text_detail, sttl_month))
        detective_db.Stocks.objects.filter(code=crp_cd).update(market_text=market_text, market_text_detail=market_text_detail, settlement_month=sttl_month)
    except Exception as e:
        print('[Error on StockDataUpdate]\n', '*' * 50, e)


def USStockMarketTextUpdate(crp_cd, market_code, market_text, market_text_detail, sttl_month, issued_shares):
    import sys
    import os
    import django
    from datetime import datetime
    # sys.path.append(r'D:\Waver\MainBoard')
    # sys.path.append(r'D:\Waver\MainBoard\MainBoard')
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    try:
        print("Updating market info...{}-{}-{}-{}-{}".format(crp_cd, market_code, market_text, market_text_detail, sttl_month))
        detective_db.USStocks.objects.filter(ticker=crp_cd).update(category_code=market_code,
                                                                   category_name_kr=market_text,
                                                                   category_detail_kr=market_text_detail,
                                                                   settlement_month=sttl_month,
                                                                   issued_shares=issued_shares)
        detective_db.USNasdaqStocks.objects.filter(ticker=crp_cd).update(category_code=market_code,
                                                                         category_name_kr=market_text,
                                                                         category_detail_kr=market_text_detail,
                                                                         settlement_month=sttl_month,
                                                                         issued_shares=issued_shares)
    except Exception as e:
        print('[Error on USStockMarketTextUpdate]\n', '*' * 50, e)


def USStockMarketTextUpdateAdvcd(crp_cd, category_code, category_name, category_detail, tel, address, location, description, issued_shares):
    import sys
    import os
    import django
    from datetime import datetime
    # sys.path.append(r'D:\Waver\MainBoard')
    # sys.path.append(r'D:\Waver\MainBoard\MainBoard')
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    try:
        print("Updating market info...{}-{}-{}-{}-{}".format(crp_cd, category_code, category_name, category_detail,
                                                             issued_shares))
        detective_db.USNasdaqStocks.objects.filter(ticker=crp_cd).update(category_code=category_code,
                                                                         category_name=category_name,
                                                                         category_detail=category_detail,
                                                                         tel=tel,
                                                                         address=address,
                                                                         location=location,
                                                                         description=description,
                                                                         issued_shares=issued_shares)
    except Exception as e:
        print('[Error on USStockMarketTextUpdate]\n', '*' * 50, e)


def DailySnapShotDataStore(report_name, crp_cd, crp_nm, caption, column_names, key, data_list):
    import sys
    import os
    import django
    from datetime import datetime
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    django.setup()
    import detective_app.models as detective_db
    try:
        for idx, column_name in enumerate(column_names):
            info = detective_db.FnGuideDailySnapShot.objects.update_or_create(rpt_nm=caption,
                                                                              rpt_tp='',
                                                                              crp_cd=crp_cd,
                                                                              crp_nm=crp_nm,
                                                                              disc_date=datetime.now().strftime(
                                                                                  '%Y-%m-%d'),
                                                                              column_nm=column_name,
                                                                              key=key,
                                                                              defaults={
                                                                                  'value': None
                                                                                  if not is_float(data_list[idx])
                                                                                  else float(
                                                                                      data_list[idx].replace(',', '')),
                                                                                  'value_rmk': ''
                                                                                  if is_float(data_list[idx])
                                                                                  else data_list[idx],
                                                                              }
                                                                              )
            # print(key, column_name, data_list[idx])
        # print("[%s][%s][%s] %s information stored successfully" % (caption, crp_cd, crp_nm, key))
        # print("[%s][%s][%s] information stored successfully" % (report_name, crp_cd, crp_nm))
    except Exception as e:
        print('[Error on DailySnapShotDataStore]\n', '*' * 50, e)


def SnapShotDataStore(report_name, crp_cd, crp_nm, categorizing, column_names, key, data_list):
    import sys
    import os
    import django
    # sys.path.append(r'D:\Waver\MainBoard')
    # sys.path.append(r'D:\Waver\MainBoard\MainBoard')
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    try:
        for idx, column_name in enumerate(column_names[1:]):

            period_info = column_name.split('/')
            f_p_e = 'F'
            if len(period_info) < 2:
                continue
            elif len(period_info) == 2 and len(period_info[1]) > 2:
                if '(E)' in period_info[1]:
                    f_p_e = 'E'
                    period_info[1] = period_info[1].replace('(E)', '')
                elif '(P)' in period_info[1]:
                    f_p_e = 'P'
                    period_info[1] = period_info[1].replace('(P)', '')
                # print(period_info[1])
            # print(key, column_name, data_list[idx])
            # print(report_name, crp_cd, crp_nm, categorizing, period_info[0], period_info[1])
            #       str(int(period_info[1])/3)[0]+'Q', key, data_list[idx])
            info = detective_db.FnGuideSnapShot.objects.update_or_create(rpt_nm=report_name,
                                                                         rpt_tp=column_names[0],
                                                                         crp_cd=crp_cd,
                                                                         crp_nm=crp_nm,
                                                                         disc_year=period_info[0],
                                                                         disc_month=period_info[1],
                                                                         disc_quarter=int(period_info[1]) / 3,
                                                                         disc_categorizing=categorizing,
                                                                         accnt_nm=key,
                                                                         defaults={
                                                                             'accnt_cd': '',
                                                                             'fix_or_prov_or_estm': f_p_e,
                                                                             'value': None
                                                                             if not is_float(data_list[idx])
                                                                             else float(
                                                                                 data_list[idx].replace(',', '')),
                                                                             'rmk': ''
                                                                             if is_float(data_list[idx])
                                                                             else data_list[idx],
                                                                         }
                                                                         )

        # print("[%s][%s][%s] %s information stored successfully" % (report_name, crp_cd, crp_nm, key))
        # print("[%s][%s][%s] information stored successfully" % (report_name, crp_cd, crp_nm))
    except Exception as e:
        print('[Error on SnapShotDataStore]\n', '*' * 50, e)


def FinancialReportDataStore(report_name, crp_cd, crp_nm, categorizing, column_names, key, data_list):
    import sys
    import os
    import django
    # sys.path.append(r'D:\Waver\MainBoard')
    # sys.path.append(r'D:\Waver\MainBoard\MainBoard')
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    try:
        for idx, column_name in enumerate(column_names[1:]):
            period_info = column_name.split('/')
            f_p_e = 'F'
            if len(period_info) < 2:
                continue
            elif len(period_info) == 2 and len(period_info[1]) > 2:
                if '(E)' in period_info[1]:
                    f_p_e = 'E'
                    period_info[1] = period_info[1].replace('(E)', '')
                elif '(P)' in period_info[1]:
                    f_p_e = 'P'
                    period_info[1] = period_info[1].replace('(P)', '')

            # print(report_name, crp_cd, crp_nm, categorizing, period_info[0], period_info[1],
            #       str(int(period_info[1])/3)[0]+'Q', key, data_list[idx])
            info = detective_db.FnGuideFinancialReport.objects.update_or_create(rpt_nm=report_name,
                                                                                rpt_tp=column_names[0],
                                                                                crp_cd=crp_cd,
                                                                                crp_nm=crp_nm,
                                                                                disc_year=period_info[0],
                                                                                disc_month=period_info[1],
                                                                                disc_quarter=int(period_info[1]) / 3,
                                                                                disc_categorizing=categorizing,
                                                                                accnt_nm=key,
                                                                                defaults={
                                                                                    'accnt_cd': '',
                                                                                    'fix_or_prov_or_estm': f_p_e,
                                                                                    'value': None
                                                                                    if not is_float(data_list[idx])
                                                                                    else float(
                                                                                        data_list[idx].replace(',',
                                                                                                               '')),
                                                                                    'rmk': ''
                                                                                    if is_float(data_list[idx])
                                                                                    else data_list[idx],
                                                                                }
                                                                                )

        # print("[%s][%s][%s] %s information stored successfully" % (report_name, crp_cd, crp_nm, key))
        # print("[%s][%s][%s] information stored successfully" % (report_name, crp_cd, crp_nm))
    except Exception as e:
        print('[Error on FinancialReportDataStore]\n', '*' * 50, e)


def static_parse_table(divs, itemcode, itemname):
    for d in divs:
        if len(d.attrs) > 0 and 'class' in d.attrs.keys() and d.attrs['class'] in [['ul_col2wrap', 'pd_t25']]:
            column_name = []
            column_data = []
            categorizing = None
            data_information = {}
            report_type = None
            report_name = d.find('div').find('div').find('div').get_text().replace('\n', '')
            if report_name.find('3') > 0:
                categorizing = 'QUARTERLY'
            else:
                categorizing = 'YEARLY'
            for th in d.table.thead.find_all('th'):
                # print(th.get_text())
                if th.get_text().find('IFRS') > -1 or th.get_text().find('GAAP') > -1:
                    report_type = th.get_text()
                    continue
                else:
                    column_name.append(th.get_text())

            for tr in d.table.tbody.find_all('tr'):
                data_header = ''
                if tr.attrs['class'] == ['tbody_tit']:  # 표 이름은 저장하지 않음
                    continue
                elif 'acd_dep2_sub' in tr.attrs['class']:  # 하위의 BackData 는 저장하지 않음
                    # continue
                    if len(tr.th.div.find_all('dl')) > 0:
                        print(tr.th.div.dl.dt.get_text())
                    else:
                        print(tr.th.div.get_text())
                    # print(tr.th)
                elif 'acd_dep_start_close' in tr.attrs['class']:
                    data_header = tr.th.div.div.dl.dt.get_text()
                    column_data = []
                    for td in tr.find_all('td'):
                        if len(td.find_all('span')) > 0:
                            column_data.append(td.span.get_text())
                        else:
                            column_data.append(td.get_text())
                data_information[data_header] = column_data
            print(report_name, column_name)
            for dh in data_information.keys():
                print(dh, data_information[dh])
                # FinancialRatioDataStore(report_name, report_type, itemcode, itemname, categorizing, column_name, dh, data_information[dh])
            print('\n\n')


def is_float(s):
    try:
        float(s.replace(',', ''))
        return True
    except ValueError:
        return False


def get_table_contents(soup, structure):
    retList = []
    if soup:
        for tag in soup.select(structure):
            if tag.div and tag.div.dl and tag.div.dl.dt:
                if '(E) : Estimate' == tag.div.dl.dt.text.replace(u'\xa0', '').replace('\n', '').replace('  ',
                                                                                                         '').replace(
                        '   ', '').strip():
                    retList.append(
                        tag.div.span.text.replace(u'\xa0', '').replace('\n', '').replace('  ', '').replace('   ',
                                                                                                           '').strip())
                elif '(P) : Provisional' == tag.div.dl.dt.text.replace(u'\xa0', '').replace('\n', '').replace('  ',
                                                                                                              '').replace(
                        '   ', '').strip():
                    retList.append(
                        tag.div.span.text.replace(u'\xa0', '').replace('\n', '').replace('  ', '').replace('   ',
                                                                                                           '').strip())
                else:
                    retList.append(
                        tag.div.dl.dt.text.replace(u'\xa0', '').replace('\n', '').replace('  ', '').replace('   ',
                                                                                                            '').strip())
            elif tag.a:
                retList.append('%s(%s)' % (tag.a.text, tag.a['href']))
                continue
            if tag.div and tag.div.dl and tag.div.dl.dd:
                # print('[Continue]', tag.div.dl.dd)
                continue
            if tag.text.replace(u'\xa0', '').replace('\n', '').replace('  ', '').replace('   ', '').strip() == '헤더' \
                or tag.text.replace(u'\xa0', '').replace('\n', '').replace('  ', '').replace('   ', '').strip() == '내용':
                continue
            retList.append(tag.text.replace(u'\xa0', '').replace('\n', '').replace('  ', '').replace('   ', '').strip())
    return retList


def select_by_attr(soup, tagname, attr, condition, all=None):
    retTag = None
    if all:
        if attr == 'id':
            retTag = soup.find_all(tagname, {"id": condition})
        elif attr == 'class':
            retTag = soup.find_all(tagname, {"class": condition})
        elif attr == 'style':
            retTag = soup.find_all(tagname, {"style": condition})
        elif attr == 'scope':
            retTag = soup.find_all(tagname, {"scope": condition})
        elif attr == 'href':
            if condition:
                retTag = soup.find_all(tagname, {"href": condition})
            else:
                retTag = soup.find_all(tagname, href=True)
        else:
            pass
    else:
        if attr == 'id':
            retTag = soup.find(tagname, {"id": condition})
        elif attr == 'class':
            retTag = soup.find(tagname, {"class": condition})
        elif attr == 'style':
            retTag = soup.find(tagname, {"style": condition})
        elif attr == 'scope':
            retTag = soup.find(tagname, {"scope": condition})
        elif attr == 'href':
            retTag = soup.find(tagname, {"href": condition})
        else:
            pass
    return retTag


def setting(header, items, datas):
    retHeader = []
    retKey = []
    retValue = []
    try:
        if len(datas) < len(header) or len(datas) < len(items):
            # print("입력할 데이터 없음!!!")
            pass
        elif len(header) == 0:
            # print(
            #     "::::::::::::::::::::::::::::::::::::::len(header) == 0::::::::::::::::::::::::::::::::::::::::::::::::")
            for idx, item in enumerate(items):
                prev_column = ''
                tmpHeader = []
                tmpData = []
                if item.find('/') > -1:  # 한 컬럼에 여러개의 값이 있는 경우
                    if item.find('(') > -1:  # 여러개의 컬럼의 괄호로 묶인 공통인자가 있는 경우
                        prev_column = item[:item.find('(')].strip().replace('  ', '').replace('   ', '')
                        tmpHeader = [(prev_column + '-' + i.replace(' ', '')) for i in
                                     item[item.find('(') + 1:item.find(')')].strip().replace('  ', '').replace('   ',
                                                                                                               '').split(
                                         '/')]
                    elif item.find('.') > -1:  # 여러개의 컬럼의 마침표로 분리된 공통인자가 있는 경우
                        prev_column = item[:item.find('.')]
                        tmpHeader = [(prev_column + '-' + i.replace(' ', '')) for i in
                                     item[item.find('.') + 1:].strip().replace('  ', '').replace('   ', '').split('/')]
                    else:  # 공통인자 없이 서로 다른 두개의 값이 / 로 묶인 컬럼인 경우
                        tmpHeader = item.strip().replace('  ', '').replace('   ', '').split('/')
                    tmpData = datas[idx].strip().replace('  ', '').replace('   ', '').split('/')
                    retHeader.extend(tmpHeader)
                    retValue.extend(tmpData)
                else:
                    retHeader.append(item.strip().replace('  ', '').replace('   ', ''))
                    retValue.append(datas[idx].strip().replace('  ', '').replace('   ', ''))
        elif len(items) == 0:
            # print(
            #     ":::::::::::::::::::::::::::::::::::::::len(items) == 0::::::::::::::::::::::::::::::::::::::::::::::::")
            for idx, head in enumerate(header):
                retHeader.append(head.replace('  ', '').replace('   ', ''))
                retValue.append(datas[idx].replace('  ', '').replace('   ', ''))
        else:
            # print("::::::::::::::::::::::::::::::::::::::::::::else:::::::::::::::::::::::::::::::::::::::::::::::::")
            for idx, head in enumerate(header[1:]):
                retHeader.append(head.replace('  ', '').replace('   ', ''))
            retKey = items

            for i in range(len(retKey)):
                tmpData = []
                for j in range(len(retHeader)):
                    # print(i, j, len(retHeader)*i+j)
                    tmpData.append(datas[len(retHeader) * i + j].replace('  ', '').replace('   ', ''))
                retValue.append(tmpData)
    except Exception as e:
        print(e)
        # print(header, items, datas)

    return retHeader, retKey, retValue


def FinancialRatioDataStore(report_name, report_type, crp_cd, crp_nm, categorizing, column_names, key, data_list):
    import sys
    import os
    import django
    # sys.path.append(r'D:\Waver\MainBoard')
    # sys.path.append(r'D:\Waver\MainBoard\MainBoard')
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    try:
        for idx, column_name in enumerate(column_names):
            period_info = column_name.split('/')
            f_p_e = 'F'
            if len(period_info) < 2:
                continue
            elif len(period_info) == 2 and len(period_info[1]) > 2:
                if '(E)' in period_info[1]:
                    f_p_e = 'E'
                    period_info[1] = period_info[1].replace('(E)', '')
                elif '(P)' in period_info[1]:
                    f_p_e = 'P'
                    period_info[1] = period_info[1].replace('(P)', '')
            # print(report_name, crp_cd, crp_nm, categorizing, period_info[0], period_info[1],
            #       str(int(period_info[1])/3)[0]+'Q', key, data_list[idx])
            info = detective_db.FnGuideFinancialRatio.objects.update_or_create(rpt_nm=report_name,
                                                                               rpt_tp=report_type,
                                                                               crp_cd=crp_cd,
                                                                               crp_nm=crp_nm,
                                                                               disc_year=period_info[0],
                                                                               disc_month=period_info[1],
                                                                               disc_quarter=int(period_info[1]) / 3,
                                                                               disc_categorizing=categorizing,
                                                                               ratio_nm=key,
                                                                               defaults={
                                                                                   'ratio_cd': '',
                                                                                   'fix_or_prov_or_estm': f_p_e,
                                                                                   'value': None
                                                                                   if not is_float(data_list[idx])
                                                                                   else float(
                                                                                       data_list[idx].replace(',', '')),
                                                                                   'rmk': ''
                                                                                   if is_float(data_list[idx])
                                                                                   else data_list[idx],
                                                                               }
                                                                               )

        # print("[%s][%s][%s] %s information stored successfully" % (report_name, crp_cd, crp_nm, key))
        # print("[%s][%s][%s] information stored successfully" % (report_name, crp_cd, crp_nm))
    except Exception as e:
        print('[Error on FinancialRatioDataStore]\n', '*' * 50, e)


def parse_html_table(table):
    n_columns = 0
    n_rows = 0
    column_names = []

    # Find number of rows and columns
    # we also find the column titles if we can
    for row in table.find_all('tr'):

        # Determine the number of rows in the table
        td_tags = row.find_all('td')
        if len(td_tags) > 0:
            n_rows += 1
            if n_columns == 0:
                # Set the number of columns for our table
                n_columns = len(td_tags)

        # Handle column names if we find them
        th_tags = row.find_all('th')
        if len(th_tags) > 0 and len(column_names) == 0:
            for th in th_tags:
                column_names.append(th.get_text())

    # Safeguard on Column Titles
    print(column_names, n_columns)
    if len(column_names) > 0 and len(column_names) != n_columns:
        raise Exception("Column titles do not match the number of columns")

    columns = column_names if len(column_names) > 0 else range(0, n_columns)
    df = pd.DataFrame(columns=columns,
                      index=range(0, n_rows))
    row_marker = 0
    for row in table.find_all('tr'):
        column_marker = 0
        columns = row.find_all('td')
        for column in columns:
            df.iat[row_marker, column_marker] = column.get_text()
            column_marker += 1
        if len(columns) > 0:
            row_marker += 1

    # Convert to float if possible
    for col in df:
        try:
            df[col] = df[col].astype(float)
        except ValueError:
            pass

    return df


def request(driver):
    s = requests.Session()
    # cookies = driver.get_cookies()
    # for cookie in cookies:
    #     s.cookies.set(cookie['name'], cookie['value'])
    return s


def httpRequestWithDriver(driver, url, data, method='POST'):
    try:
        req = request(driver)
        if method == 'POST':
            r = req.post(url, data)
            return r.content
        else:
            r = req.get(url, params=data)
            return r.content
    except Exception as e:
        print(e)


def httpRequest(url, data, method='POST', header=None):
    try:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36 Edg/84.0.522.49",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ko,en;q=0.9,en-US;q=0.8",
        }
        if header is None:
            pass
        else:
            headers = header
        if data is None:
            r = requests.get(url, headers=headers)
            return r.content
        else:
            if method == 'POST':
                r = requests.post(url, headers=headers, data=data)
                # print(method, 'httpRequest error status', r.raise_for_status(), data['gicode'])
                return r.content
            else:
                r = requests.get(url, headers=headers, params=data)
                # print(method, 'httpRequest error status', r.raise_for_status(), data['gicode'])
                return r.content
    except Exception as e:
        print(e)
        return None


def getUSFinanceDataNotUse(cmd=None):
    import sys
    import os
    import django
    import edgar
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    # workDir = r'%s'

    yyyymmdd = str(datetime.now())[:10]
    # url = "http://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp"
    reportType = {
        # 101: 'snapshotUS',
        103: 'financeReportUS'
        # 104: 'financeRatioUS'
    }  # 101 : snapshot, 103 : financeReport, 104 : financeRatio
    # urlInfo = {
    #     101: 'http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp',
    #     103: 'http://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp',
    #     104: 'http://comp.fnguide.com/SVO2/ASP/SVD_FinanceRatio.asp'
    # }
    # url = 'https://finance.yahoo.com/quote/%s/financials?p=%s'

    # stockInfo = detective_db.USStocks.objects.filter(listing='Y')
    stockInfo = detective_db.USStocks.objects.filter(security='Apple Inc.', listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(code='005930', listing='Y')
    for key in reportType.keys():
        # print(cmd, cmd and key != cmd)
        if cmd and key != cmd:
            continue
        workDir = r'%s\%s\%s' % (path, reportType[key], yyyymmdd)
        # workDir = r'D:\Waver\detective\reports\%s\%s' % (reportType[key], yyyymmdd)
        if not os.path.exists(workDir):
            os.makedirs(workDir)
        for s in stockInfo:
            if fileCheck(workDir, s.cik, s.security.replace(' ', '_'), reportType[key]):
                print('[%s][%s][%s] File is already exist. Skipped...' % (reportType[key], s.cik, s.security))
                continue
            print('[%s][%s][%s] File is on process...' % (reportType[key], s.cik, s.security))
            company = edgar.Company(s.security, s.cik)
            tree = company.getAllFilings(filingType="10-K")
            docs = edgar.getXMLDocuments(tree, noOfDocuments=1)
            # print(docs)
            for xml in docs:
                saveFile(workDir, s.security.replace(' ', '_'), s.cik, reportType[key], xml, 'w')


def getFinanceDataTest(cmd=None):
    import sys
    import os
    import django
    from multiprocessing import Pool
    from functools import partial
    getConfig()
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    # CHROMEDRIVER_PATH = chrome_path
    options = Options()
    options.headless = True
    # driver = webdriver.Chrome(CHROMEDRIVER_PATH, chrome_options=options)
    # driver.implicitly_wait(3)

    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    from django.db.models import Q
    global marketTxt

    yyyymmdd = str(datetime.now())[:10]
    # yyyymmdd = '2020-08-04'
    url = "http://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp"
    reportType = {
        101: 'snapshot',
        103: 'financeReport',
        104: 'financeRatio',
        108: 'consensus',
        200: 'ROE',
        300: 'GlobalCompanyProfile',
        301: 'GlobalFinancialSummary',

    }  # 101 : snapshot, 103 : financeReport, 104 : financeRatio
    urlInfo = {
        101: 'http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp',
        103: 'http://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp',
        104: 'http://comp.fnguide.com/SVO2/ASP/SVD_FinanceRatio.asp',
        108: 'http://comp.fnguide.com/SVO2/ASP/SVD_Consensus.asp',
        200: 'http://comp.fnguide.com/SVO2/json/chart/01_04/chart_A{}_D.json',
        300: 'https://api.nasdaq.com/api/company/{}/company-profile|https://api.nasdaq.com/api/quote/{}/info?assetclass=stocks',
        301: 'http://compglobal.wisereport.co.kr/miraeassetdaewoo/company/get_snap_financial_summary?ticker={}-US&freq_typ=A&en={}'
    }

    fileInfo = {
        101: 'html',
        103: 'html',
        104: 'html',
        108: 'html',
        200: 'json',
        300: 'json',
        301: 'json',
    }
    # 'http://compglobal.wisereport.co.kr/miraeassetdaewoo/Company/Snap?cmp_cd={}-US&en={}'

    data = {
        'pGB': 1,
        'gicode': '',
        'cID': '',
        'MenuYn': 'Y',
        'ReportGB': 'D',  # D: 연결, B: 별도
        'NewMenuID': 0,
        'stkGb': 701,
    }

    xmlString = ''
    result = None

    try:
        for key in reportType.keys():
            # print(cmd, cmd and key != cmd)
            if cmd and key != cmd:
                continue
            if cmd >= 300:
                stockInfo = detective_db.USNasdaqStocks.objects.filter(ticker='TLF', listing='Y', fnguide_exist='Y')
            else:
                stockInfo = detective_db.Stocks.objects.filter(code='009160', listing='Y')
            #     jobtype = reportType[key]
            #     url = urlInfo[key]
            #     # getUSFinanceData(jobtype, url)
            #     getUSFinanceDataStandalone(jobtype, url)
            #     continue

            # stockInfo = detective_db.Stocks.objects.filter(code='005930', listing='Y')
            workDir = r'%s\%s\%s' % (path, reportType[key], yyyymmdd)
            if not os.path.exists(workDir):
                os.makedirs(workDir)

            data['NewMenuID'] = key
            # ext = 'json' if cmd == 200 else 'html'
            # 신규코드(multiprocessing) 시작
            if cmd == 200:
                agents = 2
                j = jobs()
                j.filetype = fileInfo[key]
                j.workDir = workDir
                j.jobtype = reportType[key]
                j.url = urlInfo[key]
                s = stockInfo.values()
                func = partial(getTargetFileTest, j)
                with Pool(processes=agents) as pool:
                    result = pool.map(func, s)
            elif cmd == 300:
                agents = 1
                j = jobs()
                j.filetype = fileInfo[key]
                j.workDir = workDir
                j.jobtype = reportType[key]
                j.url = urlInfo[key]
                s = stockInfo.values()
                func = partial(getTargetFileTest, j)
                with Pool(processes=agents) as pool:
                    result = pool.map(func, s)

                for r in result:
                    retArr = r.split('|')
                    if len(retArr) < 3: continue

                    if retArr[2] != '' and retArr[0] == 'GlobalCompanyProfile':
                        USStockMarketTextUpdateAdvcd(retArr[1], retArr[2], retArr[3], retArr[4], retArr[5],
                                                     retArr[6], retArr[7], retArr[8], retArr[9])
                        # 0 j.jobtype,
                        # 1 ticker,
                        # 2 category_code,
                        # 3 category_name,
                        # 4 category_detail,
                        # 5 tel,
                        # 6 address,
                        # 7 location,
                        # 8 description,
                        # 9 issued_shares
                if len(stockInfo) != len(result):
                    print(
                        "Total target stocks : {}\n requested stocks : {}\nPlease check out the process.\nTerminating this program.".format(
                            len(stockInfo), len(result)))
                    exit(0)
            elif cmd == 301:
                agents = 3
                j = jobs()
                j.filetype = fileInfo[key]
                j.workDir = workDir
                j.jobtype = reportType[key]
                j.url = urlInfo[key]
                s = stockInfo.values()
                func = partial(getTargetFileTest, j)
                with Pool(processes=agents) as pool:
                    result = pool.map(func, s)
            else:
                agents = 3
                j = jobs()
                j.filetype = fileInfo[key]
                j.workDir = workDir
                j.jobtype = reportType[key]
                j.url = urlInfo[key]
                j.reqdata = data
                # j.driver = driver
                s = stockInfo.values()
                # j.driver = cc.ChromeDriver()
                func = partial(getTargetFileTest, j)
                with Pool(processes=agents) as pool:
                    result = pool.map(func, s)

                for r in result:
                    retArr = r.split('|')
                    if len(retArr) < 3: continue
                    if retArr[3] != '' and retArr[0] == 'snapshot':
                        StockMarketTextUpdate(retArr[1], retArr[3].replace('\xa0', ' '), retArr[4].replace('\xa0', ' '),
                                              retArr[5].replace('\xa0', ' '))
                if len(stockInfo) != len(result):
                    print(
                        "Total target stocks : {}\n requested stocks : {}\nPlease check out the process.\nTerminating this program.".format(
                            len(stockInfo), len(result)))
                    exit(0)
        print("FnGuideDataCollection job finished")
    except Exception as e:
        errmsg = '{}\n{}'.format('getFinanceData', str(e))
        err_messeage_to_telegram(errmsg)


def getStocksByMarketCapitalRank():
    import sys
    import os
    import django
    import json
    getConfig()

    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db

    url = 'http://compglobal.wisereport.co.kr/Screener/GetRankIdx?iso_typ=13&mkt=US&sec=WI000&condType=M&baseyear=CPD&ordItem=5&ordDirect=D&cap_chk=0&curpage=1&perpage=100&curr=USD&en={}'
    header = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36 Edg/84.0.522.49",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "ko,en;q=0.9,en-US;q=0.8",
    }
    jj = json.loads(httpRequest(url.format(generateEncCode()), None, 'GET', header).decode('utf-8'))
    tickers = []
    category = []
    industry = []
    # print(jj['header'])
    for d in jj['content']:
        tickers.append(d['TICKER'].replace("-US", ""))
    print(tickers)
    for ticker in tickers:
        stock = detective_db.USNasdaqStocks.objects.filter(ticker=ticker)
        for s in stock:
            print(s.ticker, '\t', s.security, '\t', s.category_name, '\t', s.category_detail)
            industry.append(s.category_name)
            category.append(s.category_detail)
    print(list(set(industry)))
    print(list(set(category)))

if __name__ == '__main__':
    # print(getUSFinanceData())
    # getFinanceData(101)
    # getFinanceData(200)
    # getFinanceData(103)
    # getFinanceData(108)
    getFinanceDataTest(101)
    # getUSFinanceData()
    # print(generateEncCode())
    # getStocksByMarketCapitalRank()
    # url = 'https://api.nasdaq.com/api/company/ainv/company-profile'
    # header = {
    #     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36 Edg/84.0.522.49",
    #     "Accept-Encoding": "gzip, deflate",
    #     "Accept-Language": "ko,en;q=0.9,en-US;q=0.8",
    # }
    # print(httpRequest(url, None, 'GET', header))
    # url = 'http://compglobal.wisereport.co.kr/Screener/GetRankIdx?iso_typ=13&mkt=US&sec=WI000&condType=M&baseyear=CPD&ordItem=5&ordDirect=D&cap_chk=0&curpage=1&perpage=100&curr=USD&en=57304082434525'
    # header = {
    #     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36 Edg/84.0.522.49",
    #     "Accept-Encoding": "gzip, deflate",
    #     "Accept-Language": "ko,en;q=0.9,en-US;q=0.8",
    # }
    # print(httpRequest(url, None, 'GET', header))
