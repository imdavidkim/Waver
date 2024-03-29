# -*- coding: utf-8 -*-

# import pandas as pd
# import numpy as np
# import requests
# from io import BytesIO
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
# import pprint
# import csv
# import xmltodict
import os
import detective.fnguide_collector as fnguide
import detective.messenger as msgr
from detective.messenger import err_messeage_to_telegram

DEBUG = True

import logging
global logger
logfile = 'detector'
if not os.path.exists('./logs'):
    os.makedirs('./logs')
now = datetime.now().strftime("%Y%m%d%H%M%S")

logger = logging.getLogger(__name__)
formatter = logging.Formatter('[%(asctime)s][%(filename)s:%(lineno)s] >> %(message)s')

streamHandler = logging.StreamHandler()
fileHandler = logging.FileHandler("./logs/{}_{}.log".format(logfile, now))

streamHandler.setFormatter(formatter)
fileHandler.setFormatter(formatter)

logger.addHandler(streamHandler)
logger.addHandler(fileHandler)
logger.setLevel(level=logging.INFO)

def getConfig():
    import configparser
    global path, filename, yyyymmdd, django_path, main_path, font_path
    config = configparser.ConfigParser()
    config.read('config.ini')
    path = config['COMMON']['REPORT_PATH']
    proj_path = config['COMMON']['PROJECT_PATH']
    font_path = config['COMMON']['FONT_PATH']
    django_path = proj_path + r'\MainBoard'
    main_path = django_path + r'\MainBoard'
    filename = r'\financeData_{}_{}_{}.{}'
    yyyymmdd = str(datetime.now())[:10]
    # yyyymmdd = '2021-08-03'
    # print(path, filename)


def get_soup_from_file(report_type, yyyymmdd, crp_nm, crp_cd, ext):
    getConfig()
    reportType = {
        'snapshot': 101,
        'financeReport': 103,
        'financeRatio': 104,
        'consensus': 108,
        'ROE': 200,
        'GlobalCompanyProfile': 300,
        'GlobalFinancialSummary': 301,
        'GlobalConsensus': 302,
        'GlobalFinancialStatement': 303
    }
    try:
        full_path = path + r'\{}\{}'.format(report_type, yyyymmdd) + filename.format(crp_nm, crp_cd, report_type, ext)
        with open(full_path, 'rb') as obj:
            if ext == 'json':
                soup = json.loads(obj.read())
            else:
                soup = BeautifulSoup(obj, 'lxml')
    except Exception as e:
        try:
            fnguide.getFinanceDataRetry(reportType[report_type], crp_cd)
            full_path = path + r'\{}\{}'.format(report_type, yyyymmdd) + filename.format(crp_nm, crp_cd, report_type,
                                                                                         ext)
            with open(full_path, 'rb') as obj:
                if ext == 'json':
                    soup = json.loads(obj.read())
                else:
                    soup = BeautifulSoup(obj, 'lxml')
        except Exception as ee:
            soup = None
    return soup


def dictfetchall(cursor):
    # "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def get_dateDict():
    import sys
    import os
    import django
    # sys.path.append(r'E:\Github\Waver\MainBoard')
    # sys.path.append(r'E:\Github\Waver\MainBoard\MainBoard')
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    from django.db import connection
    cursor = connection.cursor()
    sql = "SELECT strftime('%Y','now') as yyyy, strftime('%m','now') as mm, strftime('%d','now') as dd, strftime('%Y-%m-%d','now') as yyyymmdd"
    cursor.execute(sql)
    return dictfetchall(cursor)[0]


def new_get_dateDict():
    retDict = {}
    yyyymmdd = str(datetime.now())[:10]
    before730date = datetime.strptime(yyyymmdd, "%Y-%m-%d") - timedelta(days=730)
    retDict['yyyy'] = yyyymmdd[:4]
    retDict['mm'] = yyyymmdd[5:7]
    retDict['dd'] = yyyymmdd[-2:]
    retDict['yyyy2'] = before730date.strftime("%Y%m%d")
    # print(retDict)
    return retDict


def get_max_date_on_dailysnapshot(crp_cd):
    import sys
    import os
    import django
    # sys.path.append(r'E:\Github\Waver\MainBoard')
    # sys.path.append(r'E:\Github\Waver\MainBoard\MainBoard')
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    from django.db import connection
    cursor = connection.cursor()
    sql = """select max(disc_date) as disc_date from detective_app_fnguidedailysnapshot
            where rpt_nm = '시세현황1'
            and rpt_tp = ''
            and crp_cd = '{}'""".format(crp_cd)
    cursor.execute(sql)
    return dictfetchall(cursor)[0]


def get_high_ranked_stock():
    import sys
    import os
    import django
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    try:
        from django.db import connection
        cursor = connection.cursor()
        sql = """select t.code, t.name, t.curr, t.last_price, t.price_gap, t.target_price, t.target_price2, t.return_on_equity, t.ratio, t.ratio2, (t.ratio + t.ratio2) / 2 as average_ratio  from (
                    select code, name, curr, last_price, price_gap, target_price, target_price2, return_on_equity, ratio, target_price2/last_price*100 as ratio2 from detective_app_targetstocks
                    where ratio > 100
                    --and return_on_equity > 14
                    and valuation_date = '{}'
                    order by ratio2 desc
                    limit 30) as t
                 --where last_price > 14000
                 --and ratio2 > 100
                 order by t.ratio desc""".format(yyyymmdd)
        cursor.execute(sql)
        retStr = ''
        for idx, d in enumerate(dictfetchall(cursor)):
            retStr += '{}. [{}]{}({})\n\t{} => {}[{}%]\n'.format(
                idx + 1, d['code'], d['name'], d['price_gap'], format(int(d['last_price']), ','),
                format(int(d['target_price']), ','),
                str(round(int(d['target_price']) / int(d['last_price']) * 100 - 100, 0)))
        return retStr
    except Exception as e:
        errmsg = '{}\n{}'.format('get_high_ranked_stock', str(e))
        err_messeage_to_telegram(errmsg)


def get_nasdaq_high_ranked_stock():
    import sys
    import os
    import django
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    try:
        from django.db import connection
        cursor = connection.cursor()
        sql = """select code, name, last_price, round(target_price, 2) 'target_price', price_gap, ratio, return_on_equity, return_on_sales from detective_app_ustargetstocks
                where valuation_date = '{}'
                and ratio > 100
                order by ratio desc""".format(yyyymmdd)
        cursor.execute(sql)
        retStr = ''
        for idx, d in enumerate(dictfetchall(cursor)):
            retStr += '{}. [{}]{}({})\n\t{} => {}[{}%]\n'.format(
                idx + 1, d['code'], d['name'], d['price_gap'], format(d['last_price'], ','),
                format(d['target_price'], ','), str(round((d['target_price']) / (d['last_price']) * 100 - 100, 1)))
        return retStr
    except Exception as e:
        errmsg = '{}\n{}'.format('get_nasdaq_high_ranked_stock', str(e))
        err_messeage_to_telegram(errmsg)


def send_hidden_pearl_message(d):
    from detective.naver_api import getNaverPrice
    import sys
    import os
    import django
    import matplotlib.pyplot as plt
    from matplotlib import rc, font_manager, style
    from detective.messenger import messeage_to_telegram
    import numpy as np
    import pandas as pd
    getConfig()

    try:
        font_name = font_manager.FontProperties(fname=font_path).get_name()
        # font 설정

        plt.close('all')
        txt = ""
        for group in d.keys():
            for idx, stock_code in enumerate(d[group].keys()):
                plt.rc('font', family=font_name)
                txt = "[{}그룹]".format(group)
                txt += "\n{}. [{}]{}".format(idx + 1, stock_code, d[group][stock_code]["사명"])
                txt += "\n  - 시가총액:{}".format(d[group][stock_code]["시가총액"])
                txt += "\n  - 업종:{}".format(d[group][stock_code]["업종"])
                txt += "\n  - 최근매출액영업이익률:{}".format(d[group][stock_code]["최근매출액영업이익률"])
                txt += "\n  - EPS:{}".format(d[group][stock_code]["EPS"])
                txt += "\n  - 추정EPS:{}".format(d[group][stock_code]["추정EPS"])
                txt += "\n  - 괴리율:{}".format(d[group][stock_code]["괴리율"])
                txt += "\n  - 현재가:{}".format(d[group][stock_code]["현재가"])
                txt += "\n  - 예상주가:{}\n".format(d[group][stock_code]["예상주가"])
                messeage_to_telegram(txt, dbg=True)
                fig = plt.figure(clear=True)
                url_type = 'STOCK'
                price = getNaverPrice(url_type, stock_code, 36)
                SP = fig.add_subplot(1, 1, 1)
                SP.plot(price, label="{}({})".format(d[group][stock_code]["사명"], stock_code))
                SP.legend(loc='upper center')
                plt.xticks(rotation=45)
                img_path = r'{}\{}\{}'.format(path, 'StockPriceTrace', yyyymmdd)
                # print(img_path)
                if not os.path.exists(img_path):
                    os.makedirs(img_path)
                plt.savefig(img_path + '\\{}_{}.png'.format(d[group][stock_code]["사명"], stock_code))
                # plt.show()
                msgr.img_messeage_to_telegram2(img_path + '\\{}_{}.png'.format(d[group][stock_code]["사명"], stock_code),
                                               dbg=True)
                fig = None
                plt.close('all')
                if d[group][stock_code]['FCF'] is None or d[group][stock_code]['OCF'] is None or d[group][stock_code][
                    'EARN'] is None or d[group][stock_code]['PL'] is None:
                    continue
                key = np.array(list(d[group][stock_code]['FCF'].keys()))
                value1 = np.array(list(d[group][stock_code]['FCF'].values())) / 100000000
                value2 = np.array(list(d[group][stock_code]['OCF'].values())) / 100000000
                value3 = np.array(list(d[group][stock_code]['EARN'].values())) / 100000000
                value4 = np.array(list(d[group][stock_code]['PL'].values())) / 100000000

                df = pd.DataFrame(data=dict(nQ=key, FCF=np.rint(value1), OCF=np.rint(value2), EARN=np.rint(value3),
                                            PL=np.rint(value4)))
                plt.title("{} {}({})".format(d[group][stock_code]["최종보고서"], d[group][stock_code]["사명"], stock_code))
                plt.style.use('seaborn-dark')

                ax = plt.subplot()
                data_fcf = ax.plot(key, np.rint(value1), color="green", linestyle='-', marker='o', label="FCF")
                data_ocf = ax.plot(key, np.rint(value2), color="red", linestyle='-', marker='o', label="OCF")
                data_earn = ax.plot(key, np.rint(value3), color="blue", linestyle='-', marker='o', label="EARN")
                data_pl = ax.plot(key, np.rint(value4), color="purple", linestyle='-', marker='o', label="PL")

                for k1, v1 in zip(key, np.rint(value1)):
                    ax.text(k1, v1 * 1.04, format(v1, ','), fontsize=10, horizontalalignment='center',
                            verticalalignment="bottom")
                for k1, v2 in zip(key, np.rint(value2)):
                    ax.text(k1, v2 * 1.04, format(v2, ','), fontsize=10, horizontalalignment='center',
                            verticalalignment="bottom")
                for k1, v3 in zip(key, np.rint(value3)):
                    ax.text(k1, v3 * 1.04, format(v3, ','), fontsize=10, horizontalalignment='center',
                            verticalalignment="bottom")
                for k1, v4 in zip(key, np.rint(value4)):
                    ax.text(k1, v4 * 1.04, format(v4, ','), fontsize=10, horizontalalignment='center',
                            verticalalignment="bottom")
                ax.legend()
                ax.set_ylim([min(min(value1), min(value2), min(value3), min(value4)),
                             max(map(lambda x: x[-1], [value1, value2, value3, value4])) * 1.2])
                ax.yaxis.set_ticks([])
                ax.grid(False)
                # plt.show()
                plt.savefig(img_path + '\\Cashflow_{}_{}.png'.format(d[group][stock_code]["사명"], stock_code))
                # plt.show()
                msgr.img_messeage_to_telegram2(
                    img_path + '\\Cashflow_{}_{}.png'.format(d[group][stock_code]["사명"], stock_code),
                    dbg=True)
                fig = None
                plt.close("all")
        plt = None
    except Exception as e:
        errmsg = '{}\n{}'.format('send_hidden_pearl_message', str(e))
        err_messeage_to_telegram(errmsg)
        fig = None
        plt.close('all')
        plt = None


def get_high_ranked_stock_with_closeprice():
    # from yahoofinancials import YahooFinancials
    from detective.naver_api import getNaverPrice
    import sys
    import os
    import django
    import matplotlib.pyplot as plt
    from matplotlib import rc, font_manager
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    try:
        from django.db import connection
        cursor = connection.cursor()
        sql = """select t.code, t.market_text, t.name, t.curr, t.last_price, t.target_price, t.target_price2, t.return_on_equity, t.ratio, t.ratio2, (t.ratio + t.ratio2) / 2 as average_ratio  from (
                    select s.code, s.market_text, ts.name, ts.curr, ts.last_price, ts.target_price, ts.target_price2, ts.return_on_equity, ts.ratio, ts.target_price2/ts.last_price*100 as ratio2 from detective_app_targetstocks ts, detective_app_stocks s
                    where ts.ratio > 100
                    and s.code = ts.code
                    --and return_on_equity > 14
                    and ts.valuation_date = '{}'
                    order by ratio2 desc
                    limit 30) as t
                 --where last_price > 14000
                 --and ratio2 > 100
                 order by t.ratio desc""".format(yyyymmdd)
        cursor.execute(sql)
        # retStr = ''
        fig = None
        # 폰트 경로
        # font_path = r"C:/Windows/Fonts/KoPubDotum_Pro_Light.otf"
        # 폰트 이름 얻어오기
        # font_name = font_manager.FontProperties(fname=font_path).get_name()
        # # font 설정
        # plt.rc('font', family=font_name)
        # plt.close('all')
        # plt.clf()
        for idx, d in enumerate(dictfetchall(cursor)):
            t = new_find_hidden_pearl_with_dartpipe_single(d['code'])
            send_hidden_pearl_message(t)
            # plt.rc('font', family=font_name)
            # fig = plt.figure(clear=True)
            # url_type = 'STOCK'
            # price = getNaverPrice(url_type, d['code'], 36)
            # SP = fig.add_subplot(1, 1, 1)
            # SP.plot(price, label="{}({})".format(d['name'], d['code']))
            # SP.legend(loc='upper center')
            # plt.xticks(rotation=45)
            # img_path = r'{}\{}\{}'.format(path, 'StockPriceTrace', yyyymmdd)
            # # print(img_path)
            # if not os.path.exists(img_path):
            #     os.makedirs(img_path)
            # plt.savefig(img_path + '\\{}_{}.png'.format(d['name'], d['code']))
            # # plt.show()
            # msgr.img_messeage_to_telegram(img_path + '\\{}_{}.png'.format(d['name'], d['code']))
            # fig = None
            # plt.close('all')

        plt = None
    except Exception as e:
        errmsg = '{}\n{}'.format('get_high_ranked_stock_with_closeprice', str(e))
        err_messeage_to_telegram(errmsg)
        fig = None
        plt.close('all')
        plt = None
    # todaydate = datetime.strptime(yyyymmdd, "%Y-%m-%d")
    # before30date = datetime.strptime(yyyymmdd, "%Y-%m-%d") - timedelta(days=30)
    # print(str(todaydate)[:10], str(before30date)[:10])
    # for idx, d in enumerate(dictfetchall(cursor)):
    #     dates = []
    #     prcs = []
    #     ins_ticker = '{}.KS'.format(d['code']) if d['market_text'].split("\xa0")[0].strip() == 'KSE' else '{}.KQ'.format(d['code'])
    #     print(idx, ins_ticker)
    #     instrument = YahooFinancials(ins_ticker)
    #     prices = instrument.get_historical_price_data(str(before30date)[:10], str(todaydate)[:10], "daily")
    #     if "prices" not in prices[ins_ticker].keys(): print(prices)
    #     for info in prices[ins_ticker]['prices']:
    #         dates.append(info['formatted_date'])
    #         prcs.append(info['close'])
    #     print(dates)
    #     print(prcs)

    #     retStr += '%d. {}\t{} => {}[{}%%]\n'.format(
    #         idx + 1, d['name'], format(int(d['last_price']), ','), format(int(d['target_price']), ','), str(round(int(d['target_price'])/int(d['last_price'])*100-100, 0)))
    # return retStr


def get_nasdaq_high_ranked_stock_with_closeprice():
    from yahoofinancials import YahooFinancials
    from detective.naver_api import getNaverPrice
    import sys
    import os
    import django
    import matplotlib.pyplot as plt
    from matplotlib import rc, font_manager
    import pandas as pd

    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    # yyyymmdd = '2020-08-11'
    try:
        from django.db import connection
        cursor = connection.cursor()
        sql = """select code, name, last_price, round(target_price, 2) 'target_price', price_gap, ratio, return_on_equity, return_on_sales from detective_app_ustargetstocks
                where valuation_date = '{}'
                and ratio > 100
                order by ratio desc""".format(yyyymmdd)
        cursor.execute(sql)
        # retStr = ''
        fig = None
        # 폰트 경로
        # font_path = r"C:/Windows/Fonts/KoPubDotum_Pro_Light.otf"
        # 폰트 이름 얻어오기
        font_name = font_manager.FontProperties(fname=font_path).get_name()
        # font 설정
        plt.rc('font', family=font_name)
        plt.close('all')
        # plt.clf()
        todaydate = datetime.strptime(yyyymmdd, "%Y-%m-%d")
        before180days = datetime.strptime(yyyymmdd, "%Y-%m-%d") - timedelta(days=180)
        # print(str(todaydate)[:10], str(before180days)[:10])
        for idx, d in enumerate(dictfetchall(cursor)):
            fig = plt.figure(clear=True)
            dates = []
            prcs = []
            ins_ticker = d['code']
            # print(idx, ins_ticker)
            instrument = YahooFinancials(ins_ticker)
            prices = instrument.get_historical_price_data(str(before180days)[:10], str(todaydate)[:10], "daily")
            # if "prices" not in prices[ins_ticker].keys(): print(prices)
            for info in prices[ins_ticker]['prices']:
                dates.append(datetime.strptime(info['formatted_date'], "%Y-%m-%d"))
                prcs.append(info['close'])
            price = pd.core.series.Series(prcs, dates)
            SP = fig.add_subplot(1, 1, 1)
            SP.plot(price, label="{}({})".format(d['name'], d['code']))
            SP.legend(loc='upper center')
            img_path = r'{}\{}\{}'.format(path, 'USStockPriceTrace', yyyymmdd)
            print(img_path)
            if not os.path.exists(img_path):
                os.makedirs(img_path)
            plt.savefig(img_path + '\\{}_{}.png'.format(d['name'], d['code']))
            plt.xticks(rotation=45)
            # plt.show()
            msgr.img_messeage_to_telegram(img_path + '\\{}_{}.png'.format(d['name'], d['code']))
            fig = None
            plt.close('all')
        plt = None
    except Exception as e:
        errmsg = '{}\n{}'.format('get_nasdaq_high_ranked_stock_with_closeprice', str(e))
        err_messeage_to_telegram(errmsg)
        fig = None
        plt.close('all')
        plt = None
    # todaydate = datetime.strptime(yyyymmdd, "%Y-%m-%d")
    # before30date = datetime.strptime(yyyymmdd, "%Y-%m-%d") - timedelta(days=30)
    # print(str(todaydate)[:10], str(before30date)[:10])
    # for idx, d in enumerate(dictfetchall(cursor)):
    #     dates = []
    #     prcs = []
    #     ins_ticker = '{}.KS'.format(d['code']) if d['market_text'].split("\xa0")[0].strip() == 'KSE' else '{}.KQ'.format(d['code'])
    #     print(idx, ins_ticker)
    #     instrument = YahooFinancials(ins_ticker)
    #     prices = instrument.get_historical_price_data(str(before30date)[:10], str(todaydate)[:10], "daily")
    #     if "prices" not in prices[ins_ticker].keys(): print(prices)
    #     for info in prices[ins_ticker]['prices']:
    #         dates.append(info['formatted_date'])
    #         prcs.append(info['close'])
    #     print(dates)
    #     print(prcs)

    #     retStr += '%d. {}\t{} => {}[{}%%]\n'.format(
    #         idx + 1, d['name'], format(int(d['last_price']), ','), format(int(d['target_price']), ','), str(round(int(d['target_price'])/int(d['last_price'])*100-100, 0)))
    # return retStr


def get_nasdaq_stock_graph(d):
    from yahoofinancials import YahooFinancials
    import sys
    import os
    import django
    import matplotlib.pyplot as plt
    from matplotlib import rc, font_manager, style
    from detective.messenger import messeage_to_telegram
    import pandas as pd
    import numpy as np

    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    try:
        font_name = font_manager.FontProperties(fname=font_path).get_name()
        # font 설정

        plt.close('all')
        txt = ""
        todaydate = datetime.strptime(yyyymmdd, "%Y-%m-%d")
        before180days = datetime.strptime(yyyymmdd, "%Y-%m-%d") - timedelta(days=180)
        for group in d.keys():
            for idx, stock_code in enumerate(d[group].keys()):
                # print(idx, ins_ticker)
                fig = plt.figure(clear=True)
                dates = []
                prcs = []
                instrument = YahooFinancials(stock_code)
                prices = instrument.get_historical_price_data(str(before180days)[:10], str(todaydate)[:10], "daily")
                mkt_cap = instrument.get_market_cap()
                plt.rc('font', family=font_name)
                txt = "[{}그룹]".format(group)
                txt += "\n{}. [{}]{}".format(idx + 1, stock_code, d[group][stock_code]["Name"])
                txt += "\n  - 시가총액:{}mn".format(f'{round(mkt_cap / 1000000,0):,}')
                txt += "\n  - 업종:{}".format(d[group][stock_code]["Industry"])
                txt += "\n  - 예상매출액영업이익률:{}".format(d[group][stock_code]["영업이익률"])
                txt += "\n  - EPS:{}".format(d[group][stock_code]["EPS"])
                txt += "\n  - 예상EPS:{}".format(d[group][stock_code]["12M_Fwd_EPS"])
                messeage_to_telegram(txt, dbg=True)
                fig = plt.figure(clear=True)
                for info in prices[stock_code]['prices']:
                    dates.append(datetime.strptime(info['formatted_date'], "%Y-%m-%d"))
                    prcs.append(info['close'])
                price = pd.core.series.Series(prcs, dates)
                SP = fig.add_subplot(1, 1, 1)
                SP.plot(price, label="{}({})".format(d[group][stock_code]["Name"], stock_code))
                SP.legend(loc='upper center')
                img_path = r'{}\{}\{}'.format(path, 'USStockPriceTrace', yyyymmdd)
                print(img_path)
                if not os.path.exists(img_path):
                    os.makedirs(img_path)
                plt.savefig(img_path + '\\{}_{}.png'.format(d[group][stock_code]["Name"], stock_code))
                plt.xticks(rotation=45)
                # plt.show()
                msgr.img_messeage_to_telegram(img_path + '\\{}_{}.png'.format(d[group][stock_code]["Name"], stock_code),
                                              True)
                fig = None
                plt.close('all')
                if d[group][stock_code]['FCF'] is None or d[group][stock_code]['OCF'] is None or d[group][stock_code][
                    'EARN'] is None or d[group][stock_code]['NETINC'] is None:
                    continue
                key = np.array(list(d[group][stock_code]['FCF'].keys()))
                value1 = np.array(list(d[group][stock_code]['FCF'].values()))
                value2 = np.array(list(d[group][stock_code]['OCF'].values()))
                value3 = np.array(list(d[group][stock_code]['EARN'].values()))
                value4 = np.array(list(d[group][stock_code]['NETINC'].values()))

                df = pd.DataFrame(data=dict(nQ=key, FCF=np.rint(value1), OCF=np.rint(value2), EARN=np.rint(value3),
                                            PL=np.rint(value4)))
                plt.title("{} {}({})".format(d[group][stock_code]["Period"], d[group][stock_code]["Name"], stock_code))
                plt.style.use('seaborn-dark')

                ax = plt.subplot()
                data_fcf = ax.plot(key, np.rint(value1), color="green", linestyle='-', marker='o', label="FCF")
                data_ocf = ax.plot(key, np.rint(value2), color="red", linestyle='-', marker='o', label="OCF")
                data_earn = ax.plot(key, np.rint(value3), color="blue", linestyle='-', marker='o', label="EARN")
                data_pl = ax.plot(key, np.rint(value4), color="purple", linestyle='-', marker='o', label="PL")

                for k1, v1 in zip(key, np.rint(value1)):
                    ax.text(k1, v1 * 1.04, format(v1, ','), fontsize=10, horizontalalignment='center',
                            verticalalignment="bottom")
                for k1, v2 in zip(key, np.rint(value2)):
                    ax.text(k1, v2 * 1.04, format(v2, ','), fontsize=10, horizontalalignment='center',
                            verticalalignment="bottom")
                for k1, v3 in zip(key, np.rint(value3)):
                    ax.text(k1, v3 * 1.04, format(v3, ','), fontsize=10, horizontalalignment='center',
                            verticalalignment="bottom")
                for k1, v4 in zip(key, np.rint(value4)):
                    ax.text(k1, v4 * 1.04, format(v4, ','), fontsize=10, horizontalalignment='center',
                            verticalalignment="bottom")
                ax.legend()
                ax.set_ylim([min(min(value1), min(value2), min(value3), min(value4)),
                             max(map(lambda x: x[-1], [value1, value2, value3, value4])) * 1.2])
                ax.yaxis.set_ticks([])
                ax.grid(False)
                # plt.show()
                plt.savefig(img_path + '\\Cashflow_{}_{}.png'.format(d[group][stock_code]["Name"], stock_code))
                # plt.show()
                msgr.img_messeage_to_telegram2(
                    img_path + '\\Cashflow_{}_{}.png'.format(d[group][stock_code]["Name"], stock_code),
                    dbg=True)
                fig = None
                plt.close("all")
        plt = None
    except Exception as e:
        errmsg = '{}\n{}'.format('get_nasdaq_stock_graph', str(e))
        err_messeage_to_telegram(errmsg)
        fig = None
        plt.close('all')
        plt = None


def align_string(switch, text, digit):
    if switch == 'L':
        return format(text, " <%d" % digit)
    elif switch == 'R':
        return format(text, " >%d" % digit)
    elif switch == ',':
        return format(format(float(text), ','), " >%d" % digit)
    else:
        return None


def telegram_test():
    import telegram
    # my_token = '577949495:AAFk3JWQjHlbJr2_AtZeonjqQS7buu8cYG4'
    my_token = '781845768:AAEG55_jbdDIDlmGXWHl8Ag2aDUg-YAA8fc'
    chat_id = '84410715'
    bot = telegram.Bot(token=my_token)
    txt = '고생했다~~앞으로 여기로 보내줄께'
    bot.sendMessage(chat_id=chat_id, text=txt)


def get_dailysnapshot_objects(rpt_nm, rpt_tp, column_nm, crp_cd, dateDict, key=None):
    import sys
    import os
    import django
    # sys.path.append(r'E:\Github\Waver\MainBoard')
    # sys.path.append(r'E:\Github\Waver\MainBoard\MainBoard')
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    if key:
        result = detective_db.FnGuideDailySnapShot.objects.filter(rpt_nm=rpt_nm,
                                                                  rpt_tp=rpt_tp,
                                                                  column_nm=column_nm,
                                                                  key=key,
                                                                  disc_date=dateDict['yyyymmdd'],
                                                                  crp_cd=crp_cd,
                                                                  ).values()
        if len(result) == 0:
            yyyymmdd = get_max_date_on_dailysnapshot(crp_cd)
            # print(yyyymmdd)
            result = detective_db.FnGuideDailySnapShot.objects.filter(rpt_nm=rpt_nm,
                                                                      rpt_tp=rpt_tp,
                                                                      column_nm=column_nm,
                                                                      key=key,
                                                                      disc_date=yyyymmdd['disc_date'],
                                                                      crp_cd=crp_cd,
                                                                      ).values()
    else:
        result = detective_db.FnGuideDailySnapShot.objects.filter(rpt_nm=rpt_nm,
                                                                  rpt_tp=rpt_tp,
                                                                  column_nm=column_nm,
                                                                  disc_date=dateDict['yyyymmdd'],
                                                                  crp_cd=crp_cd,
                                                                  ).values()
        if len(result) == 0:
            yyyymmdd = get_max_date_on_dailysnapshot(crp_cd)
            # print(yyyymmdd)
            result = detective_db.FnGuideDailySnapShot.objects.filter(rpt_nm=rpt_nm,
                                                                      rpt_tp=rpt_tp,
                                                                      column_nm=column_nm,
                                                                      disc_date=yyyymmdd['disc_date'],
                                                                      crp_cd=crp_cd,
                                                                      ).values()
    return result


def get_snapshot_objects(rpt_nm, rpt_tp, accnt_nm, disc_categorizing, fix_or_prov_or_estm, crp_cd, dateDict):
    import sys
    import os
    import django
    # sys.path.append(r'E:\Github\Waver\MainBoard')
    # sys.path.append(r'E:\Github\Waver\MainBoard\MainBoard')
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    result = detective_db.FnGuideSnapShot.objects.filter(rpt_nm=rpt_nm,
                                                         rpt_tp=rpt_tp,
                                                         accnt_nm=accnt_nm,
                                                         disc_categorizing=disc_categorizing,
                                                         fix_or_prov_or_estm=fix_or_prov_or_estm,
                                                         crp_cd=crp_cd,
                                                         disc_year=dateDict['yyyy']
                                                         ).exclude(rmk='None').exclude(rmk='완전잠식').values()
    if len(result) == 0:
        yyyy = str(int(dateDict['yyyy']) - 1)
        result = detective_db.FnGuideSnapShot.objects.filter(rpt_nm=rpt_nm,
                                                             rpt_tp=rpt_tp,
                                                             accnt_nm=accnt_nm,
                                                             disc_categorizing=disc_categorizing,
                                                             fix_or_prov_or_estm=fix_or_prov_or_estm,
                                                             crp_cd=crp_cd,
                                                             disc_year=yyyy,
                                                             disc_month='12'
                                                             ).exclude(rmk='None').exclude(rmk='완전잠식').values()
        if len(result) == 0:
            fix_or_prov_or_estm = 'P'
            result = detective_db.FnGuideSnapShot.objects.filter(rpt_nm=rpt_nm,
                                                                 rpt_tp=rpt_tp,
                                                                 accnt_nm=accnt_nm,
                                                                 disc_categorizing=disc_categorizing,
                                                                 fix_or_prov_or_estm=fix_or_prov_or_estm,
                                                                 crp_cd=crp_cd,
                                                                 disc_year=yyyy,
                                                                 disc_month='12'
                                                                 ).exclude(rmk='None').exclude(rmk='완전잠식').values()
            if len(result) == 0:
                fix_or_prov_or_estm = 'F'
                result = detective_db.FnGuideSnapShot.objects.filter(rpt_nm=rpt_nm,
                                                                     rpt_tp=rpt_tp,
                                                                     accnt_nm=accnt_nm,
                                                                     disc_categorizing=disc_categorizing,
                                                                     fix_or_prov_or_estm=fix_or_prov_or_estm,
                                                                     crp_cd=crp_cd,
                                                                     disc_year=yyyy,
                                                                     disc_month='12'
                                                                     ).exclude(rmk='None').exclude(rmk='완전잠식').values()
    return result


def get_financialreport_objects(rpt_nm, rpt_tp, accnt_nm, disc_categorizing, fix_or_prov_or_estm, crp_cd, dateDict):
    import sys
    import os
    import django
    # sys.path.append(r'E:\Github\Waver\MainBoard')
    # sys.path.append(r'E:\Github\Waver\MainBoard\MainBoard')
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    result = detective_db.FnGuideFinancialReport.objects.filter(rpt_nm=rpt_nm,
                                                                rpt_tp=rpt_tp,
                                                                accnt_nm=accnt_nm,
                                                                disc_categorizing=disc_categorizing,
                                                                fix_or_prov_or_estm=fix_or_prov_or_estm,
                                                                crp_cd=crp_cd,
                                                                disc_year=dateDict['yyyy']
                                                                ).exclude(rmk='None').exclude(rmk='완전잠식').values()
    if len(result) == 0:
        yyyy = str(int(dateDict['yyyy']) - 1)
        result = detective_db.FnGuideFinancialReport.objects.filter(rpt_nm=rpt_nm,
                                                                    rpt_tp=rpt_tp,
                                                                    accnt_nm=accnt_nm,
                                                                    disc_categorizing=disc_categorizing,
                                                                    fix_or_prov_or_estm=fix_or_prov_or_estm,
                                                                    crp_cd=crp_cd,
                                                                    disc_year=yyyy,
                                                                    disc_month='12'
                                                                    ).exclude(rmk='None').exclude(rmk='완전잠식').values()
        if len(result) == 0:
            fix_or_prov_or_estm = 'P'
            result = detective_db.FnGuideFinancialReport.objects.filter(rpt_nm=rpt_nm,
                                                                        rpt_tp=rpt_tp,
                                                                        accnt_nm=accnt_nm,
                                                                        disc_categorizing=disc_categorizing,
                                                                        fix_or_prov_or_estm=fix_or_prov_or_estm,
                                                                        crp_cd=crp_cd,
                                                                        disc_year=yyyy,
                                                                        disc_month='12'
                                                                        ).exclude(rmk='None').exclude(
                rmk='완전잠식').values()
            if len(result) == 0:
                fix_or_prov_or_estm = 'F'
                result = detective_db.FnGuideFinancialReport.objects.filter(rpt_nm=rpt_nm,
                                                                            rpt_tp=rpt_tp,
                                                                            accnt_nm=accnt_nm,
                                                                            disc_categorizing=disc_categorizing,
                                                                            fix_or_prov_or_estm=fix_or_prov_or_estm,
                                                                            crp_cd=crp_cd,
                                                                            disc_year=yyyy,
                                                                            disc_month='12'
                                                                            ).exclude(rmk='None').exclude(
                    rmk='완전잠식').values()
    return result


def new_find_hidden_pearl():
    import sys
    import os
    import django
    # sys.path.append(r'E:\Github\Waver\MainBoard')
    # sys.path.append(r'E:\Github\Waver\MainBoard\MainBoard')
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    import json
    import logging

    logfile = 'detector'
    if not os.path.exists('./logs'):
        os.makedirs('./logs')
    now = datetime.now().strftime("%Y%m%d%H%M%S")

    logger = logging.getLogger(__name__)
    formatter = logging.Formatter('[%(asctime)s][%(filename)s:%(lineno)s] >> %(message)s')

    streamHandler = logging.StreamHandler()
    fileHandler = logging.FileHandler("./logs/{}_{}.log".format(logfile, now))

    streamHandler.setFormatter(formatter)
    fileHandler.setFormatter(formatter)

    logger.addHandler(streamHandler)
    logger.addHandler(fileHandler)
    logger.setLevel(level=logging.INFO)

    # logging
    # logging.basicConfig(filename=logfile, filemode='w', level=logging.DEBUG)
    # logging.debug("Log started at %s", str(datetime.datetime.now()))

    pass_reason = ''
    req_rate = 8.0
    treasure = {}
    trash = {}
    data = {}
    # 날짜 정보 셋팅
    dateDict = new_get_dateDict()
    # 종목 정보 셋팅
    # DEBUG = True
    DEBUG = False
    # USE_JSON = False
    USE_JSON = True
    stockInfo = detective_db.Stocks.objects.filter(listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(code='270660', listing='Y') # 제일파마홀딩스
    # stockInfo = detective_db.Stocks.objects.filter(code='005930', listing='Y') # 삼성전자
    print(align_string('L', 'No.', 10),
          align_string('R', 'Code', 10),
          align_string('R', 'Name', 20),
          align_string('R', 'Issued Shares', 20),
          align_string('R', 'Capital', 20),
          align_string('R', 'ParValue', 10),
          align_string('R', 'Currency', 10),
          '\n')
    # 예상되는 당기순이익 조회 조건 셋팅
    # rpt_nm = 'FinancialHighlight'
    # rpt_tp = 'IFRS(연결)'
    # disc_categorizing = 'YEARLY'
    # # disc_categorizing = 'QUARTERLY'
    # fix_or_prov_or_estm = 'E'
    # # ----------------------------------
    HIGH_ROS = []
    HIGH_RESERVE = []
    try:
        JsonDir = '{}\ResultJson'.format(path)
        if not os.path.exists(JsonDir):
            os.makedirs(JsonDir)
        if os.path.exists(r'{}\result.{}.json'.format(JsonDir, yyyymmdd)) and USE_JSON:
            with open(r'{}\result.{}.json'.format(JsonDir, yyyymmdd), "r") as f:
                data = f.read()
                treasure = json.loads(data)
                # print(treasure)
        if os.path.exists(r'{}\trash.{}.json'.format(JsonDir, yyyymmdd)) and USE_JSON:
            with open(r'{}\trash.{}.json'.format(JsonDir, yyyymmdd), "r") as f:
                data = f.read()
                trash = json.loads(data)
                # print(treasure)
        for ii, stock in enumerate(stockInfo):
            # if ii > 10: break
            if stock.code in treasure.keys():
                print("stock.code in treasure.keys()")
                continue
            else:
                if stock.code in trash.keys():
                    print("stock.code in trash.keys()")
                    continue
                else:
                    pass
            data = {}
            info_lack = False
            # print(dir(stock))
            print(align_string('L', ii + 1, 10),
                  align_string('R', stock.code, 10),
                  align_string('R', stock.name, 20 - len(stock.name)),
                  align_string(',', stock.issued_shares, 20),
                  align_string(',', stock.capital, 20),
                  align_string('R', stock.par_value, 10),
                  align_string('R', stock.curr, 10),
                  )
            dic = get_soup_from_file('ROE', yyyymmdd, stock.name, stock.code, 'json')
            # if DEBUG: print(dic)
            for key in dic:
                if '04' == key:
                    # 해당 종목의 ROE 가 없으면 당해년 Estimation 이 없는 것으로 정확한 가치평가 불가하므로 제외
                    # if dic[key][0]['VAL3'] == '-':
                    #     # print("정보부족")
                    #     info_lack = True
                    #     pass_reason = '[{}][{}] 종목의 당해년 Estimation 이 없는 것으로 정확한 가치평가 불가 1차'.format(stock.code, stock.name)
                    #     break
                    # else:
                    if len(dic[key]) == 3:
                        data['요구수익률'] = 0 if dic[key][-2]['VAL3'] == '-' else float(dic[key][-2]['VAL3'])
                        data['요구수익률2'] = 0 if dic[key][-1]['VAL3'] == '-' else float(dic[key][-1]['VAL3'])
                    else:
                        data['요구수익률'] = 0 if dic[key][-1]['VAL3'] == '-' else float(dic[key][-1]['VAL3'])
                        data['요구수익률2'] = data['요구수익률']
                    # if DEBUG: print(data['요구수익률'], data['요구수익률2'])

            data['회사명'] = stock.name
            data['발행주식수'] = stock.issued_shares
            data['자본금'] = stock.capital
            data['액면가'] = stock.par_value
            data['통화'] = 'KRW' if stock.curr == '' else stock.curr
            soup = get_soup_from_file('snapshot', yyyymmdd, stock.name, stock.code, 'html')
            # print(soup)
            # marketTxt = fnguide.select_by_attr(soup, 'span', 'id', 'strMarketTxt').text.replace(' ', '') # 업종분류
            # data['업종구분'] = marketTxt.replace('\n', '')
            # # print(data['업종구분'], stock.market_text)
            # if data['업종구분'] != '' and stock.market_text is None:
            #     fnguide.StockMarketTextUpdate(stock.code, marketTxt)
            check = fnguide.select_by_attr(soup, 'span', 'class', 'stxt stxt1')
            if check:
                pass
            else:
                continue
            marketTxt = check.text.replace(' ', '')  # 업종분류
            data['업종구분'] = marketTxt.replace('\n', '')
            marketTxt = fnguide.select_by_attr(soup, 'span', 'class', 'stxt stxt2').text.replace(' ', '')  # 업종분류
            data['업종구분상세'] = marketTxt.replace('\n', '')
            sttl_month = fnguide.select_by_attr(soup, 'span', 'class', 'stxt stxt3').text.replace(' ', '')  # 업종분류
            data['결산월'] = sttl_month.replace('\n', '')
            # print(data['업종구분'], data['업종구분상세'], stock.market_text)
            if (data['업종구분'] != '' and stock.market_text is None) or (
                    data['업종구분상세'] != '' and stock.market_text_detail is None):
                fnguide.StockMarketTextUpdate(stock.code, data['업종구분'], data['업종구분상세'], data['결산월'])
            # # 업종구분까지 업데이트 한 후 Valuation 정보가 부족한 종목은 Pass
            # if info_lack:
            #     # print("Lack of information")
            #     logger.info(pass_reason)
            #     pass_reason = ""
            #     continue
            yearly_highlight = fnguide.select_by_attr(soup, 'div', 'id', 'highlight_D_Y')  # Snapshot FinancialHighlight
            # print(yearly_highlight)
            if yearly_highlight:
                # print(len(fnguide.get_table_contents(yearly_highlight, 'table thead tr th')))
                # print(len(fnguide.get_table_contents(yearly_highlight, 'table tbody tr th')))
                # print(fnguide.get_table_contents(yearly_highlight, 'table tbody tr td'))
                # if DEBUG: print(yearly_highlight)
                columns, items, values = fnguide.setting(
                    fnguide.get_table_contents(yearly_highlight, 'table thead tr th')[1:],
                    fnguide.get_table_contents(yearly_highlight, 'table tbody tr th'),
                    fnguide.get_table_contents(yearly_highlight, 'table tbody tr td'))
                # if DEBUG: print(columns, items, values)
                for idx, i in enumerate(items):
                    if i in ['지배주주순이익', '지배주주지분', '자산총계', '매출액', '이자수익', '보험료수익', '순영업수익', '영업수익', '유보율(%)', '부채비율(%)', '영업이익률(%)']:
                        for idx2, yyyymm in enumerate(columns):
                            # print(idx2, yyyymm)
                            # print(yyyymm[:4], dateDict['yyyy'], i, values[idx][idx2])
                            if yyyymm[:4] == dateDict['yyyy'] and values[idx][idx2] != '':
                                data['Period'] = yyyymm
                                if i[-3:] == '(%)':
                                    if fnguide.is_float(values[idx][idx2].replace(',', '')):
                                        data[i] = float(values[idx][idx2].replace(',', ''))
                                    else:
                                        data[i] = 0
                                    if values[idx][idx2 - 1] != '' and fnguide.is_float(
                                            values[idx][idx2 - 1].replace(',', '')):
                                        data['X' + i] = float(values[idx][idx2 - 1].replace(',', ''))
                                    else:
                                        data['X' + i] = 0
                                    break
                                else:
                                    if fnguide.is_float(values[idx][idx2].replace(',', '')):
                                        data[i] = float(values[idx][idx2].replace(',', '')) * 100000000
                                    else:
                                        data[i] = 0
                                    if values[idx][idx2 - 1] != '' and fnguide.is_float(
                                            values[idx][idx2 - 1].replace(',', '')):
                                        data['X' + i] = float(values[idx][idx2 - 1].replace(',', '')) * 100000000
                                    else:
                                        data['X' + i] = 0
                                    break
                            # elif yyyymm[:4] == dateDict['yyyy'] and values[idx][idx2] == '':
                            #     if yyyymm[:4] == dateDict['yyyy'] and values[idx][idx2 - 1] == '':
                            #         if yyyymm[:4] == dateDict['yyyy'] and values[idx][idx2 - 2] == '':
                            #             continue
                            #             # data['Period'] = columns[idx2 - 3]
                            #             # data[i] = float(values[idx][idx2 - 3].replace(',', '')) * 100000000
                            #         else:
                            #             # print("data['Period'] = columns[idx2 - 2]")
                            #             data['Period'] = columns[idx2 - 2]
                            #             data[i] = float(values[idx][idx2 - 2].replace(',', '')) * 100000000
                            #     else:
                            #         # print("data['Period'] = columns[idx2-1]")
                            #         data['Period'] = columns[idx2-1]
                            #         data[i] = float(values[idx][idx2-1].replace(',', '')) * 100000000
                            else:
                                if values[idx][idx2 - 1] != '' and fnguide.is_float(
                                        values[idx][idx2 - 1].replace(',', '')):
                                    if i[-3:] == '(%)':
                                        data['X' + i] = float(values[idx][idx2 - 1].replace(',', ''))
                                    else:
                                        data['X' + i] = float(values[idx][idx2 - 1].replace(',', '')) * 100000000
                                else:
                                    continue
                    elif i in ['ROE(%)']:
                        for idx2, yyyymm in enumerate(columns):
                            # print(idx2, yyyymm)
                            # print(yyyymm[:4], dateDict['yyyy'], values[idx][idx2])
                            if yyyymm[:4] == dateDict['yyyy'] and values[idx][idx2] != '':
                                data['Period'] = yyyymm
                                if fnguide.is_float(values[idx][idx2].replace(',', '')):
                                    pass
                                else:
                                    data['확인사항'] = values[idx][idx2].replace(',', '')
                                break
                            elif yyyymm[:4] == dateDict['yyyy'] and values[idx][idx2] == '':
                                data['Period'] = columns[idx2 - 1]
                                if fnguide.is_float(values[idx][idx2 - 1].replace(',', '')):
                                    pass
                                else:
                                    data['확인사항'] = values[idx][idx2 - 1].replace(',', '')
                                break
                            else:
                                continue

                if not set(['지배주주순이익', '지배주주지분', '자산총계']).issubset(data.keys()):
                    yearly_highlight = fnguide.select_by_attr(soup, 'div', 'id',
                                                              'highlight_B_Y')  # Snapshot FinancialHighlight
                    # print(yearly_highlight)
                    if yearly_highlight:
                        columns, items, values = fnguide.setting(
                            fnguide.get_table_contents(yearly_highlight, 'table thead tr th')[1:],
                            fnguide.get_table_contents(yearly_highlight, 'table tbody tr th'),
                            fnguide.get_table_contents(yearly_highlight, 'table tbody tr td'))
                        # if DEBUG: print(columns, items, values)
                        for idx, i in enumerate(items):
                            if i in ['당기순이익', '자본총계', '자산총계', '매출액', '이자수익', '보험료수익', '순영업수익', '영업수익', '유보율(%)',
                                     '부채비율(%)', '영업이익(발표기준)', '영업이익률(%)']:
                                for idx2, yyyymm in enumerate(columns):
                                    # print(idx2, yyyymm)
                                    # print(yyyymm[:4], dateDict['yyyy'], i, values[idx][idx2])
                                    if yyyymm[:4] == dateDict['yyyy'] and values[idx][idx2] != '':
                                        data['Period'] = yyyymm
                                        if i[-3:] == '(%)':
                                            if fnguide.is_float(values[idx][idx2].replace(',', '')):
                                                data[i] = float(values[idx][idx2].replace(',', ''))
                                            else:
                                                data[i] = 0
                                            if values[idx][idx2 - 1] != '' and fnguide.is_float(
                                                    values[idx][idx2 - 1].replace(',', '')):
                                                data['X' + i] = float(values[idx][idx2 - 1].replace(',', ''))
                                            else:
                                                data['X' + i] = 0
                                            break
                                        else:
                                            if fnguide.is_float(values[idx][idx2].replace(',', '')):
                                                data[i] = float(values[idx][idx2].replace(',', '')) * 100000000
                                            else:
                                                data[i] = 0
                                            if values[idx][idx2 - 1] != '' and fnguide.is_float(
                                                    values[idx][idx2 - 1].replace(',', '')):
                                                data['X' + i] = float(
                                                    values[idx][idx2 - 1].replace(',', '')) * 100000000
                                            else:
                                                data['X' + i] = 0
                                            break

                                    else:
                                        if values[idx][idx2 - 1] != '' and fnguide.is_float(
                                                values[idx][idx2 - 1].replace(',', '')):
                                            if i[-3:] == '(%)':
                                                data['X' + i] = float(values[idx][idx2 - 1].replace(',', ''))
                                            else:
                                                data['X' + i] = float(
                                                    values[idx][idx2 - 1].replace(',', '')) * 100000000
                                        else:
                                            continue
                            elif i in ['ROE(%)']:
                                for idx2, yyyymm in enumerate(columns):
                                    # print(idx2, yyyymm)
                                    # print(yyyymm[:4], dateDict['yyyy'], values[idx][idx2])
                                    if yyyymm[:4] == dateDict['yyyy'] and values[idx][idx2] != '':
                                        data['Period'] = yyyymm
                                        if fnguide.is_float(values[idx][idx2].replace(',', '')):
                                            pass
                                        else:
                                            data['확인사항'] = values[idx][idx2].replace(',', '')
                                        break
                                    elif yyyymm[:4] == dateDict['yyyy'] and values[idx][idx2] == '':
                                        data['Period'] = columns[idx2 - 1]
                                        if fnguide.is_float(values[idx][idx2 - 1].replace(',', '')):
                                            pass
                                        else:
                                            data['확인사항'] = values[idx][idx2 - 1].replace(',', '')
                                        break
                                    else:
                                        continue
                    if '당기순이익' in data.keys():
                        data['지배주주순이익'] = data['당기순이익']
                    if '자본총계' in data.keys():
                        data['지배주주지분'] = data['자본총계']
                if not set(['지배주주순이익', '지배주주지분', '자산총계']).issubset(data.keys()):
                    pass_reason = '[{}][{}] Not enough Information for valuation 2차'.format(stock.code, stock.name)
                    logger.info(pass_reason)
                    trash[stock.code] = data
                    continue
                daily = fnguide.select_by_attr(soup, 'div', 'id', 'svdMainGrid1')  # Snapshot 시세현황1
                columns, items, values = fnguide.setting(
                    fnguide.get_table_contents(daily, 'table thead tr th')[1:],
                    fnguide.get_table_contents(daily, 'table tbody tr th'),
                    fnguide.get_table_contents(daily, 'table tbody tr td'))
                # if DEBUG: print(columns, items, values)
                for idx, col in enumerate(columns):
                    # print(col, values[idx])
                    if col.strip() in ['종가', '외국인 보유비중', '비율', '거래량', '전일대비']:
                        if col.strip() == '전일대비':
                            tmp = values[idx].replace(' ', '').replace('+', '△ ').replace('-', '▽ ').replace(',', '')
                            tmp2 = tmp.split(' ')
                            if tmp == '' or tmp2[1] == '0':
                                data[col.strip()] = "-"
                            else:
                                if tmp2[0] == '△':
                                    pct = round(float(tmp2[1]) / (data['종가'] - float(tmp2[1])) * 100, 2)
                                else:
                                    pct = round(float(tmp2[1]) / (data['종가'] + float(tmp2[1])) * 100, 2)
                                data[col.strip()] = "{}{}%".format(tmp2[0], pct)
                        else:
                            data[col] = float(values[idx].replace(',', '')) if (
                                        values[idx] is not None and values[idx] != '') else 0.0
                        # break
                    if col in ['발행주식수-보통주'] and values[idx] != '' and data['발행주식수'] != float(
                            values[idx].replace(',', '')):
                        print("[{}][{}]발행주식수가 다릅니다. {} <> {}".format(stock.code, stock.name, stock.issued_shares,
                                                                     float(values[idx].replace(',', ''))))
                        data['발행주식수'] = float(values[idx].replace(',', ''))
                # 20190419 요구수익률을 다른곳에서 가져오면서 주석처리
                # daily = fnguide.select_by_attr(soup, 'div', 'id', 'svdMainGrid10D')  # Snapshot 업종비교
                # columns, items, values = fnguide.setting(
                #     fnguide.get_table_contents(daily, 'table thead tr th'),
                #     fnguide.get_table_contents(daily, 'table tbody tr th'),
                #     fnguide.get_table_contents(daily, 'table tbody tr td'))
                # if DEBUG: print(columns, items, values)
                # for idx, i in enumerate(items):
                #     if i in ['ROE']:
                #         for idx2, col in enumerate(columns):
                #             # print(columns, items, values)
                #             # print(idx, i, idx2, col, values[idx][idx2])
                #             if col != '' and col.replace('\n', '').replace(' ', '') == marketTxt.replace('\n', '').replace(' ', ''):
                #                 data['요구수익률'] = float(values[idx][idx2])
                #                 break
                # if '요구수익률' not in data.keys():
                #     for idx, i in enumerate(items):
                #         if i in ['ROE']:
                #             for idx2, col in enumerate(columns):
                #                 if col != '' and col.replace('\n', '').replace(' ', '') == 'KOSPI':
                #                     data['요구수익률'] = float(values[idx][idx2])
                #                     break
                # if '요구수익률' not in data.keys(): data['요구수익률'] = 10.0
                # if data['요구수익률'] < 8.0: data['요구수익률'] = 8.0
                # 20190419 요구수익률을 다른곳에서 가져오면서 주석처리 끝

                # data['요구수익률'] = (data['요구수익률'] + 10) /2
                # print(data)
                # 포괄손익계산서가 과거데이터가 많아 제외 - 20190417
                # soup = get_soup_from_file('financeReport', yyyymmdd, stock.name, stock.code)
                # yearly_sonik = fnguide.select_by_attr(soup, 'div', 'id', 'divSonikY')  # Snapshot 포괄손익계산서
                # columns, valueDict = fnguide.dynamic_parse_table('divSonikY', yearly_sonik.table, stock.code, stock.name)
                # if DEBUG:
                #     for key in valueDict.keys():
                #         # if key.endswith('금융수익'):
                #             print(key, valueDict[key])
                # # print(columns, valueDict)
                # for key in valueDict.keys():
                #     if key in ['중단영업이익', '금융수익-금융수익', '기타수익-기타수익']:
                #         for idx, yyyymm in enumerate(columns[1:]):
                #             if DEBUG: print(yyyymm, dateDict)
                #             # if yyyymm[:4] == dateDict['yyyy'] and yyyymm[5:7] == dateDict['mm']:
                #             if yyyymm[:4] == data['Period'][:4] and yyyymm[5:7] == data['Period'][5:7]:
                #                 data[key] = 0.0 if valueDict[key][idx] == '' else float(valueDict[key][idx].replace(',', '')) * 100000000
                #                 break
                #             elif yyyymm[:4] == data['Period'][:4]:
                #                 data[key] = 0.0 if valueDict[key][idx] == '' else float(valueDict[key][idx].replace(',', '')) * 100000000
                #                 break
                #             else:
                #                 continue
                #     # elif key.startswith('금융수익'):
                #     #     if '금융수익' not in data.keys(): data['금융수익'] = 0.0
                #     #     for idx, yyyymm in enumerate(columns[1:]):
                #     #         if yyyymm[:4] == data['Period'][:4] and yyyymm[5:7] == data['Period'][5:7]:
                #     #             data['금융수익'] += 0.0 if valueDict[key][idx] == '' else float(valueDict[key][idx].replace(',', '')) * 100000000
                #     #             break
                #     #         elif yyyymm[:4] == data['Period'][:4]:
                #     #             data['금융수익'] += 0.0 if valueDict[key][idx] == '' else float(valueDict[key][idx].replace(',', '')) * 100000000
                #     #             break
                #     #         else:
                #     #             continue
                fwd_summary = fnguide.select_by_attr(soup, 'div', 'id', 'corp_group2')  # Snapshot section ul_corpinfo
                summary_title = []
                summary_data = []
                if fwd_summary:
                    for tag in fwd_summary.select('dl'):
                        if tag.dt.text.strip() != '' and tag.dt.text.strip() != '\n':
                            # print(tag.dt.text.strip())
                            summary_title.append(tag.dt.text.strip())
                    for tag in fwd_summary.select('dl dd'):
                        try:
                            # print(tag.text.strip())
                            float(tag.text.strip().replace(',', ''))
                            summary_data.append(float(tag.text.strip().replace(',', '')))
                        except Exception as e:
                            # print('[Error]', tag.text.strip())
                            if '%' in tag.text.strip():
                                summary_data.append(tag.text.strip())
                                # summary_data.append(float(tag.text.strip().replace('%', '')) * 0.01)
                            elif '-' == tag.text.strip():
                                summary_data.append(0)
                            else:
                                continue
                # print(fwd_summary)
                # print(summary_title)
                # print(summary_data)
                if fwd_summary and summary_title:
                    for idx, title in enumerate(summary_title):
                        data[title] = summary_data[idx]
                        # print(title, summary_data[idx])
                adjval = data['업종 PER'] * data['PBR(Price Book-value Ratio)']
                # if '중단영업이익' not in data.keys(): data['중단영업이익'] = 0.0
                # if '금융수익-금융수익' not in data.keys(): data['금융수익-금융수익'] = 0.0
                # if '기타수익-기타수익' not in data.keys(): data['기타수익-기타수익'] = 0.0
                # data['ROE'] = (data['지배주주순이익'] - data['중단영업이익']) / data['지배주주지분'] * 100
                # print(data)
                if '매출액' not in data.keys():
                    data['매출액'] = data['이자수익'] if '이자수익' in data.keys() else data[
                        '보험료수익'] if '보험료수익' in data.keys() else data['순영업수익'] if '순영업수익' in data.keys() else data[
                        '영업수익'] if '영업수익' in data.keys() else 0
                if data['매출액'] == 0: continue
                if data['요구수익률'] == 0: data['요구수익률'] = 10.0
                if DEBUG: print("data['지배주주지분']", data['지배주주지분'])
                if DEBUG: print("data['요구수익률']", data['요구수익률'])
                if DEBUG: print("data['발행주식수']", data['발행주식수'])
                if DEBUG: print("data['자산총계']", data['자산총계'])
                if DEBUG: print("data['매출액']", data['매출액'])
                if DEBUG: print("data['유보율']", data['X유보율(%)'])
                if DEBUG: print("data['부채비율']", data['부채비율(%)'])
                if 'X지배주주순이익' not in data.keys(): data['X지배주주순이익'] = 0.0
                if data['지배주주지분'] == 0:
                    data['ROE'] = 0.0
                else:
                    data['ROE'] = data['지배주주순이익'] / data['지배주주지분'] * 100
                # if data['ROE'] > 20 and (data['금융수익-금융수익'] / data['지배주주순이익'] > 0.7 or data['기타수익-기타수익'] / data['지배주주순이익'] > 0.7 ):
                #     # data['ROE'] = (data['지배주주순이익'] - data['금융수익-금융수익'] - data['기타수익-기타수익'] - data['중단영업이익']) / data['지배주주지분'] * 100
                #     data['ROE'] = (data['지배주주순이익'] - data['중단영업이익']) / data['지배주주지분'] * 100
                data['주주가치'] = data['지배주주지분'] + (
                        data['지배주주지분'] * (data['ROE'] - data['요구수익률']) / (data['요구수익률']))
                data['NPV'] = data['주주가치'] / data['발행주식수']
                data['NPV2'] = (data['주주가치'] * (data['지배주주지분'] / data['자산총계'])) / data['발행주식수']
                data['ROS'] = data['지배주주순이익'] / data['매출액'] * 100
                if data['ROS'] > 15: HIGH_ROS.append(data['회사명'])
                if 'X유보율(%)' in data.keys() and data['X유보율(%)'] > 1000: HIGH_RESERVE.append(data['회사명'])
                if DEBUG: print(data)
                treasure[stock.code] = data
        print('=' * 50, '마이너스', '=' * 50)
        print(align_string('L', 'No.', 5),
              align_string('R', 'Code', 10),
              align_string('R', '업종구분', 20),
              align_string('R', 'Name', 20),
              # align_string('R', 'X지배주주순이익', 20),
              align_string('R', '요구수익률', 15),
              align_string('R', 'ROE', 20),
              align_string('R', '영업이익률', 20),
              align_string('R', '12M PER', 8),
              align_string('R', '업종 PER', 8),
              align_string('R', '지배주주지분', 14),
              align_string('R', '주주가치', 16),
              align_string('R', 'NPV', 20),
              align_string('R', '종가', 10),
              align_string('R', '확인사항', 16),
              )
        if not DEBUG: dataInit()
        cnt = 0
        print(treasure)
        TargetStockDataDelete(yyyymmdd)
        for d in treasure.keys():
            # print(d)
            # if treasure[d]['NPV'] > 0 and treasure[d]['NPV']/treasure[d]['종가']*100 > 100:  # 수익예상 종목

            # if treasure[d]['NPV'] < 0 or ('확인사항' in treasure[d].keys() and treasure[d]['확인사항'] == '완전잠식'):  # 제외종목
            #     cnt += 1
            #     print(align_string('L', cnt, 10),
            #           align_string('R', d, 10),
            #           align_string('R', treasure[d]['회사명'], 20 - len(treasure[d]['회사명'])),
            #           align_string(',', round(treasure[d]['ROE'], 2), 20),
            #           align_string(',', treasure[d]['12M PER'], 8),
            #           align_string(',', treasure[d]['업종 PER'], 8),
            #           align_string(',', treasure[d]['지배주주지분'], 20),
            #           align_string(',', treasure[d]['주주가치'], 20),
            #           align_string(',', round(treasure[d]['NPV'], 2), 20),
            #           align_string(',', treasure[d]['종가'], 10),
            #           align_string('R', '' if '확인사항' not in treasure[d].keys() else treasure[d]['확인사항'], 20),
            #           )
            #     continue
            # if treasure[d]['12M PER'] > treasure[d]['업종 PER'] * 0.7 or \
            #             #    treasure[d]['ROE'] < 10 or \
            #             #    treasure[d]['12M PER'] > 10 or \
            #             #    treasure[d]['PBR(Price Book-value Ratio)'] > 3:
            #             #     # or treasure[d]['NPV'] < 0 or treasure[d]['12M PER'] == 0 or \
            #             #    # treasure[d]['NPV']/treasure[d]['종가']*100 < 100 \
            # if treasure[d]['12M PER'] > treasure[d]['업종 PER'] * 0.7 or \
            #    treasure[d]['ROS'] < 10 or \
            #    treasure[d]['ROE'] / treasure[d]['ROS'] < 0.2 or \
            #    treasure[d]['12M PER'] == 0 or
            # if treasure[d]['X지배주주순이익'] < 1 or \
            #      treasure[d]['업종구분'].replace('\n', '') in ['코스닥제조', '코스피제조업', '코스피건설업', '코스닥건설'] or \
            #      treasure[d]['지배주주지분'] / treasure[d]['자산총계'] < 0.51 or \
            # if treasure[d]['ROE'] < 15 or \
            #         treasure[d]['ROE'] < treasure[d]['요구수익률'] or \
            #         treasure[d]['업종구분'].replace('\n', '') in ['코스닥제조', '코스피제조업', '코스피건설업', '코스닥건설', '코스피금융업'] or \
            #         treasure[d]['지배주주지분'] / treasure[d]['자산총계'] < 0.51 or \
            #         treasure[d]['NPV'] < 0 or \
            #         treasure[d]['NPV'] / treasure[d]['종가'] * 100 < 105:
            if treasure[d]['영업이익률(%)'] < 15 or \
                    treasure[d]['ROE'] < 15 or \
                    treasure[d]['업종구분'].replace('\n', '').replace('\xa0', "") in ['KSE코스피금융업', 'KOSDAQ코스닥금융', 'KSE코스피은행', 'KSE코스피증권']:
                cnt += 1
                print(align_string('L', cnt, 5),
                      align_string('R', d, 10),
                      align_string('R', treasure[d]['업종구분'], 10),
                      align_string('R', treasure[d]['회사명'], 20 - len(treasure[d]['회사명'])),
                      # align_string(',', round(treasure[d]['X지배주주순이익'], 2), 20),
                      align_string(',', round(treasure[d]['요구수익률'], 2), 20),
                      align_string(',', round(treasure[d]['ROE'], 2), 20),
                      align_string(',', round(treasure[d]['영업이익률(%)'], 2), 20),
                      align_string(',', treasure[d]['12M PER'], 8),
                      align_string(',', treasure[d]['업종 PER'], 8),
                      align_string(',', round(treasure[d]['지배주주지분'], 0), 20),
                      align_string(',', round(treasure[d]['주주가치'], 0), 20),
                      align_string(',', round(treasure[d]['NPV'], 0), 20),
                      align_string(',', treasure[d]['종가'], 10),
                      align_string('R', '' if '확인사항' not in treasure[d].keys() else treasure[d]['확인사항'], 20),
                      )
                # if treasure[d]['ROE'] < 15 or treasure[d]['ROE'] < treasure[d]['요구수익률']:
                #     pass_reason = "[{}][{}]['ROE'] < 15 또는 ['ROE'] < ['요구수익률'] => ROE : {} / 요구수익률 : {}".format(d,
                #                                                                                                 treasure[
                #                                                                                                     d][
                #                                                                                                     '회사명'],
                #                                                                                                 treasure[
                #                                                                                                     d][
                #                                                                                                     'ROE'],
                #                                                                                                 treasure[
                #                                                                                                     d][
                #                                                                                                     '요구수익률'])
                # elif treasure[d]['업종구분'].replace('\n', '') in ['코스닥제조', '코스피제조업', '코스피건설업', '코스닥건설', '코스피금융업']:
                #     pass_reason = "[{}][{}][업종구분이 제조, 건설 또는 금융] => 업종구분 : {}".format(d, treasure[d]['회사명'],
                #                                                                      treasure[d]['업종구분'].replace(
                #                                                                          u'\xa0', '').replace('\n', ''))
                # elif treasure[d]['지배주주지분'] / treasure[d]['자산총계'] < 0.51:
                #     pass_reason = "[{}][{}][지배주주 자산지분 비율이 51% 미만] => 지배주주지분 / 자산총계 : {:.2f}".format(d,
                #                                                                                     treasure[d]['회사명'],
                #                                                                                     treasure[d][
                #                                                                                         '지배주주지분'] /
                #                                                                                     treasure[d]['자산총계'])
                # else:
                #     pass_reason = "[{}][{}]전기지배주주순이익 : {}\n지배주주지분 : {}\n자산총계 : {}\nROE : {:.2f} < 15\n업종구분 : {}\nNPV : {:.2f}\n종가 : {}".format(
                #         d, treasure[d]['회사명'], treasure[d]['X지배주주순이익'], treasure[d]['지배주주지분'], treasure[d]['자산총계'],
                #         treasure[d]['ROE'], treasure[d]['업종구분'].replace(u'\xa0', '').replace('\n', ''),
                #         treasure[d]['NPV'],
                #         treasure[d]['종가'])

                if treasure[d]['ROE'] >= 30 or treasure[d]['영업이익률(%)'] > 30 or treasure[d]['NPV'] / treasure[d]['종가'] * 100 > 200:
                    logger.info("[NEED TO CHECK]" + pass_reason)
                else:
                    logger.error(pass_reason)
                pass_reason = ""
                continue
            print(align_string('L', cnt, 5),
                  align_string('R', d, 10),
                  align_string('R', treasure[d]['업종구분'], 10),
                  align_string('R', treasure[d]['회사명'], 20 - len(treasure[d]['회사명'])),
                  # align_string(',', round(treasure[d]['X지배주주순이익'], 2), 20),
                  align_string(',', round(treasure[d]['요구수익률'], 2), 20),
                  align_string(',', round(treasure[d]['ROE'], 2), 20),
                  align_string(',', round(treasure[d]['영업이익률(%)'], 2), 20),
                  align_string(',', treasure[d]['12M PER'], 8),
                  align_string(',', treasure[d]['업종 PER'], 8),
                  align_string(',', round(treasure[d]['지배주주지분'], 0), 20),
                  align_string(',', round(treasure[d]['주주가치'], 0), 20),
                  align_string(',', round(treasure[d]['NPV'], 0), 20),
                  align_string(',', treasure[d]['종가'], 10),
                  align_string('R', '' if '확인사항' not in treasure[d].keys() else treasure[d]['확인사항'], 20),
                  )
            TargetStockDataStore(d, treasure[d])
        # print(HIGH_ROS)
        # print(HIGH_RESERVE)
        logger.info(HIGH_RESERVE)
        if os.path.exists(r'{}\result.{}.json'.format(JsonDir, yyyymmdd)):
            os.remove(r'{}\result.{}.json'.format(JsonDir, yyyymmdd))
        with open(r'{}\result.{}.json'.format(JsonDir, yyyymmdd), 'w') as fp:
            json.dump(treasure, fp)
        if os.path.exists(r'{}\trash.{}.json'.format(JsonDir, yyyymmdd)):
            os.remove(r'{}\trash.{}.json'.format(JsonDir, yyyymmdd))
        with open(r'{}\trash.{}.json'.format(JsonDir, yyyymmdd), 'w') as fp:
            json.dump(trash, fp)
    except Exception as e:
        print('error', e, '\n', stock)
        errmsg = '{}\n{}\n[{}][{}]'.format('new_find_hidden_pearl', str(e), stock.code, stock.name)
        err_messeage_to_telegram(errmsg)
        if os.path.exists(r'{}\result.{}.json'.format(JsonDir, yyyymmdd)):
            os.remove(r'{}\result.{}.json'.format(JsonDir, yyyymmdd))
        with open(r'{}\result.{}.json'.format(JsonDir, yyyymmdd), 'w') as fp:
            json.dump(treasure, fp)
        if os.path.exists(r'{}\trash.{}.json'.format(JsonDir, yyyymmdd)):
            os.remove(r'{}\trash.{}.json'.format(JsonDir, yyyymmdd))
        with open(r'{}\trash.{}.json'.format(JsonDir, yyyymmdd), 'w') as fp:
            json.dump(trash, fp)


def new_find_hidden_pearl_with_dartpipe(all=False, bgn_dt=None, end_dt=None):
    import sys
    import os
    import django
    from OpenDartPipe import pipe
    # sys.path.append(r'E:\Github\Waver\MainBoard')
    # sys.path.append(r'E:\Github\Waver\MainBoard\MainBoard')
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    import json
    import numpy as np
    import requests
    import logging
    from django.db.models import Q

    logfile = 'detector'
    if not os.path.exists('./logs'):
        os.makedirs('./logs')
    now = datetime.now().strftime("%Y%m%d%H%M%S")

    logger = logging.getLogger(__name__)
    formatter = logging.Formatter('[%(asctime)s][%(filename)s:%(lineno)s] >> %(message)s')

    streamHandler = logging.StreamHandler()
    fileHandler = logging.FileHandler("./logs/{}_{}.log".format(logfile, now))

    streamHandler.setFormatter(formatter)
    fileHandler.setFormatter(formatter)

    logger.addHandler(streamHandler)
    logger.addHandler(fileHandler)
    logger.setLevel(level=logging.INFO)

    # logging
    # logging.basicConfig(filename=logfile, filemode='w', level=logging.DEBUG)
    # logging.debug("Log started at %s", str(datetime.datetime.now()))

    current_pos = None
    treasure = {}
    trash = {}
    data = {}
    best = {}
    better = {}
    good = {}
    soso = {}
    lists = None
    none_list = []
    # 날짜 정보 셋팅
    dateDict = new_get_dateDict()
    # 종목 정보 셋팅
    # DEBUG = True
    DEBUG = False
    # USE_JSON = False
    USE_JSON = True
    # stockInfo = detective_db.Stocks.objects.filter(category_name__contains="일반 목적", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(category_name__contains="특수", listing='Y')
    stockInfo = detective_db.Stocks.objects.filter(category_name__contains="플라스틱", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(category_name__contains="반도체", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(category_name__contains="정밀", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(category_name__contains="철강", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(category_name__contains="생물", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(category_name__contains="운송", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(market_text__contains="제조", market_text_detail__contains="장비", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(code="005930", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(code=code, listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(Q(category_name__contains="도매") | Q(category_name__contains="소매"))
    print(len(stockInfo))
    dart = pipe.Pipe()
    dart.create()
    for stock in stockInfo:
        current_key = None
        ret, code = dart.get_corp_code(stock.code)
        try:
            if ret:
                data[stock.code] = {"corp_code": code,
                                    "last_report": None,
                                    "corp_name": stock.name,
                                    "category": stock.category_name,
                                    "list_shares": stock.issued_shares,
                                    "PL": {"Y": {}, "Q": {}},
                                    "FS": {"TotalAsset": {}, "TotalDebt": {}, "RetainedEarnings": {}},
                                    "CF": {"영업활동현금흐름": {}, "유형자산취득": {}, "무형자산취득": {}, "FCF": {}},
                                    "AverageRate": {"Y": {}, "Q": {}}}
                # print(dateDict["yyyy2"], dateDict)
                if bgn_dt is None:
                    lists = dart.get_list(corp_code=code, bgn_de=dateDict["yyyy2"], pblntf_ty='A', req_type=True)[
                                "list"][:5]
                elif end_dt is None:
                    lists = dart.get_list(corp_code=code, bgn_de=bgn_dt, pblntf_ty='A', req_type=True)["list"][:5]
                else:
                    lists = dart.get_list(corp_code=code, bgn_de=bgn_dt, end_de=end_dt, pblntf_ty='A', req_type=True)[
                                "list"][:5]
                # lists = dart.get_list(corp_code=code, bgn_de=dateDict["yyyy2"], pblntf_ty='A', req_type=True)["list"][:5]
                for l in lists:
                    if data[stock.code]["last_report"] is None:
                        data[stock.code]["last_report"] = l["report_nm"]
                    else:
                        if data[stock.code]["last_report"] < l["report_nm"]: data[stock.code]["last_report"] = l[
                            "report_nm"]
                    logger.info(l)
                req_list, req_list2 = dart.get_req_lists(lists)
                result = dart.get_fnlttSinglAcnt_from_req_list(code, req_list, "ALL")
                current_pos = result
                # for key in result.keys():  # key = ["연결재무제표", "재무제표"]
                #     for report in result[key].keys():  # report = ["재무상태표", "손익계산서"]
                #         if report == "재무상태표":
                #             for acc in result[key][report].keys():
                #                 # acc = ["유동자산", "비유동자산", "자산총계", "유동부채", "비유동부채", "부채총계", "자본금", "이익잉여금", "자본총계"]
                #                 for category in sorted(result[key][report][acc].keys()):
                #                     # category = ["YYYY 1/4", "YYYY 2/4", "YYYY 3/4", "YYYY 4/4"]
                #                     print(key, report, acc, category, result[key][report][acc][category])
                #                     # for k in result[key][report][acc][category].keys():
                #                     #     print(key, report, acc, category, k, result[key][report][acc][category][k])
                #         else:
                #             for acc in result[key][report].keys():
                #                 # acc = ["매출액", 영업이익", "법인세차감전", "당기순이익"]
                #                 for category in result[key][report][acc].keys():
                #                     # category = ["누계", "당기"]
                #                     for k in sorted(result[key][report][acc][category].keys()):
                #                         # k = ["YYYY 1/4", "YYYY 2/4", "YYYY 3/4", "YYYY 4/4"]
                #                         print(key, report, acc, category, k, result[key][report][acc][category][k])
                d1 = None
                d2 = None
                d3 = None
                d4 = None
                d5 = None
                d6 = None
                d7 = None
                d8 = None
                d9 = None
                d10 = None
                d11 = None
                d12 = None
                d13 = None
                d14 = None
                dicTemp0 = {}
                dicTemp1 = {}
                dicTemp2 = {}
                dicTemp3 = {}
                dicTemp4 = {}
                dicTemp5 = {}
                dicTemp6 = {}
                dicTemp7 = {}
                dicTemp8 = {}
                dicTemp9 = {}
                dicTemp10 = {}
                dicTemp11 = {}
                dicTemp12 = {}
                dicTemp13 = {}
                dicTemp14 = {}
                # if stock == "006360":
                #     print()
                d1keys = ["매출", "수익(매출액)", "I.  매출액", "영업수익", "매출액", "Ⅰ. 매출액", "매출 및 지분법 손익", "매출 및 지분법손익"]
                d2keys = ["영업이익(손실)", "영업이익 (손실)", "영업이익", "영업손익", "V. 영업손익", "Ⅴ. 영업이익", "Ⅴ. 영업이익(손실)", "V. 영업이익",
                          "영업손실"]
                d8keys = ["당기순이익(손실)", "당기순이익 (손실)", "당기순이익", "분기순이익", "반기순이익", "당기순이익(손실)", "분기순이익(손실)", "반기순이익(손실)",
                          "연결당기순이익", "연결분기순이익", "연결반기순이익", "연결당기순이익(손실)", "연결분기순이익(손실)", "연결반기순이익(손실)", "당기순손익",
                          "분기순손익",
                          "반기순손익", "지배기업 소유주지분", "지배기업의 소유주에게 귀속되는 당기순이익(손실)", "당기순손실", "분기순손실", "반기순손실",
                          "Ⅷ. 당기순이익(손실)", "지배기업 소유주 지분",
                          "Ⅷ. 당기순이익", "VIII. 당기순이익", "지배기업 소유주", "VIII. 분기순손익", "VIII. 분기순이익", "I.당기순이익", "I.반기순이익",
                          "I.분기순이익", "반기연결순이익(손실)", "지배기업의 소유주지분", "지배기업소유주지분", "지배기업의소유주지분"]
                d10keys = ["영업활동현금흐름", "영업활동 현금흐름", "영업활동으로 인한 현금흐름", "영업활동 순현금흐름유입", "영업활동으로인한현금흐름", "영업활동으로 인한 순현금흐름",
                           "Ⅰ. 영업활동으로 인한 현금흐름", "Ⅰ. 영업활동으로 인한 현금흐름", "영업활동순현금흐름 합계", "영업활동순현금흐름", "I. 영업활동현금흐름"]
                d11keys = ["유형자산의 취득", "유형자산 취득", "유형자산의취득"]
                d12keys = ["무형자산의 취득", "무형자산 취득", "무형자산의취득", "무형자산의 증가"]
                d13keys = ["토지의 취득", "건물의 취득", "구축물의 취득", "기계장치의 취득", "차량운반구의 취득", "공구와기구의 취득", "비품의 취득",
                           "기타유형자산의 취득", "건설중인자산의 취득", "투자부동산의 취득", "집기비품의 취득", "시험기기의 취득", "시설공사의 취득",
                           "토지의취득", "건물의취득", "구축물의취득", "기계장치의취득", "차량운반구의취득", "공구와기구의취득", "비품의취득",
                           "기타유형자산의취득", "건설중인자산의취득", "투자부동산의취득", "집기비품의취득", "시험기기의취득", "시설공사의취득"
                           ]
                d14keys = ["컴퓨터소프트웨어의 취득", "산업재산권의 취득", "소프트웨어의 취득", "기타무형자산의 취득", "소프트웨어의 증가",
                           "컴퓨터소프트웨어의취득", "산업재산권의취득", "소프트웨어의취득", "기타무형자산의취득", "소프트웨어의증가"]
                # if stock == "006360":
                #     print()
                if result is not {} and "연결재무제표" in result.keys():
                    logger.info("연결재무제표 start")
                    if "포괄손익계산서" in result["연결재무제표"].keys():
                        logger.info("연결재무제표 포괄손익계산서 start")
                        tmp_result1 = {key: result["연결재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                       result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d1keys}}
                        tmp_result2 = {key: result["연결재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                       result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d2keys}}
                        tmp_result3 = {key: result["연결재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                       result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d1keys}}
                        tmp_result4 = {key: result["연결재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                       result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d2keys}}
                        tmp_result8 = {key: result["연결재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                       result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d8keys}}
                        tmp_result9 = {key: result["연결재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                       result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d8keys}}
                        if tmp_result1:
                            for key in tmp_result1.keys():
                                if d1 is None:
                                    d1 = tmp_result1[key]
                                else:
                                    d1.update(tmp_result1[key])
                        if tmp_result2:
                            for key in tmp_result2.keys():
                                if d2 is None:
                                    d2 = tmp_result2[key]
                                else:
                                    d2.update(tmp_result2[key])
                        if tmp_result3:
                            for key in tmp_result3.keys():
                                if d3 is None:
                                    d3 = tmp_result3[key]
                                else:
                                    d3.update(tmp_result3[key])
                        if tmp_result4:
                            for key in tmp_result4.keys():
                                if d4 is None:
                                    d4 = tmp_result4[key]
                                else:
                                    d4.update(tmp_result4[key])
                        if tmp_result8:
                            for key in tmp_result8.keys():
                                if d8 is None:
                                    d8 = tmp_result8[key]
                                else:
                                    d8.update(tmp_result8[key])
                        if tmp_result9:
                            for key in tmp_result9.keys():
                                if d9 is None:
                                    d9 = tmp_result9[key]
                                else:
                                    d9.update(tmp_result9[key])
                    if "손익계산서" in result["연결재무제표"].keys():
                        logger.info("연결재무제표 손익계산서 start")
                        tmp_result1 = {key: result["연결재무제표"]["손익계산서"][key]["누계"] for key in
                                       result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d1keys}}
                        tmp_result2 = {key: result["연결재무제표"]["손익계산서"][key]["누계"] for key in
                                       result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d2keys}}
                        tmp_result3 = {key: result["연결재무제표"]["손익계산서"][key]["당기"] for key in
                                       result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d1keys}}
                        tmp_result4 = {key: result["연결재무제표"]["손익계산서"][key]["당기"] for key in
                                       result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d2keys}}
                        tmp_result8 = {key: result["연결재무제표"]["손익계산서"][key]["누계"] for key in
                                       result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d8keys}}
                        tmp_result9 = {key: result["연결재무제표"]["손익계산서"][key]["당기"] for key in
                                       result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d8keys}}
                        if tmp_result1:
                            for key in tmp_result1.keys():
                                if d1 is None:
                                    d1 = tmp_result1[key]
                                else:
                                    d1.update(tmp_result1[key])
                        if tmp_result2:
                            for key in tmp_result2.keys():
                                if d2 is None:
                                    d2 = tmp_result2[key]
                                else:
                                    d2.update(tmp_result2[key])
                        if tmp_result3:
                            for key in tmp_result3.keys():
                                if d3 is None:
                                    d3 = tmp_result3[key]
                                else:
                                    d3.update(tmp_result3[key])
                        if tmp_result4:
                            for key in tmp_result4.keys():
                                if d4 is None:
                                    d4 = tmp_result4[key]
                                else:
                                    d4.update(tmp_result4[key])
                        if tmp_result8:
                            for key in tmp_result8.keys():
                                if d8 is None:
                                    d8 = tmp_result8[key]
                                else:
                                    d8.update(tmp_result8[key])
                        if tmp_result9:
                            for key in tmp_result9.keys():
                                if d9 is None:
                                    d9 = tmp_result9[key]
                                else:
                                    d9.update(tmp_result9[key])
                    if "현금흐름표" in result["연결재무제표"].keys():
                        logger.info("연결재무제표 현금흐름표 start")
                        tmp_result10 = {key: result["연결재무제표"]["현금흐름표"][key] for key in
                                        result["연결재무제표"]["현금흐름표"].keys() & {keys for keys in d10keys}}
                        tmp_result11 = {key: result["연결재무제표"]["현금흐름표"][key] for key in
                                        result["연결재무제표"]["현금흐름표"].keys() & {keys for keys in d11keys}}
                        tmp_result12 = {key: result["연결재무제표"]["현금흐름표"][key] for key in
                                        result["연결재무제표"]["현금흐름표"].keys() & {keys for keys in d12keys}}
                        tmp_result13 = {key: result["연결재무제표"]["현금흐름표"][key] for key in
                                        result["연결재무제표"]["현금흐름표"].keys() & {keys for keys in d13keys}}
                        tmp_result14 = {key: result["연결재무제표"]["현금흐름표"][key] for key in
                                        result["연결재무제표"]["현금흐름표"].keys() & {keys for keys in d14keys}}
                        if tmp_result10:
                            for key in tmp_result10.keys():
                                if d10 is None:
                                    d10 = tmp_result10[key]
                                else:
                                    d10.update(tmp_result10[key])
                        if tmp_result11:
                            for key in tmp_result11.keys():
                                if d11 is None:
                                    d11 = tmp_result11[key]
                                else:
                                    d11.update(tmp_result11[key])
                        if tmp_result12:
                            for key in tmp_result12.keys():
                                if d12 is None:
                                    d12 = tmp_result12[key]
                                else:
                                    d12.update(tmp_result12[key])
                        if tmp_result13:
                            d13 = dictionary_add(tmp_result13)
                            # for key in tmp_result13.keys():
                            #     if d13 is None:
                            #         d13 = tmp_result13[key]
                            #     else:
                            #         d13.update(tmp_result13[key])
                        if tmp_result14:
                            d14 = dictionary_add(tmp_result14)
                            # for key in tmp_result14.keys():
                            #     if d14 is None:
                            #         d14 = tmp_result14[key]
                            #     else:
                            #         d14.update(tmp_result14[key])
                    if d11 is None: d11 = d13
                    if d12 is None: d12 = d14
                    d5 = result["연결재무제표"]["재무상태표"]["자산총계"] if "자산총계" in result["연결재무제표"]["재무상태표"].keys() else None
                    d6 = result["연결재무제표"]["재무상태표"]["부채총계"] if "부채총계" in result["연결재무제표"]["재무상태표"].keys() else None
                    d7 = result["연결재무제표"]["재무상태표"]["이익잉여금"] if "이익잉여금" in result["연결재무제표"]["재무상태표"].keys() else None
                    if d5 is None:
                        if "자  산  총  계" in result["연결재무제표"]["재무상태표"].keys():
                            d5 = result["연결재무제표"]["재무상태표"]["자  산  총  계"]
                    else:
                        if "자  산  총  계" in result["연결재무제표"]["재무상태표"].keys():
                            d5.update(result["연결재무제표"]["재무상태표"]["자  산  총  계"])
                    if d5 is None:
                        if "자산 총계" in result["연결재무제표"]["재무상태표"].keys():
                            d5 = result["연결재무제표"]["재무상태표"]["자산 총계"]
                    else:
                        if "자산 총계" in result["연결재무제표"]["재무상태표"].keys():
                            d5.update(result["연결재무제표"]["재무상태표"]["자산 총계"])
                    if d6 is None:
                        if "부  채  총  계" in result["연결재무제표"]["재무상태표"].keys():
                            d6 = result["연결재무제표"]["재무상태표"]["부  채  총  계"]
                    else:
                        if "부  채  총  계" in result["연결재무제표"]["재무상태표"].keys():
                            d6.update(result["연결재무제표"]["재무상태표"]["부  채  총  계"])
                    if d6 is None:
                        if "부채 총계" in result["연결재무제표"]["재무상태표"].keys():
                            d6 = result["연결재무제표"]["재무상태표"]["부채 총계"]
                    else:
                        if "부채 총계" in result["연결재무제표"]["재무상태표"].keys():
                            d6.update(result["연결재무제표"]["재무상태표"]["부채 총계"])
                    if d7 is None:
                        if "이익잉여금(결손금)" in result["연결재무제표"]["재무상태표"].keys():
                            d7 = result["연결재무제표"]["재무상태표"]["이익잉여금(결손금)"]
                    else:
                        if "이익잉여금(결손금)" in result["연결재무제표"]["재무상태표"].keys():
                            d7.update(result["연결재무제표"]["재무상태표"]["이익잉여금(결손금)"])
                    if d7 is None:
                        if "결손금" in result["연결재무제표"]["재무상태표"].keys():
                            d7 = result["연결재무제표"]["재무상태표"]["결손금"]
                    else:
                        if "결손금" in result["연결재무제표"]["재무상태표"].keys():
                            d7.update(result["연결재무제표"]["재무상태표"]["결손금"])
                else:
                    logger.info("재무제표 start")
                    if "포괄손익계산서" in result["재무제표"].keys():
                        logger.info("재무제표 포괄손익계산서 start")
                        tmp_result1 = {key: result["재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                       result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d1keys}}
                        tmp_result2 = {key: result["재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                       result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d2keys}}
                        tmp_result3 = {key: result["재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                       result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d1keys}}
                        tmp_result4 = {key: result["재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                       result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d2keys}}
                        tmp_result8 = {key: result["재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                       result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d8keys}}
                        tmp_result9 = {key: result["재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                       result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d8keys}}
                        if tmp_result1:
                            for key in tmp_result1.keys():
                                if d1 is None:
                                    d1 = tmp_result1[key]
                                else:
                                    d1.update(tmp_result1[key])
                        if tmp_result2:
                            for key in tmp_result2.keys():
                                if d2 is None:
                                    d2 = tmp_result2[key]
                                else:
                                    d2.update(tmp_result2[key])
                        if tmp_result3:
                            for key in tmp_result3.keys():
                                if d3 is None:
                                    d3 = tmp_result3[key]
                                else:
                                    d3.update(tmp_result3[key])
                        if tmp_result4:
                            for key in tmp_result4.keys():
                                if d4 is None:
                                    d4 = tmp_result4[key]
                                else:
                                    d4.update(tmp_result4[key])
                        if tmp_result8:
                            for key in tmp_result8.keys():
                                if d8 is None:
                                    d8 = tmp_result8[key]
                                else:
                                    d8.update(tmp_result8[key])
                        if tmp_result9:
                            for key in tmp_result9.keys():
                                if d9 is None:
                                    d9 = tmp_result9[key]
                                else:
                                    d9.update(tmp_result9[key])
                    if "손익계산서" in result["재무제표"].keys():
                        logger.info("재무제표 손익계산서 매출 start")
                        tmp_result1 = {key: result["재무제표"]["손익계산서"][key]["누계"] for key in
                                       result["재무제표"]["손익계산서"].keys() & {keys for keys in d1keys}}
                        tmp_result2 = {key: result["재무제표"]["손익계산서"][key]["누계"] for key in
                                       result["재무제표"]["손익계산서"].keys() & {keys for keys in d2keys}}
                        tmp_result3 = {key: result["재무제표"]["손익계산서"][key]["당기"] for key in
                                       result["재무제표"]["손익계산서"].keys() & {keys for keys in d1keys}}
                        tmp_result4 = {key: result["재무제표"]["손익계산서"][key]["당기"] for key in
                                       result["재무제표"]["손익계산서"].keys() & {keys for keys in d2keys}}
                        tmp_result8 = {key: result["재무제표"]["손익계산서"][key]["누계"] for key in
                                       result["재무제표"]["손익계산서"].keys() & {keys for keys in d8keys}}
                        tmp_result9 = {key: result["재무제표"]["손익계산서"][key]["당기"] for key in
                                       result["재무제표"]["손익계산서"].keys() & {keys for keys in d8keys}}
                        if tmp_result1:
                            for key in tmp_result1.keys():
                                if d1 is None:
                                    d1 = tmp_result1[key]
                                else:
                                    d1.update(tmp_result1[key])
                        if tmp_result2:
                            for key in tmp_result2.keys():
                                if d2 is None:
                                    d2 = tmp_result2[key]
                                else:
                                    d2.update(tmp_result2[key])
                        if tmp_result3:
                            for key in tmp_result3.keys():
                                if d3 is None:
                                    d3 = tmp_result3[key]
                                else:
                                    d3.update(tmp_result3[key])
                        if tmp_result4:
                            for key in tmp_result4.keys():
                                if d4 is None:
                                    d4 = tmp_result4[key]
                                else:
                                    d4.update(tmp_result4[key])
                        if tmp_result8:
                            for key in tmp_result8.keys():
                                if d8 is None:
                                    d8 = tmp_result8[key]
                                else:
                                    d8.update(tmp_result8[key])
                        if tmp_result9:
                            for key in tmp_result9.keys():
                                if d9 is None:
                                    d9 = tmp_result9[key]
                                else:
                                    d9.update(tmp_result9[key])
                    if "현금흐름표" in result["재무제표"].keys():
                        logger.info("재무제표 현금흐름표 start")
                        tmp_result10 = {key: result["재무제표"]["현금흐름표"][key] for key in
                                        result["재무제표"]["현금흐름표"].keys() & {keys for keys in d10keys}}
                        tmp_result11 = {key: result["재무제표"]["현금흐름표"][key] for key in
                                        result["재무제표"]["현금흐름표"].keys() & {keys for keys in d11keys}}
                        tmp_result12 = {key: result["재무제표"]["현금흐름표"][key] for key in
                                        result["재무제표"]["현금흐름표"].keys() & {keys for keys in d12keys}}
                        tmp_result13 = {key: result["재무제표"]["현금흐름표"][key] for key in
                                        result["재무제표"]["현금흐름표"].keys() & {keys for keys in d13keys}}
                        tmp_result14 = {key: result["재무제표"]["현금흐름표"][key] for key in
                                        result["재무제표"]["현금흐름표"].keys() & {keys for keys in d14keys}}
                        if tmp_result10:
                            for key in tmp_result10.keys():
                                if d10 is None:
                                    d10 = tmp_result10[key]
                                else:
                                    d10.update(tmp_result10[key])
                        if tmp_result11:
                            for key in tmp_result11.keys():
                                if d11 is None:
                                    d11 = tmp_result11[key]
                                else:
                                    d11.update(tmp_result11[key])
                        if tmp_result12:
                            for key in tmp_result12.keys():
                                if d12 is None:
                                    d12 = tmp_result12[key]
                                else:
                                    d12.update(tmp_result12[key])
                        if tmp_result13:
                            d13 = dictionary_add(tmp_result13)
                            # for key in tmp_result13.keys():
                            #     if d13 is None:
                            #         d13 = tmp_result13[key]
                            #     else:
                            #         d13.update(tmp_result13[key])
                        if tmp_result14:
                            d14 = dictionary_add(tmp_result14)
                            # for key in tmp_result14.keys():
                            #     if d14 is None:
                            #         d14 = tmp_result14[key]
                            #     else:
                            #         d14.update(tmp_result14[key])
                    if d11 is None: d11 = d13
                    if d12 is None: d12 = d14
                    d5 = result["재무제표"]["재무상태표"]["자산총계"] if "자산총계" in result["재무제표"]["재무상태표"].keys() else None
                    d6 = result["재무제표"]["재무상태표"]["부채총계"] if "부채총계" in result["재무제표"]["재무상태표"].keys() else None
                    d7 = result["재무제표"]["재무상태표"]["이익잉여금"] if "이익잉여금" in result["재무제표"]["재무상태표"].keys() else None
                    if d5 is None:
                        if "자  산  총  계" in result["재무제표"]["재무상태표"].keys():
                            d5 = result["재무제표"]["재무상태표"]["자  산  총  계"]
                    else:
                        if "자  산  총  계" in result["재무제표"]["재무상태표"].keys():
                            d5.update(result["재무제표"]["재무상태표"]["자  산  총  계"])
                    if d5 is None:
                        if "자산 총계" in result["재무제표"]["재무상태표"].keys():
                            d5 = result["재무제표"]["재무상태표"]["자산 총계"]
                    else:
                        if "자산 총계" in result["재무제표"]["재무상태표"].keys():
                            d5.update(result["재무제표"]["재무상태표"]["자산 총계"])
                    if d6 is None:
                        if "부  채  총  계" in result["재무제표"]["재무상태표"].keys():
                            d6 = result["재무제표"]["재무상태표"]["부  채  총  계"]
                    else:
                        if "부  채  총  계" in result["재무제표"]["재무상태표"].keys():
                            d6.update(result["재무제표"]["재무상태표"]["부  채  총  계"])
                    if d6 is None:
                        if "부채 총계" in result["재무제표"]["재무상태표"].keys():
                            d6 = result["재무제표"]["재무상태표"]["부채 총계"]
                    else:
                        if "부채 총계" in result["재무제표"]["재무상태표"].keys():
                            d6.update(result["재무제표"]["재무상태표"]["부채 총계"])
                    if d7 is None:
                        if "이익잉여금(결손금)" in result["재무제표"]["재무상태표"].keys():
                            d7 = result["재무제표"]["재무상태표"]["이익잉여금(결손금)"]
                    else:
                        if "이익잉여금(결손금)" in result["재무제표"]["재무상태표"].keys():
                            d7.update(result["재무제표"]["재무상태표"]["이익잉여금(결손금)"])
                    if d7 is None:
                        if "결손금" in result["재무제표"]["재무상태표"].keys():
                            d7 = result["재무제표"]["재무상태표"]["결손금"]
                    else:
                        if "결손금" in result["재무제표"]["재무상태표"].keys():
                            d7.update(result["재무제표"]["재무상태표"]["결손금"])
                logger.info("매출액 누계 : {}".format(d1))  # 매출액 누계
                logger.info("영업이익 누계 : {}".format(d2))  # 영업이익 누계
                logger.info("매출액 당기 : {}".format(d3))  # 매출액 당기
                logger.info("영업이익 당기 : {}".format(d4))  # 영업이익 당기
                logger.info("자산총계 : {}".format(d5))  # 자산총계
                logger.info("부채총계 : {}".format(d6))  # 부채총계
                logger.info("이익잉여금 : {}".format(d7))  # 이익잉여금
                logger.info("당기순이익 누계 : {}".format(d8))  # 당기순이익 누계
                logger.info("당기순이익 : {}".format(d9))  # 당기순이익
                logger.info("영업활동현금흐름 : {}".format(d10))  # 영업활동현금흐름
                logger.info("유형자산의 취득 : {}".format(d11))  # 유형자산의 취득
                logger.info("무형자산의 취득 : {}".format(d12))  # 무형자산의 취득
                logger.info("유형자산의 취득(유형자산의 취득으로 표시되지 않는) : {}".format(d13))  # 유형자산의 취득(유형자산의 취득으로 표시되지 않는)
                logger.info("무형자산의 취득(무형자산의 취득으로 표시되지 않는) : {}".format(d14))  # 무형자산의 취득(무형자산의 취득으로 표시되지 않는)
                if d10 is None:
                    none_list.append("[{}][{}]-영업활동현금흐름".format(stock.code, stock.name))
                if d11 is None:
                    none_list.append("[{}][{}]-유형자산의 취득".format(stock.code, stock.name))
                if d12 is None:
                    none_list.append("[{}][{}]-무형자산의 취득".format(stock.code, stock.name))
                for key1 in d1.keys():
                    current_key = key1
                    if "Rate" in key1: continue
                    if "4/4" in key1:
                        data[stock.code]["PL"]["Y"]["매출액영업이익률"] = dict(sorted({
                                                                                  k: round(float(
                                                                                      d2[key1][k].replace(",",
                                                                                                          "")) / float(
                                                                                      d1[key1][k].replace(",",
                                                                                                          "")) * 100,
                                                                                           2) if float(
                                                                                      d1[key1][k].replace(",",
                                                                                                          "")) != 0.0 else 0
                                                                                  for k in d1[key1]}.items()))

                        data[stock.code]["PL"]["Y"]["매출액"] = dict(
                            sorted({k: float(d1[key1][k].replace(",", "")) for k in
                                    d1[key1]}.items()))
                        # data[stock.code]["PL"]["Y"]["매출액"]["최근"] = provision_info[stock]["PL"]["Y"]["매출액"]
                        data[stock.code]["PL"]["Y"]["영업이익"] = dict(
                            sorted({k: float(d2[key1][k].replace(",", "")) for k in
                                    d2[key1]}.items()))
                        data[stock.code]["PL"]["Y"]["당기순이익"] = dict(
                            sorted({k: float(d8[key1][k].replace(",", "")) for k in
                                    d8[key1]}.items()))
                        # data[stock.code]["PL"]["Y"]["영업이익"]["최근"] = provision_info[stock]["PL"]["Y"]["영업이익"]
                        for k in sorted(d1[key1]):
                            dicTemp1[k] = float(d1[key1][k].replace(",", ""))
                        for k in sorted(d2[key1]):
                            dicTemp2[k] = float(d2[key1][k].replace(",", ""))
                        for k in sorted(d8[key1]):
                            dicTemp8[k] = float(d8[key1][k].replace(",", ""))
                    else:
                        for k in sorted(d1[key1]):
                            dicTemp0[k] = round(
                                float(d2[key1][k].replace(",", "")) / float(d1[key1][k].replace(",", "")) * 100,
                                2) if float(d1[key1][k].replace(",", "")) != 0.0 else 0
                        for k in sorted(d1[key1]):
                            dicTemp1[k] = float(d1[key1][k].replace(",", ""))
                            # data[stock.code]["PL"]["Q"]["누계매출액"][k] = float(d1[key1][k].replace(",", ""))
                        for k in sorted(d2[key1]):
                            dicTemp2[k] = float(d2[key1][k].replace(",", ""))
                            # data[stock.code]["PL"]["Q"]["누계영업이익"][k] = float(d2[key1][k].replace(",", ""))
                        for k in sorted(d3[key1]):
                            dicTemp3[k] = float(d3[key1][k].replace(",", ""))
                            # data[stock.code]["PL"]["Q"]["당기매출액"][k] = float(d3[key1][k].replace(",", ""))
                        for k in sorted(d4[key1]):
                            dicTemp4[k] = float(d4[key1][k].replace(",", ""))
                            # data[stock.code]["PL"]["Q"]["당기영업이익"][k] = float(d4[key1][k].replace(",", ""))
                        for k in sorted(d8[key1]):
                            dicTemp8[k] = float(d8[key1][k].replace(",", ""))
                            # data[stock.code]["PL"]["Q"]["당기매출액"][k] = float(d3[key1][k].replace(",", ""))
                        for k in sorted(d9[key1]):
                            dicTemp9[k] = float(d9[key1][k].replace(",", ""))
                            # data[stock.code]["PL"]["Q"]["당기영업이익"][k] = float(d4[key1][k].replace(",", ""))
                for key2 in d10.keys():
                    current_key = key2
                    if "Rate" in key2: continue
                    # if key2 not in data[stock.code]["CF"]["FCF"].keys():
                    #     data[stock.code]["CF"]["FCF"][key2] = {}
                    for key3 in d10[key2].keys():
                        yhasset = int(d11[key2][key3]) if d11 is not None and key2 in d11.keys() and key3 in d11[
                            key2].keys() else 0
                        mhasset = int(d12[key2][key3]) if d12 is not None and key2 in d12.keys() and key3 in d12[
                            key2].keys() else 0
                        data[stock.code]["CF"]["FCF"][key3] = int(d10[key2][key3]) - (yhasset + mhasset)
                data[stock.code]["PL"]["Q"]["매출액영업이익률"] = dict(sorted(dicTemp0.items()))
                data[stock.code]["PL"]["Q"]["누계매출액추이"] = dict(sorted(dicTemp1.items()))
                data[stock.code]["PL"]["Q"]["누계영업이익추이"] = dict(sorted(dicTemp2.items()))
                data[stock.code]["PL"]["Q"]["당기매출액"] = dict(sorted(dicTemp3.items()))
                data[stock.code]["PL"]["Q"]["당기영업이익"] = dict(sorted(dicTemp4.items()))
                data[stock.code]["PL"]["Q"]["누계당기순이익추이"] = dict(sorted(dicTemp8.items()))
                data[stock.code]["PL"]["Q"]["당기순이익"] = dict(sorted(dicTemp9.items()))
                # print("MakeAvg1?")
                # print(data)
                data[stock.code]["AverageRate"]["Y"]["매출액영업이익률"] = round(sum(
                    data[stock.code]["PL"]["Y"]["매출액영업이익률"].values()) / float(
                    len(data[stock.code]["PL"]["Y"]["매출액영업이익률"])), 2) if "매출액영업이익률" in data[stock.code]["PL"][
                    "Y"].keys() else None
                # print("MakeAvg2?")
                data[stock.code]["AverageRate"]["Y"]["매출액"] = round(sum(
                    data[stock.code]["PL"]["Y"]["매출액"].values()) / float(
                    len(data[stock.code]["PL"]["Y"]["매출액"])), 0) if "매출액" in data[stock.code]["PL"]["Y"].keys() and \
                                                                    len(data[stock.code]["PL"]["Y"][
                                                                            "매출액"]) != 0 else None
                # print("MakeAvg3?")
                data[stock.code]["AverageRate"]["Y"]["영업이익"] = round(sum(
                    data[stock.code]["PL"]["Y"]["영업이익"].values()) / float(
                    len(data[stock.code]["PL"]["Y"]["영업이익"])), 0) if "영업이익" in data[stock.code]["PL"]["Y"].keys() and \
                                                                     len(data[stock.code]["PL"]["Y"][
                                                                             "영업이익"]) != 0 else None
                data[stock.code]["AverageRate"]["Y"]["당기순이익"] = round(sum(
                    data[stock.code]["PL"]["Y"]["당기순이익"].values()) / float(
                    len(data[stock.code]["PL"]["Y"]["당기순이익"])), 0) if "당기순이익" in data[stock.code]["PL"]["Y"].keys() and \
                                                                      len(data[stock.code]["PL"]["Y"][
                                                                              "당기순이익"]) != 0 else None
                # print("MakeAvg4?")
                data[stock.code]["AverageRate"]["Q"]["매출액영업이익률"] = round(sum(
                    data[stock.code]["PL"]["Q"]["매출액영업이익률"].values()) / float(
                    len(data[stock.code]["PL"]["Q"]["매출액영업이익률"])), 2) if "매출액영업이익률" in data[stock.code]["PL"][
                    "Q"].keys() and \
                                                                         len(data[stock.code]["PL"]["Q"][
                                                                                 "매출액영업이익률"]) != 0 else None
                # print("MakeAvg5?")
                data[stock.code]["AverageRate"]["Q"]["매출액"] = round(sum(
                    data[stock.code]["PL"]["Q"]["당기매출액"].values()) / float(
                    len(data[stock.code]["PL"]["Q"]["당기매출액"])), 0) if "당기매출액" in data[stock.code]["PL"]["Q"].keys() and \
                                                                      len(data[stock.code]["PL"]["Q"][
                                                                              "당기매출액"]) != 0 else None
                # print("MakeAvg6?")
                data[stock.code]["AverageRate"]["Q"]["영업이익"] = round(sum(
                    data[stock.code]["PL"]["Q"]["당기영업이익"].values()) / float(
                    len(data[stock.code]["PL"]["Q"]["당기영업이익"])), 0) if "당기영업이익" in data[stock.code]["PL"][
                    "Q"].keys() and \
                                                                       len(data[stock.code]["PL"]["Q"][
                                                                               "당기영업이익"]) != 0 else None
                data[stock.code]["AverageRate"]["Q"]["당기순이익"] = round(sum(
                    data[stock.code]["PL"]["Q"]["당기순이익"].values()) / float(
                    len(data[stock.code]["PL"]["Q"]["당기순이익"])), 0) if "당기순이익" in data[stock.code]["PL"]["Q"].keys() and \
                                                                      len(data[stock.code]["PL"]["Q"][
                                                                              "당기순이익"]) != 0 else None
                # print("MakeAvg7?")
                # 손익계산서 분석 끝
                for key1 in d1.keys():
                    if "Rate" in key1: continue
                    if d5 is not None and key1 in d5.keys():
                        for k in sorted(d5[key1]):
                            dicTemp5[k] = float(d5[key1][k].replace(",", "")) if d5 is not None else 0
                    if d6 is not None and key1 in d6.keys():
                        for k in sorted(d6[key1]):
                            dicTemp6[k] = float(d6[key1][k].replace(",", "")) if d6 is not None else 0
                    if d7 is not None and key1 in d7.keys():
                        for k in sorted(d7[key1]):
                            dicTemp7[k] = float(d7[key1][k].replace(",", "")) if d7 is not None else 0
                    if d10 is not None and key1 in d10.keys():
                        for k in sorted(d10[key1]):
                            dicTemp10[k] = float(str(d10[key1][k]).replace(",", "")) if d10 is not None else 0
                    if d11 is not None and key1 in d11.keys():
                        for k in sorted(d11[key1]):
                            dicTemp11[k] = float(str(d11[key1][k]).replace(",", "")) if d11 is not None else 0
                    if d12 is not None and key1 in d12.keys():
                        for k in sorted(d12[key1]):
                            dicTemp12[k] = float(str(d12[key1][k]).replace(",", "")) if d12 is not None else 0
                data[stock.code]["FS"]["TotalAsset"] = dict(sorted(dicTemp5.items()))
                data[stock.code]["FS"]["TotalDebt"] = dict(sorted(dicTemp6.items()))
                data[stock.code]["FS"]["RetainedEarnings"] = dict(sorted(dicTemp7.items()))
                data[stock.code]["CF"]["영업활동현금흐름"] = dict(sorted(dicTemp10.items()))
                data[stock.code]["CF"]["유형자산취득"] = dict(sorted(dicTemp11.items()))
                data[stock.code]["CF"]["무형자산취득"] = dict(sorted(dicTemp12.items()))
                data[stock.code]["CF"]["FCF"] = dict(sorted(data[stock.code]["CF"]["FCF"].items()))
        except Exception as e:
            logger.error(e)
            # logger.error(current_pos)
            logger.error(current_key)
            for key in current_pos.keys():  # key = ["연결재무제표", "재무제표"]
                for report in current_pos[key].keys():  # report = ["재무상태표", "손익계산서"]
                    if report not in ["손익계산서", "포괄손익계산서"]:  # ["재무상태표", "현금흐름표", "자본변동표"]:
                        for acc in current_pos[key][report].keys():
                            # acc = ["유동자산", "비유동자산", "자산총계", "유동부채", "비유동부채", "부채총계", "자본금", "이익잉여금", "자본총계"]
                            for category in sorted(current_pos[key][report][acc].keys()):
                                # category = ["YYYY 1/4", "YYYY 2/4", "YYYY 3/4", "YYYY 4/4"]
                                logger.error("{}\t{}\t{}\t{}\t{}".format(key, report, acc, category,
                                                                         current_pos[key][report][acc][category]))
                                # for k in result[key][report][acc][category].keys():
                                #     print(key, report, acc, category, k, current_pos[key][report][acc][category][k])
                    else:
                        for acc in current_pos[key][report].keys():
                            # acc = ["매출액", 영업이익", "법인세차감전", "당기순이익"]
                            for category in current_pos[key][report][acc].keys():
                                # category = ["누계", "당기"]
                                for k in sorted(current_pos[key][report][acc][category].keys()):
                                    # k = ["YYYY 1/4", "YYYY 2/4", "YYYY 3/4", "YYYY 4/4"]
                                    logger.error("{}\t{}\t{}\t{}\t{}\t{}".format(key, report, acc, category, k,
                                                                                 current_pos[key][report][acc][
                                                                                     category][k]))
        logger.info(data)

    for k in data.keys():
        avg_sales_op_profit_rate = None
        avg_sales = None
        avg_op_profit = None
        avg_net_income = None
        last_sales_op_profit_rate = None
        last_sales = None
        last_op_profit = None
        last_net_income = None
        before_sales = None
        before_op_profit = None
        before_net_income = None
        fcf_last_5 = None
        ocf_last_5 = None
        earn_last_5 = None
        pl_last_5 = None
        last_5_keys = list(data[k]["CF"]["영업활동현금흐름"].keys())[-5:]
        for lastkey in last_5_keys:
            if lastkey not in data[k]["CF"]["FCF"].keys() or lastkey not in data[k]["CF"]["영업활동현금흐름"].keys() \
                    or lastkey not in data[k]["FS"]["RetainedEarnings"].keys() or lastkey not in data[k]["PL"]["Q"][
                "누계당기순이익추이"].keys():
                last_5_keys.remove(lastkey)
        try:
            fcf_last_5 = {lk: data[k]["CF"]["FCF"][lk] for lk in last_5_keys}
            ocf_last_5 = {lk: data[k]["CF"]["영업활동현금흐름"][lk] for lk in last_5_keys}
            earn_last_5 = {lk: data[k]["FS"]["RetainedEarnings"][lk] for lk in last_5_keys}
            pl_last_5 = {lk: data[k]["PL"]["Q"]["누계당기순이익추이"][lk] for lk in last_5_keys}
        except Exception as e:
            print(last_5_keys)
            print(k)
            print(fcf_last_5)
            print(ocf_last_5)
            print(earn_last_5)
            print(pl_last_5)
        print(k, data[k]["corp_name"], "*" * 100)
        for key in data[k]["PL"]["Y"].keys():
            print("연간", key, data[k]["PL"]["Y"][key])
        print("연간", data[k]["AverageRate"]["Y"])
        for key in data[k]["PL"]["Q"].keys():
            print("당기", key, data[k]["PL"]["Q"][key])
        print("당기", data[k]["AverageRate"]["Q"])
        print("재무상태표-자산총계", data[k]["FS"]["TotalAsset"])
        print("재무상태표-부채총계", data[k]["FS"]["TotalDebt"])
        print("재무상태표-이익잉여금", data[k]["FS"]["RetainedEarnings"])
        print("현금흐름표-영업활동현금흐름", data[k]["CF"]["영업활동현금흐름"])
        print("현금흐름표-유형자산취득", data[k]["CF"]["유형자산취득"])
        print("현금흐름표-무형자산취득", data[k]["CF"]["무형자산취득"])
        print("FreeCashFlow", data[k]["CF"]["FCF"])
        # print("here1?")
        if "매출액영업이익률" in data[k]["AverageRate"]["Y"].keys() \
                and "매출액" in data[k]["AverageRate"]["Y"].keys() \
                and "영업이익" in data[k]["AverageRate"]["Y"].keys() \
                and "당기순이익" in data[k]["AverageRate"]["Y"].keys():
            # print("here2?")
            avg_sales_op_profit_rate = data[k]["AverageRate"]["Y"]["매출액영업이익률"]
            avg_sales = data[k]["AverageRate"]["Y"]["매출액"]
            avg_op_profit = data[k]["AverageRate"]["Y"]["영업이익"]
            avg_net_income = data[k]["AverageRate"]["Y"]["당기순이익"]

            if "매출액영업이익률" in data[k]["PL"]["Q"].keys():
                # print("here3?")
                last_sales_op_profit_rate = data[k]["PL"]["Q"]["매출액영업이익률"].popitem()[1] if len(
                    data[k]["PL"]["Q"]["매출액영업이익률"]) > 0 else None
                last_sales = data[k]["PL"]["Q"]["누계매출액추이"].popitem()[1] if len(
                    data[k]["PL"]["Q"]["누계매출액추이"]) > 0 else None
                if "매출액" in data[k]["PL"]["Y"].keys():
                    data[k]["PL"]["Y"]["매출액"].popitem() if len(data[k]["PL"]["Y"]["매출액"]) > 0 else None
                    before_sales = data[k]["PL"]["Y"]["매출액"].popitem()[1] if len(
                        data[k]["PL"]["Y"]["매출액"]) > 0 else None
                last_op_profit = data[k]["PL"]["Q"]["누계영업이익추이"].popitem()[1] if len(
                    data[k]["PL"]["Q"]["누계영업이익추이"]) > 0 else None
                if "영업이익" in data[k]["PL"]["Y"].keys():
                    data[k]["PL"]["Y"]["영업이익"].popitem() if len(data[k]["PL"]["Y"]["영업이익"]) > 0 else None
                    before_op_profit = data[k]["PL"]["Y"]["영업이익"].popitem()[1] if len(
                        data[k]["PL"]["Y"]["영업이익"]) > 0 else None
                last_net_income = data[k]["PL"]["Q"]["누계당기순이익추이"].popitem()[1] if len(
                    data[k]["PL"]["Q"]["누계당기순이익추이"]) > 0 else None
                if "당기순이익" in data[k]["PL"]["Y"].keys():
                    data[k]["PL"]["Y"]["당기순이익"].popitem() if len(data[k]["PL"]["Y"]["당기순이익"]) > 0 else None
                    before_net_income = data[k]["PL"]["Y"]["당기순이익"].popitem()[1] if len(
                        data[k]["PL"]["Y"]["당기순이익"]) > 0 else None
        # print("here4?")
        if avg_sales_op_profit_rate and last_sales_op_profit_rate:
            if last_sales_op_profit_rate > 0 and avg_sales_op_profit_rate > 0 and last_sales_op_profit_rate > avg_sales_op_profit_rate:
                # print("here5?")
                if avg_sales and last_sales and before_sales and \
                        avg_net_income and last_net_income and before_net_income and \
                        last_sales > avg_sales and last_sales > before_sales and \
                        last_net_income > avg_net_income and last_net_income > before_net_income:
                    if last_sales_op_profit_rate > 20:
                        best[k] = {"stock_code": k, "corp_name": data[k]["corp_name"],
                                   "last_report": data[k]["last_report"], "업종": data[k]["category"],
                                   "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                   "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                   "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                   "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                   "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                   "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                   "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                                   "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                   "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                   "직전당기순이익": format(before_net_income, ",") if before_net_income is not None else None,
                                   "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None,
                                   "FCF": fcf_last_5 if fcf_last_5 is not None else None,
                                   "OCF": ocf_last_5 if ocf_last_5 is not None else None,
                                   "EARN": earn_last_5 if earn_last_5 is not None else None,
                                   "PL": pl_last_5 if pl_last_5 is not None else None
                                   }
                        call = json.loads(requests.get(
                            "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                                k)).content.decode("utf-8"))
                        best[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                        best[k]["PER"] = call["per"]
                        best[k]["EPS"] = call["eps"]
                        best[k]["PBR"] = call["pbr"]
                        best[k]["현재가"] = f'{call["now"]:,}'
                        best[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                data[k][
                                                                                                    "list_shares"] else 0
                        best[k]["PER2"] = round(call["now"] / best[k]["EPS2"], 0) if best[k]["EPS2"] != 0 else 0
                        best[k]["예상주가"] = format(int(round(best[k]["EPS2"] * best[k]["PER"], 0)), ",") if best[k][
                                                                                                              "EPS2"] and \
                                                                                                          best[k][
                                                                                                              "PER"] else 0
                    elif np.sign(last_sales_op_profit_rate) > np.sign(avg_sales_op_profit_rate):
                        best[k] = {"stock_code": k, "corp_name": data[k]["corp_name"],
                                   "last_report": data[k]["last_report"], "업종": data[k]["category"],
                                   "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                   "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                   "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                   "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                   "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                   "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                   "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                                   "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                   "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                   "직전당기순이익": format(before_net_income, ",") if before_net_income is not None else None,
                                   "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None,
                                   "FCF": fcf_last_5 if fcf_last_5 is not None else None,
                                   "OCF": ocf_last_5 if ocf_last_5 is not None else None,
                                   "EARN": earn_last_5 if earn_last_5 is not None else None,
                                   "PL": pl_last_5 if pl_last_5 is not None else None}
                        call = json.loads(requests.get(
                            "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                                k)).content.decode("utf-8"))
                        best[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                        best[k]["PER"] = call["per"]
                        best[k]["EPS"] = call["eps"]
                        best[k]["PBR"] = call["pbr"]
                        best[k]["현재가"] = f'{call["now"]:,}'
                        best[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                data[k][
                                                                                                    "list_shares"] else 0
                        best[k]["PER2"] = round(call["now"] / best[k]["EPS2"], 0) if best[k]["EPS2"] != 0 else 0
                        best[k]["예상주가"] = format(int(round(best[k]["EPS2"] * best[k]["PER"], 0)), ",") if best[k][
                                                                                                              "EPS2"] and \
                                                                                                          best[k][
                                                                                                              "PER"] else 0
                    else:
                        better[k] = {"stock_code": k, "corp_name": data[k]["corp_name"],
                                     "last_report": data[k]["last_report"], "업종": data[k]["category"],
                                     "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                     "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                     "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                     "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                     "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                     "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                     "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                                     "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                     "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                     "직전당기순이익": format(before_net_income,
                                                       ",") if before_net_income is not None else None,
                                     "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None,
                                     "FCF": fcf_last_5 if fcf_last_5 is not None else None,
                                     "OCF": ocf_last_5 if ocf_last_5 is not None else None,
                                     "EARN": earn_last_5 if earn_last_5 is not None else None,
                                     "PL": pl_last_5 if pl_last_5 is not None else None
                                     }
                        call = json.loads(requests.get(
                            "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                                k)).content.decode("utf-8"))
                        better[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                        better[k]["PER"] = call["per"]
                        better[k]["EPS"] = call["eps"]
                        better[k]["PBR"] = call["pbr"]
                        better[k]["현재가"] = f'{call["now"]:,}'
                        better[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                  data[k][
                                                                                                      "list_shares"] else 0
                        better[k]["PER2"] = round(call["now"] / better[k]["EPS2"], 0) if better[k]["EPS2"] != 0 else 0
                        better[k]["예상주가"] = format(int(round(better[k]["EPS2"] * better[k]["PER"], 0)), ",") if \
                        better[k]["EPS2"] and better[k]["PER"] else 0
                else:
                    if last_sales_op_profit_rate > 15:
                        better[k] = {"stock_code": k, "corp_name": data[k]["corp_name"],
                                     "last_report": data[k]["last_report"], "업종": data[k]["category"],
                                     "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                     "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                     "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                     "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                     "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                     "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                     "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                                     "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                     "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                     "직전당기순이익": format(before_net_income,
                                                       ",") if before_net_income is not None else None,
                                     "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None,
                                     "FCF": fcf_last_5 if fcf_last_5 is not None else None,
                                     "OCF": ocf_last_5 if ocf_last_5 is not None else None,
                                     "EARN": earn_last_5 if earn_last_5 is not None else None,
                                     "PL": pl_last_5 if pl_last_5 is not None else None
                                     }
                        call = json.loads(requests.get(
                            "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                                k)).content.decode("utf-8"))
                        better[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                        better[k]["PER"] = call["per"]
                        better[k]["EPS"] = call["eps"]
                        better[k]["PBR"] = call["pbr"]
                        better[k]["현재가"] = f'{call["now"]:,}'
                        better[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                  data[k][
                                                                                                      "list_shares"] else 0
                        better[k]["PER2"] = round(call["now"] / better[k]["EPS2"], 0) if better[k]["EPS2"] != 0 else 0
                        better[k]["예상주가"] = format(int(round(better[k]["EPS2"] * better[k]["PER"], 0)), ",") if \
                        better[k]["EPS2"] and better[k]["PER"] else 0
                    else:
                        # print("here7?")
                        good[k] = {"stock_code": k, "corp_name": data[k]["corp_name"],
                                   "last_report": data[k]["last_report"], "업종": data[k]["category"],
                                   "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                   "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                   "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                   "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                   "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                   "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                   "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                                   "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                   "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                   "직전당기순이익": format(before_net_income, ",") if before_net_income is not None else None,
                                   "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None,
                                   "FCF": fcf_last_5 if fcf_last_5 is not None else None,
                                   "OCF": ocf_last_5 if ocf_last_5 is not None else None,
                                   "EARN": earn_last_5 if earn_last_5 is not None else None,
                                   "PL": pl_last_5 if pl_last_5 is not None else None
                                   }
                        call = json.loads(requests.get(
                            "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                                k)).content.decode("utf-8"))
                        good[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                        good[k]["PER"] = call["per"]
                        good[k]["EPS"] = call["eps"]
                        good[k]["PBR"] = call["pbr"]
                        good[k]["현재가"] = f'{call["now"]:,}'
                        good[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                data[k][
                                                                                                    "list_shares"] else 0
                        good[k]["PER2"] = round(call["now"] / good[k]["EPS2"], 0) if good[k]["EPS2"] != 0 else 0
                        good[k]["예상주가"] = format(int(round(good[k]["EPS2"] * good[k]["PER"], 0)), ",") if good[k][
                                                                                                              "EPS2"] and \
                                                                                                          good[k][
                                                                                                              "PER"] else 0
            else:
                if last_sales_op_profit_rate > 15:
                    better[k] = {"stock_code": k, "corp_name": data[k]["corp_name"],
                                 "last_report": data[k]["last_report"], "업종": data[k]["category"],
                                 "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                 "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                 "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                 "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                 "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                 "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                 "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                                 "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                 "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                 "직전당기순이익": format(before_net_income, ",") if before_net_income is not None else None,
                                 "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None,
                                 "FCF": fcf_last_5 if fcf_last_5 is not None else None,
                                 "OCF": ocf_last_5 if ocf_last_5 is not None else None,
                                 "EARN": earn_last_5 if earn_last_5 is not None else None,
                                 "PL": pl_last_5 if pl_last_5 is not None else None
                                 }
                    call = json.loads(requests.get(
                        "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                            k)).content.decode("utf-8"))
                    better[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                    better[k]["PER"] = call["per"]
                    better[k]["EPS"] = call["eps"]
                    better[k]["PBR"] = call["pbr"]
                    better[k]["현재가"] = f'{call["now"]:,}'
                    better[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                              data[k][
                                                                                                  "list_shares"] else 0
                    better[k]["PER2"] = round(call["now"] / better[k]["EPS2"], 0) if better[k]["EPS2"] != 0 else 0
                    better[k]["예상주가"] = format(int(round(better[k]["EPS2"] * better[k]["PER"], 0)), ",") if better[k][
                                                                                                                "EPS2"] and \
                                                                                                            better[k][
                                                                                                                "PER"] else 0
                else:
                    soso[k] = {"stock_code": k, "corp_name": data[k]["corp_name"],
                               "last_report": data[k]["last_report"], "업종": data[k]["category"],
                               "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                               "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                               "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                               "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                               "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                               "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                               "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                               "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                               "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                               "직전당기순이익": format(before_net_income, ",") if before_net_income is not None else None,
                               "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None,
                               "FCF": fcf_last_5 if fcf_last_5 is not None else None,
                               "OCF": ocf_last_5 if ocf_last_5 is not None else None,
                               "EARN": earn_last_5 if earn_last_5 is not None else None,
                               "PL": pl_last_5 if pl_last_5 is not None else None
                               }
                    call = json.loads(requests.get(
                        "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                            k)).content.decode("utf-8"))
                    soso[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                    soso[k]["PER"] = call["per"]
                    soso[k]["EPS"] = call["eps"]
                    soso[k]["PBR"] = call["pbr"]
                    soso[k]["현재가"] = f'{call["now"]:,}'
                    soso[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                            data[k][
                                                                                                "list_shares"] else 0
                    soso[k]["PER2"] = round(call["now"] / soso[k]["EPS2"], 0) if soso[k]["EPS2"] != 0 else 0
                    soso[k]["예상주가"] = format(int(round(soso[k]["EPS2"] * soso[k]["PER"], 0)), ",") if soso[k][
                                                                                                          "EPS2"] and \
                                                                                                      soso[k][
                                                                                                          "PER"] else 0
        else:
            soso[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "last_report": data[k]["last_report"],
                       "업종": data[k]["category"],
                       "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                       "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                       "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                       "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                       "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                       "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                       "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                       "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                       "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                       "직전당기순이익": format(before_net_income, ",") if before_net_income is not None else None,
                       "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None,
                       "FCF": fcf_last_5 if fcf_last_5 is not None else None,
                       "OCF": ocf_last_5 if ocf_last_5 is not None else None,
                       "EARN": earn_last_5 if earn_last_5 is not None else None,
                       "PL": pl_last_5 if pl_last_5 is not None else None
                       }
            call = json.loads(requests.get(
                "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                    k)).content.decode("utf-8"))
            soso[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
            soso[k]["PER"] = call["per"]
            soso[k]["EPS"] = call["eps"]
            soso[k]["PBR"] = call["pbr"]
            soso[k]["현재가"] = f'{call["now"]:,}'
            soso[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                    data[k][
                                                                                        "list_shares"] else 0
            soso[k]["PER2"] = round(call["now"] / soso[k]["EPS2"], 0) if soso[k]["EPS2"] != 0 else 0
            soso[k]["예상주가"] = format(int(round(soso[k]["EPS2"] * soso[k]["PER"], 0)), ",") if soso[k]["EPS2"] and \
                                                                                              soso[k]["PER"] else 0
            # info_lack[k] = {"corp_name": data[k]["corp_name"], "corp_code": data[k]["corp_code"]}
    logger.info("{} {} {} {}".format("*" * 100, "BEST", len(best), "*" * 100))
    for key in best.keys():
        logger.info(best[key])
        # if best[key]["EPS2"] != 0 and best[key]["EPS2"] > best[key]["EPS"] and (best[key]["EPS2"] - best[key]["EPS"])/best[key]["EPS"] * 100 >= 30:
        if "BEST" not in treasure.keys():
            treasure["BEST"] = {}
        treasure["BEST"][key] = {"사명": best[key]["corp_name"], "시가총액": best[key]["시가총액"], "업종": best[key]["업종"],
                                 "최근매출액영업이익률": best[key]["최근매출액영업이익률"], "EPS": best[key]["EPS"],
                                 "추정EPS": best[key]["EPS2"],
                                 "괴리율": round((best[key]["EPS2"] - best[key]["EPS"]) / best[key]["EPS"] * 100,
                                              2)  if best[key]["EPS2"] and best[key]["EPS"] else None, "현재가": best[key]["현재가"], "예상주가": best[key]["예상주가"],
                                 "EARN": best[key]["EARN"],
                                 "FCF": best[key]["FCF"], "OCF": best[key]["OCF"], "PL": best[key]["PL"],
                                 "최종보고서": best[key]["last_report"]}
    logger.info("{} {} {} {}".format("*" * 100, "BETTER", len(better), "*" * 100))
    for key in better.keys():
        logger.info(better[key])
        # if better[key]["EPS2"] != 0 and better[key]["EPS2"] > better[key]["EPS"] and (better[key]["EPS2"] - better[key]["EPS"])/better[key]["EPS"] * 100 >= 30:
        if "BETTER" not in treasure.keys():
            treasure["BETTER"] = {}
        treasure["BETTER"][key] = {"사명": better[key]["corp_name"], "시가총액": better[key]["시가총액"],
                                   "업종": better[key]["업종"], "최근매출액영업이익률": better[key]["최근매출액영업이익률"],
                                   "EPS": better[key]["EPS"], "추정EPS": better[key]["EPS2"], "괴리율": round(
                (better[key]["EPS2"] - better[key]["EPS"]) / better[key]["EPS"] * 100, 2) if better[key]["EPS2"] and better[key]["EPS"] else None,
                                   "현재가": better[key]["현재가"], "예상주가": better[key]["예상주가"], "EARN": better[key]["EARN"],
                                   "FCF": better[key]["FCF"], "OCF": better[key]["OCF"], "PL": better[key]["PL"],
                                   "최종보고서": better[key]["last_report"]}
    logger.info("{} {} {} {}".format("*" * 100, "GOOD", len(good), "*" * 100))
    for key in good.keys():
        logger.info(good[key])
        if all:
            if "GOOD" not in treasure.keys():
                treasure["GOOD"] = {}
            treasure["GOOD"][key] = {"사명": good[key]["corp_name"], "시가총액": good[key]["시가총액"], "업종": good[key]["업종"],
                                     "최근매출액영업이익률": good[key]["최근매출액영업이익률"], "EPS": good[key]["EPS"],
                                     "추정EPS": good[key]["EPS2"],
                                     "괴리율": round((good[key]["EPS2"] - good[key]["EPS"]) / good[key]["EPS"] * 100, 2) if good[key]["EPS2"] and good[key]["EPS"] else None,
                                     "현재가": good[key]["현재가"], "예상주가": good[key]["예상주가"], "EARN": good[key]["EARN"],
                                     "FCF": good[key]["FCF"],
                                     "OCF": good[key]["OCF"], "PL": good[key]["PL"], "최종보고서": good[key]["last_report"]}
        else:
            if good[key]["EPS2"] != 0 and good[key]["EPS2"] > good[key]["EPS"] and (good[key]["EPS2"] - good[key]["EPS"]) / \
                    good[key]["EPS"] * 100 >= 30:
                if "GOOD" not in treasure.keys():
                    treasure["GOOD"] = {}
                treasure["GOOD"][key] = {"사명": good[key]["corp_name"], "시가총액": good[key]["시가총액"], "업종": good[key]["업종"],
                                         "최근매출액영업이익률": good[key]["최근매출액영업이익률"], "EPS": good[key]["EPS"],
                                         "추정EPS": good[key]["EPS2"],
                                         "괴리율": round((good[key]["EPS2"] - good[key]["EPS"]) / good[key]["EPS"] * 100, 2) if good[key]["EPS2"] and good[key]["EPS"] else None,
                                         "현재가": good[key]["현재가"], "예상주가": good[key]["예상주가"], "EARN": good[key]["EARN"],
                                         "FCF": good[key]["FCF"],
                                         "OCF": good[key]["OCF"], "PL": good[key]["PL"], "최종보고서": good[key]["last_report"]}
    logger.info("{} {} {} {}".format("*" * 100, "CHECK", len(soso), "*" * 100))
    for key in soso.keys():
        logger.info(soso[key])
        if all:
            if "SOSO" not in treasure.keys():
                treasure["SOSO"] = {}
            treasure["SOSO"][key] = {"사명": soso[key]["corp_name"], "시가총액": soso[key]["시가총액"], "업종": soso[key]["업종"],
                                     "최근매출액영업이익률": soso[key]["최근매출액영업이익률"], "EPS": soso[key]["EPS"],
                                     "추정EPS": soso[key]["EPS2"],
                                     "괴리율": round((soso[key]["EPS2"] - soso[key]["EPS"]) / soso[key]["EPS"] * 100,
                                                  2) if soso[key]["EPS2"] and soso[key]["EPS"] else None, "현재가": soso[key]["현재가"], "예상주가": soso[key]["예상주가"],
                                     "EARN": soso[key]["EARN"],
                                     "FCF": soso[key]["FCF"], "OCF": soso[key]["OCF"], "PL": soso[key]["PL"],
                                     "최종보고서": soso[key]["last_report"]}
        else:
            if soso[key]["EPS2"] != 0 and soso[key]["EPS2"] > soso[key]["EPS"] and (soso[key]["EPS2"] - soso[key]["EPS"]) / \
                    soso[key]["EPS"] * 100 >= 30:
                if "SOSO" not in treasure.keys():
                    treasure["SOSO"] = {}
                treasure["SOSO"][key] = {"사명": soso[key]["corp_name"], "시가총액": soso[key]["시가총액"], "업종": soso[key]["업종"],
                                         "최근매출액영업이익률": soso[key]["최근매출액영업이익률"], "EPS": soso[key]["EPS"],
                                         "추정EPS": soso[key]["EPS2"],
                                         "괴리율": round((soso[key]["EPS2"] - soso[key]["EPS"]) / soso[key]["EPS"] * 100,
                                                      2) if soso[key]["EPS2"] and soso[key]["EPS"] else None, "현재가": soso[key]["현재가"], "예상주가": soso[key]["예상주가"],
                                         "EARN": soso[key]["EARN"],
                                         "FCF": soso[key]["FCF"], "OCF": soso[key]["OCF"], "PL": soso[key]["PL"],
                                         "최종보고서": soso[key]["last_report"]}
    logger.info(none_list)
    return treasure


def dictionary_add(d):
    tmp_dic = {}
    for key in d.keys():  # key = ["기계장치의 취득"...등등]
        for key1 in d[key].keys():  # key1 = ["2020 3/4"]
            if "Rate" in key1:
                continue
            if key1 not in tmp_dic.keys():
                tmp_dic[key1] = {}
            for key2 in d[key][key1].keys():  # key2 = ["몇기, 몇기"]
                if key2 not in tmp_dic[key1].keys():
                    tmp_dic[key1][key2] = int(d[key][key1][key2])
                else:
                    tmp_dic[key1][key2] += int(d[key][key1][key2])
    print(tmp_dic)
    return tmp_dic

def hidden_pearl_finding_with_regular_report(rcept_no, bgn_dt, end_dt=None):
    import sys
    import os
    import django
    from OpenDartPipe import pipe
    # sys.path.append(r'E:\Github\Waver\MainBoard')
    # sys.path.append(r'E:\Github\Waver\MainBoard\MainBoard')
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    import json
    import numpy as np
    import requests


    current_pos = None
    treasure = {}
    trash = {}
    data = {}
    best = {}
    better = {}
    good = {}
    soso = {}
    lists = None
    none_list = []
    # 날짜 정보 셋팅
    dateDict = new_get_dateDict()
    # 종목 정보 셋팅
    # DEBUG = True
    DEBUG = False
    # USE_JSON = False
    USE_JSON = True

    dart = pipe.Pipe()
    dart.create()
    if end_dt:
        # dart.get_regular_reporting(bgn_dt, end_dt)
        stockInfo = dart.get_regular_reporting_corp_info(rcept_no, bgn_dt, end_dt)
    else:
        # dart.get_regular_reporting(bgn_dt)
        stockInfo = dart.get_regular_reporting_corp_info(rcept_no, bgn_dt)
    print(len(stockInfo), stockInfo)
    for stock in stockInfo:
        result = new_find_hidden_pearl_with_dartpipe_single(stock["stock_code"])
        send_hidden_pearl_message(result)

def new_find_hidden_pearl_with_dartpipe_single(code, bgn_dt=None, end_dt=None):
    import sys
    import os
    import django
    from OpenDartPipe import pipe
    # sys.path.append(r'E:\Github\Waver\MainBoard')
    # sys.path.append(r'E:\Github\Waver\MainBoard\MainBoard')
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    import json
    import numpy as np
    import requests
    # import logging
    #
    # logfile = 'detector'
    # if not os.path.exists('./logs'):
    #     os.makedirs('./logs')
    # now = datetime.now().strftime("%Y%m%d%H%M%S")
    #
    # logger = logging.getLogger(__name__)
    # formatter = logging.Formatter('[%(asctime)s][%(filename)s:%(lineno)s] >> %(message)s')
    #
    # streamHandler = logging.StreamHandler()
    # fileHandler = logging.FileHandler("./logs/{}_{}.log".format(logfile, now))
    #
    # streamHandler.setFormatter(formatter)
    # fileHandler.setFormatter(formatter)
    #
    # logger.addHandler(streamHandler)
    # logger.addHandler(fileHandler)
    # logger.setLevel(level=logging.INFO)

    # logging
    # logging.basicConfig(filename=logfile, filemode='w', level=logging.DEBUG)
    # logging.debug("Log started at %s", str(datetime.datetime.now()))

    current_pos = None
    treasure = {}
    trash = {}
    data = {}
    best = {}
    better = {}
    good = {}
    soso = {}
    lists = None
    none_list = []
    # 날짜 정보 셋팅
    dateDict = new_get_dateDict()
    # 종목 정보 셋팅
    # DEBUG = True
    DEBUG = False
    # USE_JSON = False
    USE_JSON = True
    # stockInfo = detective_db.Stocks.objects.filter(category_name__contains="일반 목적", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(category_name__contains="특수", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(category_name__contains="생물", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(category_name__contains="화학", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(category_name__contains="자연", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(category_name__contains="건축", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(category_name__contains="축전지", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(code="005930", listing='Y')
    stockInfo = detective_db.Stocks.objects.filter(code=code, listing='Y')
    dart = pipe.Pipe()
    dart.create()
    for stock in stockInfo:
        current_key = None
        ret, code = dart.get_corp_code(stock.code)
        try:
            if ret:
                data[stock.code] = {"corp_code": code,
                                    "last_report": None,
                                    "corp_name": stock.name,
                                    "category": stock.category_name,
                                    "list_shares": stock.issued_shares,
                                    "PL": {"Y": {}, "Q": {}},
                                    "FS": {"TotalAsset": {}, "TotalDebt": {}, "RetainedEarnings": {}},
                                    "CF": {"영업활동현금흐름": {}, "유형자산취득": {}, "무형자산취득": {}, "FCF": {}},
                                    "AverageRate": {"Y": {}, "Q": {}}}
                # print(dateDict["yyyy2"], dateDict)
                if bgn_dt is None:
                    lists = dart.get_list(corp_code=code, bgn_de=dateDict["yyyy2"], pblntf_ty='A', req_type=True)[
                                "list"][:6]
                elif end_dt is None:
                    lists = dart.get_list(corp_code=code, bgn_de=bgn_dt, pblntf_ty='A', req_type=True)["list"][:6]
                else:
                    lists = dart.get_list(corp_code=code, bgn_de=bgn_dt, end_de=end_dt, pblntf_ty='A', req_type=True)[
                                "list"][:6]
                # lists = dart.get_list(corp_code=code, bgn_de=dateDict["yyyy2"], pblntf_ty='A', req_type=True)["list"][:5]
                for l in lists:
                    if data[stock.code]["last_report"] is None:
                        data[stock.code]["last_report"] = l["report_nm"]
                    else:
                        if data[stock.code]["last_report"] < l["report_nm"]: data[stock.code]["last_report"] = l[
                            "report_nm"]
                    logger.info(l)
                req_list, req_list2 = dart.get_req_lists(lists)
                result = dart.get_fnlttSinglAcnt_from_req_list(code, req_list, "ALL")
                current_pos = result
                # for key in result.keys():  # key = ["연결재무제표", "재무제표"]
                #     for report in result[key].keys():  # report = ["재무상태표", "손익계산서"]
                #         if report == "재무상태표":
                #             for acc in result[key][report].keys():
                #                 # acc = ["유동자산", "비유동자산", "자산총계", "유동부채", "비유동부채", "부채총계", "자본금", "이익잉여금", "자본총계"]
                #                 for category in sorted(result[key][report][acc].keys()):
                #                     # category = ["YYYY 1/4", "YYYY 2/4", "YYYY 3/4", "YYYY 4/4"]
                #                     print(key, report, acc, category, result[key][report][acc][category])
                #                     # for k in result[key][report][acc][category].keys():
                #                     #     print(key, report, acc, category, k, result[key][report][acc][category][k])
                #         else:
                #             for acc in result[key][report].keys():
                #                 # acc = ["매출액", 영업이익", "법인세차감전", "당기순이익"]
                #                 for category in result[key][report][acc].keys():
                #                     # category = ["누계", "당기"]
                #                     for k in sorted(result[key][report][acc][category].keys()):
                #                         # k = ["YYYY 1/4", "YYYY 2/4", "YYYY 3/4", "YYYY 4/4"]
                #                         print(key, report, acc, category, k, result[key][report][acc][category][k])
                d1 = None
                d2 = None
                d3 = None
                d4 = None
                d5 = None
                d6 = None
                d7 = None
                d8 = None
                d9 = None
                d10 = None
                d11 = None
                d12 = None
                d13 = None
                d14 = None
                dicTemp0 = {}
                dicTemp1 = {}
                dicTemp2 = {}
                dicTemp3 = {}
                dicTemp4 = {}
                dicTemp5 = {}
                dicTemp6 = {}
                dicTemp7 = {}
                dicTemp8 = {}
                dicTemp9 = {}
                dicTemp10 = {}
                dicTemp11 = {}
                dicTemp12 = {}
                dicTemp13 = {}
                dicTemp14 = {}
                # if stock == "006360":
                #     print()
                d1keys = ["매출", "수익(매출액)", "I.  매출액", "영업수익", "매출액", "Ⅰ. 매출액", "매출 및 지분법 손익", "매출 및 지분법손익"]
                d2keys = ["영업이익(손실)", "영업이익 (손실)", "영업이익", "영업손익", "V. 영업손익", "Ⅴ. 영업이익", "Ⅴ. 영업이익(손실)", "V. 영업이익",
                          "영업손실"]
                d8keys = ["당기순이익(손실)", "당기순이익 (손실)", "당기순이익", "분기순이익", "반기순이익", "당기순이익(손실)", "분기순이익(손실)", "반기순이익(손실)",
                          "연결당기순이익", "연결분기순이익", "연결반기순이익", "연결당기순이익(손실)", "연결분기순이익(손실)", "연결반기순이익(손실)", "당기순손익",
                          "분기순손익",
                          "반기순손익", "지배기업 소유주지분", "지배기업의 소유주에게 귀속되는 당기순이익(손실)", "당기순손실", "분기순손실", "반기순손실",
                          "Ⅷ. 당기순이익(손실)", "지배기업 소유주 지분",
                          "Ⅷ. 당기순이익", "VIII. 당기순이익", "지배기업 소유주", "VIII. 분기순손익", "VIII. 분기순이익", "I.당기순이익", "I.반기순이익",
                          "I.분기순이익", "반기연결순이익(손실)", "지배기업의 소유주지분", "지배기업소유주지분", "지배기업의소유주지분"]
                d10keys = ["영업활동현금흐름", "영업활동 현금흐름", "영업활동으로 인한 현금흐름", "영업활동 순현금흐름유입", "영업활동으로인한현금흐름", "영업활동으로 인한 순현금흐름",
                           "Ⅰ. 영업활동으로 인한 현금흐름", "Ⅰ. 영업활동으로 인한 현금흐름", "영업활동순현금흐름 합계", "영업활동순현금흐름", "I. 영업활동현금흐름"]
                d11keys = ["유형자산의 취득", "유형자산 취득", "유형자산의취득"]
                d12keys = ["무형자산의 취득", "무형자산 취득", "무형자산의취득", "무형자산의 증가"]
                d13keys = ["토지의 취득", "건물의 취득", "구축물의 취득", "기계장치의 취득", "차량운반구의 취득", "공구와기구의 취득", "비품의 취득",
                           "기타유형자산의 취득", "건설중인자산의 취득", "투자부동산의 취득", "집기비품의 취득", "시험기기의 취득", "시설공사의 취득",
                           "토지의취득", "건물의취득", "구축물의취득", "기계장치의취득", "차량운반구의취득", "공구와기구의취득", "비품의취득",
                           "기타유형자산의취득", "건설중인자산의취득", "투자부동산의취득", "집기비품의취득", "시험기기의취득", "시설공사의취득"
                           ]
                d14keys = ["컴퓨터소프트웨어의 취득", "산업재산권의 취득", "소프트웨어의 취득", "기타무형자산의 취득", "소프트웨어의 증가",
                           "컴퓨터소프트웨어의취득", "산업재산권의취득", "소프트웨어의취득", "기타무형자산의취득", "소프트웨어의증가"]
                # if stock == "006360":
                #     print()
                if result is not {} and "연결재무제표" in result.keys():
                    logger.info("연결재무제표 start")
                    if "포괄손익계산서" in result["연결재무제표"].keys():
                        logger.info("연결재무제표 포괄손익계산서 start")
                        tmp_result1 = {key: result["연결재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                       result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d1keys}}
                        tmp_result2 = {key: result["연결재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                       result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d2keys}}
                        tmp_result3 = {key: result["연결재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                       result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d1keys}}
                        tmp_result4 = {key: result["연결재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                       result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d2keys}}
                        tmp_result8 = {key: result["연결재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                       result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d8keys}}
                        tmp_result9 = {key: result["연결재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                       result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d8keys}}
                        if tmp_result1:
                            for key in tmp_result1.keys():
                                if d1 is None:
                                    d1 = tmp_result1[key]
                                else:
                                    d1.update(tmp_result1[key])
                        if tmp_result2:
                            for key in tmp_result2.keys():
                                if d2 is None:
                                    d2 = tmp_result2[key]
                                else:
                                    d2.update(tmp_result2[key])
                        if tmp_result3:
                            for key in tmp_result3.keys():
                                if d3 is None:
                                    d3 = tmp_result3[key]
                                else:
                                    d3.update(tmp_result3[key])
                        if tmp_result4:
                            for key in tmp_result4.keys():
                                if d4 is None:
                                    d4 = tmp_result4[key]
                                else:
                                    d4.update(tmp_result4[key])
                        if tmp_result8:
                            for key in tmp_result8.keys():
                                if d8 is None:
                                    d8 = tmp_result8[key]
                                else:
                                    d8.update(tmp_result8[key])
                        if tmp_result9:
                            for key in tmp_result9.keys():
                                if d9 is None:
                                    d9 = tmp_result9[key]
                                else:
                                    d9.update(tmp_result9[key])
                    if "손익계산서" in result["연결재무제표"].keys():
                        logger.info("연결재무제표 손익계산서 start")
                        tmp_result1 = {key: result["연결재무제표"]["손익계산서"][key]["누계"] for key in
                                       result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d1keys}}
                        tmp_result2 = {key: result["연결재무제표"]["손익계산서"][key]["누계"] for key in
                                       result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d2keys}}
                        tmp_result3 = {key: result["연결재무제표"]["손익계산서"][key]["당기"] for key in
                                       result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d1keys}}
                        tmp_result4 = {key: result["연결재무제표"]["손익계산서"][key]["당기"] for key in
                                       result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d2keys}}
                        tmp_result8 = {key: result["연결재무제표"]["손익계산서"][key]["누계"] for key in
                                       result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d8keys}}
                        tmp_result9 = {key: result["연결재무제표"]["손익계산서"][key]["당기"] for key in
                                       result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d8keys}}
                        if tmp_result1:
                            for key in tmp_result1.keys():
                                if d1 is None:
                                    d1 = tmp_result1[key]
                                else:
                                    d1.update(tmp_result1[key])
                        if tmp_result2:
                            for key in tmp_result2.keys():
                                if d2 is None:
                                    d2 = tmp_result2[key]
                                else:
                                    d2.update(tmp_result2[key])
                        if tmp_result3:
                            for key in tmp_result3.keys():
                                if d3 is None:
                                    d3 = tmp_result3[key]
                                else:
                                    d3.update(tmp_result3[key])
                        if tmp_result4:
                            for key in tmp_result4.keys():
                                if d4 is None:
                                    d4 = tmp_result4[key]
                                else:
                                    d4.update(tmp_result4[key])
                        if tmp_result8:
                            for key in tmp_result8.keys():
                                if d8 is None:
                                    d8 = tmp_result8[key]
                                else:
                                    d8.update(tmp_result8[key])
                        if tmp_result9:
                            for key in tmp_result9.keys():
                                if d9 is None:
                                    d9 = tmp_result9[key]
                                else:
                                    d9.update(tmp_result9[key])
                    if "현금흐름표" in result["연결재무제표"].keys():
                        logger.info("연결재무제표 현금흐름표 start")
                        tmp_result10 = {key: result["연결재무제표"]["현금흐름표"][key] for key in
                                        result["연결재무제표"]["현금흐름표"].keys() & {keys for keys in d10keys}}
                        tmp_result11 = {key: result["연결재무제표"]["현금흐름표"][key] for key in
                                        result["연결재무제표"]["현금흐름표"].keys() & {keys for keys in d11keys}}
                        tmp_result12 = {key: result["연결재무제표"]["현금흐름표"][key] for key in
                                        result["연결재무제표"]["현금흐름표"].keys() & {keys for keys in d12keys}}
                        tmp_result13 = {key: result["연결재무제표"]["현금흐름표"][key] for key in
                                        result["연결재무제표"]["현금흐름표"].keys() & {keys for keys in d13keys}}
                        tmp_result14 = {key: result["연결재무제표"]["현금흐름표"][key] for key in
                                        result["연결재무제표"]["현금흐름표"].keys() & {keys for keys in d14keys}}
                        if tmp_result10:
                            for key in tmp_result10.keys():
                                if d10 is None:
                                    d10 = tmp_result10[key]
                                else:
                                    d10.update(tmp_result10[key])
                        if tmp_result11:
                            for key in tmp_result11.keys():
                                if d11 is None:
                                    d11 = tmp_result11[key]
                                else:
                                    d11.update(tmp_result11[key])
                        if tmp_result12:
                            for key in tmp_result12.keys():
                                if d12 is None:
                                    d12 = tmp_result12[key]
                                else:
                                    d12.update(tmp_result12[key])
                        if tmp_result13:
                            d13 = dictionary_add(tmp_result13)
                            # for key in tmp_result13.keys():
                            #     if d13 is None:
                            #         d13 = tmp_result13[key]
                            #     else:
                            #         d13.update(tmp_result13[key])
                        if tmp_result14:
                            d14 = dictionary_add(tmp_result14)
                            # for key in tmp_result14.keys():
                            #     if d14 is None:
                            #         d14 = tmp_result14[key]
                            #     else:
                            #         d14.update(tmp_result14[key])
                    if d11 is None: d11 = d13
                    if d12 is None: d12 = d14
                    d5 = result["연결재무제표"]["재무상태표"]["자산총계"] if "자산총계" in result["연결재무제표"]["재무상태표"].keys() else None
                    d6 = result["연결재무제표"]["재무상태표"]["부채총계"] if "부채총계" in result["연결재무제표"]["재무상태표"].keys() else None
                    d7 = result["연결재무제표"]["재무상태표"]["이익잉여금"] if "이익잉여금" in result["연결재무제표"]["재무상태표"].keys() else None
                    if d5 is None:
                        if "자  산  총  계" in result["연결재무제표"]["재무상태표"].keys():
                            d5 = result["연결재무제표"]["재무상태표"]["자  산  총  계"]
                    else:
                        if "자  산  총  계" in result["연결재무제표"]["재무상태표"].keys():
                            d5.update(result["연결재무제표"]["재무상태표"]["자  산  총  계"])
                    if d5 is None:
                        if "자산 총계" in result["연결재무제표"]["재무상태표"].keys():
                            d5 = result["연결재무제표"]["재무상태표"]["자산 총계"]
                    else:
                        if "자산 총계" in result["연결재무제표"]["재무상태표"].keys():
                            d5.update(result["연결재무제표"]["재무상태표"]["자산 총계"])
                    if d6 is None:
                        if "부  채  총  계" in result["연결재무제표"]["재무상태표"].keys():
                            d6 = result["연결재무제표"]["재무상태표"]["부  채  총  계"]
                    else:
                        if "부  채  총  계" in result["연결재무제표"]["재무상태표"].keys():
                            d6.update(result["연결재무제표"]["재무상태표"]["부  채  총  계"])
                    if d6 is None:
                        if "부채 총계" in result["연결재무제표"]["재무상태표"].keys():
                            d6 = result["연결재무제표"]["재무상태표"]["부채 총계"]
                    else:
                        if "부채 총계" in result["연결재무제표"]["재무상태표"].keys():
                            d6.update(result["연결재무제표"]["재무상태표"]["부채 총계"])
                    if d7 is None:
                        if "이익잉여금(결손금)" in result["연결재무제표"]["재무상태표"].keys():
                            d7 = result["연결재무제표"]["재무상태표"]["이익잉여금(결손금)"]
                    else:
                        if "이익잉여금(결손금)" in result["연결재무제표"]["재무상태표"].keys():
                            d7.update(result["연결재무제표"]["재무상태표"]["이익잉여금(결손금)"])
                    if d7 is None:
                        if "결손금" in result["연결재무제표"]["재무상태표"].keys():
                            d7 = result["연결재무제표"]["재무상태표"]["결손금"]
                    else:
                        if "결손금" in result["연결재무제표"]["재무상태표"].keys():
                            d7.update(result["연결재무제표"]["재무상태표"]["결손금"])
                else:
                    logger.info("재무제표 start")
                    if "포괄손익계산서" in result["재무제표"].keys():
                        logger.info("재무제표 포괄손익계산서 start")
                        tmp_result1 = {key: result["재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                       result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d1keys}}
                        tmp_result2 = {key: result["재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                       result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d2keys}}
                        tmp_result3 = {key: result["재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                       result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d1keys}}
                        tmp_result4 = {key: result["재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                       result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d2keys}}
                        tmp_result8 = {key: result["재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                       result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d8keys}}
                        tmp_result9 = {key: result["재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                       result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d8keys}}
                        if tmp_result1:
                            for key in tmp_result1.keys():
                                if d1 is None:
                                    d1 = tmp_result1[key]
                                else:
                                    d1.update(tmp_result1[key])
                        if tmp_result2:
                            for key in tmp_result2.keys():
                                if d2 is None:
                                    d2 = tmp_result2[key]
                                else:
                                    d2.update(tmp_result2[key])
                        if tmp_result3:
                            for key in tmp_result3.keys():
                                if d3 is None:
                                    d3 = tmp_result3[key]
                                else:
                                    d3.update(tmp_result3[key])
                        if tmp_result4:
                            for key in tmp_result4.keys():
                                if d4 is None:
                                    d4 = tmp_result4[key]
                                else:
                                    d4.update(tmp_result4[key])
                        if tmp_result8:
                            for key in tmp_result8.keys():
                                if d8 is None:
                                    d8 = tmp_result8[key]
                                else:
                                    d8.update(tmp_result8[key])
                        if tmp_result9:
                            for key in tmp_result9.keys():
                                if d9 is None:
                                    d9 = tmp_result9[key]
                                else:
                                    d9.update(tmp_result9[key])
                    if "손익계산서" in result["재무제표"].keys():
                        logger.info("재무제표 손익계산서 매출 start")
                        tmp_result1 = {key: result["재무제표"]["손익계산서"][key]["누계"] for key in
                                       result["재무제표"]["손익계산서"].keys() & {keys for keys in d1keys}}
                        tmp_result2 = {key: result["재무제표"]["손익계산서"][key]["누계"] for key in
                                       result["재무제표"]["손익계산서"].keys() & {keys for keys in d2keys}}
                        tmp_result3 = {key: result["재무제표"]["손익계산서"][key]["당기"] for key in
                                       result["재무제표"]["손익계산서"].keys() & {keys for keys in d1keys}}
                        tmp_result4 = {key: result["재무제표"]["손익계산서"][key]["당기"] for key in
                                       result["재무제표"]["손익계산서"].keys() & {keys for keys in d2keys}}
                        tmp_result8 = {key: result["재무제표"]["손익계산서"][key]["누계"] for key in
                                       result["재무제표"]["손익계산서"].keys() & {keys for keys in d8keys}}
                        tmp_result9 = {key: result["재무제표"]["손익계산서"][key]["당기"] for key in
                                       result["재무제표"]["손익계산서"].keys() & {keys for keys in d8keys}}
                        if tmp_result1:
                            for key in tmp_result1.keys():
                                if d1 is None:
                                    d1 = tmp_result1[key]
                                else:
                                    d1.update(tmp_result1[key])
                        if tmp_result2:
                            for key in tmp_result2.keys():
                                if d2 is None:
                                    d2 = tmp_result2[key]
                                else:
                                    d2.update(tmp_result2[key])
                        if tmp_result3:
                            for key in tmp_result3.keys():
                                if d3 is None:
                                    d3 = tmp_result3[key]
                                else:
                                    d3.update(tmp_result3[key])
                        if tmp_result4:
                            for key in tmp_result4.keys():
                                if d4 is None:
                                    d4 = tmp_result4[key]
                                else:
                                    d4.update(tmp_result4[key])
                        if tmp_result8:
                            for key in tmp_result8.keys():
                                if d8 is None:
                                    d8 = tmp_result8[key]
                                else:
                                    d8.update(tmp_result8[key])
                        if tmp_result9:
                            for key in tmp_result9.keys():
                                if d9 is None:
                                    d9 = tmp_result9[key]
                                else:
                                    d9.update(tmp_result9[key])
                    if "현금흐름표" in result["재무제표"].keys():
                        logger.info("재무제표 현금흐름표 start")
                        tmp_result10 = {key: result["재무제표"]["현금흐름표"][key] for key in
                                        result["재무제표"]["현금흐름표"].keys() & {keys for keys in d10keys}}
                        tmp_result11 = {key: result["재무제표"]["현금흐름표"][key] for key in
                                        result["재무제표"]["현금흐름표"].keys() & {keys for keys in d11keys}}
                        tmp_result12 = {key: result["재무제표"]["현금흐름표"][key] for key in
                                        result["재무제표"]["현금흐름표"].keys() & {keys for keys in d12keys}}
                        tmp_result13 = {key: result["재무제표"]["현금흐름표"][key] for key in
                                        result["재무제표"]["현금흐름표"].keys() & {keys for keys in d13keys}}
                        tmp_result14 = {key: result["재무제표"]["현금흐름표"][key] for key in
                                        result["재무제표"]["현금흐름표"].keys() & {keys for keys in d14keys}}
                        if tmp_result10:
                            for key in tmp_result10.keys():
                                if d10 is None:
                                    d10 = tmp_result10[key]
                                else:
                                    d10.update(tmp_result10[key])
                        if tmp_result11:
                            for key in tmp_result11.keys():
                                if d11 is None:
                                    d11 = tmp_result11[key]
                                else:
                                    d11.update(tmp_result11[key])
                        if tmp_result12:
                            for key in tmp_result12.keys():
                                if d12 is None:
                                    d12 = tmp_result12[key]
                                else:
                                    d12.update(tmp_result12[key])
                        if tmp_result13:
                            d13 = dictionary_add(tmp_result13)
                            # for key in tmp_result13.keys():
                            #     if d13 is None:
                            #         d13 = tmp_result13[key]
                            #     else:
                            #         d13.update(tmp_result13[key])
                        if tmp_result14:
                            d14 = dictionary_add(tmp_result14)
                            # for key in tmp_result14.keys():
                            #     if d14 is None:
                            #         d14 = tmp_result14[key]
                            #     else:
                            #         d14.update(tmp_result14[key])
                    if d11 is None: d11 = d13
                    if d12 is None: d12 = d14
                    d5 = result["재무제표"]["재무상태표"]["자산총계"] if "자산총계" in result["재무제표"]["재무상태표"].keys() else None
                    d6 = result["재무제표"]["재무상태표"]["부채총계"] if "부채총계" in result["재무제표"]["재무상태표"].keys() else None
                    d7 = result["재무제표"]["재무상태표"]["이익잉여금"] if "이익잉여금" in result["재무제표"]["재무상태표"].keys() else None
                    if d5 is None:
                        if "자  산  총  계" in result["재무제표"]["재무상태표"].keys():
                            d5 = result["재무제표"]["재무상태표"]["자  산  총  계"]
                    else:
                        if "자  산  총  계" in result["재무제표"]["재무상태표"].keys():
                            d5.update(result["재무제표"]["재무상태표"]["자  산  총  계"])
                    if d5 is None:
                        if "자산 총계" in result["재무제표"]["재무상태표"].keys():
                            d5 = result["재무제표"]["재무상태표"]["자산 총계"]
                    else:
                        if "자산 총계" in result["재무제표"]["재무상태표"].keys():
                            d5.update(result["재무제표"]["재무상태표"]["자산 총계"])
                    if d6 is None:
                        if "부  채  총  계" in result["재무제표"]["재무상태표"].keys():
                            d6 = result["재무제표"]["재무상태표"]["부  채  총  계"]
                    else:
                        if "부  채  총  계" in result["재무제표"]["재무상태표"].keys():
                            d6.update(result["재무제표"]["재무상태표"]["부  채  총  계"])
                    if d6 is None:
                        if "부채 총계" in result["재무제표"]["재무상태표"].keys():
                            d6 = result["재무제표"]["재무상태표"]["부채 총계"]
                    else:
                        if "부채 총계" in result["재무제표"]["재무상태표"].keys():
                            d6.update(result["재무제표"]["재무상태표"]["부채 총계"])
                    if d7 is None:
                        if "이익잉여금(결손금)" in result["재무제표"]["재무상태표"].keys():
                            d7 = result["재무제표"]["재무상태표"]["이익잉여금(결손금)"]
                    else:
                        if "이익잉여금(결손금)" in result["재무제표"]["재무상태표"].keys():
                            d7.update(result["재무제표"]["재무상태표"]["이익잉여금(결손금)"])
                    if d7 is None:
                        if "결손금" in result["재무제표"]["재무상태표"].keys():
                            d7 = result["재무제표"]["재무상태표"]["결손금"]
                    else:
                        if "결손금" in result["재무제표"]["재무상태표"].keys():
                            d7.update(result["재무제표"]["재무상태표"]["결손금"])
                logger.info("매출액 누계 : {}".format(d1))  # 매출액 누계
                logger.info("영업이익 누계 : {}".format(d2))  # 영업이익 누계
                logger.info("매출액 당기 : {}".format(d3))  # 매출액 당기
                logger.info("영업이익 당기 : {}".format(d4))  # 영업이익 당기
                logger.info("자산총계 : {}".format(d5))  # 자산총계
                logger.info("부채총계 : {}".format(d6))  # 부채총계
                logger.info("이익잉여금 : {}".format(d7))  # 이익잉여금
                logger.info("당기순이익 누계 : {}".format(d8))  # 당기순이익 누계
                logger.info("당기순이익 : {}".format(d9))  # 당기순이익
                logger.info("영업활동현금흐름 : {}".format(d10))  # 영업활동현금흐름
                logger.info("유형자산의 취득 : {}".format(d11))  # 유형자산의 취득
                logger.info("무형자산의 취득 : {}".format(d12))  # 무형자산의 취득
                logger.info("유형자산의 취득(유형자산의 취득으로 표시되지 않는) : {}".format(d13))  # 유형자산의 취득(유형자산의 취득으로 표시되지 않는)
                logger.info("무형자산의 취득(무형자산의 취득으로 표시되지 않는) : {}".format(d14))  # 무형자산의 취득(무형자산의 취득으로 표시되지 않는)
                if d10 is None:
                    none_list.append("[{}][{}]-영업활동현금흐름".format(stock.code, stock.name))
                if d11 is None:
                    none_list.append("[{}][{}]-유형자산의 취득".format(stock.code, stock.name))
                if d12 is None:
                    none_list.append("[{}][{}]-무형자산의 취득".format(stock.code, stock.name))
                for key1 in d1.keys():
                    current_key = key1
                    if "Rate" in key1: continue
                    if "4/4" in key1:
                        data[stock.code]["PL"]["Y"]["매출액영업이익률"] = dict(sorted({
                                                                                  k: round(float(
                                                                                      d2[key1][k].replace(",",
                                                                                                          "")) / float(
                                                                                      d1[key1][k].replace(",",
                                                                                                          "")) * 100,
                                                                                           2) if float(
                                                                                      d1[key1][k].replace(",",
                                                                                                          "")) != 0.0 else 0
                                                                                  for k in d1[key1]}.items()))

                        data[stock.code]["PL"]["Y"]["매출액"] = dict(
                            sorted({k: float(d1[key1][k].replace(",", "")) for k in
                                    d1[key1]}.items()))
                        # data[stock.code]["PL"]["Y"]["매출액"]["최근"] = provision_info[stock]["PL"]["Y"]["매출액"]
                        data[stock.code]["PL"]["Y"]["영업이익"] = dict(
                            sorted({k: float(d2[key1][k].replace(",", "")) for k in
                                    d2[key1]}.items()))
                        data[stock.code]["PL"]["Y"]["당기순이익"] = dict(
                            sorted({k: float(d8[key1][k].replace(",", "")) for k in
                                    d8[key1]}.items()))
                        # data[stock.code]["PL"]["Y"]["영업이익"]["최근"] = provision_info[stock]["PL"]["Y"]["영업이익"]
                        for k in sorted(d1[key1]):
                            dicTemp1[k] = float(d1[key1][k].replace(",", ""))
                        for k in sorted(d2[key1]):
                            dicTemp2[k] = float(d2[key1][k].replace(",", ""))
                        for k in sorted(d8[key1]):
                            dicTemp8[k] = float(d8[key1][k].replace(",", ""))
                    else:
                        for k in sorted(d1[key1]):
                            dicTemp0[k] = round(
                                float(d2[key1][k].replace(",", "")) / float(d1[key1][k].replace(",", "")) * 100,
                                2) if float(d1[key1][k].replace(",", "")) != 0.0 else 0
                        for k in sorted(d1[key1]):
                            dicTemp1[k] = float(d1[key1][k].replace(",", ""))
                            # data[stock.code]["PL"]["Q"]["누계매출액"][k] = float(d1[key1][k].replace(",", ""))
                        for k in sorted(d2[key1]):
                            dicTemp2[k] = float(d2[key1][k].replace(",", ""))
                            # data[stock.code]["PL"]["Q"]["누계영업이익"][k] = float(d2[key1][k].replace(",", ""))
                        for k in sorted(d3[key1]):
                            dicTemp3[k] = float(d3[key1][k].replace(",", ""))
                            # data[stock.code]["PL"]["Q"]["당기매출액"][k] = float(d3[key1][k].replace(",", ""))
                        for k in sorted(d4[key1]):
                            dicTemp4[k] = float(d4[key1][k].replace(",", ""))
                            # data[stock.code]["PL"]["Q"]["당기영업이익"][k] = float(d4[key1][k].replace(",", ""))
                        for k in sorted(d8[key1]):
                            dicTemp8[k] = float(d8[key1][k].replace(",", ""))
                            # data[stock.code]["PL"]["Q"]["당기매출액"][k] = float(d3[key1][k].replace(",", ""))
                        for k in sorted(d9[key1]):
                            dicTemp9[k] = float(d9[key1][k].replace(",", ""))
                            # data[stock.code]["PL"]["Q"]["당기영업이익"][k] = float(d4[key1][k].replace(",", ""))
                for key2 in d10.keys():
                    current_key = key2
                    if "Rate" in key2: continue
                    # if key2 not in data[stock.code]["CF"]["FCF"].keys():
                    #     data[stock.code]["CF"]["FCF"][key2] = {}
                    for key3 in d10[key2].keys():
                        yhasset = int(d11[key2][key3]) if d11 is not None and key2 in d11.keys() and key3 in d11[
                            key2].keys() else 0
                        mhasset = int(d12[key2][key3]) if d12 is not None and key2 in d12.keys() and key3 in d12[
                            key2].keys() else 0
                        data[stock.code]["CF"]["FCF"][key3] = int(d10[key2][key3]) - (yhasset + mhasset)
                data[stock.code]["PL"]["Q"]["매출액영업이익률"] = dict(sorted(dicTemp0.items()))
                data[stock.code]["PL"]["Q"]["누계매출액추이"] = dict(sorted(dicTemp1.items()))
                data[stock.code]["PL"]["Q"]["누계영업이익추이"] = dict(sorted(dicTemp2.items()))
                data[stock.code]["PL"]["Q"]["당기매출액"] = dict(sorted(dicTemp3.items()))
                data[stock.code]["PL"]["Q"]["당기영업이익"] = dict(sorted(dicTemp4.items()))
                data[stock.code]["PL"]["Q"]["누계당기순이익추이"] = dict(sorted(dicTemp8.items()))
                data[stock.code]["PL"]["Q"]["당기순이익"] = dict(sorted(dicTemp9.items()))
                # print("MakeAvg1?")
                # print(data)
                data[stock.code]["AverageRate"]["Y"]["매출액영업이익률"] = round(sum(
                    data[stock.code]["PL"]["Y"]["매출액영업이익률"].values()) / float(
                    len(data[stock.code]["PL"]["Y"]["매출액영업이익률"])), 2) if "매출액영업이익률" in data[stock.code]["PL"][
                    "Y"].keys() else None
                # print("MakeAvg2?")
                data[stock.code]["AverageRate"]["Y"]["매출액"] = round(sum(
                    data[stock.code]["PL"]["Y"]["매출액"].values()) / float(
                    len(data[stock.code]["PL"]["Y"]["매출액"])), 0) if "매출액" in data[stock.code]["PL"]["Y"].keys() and \
                                                                    len(data[stock.code]["PL"]["Y"][
                                                                            "매출액"]) != 0 else None
                # print("MakeAvg3?")
                data[stock.code]["AverageRate"]["Y"]["영업이익"] = round(sum(
                    data[stock.code]["PL"]["Y"]["영업이익"].values()) / float(
                    len(data[stock.code]["PL"]["Y"]["영업이익"])), 0) if "영업이익" in data[stock.code]["PL"]["Y"].keys() and \
                                                                     len(data[stock.code]["PL"]["Y"][
                                                                             "영업이익"]) != 0 else None
                data[stock.code]["AverageRate"]["Y"]["당기순이익"] = round(sum(
                    data[stock.code]["PL"]["Y"]["당기순이익"].values()) / float(
                    len(data[stock.code]["PL"]["Y"]["당기순이익"])), 0) if "당기순이익" in data[stock.code]["PL"]["Y"].keys() and \
                                                                      len(data[stock.code]["PL"]["Y"][
                                                                              "당기순이익"]) != 0 else None
                # print("MakeAvg4?")
                data[stock.code]["AverageRate"]["Q"]["매출액영업이익률"] = round(sum(
                    data[stock.code]["PL"]["Q"]["매출액영업이익률"].values()) / float(
                    len(data[stock.code]["PL"]["Q"]["매출액영업이익률"])), 2) if "매출액영업이익률" in data[stock.code]["PL"][
                    "Q"].keys() and \
                                                                         len(data[stock.code]["PL"]["Q"][
                                                                                 "매출액영업이익률"]) != 0 else None
                # print("MakeAvg5?")
                data[stock.code]["AverageRate"]["Q"]["매출액"] = round(sum(
                    data[stock.code]["PL"]["Q"]["당기매출액"].values()) / float(
                    len(data[stock.code]["PL"]["Q"]["당기매출액"])), 0) if "당기매출액" in data[stock.code]["PL"]["Q"].keys() and \
                                                                      len(data[stock.code]["PL"]["Q"][
                                                                              "당기매출액"]) != 0 else None
                # print("MakeAvg6?")
                data[stock.code]["AverageRate"]["Q"]["영업이익"] = round(sum(
                    data[stock.code]["PL"]["Q"]["당기영업이익"].values()) / float(
                    len(data[stock.code]["PL"]["Q"]["당기영업이익"])), 0) if "당기영업이익" in data[stock.code]["PL"][
                    "Q"].keys() and \
                                                                       len(data[stock.code]["PL"]["Q"][
                                                                               "당기영업이익"]) != 0 else None
                data[stock.code]["AverageRate"]["Q"]["당기순이익"] = round(sum(
                    data[stock.code]["PL"]["Q"]["당기순이익"].values()) / float(
                    len(data[stock.code]["PL"]["Q"]["당기순이익"])), 0) if "당기순이익" in data[stock.code]["PL"]["Q"].keys() and \
                                                                      len(data[stock.code]["PL"]["Q"][
                                                                              "당기순이익"]) != 0 else None
                # print("MakeAvg7?")
                # 손익계산서 분석 끝
                for key1 in d1.keys():
                    if "Rate" in key1: continue
                    if d5 is not None and key1 in d5.keys():
                        for k in sorted(d5[key1]):
                            dicTemp5[k] = float(d5[key1][k].replace(",", "")) if d5 is not None else 0
                    if d6 is not None and key1 in d6.keys():
                        for k in sorted(d6[key1]):
                            dicTemp6[k] = float(d6[key1][k].replace(",", "")) if d6 is not None else 0
                    if d7 is not None and key1 in d7.keys():
                        for k in sorted(d7[key1]):
                            dicTemp7[k] = float(d7[key1][k].replace(",", "")) if d7 is not None else 0
                    if d10 is not None and key1 in d10.keys():
                        for k in sorted(d10[key1]):
                            dicTemp10[k] = float(str(d10[key1][k]).replace(",", "")) if d10 is not None else 0
                    if d11 is not None and key1 in d11.keys():
                        for k in sorted(d11[key1]):
                            dicTemp11[k] = float(str(d11[key1][k]).replace(",", "")) if d11 is not None else 0
                    if d12 is not None and key1 in d12.keys():
                        for k in sorted(d12[key1]):
                            dicTemp12[k] = float(str(d12[key1][k]).replace(",", "")) if d12 is not None else 0
                data[stock.code]["FS"]["TotalAsset"] = dict(sorted(dicTemp5.items()))
                data[stock.code]["FS"]["TotalDebt"] = dict(sorted(dicTemp6.items()))
                data[stock.code]["FS"]["RetainedEarnings"] = dict(sorted(dicTemp7.items()))
                data[stock.code]["CF"]["영업활동현금흐름"] = dict(sorted(dicTemp10.items()))
                data[stock.code]["CF"]["유형자산취득"] = dict(sorted(dicTemp11.items()))
                data[stock.code]["CF"]["무형자산취득"] = dict(sorted(dicTemp12.items()))
                data[stock.code]["CF"]["FCF"] = dict(sorted(data[stock.code]["CF"]["FCF"].items()))
        except Exception as e:
            logger.error(e)
            # logger.error(current_pos)
            logger.error(current_key)
            for key in current_pos.keys():  # key = ["연결재무제표", "재무제표"]
                for report in current_pos[key].keys():  # report = ["재무상태표", "손익계산서"]
                    if report not in ["손익계산서", "포괄손익계산서"]:  # ["재무상태표", "현금흐름표", "자본변동표"]:
                        for acc in current_pos[key][report].keys():
                            # acc = ["유동자산", "비유동자산", "자산총계", "유동부채", "비유동부채", "부채총계", "자본금", "이익잉여금", "자본총계"]
                            for category in sorted(current_pos[key][report][acc].keys()):
                                # category = ["YYYY 1/4", "YYYY 2/4", "YYYY 3/4", "YYYY 4/4"]
                                logger.error("{}\t{}\t{}\t{}\t{}".format(key, report, acc, category,
                                                                         current_pos[key][report][acc][category]))
                                # for k in result[key][report][acc][category].keys():
                                #     print(key, report, acc, category, k, current_pos[key][report][acc][category][k])
                    else:
                        for acc in current_pos[key][report].keys():
                            # acc = ["매출액", 영업이익", "법인세차감전", "당기순이익"]
                            for category in current_pos[key][report][acc].keys():
                                # category = ["누계", "당기"]
                                for k in sorted(current_pos[key][report][acc][category].keys()):
                                    # k = ["YYYY 1/4", "YYYY 2/4", "YYYY 3/4", "YYYY 4/4"]
                                    logger.error("{}\t{}\t{}\t{}\t{}\t{}".format(key, report, acc, category, k,
                                                                                 current_pos[key][report][acc][
                                                                                     category][k]))
        logger.info(data)

    for k in data.keys():
        avg_sales_op_profit_rate = None
        avg_sales = None
        avg_op_profit = None
        avg_net_income = None
        last_sales_op_profit_rate = None
        last_sales = None
        last_op_profit = None
        last_net_income = None
        before_sales = None
        before_op_profit = None
        before_net_income = None
        fcf_last_5 = None
        ocf_last_5 = None
        earn_last_5 = None
        pl_last_5 = None
        last_5_keys = list(data[k]["CF"]["영업활동현금흐름"].keys())[-6:]
        for lastkey in last_5_keys:
            if lastkey not in data[k]["CF"]["FCF"].keys() or lastkey not in data[k]["CF"]["영업활동현금흐름"].keys() \
                    or lastkey not in data[k]["FS"]["RetainedEarnings"].keys() or lastkey not in data[k]["PL"]["Q"][
                "누계당기순이익추이"].keys():
                last_5_keys.remove(lastkey)
        try:
            fcf_last_5 = {lk: data[k]["CF"]["FCF"][lk] for lk in last_5_keys}
            ocf_last_5 = {lk: data[k]["CF"]["영업활동현금흐름"][lk] for lk in last_5_keys}
            earn_last_5 = {lk: data[k]["FS"]["RetainedEarnings"][lk] for lk in last_5_keys}
            pl_last_5 = {lk: data[k]["PL"]["Q"]["누계당기순이익추이"][lk] for lk in last_5_keys}
        except Exception as e:
            print(last_5_keys)
            print(k)
            print(fcf_last_5)
            print(ocf_last_5)
            print(earn_last_5)
            print(pl_last_5)
        print(k, data[k]["corp_name"], "*" * 100)
        for key in data[k]["PL"]["Y"].keys():
            print("연간", key, data[k]["PL"]["Y"][key])
        print("연간", data[k]["AverageRate"]["Y"])
        for key in data[k]["PL"]["Q"].keys():
            print("당기", key, data[k]["PL"]["Q"][key])
        print("당기", data[k]["AverageRate"]["Q"])
        print("재무상태표-자산총계", data[k]["FS"]["TotalAsset"])
        print("재무상태표-부채총계", data[k]["FS"]["TotalDebt"])
        print("재무상태표-이익잉여금", data[k]["FS"]["RetainedEarnings"])
        print("현금흐름표-영업활동현금흐름", data[k]["CF"]["영업활동현금흐름"])
        print("현금흐름표-유형자산취득", data[k]["CF"]["유형자산취득"])
        print("현금흐름표-무형자산취득", data[k]["CF"]["무형자산취득"])
        print("FreeCashFlow", data[k]["CF"]["FCF"])
        # print("here1?")
        if "매출액영업이익률" in data[k]["AverageRate"]["Y"].keys() \
                and "매출액" in data[k]["AverageRate"]["Y"].keys() \
                and "영업이익" in data[k]["AverageRate"]["Y"].keys() \
                and "당기순이익" in data[k]["AverageRate"]["Y"].keys():
            # print("here2?")
            avg_sales_op_profit_rate = data[k]["AverageRate"]["Y"]["매출액영업이익률"]
            avg_sales = data[k]["AverageRate"]["Y"]["매출액"]
            avg_op_profit = data[k]["AverageRate"]["Y"]["영업이익"]
            avg_net_income = data[k]["AverageRate"]["Y"]["당기순이익"]

            if "매출액영업이익률" in data[k]["PL"]["Q"].keys():
                # print("here3?")
                last_sales_op_profit_rate = data[k]["PL"]["Q"]["매출액영업이익률"].popitem()[1] if len(
                    data[k]["PL"]["Q"]["매출액영업이익률"]) > 0 else None
                last_sales = data[k]["PL"]["Q"]["누계매출액추이"].popitem()[1] if len(
                    data[k]["PL"]["Q"]["누계매출액추이"]) > 0 else None
                if "매출액" in data[k]["PL"]["Y"].keys():
                    data[k]["PL"]["Y"]["매출액"].popitem() if len(data[k]["PL"]["Y"]["매출액"]) > 0 else None
                    before_sales = data[k]["PL"]["Y"]["매출액"].popitem()[1] if len(
                        data[k]["PL"]["Y"]["매출액"]) > 0 else None
                last_op_profit = data[k]["PL"]["Q"]["누계영업이익추이"].popitem()[1] if len(
                    data[k]["PL"]["Q"]["누계영업이익추이"]) > 0 else None
                if "영업이익" in data[k]["PL"]["Y"].keys():
                    data[k]["PL"]["Y"]["영업이익"].popitem() if len(data[k]["PL"]["Y"]["영업이익"]) > 0 else None
                    before_op_profit = data[k]["PL"]["Y"]["영업이익"].popitem()[1] if len(
                        data[k]["PL"]["Y"]["영업이익"]) > 0 else None
                last_net_income = data[k]["PL"]["Q"]["누계당기순이익추이"].popitem()[1] if len(
                    data[k]["PL"]["Q"]["누계당기순이익추이"]) > 0 else None
                if "당기순이익" in data[k]["PL"]["Y"].keys():
                    data[k]["PL"]["Y"]["당기순이익"].popitem() if len(data[k]["PL"]["Y"]["당기순이익"]) > 0 else None
                    before_net_income = data[k]["PL"]["Y"]["당기순이익"].popitem()[1] if len(
                        data[k]["PL"]["Y"]["당기순이익"]) > 0 else None
        # print("here4?")
        if avg_sales_op_profit_rate and last_sales_op_profit_rate:
            if last_sales_op_profit_rate > 0 and avg_sales_op_profit_rate > 0 and last_sales_op_profit_rate > avg_sales_op_profit_rate:
                # print("here5?")
                if avg_sales and last_sales and before_sales and \
                        avg_net_income and last_net_income and before_net_income and \
                        last_sales > avg_sales and last_sales > before_sales and \
                        last_net_income > avg_net_income and last_net_income > before_net_income:
                    if last_sales_op_profit_rate > 20:
                        best[k] = {"stock_code": k, "corp_name": data[k]["corp_name"],
                                   "last_report": data[k]["last_report"], "업종": data[k]["category"],
                                   "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                   "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                   "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                   "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                   "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                   "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                   "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                                   "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                   "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                   "직전당기순이익": format(before_net_income, ",") if before_net_income is not None else None,
                                   "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None,
                                   "FCF": fcf_last_5 if fcf_last_5 is not None else None,
                                   "OCF": ocf_last_5 if ocf_last_5 is not None else None,
                                   "EARN": earn_last_5 if earn_last_5 is not None else None,
                                   "PL": pl_last_5 if pl_last_5 is not None else None
                                   }
                        call = json.loads(requests.get(
                            "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                                k)).content.decode("utf-8"))
                        best[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                        best[k]["PER"] = call["per"]
                        best[k]["EPS"] = call["eps"]
                        best[k]["PBR"] = call["pbr"]
                        best[k]["현재가"] = f'{call["now"]:,}'
                        best[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                data[k][
                                                                                                    "list_shares"] else 0
                        best[k]["PER2"] = round(call["now"] / best[k]["EPS2"], 0) if best[k]["EPS2"] != 0 else 0
                        best[k]["예상주가"] = format(int(round(best[k]["EPS2"] * best[k]["PER"], 0)), ",") if best[k][
                                                                                                              "EPS2"] and \
                                                                                                          best[k][
                                                                                                              "PER"] else 0
                    elif np.sign(last_sales_op_profit_rate) > np.sign(avg_sales_op_profit_rate):
                        best[k] = {"stock_code": k, "corp_name": data[k]["corp_name"],
                                   "last_report": data[k]["last_report"], "업종": data[k]["category"],
                                   "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                   "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                   "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                   "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                   "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                   "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                   "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                                   "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                   "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                   "직전당기순이익": format(before_net_income, ",") if before_net_income is not None else None,
                                   "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None,
                                   "FCF": fcf_last_5 if fcf_last_5 is not None else None,
                                   "OCF": ocf_last_5 if ocf_last_5 is not None else None,
                                   "EARN": earn_last_5 if earn_last_5 is not None else None,
                                   "PL": pl_last_5 if pl_last_5 is not None else None}
                        call = json.loads(requests.get(
                            "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                                k)).content.decode("utf-8"))
                        best[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                        best[k]["PER"] = call["per"]
                        best[k]["EPS"] = call["eps"]
                        best[k]["PBR"] = call["pbr"]
                        best[k]["현재가"] = f'{call["now"]:,}'
                        best[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                data[k][
                                                                                                    "list_shares"] else 0
                        best[k]["PER2"] = round(call["now"] / best[k]["EPS2"], 0) if best[k]["EPS2"] != 0 else 0
                        best[k]["예상주가"] = format(int(round(best[k]["EPS2"] * best[k]["PER"], 0)), ",") if best[k][
                                                                                                              "EPS2"] and \
                                                                                                          best[k][
                                                                                                              "PER"] else 0
                    else:
                        better[k] = {"stock_code": k, "corp_name": data[k]["corp_name"],
                                     "last_report": data[k]["last_report"], "업종": data[k]["category"],
                                     "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                     "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                     "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                     "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                     "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                     "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                     "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                                     "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                     "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                     "직전당기순이익": format(before_net_income,
                                                       ",") if before_net_income is not None else None,
                                     "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None,
                                     "FCF": fcf_last_5 if fcf_last_5 is not None else None,
                                     "OCF": ocf_last_5 if ocf_last_5 is not None else None,
                                     "EARN": earn_last_5 if earn_last_5 is not None else None,
                                     "PL": pl_last_5 if pl_last_5 is not None else None
                                     }
                        call = json.loads(requests.get(
                            "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                                k)).content.decode("utf-8"))
                        better[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                        better[k]["PER"] = call["per"]
                        better[k]["EPS"] = call["eps"]
                        better[k]["PBR"] = call["pbr"]
                        better[k]["현재가"] = f'{call["now"]:,}'
                        better[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                  data[k][
                                                                                                      "list_shares"] else 0
                        better[k]["PER2"] = round(call["now"] / better[k]["EPS2"], 0) if better[k]["EPS2"] != 0 else 0
                        better[k]["예상주가"] = format(int(round(better[k]["EPS2"] * better[k]["PER"], 0)), ",") if \
                        better[k]["EPS2"] and better[k]["PER"] else 0
                else:
                    if last_sales_op_profit_rate > 15:
                        better[k] = {"stock_code": k, "corp_name": data[k]["corp_name"],
                                     "last_report": data[k]["last_report"], "업종": data[k]["category"],
                                     "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                     "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                     "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                     "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                     "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                     "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                     "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                                     "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                     "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                     "직전당기순이익": format(before_net_income,
                                                       ",") if before_net_income is not None else None,
                                     "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None,
                                     "FCF": fcf_last_5 if fcf_last_5 is not None else None,
                                     "OCF": ocf_last_5 if ocf_last_5 is not None else None,
                                     "EARN": earn_last_5 if earn_last_5 is not None else None,
                                     "PL": pl_last_5 if pl_last_5 is not None else None
                                     }
                        call = json.loads(requests.get(
                            "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                                k)).content.decode("utf-8"))
                        better[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                        better[k]["PER"] = call["per"]
                        better[k]["EPS"] = call["eps"]
                        better[k]["PBR"] = call["pbr"]
                        better[k]["현재가"] = f'{call["now"]:,}'
                        better[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                  data[k][
                                                                                                      "list_shares"] else 0
                        better[k]["PER2"] = round(call["now"] / better[k]["EPS2"], 0) if better[k]["EPS2"] != 0 else 0
                        better[k]["예상주가"] = format(int(round(better[k]["EPS2"] * better[k]["PER"], 0)), ",") if \
                        better[k]["EPS2"] and better[k]["PER"] else 0
                    else:
                        # print("here7?")
                        good[k] = {"stock_code": k, "corp_name": data[k]["corp_name"],
                                   "last_report": data[k]["last_report"], "업종": data[k]["category"],
                                   "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                   "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                   "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                   "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                   "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                   "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                   "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                                   "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                   "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                   "직전당기순이익": format(before_net_income, ",") if before_net_income is not None else None,
                                   "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None,
                                   "FCF": fcf_last_5 if fcf_last_5 is not None else None,
                                   "OCF": ocf_last_5 if ocf_last_5 is not None else None,
                                   "EARN": earn_last_5 if earn_last_5 is not None else None,
                                   "PL": pl_last_5 if pl_last_5 is not None else None
                                   }
                        call = json.loads(requests.get(
                            "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                                k)).content.decode("utf-8"))
                        good[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                        good[k]["PER"] = call["per"]
                        good[k]["EPS"] = call["eps"]
                        good[k]["PBR"] = call["pbr"]
                        good[k]["현재가"] = f'{call["now"]:,}'
                        good[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                data[k][
                                                                                                    "list_shares"] else 0
                        good[k]["PER2"] = round(call["now"] / good[k]["EPS2"], 0) if good[k]["EPS2"] != 0 else 0
                        good[k]["예상주가"] = format(int(round(good[k]["EPS2"] * good[k]["PER"], 0)), ",") if good[k][
                                                                                                              "EPS2"] and \
                                                                                                          good[k][
                                                                                                              "PER"] else 0
            else:
                if last_sales_op_profit_rate > 15:
                    better[k] = {"stock_code": k, "corp_name": data[k]["corp_name"],
                                 "last_report": data[k]["last_report"], "업종": data[k]["category"],
                                 "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                 "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                 "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                 "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                 "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                 "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                 "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                                 "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                 "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                 "직전당기순이익": format(before_net_income, ",") if before_net_income is not None else None,
                                 "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None,
                                 "FCF": fcf_last_5 if fcf_last_5 is not None else None,
                                 "OCF": ocf_last_5 if ocf_last_5 is not None else None,
                                 "EARN": earn_last_5 if earn_last_5 is not None else None,
                                 "PL": pl_last_5 if pl_last_5 is not None else None
                                 }
                    call = json.loads(requests.get(
                        "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                            k)).content.decode("utf-8"))
                    better[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                    better[k]["PER"] = call["per"]
                    better[k]["EPS"] = call["eps"]
                    better[k]["PBR"] = call["pbr"]
                    better[k]["현재가"] = f'{call["now"]:,}'
                    better[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                              data[k][
                                                                                                  "list_shares"] else 0
                    better[k]["PER2"] = round(call["now"] / better[k]["EPS2"], 0) if better[k]["EPS2"] != 0 else 0
                    better[k]["예상주가"] = format(int(round(better[k]["EPS2"] * better[k]["PER"], 0)), ",") if better[k][
                                                                                                                "EPS2"] and \
                                                                                                            better[k][
                                                                                                                "PER"] else 0
                else:
                    soso[k] = {"stock_code": k, "corp_name": data[k]["corp_name"],
                               "last_report": data[k]["last_report"], "업종": data[k]["category"],
                               "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                               "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                               "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                               "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                               "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                               "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                               "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                               "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                               "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                               "직전당기순이익": format(before_net_income, ",") if before_net_income is not None else None,
                               "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None,
                               "FCF": fcf_last_5 if fcf_last_5 is not None else None,
                               "OCF": ocf_last_5 if ocf_last_5 is not None else None,
                               "EARN": earn_last_5 if earn_last_5 is not None else None,
                               "PL": pl_last_5 if pl_last_5 is not None else None
                               }
                    call = json.loads(requests.get(
                        "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                            k)).content.decode("utf-8"))
                    soso[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                    soso[k]["PER"] = call["per"]
                    soso[k]["EPS"] = call["eps"]
                    soso[k]["PBR"] = call["pbr"]
                    soso[k]["현재가"] = f'{call["now"]:,}'
                    soso[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                            data[k][
                                                                                                "list_shares"] else 0
                    soso[k]["PER2"] = round(call["now"] / soso[k]["EPS2"], 0) if soso[k]["EPS2"] != 0 else 0
                    soso[k]["예상주가"] = format(int(round(soso[k]["EPS2"] * soso[k]["PER"], 0)), ",") if soso[k][
                                                                                                          "EPS2"] and \
                                                                                                      soso[k][
                                                                                                          "PER"] else 0
        else:
            soso[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "last_report": data[k]["last_report"],
                       "업종": data[k]["category"],
                       "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                       "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                       "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                       "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                       "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                       "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                       "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                       "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                       "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                       "직전당기순이익": format(before_net_income, ",") if before_net_income is not None else None,
                       "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None,
                       "FCF": fcf_last_5 if fcf_last_5 is not None else None,
                       "OCF": ocf_last_5 if ocf_last_5 is not None else None,
                       "EARN": earn_last_5 if earn_last_5 is not None else None,
                       "PL": pl_last_5 if pl_last_5 is not None else None
                       }
            call = json.loads(requests.get(
                "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                    k)).content.decode("utf-8"))
            soso[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
            soso[k]["PER"] = call["per"]
            soso[k]["EPS"] = call["eps"]
            soso[k]["PBR"] = call["pbr"]
            soso[k]["현재가"] = f'{call["now"]:,}'
            soso[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                    data[k][
                                                                                        "list_shares"] else 0
            soso[k]["PER2"] = round(call["now"] / soso[k]["EPS2"], 0) if soso[k]["EPS2"] != 0 else 0
            soso[k]["예상주가"] = format(int(round(soso[k]["EPS2"] * soso[k]["PER"], 0)), ",") if soso[k]["EPS2"] and \
                                                                                              soso[k]["PER"] else 0
            # info_lack[k] = {"corp_name": data[k]["corp_name"], "corp_code": data[k]["corp_code"]}
    logger.info("{} {} {} {}".format("*" * 100, "BEST", len(best), "*" * 100))
    for key in best.keys():
        logger.info(best[key])
        # if best[key]["EPS2"] != 0 and best[key]["EPS2"] > best[key]["EPS"] and (best[key]["EPS2"] - best[key]["EPS"])/best[key]["EPS"] * 100 >= 30:
        if "BEST" not in treasure.keys():
            treasure["BEST"] = {}
        treasure["BEST"][key] = {"사명": best[key]["corp_name"], "시가총액": best[key]["시가총액"], "업종": best[key]["업종"],
                                 "최근매출액영업이익률": best[key]["최근매출액영업이익률"], "EPS": best[key]["EPS"],
                                 "추정EPS": best[key]["EPS2"],
                                 "괴리율": round((best[key]["EPS2"] - best[key]["EPS"]) / best[key]["EPS"] * 100,
                                              2) if best[key]["EPS2"] and best[key]["EPS"] else None, "현재가": best[key]["현재가"], "예상주가": best[key]["예상주가"],
                                 "EARN": best[key]["EARN"],
                                 "FCF": best[key]["FCF"], "OCF": best[key]["OCF"], "PL": best[key]["PL"],
                                 "최종보고서": best[key]["last_report"]}
    logger.info("{} {} {} {}".format("*" * 100, "BETTER", len(better), "*" * 100))
    for key in better.keys():
        logger.info(better[key])
        # if better[key]["EPS2"] != 0 and better[key]["EPS2"] > better[key]["EPS"] and (better[key]["EPS2"] - better[key]["EPS"])/better[key]["EPS"] * 100 >= 30:
        if "BETTER" not in treasure.keys():
            treasure["BETTER"] = {}
        treasure["BETTER"][key] = {"사명": better[key]["corp_name"], "시가총액": better[key]["시가총액"],
                                   "업종": better[key]["업종"], "최근매출액영업이익률": better[key]["최근매출액영업이익률"],
                                   "EPS": better[key]["EPS"], "추정EPS": better[key]["EPS2"], "괴리율": round(
                (better[key]["EPS2"] - better[key]["EPS"]) / better[key]["EPS"] * 100, 2) if better[key]["EPS2"] and better[key]["EPS"] else None,
                                   "현재가": better[key]["현재가"], "예상주가": better[key]["예상주가"], "EARN": better[key]["EARN"],
                                   "FCF": better[key]["FCF"], "OCF": better[key]["OCF"], "PL": better[key]["PL"],
                                   "최종보고서": better[key]["last_report"]}
    logger.info("{} {} {} {}".format("*" * 100, "GOOD", len(good), "*" * 100))
    for key in good.keys():
        logger.info(good[key])
        # if good[key]["EPS2"] != 0 and good[key]["EPS2"] > good[key]["EPS"] and (good[key]["EPS2"] - good[key]["EPS"]) / \
        #         good[key]["EPS"] * 100 >= 30:
        if "GOOD" not in treasure.keys():
            treasure["GOOD"] = {}
        treasure["GOOD"][key] = {"사명": good[key]["corp_name"], "시가총액": good[key]["시가총액"], "업종": good[key]["업종"],
                                 "최근매출액영업이익률": good[key]["최근매출액영업이익률"], "EPS": good[key]["EPS"],
                                 "추정EPS": good[key]["EPS2"],
                                 "괴리율": round((good[key]["EPS2"] - good[key]["EPS"]) / good[key]["EPS"] * 100, 2) if good[key]["EPS2"] and good[key]["EPS"] else None,
                                 "현재가": good[key]["현재가"], "예상주가": good[key]["예상주가"], "EARN": good[key]["EARN"],
                                 "FCF": good[key]["FCF"],
                                 "OCF": good[key]["OCF"], "PL": good[key]["PL"], "최종보고서": good[key]["last_report"]}
    logger.info("{} {} {} {}".format("*" * 100, "CHECK", len(soso), "*" * 100))
    for key in soso.keys():
        logger.info(soso[key])
        # if soso[key]["EPS2"] != 0 and soso[key]["EPS2"] > soso[key]["EPS"] and (soso[key]["EPS2"] - soso[key]["EPS"]) / \
        #         soso[key]["EPS"] * 100 >= 30:
        if "SOSO" not in treasure.keys():
            treasure["SOSO"] = {}
        treasure["SOSO"][key] = {"사명": soso[key]["corp_name"], "시가총액": soso[key]["시가총액"], "업종": soso[key]["업종"],
                                 "최근매출액영업이익률": soso[key]["최근매출액영업이익률"], "EPS": soso[key]["EPS"],
                                 "추정EPS": soso[key]["EPS2"],
                                 "괴리율": round((soso[key]["EPS2"] - soso[key]["EPS"]) / soso[key]["EPS"] * 100,
                                              2) if soso[key]["EPS2"] and soso[key]["EPS"] else None, "현재가": soso[key]["현재가"], "예상주가": soso[key]["예상주가"],
                                 "EARN": soso[key]["EARN"],
                                 "FCF": soso[key]["FCF"], "OCF": soso[key]["OCF"], "PL": soso[key]["PL"],
                                 "최종보고서": soso[key]["last_report"]}
    # logger.info(none_list)
    return treasure

def new_find_hidden_pearl_with_dartpipe_multiple(codes, bgn_dt=None, end_dt=None):
    import sys
    import os
    import django
    from OpenDartPipe import pipe
    # sys.path.append(r'E:\Github\Waver\MainBoard')
    # sys.path.append(r'E:\Github\Waver\MainBoard\MainBoard')
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    import json
    import numpy as np
    import requests
    import logging

    logfile = 'detector'
    if not os.path.exists('./logs'):
        os.makedirs('./logs')
    now = datetime.now().strftime("%Y%m%d%H%M%S")

    logger = logging.getLogger(__name__)
    formatter = logging.Formatter('[%(asctime)s][%(filename)s:%(lineno)s] >> %(message)s')

    streamHandler = logging.StreamHandler()
    fileHandler = logging.FileHandler("./logs/{}_{}.log".format(logfile, now))

    streamHandler.setFormatter(formatter)
    fileHandler.setFormatter(formatter)

    logger.addHandler(streamHandler)
    logger.addHandler(fileHandler)
    logger.setLevel(level=logging.INFO)

    # logging
    # logging.basicConfig(filename=logfile, filemode='w', level=logging.DEBUG)
    # logging.debug("Log started at %s", str(datetime.datetime.now()))

    current_pos = None
    treasure = {}
    trash = {}
    data = {}
    best = {}
    better = {}
    good = {}
    soso = {}
    lists = None
    none_list = []
    # 날짜 정보 셋팅
    dateDict = new_get_dateDict()
    # 종목 정보 셋팅
    # DEBUG = True
    DEBUG = False
    # USE_JSON = False
    USE_JSON = True
    # stockInfo = detective_db.Stocks.objects.filter(category_name__contains="일반 목적", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(category_name__contains="특수", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(category_name__contains="생물", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(category_name__contains="화학", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(category_name__contains="자연", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(category_name__contains="건축", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(category_name__contains="축전지", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(code="005930", listing='Y')
    stockInfo = detective_db.Stocks.objects.filter(code__in=codes, listing='Y')
    dart = pipe.Pipe()
    dart.create()
    for stock in stockInfo:
        current_key = None
        ret, code = dart.get_corp_code(stock.code)
        try:
            if ret:
                data[stock.code] = {"corp_code": code,
                                    "last_report": None,
                                    "corp_name": stock.name,
                                    "category": stock.category_name,
                                    "list_shares": stock.issued_shares,
                                    "PL": {"Y": {}, "Q": {}},
                                    "FS": {"TotalAsset": {}, "TotalDebt": {}, "RetainedEarnings": {}},
                                    "CF": {"영업활동현금흐름": {}, "유형자산취득": {}, "무형자산취득": {}, "FCF": {}},
                                    "AverageRate": {"Y": {}, "Q": {}}}
                # print(dateDict["yyyy2"], dateDict)
                if bgn_dt is None:
                    lists = dart.get_list(corp_code=code, bgn_de=dateDict["yyyy2"], pblntf_ty='A', req_type=True)["list"][:5]
                elif end_dt is None:
                    lists = dart.get_list(corp_code=code, bgn_de=bgn_dt, pblntf_ty='A', req_type=True)["list"][:5]
                else:
                    lists = dart.get_list(corp_code=code, bgn_de=bgn_dt, end_de=end_dt, pblntf_ty='A', req_type=True)["list"][:5]
                # lists = dart.get_list(corp_code=code, bgn_de=dateDict["yyyy2"], pblntf_ty='A', req_type=True)["list"][:4]
                for l in lists:
                    if data[stock.code]["last_report"] is None: data[stock.code]["last_report"] = l["report_nm"]
                    else:
                        if data[stock.code]["last_report"] < l["report_nm"]: data[stock.code]["last_report"] = l["report_nm"]
                    logger.info(l)
                req_list, req_list2 = dart.get_req_lists(lists)
                result = dart.get_fnlttSinglAcnt_from_req_list(code, req_list, "ALL")
                current_pos = result
                # for key in result.keys():  # key = ["연결재무제표", "재무제표"]
                #     for report in result[key].keys():  # report = ["재무상태표", "손익계산서"]
                #         if report == "재무상태표":
                #             for acc in result[key][report].keys():
                #                 # acc = ["유동자산", "비유동자산", "자산총계", "유동부채", "비유동부채", "부채총계", "자본금", "이익잉여금", "자본총계"]
                #                 for category in sorted(result[key][report][acc].keys()):
                #                     # category = ["YYYY 1/4", "YYYY 2/4", "YYYY 3/4", "YYYY 4/4"]
                #                     print(key, report, acc, category, result[key][report][acc][category])
                #                     # for k in result[key][report][acc][category].keys():
                #                     #     print(key, report, acc, category, k, result[key][report][acc][category][k])
                #         else:
                #             for acc in result[key][report].keys():
                #                 # acc = ["매출액", 영업이익", "법인세차감전", "당기순이익"]
                #                 for category in result[key][report][acc].keys():
                #                     # category = ["누계", "당기"]
                #                     for k in sorted(result[key][report][acc][category].keys()):
                #                         # k = ["YYYY 1/4", "YYYY 2/4", "YYYY 3/4", "YYYY 4/4"]
                #                         print(key, report, acc, category, k, result[key][report][acc][category][k])
                d1 = None
                d2 = None
                d3 = None
                d4 = None
                d5 = None
                d6 = None
                d7 = None
                d8 = None
                d9 = None
                d10 = None
                d11 = None
                d12 = None
                d13 = None
                d14 = None
                dicTemp0 = {}
                dicTemp1 = {}
                dicTemp2 = {}
                dicTemp3 = {}
                dicTemp4 = {}
                dicTemp5 = {}
                dicTemp6 = {}
                dicTemp7 = {}
                dicTemp8 = {}
                dicTemp9 = {}
                dicTemp10 = {}
                dicTemp11 = {}
                dicTemp12 = {}
                dicTemp13 = {}
                dicTemp14 = {}
                # if stock == "006360":
                #     print()
                d1keys = ["매출", "수익(매출액)", "I.  매출액", "영업수익", "매출액", "Ⅰ. 매출액", "매출 및 지분법 손익", "매출 및 지분법손익"]
                d2keys = ["영업이익(손실)", "영업이익 (손실)", "영업이익", "영업손익", "V. 영업손익", "Ⅴ. 영업이익", "Ⅴ. 영업이익(손실)", "V. 영업이익", "영업손실"]
                d8keys = ["당기순이익(손실)", "당기순이익 (손실)", "당기순이익", "분기순이익", "반기순이익", "당기순이익(손실)", "분기순이익(손실)", "반기순이익(손실)",
                          "연결당기순이익", "연결분기순이익", "연결반기순이익", "연결당기순이익(손실)", "연결분기순이익(손실)", "연결반기순이익(손실)", "당기순손익",
                          "분기순손익",
                          "반기순손익", "지배기업 소유주지분", "지배기업의 소유주에게 귀속되는 당기순이익(손실)", "당기순손실", "분기순손실", "반기순손실",
                          "Ⅷ. 당기순이익(손실)", "지배기업 소유주 지분",
                          "Ⅷ. 당기순이익", "VIII. 당기순이익", "지배기업 소유주", "VIII. 분기순손익", "VIII. 분기순이익", "I.당기순이익", "I.반기순이익",
                          "I.분기순이익", "반기연결순이익(손실)", "지배기업의 소유주지분", "지배기업소유주지분", "지배기업의소유주지분"]
                d10keys = ["영업활동현금흐름", "영업활동 현금흐름", "영업활동으로 인한 현금흐름", "영업활동 순현금흐름유입", "영업활동으로인한현금흐름", "영업활동으로 인한 순현금흐름", "Ⅰ. 영업활동으로 인한 현금흐름", "Ⅰ. 영업활동으로 인한 현금흐름", "영업활동순현금흐름 합계", "영업활동순현금흐름", "I. 영업활동현금흐름"]
                d11keys = ["유형자산의 취득", "유형자산 취득", "유형자산의취득"]
                d12keys = ["무형자산의 취득", "무형자산 취득", "무형자산의취득", "무형자산의 증가"]
                d13keys = ["토지의 취득", "건물의 취득", "구축물의 취득", "기계장치의 취득", "차량운반구의 취득", "공구와기구의 취득", "비품의 취득",
                           "기타유형자산의 취득", "건설중인자산의 취득", "투자부동산의 취득", "집기비품의 취득", "시험기기의 취득", "시설공사의 취득",
                           "토지의취득", "건물의취득", "구축물의취득", "기계장치의취득", "차량운반구의취득", "공구와기구의취득", "비품의취득",
                           "기타유형자산의취득", "건설중인자산의취득", "투자부동산의취득", "집기비품의취득", "시험기기의취득", "시설공사의취득"
                           ]
                d14keys = ["컴퓨터소프트웨어의 취득", "산업재산권의 취득", "소프트웨어의 취득", "기타무형자산의 취득", "소프트웨어의 증가",
                           "컴퓨터소프트웨어의취득", "산업재산권의취득", "소프트웨어의취득", "기타무형자산의취득", "소프트웨어의증가"]
                # if stock == "006360":
                #     print()
                if result is not {} and "연결재무제표" in result.keys():
                    logger.info("연결재무제표 start")
                    if "포괄손익계산서" in result["연결재무제표"].keys():
                        logger.info("연결재무제표 포괄손익계산서 start")
                        tmp_result1 = {key: result["연결재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                       result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d1keys}}
                        tmp_result2 = {key: result["연결재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                       result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d2keys}}
                        tmp_result3 = {key: result["연결재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                       result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d1keys}}
                        tmp_result4 = {key: result["연결재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                       result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d2keys}}
                        tmp_result8 = {key: result["연결재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                       result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d8keys}}
                        tmp_result9 = {key: result["연결재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                       result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d8keys}}
                        if tmp_result1:
                            for key in tmp_result1.keys():
                                if d1 is None:
                                    d1 = tmp_result1[key]
                                else:
                                    d1.update(tmp_result1[key])
                        if tmp_result2:
                            for key in tmp_result2.keys():
                                if d2 is None:
                                    d2 = tmp_result2[key]
                                else:
                                    d2.update(tmp_result2[key])
                        if tmp_result3:
                            for key in tmp_result3.keys():
                                if d3 is None:
                                    d3 = tmp_result3[key]
                                else:
                                    d3.update(tmp_result3[key])
                        if tmp_result4:
                            for key in tmp_result4.keys():
                                if d4 is None:
                                    d4 = tmp_result4[key]
                                else:
                                    d4.update(tmp_result4[key])
                        if tmp_result8:
                            for key in tmp_result8.keys():
                                if d8 is None:
                                    d8 = tmp_result8[key]
                                else:
                                    d8.update(tmp_result8[key])
                        if tmp_result9:
                            for key in tmp_result9.keys():
                                if d9 is None:
                                    d9 = tmp_result9[key]
                                else:
                                    d9.update(tmp_result9[key])
                    if "손익계산서" in result["연결재무제표"].keys():
                        logger.info("연결재무제표 손익계산서 start")
                        tmp_result1 = {key: result["연결재무제표"]["손익계산서"][key]["누계"] for key in
                                       result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d1keys}}
                        tmp_result2 = {key: result["연결재무제표"]["손익계산서"][key]["누계"] for key in
                                       result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d2keys}}
                        tmp_result3 = {key: result["연결재무제표"]["손익계산서"][key]["당기"] for key in
                                       result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d1keys}}
                        tmp_result4 = {key: result["연결재무제표"]["손익계산서"][key]["당기"] for key in
                                       result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d2keys}}
                        tmp_result8 = {key: result["연결재무제표"]["손익계산서"][key]["누계"] for key in
                                       result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d8keys}}
                        tmp_result9 = {key: result["연결재무제표"]["손익계산서"][key]["당기"] for key in
                                       result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d8keys}}
                        if tmp_result1:
                            for key in tmp_result1.keys():
                                if d1 is None:
                                    d1 = tmp_result1[key]
                                else:
                                    d1.update(tmp_result1[key])
                        if tmp_result2:
                            for key in tmp_result2.keys():
                                if d2 is None:
                                    d2 = tmp_result2[key]
                                else:
                                    d2.update(tmp_result2[key])
                        if tmp_result3:
                            for key in tmp_result3.keys():
                                if d3 is None:
                                    d3 = tmp_result3[key]
                                else:
                                    d3.update(tmp_result3[key])
                        if tmp_result4:
                            for key in tmp_result4.keys():
                                if d4 is None:
                                    d4 = tmp_result4[key]
                                else:
                                    d4.update(tmp_result4[key])
                        if tmp_result8:
                            for key in tmp_result8.keys():
                                if d8 is None:
                                    d8 = tmp_result8[key]
                                else:
                                    d8.update(tmp_result8[key])
                        if tmp_result9:
                            for key in tmp_result9.keys():
                                if d9 is None:
                                    d9 = tmp_result9[key]
                                else:
                                    d9.update(tmp_result9[key])
                    if "현금흐름표" in result["연결재무제표"].keys():
                        logger.info("연결재무제표 현금흐름표 start")
                        tmp_result10 = {key: result["연결재무제표"]["현금흐름표"][key] for key in
                                        result["연결재무제표"]["현금흐름표"].keys() & {keys for keys in d10keys}}
                        tmp_result11 = {key: result["연결재무제표"]["현금흐름표"][key] for key in
                                        result["연결재무제표"]["현금흐름표"].keys() & {keys for keys in d11keys}}
                        tmp_result12 = {key: result["연결재무제표"]["현금흐름표"][key] for key in
                                        result["연결재무제표"]["현금흐름표"].keys() & {keys for keys in d12keys}}
                        tmp_result13 = {key: result["연결재무제표"]["현금흐름표"][key] for key in
                                        result["연결재무제표"]["현금흐름표"].keys() & {keys for keys in d13keys}}
                        tmp_result14 = {key: result["연결재무제표"]["현금흐름표"][key] for key in
                                        result["연결재무제표"]["현금흐름표"].keys() & {keys for keys in d14keys}}
                        if tmp_result10:
                            for key in tmp_result10.keys():
                                if d10 is None:
                                    d10 = tmp_result10[key]
                                else:
                                    d10.update(tmp_result10[key])
                        if tmp_result11:
                            for key in tmp_result11.keys():
                                if d11 is None:
                                    d11 = tmp_result11[key]
                                else:
                                    d11.update(tmp_result11[key])
                        if tmp_result12:
                            for key in tmp_result12.keys():
                                if d12 is None:
                                    d12 = tmp_result12[key]
                                else:
                                    d12.update(tmp_result12[key])
                        if tmp_result13:
                            d13 = dictionary_add(tmp_result13)
                            # for key in tmp_result13.keys():
                            #     if d13 is None:
                            #         d13 = tmp_result13[key]
                            #     else:
                            #         d13.update(tmp_result13[key])
                        if tmp_result14:
                            d14 = dictionary_add(tmp_result14)
                            # for key in tmp_result14.keys():
                            #     if d14 is None:
                            #         d14 = tmp_result14[key]
                            #     else:
                            #         d14.update(tmp_result14[key])
                    if d11 is None: d11 = d13
                    if d12 is None: d12 = d14
                    d5 = result["연결재무제표"]["재무상태표"]["자산총계"] if "자산총계" in result["연결재무제표"]["재무상태표"].keys() else None
                    d6 = result["연결재무제표"]["재무상태표"]["부채총계"] if "부채총계" in result["연결재무제표"]["재무상태표"].keys() else None
                    d7 = result["연결재무제표"]["재무상태표"]["이익잉여금"] if "이익잉여금" in result["연결재무제표"]["재무상태표"].keys() else None
                    if d5 is None:
                        if "자  산  총  계" in result["연결재무제표"]["재무상태표"].keys():
                            d5 = result["연결재무제표"]["재무상태표"]["자  산  총  계"]
                    else:
                        if "자  산  총  계" in result["연결재무제표"]["재무상태표"].keys():
                            d5.update(result["연결재무제표"]["재무상태표"]["자  산  총  계"])
                    if d5 is None:
                        if "자산 총계" in result["연결재무제표"]["재무상태표"].keys():
                            d5 = result["연결재무제표"]["재무상태표"]["자산 총계"]
                    else:
                        if "자산 총계" in result["연결재무제표"]["재무상태표"].keys():
                            d5.update(result["연결재무제표"]["재무상태표"]["자산 총계"])
                    if d6 is None:
                        if "부  채  총  계" in result["연결재무제표"]["재무상태표"].keys():
                            d6 = result["연결재무제표"]["재무상태표"]["부  채  총  계"]
                    else:
                        if "부  채  총  계" in result["연결재무제표"]["재무상태표"].keys():
                            d6.update(result["연결재무제표"]["재무상태표"]["부  채  총  계"])
                    if d6 is None:
                        if "부채 총계" in result["연결재무제표"]["재무상태표"].keys():
                            d6 = result["연결재무제표"]["재무상태표"]["부채 총계"]
                    else:
                        if "부채 총계" in result["연결재무제표"]["재무상태표"].keys():
                            d6.update(result["연결재무제표"]["재무상태표"]["부채 총계"])
                    if d7 is None:
                        if "이익잉여금(결손금)" in result["연결재무제표"]["재무상태표"].keys():
                            d7 = result["연결재무제표"]["재무상태표"]["이익잉여금(결손금)"]
                    else:
                        if "이익잉여금(결손금)" in result["연결재무제표"]["재무상태표"].keys():
                            d7.update(result["연결재무제표"]["재무상태표"]["이익잉여금(결손금)"])
                    if d7 is None:
                        if "결손금" in result["연결재무제표"]["재무상태표"].keys():
                            d7 = result["연결재무제표"]["재무상태표"]["결손금"]
                    else:
                        if "결손금" in result["연결재무제표"]["재무상태표"].keys():
                            d7.update(result["연결재무제표"]["재무상태표"]["결손금"])
                else:
                    logger.info("재무제표 start")
                    if "포괄손익계산서" in result["재무제표"].keys():
                        logger.info("재무제표 포괄손익계산서 start")
                        tmp_result1 = {key: result["재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                       result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d1keys}}
                        tmp_result2 = {key: result["재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                       result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d2keys}}
                        tmp_result3 = {key: result["재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                       result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d1keys}}
                        tmp_result4 = {key: result["재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                       result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d2keys}}
                        tmp_result8 = {key: result["재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                       result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d8keys}}
                        tmp_result9 = {key: result["재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                       result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d8keys}}
                        if tmp_result1:
                            for key in tmp_result1.keys():
                                if d1 is None:
                                    d1 = tmp_result1[key]
                                else:
                                    d1.update(tmp_result1[key])
                        if tmp_result2:
                            for key in tmp_result2.keys():
                                if d2 is None:
                                    d2 = tmp_result2[key]
                                else:
                                    d2.update(tmp_result2[key])
                        if tmp_result3:
                            for key in tmp_result3.keys():
                                if d3 is None:
                                    d3 = tmp_result3[key]
                                else:
                                    d3.update(tmp_result3[key])
                        if tmp_result4:
                            for key in tmp_result4.keys():
                                if d4 is None:
                                    d4 = tmp_result4[key]
                                else:
                                    d4.update(tmp_result4[key])
                        if tmp_result8:
                            for key in tmp_result8.keys():
                                if d8 is None:
                                    d8 = tmp_result8[key]
                                else:
                                    d8.update(tmp_result8[key])
                        if tmp_result9:
                            for key in tmp_result9.keys():
                                if d9 is None:
                                    d9 = tmp_result9[key]
                                else:
                                    d9.update(tmp_result9[key])
                    if "손익계산서" in result["재무제표"].keys():
                        logger.info("재무제표 손익계산서 매출 start")
                        tmp_result1 = {key: result["재무제표"]["손익계산서"][key]["누계"] for key in
                                       result["재무제표"]["손익계산서"].keys() & {keys for keys in d1keys}}
                        tmp_result2 = {key: result["재무제표"]["손익계산서"][key]["누계"] for key in
                                       result["재무제표"]["손익계산서"].keys() & {keys for keys in d2keys}}
                        tmp_result3 = {key: result["재무제표"]["손익계산서"][key]["당기"] for key in
                                       result["재무제표"]["손익계산서"].keys() & {keys for keys in d1keys}}
                        tmp_result4 = {key: result["재무제표"]["손익계산서"][key]["당기"] for key in
                                       result["재무제표"]["손익계산서"].keys() & {keys for keys in d2keys}}
                        tmp_result8 = {key: result["재무제표"]["손익계산서"][key]["누계"] for key in
                                       result["재무제표"]["손익계산서"].keys() & {keys for keys in d8keys}}
                        tmp_result9 = {key: result["재무제표"]["손익계산서"][key]["당기"] for key in
                                       result["재무제표"]["손익계산서"].keys() & {keys for keys in d8keys}}
                        if tmp_result1:
                            for key in tmp_result1.keys():
                                if d1 is None:
                                    d1 = tmp_result1[key]
                                else:
                                    d1.update(tmp_result1[key])
                        if tmp_result2:
                            for key in tmp_result2.keys():
                                if d2 is None:
                                    d2 = tmp_result2[key]
                                else:
                                    d2.update(tmp_result2[key])
                        if tmp_result3:
                            for key in tmp_result3.keys():
                                if d3 is None:
                                    d3 = tmp_result3[key]
                                else:
                                    d3.update(tmp_result3[key])
                        if tmp_result4:
                            for key in tmp_result4.keys():
                                if d4 is None:
                                    d4 = tmp_result4[key]
                                else:
                                    d4.update(tmp_result4[key])
                        if tmp_result8:
                            for key in tmp_result8.keys():
                                if d8 is None:
                                    d8 = tmp_result8[key]
                                else:
                                    d8.update(tmp_result8[key])
                        if tmp_result9:
                            for key in tmp_result9.keys():
                                if d9 is None:
                                    d9 = tmp_result9[key]
                                else:
                                    d9.update(tmp_result9[key])
                    if "현금흐름표" in result["재무제표"].keys():
                        logger.info("재무제표 현금흐름표 start")
                        tmp_result10 = {key: result["재무제표"]["현금흐름표"][key] for key in
                                       result["재무제표"]["현금흐름표"].keys() & {keys for keys in d10keys}}
                        tmp_result11 = {key: result["재무제표"]["현금흐름표"][key] for key in
                                        result["재무제표"]["현금흐름표"].keys() & {keys for keys in d11keys}}
                        tmp_result12 = {key: result["재무제표"]["현금흐름표"][key] for key in
                                        result["재무제표"]["현금흐름표"].keys() & {keys for keys in d12keys}}
                        tmp_result13 = {key: result["재무제표"]["현금흐름표"][key] for key in
                                        result["재무제표"]["현금흐름표"].keys() & {keys for keys in d13keys}}
                        tmp_result14 = {key: result["재무제표"]["현금흐름표"][key] for key in
                                        result["재무제표"]["현금흐름표"].keys() & {keys for keys in d14keys}}
                        if tmp_result10:
                            for key in tmp_result10.keys():
                                if d10 is None:
                                    d10 = tmp_result10[key]
                                else:
                                    d10.update(tmp_result10[key])
                        if tmp_result11:
                            for key in tmp_result11.keys():
                                if d11 is None:
                                    d11 = tmp_result11[key]
                                else:
                                    d11.update(tmp_result11[key])
                        if tmp_result12:
                            for key in tmp_result12.keys():
                                if d12 is None:
                                    d12 = tmp_result12[key]
                                else:
                                    d12.update(tmp_result12[key])
                        if tmp_result13:
                            d13 = dictionary_add(tmp_result13)
                            # for key in tmp_result13.keys():
                            #     if d13 is None:
                            #         d13 = tmp_result13[key]
                            #     else:
                            #         d13.update(tmp_result13[key])
                        if tmp_result14:
                            d14 = dictionary_add(tmp_result14)
                            # for key in tmp_result14.keys():
                            #     if d14 is None:
                            #         d14 = tmp_result14[key]
                            #     else:
                            #         d14.update(tmp_result14[key])
                    if d11 is None: d11 = d13
                    if d12 is None: d12 = d14
                    d5 = result["재무제표"]["재무상태표"]["자산총계"] if "자산총계" in result["재무제표"]["재무상태표"].keys() else None
                    d6 = result["재무제표"]["재무상태표"]["부채총계"] if "부채총계" in result["재무제표"]["재무상태표"].keys() else None
                    d7 = result["재무제표"]["재무상태표"]["이익잉여금"] if "이익잉여금" in result["재무제표"]["재무상태표"].keys() else None
                    if d5 is None:
                        if "자  산  총  계" in result["재무제표"]["재무상태표"].keys():
                            d5 = result["재무제표"]["재무상태표"]["자  산  총  계"]
                    else:
                        if "자  산  총  계" in result["재무제표"]["재무상태표"].keys():
                            d5.update(result["재무제표"]["재무상태표"]["자  산  총  계"])
                    if d5 is None:
                        if "자산 총계" in result["재무제표"]["재무상태표"].keys():
                            d5 = result["재무제표"]["재무상태표"]["자산 총계"]
                    else:
                        if "자산 총계" in result["재무제표"]["재무상태표"].keys():
                            d5.update(result["재무제표"]["재무상태표"]["자산 총계"])
                    if d6 is None:
                        if "부  채  총  계" in result["재무제표"]["재무상태표"].keys():
                            d6 = result["재무제표"]["재무상태표"]["부  채  총  계"]
                    else:
                        if "부  채  총  계" in result["재무제표"]["재무상태표"].keys():
                            d6.update(result["재무제표"]["재무상태표"]["부  채  총  계"])
                    if d6 is None:
                        if "부채 총계" in result["재무제표"]["재무상태표"].keys():
                            d6 = result["재무제표"]["재무상태표"]["부채 총계"]
                    else:
                        if "부채 총계" in result["재무제표"]["재무상태표"].keys():
                            d6.update(result["재무제표"]["재무상태표"]["부채 총계"])
                    if d7 is None:
                        if "이익잉여금(결손금)" in result["재무제표"]["재무상태표"].keys():
                            d7 = result["재무제표"]["재무상태표"]["이익잉여금(결손금)"]
                    else:
                        if "이익잉여금(결손금)" in result["재무제표"]["재무상태표"].keys():
                            d7.update(result["재무제표"]["재무상태표"]["이익잉여금(결손금)"])
                    if d7 is None:
                        if "결손금" in result["재무제표"]["재무상태표"].keys():
                            d7 = result["재무제표"]["재무상태표"]["결손금"]
                    else:
                        if "결손금" in result["재무제표"]["재무상태표"].keys():
                            d7.update(result["재무제표"]["재무상태표"]["결손금"])
                logger.info("매출액 누계 : {}".format(d1))  # 매출액 누계
                logger.info("영업이익 누계 : {}".format(d2))  # 영업이익 누계
                logger.info("매출액 당기 : {}".format(d3))  # 매출액 당기
                logger.info("영업이익 당기 : {}".format(d4))  # 영업이익 당기
                logger.info("자산총계 : {}".format(d5))  # 자산총계
                logger.info("부채총계 : {}".format(d6))  # 부채총계
                logger.info("이익잉여금 : {}".format(d7))  # 이익잉여금
                logger.info("당기순이익 누계 : {}".format(d8))  # 당기순이익 누계
                logger.info("당기순이익 : {}".format(d9))  # 당기순이익
                logger.info("영업활동현금흐름 : {}".format(d10))  # 영업활동현금흐름
                logger.info("유형자산의 취득 : {}".format(d11))  # 유형자산의 취득
                logger.info("무형자산의 취득 : {}".format(d12))  # 무형자산의 취득
                logger.info("유형자산의 취득(유형자산의 취득으로 표시되지 않는) : {}".format(d13))  # 유형자산의 취득(유형자산의 취득으로 표시되지 않는)
                logger.info("무형자산의 취득(무형자산의 취득으로 표시되지 않는) : {}".format(d14))  # 무형자산의 취득(무형자산의 취득으로 표시되지 않는)
                if d10 is None:
                    none_list.append("[{}][{}]-영업활동현금흐름".format(stock.code, stock.name))
                if d11 is None:
                    none_list.append("[{}][{}]-유형자산의 취득".format(stock.code, stock.name))
                if d12 is None:
                    none_list.append("[{}][{}]-무형자산의 취득".format(stock.code, stock.name))
                for key1 in d1.keys():
                    current_key = key1
                    if "Rate" in key1: continue
                    if "4/4" in key1:
                        data[stock.code]["PL"]["Y"]["매출액영업이익률"] = dict(sorted({
                                                                             k: round(float(
                                                                                 d2[key1][k].replace(",", "")) / float(
                                                                                 d1[key1][k].replace(",", "")) * 100,
                                                                                      2) if float(
                                                                                 d1[key1][k].replace(",",
                                                                                                     "")) != 0.0 else 0
                                                                             for k in d1[key1]}.items()))

                        data[stock.code]["PL"]["Y"]["매출액"] = dict(
                            sorted({k: float(d1[key1][k].replace(",", "")) for k in
                                    d1[key1]}.items()))
                        # data[stock.code]["PL"]["Y"]["매출액"]["최근"] = provision_info[stock]["PL"]["Y"]["매출액"]
                        data[stock.code]["PL"]["Y"]["영업이익"] = dict(
                            sorted({k: float(d2[key1][k].replace(",", "")) for k in
                                    d2[key1]}.items()))
                        data[stock.code]["PL"]["Y"]["당기순이익"] = dict(
                            sorted({k: float(d8[key1][k].replace(",", "")) for k in
                                    d8[key1]}.items()))
                        # data[stock.code]["PL"]["Y"]["영업이익"]["최근"] = provision_info[stock]["PL"]["Y"]["영업이익"]
                        for k in sorted(d1[key1]):
                            dicTemp1[k] = float(d1[key1][k].replace(",", ""))
                        for k in sorted(d2[key1]):
                            dicTemp2[k] = float(d2[key1][k].replace(",", ""))
                        for k in sorted(d8[key1]):
                            dicTemp8[k] = float(d8[key1][k].replace(",", ""))
                    else:
                        for k in sorted(d1[key1]):
                            dicTemp0[k] = round(
                                float(d2[key1][k].replace(",", "")) / float(d1[key1][k].replace(",", "")) * 100,
                                2) if float(d1[key1][k].replace(",", "")) != 0.0 else 0
                        for k in sorted(d1[key1]):
                            dicTemp1[k] = float(d1[key1][k].replace(",", ""))
                            # data[stock.code]["PL"]["Q"]["누계매출액"][k] = float(d1[key1][k].replace(",", ""))
                        for k in sorted(d2[key1]):
                            dicTemp2[k] = float(d2[key1][k].replace(",", ""))
                            # data[stock.code]["PL"]["Q"]["누계영업이익"][k] = float(d2[key1][k].replace(",", ""))
                        for k in sorted(d3[key1]):
                            dicTemp3[k] = float(d3[key1][k].replace(",", ""))
                            # data[stock.code]["PL"]["Q"]["당기매출액"][k] = float(d3[key1][k].replace(",", ""))
                        for k in sorted(d4[key1]):
                            dicTemp4[k] = float(d4[key1][k].replace(",", ""))
                            # data[stock.code]["PL"]["Q"]["당기영업이익"][k] = float(d4[key1][k].replace(",", ""))
                        for k in sorted(d8[key1]):
                            dicTemp8[k] = float(d8[key1][k].replace(",", ""))
                            # data[stock.code]["PL"]["Q"]["당기매출액"][k] = float(d3[key1][k].replace(",", ""))
                        for k in sorted(d9[key1]):
                            dicTemp9[k] = float(d9[key1][k].replace(",", ""))
                            # data[stock.code]["PL"]["Q"]["당기영업이익"][k] = float(d4[key1][k].replace(",", ""))
                for key2 in d10.keys():
                    current_key = key2
                    if "Rate" in key2: continue
                    # if key2 not in data[stock.code]["CF"]["FCF"].keys():
                    #     data[stock.code]["CF"]["FCF"][key2] = {}
                    for key3 in d10[key2].keys():
                        yhasset = int(d11[key2][key3]) if d11 is not None and key2 in d11.keys() and key3 in d11[key2].keys() else 0
                        mhasset = int(d12[key2][key3]) if d12 is not None and key2 in d12.keys() and key3 in d12[key2].keys() else 0
                        data[stock.code]["CF"]["FCF"][key3] = int(d10[key2][key3]) - (yhasset + mhasset)
                data[stock.code]["PL"]["Q"]["매출액영업이익률"] = dict(sorted(dicTemp0.items()))
                data[stock.code]["PL"]["Q"]["누계매출액추이"] = dict(sorted(dicTemp1.items()))
                data[stock.code]["PL"]["Q"]["누계영업이익추이"] = dict(sorted(dicTemp2.items()))
                data[stock.code]["PL"]["Q"]["당기매출액"] = dict(sorted(dicTemp3.items()))
                data[stock.code]["PL"]["Q"]["당기영업이익"] = dict(sorted(dicTemp4.items()))
                data[stock.code]["PL"]["Q"]["누계당기순이익추이"] = dict(sorted(dicTemp8.items()))
                data[stock.code]["PL"]["Q"]["당기순이익"] = dict(sorted(dicTemp9.items()))
                # print("MakeAvg1?")
                # print(data)
                data[stock.code]["AverageRate"]["Y"]["매출액영업이익률"] = round(sum(
                    data[stock.code]["PL"]["Y"]["매출액영업이익률"].values()) / float(
                    len(data[stock.code]["PL"]["Y"]["매출액영업이익률"])), 2) if "매출액영업이익률" in data[stock.code]["PL"][
                    "Y"].keys() else None
                # print("MakeAvg2?")
                data[stock.code]["AverageRate"]["Y"]["매출액"] = round(sum(
                    data[stock.code]["PL"]["Y"]["매출액"].values()) / float(
                    len(data[stock.code]["PL"]["Y"]["매출액"])), 0) if "매출액" in data[stock.code]["PL"]["Y"].keys() and \
                                                                    len(data[stock.code]["PL"]["Y"][
                                                                            "매출액"]) != 0 else None
                # print("MakeAvg3?")
                data[stock.code]["AverageRate"]["Y"]["영업이익"] = round(sum(
                    data[stock.code]["PL"]["Y"]["영업이익"].values()) / float(
                    len(data[stock.code]["PL"]["Y"]["영업이익"])), 0) if "영업이익" in data[stock.code]["PL"]["Y"].keys() and \
                                                                     len(data[stock.code]["PL"]["Y"][
                                                                             "영업이익"]) != 0 else None
                data[stock.code]["AverageRate"]["Y"]["당기순이익"] = round(sum(
                    data[stock.code]["PL"]["Y"]["당기순이익"].values()) / float(
                    len(data[stock.code]["PL"]["Y"]["당기순이익"])), 0) if "당기순이익" in data[stock.code]["PL"]["Y"].keys() and \
                                                                      len(data[stock.code]["PL"]["Y"][
                                                                              "당기순이익"]) != 0 else None
                # print("MakeAvg4?")
                data[stock.code]["AverageRate"]["Q"]["매출액영업이익률"] = round(sum(
                    data[stock.code]["PL"]["Q"]["매출액영업이익률"].values()) / float(
                    len(data[stock.code]["PL"]["Q"]["매출액영업이익률"])), 2) if "매출액영업이익률" in data[stock.code]["PL"][
                    "Q"].keys() and \
                                                                         len(data[stock.code]["PL"]["Q"][
                                                                                 "매출액영업이익률"]) != 0 else None
                # print("MakeAvg5?")
                data[stock.code]["AverageRate"]["Q"]["매출액"] = round(sum(
                    data[stock.code]["PL"]["Q"]["당기매출액"].values()) / float(
                    len(data[stock.code]["PL"]["Q"]["당기매출액"])), 0) if "당기매출액" in data[stock.code]["PL"]["Q"].keys() and \
                                                                      len(data[stock.code]["PL"]["Q"][
                                                                              "당기매출액"]) != 0 else None
                # print("MakeAvg6?")
                data[stock.code]["AverageRate"]["Q"]["영업이익"] = round(sum(
                    data[stock.code]["PL"]["Q"]["당기영업이익"].values()) / float(
                    len(data[stock.code]["PL"]["Q"]["당기영업이익"])), 0) if "당기영업이익" in data[stock.code]["PL"][
                    "Q"].keys() and \
                                                                       len(data[stock.code]["PL"]["Q"][
                                                                               "당기영업이익"]) != 0 else None
                data[stock.code]["AverageRate"]["Q"]["당기순이익"] = round(sum(
                    data[stock.code]["PL"]["Q"]["당기순이익"].values()) / float(
                    len(data[stock.code]["PL"]["Q"]["당기순이익"])), 0) if "당기순이익" in data[stock.code]["PL"]["Q"].keys() and \
                                                                      len(data[stock.code]["PL"]["Q"][
                                                                              "당기순이익"]) != 0 else None
                # print("MakeAvg7?")
                # 손익계산서 분석 끝
                for key1 in d1.keys():
                    if "Rate" in key1: continue
                    if d5 is not None and key1 in d5.keys():
                        for k in sorted(d5[key1]):
                            dicTemp5[k] = float(d5[key1][k].replace(",", "")) if d5 is not None else 0
                    if d6 is not None and key1 in d6.keys():
                        for k in sorted(d6[key1]):
                            dicTemp6[k] = float(d6[key1][k].replace(",", "")) if d6 is not None else 0
                    if d7 is not None and key1 in d7.keys():
                        for k in sorted(d7[key1]):
                            dicTemp7[k] = float(d7[key1][k].replace(",", "")) if d7 is not None else 0
                    if d10 is not None and key1 in d10.keys():
                        for k in sorted(d10[key1]):
                            dicTemp10[k] = float(str(d10[key1][k]).replace(",", "")) if d10 is not None else 0
                    if d11 is not None and key1 in d11.keys():
                        for k in sorted(d11[key1]):
                            dicTemp11[k] = float(str(d11[key1][k]).replace(",", "")) if d11 is not None else 0
                    if d12 is not None and key1 in d12.keys():
                        for k in sorted(d12[key1]):
                            dicTemp12[k] = float(str(d12[key1][k]).replace(",", "")) if d12 is not None else 0
                data[stock.code]["FS"]["TotalAsset"] = dict(sorted(dicTemp5.items()))
                data[stock.code]["FS"]["TotalDebt"] = dict(sorted(dicTemp6.items()))
                data[stock.code]["FS"]["RetainedEarnings"] = dict(sorted(dicTemp7.items()))
                data[stock.code]["CF"]["영업활동현금흐름"] = dict(sorted(dicTemp10.items()))
                data[stock.code]["CF"]["유형자산취득"] = dict(sorted(dicTemp11.items()))
                data[stock.code]["CF"]["무형자산취득"] = dict(sorted(dicTemp12.items()))
                data[stock.code]["CF"]["FCF"] = dict(sorted(data[stock.code]["CF"]["FCF"].items()))
        except Exception as e:
            logger.error(e)
            # logger.error(current_pos)
            logger.error(current_key)
            for key in current_pos.keys():  # key = ["연결재무제표", "재무제표"]
                for report in current_pos[key].keys():  # report = ["재무상태표", "손익계산서"]
                    if report not in ["손익계산서", "포괄손익계산서"]:  # ["재무상태표", "현금흐름표", "자본변동표"]:
                        for acc in current_pos[key][report].keys():
                            # acc = ["유동자산", "비유동자산", "자산총계", "유동부채", "비유동부채", "부채총계", "자본금", "이익잉여금", "자본총계"]
                            for category in sorted(current_pos[key][report][acc].keys()):
                                # category = ["YYYY 1/4", "YYYY 2/4", "YYYY 3/4", "YYYY 4/4"]
                                logger.error("{}\t{}\t{}\t{}\t{}".format(key, report, acc, category,
                                                                         current_pos[key][report][acc][category]))
                                # for k in result[key][report][acc][category].keys():
                                #     print(key, report, acc, category, k, current_pos[key][report][acc][category][k])
                    else:
                        for acc in current_pos[key][report].keys():
                            # acc = ["매출액", 영업이익", "법인세차감전", "당기순이익"]
                            for category in current_pos[key][report][acc].keys():
                                # category = ["누계", "당기"]
                                for k in sorted(current_pos[key][report][acc][category].keys()):
                                    # k = ["YYYY 1/4", "YYYY 2/4", "YYYY 3/4", "YYYY 4/4"]
                                    logger.error("{}\t{}\t{}\t{}\t{}\t{}".format(key, report, acc, category, k,
                                                                                 current_pos[key][report][acc][
                                                                                     category][k]))
        logger.info(data)

    for k in data.keys():
        avg_sales_op_profit_rate = None
        avg_sales = None
        avg_op_profit = None
        avg_net_income = None
        last_sales_op_profit_rate = None
        last_sales = None
        last_op_profit = None
        last_net_income = None
        before_sales = None
        before_op_profit = None
        before_net_income = None
        fcf_last_5 = None
        ocf_last_5 = None
        earn_last_5 = None
        pl_last_5 = None
        last_5_keys = list(data[k]["CF"]["영업활동현금흐름"].keys())[-6:]
        for lastkey in last_5_keys:
            if lastkey not in data[k]["CF"]["FCF"].keys() or lastkey not in data[k]["CF"]["영업활동현금흐름"].keys() \
               or lastkey not in data[k]["FS"]["RetainedEarnings"].keys() or lastkey not in data[k]["PL"]["Q"]["누계당기순이익추이"].keys():
                last_5_keys.remove(lastkey)
        try:
            fcf_last_5 = {lk: data[k]["CF"]["FCF"][lk] for lk in last_5_keys}
            ocf_last_5 = {lk: data[k]["CF"]["영업활동현금흐름"][lk] for lk in last_5_keys}
            earn_last_5 = {lk: data[k]["FS"]["RetainedEarnings"][lk] for lk in last_5_keys}
            pl_last_5 = {lk: data[k]["PL"]["Q"]["누계당기순이익추이"][lk] for lk in last_5_keys}
        except Exception as e:
            print(last_5_keys)
            print(k)
            print(fcf_last_5)
            print(ocf_last_5)
            print(earn_last_5)
            print(pl_last_5)
        print(k, data[k]["corp_name"], "*" * 100)
        for key in data[k]["PL"]["Y"].keys():
            print("연간", key, data[k]["PL"]["Y"][key])
        print("연간", data[k]["AverageRate"]["Y"])
        for key in data[k]["PL"]["Q"].keys():
            print("당기", key, data[k]["PL"]["Q"][key])
        print("당기", data[k]["AverageRate"]["Q"])
        print("재무상태표-자산총계", data[k]["FS"]["TotalAsset"])
        print("재무상태표-부채총계", data[k]["FS"]["TotalDebt"])
        print("재무상태표-이익잉여금", data[k]["FS"]["RetainedEarnings"])
        print("현금흐름표-영업활동현금흐름", data[k]["CF"]["영업활동현금흐름"])
        print("현금흐름표-유형자산취득", data[k]["CF"]["유형자산취득"])
        print("현금흐름표-무형자산취득", data[k]["CF"]["무형자산취득"])
        print("FreeCashFlow", data[k]["CF"]["FCF"])
        # print("here1?")
        if "매출액영업이익률" in data[k]["AverageRate"]["Y"].keys() \
                and "매출액" in data[k]["AverageRate"]["Y"].keys() \
                and "영업이익" in data[k]["AverageRate"]["Y"].keys() \
                and "당기순이익" in data[k]["AverageRate"]["Y"].keys():
            # print("here2?")
            avg_sales_op_profit_rate = data[k]["AverageRate"]["Y"]["매출액영업이익률"]
            avg_sales = data[k]["AverageRate"]["Y"]["매출액"]
            avg_op_profit = data[k]["AverageRate"]["Y"]["영업이익"]
            avg_net_income = data[k]["AverageRate"]["Y"]["당기순이익"]

            if "매출액영업이익률" in data[k]["PL"]["Q"].keys():
                # print("here3?")
                last_sales_op_profit_rate = data[k]["PL"]["Q"]["매출액영업이익률"].popitem()[1] if len(data[k]["PL"]["Q"]["매출액영업이익률"]) > 0 else None
                last_sales = data[k]["PL"]["Q"]["누계매출액추이"].popitem()[1] if len(data[k]["PL"]["Q"]["누계매출액추이"]) > 0 else None
                if "매출액" in data[k]["PL"]["Y"].keys():
                    data[k]["PL"]["Y"]["매출액"].popitem() if len(data[k]["PL"]["Y"]["매출액"]) > 0 else None
                    before_sales = data[k]["PL"]["Y"]["매출액"].popitem()[1] if len(data[k]["PL"]["Y"]["매출액"]) > 0 else None
                last_op_profit = data[k]["PL"]["Q"]["누계영업이익추이"].popitem()[1] if len(data[k]["PL"]["Q"]["누계영업이익추이"]) > 0 else None
                if "영업이익" in data[k]["PL"]["Y"].keys():
                    data[k]["PL"]["Y"]["영업이익"].popitem() if len(data[k]["PL"]["Y"]["영업이익"]) > 0 else None
                    before_op_profit = data[k]["PL"]["Y"]["영업이익"].popitem()[1] if len(data[k]["PL"]["Y"]["영업이익"]) > 0 else None
                last_net_income = data[k]["PL"]["Q"]["누계당기순이익추이"].popitem()[1] if len(data[k]["PL"]["Q"]["누계당기순이익추이"]) > 0 else None
                if "당기순이익" in data[k]["PL"]["Y"].keys():
                    data[k]["PL"]["Y"]["당기순이익"].popitem() if len(data[k]["PL"]["Y"]["당기순이익"]) > 0 else None
                    before_net_income = data[k]["PL"]["Y"]["당기순이익"].popitem()[1] if len(data[k]["PL"]["Y"]["당기순이익"]) > 0 else None
        # print("here4?")
        if avg_sales_op_profit_rate and last_sales_op_profit_rate:
            if last_sales_op_profit_rate > 0 and avg_sales_op_profit_rate > 0 and last_sales_op_profit_rate > avg_sales_op_profit_rate:
                # print("here5?")
                if avg_sales and last_sales and before_sales and \
                        avg_net_income and last_net_income and before_net_income and \
                        last_sales > avg_sales and last_sales > before_sales and \
                        last_net_income > avg_net_income and last_net_income > before_net_income:
                    if last_sales_op_profit_rate > 20:
                        best[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "last_report": data[k]["last_report"], "업종": data[k]["category"],
                                   "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                   "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                   "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                   "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                   "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                   "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                   "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                                   "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                   "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                   "직전당기순이익": format(before_net_income, ",") if before_net_income is not None else None,
                                   "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None,
                                   "FCF": fcf_last_5 if fcf_last_5 is not None else None,
                                   "OCF": ocf_last_5 if ocf_last_5 is not None else None,
                                   "EARN": earn_last_5 if earn_last_5 is not None else None,
                                   "PL": pl_last_5 if pl_last_5 is not None else None
                                   }
                        call = json.loads(requests.get(
                            "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                                k)).content.decode("utf-8"))
                        best[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                        best[k]["PER"] = call["per"]
                        best[k]["EPS"] = call["eps"]
                        best[k]["PBR"] = call["pbr"]
                        best[k]["현재가"] = f'{call["now"]:,}'
                        best[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                  data[k][
                                                                                                      "list_shares"] else 0
                        best[k]["PER2"] = round(call["now"] / best[k]["EPS2"], 0) if best[k]["EPS2"] != 0 else 0
                        best[k]["예상주가"] = format(int(round(best[k]["EPS2"] * best[k]["PER"], 0)), ",") if best[k]["EPS2"] and best[k]["PER"] else 0
                    elif np.sign(last_sales_op_profit_rate) > np.sign(avg_sales_op_profit_rate):
                        best[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "last_report": data[k]["last_report"], "업종": data[k]["category"],
                                   "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                   "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                   "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                   "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                   "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                   "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                   "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                                   "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                   "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                   "직전당기순이익": format(before_net_income, ",") if before_net_income is not None else None,
                                   "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None,
                                   "FCF": fcf_last_5 if fcf_last_5 is not None else None,
                                   "OCF": ocf_last_5 if ocf_last_5 is not None else None,
                                   "EARN": earn_last_5 if earn_last_5 is not None else None,
                                   "PL": pl_last_5 if pl_last_5 is not None else None}
                        call = json.loads(requests.get(
                            "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                                k)).content.decode("utf-8"))
                        best[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                        best[k]["PER"] = call["per"]
                        best[k]["EPS"] = call["eps"]
                        best[k]["PBR"] = call["pbr"]
                        best[k]["현재가"] = f'{call["now"]:,}'
                        best[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                  data[k][
                                                                                                      "list_shares"] else 0
                        best[k]["PER2"] = round(call["now"] / best[k]["EPS2"], 0) if best[k]["EPS2"] != 0 else 0
                        best[k]["예상주가"] = format(int(round(best[k]["EPS2"] * best[k]["PER"], 0)), ",") if best[k]["EPS2"] and best[k]["PER"] else 0
                    else:
                        better[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "last_report": data[k]["last_report"], "업종": data[k]["category"],
                                     "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                     "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                     "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                     "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                     "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                     "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                     "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                                     "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                     "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                     "직전당기순이익": format(before_net_income,
                                                       ",") if before_net_income is not None else None,
                                     "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None,
                                     "FCF": fcf_last_5 if fcf_last_5 is not None else None,
                                     "OCF": ocf_last_5 if ocf_last_5 is not None else None,
                                     "EARN": earn_last_5 if earn_last_5 is not None else None,
                                     "PL": pl_last_5 if pl_last_5 is not None else None
                                     }
                        call = json.loads(requests.get(
                            "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                                k)).content.decode("utf-8"))
                        better[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                        better[k]["PER"] = call["per"]
                        better[k]["EPS"] = call["eps"]
                        better[k]["PBR"] = call["pbr"]
                        better[k]["현재가"] = f'{call["now"]:,}'
                        better[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                  data[k][
                                                                                                      "list_shares"] else 0
                        better[k]["PER2"] = round(call["now"] / better[k]["EPS2"], 0) if better[k]["EPS2"] != 0 else 0
                        better[k]["예상주가"] = format(int(round(better[k]["EPS2"] * better[k]["PER"], 0)), ",") if better[k]["EPS2"] and better[k]["PER"] else 0
                else:
                    if last_sales_op_profit_rate > 15:
                        better[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "last_report": data[k]["last_report"], "업종": data[k]["category"],
                                     "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                     "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                     "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                     "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                     "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                     "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                     "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                                     "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                     "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                     "직전당기순이익": format(before_net_income,
                                                       ",") if before_net_income is not None else None,
                                     "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None,
                                     "FCF": fcf_last_5 if fcf_last_5 is not None else None,
                                     "OCF": ocf_last_5 if ocf_last_5 is not None else None,
                                     "EARN": earn_last_5 if earn_last_5 is not None else None,
                                     "PL": pl_last_5 if pl_last_5 is not None else None
                                     }
                        call = json.loads(requests.get(
                            "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                                k)).content.decode("utf-8"))
                        better[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                        better[k]["PER"] = call["per"]
                        better[k]["EPS"] = call["eps"]
                        better[k]["PBR"] = call["pbr"]
                        better[k]["현재가"] = f'{call["now"]:,}'
                        better[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                  data[k][
                                                                                                      "list_shares"] else 0
                        better[k]["PER2"] = round(call["now"] / better[k]["EPS2"], 0) if better[k]["EPS2"] != 0 else 0
                        better[k]["예상주가"] = format(int(round(better[k]["EPS2"] * better[k]["PER"], 0)), ",") if better[k]["EPS2"] and better[k]["PER"] else 0
                    else:
                        # print("here7?")
                        good[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "last_report": data[k]["last_report"], "업종": data[k]["category"],
                                   "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                   "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                   "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                   "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                   "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                   "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                   "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                                   "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                   "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                   "직전당기순이익": format(before_net_income, ",") if before_net_income is not None else None,
                                   "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None,
                                   "FCF": fcf_last_5 if fcf_last_5 is not None else None,
                                   "OCF": ocf_last_5 if ocf_last_5 is not None else None,
                                   "EARN": earn_last_5 if earn_last_5 is not None else None,
                                   "PL": pl_last_5 if pl_last_5 is not None else None
                                   }
                        call = json.loads(requests.get(
                            "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                                k)).content.decode("utf-8"))
                        good[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                        good[k]["PER"] = call["per"]
                        good[k]["EPS"] = call["eps"]
                        good[k]["PBR"] = call["pbr"]
                        good[k]["현재가"] = f'{call["now"]:,}'
                        good[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                  data[k][
                                                                                                      "list_shares"] else 0
                        good[k]["PER2"] = round(call["now"] / good[k]["EPS2"], 0) if good[k]["EPS2"] != 0 else 0
                        good[k]["예상주가"] = format(int(round(good[k]["EPS2"] * good[k]["PER"], 0)), ",") if good[k]["EPS2"] and good[k]["PER"] else 0
            else:
                if last_sales_op_profit_rate > 15:
                    better[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "last_report": data[k]["last_report"], "업종": data[k]["category"],
                                 "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                 "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                 "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                 "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                 "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                 "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                 "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                                 "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                 "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                 "직전당기순이익": format(before_net_income, ",") if before_net_income is not None else None,
                                 "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None,
                                 "FCF": fcf_last_5 if fcf_last_5 is not None else None,
                                 "OCF": ocf_last_5 if ocf_last_5 is not None else None,
                                 "EARN": earn_last_5 if earn_last_5 is not None else None,
                                 "PL": pl_last_5 if pl_last_5 is not None else None
                                 }
                    call = json.loads(requests.get(
                        "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                            k)).content.decode("utf-8"))
                    better[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                    better[k]["PER"] = call["per"]
                    better[k]["EPS"] = call["eps"]
                    better[k]["PBR"] = call["pbr"]
                    better[k]["현재가"] = f'{call["now"]:,}'
                    better[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                  data[k][
                                                                                                      "list_shares"] else 0
                    better[k]["PER2"] = round(call["now"] / better[k]["EPS2"], 0) if better[k]["EPS2"] != 0 else 0
                    better[k]["예상주가"] = format(int(round(better[k]["EPS2"] * better[k]["PER"], 0)), ",") if better[k]["EPS2"] and better[k]["PER"] else 0
                else:
                    soso[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "last_report": data[k]["last_report"], "업종": data[k]["category"],
                               "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                               "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                               "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                               "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                               "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                               "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                               "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                               "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                               "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                               "직전당기순이익": format(before_net_income, ",") if before_net_income is not None else None,
                               "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None,
                               "FCF": fcf_last_5 if fcf_last_5 is not None else None,
                               "OCF": ocf_last_5 if ocf_last_5 is not None else None,
                               "EARN": earn_last_5 if earn_last_5 is not None else None,
                               "PL": pl_last_5 if pl_last_5 is not None else None
                               }
                    call = json.loads(requests.get(
                        "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                            k)).content.decode("utf-8"))
                    soso[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                    soso[k]["PER"] = call["per"]
                    soso[k]["EPS"] = call["eps"]
                    soso[k]["PBR"] = call["pbr"]
                    soso[k]["현재가"] = f'{call["now"]:,}'
                    soso[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                  data[k][
                                                                                                      "list_shares"] else 0
                    soso[k]["PER2"] = round(call["now"] / soso[k]["EPS2"], 0) if soso[k]["EPS2"] != 0 else 0
                    soso[k]["예상주가"] = format(int(round(soso[k]["EPS2"] * soso[k]["PER"], 0)), ",") if soso[k]["EPS2"] and soso[k]["PER"] else 0
        else:
            soso[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "last_report": data[k]["last_report"], "업종": data[k]["category"],
                       "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                       "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                       "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                       "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                       "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                       "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                       "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                       "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                       "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                       "직전당기순이익": format(before_net_income, ",") if before_net_income is not None else None,
                       "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None,
                       "FCF": fcf_last_5 if fcf_last_5 is not None else None,
                       "OCF": ocf_last_5 if ocf_last_5 is not None else None,
                       "EARN": earn_last_5 if earn_last_5 is not None else None,
                       "PL": pl_last_5 if pl_last_5 is not None else None
                       }
            call = json.loads(requests.get(
                "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                    k)).content.decode("utf-8"))
            soso[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
            soso[k]["PER"] = call["per"]
            soso[k]["EPS"] = call["eps"]
            soso[k]["PBR"] = call["pbr"]
            soso[k]["현재가"] = f'{call["now"]:,}'
            soso[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                  data[k][
                                                                                                      "list_shares"] else 0
            soso[k]["PER2"] = round(call["now"] / soso[k]["EPS2"], 0) if soso[k]["EPS2"] != 0 else 0
            soso[k]["예상주가"] = format(int(round(soso[k]["EPS2"] * soso[k]["PER"], 0)), ",") if soso[k]["EPS2"] and soso[k]["PER"] else 0
            # info_lack[k] = {"corp_name": data[k]["corp_name"], "corp_code": data[k]["corp_code"]}
    logger.info("{} {} {} {}".format("*" * 100, "BEST", len(best), "*" * 100))
    for key in best.keys():
        logger.info(best[key])
        # if best[key]["EPS2"] != 0 and best[key]["EPS2"] > best[key]["EPS"] and (best[key]["EPS2"] - best[key]["EPS"])/best[key]["EPS"] * 100 >= 30:
        if "BEST" not in treasure.keys():
            treasure["BEST"] = {}
        treasure["BEST"][key] = {"사명": best[key]["corp_name"], "시가총액": best[key]["시가총액"], "업종": best[key]["업종"],
                                 "최근매출액영업이익률": best[key]["최근매출액영업이익률"], "EPS": best[key]["EPS"],
                                 "추정EPS": best[key]["EPS2"],
                                 "괴리율": round((best[key]["EPS2"] - best[key]["EPS"]) / best[key]["EPS"] * 100,
                                              2) if best[key]["EPS2"] and best[key]["EPS"] else None, "현재가": best[key]["현재가"], "예상주가": best[key]["예상주가"], "EARN": best[key]["EARN"],
                                 "FCF": best[key]["FCF"], "OCF": best[key]["OCF"], "PL": best[key]["PL"], "최종보고서": best[key]["last_report"]}
    logger.info("{} {} {} {}".format("*" * 100, "BETTER", len(better), "*" * 100))
    for key in better.keys():
        logger.info(better[key])
        # if better[key]["EPS2"] != 0 and better[key]["EPS2"] > better[key]["EPS"] and (better[key]["EPS2"] - better[key]["EPS"])/better[key]["EPS"] * 100 >= 30:
        if "BETTER" not in treasure.keys():
            treasure["BETTER"] = {}
        treasure["BETTER"][key] = {"사명": better[key]["corp_name"], "시가총액": better[key]["시가총액"],
                                   "업종": better[key]["업종"], "최근매출액영업이익률": better[key]["최근매출액영업이익률"],
                                   "EPS": better[key]["EPS"], "추정EPS": better[key]["EPS2"], "괴리율": round(
                (better[key]["EPS2"] - better[key]["EPS"]) / better[key]["EPS"] * 100, 2) if better[key]["EPS2"] and better[key]["EPS"] else None,
                                   "현재가": better[key]["현재가"], "예상주가": better[key]["예상주가"], "EARN": better[key]["EARN"],
                                   "FCF": better[key]["FCF"], "OCF": better[key]["OCF"], "PL": better[key]["PL"], "최종보고서": better[key]["last_report"]}
    logger.info("{} {} {} {}".format("*" * 100, "GOOD", len(good), "*" * 100))
    for key in good.keys():
        logger.info(good[key])
        # if good[key]["EPS2"] != 0 and good[key]["EPS2"] > good[key]["EPS"] and (good[key]["EPS2"] - good[key]["EPS"])/good[key]["EPS"] * 100 >= 30:
        if "GOOD" not in treasure.keys():
            treasure["GOOD"] = {}
        treasure["GOOD"][key] = {"사명": good[key]["corp_name"], "시가총액": good[key]["시가총액"], "업종": good[key]["업종"],
                                 "최근매출액영업이익률": good[key]["최근매출액영업이익률"], "EPS": good[key]["EPS"],
                                 "추정EPS": good[key]["EPS2"],
                                 "괴리율": round((good[key]["EPS2"] - good[key]["EPS"]) / good[key]["EPS"] * 100, 2) if good[key]["EPS2"] and good[key]["EPS"] else None,
                                 "현재가": good[key]["현재가"], "예상주가": good[key]["예상주가"], "EARN": good[key]["EARN"], "FCF": good[key]["FCF"],
                                 "OCF": good[key]["OCF"], "PL": good[key]["PL"], "최종보고서": good[key]["last_report"]}
    logger.info("{} {} {} {}".format("*" * 100, "CHECK", len(soso), "*" * 100))
    for key in soso.keys():
        logger.info(soso[key])
        # if soso[key]["EPS2"] != 0 and soso[key]["EPS2"] > soso[key]["EPS"] and (soso[key]["EPS2"] - soso[key]["EPS"])/soso[key]["EPS"] * 100 >= 30:
        if "SOSO" not in treasure.keys():
            treasure["SOSO"] = {}
        treasure["SOSO"][key] = {"사명": soso[key]["corp_name"], "시가총액": soso[key]["시가총액"], "업종": soso[key]["업종"],
                                 "최근매출액영업이익률": soso[key]["최근매출액영업이익률"], "EPS": soso[key]["EPS"],
                                 "추정EPS": soso[key]["EPS2"],
                                 "괴리율": round((soso[key]["EPS2"] - soso[key]["EPS"]) / soso[key]["EPS"] * 100,
                                              2) if soso[key]["EPS2"] and soso[key]["EPS"] else None, "현재가": soso[key]["현재가"], "예상주가": soso[key]["예상주가"], "EARN": soso[key]["EARN"],
                                 "FCF": soso[key]["FCF"], "OCF": soso[key]["OCF"], "PL": soso[key]["PL"],
                                 "최종보고서": soso[key]["last_report"]}
    # logger.info(none_list)
    return treasure


def new_find_hidden_pearl_with_dartpipe_provision(search, bgn_dt, end_dt=None):
    import sys
    import os
    import django
    from OpenDartPipe import pipe
    # sys.path.append(r'E:\Github\Waver\MainBoard')
    # sys.path.append(r'E:\Github\Waver\MainBoard\MainBoard')
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    # import detective_app.models as detective_db
    import watson.db_factory as db
    import json
    import numpy as np
    import requests
    import logging

    logfile = 'detector'
    if not os.path.exists(r'C:\Users\Kim\Documents\Projects\Waver\detective\logs'):
        os.makedirs(r'C:\Users\Kim\Documents\Projects\Waver\detective\logs')
    now = datetime.now().strftime("%Y%m%d%H%M%S")

    logger = logging.getLogger(__name__)
    formatter = logging.Formatter('[%(asctime)s][%(filename)s:%(lineno)s] >> %(message)s')

    streamHandler = logging.StreamHandler()
    fileHandler = logging.FileHandler("./logs/{}_{}.log".format(logfile, now))
    streamHandler.setFormatter(formatter)
    fileHandler.setFormatter(formatter)

    logger.addHandler(streamHandler)
    logger.addHandler(fileHandler)
    logger.setLevel(level=logging.INFO)

    # logging
    # logging.basicConfig(filename=logfile, filemode='w', level=logging.DEBUG)
    # logging.debug("Log started at %s", str(datetime.datetime.now()))

    current_pos = None
    current_key = None
    treasure = {}
    data = {}
    best = {}
    better = {}
    good = {}
    soso = {}
    info_lack = {}
    none_list = []
    # 날짜 정보 셋팅
    dateDict = new_get_dateDict()
    # 종목 정보 셋팅
    DEBUG = True
    # DEBUG = False
    # USE_JSON = False
    USE_JSON = True
    # stockInfo = detective_db.Stocks.objects.filter(category_name__contains="일반 목적", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(category_name__contains="특수", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(market_text__contains="제조", market_text_detail__contains="장비", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(code="058110", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(code="005930", listing='Y')
    dart = pipe.Pipe()
    dart.create()
    if end_dt is None:
        if search: dart.get_krx_reporting(bgn_dt)
        provision_info = dart.get_provisional_performance_reporting_corp_info(bgn_dt)
    else:
        if search: dart.get_krx_reporting(bgn_dt, end_dt)
        provision_info = dart.get_provisional_performance_reporting_corp_info(bgn_dt, end_dt)
    for stock in provision_info.keys():
        # print(stock)
        try:
            stock_obj = db.getStockInfo(stock).values().get()
            code = provision_info[stock]["corp_code"]
            name = provision_info[stock]["corp_name"]
            data[stock] = {"corp_code": code,
                           "corp_name": name,
                           "category": stock_obj["category_name"],
                           "list_shares": stock_obj["issued_shares"],
                           "PL": {"Y": {}, "Q": {}},
                           "FS": {"TotalAsset": {}, "TotalDebt": {}, "RetainedEarnings": {}},
                           "CF": {"영업활동현금흐름": {}, "유형자산취득": {}, "무형자산취득": {}, "FCF": {}},
                           "AverageRate": {"Y": {}, "Q": {}}}
            # print(dateDict["yyyy2"], dateDict)
            lists = None
            lists = dart.get_list(corp_code=code, bgn_de=dateDict["yyyy2"], pblntf_ty='A', req_type=True)["list"][:5]
            for l in lists:
                logger.info(l)
            # if stock == "064350":
            #     print()
            req_list, req_list2 = dart.get_req_lists(lists)
            result = dart.get_fnlttSinglAcnt_from_req_list(code, req_list, "ALL")
            # result = dart.get_fnlttSinglAcnt_from_req_list(code, req_list)
            current_pos = result

            # for key in result.keys():  # key = ["연결재무제표", "재무제표"]
            #     for report in result[key].keys():  # report = ["재무상태표", "손익계산서"]
            #         if report not in ["손익계산서", "포괄손익계산서"]: # ["재무상태표", "현금흐름표", "자본변동표"]:
            #             for acc in result[key][report].keys():
            #                 # acc = ["유동자산", "비유동자산", "자산총계", "유동부채", "비유동부채", "부채총계", "자본금", "이익잉여금", "자본총계"]
            #                 for category in sorted(result[key][report][acc].keys()):
            #                     # category = ["YYYY 1/4", "YYYY 2/4", "YYYY 3/4", "YYYY 4/4"]
            #                     print(key, report, acc, category, result[key][report][acc][category])
            #                     # for k in result[key][report][acc][category].keys():
            #                     #     print(key, report, acc, category, k, result[key][report][acc][category][k])
            #         else:
            #             for acc in result[key][report].keys():
            #                 # acc = ["매출액", 영업이익", "법인세차감전", "당기순이익"]
            #                 for category in result[key][report][acc].keys():
            #                     # category = ["누계", "당기"]
            #                     for k in sorted(result[key][report][acc][category].keys()):
            #                         # k = ["YYYY 1/4", "YYYY 2/4", "YYYY 3/4", "YYYY 4/4"]
            #                         print(key, report, acc, category, k, result[key][report][acc][category][k])
            d1 = None
            d2 = None
            d3 = None
            d4 = None
            d5 = None
            d6 = None
            d7 = None
            d8 = None
            d9 = None
            d10 = None
            d11 = None
            d12 = None
            d13 = None
            d14 = None
            dicTemp0 = {}
            dicTemp1 = {}
            dicTemp2 = {}
            dicTemp3 = {}
            dicTemp4 = {}
            dicTemp5 = {}
            dicTemp6 = {}
            dicTemp7 = {}
            dicTemp8 = {}
            dicTemp9 = {}
            dicTemp10 = {}
            dicTemp11 = {}
            dicTemp12 = {}
            dicTemp13 = {}
            dicTemp14 = {}
            # if stock == "006360":
            #     print()
            d1keys = ["매출", "수익(매출액)", "I.  매출액", "영업수익", "매출액", "Ⅰ. 매출액", "매출 및 지분법 손익", "매출 및 지분법손익"]
            d2keys = ["영업이익(손실)", "영업이익 (손실)", "영업이익", "영업손익", "V. 영업손익", "Ⅴ. 영업이익", "Ⅴ. 영업이익(손실)", "V. 영업이익", "영업손실"]
            d8keys = ["당기순이익(손실)", "당기순이익 (손실)", "당기순이익", "분기순이익", "반기순이익", "당기순이익(손실)", "분기순이익(손실)", "반기순이익(손실)",
                      "연결당기순이익", "연결분기순이익", "연결반기순이익", "연결당기순이익(손실)", "연결분기순이익(손실)", "연결반기순이익(손실)", "당기순손익",
                      "분기순손익",
                      "반기순손익", "지배기업 소유주지분", "지배기업의 소유주에게 귀속되는 당기순이익(손실)", "당기순손실", "분기순손실", "반기순손실",
                      "Ⅷ. 당기순이익(손실)", "지배기업 소유주 지분",
                      "Ⅷ. 당기순이익", "VIII. 당기순이익", "지배기업 소유주", "VIII. 분기순손익", "VIII. 분기순이익", "I.당기순이익", "I.반기순이익",
                      "I.분기순이익", "반기연결순이익(손실)", "지배기업의 소유주지분", "지배기업소유주지분", "지배기업의소유주지분"]
            d10keys = ["영업활동현금흐름", "영업활동 현금흐름", "영업활동으로 인한 현금흐름", "영업활동 순현금흐름유입", "영업활동으로인한현금흐름", "영업활동으로 인한 순현금흐름",
                       "Ⅰ. 영업활동으로 인한 현금흐름", "Ⅰ. 영업활동으로 인한 현금흐름", "영업활동순현금흐름 합계", "영업활동순현금흐름", "I. 영업활동현금흐름"]
            d11keys = ["유형자산의 취득", "유형자산 취득", "유형자산의취득"]
            d12keys = ["무형자산의 취득", "무형자산 취득", "무형자산의취득", "무형자산의 증가"]
            d13keys = ["토지의 취득", "건물의 취득", "구축물의 취득", "기계장치의 취득", "차량운반구의 취득", "공구와기구의취득", "공구와기구의 취득", "비품의 취득",
                       "기타유형자산의 취득", "건설중인자산의 취득", "투자부동산의 취득", "집기비품의 취득", "시험기기의 취득"]
            d14keys = ["컴퓨터소프트웨어의 취득", "산업재산권의 취득", "소프트웨어의 취득", "기타무형자산의 취득"]
            # if stock == "006360":
            #     print()
            if result is not {} and "연결재무제표" in result.keys():
                logger.info("연결재무제표 start")
                if "포괄손익계산서" in result["연결재무제표"].keys():
                    logger.info("연결재무제표 포괄손익계산서 start")
                    tmp_result1 = {key: result["연결재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                   result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d1keys}}
                    tmp_result2 = {key: result["연결재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                   result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d2keys}}
                    tmp_result3 = {key: result["연결재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                   result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d1keys}}
                    tmp_result4 = {key: result["연결재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                   result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d2keys}}
                    tmp_result8 = {key: result["연결재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                   result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d8keys}}
                    tmp_result9 = {key: result["연결재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                   result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d8keys}}
                    if tmp_result1:
                        for key in tmp_result1.keys():
                            if d1 is None:
                                d1 = tmp_result1[key]
                            else:
                                d1.update(tmp_result1[key])
                    if tmp_result2:
                        for key in tmp_result2.keys():
                            if d2 is None:
                                d2 = tmp_result2[key]
                            else:
                                d2.update(tmp_result2[key])
                    if tmp_result3:
                        for key in tmp_result3.keys():
                            if d3 is None:
                                d3 = tmp_result3[key]
                            else:
                                d3.update(tmp_result3[key])
                    if tmp_result4:
                        for key in tmp_result4.keys():
                            if d4 is None:
                                d4 = tmp_result4[key]
                            else:
                                d4.update(tmp_result4[key])
                    if tmp_result8:
                        for key in tmp_result8.keys():
                            if d8 is None:
                                d8 = tmp_result8[key]
                            else:
                                d8.update(tmp_result8[key])
                    if tmp_result9:
                        for key in tmp_result9.keys():
                            if d9 is None:
                                d9 = tmp_result9[key]
                            else:
                                d9.update(tmp_result9[key])
                if "손익계산서" in result["연결재무제표"].keys():
                    logger.info("연결재무제표 손익계산서 start")
                    tmp_result1 = {key: result["연결재무제표"]["손익계산서"][key]["누계"] for key in
                                   result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d1keys}}
                    tmp_result2 = {key: result["연결재무제표"]["손익계산서"][key]["누계"] for key in
                                   result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d2keys}}
                    tmp_result3 = {key: result["연결재무제표"]["손익계산서"][key]["당기"] for key in
                                   result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d1keys}}
                    tmp_result4 = {key: result["연결재무제표"]["손익계산서"][key]["당기"] for key in
                                   result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d2keys}}
                    tmp_result8 = {key: result["연결재무제표"]["손익계산서"][key]["누계"] for key in
                                   result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d8keys}}
                    tmp_result9 = {key: result["연결재무제표"]["손익계산서"][key]["당기"] for key in
                                   result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d8keys}}
                    if tmp_result1:
                        for key in tmp_result1.keys():
                            if d1 is None:
                                d1 = tmp_result1[key]
                            else:
                                d1.update(tmp_result1[key])
                    if tmp_result2:
                        for key in tmp_result2.keys():
                            if d2 is None:
                                d2 = tmp_result2[key]
                            else:
                                d2.update(tmp_result2[key])
                    if tmp_result3:
                        for key in tmp_result3.keys():
                            if d3 is None:
                                d3 = tmp_result3[key]
                            else:
                                d3.update(tmp_result3[key])
                    if tmp_result4:
                        for key in tmp_result4.keys():
                            if d4 is None:
                                d4 = tmp_result4[key]
                            else:
                                d4.update(tmp_result4[key])
                    if tmp_result8:
                        for key in tmp_result8.keys():
                            if d8 is None:
                                d8 = tmp_result8[key]
                            else:
                                d8.update(tmp_result8[key])
                    if tmp_result9:
                        for key in tmp_result9.keys():
                            if d9 is None:
                                d9 = tmp_result9[key]
                            else:
                                d9.update(tmp_result9[key])
                if "현금흐름표" in result["연결재무제표"].keys():
                    logger.info("연결재무제표 현금흐름표 start")
                    tmp_result10 = {key: result["연결재무제표"]["현금흐름표"][key] for key in
                                    result["연결재무제표"]["현금흐름표"].keys() & {keys for keys in d10keys}}
                    tmp_result11 = {key: result["연결재무제표"]["현금흐름표"][key] for key in
                                    result["연결재무제표"]["현금흐름표"].keys() & {keys for keys in d11keys}}
                    tmp_result12 = {key: result["연결재무제표"]["현금흐름표"][key] for key in
                                    result["연결재무제표"]["현금흐름표"].keys() & {keys for keys in d12keys}}
                    tmp_result13 = {key: result["연결재무제표"]["현금흐름표"][key] for key in
                                    result["연결재무제표"]["현금흐름표"].keys() & {keys for keys in d13keys}}
                    tmp_result14 = {key: result["연결재무제표"]["현금흐름표"][key] for key in
                                    result["연결재무제표"]["현금흐름표"].keys() & {keys for keys in d14keys}}
                    if tmp_result10:
                        for key in tmp_result10.keys():
                            if d10 is None:
                                d10 = tmp_result10[key]
                            else:
                                d10.update(tmp_result10[key])
                    if tmp_result11:
                        for key in tmp_result11.keys():
                            if d11 is None:
                                d11 = tmp_result11[key]
                            else:
                                d11.update(tmp_result11[key])
                    if tmp_result12:
                        for key in tmp_result12.keys():
                            if d12 is None:
                                d12 = tmp_result12[key]
                            else:
                                d12.update(tmp_result12[key])
                    if tmp_result13:
                        d13 = dictionary_add(tmp_result13)
                        # for key in tmp_result13.keys():
                        #     if d13 is None:
                        #         d13 = tmp_result13[key]
                        #     else:
                        #         d13.update(tmp_result13[key])
                    if tmp_result14:
                        d14 = dictionary_add(tmp_result14)
                        # for key in tmp_result14.keys():
                        #     if d14 is None:
                        #         d14 = tmp_result14[key]
                        #     else:
                        #         d14.update(tmp_result14[key])
                if d11 is None: d11 = d13
                if d12 is None: d12 = d14
                d5 = result["연결재무제표"]["재무상태표"]["자산총계"] if "자산총계" in result["연결재무제표"]["재무상태표"].keys() else None
                d6 = result["연결재무제표"]["재무상태표"]["부채총계"] if "부채총계" in result["연결재무제표"]["재무상태표"].keys() else None
                d7 = result["연결재무제표"]["재무상태표"]["이익잉여금"] if "이익잉여금" in result["연결재무제표"]["재무상태표"].keys() else None
                if d5 is None:
                    if "자  산  총  계" in result["연결재무제표"]["재무상태표"].keys():
                        d5 = result["연결재무제표"]["재무상태표"]["자  산  총  계"]
                else:
                    if "자  산  총  계" in result["연결재무제표"]["재무상태표"].keys():
                        d5.update(result["연결재무제표"]["재무상태표"]["자  산  총  계"])
                if d5 is None:
                    if "자산 총계" in result["연결재무제표"]["재무상태표"].keys():
                        d5 = result["연결재무제표"]["재무상태표"]["자산 총계"]
                else:
                    if "자산 총계" in result["연결재무제표"]["재무상태표"].keys():
                        d5.update(result["연결재무제표"]["재무상태표"]["자산 총계"])
                if d6 is None:
                    if "부  채  총  계" in result["연결재무제표"]["재무상태표"].keys():
                        d6 = result["연결재무제표"]["재무상태표"]["부  채  총  계"]
                else:
                    if "부  채  총  계" in result["연결재무제표"]["재무상태표"].keys():
                        d6.update(result["연결재무제표"]["재무상태표"]["부  채  총  계"])
                if d6 is None:
                    if "부채 총계" in result["연결재무제표"]["재무상태표"].keys():
                        d6 = result["연결재무제표"]["재무상태표"]["부채 총계"]
                else:
                    if "부채 총계" in result["연결재무제표"]["재무상태표"].keys():
                        d6.update(result["연결재무제표"]["재무상태표"]["부채 총계"])
                if d7 is None:
                    if "이익잉여금(결손금)" in result["연결재무제표"]["재무상태표"].keys():
                        d7 = result["연결재무제표"]["재무상태표"]["이익잉여금(결손금)"]
                else:
                    if "이익잉여금(결손금)" in result["연결재무제표"]["재무상태표"].keys():
                        d7.update(result["연결재무제표"]["재무상태표"]["이익잉여금(결손금)"])
                if d7 is None:
                    if "결손금" in result["연결재무제표"]["재무상태표"].keys():
                        d7 = result["연결재무제표"]["재무상태표"]["결손금"]
                else:
                    if "결손금" in result["연결재무제표"]["재무상태표"].keys():
                        d7.update(result["연결재무제표"]["재무상태표"]["결손금"])
            else:
                logger.info("재무제표 start")
                if "포괄손익계산서" in result["재무제표"].keys():
                    logger.info("재무제표 포괄손익계산서 start")
                    tmp_result1 = {key: result["재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                   result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d1keys}}
                    tmp_result2 = {key: result["재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                   result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d2keys}}
                    tmp_result3 = {key: result["재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                   result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d1keys}}
                    tmp_result4 = {key: result["재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                   result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d2keys}}
                    tmp_result8 = {key: result["재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                   result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d8keys}}
                    tmp_result9 = {key: result["재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                   result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d8keys}}
                    if tmp_result1:
                        for key in tmp_result1.keys():
                            if d1 is None:
                                d1 = tmp_result1[key]
                            else:
                                d1.update(tmp_result1[key])
                    if tmp_result2:
                        for key in tmp_result2.keys():
                            if d2 is None:
                                d2 = tmp_result2[key]
                            else:
                                d2.update(tmp_result2[key])
                    if tmp_result3:
                        for key in tmp_result3.keys():
                            if d3 is None:
                                d3 = tmp_result3[key]
                            else:
                                d3.update(tmp_result3[key])
                    if tmp_result4:
                        for key in tmp_result4.keys():
                            if d4 is None:
                                d4 = tmp_result4[key]
                            else:
                                d4.update(tmp_result4[key])
                    if tmp_result8:
                        for key in tmp_result8.keys():
                            if d8 is None:
                                d8 = tmp_result8[key]
                            else:
                                d8.update(tmp_result8[key])
                    if tmp_result9:
                        for key in tmp_result9.keys():
                            if d9 is None:
                                d9 = tmp_result9[key]
                            else:
                                d9.update(tmp_result9[key])
                if "손익계산서" in result["재무제표"].keys():
                    logger.info("재무제표 손익계산서 매출 start")
                    tmp_result1 = {key: result["재무제표"]["손익계산서"][key]["누계"] for key in
                                   result["재무제표"]["손익계산서"].keys() & {keys for keys in d1keys}}
                    tmp_result2 = {key: result["재무제표"]["손익계산서"][key]["누계"] for key in
                                   result["재무제표"]["손익계산서"].keys() & {keys for keys in d2keys}}
                    tmp_result3 = {key: result["재무제표"]["손익계산서"][key]["당기"] for key in
                                   result["재무제표"]["손익계산서"].keys() & {keys for keys in d1keys}}
                    tmp_result4 = {key: result["재무제표"]["손익계산서"][key]["당기"] for key in
                                   result["재무제표"]["손익계산서"].keys() & {keys for keys in d2keys}}
                    tmp_result8 = {key: result["재무제표"]["손익계산서"][key]["누계"] for key in
                                   result["재무제표"]["손익계산서"].keys() & {keys for keys in d8keys}}
                    tmp_result9 = {key: result["재무제표"]["손익계산서"][key]["당기"] for key in
                                   result["재무제표"]["손익계산서"].keys() & {keys for keys in d8keys}}
                    if tmp_result1:
                        for key in tmp_result1.keys():
                            if d1 is None:
                                d1 = tmp_result1[key]
                            else:
                                d1.update(tmp_result1[key])
                    if tmp_result2:
                        for key in tmp_result2.keys():
                            if d2 is None:
                                d2 = tmp_result2[key]
                            else:
                                d2.update(tmp_result2[key])
                    if tmp_result3:
                        for key in tmp_result3.keys():
                            if d3 is None:
                                d3 = tmp_result3[key]
                            else:
                                d3.update(tmp_result3[key])
                    if tmp_result4:
                        for key in tmp_result4.keys():
                            if d4 is None:
                                d4 = tmp_result4[key]
                            else:
                                d4.update(tmp_result4[key])
                    if tmp_result8:
                        for key in tmp_result8.keys():
                            if d8 is None:
                                d8 = tmp_result8[key]
                            else:
                                d8.update(tmp_result8[key])
                    if tmp_result9:
                        for key in tmp_result9.keys():
                            if d9 is None:
                                d9 = tmp_result9[key]
                            else:
                                d9.update(tmp_result9[key])
                if "현금흐름표" in result["재무제표"].keys():
                    logger.info("재무제표 현금흐름표 start")
                    tmp_result10 = {key: result["재무제표"]["현금흐름표"][key] for key in
                                    result["재무제표"]["현금흐름표"].keys() & {keys for keys in d10keys}}
                    tmp_result11 = {key: result["재무제표"]["현금흐름표"][key] for key in
                                    result["재무제표"]["현금흐름표"].keys() & {keys for keys in d11keys}}
                    tmp_result12 = {key: result["재무제표"]["현금흐름표"][key] for key in
                                    result["재무제표"]["현금흐름표"].keys() & {keys for keys in d12keys}}
                    tmp_result13 = {key: result["재무제표"]["현금흐름표"][key] for key in
                                    result["재무제표"]["현금흐름표"].keys() & {keys for keys in d13keys}}
                    tmp_result14 = {key: result["재무제표"]["현금흐름표"][key] for key in
                                    result["재무제표"]["현금흐름표"].keys() & {keys for keys in d14keys}}
                    if tmp_result10:
                        for key in tmp_result10.keys():
                            if d10 is None:
                                d10 = tmp_result10[key]
                            else:
                                d10.update(tmp_result10[key])
                    if tmp_result11:
                        for key in tmp_result11.keys():
                            if d11 is None:
                                d11 = tmp_result11[key]
                            else:
                                d11.update(tmp_result11[key])
                    if tmp_result12:
                        for key in tmp_result12.keys():
                            if d12 is None:
                                d12 = tmp_result12[key]
                            else:
                                d12.update(tmp_result12[key])
                    if tmp_result13:
                        d13 = dictionary_add(tmp_result13)
                        # for key in tmp_result13.keys():
                        #     if d13 is None:
                        #         d13 = tmp_result13[key]
                        #     else:
                        #         d13.update(tmp_result13[key])
                    if tmp_result14:
                        d14 = dictionary_add(tmp_result14)
                        # for key in tmp_result14.keys():
                        #     if d14 is None:
                        #         d14 = tmp_result14[key]
                        #     else:
                        #         d14.update(tmp_result14[key])
                if d11 is None: d11 = d13
                if d12 is None: d12 = d14
                d5 = result["재무제표"]["재무상태표"]["자산총계"] if "자산총계" in result["재무제표"]["재무상태표"].keys() else None
                d6 = result["재무제표"]["재무상태표"]["부채총계"] if "부채총계" in result["재무제표"]["재무상태표"].keys() else None
                d7 = result["재무제표"]["재무상태표"]["이익잉여금"] if "이익잉여금" in result["재무제표"]["재무상태표"].keys() else None
                if d5 is None:
                    if "자  산  총  계" in result["재무제표"]["재무상태표"].keys():
                        d5 = result["재무제표"]["재무상태표"]["자  산  총  계"]
                else:
                    if "자  산  총  계" in result["재무제표"]["재무상태표"].keys():
                        d5.update(result["재무제표"]["재무상태표"]["자  산  총  계"])
                if d5 is None:
                    if "자산 총계" in result["재무제표"]["재무상태표"].keys():
                        d5 = result["재무제표"]["재무상태표"]["자산 총계"]
                else:
                    if "자산 총계" in result["재무제표"]["재무상태표"].keys():
                        d5.update(result["재무제표"]["재무상태표"]["자산 총계"])
                if d6 is None:
                    if "부  채  총  계" in result["재무제표"]["재무상태표"].keys():
                        d6 = result["재무제표"]["재무상태표"]["부  채  총  계"]
                else:
                    if "부  채  총  계" in result["재무제표"]["재무상태표"].keys():
                        d6.update(result["재무제표"]["재무상태표"]["부  채  총  계"])
                if d6 is None:
                    if "부채 총계" in result["재무제표"]["재무상태표"].keys():
                        d6 = result["재무제표"]["재무상태표"]["부채 총계"]
                else:
                    if "부채 총계" in result["재무제표"]["재무상태표"].keys():
                        d6.update(result["재무제표"]["재무상태표"]["부채 총계"])
                if d7 is None:
                    if "이익잉여금(결손금)" in result["재무제표"]["재무상태표"].keys():
                        d7 = result["재무제표"]["재무상태표"]["이익잉여금(결손금)"]
                else:
                    if "이익잉여금(결손금)" in result["재무제표"]["재무상태표"].keys():
                        d7.update(result["재무제표"]["재무상태표"]["이익잉여금(결손금)"])
                if d7 is None:
                    if "결손금" in result["재무제표"]["재무상태표"].keys():
                        d7 = result["재무제표"]["재무상태표"]["결손금"]
                else:
                    if "결손금" in result["재무제표"]["재무상태표"].keys():
                        d7.update(result["재무제표"]["재무상태표"]["결손금"])
            logger.info("매출액 누계 : {}".format(d1))  # 매출액 누계
            logger.info("영업이익 누계 : {}".format(d2))  # 영업이익 누계
            logger.info("매출액 누계 : {}".format(d3))  # 매출액 당기
            logger.info("영업이익 누계 : {}".format(d4))  # 영업이익 당기
            logger.info("자산총계 : {}".format(d5))  # 자산총계
            logger.info("부채총계 : {}".format(d6))  # 부채총계
            logger.info("이익잉여금 : {}".format(d7))  # 이익잉여금
            logger.info("당기순이익 누계 : {}".format(d8))  # 당기순이익 누계
            logger.info("당기순이익 : {}".format(d9))  # 당기순이익
            logger.info("영업활동현금흐름 : {}".format(d10))  # 영업활동현금흐름
            logger.info("유형자산의 취득 : {}".format(d11))  # 유형자산의 취득
            logger.info("무형자산의 취득 : {}".format(d12))  # 무형자산의 취득
            logger.info("유형자산의 취득(유형자산의 취득으로 표시되지 않는) : {}".format(d13))  # 유형자산의 취득(유형자산의 취득으로 표시되지 않는)
            logger.info("무형자산의 취득(무형자산의 취득으로 표시되지 않는) : {}".format(d14))  # 무형자산의 취득(무형자산의 취득으로 표시되지 않는)
            logger.info(provision_info[stock])
            if d10 is None:
                none_list.append("[{}][{}]-영업활동현금흐름".format(code, name))
            if d11 is None:
                none_list.append("[{}][{}]-유형자산의 취득".format(code, name))
            if d12 is None:
                none_list.append("[{}][{}]-무형자산의 취득".format(code, name))

            for key1 in d1.keys():
                current_key = key1
                # if key1 == "2019 4/4":
                #     print(key1)
                # if "1/4" in key1:
                #     print(key1)
                if "Rate" in key1: continue
                if "4/4" in key1:
                    data[stock]["PL"]["Y"]["매출액영업이익률"] = dict(sorted({
                                                                         k: round(float(
                                                                             d2[key1][k].replace(",", "")) / float(
                                                                             d1[key1][k].replace(",", "")) * 100,
                                                                                  2) if float(
                                                                             d1[key1][k].replace(",",
                                                                                                 "")) != 0.0 else 0
                                                                         for k in d1[key1]}.items()))
                    if "매출액" in provision_info[stock]["PL"]["Y"].keys() and \
                            "영업이익" in provision_info[stock]["PL"]["Y"].keys() and \
                            provision_info[stock]["PL"]["Y"]["매출액"] != 0:
                        data[stock]["PL"]["Y"]["매출액영업이익률"]["최근"] = round(
                            provision_info[stock]["PL"]["Y"]["영업이익"] / provision_info[stock]["PL"]["Y"]["매출액"] * 100, 2)
                    else:
                        data[stock]["PL"]["Y"]["매출액영업이익률"]["최근"] = 0
                    data[stock]["PL"]["Y"]["매출액"] = dict(
                        sorted({k: float(d1[key1][k].replace(",", "")) for k in
                                d1[key1]}.items()))
                    data[stock]["PL"]["Y"]["매출액"]["최근"] = provision_info[stock]["PL"]["Y"]["매출액"] if "매출액" in \
                                                                                                     provision_info[
                                                                                                         stock]["PL"][
                                                                                                         "Y"].keys() else 0
                    # data[stock]["PL"]["Y"]["매출액"]["최근"] = provision_info[stock]["PL"]["Y"]["매출액"]
                    data[stock]["PL"]["Y"]["영업이익"] = dict(
                        sorted({k: float(d2[key1][k].replace(",", "")) for k in
                                d2[key1]}.items()))
                    data[stock]["PL"]["Y"]["영업이익"]["최근"] = provision_info[stock]["PL"]["Y"]["영업이익"] if "영업이익" in \
                                                                                                       provision_info[
                                                                                                           stock][
                                                                                                           "PL"][
                                                                                                           "Y"].keys() else 0
                    data[stock]["PL"]["Y"]["당기순이익"] = dict(
                        sorted({k: float(d8[key1][k].replace(",", "")) for k in
                                d8[key1]}.items()))
                    data[stock]["PL"]["Y"]["당기순이익"]["최근"] = provision_info[stock]["PL"]["Y"]["당기순이익"] if "당기순이익" in \
                                                                                                         provision_info[
                                                                                                             stock][
                                                                                                             "PL"][
                                                                                                             "Y"].keys() else 0
                    # data[stock]["PL"]["Y"]["영업이익"]["최근"] = provision_info[stock]["PL"]["Y"]["영업이익"]
                    for k in sorted(d1[key1]):
                        dicTemp1[k] = float(d1[key1][k].replace(",", ""))
                    dicTemp1["최근"] = provision_info[stock]["PL"]["Y"]["매출액"] if "매출액" in provision_info[stock]["PL"][
                        "Y"].keys() else 0
                    for k in sorted(d2[key1]):
                        dicTemp2[k] = float(d2[key1][k].replace(",", ""))
                    dicTemp2["최근"] = provision_info[stock]["PL"]["Y"]["영업이익"] if "영업이익" in provision_info[stock]["PL"][
                        "Y"].keys() else 0
                    for k in sorted(d8[key1]):
                        dicTemp8[k] = float(d8[key1][k].replace(",", ""))
                    dicTemp8["최근"] = provision_info[stock]["PL"]["Y"]["당기순이익"] if "당기순이익" in \
                                                                                  provision_info[stock]["PL"][
                                                                                      "Y"].keys() else 0
                else:
                    for k in sorted(d1[key1]):
                        dicTemp0[k] = round(
                            float(d2[key1][k].replace(",", "")) / float(d1[key1][k].replace(",", "")) * 100,
                            2) if float(d1[key1][k].replace(",", "")) != 0.0 else 0
                    dicTemp0["최근"] = round(
                        provision_info[stock]["PL"]["Q"]["영업이익"] / provision_info[stock]["PL"]["Q"]["매출액"] * 100, 2) if \
                        provision_info[stock]["PL"]["Q"]["매출액"] != 0 else 0
                    for k in sorted(d1[key1]):
                        dicTemp1[k] = float(d1[key1][k].replace(",", ""))
                        # data[stock]["PL"]["Q"]["누계매출액"][k] = float(d1[key1][k].replace(",", ""))
                    for k in sorted(d2[key1]):
                        dicTemp2[k] = float(d2[key1][k].replace(",", ""))
                        # data[stock]["PL"]["Q"]["누계영업이익"][k] = float(d2[key1][k].replace(",", ""))
                    for k in sorted(d3[key1]):
                        dicTemp3[k] = float(d3[key1][k].replace(",", ""))
                        # data[stock]["PL"]["Q"]["당기매출액"][k] = float(d3[key1][k].replace(",", ""))
                    for k in sorted(d4[key1]):
                        dicTemp4[k] = float(d4[key1][k].replace(",", ""))
                        # data[stock]["PL"]["Q"]["당기영업이익"][k] = float(d4[key1][k].replace(",", ""))
                    for k in sorted(d8[key1]):
                        dicTemp8[k] = float(d8[key1][k].replace(",", ""))
                        # data[stock]["PL"]["Q"]["당기매출액"][k] = float(d3[key1][k].replace(",", ""))
                    for k in sorted(d9[key1]):
                        dicTemp9[k] = float(d9[key1][k].replace(",", ""))
                        # data[stock]["PL"]["Q"]["당기영업이익"][k] = float(d4[key1][k].replace(",", ""))
                for key2 in d10.keys():
                    current_key = key2
                    if "Rate" in key2: continue
                    for key3 in d10[key2].keys():
                        yhasset = int(d11[key2][key3]) if key2 in d11.keys() and key3 in d11[key2].keys() else 0
                        mhasset = int(d12[key2][key3]) if key2 in d12.keys() and key3 in d12[key2].keys() else 0
                        data[stock]["CF"]["FCF"][key3] = int(d10[key2][key3]) - (yhasset + mhasset)
            # dicTemp1["최근"] = provision_info[stock]["PL"]["Y"]["매출액"]
            # dicTemp2["최근"] = provision_info[stock]["PL"]["Y"]["영업이익"]
            dicTemp3["최근"] = provision_info[stock]["PL"]["Q"]["매출액"] if "매출액" in provision_info[stock]["PL"][
                "Q"].keys() else 0
            dicTemp4["최근"] = provision_info[stock]["PL"]["Q"]["영업이익"] if "영업이익" in provision_info[stock]["PL"][
                "Q"].keys() else 0
            # dicTemp8["최근"] = provision_info[stock]["PL"]["Y"]["당기순이익"]
            dicTemp9["최근"] = provision_info[stock]["PL"]["Q"]["당기순이익"] if "당기순이익" in provision_info[stock]["PL"][
                "Q"].keys() else 0
            data[stock]["PL"]["Q"]["매출액영업이익률"] = dict(sorted(dicTemp0.items()))
            data[stock]["PL"]["Q"]["누계매출액추이"] = dict(sorted(dicTemp1.items()))
            data[stock]["PL"]["Q"]["누계영업이익추이"] = dict(sorted(dicTemp2.items()))
            data[stock]["PL"]["Q"]["당기매출액"] = dict(sorted(dicTemp3.items()))
            data[stock]["PL"]["Q"]["당기영업이익"] = dict(sorted(dicTemp4.items()))
            data[stock]["PL"]["Q"]["누계당기순이익추이"] = dict(sorted(dicTemp8.items()))
            data[stock]["PL"]["Q"]["당기순이익"] = dict(sorted(dicTemp9.items()))
            # print("MakeAvg1?")
            # print(data)
            data[stock]["AverageRate"]["Y"]["매출액영업이익률"] = round(sum(
                data[stock]["PL"]["Y"]["매출액영업이익률"].values()) / float(
                len(data[stock]["PL"]["Y"]["매출액영업이익률"])), 2) if "매출액영업이익률" in data[stock]["PL"][
                "Y"].keys() else None
            # print("MakeAvg2?")
            data[stock]["AverageRate"]["Y"]["매출액"] = round(sum(
                data[stock]["PL"]["Y"]["매출액"].values()) / float(
                len(data[stock]["PL"]["Y"]["매출액"])), 0) if "매출액" in data[stock]["PL"]["Y"].keys() and \
                                                           len(data[stock]["PL"]["Y"]["매출액"]) != 0 else None
            # print("MakeAvg3?")
            data[stock]["AverageRate"]["Y"]["영업이익"] = round(sum(
                data[stock]["PL"]["Y"]["영업이익"].values()) / float(
                len(data[stock]["PL"]["Y"]["영업이익"])), 0) if "영업이익" in data[stock]["PL"]["Y"].keys() and \
                                                            len(data[stock]["PL"]["Y"]["영업이익"]) != 0 else None
            data[stock]["AverageRate"]["Y"]["당기순이익"] = round(sum(
                data[stock]["PL"]["Y"]["당기순이익"].values()) / float(
                len(data[stock]["PL"]["Y"]["당기순이익"])), 0) if "당기순이익" in data[stock]["PL"]["Y"].keys() and \
                                                             len(data[stock]["PL"]["Y"]["당기순이익"]) != 0 else None
            # print("MakeAvg4?")
            data[stock]["AverageRate"]["Q"]["매출액영업이익률"] = round(sum(
                data[stock]["PL"]["Q"]["매출액영업이익률"].values()) / float(
                len(data[stock]["PL"]["Q"]["매출액영업이익률"])), 2) if "매출액영업이익률" in data[stock]["PL"]["Q"].keys() and \
                                                                len(data[stock]["PL"]["Q"]["매출액영업이익률"]) != 0 else None
            # print("MakeAvg5?")
            data[stock]["AverageRate"]["Q"]["매출액"] = round(sum(
                data[stock]["PL"]["Q"]["당기매출액"].values()) / float(
                len(data[stock]["PL"]["Q"]["당기매출액"])), 0) if "당기매출액" in data[stock]["PL"]["Q"].keys() and \
                                                             len(data[stock]["PL"]["Q"]["당기매출액"]) != 0 else None
            # print("MakeAvg6?")
            data[stock]["AverageRate"]["Q"]["영업이익"] = round(sum(
                data[stock]["PL"]["Q"]["당기영업이익"].values()) / float(
                len(data[stock]["PL"]["Q"]["당기영업이익"])), 0) if "당기영업이익" in data[stock]["PL"]["Q"].keys() and \
                                                              len(data[stock]["PL"]["Q"]["당기영업이익"]) != 0 else None
            data[stock]["AverageRate"]["Q"]["당기순이익"] = round(sum(
                data[stock]["PL"]["Q"]["당기순이익"].values()) / float(
                len(data[stock]["PL"]["Q"]["당기순이익"])), 0) if "당기순이익" in data[stock]["PL"]["Q"].keys() and \
                                                             len(data[stock]["PL"]["Q"]["당기순이익"]) != 0 else None
            # print("MakeAvg7?")
            # 손익계산서 분석 끝
            for key1 in d1.keys():
                if "Rate" in key1: continue
                if d5 is not None and key1 in d5.keys():
                    for k in sorted(d5[key1]):
                        dicTemp5[k] = float(d5[key1][k].replace(",", "")) if d5 is not None else 0
                if d6 is not None and key1 in d6.keys():
                    for k in sorted(d6[key1]):
                        dicTemp6[k] = float(d6[key1][k].replace(",", "")) if d6 is not None else 0
                if d7 is not None and key1 in d7.keys():
                    for k in sorted(d7[key1]):
                        dicTemp7[k] = float(d7[key1][k].replace(",", "")) if d7 is not None else 0
                if d10 is not None and key1 in d10.keys():
                    for k in sorted(d10[key1]):
                        dicTemp10[k] = float(d10[key1][k].replace(",", "")) if d10 is not None else 0
                if d11 is not None and key1 in d11.keys():
                    for k in sorted(d11[key1]):
                        dicTemp11[k] = float(d11[key1][k]) if d11 is not None else 0
                if d12 is not None and key1 in d12.keys():
                    for k in sorted(d12[key1]):
                        dicTemp12[k] = float(d12[key1][k]) if d12 is not None else 0
                data[stock]["FS"]["TotalAsset"] = dict(sorted(dicTemp5.items()))
                data[stock]["FS"]["TotalDebt"] = dict(sorted(dicTemp6.items()))
                data[stock]["FS"]["RetainedEarnings"] = dict(sorted(dicTemp7.items()))
                data[stock]["CF"]["영업활동현금흐름"] = dict(sorted(dicTemp10.items()))
                data[stock]["CF"]["유형자산취득"] = dict(sorted(dicTemp11.items()))
                data[stock]["CF"]["무형자산취득"] = dict(sorted(dicTemp12.items()))
                data[stock]["CF"]["FCF"] = dict(sorted(data[stock]["CF"]["FCF"].items()))
        except Exception as e:
            logger.error(e)
            # logger.error(current_pos)
            logger.error(current_key)
            for key in current_pos.keys():  # key = ["연결재무제표", "재무제표"]
                for report in current_pos[key].keys():  # report = ["재무상태표", "손익계산서"]
                    if report not in ["손익계산서", "포괄손익계산서"]:  # ["재무상태표", "현금흐름표", "자본변동표"]:
                        for acc in current_pos[key][report].keys():
                            # acc = ["유동자산", "비유동자산", "자산총계", "유동부채", "비유동부채", "부채총계", "자본금", "이익잉여금", "자본총계"]
                            for category in sorted(current_pos[key][report][acc].keys()):
                                # category = ["YYYY 1/4", "YYYY 2/4", "YYYY 3/4", "YYYY 4/4"]
                                logger.error("{}\t{}\t{}\t{}\t{}".format(key, report, acc, category,
                                                                         current_pos[key][report][acc][category]))
                                # for k in result[key][report][acc][category].keys():
                                #     print(key, report, acc, category, k, current_pos[key][report][acc][category][k])
                    else:
                        for acc in current_pos[key][report].keys():
                            # acc = ["매출액", 영업이익", "법인세차감전", "당기순이익"]
                            for category in current_pos[key][report][acc].keys():
                                # category = ["누계", "당기"]
                                for k in sorted(current_pos[key][report][acc][category].keys()):
                                    # k = ["YYYY 1/4", "YYYY 2/4", "YYYY 3/4", "YYYY 4/4"]
                                    logger.error("{}\t{}\t{}\t{}\t{}\t{}".format(key, report, acc, category, k,
                                                                                 current_pos[key][report][acc][
                                                                                     category][k]))
    logger.info(data)

    for k in data.keys():
        avg_sales_op_profit_rate = None
        avg_sales = None
        avg_op_profit = None
        avg_net_income = None
        last_sales_op_profit_rate = None
        last_sales = None
        last_op_profit = None
        last_net_income = None
        before_sales = None
        before_op_profit = None
        before_net_income = None

        logger.info("{} {} {}".format(k, data[k]["corp_name"], "*" * 100))
        for key in data[k]["PL"]["Y"].keys():
            logger.info("{} {} {}".format("연간", key, data[k]["PL"]["Y"][key]))
        logger.info("{} {}".format("연간", data[k]["AverageRate"]["Y"]))
        for key in data[k]["PL"]["Q"].keys():
            logger.info("{} {} {}".format("당기", key, data[k]["PL"]["Q"][key]))
        logger.info("{} {}".format("당기", data[k]["AverageRate"]["Q"]))
        logger.info("{} {}".format("재무상태표-자산총계", data[k]["FS"]["TotalAsset"]))
        logger.info("{} {}".format("재무상태표-부채총계", data[k]["FS"]["TotalDebt"]))
        logger.info("{} {}".format("재무상태표-이익잉여금", data[k]["FS"]["RetainedEarnings"]))
        logger.info("{} {}".format("CF-OCF", data[k]["CF"]["영업활동현금흐름"]))
        logger.info("{} {}".format("CF-유형자산취득", data[k]["CF"]["유형자산취득"]))
        logger.info("{} {}".format("CF-무형자산취득", data[k]["CF"]["무형자산취득"]))
        logger.info("{} {}".format("CF-FCF", data[k]["CF"]["FCF"]))
        # print("here1?")
        if "매출액영업이익률" in data[k]["AverageRate"]["Y"].keys() \
                and "매출액" in data[k]["AverageRate"]["Y"].keys() \
                and "영업이익" in data[k]["AverageRate"]["Y"].keys() \
                and "당기순이익" in data[k]["AverageRate"]["Y"].keys():
            # print("here2?")
            avg_sales_op_profit_rate = data[k]["AverageRate"]["Y"]["매출액영업이익률"]
            avg_sales = data[k]["AverageRate"]["Y"]["매출액"]
            avg_op_profit = data[k]["AverageRate"]["Y"]["영업이익"]
            avg_net_income = data[k]["AverageRate"]["Y"]["당기순이익"]

            if "매출액영업이익률" in data[k]["PL"]["Q"].keys():
                # print("here3?")
                last_sales_op_profit_rate = data[k]["PL"]["Q"]["매출액영업이익률"].popitem()[1] if len(
                    data[k]["PL"]["Q"]["매출액영업이익률"]) > 0 else None
                last_sales = data[k]["PL"]["Q"]["누계매출액추이"].popitem()[1] if len(
                    data[k]["PL"]["Q"]["누계매출액추이"]) > 0 else None
                if "매출액" in data[k]["PL"]["Y"].keys():
                    data[k]["PL"]["Y"]["매출액"].popitem() if len(data[k]["PL"]["Y"]["매출액"]) > 0 else None
                    before_sales = data[k]["PL"]["Y"]["매출액"].popitem()[1] if len(
                        data[k]["PL"]["Y"]["매출액"]) > 0 else None
                last_op_profit = data[k]["PL"]["Q"]["누계영업이익추이"].popitem()[1] if len(
                    data[k]["PL"]["Q"]["누계영업이익추이"]) > 0 else None
                if "영업이익" in data[k]["PL"]["Y"].keys():
                    data[k]["PL"]["Y"]["영업이익"].popitem() if len(data[k]["PL"]["Y"]["영업이익"]) > 0 else None
                    before_op_profit = data[k]["PL"]["Y"]["영업이익"].popitem()[1] if len(
                        data[k]["PL"]["Y"]["영업이익"]) > 0 else None
                last_net_income = data[k]["PL"]["Q"]["누계당기순이익추이"].popitem()[1] if len(
                    data[k]["PL"]["Q"]["누계당기순이익추이"]) > 0 else None
                if "당기순이익" in data[k]["PL"]["Y"].keys():
                    data[k]["PL"]["Y"]["당기순이익"].popitem() if len(data[k]["PL"]["Y"]["당기순이익"]) > 0 else None
                    before_net_income = data[k]["PL"]["Y"]["당기순이익"].popitem()[1] if len(
                        data[k]["PL"]["Y"]["당기순이익"]) > 0 else None
        # print("here4?")
        if avg_sales_op_profit_rate and last_sales_op_profit_rate:
            if last_sales_op_profit_rate > 0 and avg_sales_op_profit_rate > 0 and last_sales_op_profit_rate > avg_sales_op_profit_rate:
                # print("here5?")
                if avg_sales and last_sales and before_sales and \
                        avg_net_income and last_net_income and before_net_income and \
                        last_sales > avg_sales and last_sales > before_sales and \
                        last_net_income > avg_net_income and last_net_income > before_net_income:
                    if last_sales_op_profit_rate > 20:
                        best[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "업종": data[k]["category"],
                                   "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                   "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                   "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                   "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                   "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                   "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                   "직전영업이익": format(before_op_profit,
                                                    ",") if before_op_profit is not None else None,
                                   "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                   "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                   "직전당기순이익": format(before_net_income,
                                                     ",") if before_net_income is not None else None,
                                   "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None
                                   }
                        call = json.loads(requests.get(
                            "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                                k)).content.decode("utf-8"))
                        best[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                        best[k]["PER"] = call["per"]
                        best[k]["EPS"] = call["eps"]
                        best[k]["PBR"] = call["pbr"]
                        best[k]["현재가"] = f'{call["now"]:,}'
                        best[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                data[k][
                                                                                                    "list_shares"] else 0
                        best[k]["PER2"] = round(call["now"] / best[k]["EPS2"], 0) if best[k]["EPS2"] != 0 else 0
                        best[k]["예상주가"] = format(int(round(best[k]["EPS2"] * best[k]["PER"], 0)), ",") if best[k][
                                                                                                              "EPS2"] and \
                                                                                                          best[k][
                                                                                                              "PER"] else 0
                    elif np.sign(last_sales_op_profit_rate) > np.sign(avg_sales_op_profit_rate):
                        best[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "업종": data[k]["category"],
                                   "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                   "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                   "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                   "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                   "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                   "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                   "직전영업이익": format(before_op_profit,
                                                    ",") if before_op_profit is not None else None,
                                   "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                   "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                   "직전당기순이익": format(before_net_income,
                                                     ",") if before_net_income is not None else None,
                                   "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None}
                        call = json.loads(requests.get(
                            "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                                k)).content.decode("utf-8"))
                        best[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                        best[k]["PER"] = call["per"]
                        best[k]["EPS"] = call["eps"]
                        best[k]["PBR"] = call["pbr"]
                        best[k]["현재가"] = f'{call["now"]:,}'
                        best[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                data[k][
                                                                                                    "list_shares"] else 0
                        best[k]["PER2"] = round(call["now"] / best[k]["EPS2"], 0) if best[k]["EPS2"] != 0 else 0
                        best[k]["예상주가"] = format(int(round(best[k]["EPS2"] * best[k]["PER"], 0)), ",") if best[k][
                                                                                                              "EPS2"] and \
                                                                                                          best[k][
                                                                                                              "PER"] else 0
                    else:
                        better[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "업종": data[k]["category"],
                                     "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                     "최근매출액영업이익률": last_sales_op_profit_rate,
                                     "평균매출액영업이익률": avg_sales_op_profit_rate,
                                     "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                     "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                     "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                     "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                     "직전영업이익": format(before_op_profit,
                                                      ",") if before_op_profit is not None else None,
                                     "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                     "최근당기순이익": format(last_net_income,
                                                       ",") if last_net_income is not None else None,
                                     "직전당기순이익": format(before_net_income,
                                                       ",") if before_net_income is not None else None,
                                     "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None
                                     }
                        call = json.loads(requests.get(
                            "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                                k)).content.decode("utf-8"))
                        better[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                        better[k]["PER"] = call["per"]
                        better[k]["EPS"] = call["eps"]
                        better[k]["PBR"] = call["pbr"]
                        better[k]["현재가"] = f'{call["now"]:,}'
                        better[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                  data[k][
                                                                                                      "list_shares"] else 0
                        better[k]["PER2"] = round(call["now"] / better[k]["EPS2"], 0) if better[k]["EPS2"] != 0 else 0
                        better[k]["예상주가"] = format(int(round(better[k]["EPS2"] * better[k]["PER"], 0)), ",") if \
                        better[k][
                            "EPS2"] and \
                        better[k][
                            "PER"] else 0
                else:
                    if last_sales_op_profit_rate > 15:
                        better[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "업종": data[k]["category"],
                                     "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                     "최근매출액영업이익률": last_sales_op_profit_rate,
                                     "평균매출액영업이익률": avg_sales_op_profit_rate,
                                     "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                     "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                     "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                     "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                     "직전영업이익": format(before_op_profit,
                                                      ",") if before_op_profit is not None else None,
                                     "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                     "최근당기순이익": format(last_net_income,
                                                       ",") if last_net_income is not None else None,
                                     "직전당기순이익": format(before_net_income,
                                                       ",") if before_net_income is not None else None,
                                     "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None
                                     }
                        call = json.loads(requests.get(
                            "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                                k)).content.decode("utf-8"))
                        better[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                        better[k]["PER"] = call["per"]
                        better[k]["EPS"] = call["eps"]
                        better[k]["PBR"] = call["pbr"]
                        better[k]["현재가"] = f'{call["now"]:,}'
                        better[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                  data[k][
                                                                                                      "list_shares"] else 0
                        better[k]["PER2"] = round(call["now"] / better[k]["EPS2"], 0) if better[k]["EPS2"] != 0 else 0
                        better[k]["예상주가"] = format(int(round(better[k]["EPS2"] * better[k]["PER"], 0)), ",") if \
                        better[k][
                            "EPS2"] and \
                        better[k][
                            "PER"] else 0
                    else:
                        # print("here7?")
                        good[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "업종": data[k]["category"],
                                   "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                   "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                   "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                   "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                   "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                   "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                   "직전영업이익": format(before_op_profit,
                                                    ",") if before_op_profit is not None else None,
                                   "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                   "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                   "직전당기순이익": format(before_net_income,
                                                     ",") if before_net_income is not None else None,
                                   "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None
                                   }
                        call = json.loads(requests.get(
                            "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                                k)).content.decode("utf-8"))
                        good[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                        good[k]["PER"] = call["per"]
                        good[k]["EPS"] = call["eps"]
                        good[k]["PBR"] = call["pbr"]
                        good[k]["현재가"] = f'{call["now"]:,}'
                        good[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                data[k][
                                                                                                    "list_shares"] else 0
                        good[k]["PER2"] = round(call["now"] / good[k]["EPS2"], 0) if good[k]["EPS2"] != 0 else 0
                        good[k]["예상주가"] = format(int(round(good[k]["EPS2"] * good[k]["PER"], 0)), ",") if good[k][
                                                                                                              "EPS2"] and \
                                                                                                          good[k][
                                                                                                              "PER"] else 0
            else:
                if last_sales_op_profit_rate > 15:
                    better[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "업종": data[k]["category"],
                                 "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                 "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                 "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                 "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                 "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                 "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                 "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                                 "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                 "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                 "직전당기순이익": format(before_net_income,
                                                   ",") if before_net_income is not None else None,
                                 "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None
                                 }
                    call = json.loads(requests.get(
                        "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                            k)).content.decode("utf-8"))
                    better[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                    better[k]["PER"] = call["per"]
                    better[k]["EPS"] = call["eps"]
                    better[k]["PBR"] = call["pbr"]
                    better[k]["현재가"] = f'{call["now"]:,}'
                    better[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                              data[k][
                                                                                                  "list_shares"] else 0
                    better[k]["PER2"] = round(call["now"] / better[k]["EPS2"], 0) if better[k]["EPS2"] != 0 else 0
                    better[k]["예상주가"] = format(int(round(better[k]["EPS2"] * better[k]["PER"], 0)), ",") if better[k][
                                                                                                                "EPS2"] and \
                                                                                                            better[k][
                                                                                                                "PER"] else 0
                else:
                    soso[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "업종": data[k]["category"],
                               "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                               "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                               "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                               "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                               "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                               "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                               "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                               "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                               "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                               "직전당기순이익": format(before_net_income, ",") if before_net_income is not None else None,
                               "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None
                               }
                    call = json.loads(requests.get(
                        "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                            k)).content.decode("utf-8"))
                    soso[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                    soso[k]["PER"] = call["per"]
                    soso[k]["EPS"] = call["eps"]
                    soso[k]["PBR"] = call["pbr"]
                    soso[k]["현재가"] = f'{call["now"]:,}'
                    soso[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                            data[k][
                                                                                                "list_shares"] else 0
                    soso[k]["PER2"] = round(call["now"] / soso[k]["EPS2"], 0) if soso[k]["EPS2"] != 0 else 0
                    soso[k]["예상주가"] = format(int(round(soso[k]["EPS2"] * soso[k]["PER"], 0)), ",") if soso[k][
                                                                                                          "EPS2"] and \
                                                                                                      soso[k][
                                                                                                          "PER"] else 0
        else:
            soso[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "업종": data[k]["category"],
                       "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                       "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                       "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                       "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                       "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                       "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                       "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                       "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                       "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                       "직전당기순이익": format(before_net_income, ",") if before_net_income is not None else None,
                       "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None
                       }
            call = json.loads(requests.get(
                "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                    k)).content.decode("utf-8"))
            soso[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
            soso[k]["PER"] = call["per"]
            soso[k]["EPS"] = call["eps"]
            soso[k]["PBR"] = call["pbr"]
            soso[k]["현재가"] = f'{call["now"]:,}'
            soso[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                    data[k][
                                                                                        "list_shares"] else 0
            soso[k]["PER2"] = round(call["now"] / soso[k]["EPS2"], 0) if soso[k]["EPS2"] != 0 else 0
            soso[k]["예상주가"] = format(int(round(soso[k]["EPS2"] * soso[k]["PER"], 0)), ",") if soso[k]["EPS2"] and \
                                                                                              soso[k][
                                                                                                  "PER"] else 0
            # info_lack[k] = {"corp_name": data[k]["corp_name"], "corp_code": data[k]["corp_code"]}
    logger.info("{} {} {} {}".format("*" * 100, "BEST", len(best), "*" * 100))
    for key in best.keys():
        logger.info(best[key])
        if best[key]["EPS2"] != 0 and best[key]["EPS2"] > best[key]["EPS"] and (best[key]["EPS2"] - best[key]["EPS"]) / \
                best[key]["EPS"] * 100 >= 30:
            if "BEST" not in treasure.keys():
                treasure["BEST"] = {}
            treasure["BEST"][key] = {"사명": best[key]["corp_name"], "시가총액": best[key]["시가총액"], "업종": best[key]["업종"],
                                     "최근매출액영업이익률": best[key]["최근매출액영업이익률"], "EPS": best[key]["EPS"],
                                     "추정EPS": best[key]["EPS2"],
                                     "괴리율": round((best[key]["EPS2"] - best[key]["EPS"]) / best[key]["EPS"] * 100, 2),
                                     "현재가": best[key]["현재가"], "예상주가": best[key]["예상주가"]}
    logger.info("{} {} {} {}".format("*" * 100, "BETTER", len(better), "*" * 100))
    for key in better.keys():
        logger.info(better[key])
        if better[key]["EPS2"] != 0 and better[key]["EPS2"] > better[key]["EPS"] and (
                better[key]["EPS2"] - better[key]["EPS"]) / better[key]["EPS"] * 100 >= 30:
            if "BETTER" not in treasure.keys():
                treasure["BETTER"] = {}
            treasure["BETTER"][key] = {"사명": better[key]["corp_name"], "시가총액": better[key]["시가총액"],
                                       "업종": better[key]["업종"], "최근매출액영업이익률": better[key]["최근매출액영업이익률"],
                                       "EPS": better[key]["EPS"], "추정EPS": better[key]["EPS2"], "괴리율": round(
                    (better[key]["EPS2"] - better[key]["EPS"]) / better[key]["EPS"] * 100, 2),
                                       "현재가": better[key]["현재가"], "예상주가": better[key]["예상주가"]}
    logger.info("{} {} {} {}".format("*" * 100, "GOOD", len(good), "*" * 100))
    for key in good.keys():
        logger.info(good[key])
        if good[key]["EPS2"] != 0 and good[key]["EPS2"] > good[key]["EPS"] and (good[key]["EPS2"] - good[key]["EPS"]) / \
                good[key]["EPS"] * 100 >= 30:
            if "GOOD" not in treasure.keys():
                treasure["GOOD"] = {}
            treasure["GOOD"][key] = {"사명": good[key]["corp_name"], "시가총액": good[key]["시가총액"], "업종": good[key]["업종"],
                                     "최근매출액영업이익률": good[key]["최근매출액영업이익률"], "EPS": good[key]["EPS"],
                                     "추정EPS": good[key]["EPS2"],
                                     "괴리율": round((good[key]["EPS2"] - good[key]["EPS"]) / good[key]["EPS"] * 100, 2),
                                     "현재가": good[key]["현재가"], "예상주가": good[key]["예상주가"]}
    logger.info("{} {} {} {}".format("*" * 100, "CHECK", len(soso), "*" * 100))
    for key in soso.keys():
        logger.info(soso[key])
        if soso[key]["EPS2"] != 0 and soso[key]["EPS2"] > soso[key]["EPS"] and (soso[key]["EPS2"] - soso[key]["EPS"]) / \
                soso[key]["EPS"] * 100 >= 30:
            if "SOSO" not in treasure.keys():
                treasure["SOSO"] = {}
            treasure["SOSO"][key] = {"사명": soso[key]["corp_name"], "시가총액": soso[key]["시가총액"], "업종": soso[key]["업종"],
                                     "최근매출액영업이익률": soso[key]["최근매출액영업이익률"], "EPS": soso[key]["EPS"],
                                     "추정EPS": soso[key]["EPS2"],
                                     "괴리율": round((soso[key]["EPS2"] - soso[key]["EPS"]) / soso[key]["EPS"] * 100, 2),
                                     "현재가": soso[key]["현재가"], "예상주가": soso[key]["예상주가"]}
    return treasure


def new_find_hidden_pearl_with_dartpipe_provision_test(code, search, bgn_dt, end_dt=None):
    import sys
    import os
    import django
    from OpenDartPipe import pipe
    # sys.path.append(r'E:\Github\Waver\MainBoard')
    # sys.path.append(r'E:\Github\Waver\MainBoard\MainBoard')
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    # import detective_app.models as detective_db
    import watson.db_factory as db
    import json
    import numpy as np
    import requests
    import logging

    logfile = 'detector'
    if not os.path.exists(r'C:\Users\Kim\Documents\Projects\Waver\detective\logs'):
        os.makedirs(r'C:\Users\Kim\Documents\Projects\Waver\detective\logs')
    now = datetime.now().strftime("%Y%m%d%H%M%S")

    logger = logging.getLogger(__name__)
    formatter = logging.Formatter('[%(asctime)s][%(filename)s:%(lineno)s] >> %(message)s')

    streamHandler = logging.StreamHandler()
    fileHandler = logging.FileHandler(r"./logs/{}_{}.log".format(logfile, now))

    streamHandler.setFormatter(formatter)
    fileHandler.setFormatter(formatter)

    logger.addHandler(streamHandler)
    logger.addHandler(fileHandler)
    logger.setLevel(level=logging.INFO)

    # logging
    # logging.basicConfig(filename=logfile, filemode='w', level=logging.DEBUG)
    # logging.debug("Log started at %s", str(datetime.datetime.now()))

    current_pos = None
    current_key = None
    treasure = {}
    trash = {}
    data = {}
    best = {}
    better = {}
    good = {}
    soso = {}
    info_lack = {}
    none_list = []
    # 날짜 정보 셋팅
    dateDict = new_get_dateDict()
    # 종목 정보 셋팅
    # DEBUG = True
    DEBUG = False
    # USE_JSON = False
    USE_JSON = True
    # stockInfo = detective_db.Stocks.objects.filter(category_name__contains="일반 목적", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(category_name__contains="특수", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(market_text__contains="제조", market_text_detail__contains="장비", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(code="058110", listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(code="005930", listing='Y')
    dart = pipe.Pipe()
    dart.create()
    if end_dt is None:
        if search: dart.get_krx_reporting(bgn_dt)
        provision_info = dart.get_provisional_performance_reporting_corp_info_with_code(code, bgn_dt)
    else:
        if search: dart.get_krx_reporting(bgn_dt, end_dt)
        provision_info = dart.get_provisional_performance_reporting_corp_info_with_code(code, bgn_dt, end_dt)
    for stock in provision_info.keys():
        # print(stock)
        try:
            stock_obj = db.getStockInfo(stock).values().get()
            code = provision_info[stock]["corp_code"]
            name = provision_info[stock]["corp_name"]
            data[stock] = {"corp_code": code,
                           "corp_name": name,
                           "category": stock_obj["category_name"],
                           "list_shares": stock_obj["issued_shares"],
                           "PL": {"Y": {}, "Q": {}},
                           "FS": {"TotalAsset": {}, "TotalDebt": {}, "RetainedEarnings": {}},
                           "CF": {"영업활동현금흐름": {}, "유형자산취득": {}, "무형자산취득": {}, "FCF": {}},
                           "AverageRate": {"Y": {}, "Q": {}}}
            # print(dateDict["yyyy2"], dateDict)
            lists = None
            lists = dart.get_list(corp_code=code, bgn_de=dateDict["yyyy2"], pblntf_ty='A', req_type=True)["list"][:5]
            for l in lists:
                logger.info(l)
            # if stock == "064350":
            #     print()
            req_list, req_list2 = dart.get_req_lists(lists)
            result = dart.get_fnlttSinglAcnt_from_req_list(code, req_list, "ALL")
            # result = dart.get_fnlttSinglAcnt_from_req_list(code, req_list)
            current_pos = result

            for key in result.keys():  # key = ["연결재무제표", "재무제표"]
                for report in result[key].keys():  # report = ["재무상태표", "손익계산서"]
                    if report not in ["손익계산서", "포괄손익계산서"]:  # ["재무상태표", "현금흐름표", "자본변동표"]:
                        for acc in result[key][report].keys():
                            # acc = ["유동자산", "비유동자산", "자산총계", "유동부채", "비유동부채", "부채총계", "자본금", "이익잉여금", "자본총계"]
                            for category in sorted(result[key][report][acc].keys()):
                                # category = ["YYYY 1/4", "YYYY 2/4", "YYYY 3/4", "YYYY 4/4"]
                                print(key, report, acc, category, result[key][report][acc][category])
                                # for k in result[key][report][acc][category].keys():
                                #     print(key, report, acc, category, k, result[key][report][acc][category][k])
                    else:
                        for acc in result[key][report].keys():
                            # acc = ["매출액", 영업이익", "법인세차감전", "당기순이익"]
                            for category in result[key][report][acc].keys():
                                # category = ["누계", "당기"]
                                for k in sorted(result[key][report][acc][category].keys()):
                                    # k = ["YYYY 1/4", "YYYY 2/4", "YYYY 3/4", "YYYY 4/4"]
                                    print(key, report, acc, category, k, result[key][report][acc][category][k])
            d1 = None
            d2 = None
            d3 = None
            d4 = None
            d5 = None
            d6 = None
            d7 = None
            d8 = None
            d9 = None
            d10 = None
            d11 = None
            d12 = None
            d13 = None
            d14 = None
            dicTemp0 = {}
            dicTemp1 = {}
            dicTemp2 = {}
            dicTemp3 = {}
            dicTemp4 = {}
            dicTemp5 = {}
            dicTemp6 = {}
            dicTemp7 = {}
            dicTemp8 = {}
            dicTemp9 = {}
            dicTemp10 = {}
            dicTemp11 = {}
            dicTemp12 = {}
            dicTemp13 = {}
            dicTemp14 = {}
            # if stock == "006360":
            #     print()
            d1keys = ["매출", "수익(매출액)", "I.  매출액", "영업수익", "매출액", "Ⅰ. 매출액", "매출 및 지분법 손익", "매출 및 지분법손익", "매출 및 지분법손익"]
            d2keys = ["영업이익(손실)", "영업이익 (손실)", "영업이익", "영업손익", "V. 영업손익", "Ⅴ. 영업이익", "Ⅴ. 영업이익(손실)", "V. 영업이익", "영업손실"]
            d8keys = ["당기순이익(손실)", "당기순이익 (손실)", "당기순이익", "분기순이익", "반기순이익", "당기순이익(손실)", "분기순이익(손실)", "반기순이익(손실)",
                      "연결당기순이익", "연결분기순이익", "연결반기순이익", "연결당기순이익(손실)", "연결분기순이익(손실)", "연결반기순이익(손실)", "당기순손익",
                      "분기순손익",
                      "반기순손익", "지배기업 소유주지분", "지배기업의 소유주에게 귀속되는 당기순이익(손실)", "당기순손실", "분기순손실", "반기순손실",
                      "Ⅷ. 당기순이익(손실)", "지배기업 소유주 지분",
                      "Ⅷ. 당기순이익", "VIII. 당기순이익", "지배기업 소유주", "VIII. 분기순손익", "VIII. 분기순이익", "I.당기순이익", "I.반기순이익",
                      "I.분기순이익", "반기연결순이익(손실)", "지배기업의 소유주지분", "지배기업소유주지분", "지배기업의소유주지분"]
            d10keys = ["영업활동현금흐름", "영업활동 현금흐름", "영업활동으로 인한 현금흐름", "영업활동 순현금흐름유입", "영업활동으로인한현금흐름", "영업활동으로 인한 순현금흐름",
                       "Ⅰ. 영업활동으로 인한 현금흐름", "Ⅰ. 영업활동으로 인한 현금흐름", "영업활동순현금흐름 합계", "영업활동순현금흐름", "I. 영업활동현금흐름"]
            d11keys = ["유형자산의 취득", "유형자산 취득", "유형자산의취득"]
            d12keys = ["무형자산의 취득", "무형자산 취득", "무형자산의취득", "무형자산의 증가"]
            d13keys = ["토지의 취득", "건물의 취득", "구축물의 취득", "기계장치의 취득", "차량운반구의 취득", "공구와기구의취득", "공구와기구의 취득", "비품의 취득",
                       "기타유형자산의 취득", "건설중인자산의 취득", "투자부동산의 취득", "집기비품의 취득", "시험기기의 취득"]
            d14keys = ["컴퓨터소프트웨어의 취득", "산업재산권의 취득", "소프트웨어의 취득", "기타무형자산의 취득"]
            # if stock == "006360":
            #     print()
            if result is not {} and "연결재무제표" in result.keys():
                logger.info("연결재무제표 start")
                if "포괄손익계산서" in result["연결재무제표"].keys():
                    logger.info("연결재무제표 포괄손익계산서 start")
                    tmp_result1 = {key: result["연결재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                   result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d1keys}}
                    tmp_result2 = {key: result["연결재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                   result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d2keys}}
                    tmp_result3 = {key: result["연결재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                   result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d1keys}}
                    tmp_result4 = {key: result["연결재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                   result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d2keys}}
                    tmp_result8 = {key: result["연결재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                   result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d8keys}}
                    tmp_result9 = {key: result["연결재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                   result["연결재무제표"]["포괄손익계산서"].keys() & {keys for keys in d8keys}}
                    if tmp_result1:
                        for key in tmp_result1.keys():
                            if d1 is None:
                                d1 = tmp_result1[key]
                            else:
                                d1.update(tmp_result1[key])
                    if tmp_result2:
                        for key in tmp_result2.keys():
                            if d2 is None:
                                d2 = tmp_result2[key]
                            else:
                                d2.update(tmp_result2[key])
                    if tmp_result3:
                        for key in tmp_result3.keys():
                            if d3 is None:
                                d3 = tmp_result3[key]
                            else:
                                d3.update(tmp_result3[key])
                    if tmp_result4:
                        for key in tmp_result4.keys():
                            if d4 is None:
                                d4 = tmp_result4[key]
                            else:
                                d4.update(tmp_result4[key])
                    if tmp_result8:
                        for key in tmp_result8.keys():
                            if d8 is None:
                                d8 = tmp_result8[key]
                            else:
                                d8.update(tmp_result8[key])
                    if tmp_result9:
                        for key in tmp_result9.keys():
                            if d9 is None:
                                d9 = tmp_result9[key]
                            else:
                                d9.update(tmp_result9[key])
                if "손익계산서" in result["연결재무제표"].keys():
                    logger.info("연결재무제표 손익계산서 start")
                    tmp_result1 = {key: result["연결재무제표"]["손익계산서"][key]["누계"] for key in
                                   result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d1keys}}
                    tmp_result2 = {key: result["연결재무제표"]["손익계산서"][key]["누계"] for key in
                                   result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d2keys}}
                    tmp_result3 = {key: result["연결재무제표"]["손익계산서"][key]["당기"] for key in
                                   result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d1keys}}
                    tmp_result4 = {key: result["연결재무제표"]["손익계산서"][key]["당기"] for key in
                                   result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d2keys}}
                    tmp_result8 = {key: result["연결재무제표"]["손익계산서"][key]["누계"] for key in
                                   result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d8keys}}
                    tmp_result9 = {key: result["연결재무제표"]["손익계산서"][key]["당기"] for key in
                                   result["연결재무제표"]["손익계산서"].keys() & {keys for keys in d8keys}}
                    if tmp_result1:
                        for key in tmp_result1.keys():
                            if d1 is None:
                                d1 = tmp_result1[key]
                            else:
                                d1.update(tmp_result1[key])
                    if tmp_result2:
                        for key in tmp_result2.keys():
                            if d2 is None:
                                d2 = tmp_result2[key]
                            else:
                                d2.update(tmp_result2[key])
                    if tmp_result3:
                        for key in tmp_result3.keys():
                            if d3 is None:
                                d3 = tmp_result3[key]
                            else:
                                d3.update(tmp_result3[key])
                    if tmp_result4:
                        for key in tmp_result4.keys():
                            if d4 is None:
                                d4 = tmp_result4[key]
                            else:
                                d4.update(tmp_result4[key])
                    if tmp_result8:
                        for key in tmp_result8.keys():
                            if d8 is None:
                                d8 = tmp_result8[key]
                            else:
                                d8.update(tmp_result8[key])
                    if tmp_result9:
                        for key in tmp_result9.keys():
                            if d9 is None:
                                d9 = tmp_result9[key]
                            else:
                                d9.update(tmp_result9[key])
                if "현금흐름표" in result["연결재무제표"].keys():
                    logger.info("연결재무제표 현금흐름표 start")
                    tmp_result10 = {key: result["연결재무제표"]["현금흐름표"][key] for key in
                                    result["연결재무제표"]["현금흐름표"].keys() & {keys for keys in d10keys}}
                    tmp_result11 = {key: result["연결재무제표"]["현금흐름표"][key] for key in
                                    result["연결재무제표"]["현금흐름표"].keys() & {keys for keys in d11keys}}
                    tmp_result12 = {key: result["연결재무제표"]["현금흐름표"][key] for key in
                                    result["연결재무제표"]["현금흐름표"].keys() & {keys for keys in d12keys}}
                    tmp_result13 = {key: result["연결재무제표"]["현금흐름표"][key] for key in
                                    result["연결재무제표"]["현금흐름표"].keys() & {keys for keys in d13keys}}
                    tmp_result14 = {key: result["연결재무제표"]["현금흐름표"][key] for key in
                                    result["연결재무제표"]["현금흐름표"].keys() & {keys for keys in d14keys}}
                    if tmp_result10:
                        for key in tmp_result10.keys():
                            if d10 is None:
                                d10 = tmp_result10[key]
                            else:
                                d10.update(tmp_result10[key])
                    if tmp_result11:
                        for key in tmp_result11.keys():
                            if d11 is None:
                                d11 = tmp_result11[key]
                            else:
                                d11.update(tmp_result11[key])
                    if tmp_result12:
                        for key in tmp_result12.keys():
                            if d12 is None:
                                d12 = tmp_result12[key]
                            else:
                                d12.update(tmp_result12[key])
                    if tmp_result13:
                        d13 = dictionary_add(tmp_result13)
                        # for key in tmp_result13.keys():
                        #     if d13 is None:
                        #         d13 = tmp_result13[key]
                        #     else:
                        #         d13.update(tmp_result13[key])
                    if tmp_result14:
                        d14 = dictionary_add(tmp_result14)
                        # for key in tmp_result14.keys():
                        #     if d14 is None:
                        #         d14 = tmp_result14[key]
                        #     else:
                        #         d14.update(tmp_result14[key])
                if d11 is None: d11 = d13
                if d12 is None: d12 = d14
                d5 = result["연결재무제표"]["재무상태표"]["자산총계"] if "자산총계" in result["연결재무제표"]["재무상태표"].keys() else None
                d6 = result["연결재무제표"]["재무상태표"]["부채총계"] if "부채총계" in result["연결재무제표"]["재무상태표"].keys() else None
                d7 = result["연결재무제표"]["재무상태표"]["이익잉여금"] if "이익잉여금" in result["연결재무제표"]["재무상태표"].keys() else None
                if d5 is None:
                    if "자  산  총  계" in result["연결재무제표"]["재무상태표"].keys():
                        d5 = result["연결재무제표"]["재무상태표"]["자  산  총  계"]
                else:
                    if "자  산  총  계" in result["연결재무제표"]["재무상태표"].keys():
                        d5.update(result["연결재무제표"]["재무상태표"]["자  산  총  계"])
                if d5 is None:
                    if "자산 총계" in result["연결재무제표"]["재무상태표"].keys():
                        d5 = result["연결재무제표"]["재무상태표"]["자산 총계"]
                else:
                    if "자산 총계" in result["연결재무제표"]["재무상태표"].keys():
                        d5.update(result["연결재무제표"]["재무상태표"]["자산 총계"])
                if d6 is None:
                    if "부  채  총  계" in result["연결재무제표"]["재무상태표"].keys():
                        d6 = result["연결재무제표"]["재무상태표"]["부  채  총  계"]
                else:
                    if "부  채  총  계" in result["연결재무제표"]["재무상태표"].keys():
                        d6.update(result["연결재무제표"]["재무상태표"]["부  채  총  계"])
                if d6 is None:
                    if "부채 총계" in result["연결재무제표"]["재무상태표"].keys():
                        d6 = result["연결재무제표"]["재무상태표"]["부채 총계"]
                else:
                    if "부채 총계" in result["연결재무제표"]["재무상태표"].keys():
                        d6.update(result["연결재무제표"]["재무상태표"]["부채 총계"])
                if d7 is None:
                    if "이익잉여금(결손금)" in result["연결재무제표"]["재무상태표"].keys():
                        d7 = result["연결재무제표"]["재무상태표"]["이익잉여금(결손금)"]
                else:
                    if "이익잉여금(결손금)" in result["연결재무제표"]["재무상태표"].keys():
                        d7.update(result["연결재무제표"]["재무상태표"]["이익잉여금(결손금)"])
                if d7 is None:
                    if "결손금" in result["연결재무제표"]["재무상태표"].keys():
                        d7 = result["연결재무제표"]["재무상태표"]["결손금"]
                else:
                    if "결손금" in result["연결재무제표"]["재무상태표"].keys():
                        d7.update(result["연결재무제표"]["재무상태표"]["결손금"])
            else:
                logger.info("재무제표 start")
                if "포괄손익계산서" in result["재무제표"].keys():
                    logger.info("재무제표 포괄손익계산서 start")
                    tmp_result1 = {key: result["재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                   result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d1keys}}
                    tmp_result2 = {key: result["재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                   result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d2keys}}
                    tmp_result3 = {key: result["재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                   result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d1keys}}
                    tmp_result4 = {key: result["재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                   result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d2keys}}
                    tmp_result8 = {key: result["재무제표"]["포괄손익계산서"][key]["누계"] for key in
                                   result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d8keys}}
                    tmp_result9 = {key: result["재무제표"]["포괄손익계산서"][key]["당기"] for key in
                                   result["재무제표"]["포괄손익계산서"].keys() & {keys for keys in d8keys}}
                    if tmp_result1:
                        for key in tmp_result1.keys():
                            if d1 is None:
                                d1 = tmp_result1[key]
                            else:
                                d1.update(tmp_result1[key])
                    if tmp_result2:
                        for key in tmp_result2.keys():
                            if d2 is None:
                                d2 = tmp_result2[key]
                            else:
                                d2.update(tmp_result2[key])
                    if tmp_result3:
                        for key in tmp_result3.keys():
                            if d3 is None:
                                d3 = tmp_result3[key]
                            else:
                                d3.update(tmp_result3[key])
                    if tmp_result4:
                        for key in tmp_result4.keys():
                            if d4 is None:
                                d4 = tmp_result4[key]
                            else:
                                d4.update(tmp_result4[key])
                    if tmp_result8:
                        for key in tmp_result8.keys():
                            if d8 is None:
                                d8 = tmp_result8[key]
                            else:
                                d8.update(tmp_result8[key])
                    if tmp_result9:
                        for key in tmp_result9.keys():
                            if d9 is None:
                                d9 = tmp_result9[key]
                            else:
                                d9.update(tmp_result9[key])
                if "손익계산서" in result["재무제표"].keys():
                    logger.info("재무제표 손익계산서 매출 start")
                    tmp_result1 = {key: result["재무제표"]["손익계산서"][key]["누계"] for key in
                                   result["재무제표"]["손익계산서"].keys() & {keys for keys in d1keys}}
                    tmp_result2 = {key: result["재무제표"]["손익계산서"][key]["누계"] for key in
                                   result["재무제표"]["손익계산서"].keys() & {keys for keys in d2keys}}
                    tmp_result3 = {key: result["재무제표"]["손익계산서"][key]["당기"] for key in
                                   result["재무제표"]["손익계산서"].keys() & {keys for keys in d1keys}}
                    tmp_result4 = {key: result["재무제표"]["손익계산서"][key]["당기"] for key in
                                   result["재무제표"]["손익계산서"].keys() & {keys for keys in d2keys}}
                    tmp_result8 = {key: result["재무제표"]["손익계산서"][key]["누계"] for key in
                                   result["재무제표"]["손익계산서"].keys() & {keys for keys in d8keys}}
                    tmp_result9 = {key: result["재무제표"]["손익계산서"][key]["당기"] for key in
                                   result["재무제표"]["손익계산서"].keys() & {keys for keys in d8keys}}
                    if tmp_result1:
                        for key in tmp_result1.keys():
                            if d1 is None:
                                d1 = tmp_result1[key]
                            else:
                                d1.update(tmp_result1[key])
                    if tmp_result2:
                        for key in tmp_result2.keys():
                            if d2 is None:
                                d2 = tmp_result2[key]
                            else:
                                d2.update(tmp_result2[key])
                    if tmp_result3:
                        for key in tmp_result3.keys():
                            if d3 is None:
                                d3 = tmp_result3[key]
                            else:
                                d3.update(tmp_result3[key])
                    if tmp_result4:
                        for key in tmp_result4.keys():
                            if d4 is None:
                                d4 = tmp_result4[key]
                            else:
                                d4.update(tmp_result4[key])
                    if tmp_result8:
                        for key in tmp_result8.keys():
                            if d8 is None:
                                d8 = tmp_result8[key]
                            else:
                                d8.update(tmp_result8[key])
                    if tmp_result9:
                        for key in tmp_result9.keys():
                            if d9 is None:
                                d9 = tmp_result9[key]
                            else:
                                d9.update(tmp_result9[key])
                if "현금흐름표" in result["재무제표"].keys():
                    logger.info("재무제표 현금흐름표 start")
                    tmp_result10 = {key: result["재무제표"]["현금흐름표"][key] for key in
                                    result["재무제표"]["현금흐름표"].keys() & {keys for keys in d10keys}}
                    tmp_result11 = {key: result["재무제표"]["현금흐름표"][key] for key in
                                    result["재무제표"]["현금흐름표"].keys() & {keys for keys in d11keys}}
                    tmp_result12 = {key: result["재무제표"]["현금흐름표"][key] for key in
                                    result["재무제표"]["현금흐름표"].keys() & {keys for keys in d12keys}}
                    tmp_result13 = {key: result["재무제표"]["현금흐름표"][key] for key in
                                    result["재무제표"]["현금흐름표"].keys() & {keys for keys in d13keys}}
                    tmp_result14 = {key: result["재무제표"]["현금흐름표"][key] for key in
                                    result["재무제표"]["현금흐름표"].keys() & {keys for keys in d14keys}}
                    if tmp_result10:
                        for key in tmp_result10.keys():
                            if d10 is None:
                                d10 = tmp_result10[key]
                            else:
                                d10.update(tmp_result10[key])
                    if tmp_result11:
                        for key in tmp_result11.keys():
                            if d11 is None:
                                d11 = tmp_result11[key]
                            else:
                                d11.update(tmp_result11[key])
                    if tmp_result12:
                        for key in tmp_result12.keys():
                            if d12 is None:
                                d12 = tmp_result12[key]
                            else:
                                d12.update(tmp_result12[key])
                    if tmp_result13:
                        d13 = dictionary_add(tmp_result13)
                        # for key in tmp_result13.keys():
                        #     if d13 is None:
                        #         d13 = tmp_result13[key]
                        #     else:
                        #         d13.update(tmp_result13[key])
                    if tmp_result14:
                        d14 = dictionary_add(tmp_result14)
                        # for key in tmp_result14.keys():
                        #     if d14 is None:
                        #         d14 = tmp_result14[key]
                        #     else:
                        #         d14.update(tmp_result14[key])
                if d11 is None: d11 = d13
                if d12 is None: d12 = d14
                d5 = result["재무제표"]["재무상태표"]["자산총계"] if "자산총계" in result["재무제표"]["재무상태표"].keys() else None
                d6 = result["재무제표"]["재무상태표"]["부채총계"] if "부채총계" in result["재무제표"]["재무상태표"].keys() else None
                d7 = result["재무제표"]["재무상태표"]["이익잉여금"] if "이익잉여금" in result["재무제표"]["재무상태표"].keys() else None
                if d5 is None:
                    if "자  산  총  계" in result["재무제표"]["재무상태표"].keys():
                        d5 = result["재무제표"]["재무상태표"]["자  산  총  계"]
                else:
                    if "자  산  총  계" in result["재무제표"]["재무상태표"].keys():
                        d5.update(result["재무제표"]["재무상태표"]["자  산  총  계"])
                if d5 is None:
                    if "자산 총계" in result["재무제표"]["재무상태표"].keys():
                        d5 = result["재무제표"]["재무상태표"]["자산 총계"]
                else:
                    if "자산 총계" in result["재무제표"]["재무상태표"].keys():
                        d5.update(result["재무제표"]["재무상태표"]["자산 총계"])
                if d6 is None:
                    if "부  채  총  계" in result["재무제표"]["재무상태표"].keys():
                        d6 = result["재무제표"]["재무상태표"]["부  채  총  계"]
                else:
                    if "부  채  총  계" in result["재무제표"]["재무상태표"].keys():
                        d6.update(result["재무제표"]["재무상태표"]["부  채  총  계"])
                if d6 is None:
                    if "부채 총계" in result["재무제표"]["재무상태표"].keys():
                        d6 = result["재무제표"]["재무상태표"]["부채 총계"]
                else:
                    if "부채 총계" in result["재무제표"]["재무상태표"].keys():
                        d6.update(result["재무제표"]["재무상태표"]["부채 총계"])
                if d7 is None:
                    if "이익잉여금(결손금)" in result["재무제표"]["재무상태표"].keys():
                        d7 = result["재무제표"]["재무상태표"]["이익잉여금(결손금)"]
                else:
                    if "이익잉여금(결손금)" in result["재무제표"]["재무상태표"].keys():
                        d7.update(result["재무제표"]["재무상태표"]["이익잉여금(결손금)"])
                if d7 is None:
                    if "결손금" in result["재무제표"]["재무상태표"].keys():
                        d7 = result["재무제표"]["재무상태표"]["결손금"]
                else:
                    if "결손금" in result["재무제표"]["재무상태표"].keys():
                        d7.update(result["재무제표"]["재무상태표"]["결손금"])
            logger.info("매출액 누계 : {}".format(d1))  # 매출액 누계
            logger.info("영업이익 누계 : {}".format(d2))  # 영업이익 누계
            logger.info("매출액 누계 : {}".format(d3))  # 매출액 당기
            logger.info("영업이익 누계 : {}".format(d4))  # 영업이익 당기
            logger.info("자산총계 : {}".format(d5))  # 자산총계
            logger.info("부채총계 : {}".format(d6))  # 부채총계
            logger.info("이익잉여금 : {}".format(d7))  # 이익잉여금
            logger.info("당기순이익 누계 : {}".format(d8))  # 당기순이익 누계
            logger.info("당기순이익 : {}".format(d9))  # 당기순이익
            logger.info("영업활동현금흐름 : {}".format(d10))  # 영업활동현금흐름
            logger.info("유형자산의 취득 : {}".format(d11))  # 유형자산의 취득
            logger.info("무형자산의 취득 : {}".format(d12))  # 무형자산의 취득
            logger.info("유형자산의 취득(유형자산의 취득으로 표시되지 않는) : {}".format(d13))  # 유형자산의 취득(유형자산의 취득으로 표시되지 않는)
            logger.info("무형자산의 취득(무형자산의 취득으로 표시되지 않는) : {}".format(d14))  # 무형자산의 취득(무형자산의 취득으로 표시되지 않는)
            logger.info(provision_info[stock])
            if d10 is None:
                none_list.append("[{}][{}]-영업활동현금흐름".format(code, name))
            if d11 is None:
                none_list.append("[{}][{}]-유형자산의 취득".format(code, name))
            if d12 is None:
                none_list.append("[{}][{}]-무형자산의 취득".format(code, name))

            for key1 in d1.keys():
                current_key = key1
                # if key1 == "2019 4/4":
                #     print(key1)
                # if "1/4" in key1:
                #     print(key1)
                if "Rate" in key1: continue
                if "4/4" in key1:
                    data[stock]["PL"]["Y"]["매출액영업이익률"] = dict(sorted({
                                                                         k: round(float(
                                                                             d2[key1][k].replace(",", "")) / float(
                                                                             d1[key1][k].replace(",", "")) * 100,
                                                                                  2) if float(
                                                                             d1[key1][k].replace(",",
                                                                                                 "")) != 0.0 else 0
                                                                         for k in d1[key1]}.items()))
                    if "매출액" in provision_info[stock]["PL"]["Y"].keys() and \
                            "영업이익" in provision_info[stock]["PL"]["Y"].keys() and \
                            provision_info[stock]["PL"]["Y"]["매출액"] != 0:
                        data[stock]["PL"]["Y"]["매출액영업이익률"]["최근"] = round(
                            provision_info[stock]["PL"]["Y"]["영업이익"] / provision_info[stock]["PL"]["Y"]["매출액"] * 100, 2)
                    else:
                        data[stock]["PL"]["Y"]["매출액영업이익률"]["최근"] = 0
                    data[stock]["PL"]["Y"]["매출액"] = dict(
                        sorted({k: float(d1[key1][k].replace(",", "")) for k in
                                d1[key1]}.items()))
                    data[stock]["PL"]["Y"]["매출액"]["최근"] = provision_info[stock]["PL"]["Y"]["매출액"] if "매출액" in \
                                                                                                     provision_info[
                                                                                                         stock]["PL"][
                                                                                                         "Y"].keys() else 0
                    # data[stock]["PL"]["Y"]["매출액"]["최근"] = provision_info[stock]["PL"]["Y"]["매출액"]
                    data[stock]["PL"]["Y"]["영업이익"] = dict(
                        sorted({k: float(d2[key1][k].replace(",", "")) for k in
                                d2[key1]}.items()))
                    data[stock]["PL"]["Y"]["영업이익"]["최근"] = provision_info[stock]["PL"]["Y"]["영업이익"] if "영업이익" in \
                                                                                                       provision_info[
                                                                                                           stock][
                                                                                                           "PL"][
                                                                                                           "Y"].keys() else 0
                    data[stock]["PL"]["Y"]["당기순이익"] = dict(
                        sorted({k: float(d8[key1][k].replace(",", "")) for k in
                                d8[key1]}.items()))
                    data[stock]["PL"]["Y"]["당기순이익"]["최근"] = provision_info[stock]["PL"]["Y"]["당기순이익"] if "당기순이익" in \
                                                                                                         provision_info[
                                                                                                             stock][
                                                                                                             "PL"][
                                                                                                             "Y"].keys() else 0
                    # data[stock]["PL"]["Y"]["영업이익"]["최근"] = provision_info[stock]["PL"]["Y"]["영업이익"]
                    for k in sorted(d1[key1]):
                        dicTemp1[k] = float(d1[key1][k].replace(",", ""))
                    dicTemp1["최근"] = provision_info[stock]["PL"]["Y"]["매출액"] if "매출액" in provision_info[stock]["PL"][
                        "Y"].keys() else 0
                    for k in sorted(d2[key1]):
                        dicTemp2[k] = float(d2[key1][k].replace(",", ""))
                    dicTemp2["최근"] = provision_info[stock]["PL"]["Y"]["영업이익"] if "영업이익" in provision_info[stock]["PL"][
                        "Y"].keys() else 0
                    for k in sorted(d8[key1]):
                        dicTemp8[k] = float(d8[key1][k].replace(",", ""))
                    dicTemp8["최근"] = provision_info[stock]["PL"]["Y"]["당기순이익"] if "당기순이익" in \
                                                                                  provision_info[stock]["PL"][
                                                                                      "Y"].keys() else 0
                else:
                    for k in sorted(d1[key1]):
                        dicTemp0[k] = round(
                            float(d2[key1][k].replace(",", "")) / float(d1[key1][k].replace(",", "")) * 100,
                            2) if float(d1[key1][k].replace(",", "")) != 0.0 else 0
                    dicTemp0["최근"] = round(
                        provision_info[stock]["PL"]["Q"]["영업이익"] / provision_info[stock]["PL"]["Q"]["매출액"] * 100, 2) if \
                        provision_info[stock]["PL"]["Q"]["매출액"] != 0 else 0
                    for k in sorted(d1[key1]):
                        dicTemp1[k] = float(d1[key1][k].replace(",", ""))
                        # data[stock]["PL"]["Q"]["누계매출액"][k] = float(d1[key1][k].replace(",", ""))
                    for k in sorted(d2[key1]):
                        dicTemp2[k] = float(d2[key1][k].replace(",", ""))
                        # data[stock]["PL"]["Q"]["누계영업이익"][k] = float(d2[key1][k].replace(",", ""))
                    for k in sorted(d3[key1]):
                        dicTemp3[k] = float(d3[key1][k].replace(",", ""))
                        # data[stock]["PL"]["Q"]["당기매출액"][k] = float(d3[key1][k].replace(",", ""))
                    for k in sorted(d4[key1]):
                        dicTemp4[k] = float(d4[key1][k].replace(",", ""))
                        # data[stock]["PL"]["Q"]["당기영업이익"][k] = float(d4[key1][k].replace(",", ""))
                    for k in sorted(d8[key1]):
                        dicTemp8[k] = float(d8[key1][k].replace(",", ""))
                        # data[stock]["PL"]["Q"]["당기매출액"][k] = float(d3[key1][k].replace(",", ""))
                    for k in sorted(d9[key1]):
                        dicTemp9[k] = float(d9[key1][k].replace(",", ""))
                        # data[stock]["PL"]["Q"]["당기영업이익"][k] = float(d4[key1][k].replace(",", ""))
                for key2 in d10.keys():
                    current_key = key2
                    if "Rate" in key2: continue
                    for key3 in d10[key2].keys():
                        yhasset = int(d11[key2][key3]) if d11 and key2 in d11.keys() and d11 and key3 in d11[
                            key2].keys() else 0
                        mhasset = int(d12[key2][key3]) if d12 and key2 in d12.keys() and d12 and key3 in d12[
                            key2].keys() else 0
                        data[stock]["CF"]["FCF"][key3] = int(d10[key2][key3]) - (yhasset + mhasset)
            # dicTemp1["최근"] = provision_info[stock]["PL"]["Y"]["매출액"]
            # dicTemp2["최근"] = provision_info[stock]["PL"]["Y"]["영업이익"]
            dicTemp3["최근"] = provision_info[stock]["PL"]["Q"]["매출액"] if "매출액" in provision_info[stock]["PL"][
                "Q"].keys() else 0
            dicTemp4["최근"] = provision_info[stock]["PL"]["Q"]["영업이익"] if "영업이익" in provision_info[stock]["PL"][
                "Q"].keys() else 0
            # dicTemp8["최근"] = provision_info[stock]["PL"]["Y"]["당기순이익"]
            dicTemp9["최근"] = provision_info[stock]["PL"]["Q"]["당기순이익"] if "당기순이익" in provision_info[stock]["PL"][
                "Q"].keys() else 0
            data[stock]["PL"]["Q"]["매출액영업이익률"] = dict(sorted(dicTemp0.items()))
            data[stock]["PL"]["Q"]["누계매출액추이"] = dict(sorted(dicTemp1.items()))
            data[stock]["PL"]["Q"]["누계영업이익추이"] = dict(sorted(dicTemp2.items()))
            data[stock]["PL"]["Q"]["당기매출액"] = dict(sorted(dicTemp3.items()))
            data[stock]["PL"]["Q"]["당기영업이익"] = dict(sorted(dicTemp4.items()))
            data[stock]["PL"]["Q"]["누계당기순이익추이"] = dict(sorted(dicTemp8.items()))
            data[stock]["PL"]["Q"]["당기순이익"] = dict(sorted(dicTemp9.items()))
            # print("MakeAvg1?")
            # print(data)
            data[stock]["AverageRate"]["Y"]["매출액영업이익률"] = round(sum(
                data[stock]["PL"]["Y"]["매출액영업이익률"].values()) / float(
                len(data[stock]["PL"]["Y"]["매출액영업이익률"])), 2) if "매출액영업이익률" in data[stock]["PL"][
                "Y"].keys() else None
            # print("MakeAvg2?")
            data[stock]["AverageRate"]["Y"]["매출액"] = round(sum(
                data[stock]["PL"]["Y"]["매출액"].values()) / float(
                len(data[stock]["PL"]["Y"]["매출액"])), 0) if "매출액" in data[stock]["PL"]["Y"].keys() and \
                                                           len(data[stock]["PL"]["Y"]["매출액"]) != 0 else None
            # print("MakeAvg3?")
            data[stock]["AverageRate"]["Y"]["영업이익"] = round(sum(
                data[stock]["PL"]["Y"]["영업이익"].values()) / float(
                len(data[stock]["PL"]["Y"]["영업이익"])), 0) if "영업이익" in data[stock]["PL"]["Y"].keys() and \
                                                            len(data[stock]["PL"]["Y"]["영업이익"]) != 0 else None
            data[stock]["AverageRate"]["Y"]["당기순이익"] = round(sum(
                data[stock]["PL"]["Y"]["당기순이익"].values()) / float(
                len(data[stock]["PL"]["Y"]["당기순이익"])), 0) if "당기순이익" in data[stock]["PL"]["Y"].keys() and \
                                                             len(data[stock]["PL"]["Y"]["당기순이익"]) != 0 else None
            # print("MakeAvg4?")
            data[stock]["AverageRate"]["Q"]["매출액영업이익률"] = round(sum(
                data[stock]["PL"]["Q"]["매출액영업이익률"].values()) / float(
                len(data[stock]["PL"]["Q"]["매출액영업이익률"])), 2) if "매출액영업이익률" in data[stock]["PL"]["Q"].keys() and \
                                                                len(data[stock]["PL"]["Q"]["매출액영업이익률"]) != 0 else None
            # print("MakeAvg5?")
            data[stock]["AverageRate"]["Q"]["매출액"] = round(sum(
                data[stock]["PL"]["Q"]["당기매출액"].values()) / float(
                len(data[stock]["PL"]["Q"]["당기매출액"])), 0) if "당기매출액" in data[stock]["PL"]["Q"].keys() and \
                                                             len(data[stock]["PL"]["Q"]["당기매출액"]) != 0 else None
            # print("MakeAvg6?")
            data[stock]["AverageRate"]["Q"]["영업이익"] = round(sum(
                data[stock]["PL"]["Q"]["당기영업이익"].values()) / float(
                len(data[stock]["PL"]["Q"]["당기영업이익"])), 0) if "당기영업이익" in data[stock]["PL"]["Q"].keys() and \
                                                              len(data[stock]["PL"]["Q"]["당기영업이익"]) != 0 else None
            data[stock]["AverageRate"]["Q"]["당기순이익"] = round(sum(
                data[stock]["PL"]["Q"]["당기순이익"].values()) / float(
                len(data[stock]["PL"]["Q"]["당기순이익"])), 0) if "당기순이익" in data[stock]["PL"]["Q"].keys() and \
                                                             len(data[stock]["PL"]["Q"]["당기순이익"]) != 0 else None
            # print("MakeAvg7?")
            # 손익계산서 분석 끝
            for key1 in d1.keys():
                if "Rate" in key1: continue
                if d5 is not None and key1 in d5.keys():
                    for k in sorted(d5[key1]):
                        dicTemp5[k] = float(d5[key1][k].replace(",", "")) if d5 is not None else 0
                if d6 is not None and key1 in d6.keys():
                    for k in sorted(d6[key1]):
                        dicTemp6[k] = float(d6[key1][k].replace(",", "")) if d6 is not None else 0
                if d7 is not None and key1 in d7.keys():
                    for k in sorted(d7[key1]):
                        dicTemp7[k] = float(d7[key1][k].replace(",", "")) if d7 is not None else 0
                if d10 is not None and key1 in d10.keys():
                    for k in sorted(d10[key1]):
                        dicTemp10[k] = float(d10[key1][k].replace(",", "")) if d10 is not None else 0
                if d11 is not None and key1 in d11.keys():
                    for k in sorted(d11[key1]):
                        dicTemp11[k] = float(d11[key1][k]) if d11 is not None else 0
                if d12 is not None and key1 in d12.keys():
                    for k in sorted(d12[key1]):
                        dicTemp12[k] = float(d12[key1][k]) if d12 is not None else 0
                data[stock]["FS"]["TotalAsset"] = dict(sorted(dicTemp5.items()))
                data[stock]["FS"]["TotalDebt"] = dict(sorted(dicTemp6.items()))
                data[stock]["FS"]["RetainedEarnings"] = dict(sorted(dicTemp7.items()))
                data[stock]["CF"]["영업활동현금흐름"] = dict(sorted(dicTemp10.items()))
                data[stock]["CF"]["유형자산취득"] = dict(sorted(dicTemp11.items()))
                data[stock]["CF"]["무형자산취득"] = dict(sorted(dicTemp12.items()))
                data[stock]["CF"]["FCF"] = dict(sorted(data[stock]["CF"]["FCF"].items()))
        except Exception as e:
            logger.error(e)
            # logger.error(current_pos)
            logger.error(current_key)
            for key in current_pos.keys():  # key = ["연결재무제표", "재무제표"]
                for report in current_pos[key].keys():  # report = ["재무상태표", "손익계산서"]
                    if report not in ["손익계산서", "포괄손익계산서"]:  # ["재무상태표", "현금흐름표", "자본변동표"]:
                        for acc in current_pos[key][report].keys():
                            # acc = ["유동자산", "비유동자산", "자산총계", "유동부채", "비유동부채", "부채총계", "자본금", "이익잉여금", "자본총계"]
                            for category in sorted(current_pos[key][report][acc].keys()):
                                # category = ["YYYY 1/4", "YYYY 2/4", "YYYY 3/4", "YYYY 4/4"]
                                logger.error("{}\t{}\t{}\t{}\t{}".format(key, report, acc, category,
                                                                         current_pos[key][report][acc][category]))
                                # for k in result[key][report][acc][category].keys():
                                #     print(key, report, acc, category, k, current_pos[key][report][acc][category][k])
                    else:
                        for acc in current_pos[key][report].keys():
                            # acc = ["매출액", 영업이익", "법인세차감전", "당기순이익"]
                            for category in current_pos[key][report][acc].keys():
                                # category = ["누계", "당기"]
                                for k in sorted(current_pos[key][report][acc][category].keys()):
                                    # k = ["YYYY 1/4", "YYYY 2/4", "YYYY 3/4", "YYYY 4/4"]
                                    logger.error("{}\t{}\t{}\t{}\t{}\t{}".format(key, report, acc, category, k,
                                                                                 current_pos[key][report][acc][
                                                                                     category][k]))
    logger.info(data)

    for k in data.keys():
        avg_sales_op_profit_rate = None
        avg_sales = None
        avg_op_profit = None
        avg_net_income = None
        last_sales_op_profit_rate = None
        last_sales = None
        last_op_profit = None
        last_net_income = None
        before_sales = None
        before_op_profit = None
        before_net_income = None

        logger.info("{} {} {}".format(k, data[k]["corp_name"], "*" * 100))
        for key in data[k]["PL"]["Y"].keys():
            logger.info("{} {} {}".format("연간", key, data[k]["PL"]["Y"][key]))
        logger.info("{} {}".format("연간", data[k]["AverageRate"]["Y"]))
        for key in data[k]["PL"]["Q"].keys():
            logger.info("{} {} {}".format("당기", key, data[k]["PL"]["Q"][key]))
        logger.info("{} {}".format("당기", data[k]["AverageRate"]["Q"]))
        logger.info("{} {}".format("재무상태표-자산총계", data[k]["FS"]["TotalAsset"]))
        logger.info("{} {}".format("재무상태표-부채총계", data[k]["FS"]["TotalDebt"]))
        logger.info("{} {}".format("재무상태표-이익잉여금", data[k]["FS"]["RetainedEarnings"]))
        logger.info("{} {}".format("CF-OCF", data[k]["CF"]["영업활동현금흐름"]))
        logger.info("{} {}".format("CF-유형자산취득", data[k]["CF"]["유형자산취득"]))
        logger.info("{} {}".format("CF-무형자산취득", data[k]["CF"]["무형자산취득"]))
        logger.info("{} {}".format("CF-FCF", data[k]["CF"]["FCF"]))
        # print("here1?")
        if "매출액영업이익률" in data[k]["AverageRate"]["Y"].keys() \
                and "매출액" in data[k]["AverageRate"]["Y"].keys() \
                and "영업이익" in data[k]["AverageRate"]["Y"].keys() \
                and "당기순이익" in data[k]["AverageRate"]["Y"].keys():
            # print("here2?")
            avg_sales_op_profit_rate = data[k]["AverageRate"]["Y"]["매출액영업이익률"]
            avg_sales = data[k]["AverageRate"]["Y"]["매출액"]
            avg_op_profit = data[k]["AverageRate"]["Y"]["영업이익"]
            avg_net_income = data[k]["AverageRate"]["Y"]["당기순이익"]

            if "매출액영업이익률" in data[k]["PL"]["Q"].keys():
                # print("here3?")
                last_sales_op_profit_rate = data[k]["PL"]["Q"]["매출액영업이익률"].popitem()[1] if len(
                    data[k]["PL"]["Q"]["매출액영업이익률"]) > 0 else None
                last_sales = data[k]["PL"]["Q"]["누계매출액추이"].popitem()[1] if len(
                    data[k]["PL"]["Q"]["누계매출액추이"]) > 0 else None
                if "매출액" in data[k]["PL"]["Y"].keys():
                    data[k]["PL"]["Y"]["매출액"].popitem() if len(data[k]["PL"]["Y"]["매출액"]) > 0 else None
                    before_sales = data[k]["PL"]["Y"]["매출액"].popitem()[1] if len(
                        data[k]["PL"]["Y"]["매출액"]) > 0 else None
                last_op_profit = data[k]["PL"]["Q"]["누계영업이익추이"].popitem()[1] if len(
                    data[k]["PL"]["Q"]["누계영업이익추이"]) > 0 else None
                if "영업이익" in data[k]["PL"]["Y"].keys():
                    data[k]["PL"]["Y"]["영업이익"].popitem() if len(data[k]["PL"]["Y"]["영업이익"]) > 0 else None
                    before_op_profit = data[k]["PL"]["Y"]["영업이익"].popitem()[1] if len(
                        data[k]["PL"]["Y"]["영업이익"]) > 0 else None
                last_net_income = data[k]["PL"]["Q"]["누계당기순이익추이"].popitem()[1] if len(
                    data[k]["PL"]["Q"]["누계당기순이익추이"]) > 0 else None
                if "당기순이익" in data[k]["PL"]["Y"].keys():
                    data[k]["PL"]["Y"]["당기순이익"].popitem() if len(data[k]["PL"]["Y"]["당기순이익"]) > 0 else None
                    before_net_income = data[k]["PL"]["Y"]["당기순이익"].popitem()[1] if len(
                        data[k]["PL"]["Y"]["당기순이익"]) > 0 else None
        # print("here4?")
        if avg_sales_op_profit_rate and last_sales_op_profit_rate:
            if last_sales_op_profit_rate > 0 and avg_sales_op_profit_rate > 0 and last_sales_op_profit_rate > avg_sales_op_profit_rate:
                # print("here5?")
                if avg_sales and last_sales and before_sales and \
                        avg_net_income and last_net_income and before_net_income and \
                        last_sales > avg_sales and last_sales > before_sales and \
                        last_net_income > avg_net_income and last_net_income > before_net_income:
                    if last_sales_op_profit_rate > 20:
                        best[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "업종": data[k]["category"],
                                   "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                   "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                   "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                   "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                   "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                   "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                   "직전영업이익": format(before_op_profit,
                                                    ",") if before_op_profit is not None else None,
                                   "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                   "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                   "직전당기순이익": format(before_net_income,
                                                     ",") if before_net_income is not None else None,
                                   "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None
                                   }
                        call = json.loads(requests.get(
                            "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                                k)).content.decode("utf-8"))
                        best[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                        best[k]["PER"] = call["per"]
                        best[k]["EPS"] = call["eps"]
                        best[k]["PBR"] = call["pbr"]
                        best[k]["현재가"] = f'{call["now"]:,}'
                        best[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                data[k][
                                                                                                    "list_shares"] else 0
                        best[k]["PER2"] = round(call["now"] / best[k]["EPS2"], 0) if best[k]["EPS2"] != 0 else 0
                        best[k]["예상주가"] = format(int(round(best[k]["EPS2"] * best[k]["PER"], 0)), ",") if best[k][
                                                                                                              "EPS2"] and \
                                                                                                          best[k][
                                                                                                              "PER"] else 0
                    elif np.sign(last_sales_op_profit_rate) > np.sign(avg_sales_op_profit_rate):
                        best[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "업종": data[k]["category"],
                                   "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                   "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                   "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                   "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                   "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                   "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                   "직전영업이익": format(before_op_profit,
                                                    ",") if before_op_profit is not None else None,
                                   "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                   "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                   "직전당기순이익": format(before_net_income,
                                                     ",") if before_net_income is not None else None,
                                   "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None}
                        call = json.loads(requests.get(
                            "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                                k)).content.decode("utf-8"))
                        best[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                        best[k]["PER"] = call["per"]
                        best[k]["EPS"] = call["eps"]
                        best[k]["PBR"] = call["pbr"]
                        best[k]["현재가"] = f'{call["now"]:,}'
                        best[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                data[k][
                                                                                                    "list_shares"] else 0
                        best[k]["PER2"] = round(call["now"] / best[k]["EPS2"], 0) if best[k]["EPS2"] != 0 else 0
                        best[k]["예상주가"] = format(int(round(best[k]["EPS2"] * best[k]["PER"], 0)), ",") if best[k][
                                                                                                              "EPS2"] and \
                                                                                                          best[k][
                                                                                                              "PER"] else 0
                    else:
                        better[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "업종": data[k]["category"],
                                     "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                     "최근매출액영업이익률": last_sales_op_profit_rate,
                                     "평균매출액영업이익률": avg_sales_op_profit_rate,
                                     "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                     "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                     "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                     "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                     "직전영업이익": format(before_op_profit,
                                                      ",") if before_op_profit is not None else None,
                                     "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                     "최근당기순이익": format(last_net_income,
                                                       ",") if last_net_income is not None else None,
                                     "직전당기순이익": format(before_net_income,
                                                       ",") if before_net_income is not None else None,
                                     "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None
                                     }
                        call = json.loads(requests.get(
                            "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                                k)).content.decode("utf-8"))
                        better[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                        better[k]["PER"] = call["per"]
                        better[k]["EPS"] = call["eps"]
                        better[k]["PBR"] = call["pbr"]
                        better[k]["현재가"] = f'{call["now"]:,}'
                        better[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                  data[k][
                                                                                                      "list_shares"] else 0
                        better[k]["PER2"] = round(call["now"] / better[k]["EPS2"], 0) if better[k]["EPS2"] != 0 else 0
                        better[k]["예상주가"] = format(int(round(better[k]["EPS2"] * better[k]["PER"], 0)), ",") if \
                        better[k][
                            "EPS2"] and \
                        better[k][
                            "PER"] else 0
                else:
                    if last_sales_op_profit_rate > 15:
                        better[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "업종": data[k]["category"],
                                     "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                     "최근매출액영업이익률": last_sales_op_profit_rate,
                                     "평균매출액영업이익률": avg_sales_op_profit_rate,
                                     "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                     "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                     "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                     "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                     "직전영업이익": format(before_op_profit,
                                                      ",") if before_op_profit is not None else None,
                                     "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                     "최근당기순이익": format(last_net_income,
                                                       ",") if last_net_income is not None else None,
                                     "직전당기순이익": format(before_net_income,
                                                       ",") if before_net_income is not None else None,
                                     "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None
                                     }
                        call = json.loads(requests.get(
                            "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                                k)).content.decode("utf-8"))
                        better[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                        better[k]["PER"] = call["per"]
                        better[k]["EPS"] = call["eps"]
                        better[k]["PBR"] = call["pbr"]
                        better[k]["현재가"] = f'{call["now"]:,}'
                        better[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                  data[k][
                                                                                                      "list_shares"] else 0
                        better[k]["PER2"] = round(call["now"] / better[k]["EPS2"], 0) if better[k]["EPS2"] != 0 else 0
                        better[k]["예상주가"] = format(int(round(better[k]["EPS2"] * better[k]["PER"], 0)), ",") if \
                        better[k][
                            "EPS2"] and \
                        better[k][
                            "PER"] else 0
                    else:
                        # print("here7?")
                        good[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "업종": data[k]["category"],
                                   "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                   "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                   "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                   "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                   "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                   "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                   "직전영업이익": format(before_op_profit,
                                                    ",") if before_op_profit is not None else None,
                                   "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                   "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                   "직전당기순이익": format(before_net_income,
                                                     ",") if before_net_income is not None else None,
                                   "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None
                                   }
                        call = json.loads(requests.get(
                            "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                                k)).content.decode("utf-8"))
                        good[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                        good[k]["PER"] = call["per"]
                        good[k]["EPS"] = call["eps"]
                        good[k]["PBR"] = call["pbr"]
                        good[k]["현재가"] = f'{call["now"]:,}'
                        good[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                                data[k][
                                                                                                    "list_shares"] else 0
                        good[k]["PER2"] = round(call["now"] / good[k]["EPS2"], 0) if good[k]["EPS2"] != 0 else 0
                        good[k]["예상주가"] = format(int(round(good[k]["EPS2"] * good[k]["PER"], 0)), ",") if good[k][
                                                                                                              "EPS2"] and \
                                                                                                          good[k][
                                                                                                              "PER"] else 0
            else:
                if last_sales_op_profit_rate > 15:
                    better[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "업종": data[k]["category"],
                                 "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                                 "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                                 "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                                 "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                                 "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                                 "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                                 "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                                 "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                                 "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                                 "직전당기순이익": format(before_net_income,
                                                   ",") if before_net_income is not None else None,
                                 "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None
                                 }
                    call = json.loads(requests.get(
                        "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                            k)).content.decode("utf-8"))
                    better[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                    better[k]["PER"] = call["per"]
                    better[k]["EPS"] = call["eps"]
                    better[k]["PBR"] = call["pbr"]
                    better[k]["현재가"] = f'{call["now"]:,}'
                    better[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                              data[k][
                                                                                                  "list_shares"] else 0
                    better[k]["PER2"] = round(call["now"] / better[k]["EPS2"], 0) if better[k]["EPS2"] != 0 else 0
                    better[k]["예상주가"] = format(int(round(better[k]["EPS2"] * better[k]["PER"], 0)), ",") if better[k][
                                                                                                                "EPS2"] and \
                                                                                                            better[k][
                                                                                                                "PER"] else 0
                else:
                    soso[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "업종": data[k]["category"],
                               "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                               "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                               "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                               "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                               "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                               "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                               "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                               "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                               "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                               "직전당기순이익": format(before_net_income, ",") if before_net_income is not None else None,
                               "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None
                               }
                    call = json.loads(requests.get(
                        "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                            k)).content.decode("utf-8"))
                    soso[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
                    soso[k]["PER"] = call["per"]
                    soso[k]["EPS"] = call["eps"]
                    soso[k]["PBR"] = call["pbr"]
                    soso[k]["현재가"] = f'{call["now"]:,}'
                    soso[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                            data[k][
                                                                                                "list_shares"] else 0
                    soso[k]["PER2"] = round(call["now"] / soso[k]["EPS2"], 0) if soso[k]["EPS2"] != 0 else 0
                    soso[k]["예상주가"] = format(int(round(soso[k]["EPS2"] * soso[k]["PER"], 0)), ",") if soso[k][
                                                                                                          "EPS2"] and \
                                                                                                      soso[k][
                                                                                                          "PER"] else 0
        else:
            soso[k] = {"stock_code": k, "corp_name": data[k]["corp_name"], "업종": data[k]["category"],
                       "corp_code": data[k]["corp_code"], "상장주식수": data[k]["list_shares"],
                       "최근매출액영업이익률": last_sales_op_profit_rate, "평균매출액영업이익률": avg_sales_op_profit_rate,
                       "최근매출액": format(last_sales, ",") if last_sales is not None else None,
                       "직전매출액": format(before_sales, ",") if before_sales is not None else None,
                       "평균매출액": format(avg_sales, ",") if avg_sales is not None else None,
                       "최근영업이익": format(last_op_profit, ",") if last_op_profit is not None else None,
                       "직전영업이익": format(before_op_profit, ",") if before_op_profit is not None else None,
                       "평균영업이익": format(avg_op_profit, ",") if avg_op_profit is not None else None,
                       "최근당기순이익": format(last_net_income, ",") if last_net_income is not None else None,
                       "직전당기순이익": format(before_net_income, ",") if before_net_income is not None else None,
                       "평균당기순이익": format(avg_net_income, ",") if avg_net_income is not None else None
                       }
            call = json.loads(requests.get(
                "https://api.finance.naver.com/service/itemSummary.nhn?itemcode={}".format(
                    k)).content.decode("utf-8"))
            soso[k]["시가총액"] = f'{call["marketSum"] * 1000000:,}'
            soso[k]["PER"] = call["per"]
            soso[k]["EPS"] = call["eps"]
            soso[k]["PBR"] = call["pbr"]
            soso[k]["현재가"] = f'{call["now"]:,}'
            soso[k]["EPS2"] = round(last_net_income / data[k]["list_shares"], 0) if last_net_income and \
                                                                                    data[k][
                                                                                        "list_shares"] else 0
            soso[k]["PER2"] = round(call["now"] / soso[k]["EPS2"], 0) if soso[k]["EPS2"] != 0 else 0
            soso[k]["예상주가"] = format(int(round(soso[k]["EPS2"] * soso[k]["PER"], 0)), ",") if soso[k]["EPS2"] and \
                                                                                              soso[k][
                                                                                                  "PER"] else 0
            # info_lack[k] = {"corp_name": data[k]["corp_name"], "corp_code": data[k]["corp_code"]}
    logger.info("{} {} {} {}".format("*" * 100, "BEST", len(best), "*" * 100))
    for key in best.keys():
        logger.info(best[key])
        if best[key]["EPS2"] != 0 and best[key]["EPS2"] > best[key]["EPS"] and (best[key]["EPS2"] - best[key]["EPS"]) / \
                best[key]["EPS"] * 100 >= 30:
            if "BEST" not in treasure.keys():
                treasure["BEST"] = {}
            treasure["BEST"][key] = {"사명": best[key]["corp_name"], "시가총액": best[key]["시가총액"], "업종": best[key]["업종"],
                                     "최근매출액영업이익률": best[key]["최근매출액영업이익률"], "EPS": best[key]["EPS"],
                                     "추정EPS": best[key]["EPS2"],
                                     "괴리율": round((best[key]["EPS2"] - best[key]["EPS"]) / best[key]["EPS"] * 100, 2),
                                     "현재가": best[key]["현재가"], "예상주가": best[key]["예상주가"]}
    logger.info("{} {} {} {}".format("*" * 100, "BETTER", len(better), "*" * 100))
    for key in better.keys():
        logger.info(better[key])
        if better[key]["EPS2"] != 0 and better[key]["EPS2"] > better[key]["EPS"] and (
                better[key]["EPS2"] - better[key]["EPS"]) / better[key]["EPS"] * 100 >= 30:
            if "BETTER" not in treasure.keys():
                treasure["BETTER"] = {}
            treasure["BETTER"][key] = {"사명": better[key]["corp_name"], "시가총액": better[key]["시가총액"],
                                       "업종": better[key]["업종"], "최근매출액영업이익률": better[key]["최근매출액영업이익률"],
                                       "EPS": better[key]["EPS"], "추정EPS": better[key]["EPS2"], "괴리율": round(
                    (better[key]["EPS2"] - better[key]["EPS"]) / better[key]["EPS"] * 100, 2),
                                       "현재가": better[key]["현재가"], "예상주가": better[key]["예상주가"]}
    logger.info("{} {} {} {}".format("*" * 100, "GOOD", len(good), "*" * 100))
    for key in good.keys():
        logger.info(good[key])
        if good[key]["EPS2"] != 0 and good[key]["EPS2"] > good[key]["EPS"] and (good[key]["EPS2"] - good[key]["EPS"]) / \
                good[key]["EPS"] * 100 >= 30:
            if "GOOD" not in treasure.keys():
                treasure["GOOD"] = {}
            treasure["GOOD"][key] = {"사명": good[key]["corp_name"], "시가총액": good[key]["시가총액"], "업종": good[key]["업종"],
                                     "최근매출액영업이익률": good[key]["최근매출액영업이익률"], "EPS": good[key]["EPS"],
                                     "추정EPS": good[key]["EPS2"],
                                     "괴리율": round((good[key]["EPS2"] - good[key]["EPS"]) / good[key]["EPS"] * 100, 2),
                                     "현재가": good[key]["현재가"], "예상주가": good[key]["예상주가"]}
    logger.info("{} {} {} {}".format("*" * 100, "CHECK", len(soso), "*" * 100))
    for key in soso.keys():
        logger.info(soso[key])
        if soso[key]["EPS2"] != 0 and soso[key]["EPS2"] > soso[key]["EPS"] and (soso[key]["EPS2"] - soso[key]["EPS"]) / \
                soso[key]["EPS"] * 100 >= 30:
            if "SOSO" not in treasure.keys():
                treasure["SOSO"] = {}
            treasure["SOSO"][key] = {"사명": soso[key]["corp_name"], "시가총액": soso[key]["시가총액"], "업종": soso[key]["업종"],
                                     "최근매출액영업이익률": soso[key]["최근매출액영업이익률"], "EPS": soso[key]["EPS"],
                                     "추정EPS": soso[key]["EPS2"],
                                     "괴리율": round((soso[key]["EPS2"] - soso[key]["EPS"]) / soso[key]["EPS"] * 100, 2),
                                     "현재가": soso[key]["현재가"], "예상주가": soso[key]["예상주가"]}
    return treasure


def dataInit():
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
        detective_db.TargetStocks.objects.update(plus_npv='N')
    except Exception as e:
        print("TargetStocks data initialization Failed with", e)


def USDataInit():
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
        detective_db.USTargetStocks.objects.update(plus_npv='N')
    except Exception as e:
        print("TargetStocks data initialization Failed with", e)


def TargetStockDataDelete(yyyymmdd):
    import sys
    import os
    import django
    from datetime import datetime
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    try:
        info = detective_db.TargetStocks.objects.filter(valuation_date=yyyymmdd).delete()

        print("[TargetStocks][{}] information Deleted successfully".format(yyyymmdd))
        # print("[{}][{}][{}] information stored successfully".format(report_name, crp_cd, crp_nm))
    except Exception as e:
        print('[Error on TargetStockDataDelete]\n', '*' * 50, e)


def USTargetStockDataDelete(yyyymmdd):
    import sys
    import os
    import django
    from datetime import datetime
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    try:
        info = detective_db.USTargetStocks.objects.filter(valuation_date=yyyymmdd).delete()

        print("[USTargetStocks][{}] information Deleted successfully".format(yyyymmdd))
        # print("[{}][{}][{}] information stored successfully".format(report_name, crp_cd, crp_nm))
    except Exception as e:
        print('[Error on USTargetStockDataDelete]\n', '*' * 50, e)


def TargetStockDataStore(crp_cd, data):
    import sys
    import os
    import django
    from datetime import datetime
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    try:
        info = detective_db.TargetStocks.objects.update_or_create(code=crp_cd,
                                                                  valuation_date=yyyymmdd,
                                                                  defaults={
                                                                      'name': data['회사명'],
                                                                      'curr': data['통화'],
                                                                      'last_price': data['종가'],
                                                                      'price_gap': data['전일대비'],
                                                                      'target_price': data['NPV'],
                                                                      'target_price2': data['NPV2'],
                                                                      'required_yield': data['요구수익률'],
                                                                      'return_on_equity': data['ROE'],
                                                                      'ratio': data['NPV'] / data['종가'] * 100,
                                                                      'plus_npv': 'Y',
                                                                      'holders_share': data['지배주주지분'],
                                                                      'holders_value': data['주주가치'],
                                                                      'holders_profit': data['지배주주순이익'],
                                                                      'issued_shares': data['발행주식수'],
                                                                      # 'valuation_date': yyyymmdd,
                                                                      'return_on_sales': data['ROS'],
                                                                      'liquidity_rate': data['비율'],
                                                                      'foreign_holding': data['외국인 보유비중'],
                                                                      'trade_amount': data['거래량'],
                                                                      # 'impairment_profit': data['중단영업이익'],
                                                                  }
                                                                  )

        print("[TargetStocks][{}][{}] information stored successfully".format(crp_cd, data['회사명']))
        # print("[{}][{}][{}] information stored successfully".format(report_name, crp_cd, crp_nm))
    except Exception as e:
        print('[Error on TargetStockDataStore]\n', '*' * 50, e)


def USTargetStockDataStore(crp_cd, data):
    import sys
    import os
    import django
    from datetime import datetime
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    try:
        info = detective_db.USTargetStocks.objects.update_or_create(code=crp_cd,
                                                                    valuation_date=yyyymmdd,
                                                                    defaults={
                                                                        'name': data['Name'],
                                                                        'curr': 'USD',
                                                                        'last_price': data['종가'],
                                                                        'price_gap': data['전일대비'],
                                                                        'target_price': data['NPV'],
                                                                        'target_price2': None,
                                                                        'required_yield': data['요구수익률'],
                                                                        'return_on_equity': data['ROE'],
                                                                        'ratio': data['NPV'] / data['종가'] * 100,
                                                                        'plus_npv': 'Y',
                                                                        'holders_share': data['자산총계'],
                                                                        'holders_value': data['주주가치'],
                                                                        'holders_profit': data['당기순이익'],
                                                                        'issued_shares': data['발행주식수'],
                                                                        # 'valuation_date': yyyymmdd,
                                                                        'return_on_sales': None,
                                                                        'liquidity_rate': None,
                                                                        'foreign_holding': None,
                                                                        'trade_amount': data['거래량'],
                                                                        # 'impairment_profit': data['중단영업이익'],
                                                                    }
                                                                    )

        print("[USTargetStocks][{}][{}] information stored successfully".format(crp_cd, data['Name']))
        # print("[{}][{}][{}] information stored successfully".format(report_name, crp_cd, crp_nm))
    except Exception as e:
        print('[Error on USTargetStockDataStore]\n', '*' * 50, e)


def test():
    import sys
    import os
    import django

    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    DEBUG = True
    dateDict = new_get_dateDict()
    treasure = {}
    yyyymmdd = '2020-11-30'
    import detective_app.models as detective_db
    stockInfo = detective_db.Stocks.objects.filter(code='199820', listing='Y')  # 삼성전자
    print(align_string('L', 'No.', 10),
          align_string('R', 'Code', 10),
          align_string('R', 'Name', 20),
          align_string('R', 'Issued Shares', 20),
          align_string('R', 'Capital', 20),
          align_string('R', 'ParValue', 10),
          align_string('R', 'Currency', 10),
          '\n')

    for ii, stock in enumerate(stockInfo):
        data = {}
        print(align_string('L', ii + 1, 10),
              align_string('R', stock.code, 10),
              align_string('R', stock.name, 20 - len(stock.name)),
              align_string(',', stock.issued_shares, 20),
              align_string(',', stock.capital, 20),
              align_string('R', stock.par_value, 10),
              align_string('R', stock.curr, 10),
              )
        dic = get_soup_from_file('ROE', yyyymmdd, stock.name, stock.code, 'json')
        # if DEBUG: print(dic)
        for key in dic:
            if '04' == key:
                # 해당 종목의 ROE 가 없으면 당해년 Estimation 이 없는 것으로 정확한 가치평가 불가하므로 제외
                if len(dic[key]) == 3:
                    data['요구수익률'] = 0 if dic[key][-2]['VAL3'] == '-' else float(dic[key][-2]['VAL3'])
                    data['요구수익률2'] = 0 if dic[key][-1]['VAL3'] == '-' else float(dic[key][-1]['VAL3'])
                else:
                    data['요구수익률'] = 0 if dic[key][-1]['VAL3'] == '-' else float(dic[key][-1]['VAL3'])
                    data['요구수익률2'] = data['요구수익률']
                # if DEBUG: print(data['요구수익률'], data['요구수익률2'])

        data['회사명'] = stock.name
        data['발행주식수'] = stock.issued_shares
        data['자본금'] = stock.capital
        data['액면가'] = stock.par_value
        data['통화'] = 'KRW' if stock.curr == '' else stock.curr
        soup = get_soup_from_file('snapshot', yyyymmdd, stock.name, stock.code, 'html')

        marketTxt = fnguide.select_by_attr(soup, 'span', 'class', 'stxt stxt1').text.replace(' ', '')  # 업종분류
        data['업종구분'] = marketTxt.replace('\n', '')
        marketTxt = fnguide.select_by_attr(soup, 'span', 'class', 'stxt stxt2').text.replace(' ', '')  # 업종분류
        data['업종구분상세'] = marketTxt.replace('\n', '')
        sttl_month = fnguide.select_by_attr(soup, 'span', 'class', 'stxt stxt3').text.replace(' ', '')  # 업종분류
        data['결산월'] = sttl_month.replace('\n', '')
        # print(data['업종구분'], data['업종구분상세'], stock.market_text)
        if (data['업종구분'] != '' and stock.market_text is None) or (
                data['업종구분상세'] != '' and stock.market_text_detail is None):
            fnguide.StockMarketTextUpdate(stock.code, data['업종구분'], data['업종구분상세'], data['결산월'])

        yearly_highlight = fnguide.select_by_attr(soup, 'div', 'id', 'highlight_D_Y')  # Snapshot FinancialHighlight
        # print(yearly_highlight)
        if yearly_highlight:
            columns, items, values = fnguide.setting(
                fnguide.get_table_contents(yearly_highlight, 'table thead tr th')[1:],
                fnguide.get_table_contents(yearly_highlight, 'table tbody tr th'),
                fnguide.get_table_contents(yearly_highlight, 'table tbody tr td'))
            # if DEBUG: print(columns, items, values)
            for idx, i in enumerate(items):
                if i in ['지배주주순이익', '지배주주지분', '자산총계', '매출액', '이자수익', '보험료수익', '순영업수익', '영업수익', '유보율(%)', '부채비율(%)']:
                    for idx2, yyyymm in enumerate(columns):
                        # print(idx2, yyyymm)
                        # print(yyyymm[:4], dateDict['yyyy'], i, values[idx][idx2])
                        if yyyymm[:4] == dateDict['yyyy'] and values[idx][idx2] != '':
                            data['Period'] = yyyymm
                            if i[-3:] == '(%)':
                                if fnguide.is_float(values[idx][idx2].replace(',', '')):
                                    data[i] = float(values[idx][idx2].replace(',', ''))
                                else:
                                    data[i] = 0
                                if values[idx][idx2 - 1] != '' and fnguide.is_float(
                                        values[idx][idx2 - 1].replace(',', '')):
                                    data['X' + i] = float(values[idx][idx2 - 1].replace(',', ''))
                                else:
                                    data['X' + i] = 0
                                break
                            else:
                                if fnguide.is_float(values[idx][idx2].replace(',', '')):
                                    data[i] = float(values[idx][idx2].replace(',', '')) * 100000000
                                else:
                                    data[i] = 0
                                if values[idx][idx2 - 1] != '' and fnguide.is_float(
                                        values[idx][idx2 - 1].replace(',', '')):
                                    data['X' + i] = float(values[idx][idx2 - 1].replace(',', '')) * 100000000
                                else:
                                    data['X' + i] = 0
                                break

                        else:
                            if values[idx][idx2 - 1] != '' and fnguide.is_float(
                                    values[idx][idx2 - 1].replace(',', '')):
                                if i[-3:] == '(%)':
                                    data['X' + i] = float(values[idx][idx2 - 1].replace(',', ''))
                                else:
                                    data['X' + i] = float(values[idx][idx2 - 1].replace(',', '')) * 100000000
                            else:
                                continue
                elif i in ['ROE(%)']:
                    for idx2, yyyymm in enumerate(columns):
                        # print(idx2, yyyymm)
                        # print(yyyymm[:4], dateDict['yyyy'], values[idx][idx2])
                        if yyyymm[:4] == dateDict['yyyy'] and values[idx][idx2] != '':
                            data['Period'] = yyyymm
                            if fnguide.is_float(values[idx][idx2].replace(',', '')):
                                pass
                            else:
                                data['확인사항'] = values[idx][idx2].replace(',', '')
                            break
                        elif yyyymm[:4] == dateDict['yyyy'] and values[idx][idx2] == '':
                            data['Period'] = columns[idx2 - 1]
                            if fnguide.is_float(values[idx][idx2 - 1].replace(',', '')):
                                pass
                            else:
                                data['확인사항'] = values[idx][idx2 - 1].replace(',', '')
                            break
                        else:
                            continue

            if not set(['지배주주순이익', '지배주주지분', '자산총계']).issubset(data.keys()):
                yearly_highlight = fnguide.select_by_attr(soup, 'div', 'id',
                                                          'highlight_B_Y')  # Snapshot FinancialHighlight
                # print(yearly_highlight)
                if yearly_highlight:
                    columns, items, values = fnguide.setting(
                        fnguide.get_table_contents(yearly_highlight, 'table thead tr th')[1:],
                        fnguide.get_table_contents(yearly_highlight, 'table tbody tr th'),
                        fnguide.get_table_contents(yearly_highlight, 'table tbody tr td'))
                    # if DEBUG: print(columns, items, values)
                    # print(fnguide.get_table_contents_test(yearly_highlight, 'table thead tr th')[1:])
                    # print(fnguide.get_table_contents_test(yearly_highlight, 'table tbody tr th'))
                    # print(fnguide.get_table_contents_test(yearly_highlight, 'table tbody tr td'))
                    # print(items)
                    # print(values)
                    for idx, i in enumerate(items):
                        if i in ['당기순이익', '자본총계', '자산총계', '매출액', '이자수익', '보험료수익', '순영업수익', '영업수익', '유보율(%)', '부채비율(%)',
                                 '영업이익(발표기준)']:
                            for idx2, yyyymm in enumerate(columns):
                                # print(idx2, yyyymm)
                                # print(yyyymm[:4], dateDict['yyyy'], i, values[idx][idx2])
                                if yyyymm[:4] == dateDict['yyyy'] and values[idx][idx2] != '':
                                    data['Period'] = yyyymm
                                    if i[-3:] == '(%)':
                                        if fnguide.is_float(values[idx][idx2].replace(',', '')):
                                            data[i] = float(values[idx][idx2].replace(',', ''))
                                        else:
                                            data[i] = 0
                                        if values[idx][idx2 - 1] != '' and fnguide.is_float(
                                                values[idx][idx2 - 1].replace(',', '')):
                                            data['X' + i] = float(values[idx][idx2 - 1].replace(',', ''))
                                        else:
                                            data['X' + i] = 0
                                        break
                                    else:
                                        if fnguide.is_float(values[idx][idx2].replace(',', '')):
                                            data[i] = float(values[idx][idx2].replace(',', '')) * 100000000
                                        else:
                                            data[i] = 0
                                        if values[idx][idx2 - 1] != '' and fnguide.is_float(
                                                values[idx][idx2 - 1].replace(',', '')):
                                            data['X' + i] = float(values[idx][idx2 - 1].replace(',', '')) * 100000000
                                        else:
                                            data['X' + i] = 0
                                        break

                                else:
                                    # print(idx, idx2)
                                    # print(values)
                                    if values[idx][idx2 - 1] != '' and fnguide.is_float(
                                            values[idx][idx2 - 1].replace(',', '')):
                                        if i[-3:] == '(%)':
                                            data['X' + i] = float(values[idx][idx2 - 1].replace(',', ''))
                                        else:
                                            data['X' + i] = float(values[idx][idx2 - 1].replace(',', '')) * 100000000
                                    else:
                                        continue
                        elif i in ['ROE(%)']:
                            for idx2, yyyymm in enumerate(columns):
                                # print(idx2, yyyymm)
                                # print(yyyymm[:4], dateDict['yyyy'], values[idx][idx2])
                                if yyyymm[:4] == dateDict['yyyy'] and values[idx][idx2] != '':
                                    data['Period'] = yyyymm
                                    if fnguide.is_float(values[idx][idx2].replace(',', '')):
                                        pass
                                    else:
                                        data['확인사항'] = values[idx][idx2].replace(',', '')
                                    break
                                elif yyyymm[:4] == dateDict['yyyy'] and values[idx][idx2] == '':
                                    data['Period'] = columns[idx2 - 1]
                                    if fnguide.is_float(values[idx][idx2 - 1].replace(',', '')):
                                        pass
                                    else:
                                        data['확인사항'] = values[idx][idx2 - 1].replace(',', '')
                                    break
                                else:
                                    continue
                if '당기순이익' in data.keys():
                    data['지배주주순이익'] = data['당기순이익']
                if '자본총계' in data.keys():
                    data['지배주주지분'] = data['자본총계']
            if not set(['지배주주순이익', '지배주주지분', '자산총계']).issubset(data.keys()):
                pass_reason = '[{}][{}] Not enough Information for valuation 2차'.format(stock.code, stock.name)
                continue
            daily = fnguide.select_by_attr(soup, 'div', 'id', 'svdMainGrid1')  # Snapshot 시세현황1
            columns, items, values = fnguide.setting(
                fnguide.get_table_contents(daily, 'table thead tr th')[1:],
                fnguide.get_table_contents(daily, 'table tbody tr th'),
                fnguide.get_table_contents(daily, 'table tbody tr td'))
            # if DEBUG: print(columns, items, values)
            for idx, col in enumerate(columns):
                print(col, values[idx])
                if col.strip() in ['종가', '외국인 보유비중', '비율', '거래량', '전일대비']:
                    if col.strip() == '전일대비':
                        tmp = values[idx].replace(' ', '').replace('+', '△ ').replace('-', '▽ ').replace(',', '')
                        tmp2 = tmp.split(' ')
                        if tmp == '' or tmp2[1] == '0':
                            data[col.strip()] = "-"
                        else:
                            pct = round(float(tmp2[1]) / (data['종가'] - float(tmp2[1])) * 100, 2)
                            data[col.strip()] = "{}{}%".format(tmp2[0], pct)
                    else:
                        data[col] = float(values[idx].replace(',', '')) if (
                                values[idx] is not None and values[idx] != '') else 0.0
                    # break
                # if col in ['발행주식수-보통주']: print(values[idx] == '')
                if col in ['발행주식수-보통주'] and values[idx] != '' and data['발행주식수'] != float(values[idx].replace(',', '')):
                    print("[{}][{}]발행주식수가 다릅니다. {} <> {}".format(stock.code, stock.name, stock.issued_shares,
                                                                 float(values[idx].replace(',', ''))))
                    data['발행주식수'] = float(values[idx].replace(',', ''))

            fwd_summary = fnguide.select_by_attr(soup, 'div', 'id', 'corp_group2')  # Snapshot section ul_corpinfo
            summary_title = []
            summary_data = []
            if fwd_summary:
                for tag in fwd_summary.select('dl'):
                    if tag.dt.text.strip() != '' and tag.dt.text.strip() != '\n':
                        # print(tag.dt.text.strip())
                        summary_title.append(tag.dt.text.strip())
                for tag in fwd_summary.select('dl dd'):
                    try:
                        # print(tag.text.strip())
                        float(tag.text.strip().replace(',', ''))
                        summary_data.append(float(tag.text.strip().replace(',', '')))
                    except Exception as e:
                        # print('[Error]', tag.text.strip())
                        if '%' in tag.text.strip():
                            summary_data.append(tag.text.strip())
                            # summary_data.append(float(tag.text.strip().replace('%', '')) * 0.01)
                        elif '-' == tag.text.strip():
                            summary_data.append(0)
                        else:
                            continue
            # print(fwd_summary)
            # print(summary_title)
            # print(summary_data)
            if fwd_summary and summary_title:
                for idx, title in enumerate(summary_title):
                    data[title] = summary_data[idx]
                    # print(title, summary_data[idx])
            adjval = data['업종 PER'] * data['PBR(Price Book-value Ratio)']
            if '매출액' not in data.keys():
                data['매출액'] = data['이자수익'] if '이자수익' in data.keys() else data[
                    '보험료수익'] if '보험료수익' in data.keys() else data['순영업수익'] if '순영업수익' in data.keys() else data[
                    '영업수익'] if '영업수익' in data.keys() else 0
            if data['매출액'] == 0: continue
            if data['요구수익률'] == 0: data['요구수익률'] = 10.0
            if DEBUG: print("data['지배주주지분']", data['지배주주지분'])
            if DEBUG: print("data['요구수익률']", data['요구수익률'])
            if DEBUG: print("data['발행주식수']", data['발행주식수'])
            if DEBUG: print("data['자산총계']", data['자산총계'])
            if DEBUG: print("data['매출액']", data['매출액'])
            if DEBUG: print("data['유보율']", data['X유보율(%)'])
            if DEBUG: print("data['부채비율']", data['부채비율(%)'])
            if 'X지배주주순이익' not in data.keys(): data['X지배주주순이익'] = 0.0
            if data['지배주주지분'] == 0:
                data['ROE'] = 0.0
            else:
                data['ROE'] = data['지배주주순이익'] / data['지배주주지분'] * 100

            data['주주가치'] = data['지배주주지분'] + (
                    data['지배주주지분'] * (data['ROE'] - data['요구수익률']) / (data['요구수익률']))
            data['NPV'] = data['주주가치'] / data['발행주식수']
            data['NPV2'] = (data['주주가치'] * (data['지배주주지분'] / data['자산총계'])) / data['발행주식수']
            data['ROS'] = data['지배주주순이익'] / data['매출액'] * 100

            print(data)
            treasure[stock.code] = data
    print('=' * 50, '마이너스', '=' * 50)
    print(align_string('L', 'No.', 5),
          align_string('R', 'Code', 10),
          align_string('R', 'Name', 20),
          # align_string('R', 'X지배주주순이익', 20),
          align_string('R', '요구수익률', 15),
          align_string('R', 'ROE', 20),
          align_string('R', 'ROS', 20),
          align_string('R', '12M PER', 8),
          align_string('R', '업종 PER', 8),
          align_string('R', '지배주주지분', 14),
          align_string('R', '주주가치', 16),
          align_string('R', 'NPV', 20),
          align_string('R', '종가', 10),
          align_string('R', '확인사항', 16),
          )
    cnt = 0
    print(treasure)
    for d in treasure.keys():
        if treasure[d]['ROE'] < 15 or \
                treasure[d]['ROE'] < treasure[d]['요구수익률'] or \
                treasure[d]['업종구분'].replace('\n', '').replace('KSE', '').replace('KOSDAQ', '').replace(' ', '') in [
            '코스닥제조', '코스피제조업', '코스피건설업', '코스닥건설'] or \
                treasure[d]['지배주주지분'] / treasure[d]['자산총계'] < 0.51 or \
                treasure[d]['NPV'] < 0 or \
                treasure[d]['NPV'] / treasure[d]['종가'] * 100 < 105:
            cnt += 1
            print(align_string('L', cnt, 5),
                  align_string('R', d, 10),
                  align_string('R', treasure[d]['회사명'], 20 - len(treasure[d]['회사명'])),
                  # align_string(',', round(treasure[d]['X지배주주순이익'], 2), 20),
                  align_string(',', round(treasure[d]['요구수익률'], 2), 20),
                  align_string(',', round(treasure[d]['ROE'], 2), 20),
                  align_string(',', round(treasure[d]['ROS'], 2), 20),
                  align_string(',', treasure[d]['12M PER'], 8),
                  align_string(',', treasure[d]['업종 PER'], 8),
                  align_string(',', round(treasure[d]['지배주주지분'], 0), 20),
                  align_string(',', round(treasure[d]['주주가치'], 0), 20),
                  align_string(',', round(treasure[d]['NPV'], 0), 20),
                  align_string(',', treasure[d]['종가'], 10),
                  align_string('R', '' if '확인사항' not in treasure[d].keys() else treasure[d]['확인사항'], 20),
                  )
            if treasure[d]['ROE'] < 15 or treasure[d]['ROE'] < treasure[d]['요구수익률']:
                pass_reason = "[{}][{}]['ROE'] < 15 또는 ['ROE'] < ['요구수익률'] => ROE : {} / 요구수익률 : {}".format(d,
                                                                                                            treasure[d][
                                                                                                                '회사명'],
                                                                                                            treasure[d][
                                                                                                                'ROE'],
                                                                                                            treasure[d][
                                                                                                                '요구수익률'])
            elif treasure[d]['업종구분'].replace('\n', '') in ['코스닥제조', '코스피제조업', '코스피건설업', '코스닥건설']:
                pass_reason = "[{}][{}][업종구분이 제조 또는 건설] => 업종구분 : {}".format(d, treasure[d]['회사명'],
                                                                             treasure[d]['업종구분'].replace(u'\xa0',
                                                                                                         '').replace(
                                                                                 '\n', ''))
            elif treasure[d]['지배주주지분'] / treasure[d]['자산총계'] < 0.51:
                pass_reason = "[{}][{}][지배주주 자산지분 비율이 51% 미만] => 지배주주지분 / 자산총계 : {:.2f}".format(d, treasure[d]['회사명'],
                                                                                                treasure[d]['지배주주지분'] /
                                                                                                treasure[d]['자산총계'])
            else:
                pass_reason = "[{}][{}]전기지배주주순이익 : {}\n지배주주지분 : {}\n자산총계 : {}\nROE : {:.2f} < 15\n업종구분 : {}\nNPV : {:.2f}\n종가 : {}".format(
                    d, treasure[d]['회사명'], treasure[d]['X지배주주순이익'], treasure[d]['지배주주지분'], treasure[d]['자산총계'],
                    treasure[d]['ROE'], treasure[d]['업종구분'].replace(u'\xa0', '').replace('\n', ''), treasure[d]['NPV'],
                    treasure[d]['종가'])
            continue
        print(align_string('L', cnt, 5),
              align_string('R', d, 10),
              align_string('R', treasure[d]['회사명'], 20 - len(treasure[d]['회사명'])),
              align_string(',', round(treasure[d]['요구수익률'], 2), 20),
              align_string(',', round(treasure[d]['ROE'], 2), 20),
              align_string(',', round(treasure[d]['ROS'], 2), 20),
              align_string(',', treasure[d]['12M PER'], 8),
              align_string(',', treasure[d]['업종 PER'], 8),
              align_string(',', round(treasure[d]['지배주주지분'], 0), 20),
              align_string(',', round(treasure[d]['주주가치'], 0), 20),
              align_string(',', round(treasure[d]['NPV'], 0), 20),
              align_string(',', treasure[d]['종가'], 10),
              align_string('R', '' if '확인사항' not in treasure[d].keys() else treasure[d]['확인사항'], 20),
              )


def hidden_pearl_in_usmarket():
    import sys
    import os
    import django
    import logging
    from detective.fnguide_collector import fileCheck, saveFile
    from detective.fnguide_collector import generateEncCode
    import detective.chromecrawler as cc
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()

    logfile = 'US_detector'
    if not os.path.exists('./logs'):
        os.makedirs('./logs')
    now = datetime.now().strftime("%Y%m%d%H%M%S")

    logger = logging.getLogger(__name__)
    formatter = logging.Formatter('[%(asctime)s][%(filename)s:%(lineno)s] >> %(message)s')

    streamHandler = logging.StreamHandler()
    fileHandler = logging.FileHandler("./logs/{}_{}.log".format(logfile, now))

    streamHandler.setFormatter(formatter)
    fileHandler.setFormatter(formatter)

    logger.addHandler(streamHandler)
    logger.addHandler(fileHandler)
    logger.setLevel(level=logging.INFO)

    pass_reason = ''
    treasure = {}
    trash = {}
    data = {}
    # 날짜 정보 셋팅
    dateDict = new_get_dateDict()
    # 종목 정보 셋팅
    # DEBUG = True
    DEBUG = False
    # USE_JSON = False
    USE_JSON = True

    term_nm1 = 'YYMM5'
    term_nm2 = 'VAL5'
    # yyyymmdd = str(datetime.now())[:10]
    # yyyymmdd = '2020-08-04'
    # workDir = r'{}\{}\{}'.format(path, 'GlobalFinancialSummary', '2020-08-04')

    import detective_app.models as detective_db
    # stockInfo = detective_db.USNasdaqStocks.objects.filter(ticker='RXT', listing='Y')  # Apple
    stockInfo = detective_db.USNasdaqStocks.objects.filter(listing='Y')  # Apple

    HIGH_ROS = []
    HIGH_RESERVE = []

    JsonDir = r'{}\USResultJson'.format(path)
    if not os.path.exists(JsonDir):
        os.makedirs(JsonDir)
    if os.path.exists(r'{}\us_result.{}.json'.format(JsonDir, yyyymmdd)) and USE_JSON:
        with open(r'{}\us_result.{}.json'.format(JsonDir, yyyymmdd), "r") as f:
            data = f.read()
            treasure = json.loads(data)
            # print(treasure)
    if os.path.exists(r'{}\us_trash.{}.json'.format(JsonDir, yyyymmdd)) and USE_JSON:
        with open(r'{}\us_trash.{}.json'.format(JsonDir, yyyymmdd), "r") as f:
            data = f.read()
            trash = json.loads(data)
            # print(treasure)
    try:
        for ii, stock in enumerate(stockInfo):
            # if ii > 10: break
            if stock.ticker in treasure.keys():
                print("stock.ticker in treasure.keys()")
                continue
            else:
                if stock.ticker in trash.keys():
                    print("stock.ticker in trash.keys()")
                    continue
                else:
                    pass
        for idx, i in enumerate(stockInfo):
            # print(i.__dict__)
            data = {}
            data = {'Name': i.security, 'Exchange': i.category_code, 'Sector': i.category_name,
                    'Industry': i.category_detail, '발행주식수': i.issued_shares}
            sec_name = i.security.replace(' ', '') \
                .replace('&', 'AND') \
                .replace(',', '') \
                .replace('.', '') \
                .replace('!', '') \
                .replace('*', '') \
                .replace('/', '')
            dic = get_soup_from_file('GlobalCompanyProfile', yyyymmdd, sec_name, i.ticker, 'json')
            if dic is None or dic == '':
                logger.info("[{}][{}] Not exist profile File".format(i.ticker, i.security))
                continue
            if dic['data'] is not None:
                if dic['data']['primaryData'] is not None:
                    if dic['data']['primaryData']['lastSalePrice'] is not None and dic['data']['primaryData'][
                        'lastSalePrice'] != 'N/A':
                        data['종가'] = float(dic['data']['primaryData']['lastSalePrice'].replace('$', ''))
                    else:
                        data['종가'] = 0.0
                else:
                    data['종가'] = 0.0
            else:
                data['종가'] = 0.0
                continue
            data['전일대비'] = "-" if dic['data']['primaryData']['percentageChange'] == "" else dic['data']['primaryData'][
                'percentageChange'].replace('+', '△ ').replace('-', '▽ ')
            data['거래량'] = int(dic['data']['keyStats']['Volume']['value'].replace(',', ''))
            dic = get_soup_from_file('GlobalFinancialSummary', yyyymmdd, sec_name, i.ticker, 'json')
            if dic is None or dic == '':
                logger.info("[{}][{}] Not exist FinancialSummary File".format(i.ticker, i.security))
                continue
            data['Period'] = dic['Data1'][term_nm1]
            data['요구수익률'] = 10
            for d in dic['Data2']:
                if DEBUG: print(d)
                if d['ITEM_NM'] in ['자산총계', '자본총계', '매출총이익', '판매비와관리비', '영업활동현금흐름', '투자활동현금흐름', '재무활동현금흐름', 'CAPEX',
                                    'Free Cash Flow']:
                    data[d['ITEM_NM']] = d[term_nm2] * 1000000 if d[term_nm2] is not None else 0
            dic = get_soup_from_file('GlobalConsensus', yyyymmdd, sec_name, i.ticker, 'json')
            if dic is None or dic == '':
                logger.info("[{}][{}] Not exist Consensus File".format(i.ticker, i.security))
                continue
            for d in dic['Data']:
                if DEBUG: print(d)
                if d['ITEM'] in ['매출액', '영업이익', '당기순이익']:
                    data[d['ITEM']] = d['DATA3'] * 1000000 if d['DATA3'] is not None else 0
            if data['자산총계'] == 0:
                data['ROE'] = 0.0
            else:
                data['ROE'] = (data['당기순이익'] / data['자산총계'] * 100) if data['자산총계'] is not None and data[
                    '자산총계'] != 0 else 0

            data['주주가치'] = data['자산총계'] + (
                    data['자산총계'] * (data['ROE'] - data['요구수익률']) / (data['요구수익률']))
            data['NPV'] = data['주주가치'] / data['발행주식수'] if data['발행주식수'] is not None and data['발행주식수'] != 0.0 else 0
            data['ROS'] = data['당기순이익'] / data['매출액'] * 100 if data['매출액'] is not None and data['매출액'] != 0 else 0
            if data['ROS'] > 15: HIGH_ROS.append(data['Name'])
            if DEBUG: print(data)
            treasure[i.ticker] = data
        print('=' * 50, '마이너스', '=' * 50)
        print(align_string('L', 'No.', 5),
              align_string('R', 'Ticker', 10),
              align_string('R', 'Security', 20),
              align_string('R', 'ROE', 20),
              align_string('R', '자산총계', 14),
              align_string('R', '주주가치', 16),
              align_string('R', 'NPV', 20),
              align_string('R', '종가', 10),
              align_string('R', '확인사항', 16),
              )
        if not DEBUG: USDataInit()
        cnt = 0
        print(treasure)
        USTargetStockDataDelete(yyyymmdd)
        for d in treasure.keys():
            pass_reason = ""
            if treasure[d]['ROE'] < treasure[d]['요구수익률'] or \
                    treasure[d]['Sector'] in ['Finance', 'Transportation'] or \
                    treasure[d]['Industry'] in ['Construction/Ag Equipment/Trucks', 'Engineering & Construction'] or \
                    treasure[d]['NPV'] < 0 or \
                    treasure[d]['자산총계'] == 0 or \
                    treasure[d]['당기순이익'] == 0 or \
                    treasure[d]['발행주식수'] == 0 or \
                    treasure[d]['종가'] == 0.0 or \
                    treasure[d]['NPV'] / treasure[d]['종가'] * 100 < 105:
                cnt += 1
                print(align_string('L', cnt, 5),
                      align_string('R', d, 10),
                      align_string('R', treasure[d]['Name'], 40 - len(treasure[d]['Name'])),
                      align_string(',', round(treasure[d]['ROE'], 2), 20),
                      align_string(',', round(treasure[d]['자산총계'], 0), 20),
                      align_string(',', round(treasure[d]['주주가치'], 0), 20),
                      align_string(',', round(treasure[d]['NPV'], 0), 20),
                      align_string(',', treasure[d]['종가'], 10),
                      align_string('R', '' if '확인사항' not in treasure[d].keys() else treasure[d]['확인사항'], 20),
                      )
                if treasure[d]['ROE'] < treasure[d]['요구수익률']:
                    pass_reason = "[{}][{}]['ROE'] < ['요구수익률'] => ROE : {} / 요구수익률 : {}".format(d,
                                                                                                treasure[d][
                                                                                                    'Name'],
                                                                                                treasure[d][
                                                                                                    'ROE'],
                                                                                                treasure[d][
                                                                                                    '요구수익률'])
                else:
                    pass_reason = "[{}][{}]자산총계 : {}\nROE : {:.2f} < 15\n업종구분 : {}\nNPV : {:.2f}\n종가 : {}".format(
                        d, treasure[d]['Name'], treasure[d]['자산총계'], treasure[d]['ROE'], treasure[d]['Industry'],
                        treasure[d]['NPV'], treasure[d]['종가'])

                if treasure[d]['ROE'] >= 30 or (
                        treasure[d]['종가'] != 0.0 and treasure[d]['NPV'] / treasure[d]['종가'] * 100 > 200):
                    logger.info("[NEED TO CHECK]" + pass_reason)
                else:
                    logger.error(pass_reason)
                trash[d] = treasure[d]
                # treasure.pop(d)
                continue
            print(align_string('L', cnt, 5),
                  align_string('R', d, 10),
                  align_string('R', treasure[d]['Name'], 40 - len(treasure[d]['Name'])),
                  align_string(',', round(treasure[d]['ROE'], 2), 20),
                  align_string(',', round(treasure[d]['자산총계'], 0), 20),
                  align_string(',', round(treasure[d]['주주가치'], 0), 20),
                  align_string(',', round(treasure[d]['NPV'], 0), 20),
                  align_string(',', treasure[d]['종가'], 10),
                  align_string('R', '' if '확인사항' not in treasure[d].keys() else treasure[d]['확인사항'], 20),
                  )
            USTargetStockDataStore(d, treasure[d])
        # print(HIGH_ROS)
        # print(HIGH_RESERVE)
        logger.info(HIGH_ROS)
        if os.path.exists(r'{}\us_result.{}.json'.format(JsonDir, yyyymmdd)):
            os.remove(r'{}\us_result.{}.json'.format(JsonDir, yyyymmdd))
        with open(r'{}\us_result.{}.json'.format(JsonDir, yyyymmdd), 'w') as fp:
            json.dump(treasure, fp)
        if os.path.exists(r'{}\us_trash.{}.json'.format(JsonDir, yyyymmdd)):
            os.remove(r'{}\us_trash.{}.json'.format(JsonDir, yyyymmdd))
        with open(r'{}\us_trash.{}.json'.format(JsonDir, yyyymmdd), 'w') as fp:
            json.dump(trash, fp)
    except Exception as e:
        print('error', e, '\n', i)
        errmsg = '{}\n{}\n[{}][{}]'.format('hidden_pearl_in_usmarket', str(e), i.ticker, i.security)
        err_messeage_to_telegram(errmsg)
        if os.path.exists(r'{}\us_result.{}.json'.format(JsonDir, yyyymmdd)):
            os.remove(r'{}\us_result.{}.json'.format(JsonDir, yyyymmdd))
        with open(r'{}\us_result.{}.json'.format(JsonDir, yyyymmdd), 'w') as fp:
            json.dump(treasure, fp)
        if os.path.exists(r'{}\us_trash.{}.json'.format(JsonDir, yyyymmdd)):
            os.remove(r'{}\us_trash.{}.json'.format(JsonDir, yyyymmdd))
        with open(r'{}\us_trash.{}.json'.format(JsonDir, yyyymmdd), 'w') as fp:
            json.dump(trash, fp)


def hidden_pearl_in_usmarket_test():
    import sys
    import os
    import django
    import logging
    from detective.fnguide_collector import fileCheck, saveFile
    from detective.fnguide_collector import generateEncCode
    import detective.chromecrawler as cc
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()

    logfile = 'US_detector_test'
    if not os.path.exists('./logs'):
        os.makedirs('./logs')
    now = datetime.now().strftime("%Y%m%d%H%M%S")

    logger = logging.getLogger(__name__)
    formatter = logging.Formatter('[%(asctime)s][%(filename)s:%(lineno)s] >> %(message)s')

    streamHandler = logging.StreamHandler()
    fileHandler = logging.FileHandler("./logs/{}_{}.log".format(logfile, now))

    streamHandler.setFormatter(formatter)
    fileHandler.setFormatter(formatter)

    logger.addHandler(streamHandler)
    logger.addHandler(fileHandler)
    logger.setLevel(level=logging.INFO)

    pass_reason = ''
    treasure = {}
    trash = {}
    data = {}
    # 날짜 정보 셋팅
    dateDict = new_get_dateDict()
    # 종목 정보 셋팅
    # DEBUG = True
    DEBUG = False
    # USE_JSON = False
    USE_JSON = True

    term_nm1 = 'YYMM5'
    term_nm2 = 'VAL5'
    # yyyymmdd = str(datetime.now())[:10]
    # yyyymmdd = '2020-08-04'
    # workDir = r'{}\{}\{}'.format(path, 'GlobalFinancialSummary', '2020-08-04')

    import detective_app.models as detective_db
    stockInfo = detective_db.USNasdaqStocks.objects.filter(ticker='ZYXI', listing='Y')  # Apple
    # stockInfo = detective_db.USNasdaqStocks.objects.filter(listing='Y')  # Apple

    HIGH_ROS = []
    HIGH_RESERVE = []

    try:
        for idx, i in enumerate(stockInfo):
            # print(i.__dict__)
            data = {}
            data = {'Name': i.security, 'Exchange': i.category_code, 'Sector': i.category_name,
                    'Industry': i.category_detail, '발행주식수': i.issued_shares}
            sec_name = i.security.replace(' ', '') \
                .replace('&', 'AND') \
                .replace(',', '') \
                .replace('.', '') \
                .replace('!', '') \
                .replace('*', '') \
                .replace('/', '')
            dic = get_soup_from_file('GlobalCompanyProfile', yyyymmdd, sec_name, i.ticker, 'json')
            if dic is None or dic == '':
                logger.info("[{}][{}] Not exist profile File".format(i.ticker, i.security))
                continue
            if dic['data'] is not None:
                if dic['data']['primaryData'] is not None:
                    if dic['data']['primaryData']['lastSalePrice'] is not None and dic['data']['primaryData'][
                        'lastSalePrice'] != 'N/A':
                        data['종가'] = float(dic['data']['primaryData']['lastSalePrice'].replace('$', ''))
                    else:
                        data['종가'] = 0.0
                else:
                    data['종가'] = 0.0
            else:
                data['종가'] = 0.0
                continue
            data['전일대비'] = "-" if dic['data']['primaryData']['percentageChange'] == "" else dic['data']['primaryData'][
                'percentageChange'].replace('+', '△ ').replace('-', '▽ ')
            data['거래량'] = int(dic['data']['keyStats']['Volume']['value'].replace(',', ''))
            dic = get_soup_from_file('GlobalFinancialSummary', yyyymmdd, sec_name, i.ticker, 'json')
            if dic is None or dic == '':
                logger.info("[{}][{}] Not exist FinancialSummary File".format(i.ticker, i.security))
                continue
            data['Period'] = dic['Data1'][term_nm1]
            data['요구수익률'] = 10
            for d in dic['Data2']:
                if DEBUG: print(d)
                if d['ITEM_NM'] in ['자산총계', '자본총계', '매출총이익', '판매비와관리비', '영업활동현금흐름', '투자활동현금흐름', '재무활동현금흐름', 'CAPEX',
                                    'Free Cash Flow']:
                    data[d['ITEM_NM']] = d[term_nm2] * 1000000 if d[term_nm2] is not None else 0
            dic = get_soup_from_file('GlobalConsensus', yyyymmdd, sec_name, i.ticker, 'json')
            if dic is None or dic == '':
                logger.info("[{}][{}] Not exist Consensus File".format(i.ticker, i.security))
                continue
            for d in dic['Data']:
                if DEBUG: print(d)
                if d['ITEM'] in ['매출액', '영업이익', '당기순이익']:
                    data[d['ITEM']] = d['DATA3'] * 1000000 if d['DATA3'] is not None else 0
            if data['자산총계'] == 0:
                data['ROE'] = 0.0
            else:
                data['ROE'] = (data['당기순이익'] / data['자산총계'] * 100) if data['자산총계'] != 0 else 0

            data['주주가치'] = data['자산총계'] + (
                    data['자산총계'] * (data['ROE'] - data['요구수익률']) / (data['요구수익률']))
            data['NPV'] = data['주주가치'] / data['발행주식수'] if data['발행주식수'] is not None and data['발행주식수'] != 0 else 0
            data['ROS'] = data['당기순이익'] / data['매출액'] * 100 if data['매출액'] is not None and data['매출액'] != 0 else 0
            if data['ROS'] > 15: HIGH_ROS.append(data['Name'])
            if DEBUG: print(data)
            treasure[i.ticker] = data
        print('=' * 50, '마이너스', '=' * 50)
        print(align_string('L', 'No.', 5),
              align_string('R', 'Ticker', 10),
              align_string('R', 'Security', 20),
              align_string('R', 'ROE', 20),
              align_string('R', '자산총계', 14),
              align_string('R', '주주가치', 16),
              align_string('R', 'NPV', 20),
              align_string('R', '종가', 10),
              align_string('R', '확인사항', 16),
              )
        cnt = 0
        print(treasure)
        for d in treasure.keys():
            pass_reason = ""
            if treasure[d]['ROE'] < treasure[d]['요구수익률'] or \
                    treasure[d]['Sector'] in ['Finance', 'Transportation'] or \
                    treasure[d]['Industry'] in ['Construction/Ag Equipment/Trucks', 'Engineering & Construction'] or \
                    treasure[d]['NPV'] < 0 or \
                    treasure[d]['자산총계'] == 0 or \
                    treasure[d]['당기순이익'] == 0 or \
                    treasure[d]['발행주식수'] == 0 or \
                    treasure[d]['NPV'] / treasure[d]['종가'] * 100 < 105:
                cnt += 1
                print(align_string('L', cnt, 5),
                      align_string('R', d, 10),
                      align_string('R', treasure[d]['Name'], 40 - len(treasure[d]['Name'])),
                      align_string(',', round(treasure[d]['ROE'], 2), 20),
                      align_string(',', round(treasure[d]['자산총계'], 0), 20),
                      align_string(',', round(treasure[d]['주주가치'], 0), 20),
                      align_string(',', round(treasure[d]['NPV'], 0), 20),
                      align_string(',', treasure[d]['종가'], 10),
                      align_string('R', '' if '확인사항' not in treasure[d].keys() else treasure[d]['확인사항'], 20),
                      )
                if treasure[d]['ROE'] < treasure[d]['요구수익률']:
                    pass_reason = "[{}][{}]['ROE'] < ['요구수익률'] => ROE : {} / 요구수익률 : {}".format(d,
                                                                                                treasure[d][
                                                                                                    'Name'],
                                                                                                treasure[d][
                                                                                                    'ROE'],
                                                                                                treasure[d][
                                                                                                    '요구수익률'])
                else:
                    pass_reason = "[{}][{}]자산총계 : {}\nROE : {:.2f} < 15\n업종구분 : {}\nNPV : {:.2f}\n종가 : {}".format(
                        d, treasure[d]['Name'], treasure[d]['자산총계'], treasure[d]['ROE'], treasure[d]['Industry'],
                        treasure[d]['NPV'], treasure[d]['종가'])

                if treasure[d]['ROE'] >= 30 or treasure[d]['NPV'] / treasure[d]['종가'] * 100 > 200:
                    logger.info("[NEED TO CHECK]" + pass_reason)
                else:
                    logger.error(pass_reason)
                trash[d] = treasure[d]
                # treasure.pop(d)
                continue
            print(align_string('L', cnt, 5),
                  align_string('R', d, 10),
                  align_string('R', treasure[d]['Name'], 40 - len(treasure[d]['Name'])),
                  align_string(',', round(treasure[d]['ROE'], 2), 20),
                  align_string(',', round(treasure[d]['자산총계'], 0), 20),
                  align_string(',', round(treasure[d]['주주가치'], 0), 20),
                  align_string(',', round(treasure[d]['NPV'], 0), 20),
                  align_string(',', treasure[d]['종가'], 10),
                  align_string('R', '' if '확인사항' not in treasure[d].keys() else treasure[d]['확인사항'], 20),
                  )
        # print(HIGH_ROS)
        # print(HIGH_RESERVE)
        logger.info(HIGH_ROS)
    except Exception as e:
        print('error', e, '\n', i)
        errmsg = '{}\n{}\n[{}][{}]'.format('hidden_pearl_in_usmarket_test', str(e), i.ticker, i.security)
        print(errmsg)


def new_hidden_pearl_in_usmarket():
    import sys
    import os
    import django
    import logging
    from statistics import mean
    import numpy as np
    from detective.fnguide_collector import fileCheck, saveFile
    from detective.fnguide_collector import generateEncCode
    import detective.chromecrawler as cc
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()

    logfile = 'US_detector'
    if not os.path.exists('./logs'):
        os.makedirs('./logs')
    now = datetime.now().strftime("%Y%m%d%H%M%S")

    logger = logging.getLogger(__name__)
    formatter = logging.Formatter('[%(asctime)s][%(filename)s:%(lineno)s] >> %(message)s')

    streamHandler = logging.StreamHandler()
    fileHandler = logging.FileHandler("./logs/{}_{}.log".format(logfile, now))

    streamHandler.setFormatter(formatter)
    fileHandler.setFormatter(formatter)

    logger.addHandler(streamHandler)
    logger.addHandler(fileHandler)
    logger.setLevel(level=logging.INFO)

    pass_reason = ''
    treasure = {}
    trash = {}
    best = {}
    better = {}
    good = {}
    data = {}
    # 날짜 정보 셋팅
    dateDict = new_get_dateDict()
    # 종목 정보 셋팅
    # DEBUG = True
    DEBUG = False
    # USE_JSON = False
    USE_JSON = True
    current_data = None
    term_nm1 = 'YYMM5'
    term_nm2 = 'VAL5'
    term_header = {"YYMM6": "VAL6", "YYMM7": "VAL7", "YYMM8": "VAL8", "YYMM9": "VAL9", "YYMM10": "VAL10",
                   "YYMM5": "VAL5"}
    term_header2 = {"YYMM1": "DATA1", "YYMM2": "DATA2", "YYMM3": "DATA3", "YYMM4": "DATA4", "YYMM5": "DATA5"}
    # yyyymmdd = str(datetime.now())[:10]
    # yyyymmdd = '2020-08-04'
    # workDir = r'{}\{}\{}'.format(path, 'GlobalFinancialSummary', '2020-08-04')

    import detective_app.models as detective_db
    # stockInfo = detective_db.USNasdaqStocks.objects.filter(ticker='AIH', listing='Y')  # Apple
    stockInfo = detective_db.USNasdaqStocks.objects.filter(listing='Y').exclude(category_name="Finance").exclude(
        category_name="None")  # Apple

    HIGH_ROS = []
    HIGH_RESERVE = []

    JsonDir = r'{}\USResultJson'.format(path)
    if not os.path.exists(JsonDir):
        os.makedirs(JsonDir)
    if os.path.exists(r'{}\us_result.{}.json'.format(JsonDir, yyyymmdd)) and USE_JSON:
        with open(r'{}\us_result.{}.json'.format(JsonDir, yyyymmdd), "r") as f:
            data = f.read()
            treasure = json.loads(data)
            # print(treasure)
    if os.path.exists(r'{}\us_trash.{}.json'.format(JsonDir, yyyymmdd)) and USE_JSON:
        with open(r'{}\us_trash.{}.json'.format(JsonDir, yyyymmdd), "r") as f:
            data = f.read()
            trash = json.loads(data)
            # print(treasure)
    try:
        for ii, stock in enumerate(stockInfo):
            # if ii > 10: break
            if stock.ticker in treasure.keys():
                print("stock.ticker in treasure.keys()")
                continue
            else:
                if stock.ticker in trash.keys():
                    print("stock.ticker in trash.keys()")
                    continue
                else:
                    pass
        for idx, i in enumerate(stockInfo):
            # print(i.__dict__)
            data = {}
            # if i.security == "Apple Inc":
            #     print(i.category_detail)
            try:
                current_data = i
                data = {'Name': i.security, 'Exchange': i.category_code, 'Sector': i.category_name,
                        'Industry': i.category_detail, '발행주식수': i.issued_shares}
                sec_name = i.security.replace(' ', '') \
                    .replace('&', 'AND') \
                    .replace(',', '') \
                    .replace('.', '') \
                    .replace('!', '') \
                    .replace('*', '') \
                    .replace('/', '')
                dic = get_soup_from_file('GlobalCompanyProfile', yyyymmdd, sec_name, i.ticker, 'json')
                if dic is None or dic == '':
                    logger.info("[{}][{}] Not exist profile File".format(i.ticker, i.security))
                    continue
                if dic['data'] is not None:
                    if dic['data']['primaryData'] is not None:
                        if dic['data']['primaryData']['lastSalePrice'] is not None and dic['data']['primaryData'][
                            'lastSalePrice'] != 'N/A':
                            data['종가'] = float(dic['data']['primaryData']['lastSalePrice'].replace('$', ''))
                        else:
                            data['종가'] = 0.0
                    else:
                        data['종가'] = 0.0
                else:
                    data['종가'] = 0.0
                    continue
                data['전일대비'] = "-" if dic['data']['primaryData']['percentageChange'] == "" else \
                dic['data']['primaryData']['percentageChange'].replace('+', '△ ').replace('-', '▽ ')
                data['거래량'] = int(dic['data']['keyStats']['Volume']['value'].replace(',', ''))
                dic = get_soup_from_file('GlobalFinancialSummary', yyyymmdd, sec_name, i.ticker, 'json')
                if dic is None or dic == '':
                    logger.info("[{}][{}] Not exist FinancialSummary File".format(i.ticker, i.security))
                    continue
                data['Period'] = dic['Data1'][term_nm1]
                data['요구수익률'] = 20
                for d in dic['Data2']:
                    if DEBUG: print(d)
                    if d['ITEM_NM'] in ['자산총계', '자본총계', '당기순이익', '영업활동현금흐름', '투자활동현금흐름', '재무활동현금흐름', \
                                        'CAPEX', 'Free Cash Flow', '매출액']:
                        data[d['ITEM_NM']] = d[term_nm2] * 1000000 if d[term_nm2] is not None else 0
                        if d['ITEM_NM'] == '영업활동현금흐름':
                            data['OCF'] = {
                                dic['Data1'][key]: d[term_header[key]] if d[term_header[key]] is not None else 0 for key
                                in term_header.keys()}
                        if d['ITEM_NM'] == '투자활동현금흐름':
                            data['ICF'] = {
                                dic['Data1'][key]: d[term_header[key]] if d[term_header[key]] is not None else 0 for key
                                in term_header.keys()}
                        if d['ITEM_NM'] == '재무활동현금흐름':
                            data['FNCF'] = {
                                dic['Data1'][key]: d[term_header[key]] if d[term_header[key]] is not None else 0 for key
                                in term_header.keys()}
                        if d['ITEM_NM'] == 'Free Cash Flow':
                            data['FCF'] = {
                                dic['Data1'][key]: d[term_header[key]] if d[term_header[key]] is not None else 0 for key
                                in term_header.keys()}
                        if d['ITEM_NM'] == '매출액':
                            data['SALES'] = {
                                dic['Data1'][key]: d[term_header[key]] if d[term_header[key]] is not None else 0 for key
                                in term_header.keys()}
                        if d['ITEM_NM'] == '당기순이익':
                            data['NETINC'] = {
                                dic['Data1'][key]: d[term_header[key]] if d[term_header[key]] is not None else 0 for key
                                in term_header.keys()}
                    if d['ITEM_NM'] in ['매출액증가율', '영업이익률', '영업이익증가율']:
                        data[d['ITEM_NM']] = d[term_nm2] if d[term_nm2] is not None else 0
                        if d['ITEM_NM'] == '영업이익률':
                            data['OPIR'] = {
                                dic['Data1'][key]: d[term_header[key]] if d[term_header[key]] is not None else 0 for key
                                in term_header.keys()}
                        if d['ITEM_NM'] == '영업이익증가율':
                            data['OPIGR'] = {
                                dic['Data1'][key]: d[term_header[key]] if d[term_header[key]] is not None else 0 for key
                                in term_header.keys()}
                        if d['ITEM_NM'] == '매출액증가율':
                            data['SRGR'] = {
                                dic['Data1'][key]: d[term_header[key]] if d[term_header[key]] is not None else 0 for key
                                in term_header.keys()}
                dic = get_soup_from_file('GlobalFinancialStatement', yyyymmdd, sec_name, i.ticker, 'json')
                if dic is None or dic == '':
                    logger.info("[{}][{}] Not exist FinancialStatement File".format(i.ticker, i.security))
                    continue
                for d in dic['BodyData']:
                    if DEBUG: print(d)
                    if d['ACCODE'] == 112046051:
                        data['EARN'] = {
                            dic['HeaderData'][key]: d[term_header2[key]] if d[term_header2[key]] is not None else 0 for
                            key in term_header2.keys()}
                dic = get_soup_from_file('GlobalConsensus', yyyymmdd, sec_name, i.ticker, 'json')
                if dic is None or dic == '':
                    logger.info("[{}][{}] Not exist Consensus File".format(i.ticker, i.security))
                    continue
                for d in dic['Data']:
                    if DEBUG: print(d)
                    if d['ITEM'] in ['매출액', '영업이익', '당기순이익']:
                        data["12M_Fwd_{}".format(d['ITEM'])] = d['DATA3'] * 1000000 if d['DATA3'] is not None else 0
                    elif d['ITEM'] in ['EPS', 'PER', 'ROE<p class="unit"> %</p>']:
                        data["12M_Fwd_{}".format(d['ITEM'].replace('<p class="unit"> %</p>', ''))] = d['DATA3'] if d[
                                                                                                                       'DATA3'] is not None else 0
                if data['자산총계'] == 0:
                    data['ROE'] = 0.0
                else:
                    data['ROE'] = (data['당기순이익'] / data['자산총계'] * 100) if data['자산총계'] is not None and data[
                        '자산총계'] != 0 else 0
                data["EPS"] = round(data["당기순이익"] / data["발행주식수"], 2) if data["발행주식수"] is not None and data[
                    "발행주식수"] != 0 else 0
                data["PER"] = round(data["종가"] / data["EPS"] * 100, 2) if data["EPS"] is not None and data[
                    "EPS"] != 0 else 0
                # data["NPV"] = data["12M_Fwd_PER"] * data["12M_Fwd_EPS"] if data["12M_Fwd_EPS"] is not None and data["12M_Fwd_EPS"] != 0 else 0
                data['주주가치'] = data['자산총계'] + (
                        data['자산총계'] * (data['12M_Fwd_ROE'] - data['요구수익률']) / (data['요구수익률']))
                data['NPV'] = data['주주가치'] / data['발행주식수'] if data['발행주식수'] is not None and data['발행주식수'] != 0.0 else 0
                # data['ROS'] = data['당기순이익'] / data['매출액'] * 100 if data['매출액'] is not None and data['매출액'] != 0 else 0
                # if data['ROS'] > 15: HIGH_ROS.append(data['Name'])
                keylist = list(data['FCF'].keys())
                keylist.extend(list(data['EARN'].keys()))
                keyfinder = sorted(list(set(keylist)))
                # keyfinder = list(data['FCF'].keys()).append(list(data['EARN'].keys()))
                temp_dic = {}
                for kf in keyfinder:
                    if kf not in data['FCF'].keys():
                        if kf < list(data['FCF'].keys())[0]:
                            temp_dic[kf] = data["FCF"][list(data['FCF'].keys())[0]]
                        elif kf > list(data['FCF'].keys())[-1]:
                            temp_dic[kf] = data["FCF"][list(data['FCF'].keys())[-1]]
                        else:
                            pass
                    else:
                        temp_dic[kf] = data["FCF"][kf]
                data["FCF"] = {k:temp_dic[k] for k in sorted(temp_dic)}
                temp_dic = {}
                for kf in keyfinder:
                    if kf not in data['OCF'].keys():
                        if kf < list(data['OCF'].keys())[0]:
                            temp_dic[kf] = data["OCF"][list(data['OCF'].keys())[0]]
                        elif kf > list(data['OCF'].keys())[-1]:
                            temp_dic[kf] = data["OCF"][list(data['OCF'].keys())[-1]]
                        else:
                            pass
                    else:
                        temp_dic[kf] = data["OCF"][kf]
                data["OCF"] = {k:temp_dic[k] for k in sorted(temp_dic)}
                temp_dic = {}
                for kf in keyfinder:
                    if kf not in data['EARN'].keys():
                        if kf < list(data['EARN'].keys())[0]:
                            temp_dic[kf] = data["EARN"][list(data['EARN'].keys())[0]]
                        elif kf > list(data['EARN'].keys())[-1]:
                            temp_dic[kf] = data["EARN"][list(data['EARN'].keys())[-1]]
                        else:
                            pass
                    else:
                        temp_dic[kf] = data["EARN"][kf]
                data["EARN"] = {k:temp_dic[k] for k in sorted(temp_dic)}
                temp_dic = {}
                for kf in keyfinder:
                    if kf not in data['NETINC'].keys():
                        if kf < list(data['NETINC'].keys())[0]:
                            temp_dic[kf] = data["NETINC"][list(data['NETINC'].keys())[0]]
                        elif kf > list(data['NETINC'].keys())[-1]:
                            temp_dic[kf] = data["NETINC"][list(data['NETINC'].keys())[-1]]
                        else:
                            pass
                    else:
                        temp_dic[kf] = data["NETINC"][kf]
                data["NETINC"] = {k:temp_dic[k] for k in sorted(temp_dic)}

                if DEBUG: print(data)
                if data["매출액"] and data["당기순이익"] and data["매출액"] > 0 and data["당기순이익"] > 0 and data["NPV"] > data[
                    "종가"] * 1.3 \
                        and mean(data["SALES"].values()) < data["매출액"] and list(data["SALES"].values())[-1] < data[
                    "매출액"] \
                        and mean(data["NETINC"].values()) < data["당기순이익"] and list(data["NETINC"].values())[-1] < data[
                    "당기순이익"]:
                    if data["영업이익률"] > 20:  # mean(data["OPIR"].values()) > 20:
                        best[i.ticker] = data
                    elif np.sign(data["영업이익률"]) > np.sign(mean(data["OPIR"].values())):
                        best[i.ticker] = data
                    else:
                        better[i.ticker] = data
                else:
                    if mean(data["OPIR"].values()) > 20 and data["NPV"] > data["종가"]:
                        if mean(data["OPIR"].values()) < data["영업이익률"]:
                            better[i.ticker] = data
                        else:
                            good[i.ticker] = data
                    else:
                        trash[i.ticker] = data
                        continue
            except Exception as e:
                logger.error(e)
                logger.error("{} {}".format(i.ticker, i.security))
        # print('=' * 50, '마이너스', '=' * 50)
        print(align_string('L', 'No.', 5),
              align_string('R', 'Ticker', 10),
              align_string('R', 'Security', 20),
              align_string('R', 'Industry', 30),
              align_string('R', '영업이익률', 15),
              align_string('R', 'EPS', 20),
              align_string('R', '자산총계', 14),
              align_string('R', '주주가치', 16),
              align_string('R', 'NPV', 20),
              align_string('R', '종가', 10),
              align_string('R', '확인사항', 16),
              )
        if not DEBUG: USDataInit()
        cnt = 0
        # print(treasure)
        USTargetStockDataDelete(yyyymmdd)
        print("=" * 50, "BEST", "=" * 50)
        for d in best.keys():
            cnt += 1
            print(align_string('L', cnt, 5),
                  align_string('R', d, 10),
                  align_string('R', best[d]['Name'], 40 - len(best[d]['Name'])),
                  align_string('R', best[d]['Industry'], 30),
                  align_string(',', round(best[d]['영업이익률'], 2), 20),
                  align_string(',', round(best[d]['EPS'], 2), 20),
                  align_string(',', round(best[d]['자산총계'], 0), 20),
                  align_string(',', round(best[d]['주주가치'], 0), 20),
                  align_string(',', round(best[d]['NPV'], 0), 20),
                  align_string(',', best[d]['종가'], 10),
                  align_string('R', '' if '확인사항' not in best[d].keys() else best[d]['확인사항'], 20),
                  )
            if "BEST" not in treasure.keys():
                treasure["BEST"] = {}
            treasure["BEST"][d] = best[d]
        print("=" * 50, "BETTER", "=" * 50)
        for d in better.keys():
            cnt += 1
            print(align_string('L', cnt, 5),
                  align_string('R', d, 10),
                  align_string('R', better[d]['Name'], 40 - len(better[d]['Name'])),
                  align_string('R', better[d]['Industry'], 30),
                  align_string(',', round(better[d]['영업이익률'], 2), 20),
                  align_string(',', round(better[d]['EPS'], 2), 20),
                  align_string(',', round(better[d]['자산총계'], 0), 20),
                  align_string(',', round(better[d]['주주가치'], 0), 20),
                  align_string(',', round(better[d]['NPV'], 0), 20),
                  align_string(',', better[d]['종가'], 10),
                  align_string('R', '' if '확인사항' not in better[d].keys() else better[d]['확인사항'], 20),
                  )
            if "BETTER" not in treasure.keys():
                treasure["BETTER"] = {}
            treasure["BETTER"][d] = better[d]
        print("=" * 50, "GOOD", "=" * 50)
        for d in good.keys():
            cnt += 1
            print(align_string('L', cnt, 5),
                  align_string('R', d, 10),
                  align_string('R', good[d]['Name'], 40 - len(good[d]['Name'])),
                  align_string('R', good[d]['Industry'], 30),
                  align_string(',', round(good[d]['영업이익률'], 2), 20),
                  align_string(',', round(good[d]['EPS'], 2), 20),
                  align_string(',', round(good[d]['자산총계'], 0), 20),
                  align_string(',', round(good[d]['주주가치'], 0), 20),
                  align_string(',', round(good[d]['NPV'], 0), 20),
                  align_string(',', good[d]['종가'], 10),
                  align_string('R', '' if '확인사항' not in good[d].keys() else good[d]['확인사항'], 20),
                  )
            if "GOOD" not in treasure.keys():
                treasure["GOOD"] = {}
            treasure["GOOD"][d] = good[d]
        for group in treasure.keys():
            for d in treasure[group].keys():
                USTargetStockDataStore(d, treasure[group][d])
        if os.path.exists(r'{}\us_result.{}.json'.format(JsonDir, yyyymmdd)):
            os.remove(r'{}\us_result.{}.json'.format(JsonDir, yyyymmdd))
        with open(r'{}\us_result.{}.json'.format(JsonDir, yyyymmdd), 'w') as fp:
            json.dump(treasure, fp)
        if os.path.exists(r'{}\us_trash.{}.json'.format(JsonDir, yyyymmdd)):
            os.remove(r'{}\us_trash.{}.json'.format(JsonDir, yyyymmdd))
        with open(r'{}\us_trash.{}.json'.format(JsonDir, yyyymmdd), 'w') as fp:
            json.dump(trash, fp)
        return treasure
    except Exception as e:
        print('error', e, '\n', i)
        errmsg = '{}\n{}\n[{}][{}]'.format('hidden_pearl_in_usmarket', str(e), i.ticker, i.security)
        err_messeage_to_telegram(errmsg)
        if os.path.exists(r'{}\us_result.{}.json'.format(JsonDir, yyyymmdd)):
            os.remove(r'{}\us_result.{}.json'.format(JsonDir, yyyymmdd))
        with open(r'{}\us_result.{}.json'.format(JsonDir, yyyymmdd), 'w') as fp:
            json.dump(treasure, fp)
        if os.path.exists(r'{}\us_trash.{}.json'.format(JsonDir, yyyymmdd)):
            os.remove(r'{}\us_trash.{}.json'.format(JsonDir, yyyymmdd))
        with open(r'{}\us_trash.{}.json'.format(JsonDir, yyyymmdd), 'w') as fp:
            json.dump(trash, fp)
        return None


def new_hidden_pearl_in_usmarket_test(code):
    import sys
    import os
    import django
    import logging
    from statistics import mean
    import numpy as np
    from detective.fnguide_collector import fileCheck, saveFile
    from detective.fnguide_collector import generateEncCode
    import detective.chromecrawler as cc
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()

    logfile = 'US_detector'
    if not os.path.exists('./logs'):
        os.makedirs('./logs')
    now = datetime.now().strftime("%Y%m%d%H%M%S")

    logger = logging.getLogger(__name__)
    formatter = logging.Formatter('[%(asctime)s][%(filename)s:%(lineno)s] >> %(message)s')

    streamHandler = logging.StreamHandler()
    fileHandler = logging.FileHandler("./logs/{}_{}.log".format(logfile, now))

    streamHandler.setFormatter(formatter)
    fileHandler.setFormatter(formatter)

    logger.addHandler(streamHandler)
    logger.addHandler(fileHandler)
    logger.setLevel(level=logging.INFO)

    pass_reason = ''
    treasure = {}
    trash = {}
    best = {}
    better = {}
    good = {}
    data = {}
    # 날짜 정보 셋팅
    dateDict = new_get_dateDict()
    # 종목 정보 셋팅
    # DEBUG = True
    DEBUG = True
    # USE_JSON = False
    USE_JSON = True
    current_data = None
    term_nm1 = 'YYMM5'
    term_nm2 = 'VAL5'
    term_header = {"YYMM6": "VAL6", "YYMM7": "VAL7", "YYMM8": "VAL8", "YYMM9": "VAL9", "YYMM10": "VAL10",
                   "YYMM5": "VAL5"}
    term_header2 = {"YYMM1": "DATA1", "YYMM2": "DATA2", "YYMM3": "DATA3", "YYMM4": "DATA4", "YYMM5": "DATA5"}

    import detective_app.models as detective_db
    stockInfo = detective_db.USNasdaqStocks.objects.filter(ticker=code, listing='Y')  # Apple

    try:
        for idx, i in enumerate(stockInfo):
            data = {}
            try:
                current_data = i
                data = {'Name': i.security, 'Exchange': i.category_code, 'Sector': i.category_name,
                        'Industry': i.category_detail, '발행주식수': i.issued_shares}
                sec_name = i.security.replace(' ', '') \
                    .replace('&', 'AND') \
                    .replace(',', '') \
                    .replace('.', '') \
                    .replace('!', '') \
                    .replace('*', '') \
                    .replace('/', '')
                dic = get_soup_from_file('GlobalCompanyProfile', yyyymmdd, sec_name, i.ticker, 'json')
                if dic is None or dic == '':
                    logger.info("[{}][{}] Not exist profile File".format(i.ticker, i.security))
                    continue
                if dic['data'] is not None:
                    if dic['data']['primaryData'] is not None:
                        if dic['data']['primaryData']['lastSalePrice'] is not None and dic['data']['primaryData'][
                            'lastSalePrice'] != 'N/A':
                            data['종가'] = float(dic['data']['primaryData']['lastSalePrice'].replace('$', ''))
                        else:
                            data['종가'] = 0.0
                    else:
                        data['종가'] = 0.0
                else:
                    data['종가'] = 0.0
                    continue
                data['전일대비'] = "-" if dic['data']['primaryData']['percentageChange'] == "" else \
                    dic['data']['primaryData']['percentageChange'].replace('+', '△ ').replace('-', '▽ ')
                data['거래량'] = int(dic['data']['keyStats']['Volume']['value'].replace(',', ''))
                dic = get_soup_from_file('GlobalFinancialSummary', yyyymmdd, sec_name, i.ticker, 'json')
                if dic is None or dic == '':
                    logger.info("[{}][{}] Not exist FinancialSummary File".format(i.ticker, i.security))
                    continue
                data['Period'] = dic['Data1'][term_nm1]
                data['요구수익률'] = 20
                for d in dic['Data2']:
                    if DEBUG: print(d)
                    if d['ITEM_NM'] in ['자산총계', '자본총계', '당기순이익', '영업활동현금흐름', '투자활동현금흐름', '재무활동현금흐름', \
                                        'CAPEX', 'Free Cash Flow', '매출액']:
                        data[d['ITEM_NM']] = d[term_nm2] * 1000000 if d[term_nm2] is not None else 0
                        if d['ITEM_NM'] == '영업활동현금흐름':
                            data['OCF'] = {
                                dic['Data1'][key]: d[term_header[key]] if d[term_header[key]] is not None else 0 for key
                                in term_header.keys()}
                        if d['ITEM_NM'] == '투자활동현금흐름':
                            data['ICF'] = {
                                dic['Data1'][key]: d[term_header[key]] if d[term_header[key]] is not None else 0 for key
                                in term_header.keys()}
                        if d['ITEM_NM'] == '재무활동현금흐름':
                            data['FNCF'] = {
                                dic['Data1'][key]: d[term_header[key]] if d[term_header[key]] is not None else 0 for key
                                in term_header.keys()}
                        if d['ITEM_NM'] == 'Free Cash Flow':
                            data['FCF'] = {
                                dic['Data1'][key]: d[term_header[key]] if d[term_header[key]] is not None else 0 for key
                                in term_header.keys()}
                        if d['ITEM_NM'] == '매출액':
                            data['SALES'] = {
                                dic['Data1'][key]: d[term_header[key]] if d[term_header[key]] is not None else 0 for key
                                in term_header.keys()}
                        if d['ITEM_NM'] == '당기순이익':
                            data['NETINC'] = {
                                dic['Data1'][key]: d[term_header[key]] if d[term_header[key]] is not None else 0 for key
                                in term_header.keys()}
                    if d['ITEM_NM'] in ['매출액증가율', '영업이익률', '영업이익증가율']:
                        data[d['ITEM_NM']] = d[term_nm2] if d[term_nm2] is not None else 0
                        if d['ITEM_NM'] == '영업이익률':
                            data['OPIR'] = {
                                dic['Data1'][key]: d[term_header[key]] if d[term_header[key]] is not None else 0 for key
                                in term_header.keys()}
                        if d['ITEM_NM'] == '영업이익증가율':
                            data['OPIGR'] = {
                                dic['Data1'][key]: d[term_header[key]] if d[term_header[key]] is not None else 0 for key
                                in term_header.keys()}
                        if d['ITEM_NM'] == '매출액증가율':
                            data['SRGR'] = {
                                dic['Data1'][key]: d[term_header[key]] if d[term_header[key]] is not None else 0 for key
                                in term_header.keys()}
                dic = get_soup_from_file('GlobalFinancialStatement', yyyymmdd, sec_name, i.ticker, 'json')
                if dic is None or dic == '':
                    logger.info("[{}][{}] Not exist FinancialStatement File".format(i.ticker, i.security))
                    continue
                for d in dic['BodyData']:
                    if DEBUG: print(d)
                    if d['ACCODE'] == 112046051:
                        data['EARN'] = {
                            dic['HeaderData'][key]: d[term_header2[key]] if d[term_header2[key]] is not None else 0 for
                            key in term_header2.keys()}
                dic = get_soup_from_file('GlobalConsensus', yyyymmdd, sec_name, i.ticker, 'json')
                if dic is None or dic == '':
                    logger.info("[{}][{}] Not exist Consensus File".format(i.ticker, i.security))
                    continue
                for d in dic['Data']:
                    if DEBUG: print(d)
                    if d['ITEM'] in ['매출액', '영업이익', '당기순이익']:
                        data["12M_Fwd_{}".format(d['ITEM'])] = d['DATA3'] * 1000000 if d['DATA3'] is not None else 0
                    elif d['ITEM'] in ['EPS', 'PER', 'ROE<p class="unit"> %</p>']:
                        data["12M_Fwd_{}".format(d['ITEM'].replace('<p class="unit"> %</p>', ''))] = d['DATA3'] if d[
                                                                                                                       'DATA3'] is not None else 0
                if data['자산총계'] == 0:
                    data['ROE'] = 0.0
                else:
                    data['ROE'] = (data['당기순이익'] / data['자산총계'] * 100) if data['자산총계'] is not None and data[
                        '자산총계'] != 0 else 0
                data["EPS"] = round(data["당기순이익"] / data["발행주식수"], 2) if data["발행주식수"] is not None and data[
                    "발행주식수"] != 0 else 0
                data["PER"] = round(data["종가"] / data["EPS"] * 100, 2) if data["EPS"] is not None and data[
                    "EPS"] != 0 else 0
                # data["NPV"] = data["12M_Fwd_PER"] * data["12M_Fwd_EPS"] if data["12M_Fwd_EPS"] is not None and data["12M_Fwd_EPS"] != 0 else 0
                data['주주가치'] = data['자산총계'] + (
                        data['자산총계'] * (data['12M_Fwd_ROE'] - data['요구수익률']) / (data['요구수익률']))
                data['NPV'] = data['주주가치'] / data['발행주식수'] if data['발행주식수'] is not None and data['발행주식수'] != 0.0 else 0
                keylist = list(data['FCF'].keys())
                keylist.extend(list(data['EARN'].keys()))
                keyfinder = sorted(list(set(keylist)))
                temp_dic = {}
                for kf in keyfinder:
                    if kf not in data['FCF'].keys():
                        if kf < list(data['FCF'].keys())[0]:
                            temp_dic[kf] = data["FCF"][list(data['FCF'].keys())[0]]
                        elif kf > list(data['FCF'].keys())[-1]:
                            temp_dic[kf] = data["FCF"][list(data['FCF'].keys())[-1]]
                        else:
                            pass
                    else:
                        temp_dic[kf] = data["FCF"][kf]
                data["FCF"] = {k: temp_dic[k] for k in sorted(temp_dic)}
                temp_dic = {}
                for kf in keyfinder:
                    if kf not in data['OCF'].keys():
                        if kf < list(data['OCF'].keys())[0]:
                            temp_dic[kf] = data["OCF"][list(data['OCF'].keys())[0]]
                        elif kf > list(data['OCF'].keys())[-1]:
                            temp_dic[kf] = data["OCF"][list(data['OCF'].keys())[-1]]
                        else:
                            pass
                    else:
                        temp_dic[kf] = data["OCF"][kf]
                data["OCF"] = {k: temp_dic[k] for k in sorted(temp_dic)}
                temp_dic = {}
                for kf in keyfinder:
                    if kf not in data['EARN'].keys():
                        if kf < list(data['EARN'].keys())[0]:
                            temp_dic[kf] = data["EARN"][list(data['EARN'].keys())[0]]
                        elif kf > list(data['EARN'].keys())[-1]:
                            temp_dic[kf] = data["EARN"][list(data['EARN'].keys())[-1]]
                        else:
                            pass
                    else:
                        temp_dic[kf] = data["EARN"][kf]
                data["EARN"] = {k: temp_dic[k] for k in sorted(temp_dic)}
                temp_dic = {}
                for kf in keyfinder:
                    if kf not in data['NETINC'].keys():
                        if kf < list(data['NETINC'].keys())[0]:
                            temp_dic[kf] = data["NETINC"][list(data['NETINC'].keys())[0]]
                        elif kf > list(data['NETINC'].keys())[-1]:
                            temp_dic[kf] = data["NETINC"][list(data['NETINC'].keys())[-1]]
                        else:
                            pass
                    else:
                        temp_dic[kf] = data["NETINC"][kf]
                data["NETINC"] = {k: temp_dic[k] for k in sorted(temp_dic)}

                if DEBUG: print(data)
                if data["매출액"] and data["당기순이익"] and data["매출액"] > 0 and data["당기순이익"] > 0 and data["NPV"] > data[
                    "종가"] * 1.3 \
                        and mean(data["SALES"].values()) < data["매출액"] and list(data["SALES"].values())[-1] < data[
                    "매출액"] \
                        and mean(data["NETINC"].values()) < data["당기순이익"] and list(data["NETINC"].values())[-1] < data[
                    "당기순이익"]:
                    if data["영업이익률"] > 20:  # mean(data["OPIR"].values()) > 20:
                        best[i.ticker] = data
                    elif np.sign(data["영업이익률"]) > np.sign(mean(data["OPIR"].values())):
                        best[i.ticker] = data
                    else:
                        better[i.ticker] = data
                else:
                    if mean(data["OPIR"].values()) > 20 and data["NPV"] > data["종가"]:
                        if mean(data["OPIR"].values()) < data["영업이익률"]:
                            better[i.ticker] = data
                        else:
                            good[i.ticker] = data
                    else:
                        trash[i.ticker] = data
                        continue
            except Exception as e:
                logger.error(e)
                logger.error("{} {}".format(i.ticker, i.security))
        # print('=' * 50, '마이너스', '=' * 50)
        print(align_string('L', 'No.', 5),
              align_string('R', 'Ticker', 10),
              align_string('R', 'Security', 20),
              align_string('R', '영업이익률', 15),
              align_string('R', 'EPS', 20),
              align_string('R', '자산총계', 14),
              align_string('R', '주주가치', 16),
              align_string('R', 'NPV', 20),
              align_string('R', '종가', 10),
              align_string('R', '확인사항', 16),
              )
        cnt = 0
        print("=" * 50, "BEST", "=" * 50)
        for d in best.keys():
            cnt += 1
            print(align_string('L', cnt, 5),
                  align_string('R', d, 10),
                  align_string('R', best[d]['Name'], 40 - len(best[d]['Name'])),
                  align_string(',', round(best[d]['영업이익률'], 2), 20),
                  align_string(',', round(best[d]['EPS'], 2), 20),
                  align_string(',', round(best[d]['자산총계'], 0), 20),
                  align_string(',', round(best[d]['주주가치'], 0), 20),
                  align_string(',', round(best[d]['NPV'], 0), 20),
                  align_string(',', best[d]['종가'], 10),
                  align_string('R', '' if '확인사항' not in best[d].keys() else best[d]['확인사항'], 20),
                  )
            if "BEST" not in treasure.keys():
                treasure["BEST"] = {}
            treasure["BEST"][d] = best[d]
        print("=" * 50, "BETTER", "=" * 50)
        for d in better.keys():
            cnt += 1
            print(align_string('L', cnt, 5),
                  align_string('R', d, 10),
                  align_string('R', better[d]['Name'], 40 - len(better[d]['Name'])),
                  align_string(',', round(better[d]['영업이익률'], 2), 20),
                  align_string(',', round(better[d]['EPS'], 2), 20),
                  align_string(',', round(better[d]['자산총계'], 0), 20),
                  align_string(',', round(better[d]['주주가치'], 0), 20),
                  align_string(',', round(better[d]['NPV'], 0), 20),
                  align_string(',', better[d]['종가'], 10),
                  align_string('R', '' if '확인사항' not in better[d].keys() else better[d]['확인사항'], 20),
                  )
            if "BETTER" not in treasure.keys():
                treasure["BETTER"] = {}
            treasure["BETTER"][d] = better[d]
        print("=" * 50, "GOOD", "=" * 50)
        for d in good.keys():
            cnt += 1
            print(align_string('L', cnt, 5),
                  align_string('R', d, 10),
                  align_string('R', good[d]['Name'], 40 - len(good[d]['Name'])),
                  align_string(',', round(good[d]['영업이익률'], 2), 20),
                  align_string(',', round(good[d]['EPS'], 2), 20),
                  align_string(',', round(good[d]['자산총계'], 0), 20),
                  align_string(',', round(good[d]['주주가치'], 0), 20),
                  align_string(',', round(good[d]['NPV'], 0), 20),
                  align_string(',', good[d]['종가'], 10),
                  align_string('R', '' if '확인사항' not in good[d].keys() else good[d]['확인사항'], 20),
                  )
            if "GOOD" not in treasure.keys():
                treasure["GOOD"] = {}
            treasure["GOOD"][d] = good[d]
        print("=" * 50, "TRASH", "=" * 50)
        for d in trash.keys():
            cnt += 1
            print(align_string('L', cnt, 5),
                  align_string('R', d, 10),
                  align_string('R', trash[d]['Name'], 40 - len(trash[d]['Name'])),
                  align_string(',', round(trash[d]['영업이익률'], 2), 20),
                  align_string(',', round(trash[d]['EPS'], 2), 20),
                  align_string(',', round(trash[d]['자산총계'], 0), 20),
                  align_string(',', round(trash[d]['주주가치'], 0), 20),
                  align_string(',', round(trash[d]['NPV'], 0), 20),
                  align_string(',', trash[d]['종가'], 10),
                  align_string('R', '' if '확인사항' not in trash[d].keys() else trash[d]['확인사항'], 20),
                  )
            if "TRASH" not in treasure.keys():
                treasure["TRASH"] = {}
            treasure["TRASH"][d] = trash[d]
        return treasure
    except Exception as e:
        print('error', e, '\n', i)
        errmsg = '{}\n{}\n[{}][{}]'.format('hidden_pearl_in_usmarket', str(e), i.ticker, i.security)
        err_messeage_to_telegram(errmsg)
        return None


if __name__ == '__main__':
    # get_high_ranked_stock_with_closeprice()
    # find_hidden_pearl()
    # messeage_to_telegram()
    # find_hidden_pearl()
    # test_find_hidden_pearl()
    # new_find_hidden_pearl()
    # msgr.messeage_to_telegram(get_high_ranked_stock())
    # new_get_dateDict()
    # getConfig()
    # yyyymmdd = '2020-08-13'
    # report_type = 'GlobalConsensus'
    # crp_nm = 'AppleInc'
    # crp_cd = 'AAPL'
    # ext = 'json'
    # aa = get_soup_from_file(report_type, yyyymmdd, crp_nm, crp_cd, ext)
    # for a in aa['Data']:
    #     print(a)

    # print(len(aa.find_all('div')))
    # hidden_pearl_in_usmarket_test()
    # print(get_nasdaq_high_ranked_stock())
    # get_nasdaq_high_ranked_stock_with_closeprice()
    # test()
    # t = new_find_hidden_pearl_with_dartpipe(all=True)
    t = new_find_hidden_pearl_with_dartpipe_single("084010")
    codes = [
        "051910",
        "011780",
        "027580",
        "000300",
        "049480",
        "078130",
        "027580",
        "074610",
        "054940",
        "900250",
        "154040",
        "195870",
        "073110",
        "136510",
        "000300",
        "049550",
        "121600",
        "039440",
        "043360",
        "017670",
        "005930",
        "203650",
        "131090",
        "050890",
        "109080",
        "056360",
        "047310",
        "137400",
        "006400",
        "051910",
        "131390",
        "054090",
        "004490",
        "096770",
        "322000",
        "043220",
        "031390",
        "002630",
        "084990",
        "102940",
        "080520",
        "084650",
        "118000",
        "038290",
        "174900",
        "004800",
        "018000",
        "032820",
        "034020",
        "075580",
        "024880",
        "100130",
        "044490",
        "068790",
        "101170",
        "100090",
        "112610",
        "297090",
        "314130",
        "311390",
        "311690",
        "187420",
        "348150",
        "249420",
        "063160",
        "238200",
        "049960"
    ]
    # t = new_find_hidden_pearl_with_dartpipe_multiple(codes)
    # # new_find_hidden_pearl_with_dartpipe_test()
    # # t = new_find_hidden_pearl_with_dartpipe_provision(search=False, bgn_dt="20210108")
    # # t = new_find_hidden_pearl_with_dartpipe_provision_test(code="145020", search=False, bgn_dt="20210108")
    # # print(t)
    # send_hidden_pearl_message(t)
    hidden_pearl_finding_with_regular_report(rcept_no=None, bgn_dt="20210817", end_dt="20210819")
    # t = new_hidden_pearl_in_usmarket_test('AIH')
    # get_nasdaq_stock_graph(t)
