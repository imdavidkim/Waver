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
# import os
import detective.fnguide_collector as fnguide
import detective.messenger as msgr
from detective.messenger import err_messeage_to_telegram
DEBUG = True


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
    # yyyymmdd = '2019-12-12'
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
    retDict['yyyy'] = yyyymmdd[:4]
    retDict['mm'] = yyyymmdd[5:7]
    retDict['dd'] = yyyymmdd[-2:]
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
                idx + 1, d['code'], d['name'], d['price_gap'], format(int(d['last_price']), ','), format(int(d['target_price']), ','), str(round(int(d['target_price'])/int(d['last_price'])*100-100, 0)))
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
                idx + 1, d['code'], d['name'], d['price_gap'], format(d['last_price'], ','), format(d['target_price'], ','), str(round((d['target_price'])/(d['last_price'])*100-100, 1)))
        return retStr
    except Exception as e:
        errmsg = '{}\n{}'.format('get_nasdaq_high_ranked_stock', str(e))
        err_messeage_to_telegram(errmsg)


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
        font_name = font_manager.FontProperties(fname=font_path).get_name()
        # font 설정
        plt.rc('font', family=font_name)
        plt.close('all')
        # plt.clf()
        for idx, d in enumerate(dictfetchall(cursor)):
            fig = plt.figure(clear=True)
            url_type = 'STOCK'
            price = getNaverPrice(url_type, d['code'], 36)
            SP = fig.add_subplot(1, 1, 1)
            SP.plot(price, label="{}({})".format(d['name'], d['code']))
            SP.legend(loc='upper center')
            plt.xticks(rotation=45)
            img_path = r'{}\{}\{}'.format(path, 'StockPriceTrace', yyyymmdd)
            # print(img_path)
            if not os.path.exists(img_path):
                os.makedirs(img_path)
            plt.savefig(img_path + '\\{}_{}.png'.format(d['name'], d['code']))
            # plt.show()
            msgr.img_messeage_to_telegram(img_path + '\\{}_{}.png'.format(d['name'], d['code']))
            fig = None
            plt.close('all')

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
        yyyy = str(int(dateDict['yyyy'])-1)
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
        yyyy = str(int(dateDict['yyyy'])-1)
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
                                                                        ).exclude(rmk='None').exclude(rmk='완전잠식').values()
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
                                                                            ).exclude(rmk='None').exclude(rmk='완전잠식').values()
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
    # stockInfo = detective_db.Stocks.objects.filter(code='299900', listing='Y') # 제일파마홀딩스
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
            print(align_string('L', ii+1, 10),
                  align_string('R', stock.code, 10),
                  align_string('R', stock.name, 20-len(stock.name)),
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
            marketTxt = fnguide.select_by_attr(soup, 'span', 'class', 'stxt stxt1').text.replace(' ', '')  # 업종분류
            data['업종구분'] = marketTxt.replace('\n', '')
            marketTxt = fnguide.select_by_attr(soup, 'span', 'class', 'stxt stxt2').text.replace(' ', '')  # 업종분류
            data['업종구분상세'] = marketTxt.replace('\n', '')
            # print(data['업종구분'], data['업종구분상세'], stock.market_text)
            if (data['업종구분'] != '' and stock.market_text is None) or (data['업종구분상세'] != '' and stock.market_text_detail is None):
                fnguide.StockMarketTextUpdate(stock.code, data['업종구분'], data['업종구분상세'])
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
                columns, items, values = fnguide.setting(fnguide.get_table_contents(yearly_highlight, 'table thead tr th')[1:],
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
                                        data['X' + i] = float(values[idx][idx2-1].replace(',', ''))
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
                                        data['X' + i] = float(values[idx][idx2-1].replace(',', '')) * 100000000
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
                                        data['X' + i] = float(values[idx][idx2-1].replace(',', '')) * 100000000
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
                                data['Period'] = columns[idx2-1]
                                if fnguide.is_float(values[idx][idx2-1].replace(',', '')):
                                    pass
                                else:
                                    data['확인사항'] = values[idx][idx2-1].replace(',', '')
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
                                     '부채비율(%)', '영업이익(발표기준)']:
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
                            data[col] = float(values[idx].replace(',', '')) if (values[idx] is not None and values[idx] != '') else 0.0
                        # break
                    if col in ['발행주식수-보통주'] and values[idx] != '' and data['발행주식수'] != float(values[idx].replace(',', '')):
                        print("[{}][{}]발행주식수가 다릅니다. {} <> {}".format(stock.code, stock.name, stock.issued_shares, float(values[idx].replace(',', ''))))
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
        print('='*50, '마이너스', '='*50)
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
            if treasure[d]['ROE'] < 15 or \
               treasure[d]['ROE'] < treasure[d]['요구수익률'] or \
               treasure[d]['업종구분'].replace('\n', '') in ['코스닥제조', '코스피제조업', '코스피건설업', '코스닥건설', '코스피금융업'] or \
               treasure[d]['지배주주지분'] / treasure[d]['자산총계'] < 0.51 or \
               treasure[d]['NPV'] < 0 or \
               treasure[d]['NPV']/treasure[d]['종가']*100 < 105:
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
                    pass_reason = "[{}][{}]['ROE'] < 15 또는 ['ROE'] < ['요구수익률'] => ROE : {} / 요구수익률 : {}".format(d, treasure[d]['회사명'], treasure[d]['ROE'], treasure[d]['요구수익률'])
                elif treasure[d]['업종구분'].replace('\n', '') in ['코스닥제조', '코스피제조업', '코스피건설업', '코스닥건설', '코스피금융업']:
                    pass_reason = "[{}][{}][업종구분이 제조, 건설 또는 금융] => 업종구분 : {}".format(d, treasure[d]['회사명'], treasure[d]['업종구분'].replace(u'\xa0', '').replace('\n', ''))
                elif treasure[d]['지배주주지분'] / treasure[d]['자산총계'] < 0.51:
                    pass_reason = "[{}][{}][지배주주 자산지분 비율이 51% 미만] => 지배주주지분 / 자산총계 : {:.2f}".format(d, treasure[d]['회사명'], treasure[d]['지배주주지분'] / treasure[d]['자산총계'])
                else:
                    pass_reason = "[{}][{}]전기지배주주순이익 : {}\n지배주주지분 : {}\n자산총계 : {}\nROE : {:.2f} < 15\n업종구분 : {}\nNPV : {:.2f}\n종가 : {}".format(
                        d, treasure[d]['회사명'], treasure[d]['X지배주주순이익'], treasure[d]['지배주주지분'], treasure[d]['자산총계'],
                        treasure[d]['ROE'], treasure[d]['업종구분'].replace(u'\xa0', '').replace('\n', ''), treasure[d]['NPV'],
                        treasure[d]['종가'])

                if treasure[d]['ROE'] >= 30 or treasure[d]['NPV']/treasure[d]['종가']*100 > 200:
                    logger.info("[NEED TO CHECK]" + pass_reason)
                else:
                    logger.error(pass_reason)
                pass_reason = ""
                continue
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
                                                                      'ratio': data['NPV']/data['종가']*100,
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
                                                                      'ratio': data['NPV']/data['종가']*100,
                                                                      'plus_npv': 'Y',
                                                                      'holders_share': data['자산총계'],
                                                                      'holders_value': data['주주가치'],
                                                                      'holders_profit': data['당기순이익'],
                                                                      'issued_shares': data['발행주식수'],
                                                                      # 'valuation_date': yyyymmdd,
                                                                      'return_on_sales': data['ROS'],
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
    yyyymmdd = '2020-11-10'
    import detective_app.models as detective_db
    stockInfo = detective_db.Stocks.objects.filter(code='010960', listing='Y')  # 삼성전자
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
        # print(data['업종구분'], data['업종구분상세'], stock.market_text)
        if (data['업종구분'] != '' and stock.market_text is None) or (
                data['업종구분상세'] != '' and stock.market_text_detail is None):
            fnguide.StockMarketTextUpdate(stock.code, data['업종구분'], data['업종구분상세'])

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
                        if i in ['당기순이익', '자본총계', '자산총계', '매출액', '이자수익', '보험료수익', '순영업수익', '영업수익', '유보율(%)', '부채비율(%)', '영업이익(발표기준)']:
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
                treasure[d]['업종구분'].replace('\n', '').replace('KSE', '').replace('KOSDAQ', '').replace(' ', '') in ['코스닥제조', '코스피제조업', '코스피건설업', '코스닥건설'] or \
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
            data = {'Name': i.security, 'Exchange': i.category_code, 'Sector': i.category_name, 'Industry': i.category_detail, '발행주식수': i.issued_shares}
            sec_name = i.security.replace(' ', '')\
                .replace('&', 'AND')\
                .replace(',', '')\
                .replace('.', '')\
                .replace('!', '')\
                .replace('*', '')\
                .replace('/', '')
            dic = get_soup_from_file('GlobalCompanyProfile', yyyymmdd, sec_name, i.ticker, 'json')
            if dic is None or dic == '':
                logger.info("[{}][{}] Not exist profile File".format(i.ticker, i.security))
                continue
            if dic['data'] is not None:
                if dic['data']['primaryData'] is not None:
                    if dic['data']['primaryData']['lastSalePrice'] is not None and dic['data']['primaryData']['lastSalePrice'] != 'N/A':
                        data['종가'] = float(dic['data']['primaryData']['lastSalePrice'].replace('$', ''))
                    else: data['종가'] = 0.0
                else: data['종가'] = 0.0
            else:
                data['종가'] = 0.0
                continue
            data['전일대비'] = "-" if dic['data']['primaryData']['percentageChange'] == "" else dic['data']['primaryData']['percentageChange'].replace('+', '△ ').replace('-', '▽ ')
            data['거래량'] = int(dic['data']['keyStats']['Volume']['value'].replace(',', ''))
            dic = get_soup_from_file('GlobalFinancialSummary', yyyymmdd, sec_name, i.ticker, 'json')
            if dic is None or dic == '':
                logger.info("[{}][{}] Not exist FinancialSummary File".format(i.ticker, i.security))
                continue
            data['Period'] = dic['Data1'][term_nm1]
            data['요구수익률'] = 10
            for d in dic['Data2']:
                if DEBUG: print(d)
                if d['ITEM_NM'] in ['자산총계', '자본총계', '매출총이익', '판매비와관리비', '영업활동현금흐름', '투자활동현금흐름', '재무활동현금흐름', 'CAPEX', 'Free Cash Flow']:
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
                data['ROE'] = (data['당기순이익'] / data['자산총계'] * 100) if data['자산총계'] is not None and data['자산총계'] != 0 else 0

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

                if treasure[d]['ROE'] >= 30 or (treasure[d]['종가'] != 0.0 and treasure[d]['NPV'] / treasure[d]['종가'] * 100 > 200):
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
            data = {'Name': i.security, 'Exchange': i.category_code, 'Sector': i.category_name, 'Industry': i.category_detail, '발행주식수': i.issued_shares}
            sec_name = i.security.replace(' ', '')\
                .replace('&', 'AND')\
                .replace(',', '')\
                .replace('.', '')\
                .replace('!', '')\
                .replace('*', '')\
                .replace('/', '')
            dic = get_soup_from_file('GlobalCompanyProfile', yyyymmdd, sec_name, i.ticker, 'json')
            if dic is None or dic == '':
                logger.info("[{}][{}] Not exist profile File".format(i.ticker, i.security))
                continue
            if dic['data'] is not None:
                if dic['data']['primaryData'] is not None:
                    if dic['data']['primaryData']['lastSalePrice'] is not None and dic['data']['primaryData']['lastSalePrice'] != 'N/A':
                        data['종가'] = float(dic['data']['primaryData']['lastSalePrice'].replace('$', ''))
                    else: data['종가'] = 0.0
                else: data['종가'] = 0.0
            else:
                data['종가'] = 0.0
                continue
            data['전일대비'] = "-" if dic['data']['primaryData']['percentageChange'] == "" else dic['data']['primaryData']['percentageChange'].replace('+', '△ ').replace('-', '▽ ')
            data['거래량'] = int(dic['data']['keyStats']['Volume']['value'].replace(',', ''))
            dic = get_soup_from_file('GlobalFinancialSummary', yyyymmdd, sec_name, i.ticker, 'json')
            if dic is None or dic == '':
                logger.info("[{}][{}] Not exist FinancialSummary File".format(i.ticker, i.security))
                continue
            data['Period'] = dic['Data1'][term_nm1]
            data['요구수익률'] = 10
            for d in dic['Data2']:
                if DEBUG: print(d)
                if d['ITEM_NM'] in ['자산총계', '자본총계', '매출총이익', '판매비와관리비', '영업활동현금흐름', '투자활동현금흐름', '재무활동현금흐름', 'CAPEX', 'Free Cash Flow']:
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
            data['NPV'] = data['주주가치'] / data['발행주식수'] if data['발행주식수'] is not None and data['발행주식수'] != 0  else 0
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
    test()
