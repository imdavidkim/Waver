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
DEBUG = True


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
    yyyymmdd = str(datetime.now())[:10]
    # yyyymmdd = '2019-12-12'
    # print(path, filename)


def get_soup_from_file(report_type, yyyymmdd, crp_nm, crp_cd, ext):
    getConfig()
    full_path = path + r'\%s\%s' % (report_type, yyyymmdd) + filename % (crp_nm, crp_cd, report_type, ext)
    with open(full_path, 'rb') as obj:
        if ext == 'json':
            soup = json.loads(obj.read())
        else:
            soup = BeautifulSoup(obj, 'lxml')
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
            and crp_cd = '%s'""" % crp_cd
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
    from django.db import connection
    cursor = connection.cursor()
    sql = """select t.code, t.name, t.curr, t.last_price, t.target_price, t.target_price2, t.return_on_equity, t.ratio, t.ratio2, (t.ratio + t.ratio2) / 2 as average_ratio  from (
                select code, name, curr, last_price, target_price, target_price2, return_on_equity, ratio, target_price2/last_price*100 as ratio2 from detective_app_targetstocks
                where ratio > 100
                --and return_on_equity > 14
                and valuation_date = '%s'
                order by ratio2 desc, return_on_equity desc, ratio desc
                limit 30) as t
             --where last_price > 14000
             --and ratio2 > 100
             order by t.ratio desc""" % yyyymmdd
    cursor.execute(sql)
    retStr = ''
    for idx, d in enumerate(dictfetchall(cursor)):
        retStr += '%d. %s\t%s => %s[%s%%]\n' % (
            idx + 1, d['name'], format(int(d['last_price']), ','), format(int(d['target_price']), ','), str(round(int(d['target_price'])/int(d['last_price'])*100-100, 0)))
    return retStr


def get_high_ranked_stock_with_closeprice():
    from yahoofinancials import YahooFinancials
    import sys
    import os
    import django
    import matplotlib.pyplot as plt
    getConfig()
    sys.path.append(django_path)
    sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    from django.db import connection
    cursor = connection.cursor()
    sql = """select t.code, t.market_text, t.name, t.curr, t.last_price, t.target_price, t.target_price2, t.return_on_equity, t.ratio, t.ratio2, (t.ratio + t.ratio2) / 2 as average_ratio  from (
                select s.code, s.market_text, ts.name, ts.curr, ts.last_price, ts.target_price, ts.target_price2, ts.return_on_equity, ts.ratio, ts.target_price2/ts.last_price*100 as ratio2 from detective_app_targetstocks ts, detective_app_stocks s
                where ts.ratio > 100
                and s.code = ts.code
                --and return_on_equity > 14
                and ts.valuation_date = '%s'
                order by ratio2 desc, return_on_equity desc, ratio desc
                limit 30) as t
             --where last_price > 14000
             --and ratio2 > 100
             order by t.ratio desc""" % yyyymmdd
    cursor.execute(sql)
    # retStr = ''
    fig = plt.figure()
    todaydate = datetime.strptime(yyyymmdd, "%Y-%m-%d")
    before30date = datetime.strptime(yyyymmdd, "%Y-%m-%d") - timedelta(days=30)
    print(str(todaydate)[:10], str(before30date)[:10])
    for idx, d in enumerate(dictfetchall(cursor)):
        dates = []
        prcs = []
        ins_ticker = '{}.KS'.format(d['code']) if d['market_text'].split("\xa0")[0].strip() == 'KSE' else '{}.KQ'.format(d['code'])
        print(idx, ins_ticker)
        instrument = YahooFinancials(ins_ticker)
        prices = instrument.get_historical_price_data(str(before30date)[:10], str(todaydate)[:10], "daily")
        if "prices" not in prices[ins_ticker].keys(): print(prices)
        for info in prices[ins_ticker]['prices']:
            dates.append(info['formatted_date'])
            prcs.append(info['close'])
        print(dates)
        print(prcs)

    #     retStr += '%d. %s\t%s => %s[%s%%]\n' % (
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


# def messeage_to_telegram(txt):
#     import telegram
#     my_token = '577949495:AAFk3JWQjHlbJr2_AtZeonjqQS7buu8cYG4'
#     chat_id = '568559695'
#     bot = telegram.Bot(token=my_token)
#     print(txt)
#     if txt is not None and txt != '':
#         bot.sendMessage(chat_id=chat_id, text=txt)
#     # 진오 =====================================================
#     # my_token = '781845768:AAEG55_jbdDIDlmGXWHl8Ag2aDUg-YAA8fc'
#     # chat_id = '84410715'
#     # bot = telegram.Bot(token=my_token)
#     # if txt is not None and txt != '':
#     #         bot.sendMessage(chat_id=chat_id, text=txt)
#     # ==========================================================
#     # 아부지====================================================
#     # my_token = '866257502:AAH3zxEzlNT-venJnI-ZacJBwrnh2nxLsNk'
#     # chat_id = '869289245'
#     # bot = telegram.Bot(token=my_token)
#     # if txt is not None and txt != '':
#     #         bot.sendMessage(chat_id=chat_id, text=txt)
#     # ==========================================================
#
#     # my_token = '781845768:AAEG55_jbdDIDlmGXWH18Ag2aDUg-YAA8fc'
#     # bot = telegram.Bot(token=my_token)
#     # updates = bot.getUpdates()
#     # for u in updates:
#     #     print(u.message)


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

    req_rate = 8.0
    treasure = {}
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
    try:
        JsonDir = '%s\ResultJson' % path
        if not os.path.exists(JsonDir):
            os.makedirs(JsonDir)
        if os.path.exists(r'%s\result.%s.json' % (JsonDir, yyyymmdd)) and USE_JSON:
            with open(r'%s\result.%s.json' % (JsonDir, yyyymmdd), "r") as f:
                data = f.read()
                treasure = json.loads(data)
                # print(treasure)
        for ii, stock in enumerate(stockInfo):
            # if ii > 10: break
            if stock.code in treasure.keys():
                # print("stock.code in treasure.keys()")
                continue
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
                    if dic[key][0]['VAL3'] == '-':
                        # print("정보부족")
                        info_lack = True
                        break
                    else:
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

            # marketTxt = fnguide.select_by_attr(soup, 'span', 'id', 'strMarketTxt').text.replace(' ', '') # 업종분류
            # data['업종구분'] = marketTxt.replace('\n', '')
            # # print(data['업종구분'], stock.market_text)
            # if data['업종구분'] != '' and stock.market_text is None:
            #     fnguide.StockMarketTextUpdate(stock.code, marketTxt)
            marketTxt = fnguide.select_by_attr(soup, 'span', 'class', 'stxt stxt1').text.replace(' ', '')  # 업종분류
            data['업종구분'] = marketTxt.replace('\n', '')
            marketTxt = fnguide.select_by_attr(soup, 'span', 'class', 'stxt stxt2').text.replace(' ', '')  # 업종분류
            data['업종구분상세'] = marketTxt.replace('\n', '')
            # print(data['업종구분'], stock.market_text)
            if (data['업종구분'] != '' and stock.market_text is None) or (data['업종구분상세'] != '' and stock.market_text_detail is None):
                fnguide.StockMarketTextUpdate(stock.code, data['업종구분'], data['업종구분상세'])
            # 업종구분까지 업데이트 한 후 Valuation 정보가 부족한 종목은 Pass
            if info_lack:
                # print("Lack of information")
                continue
            yearly_highlight = fnguide.select_by_attr(soup, 'div', 'id', 'highlight_D_Y')  # Snapshot FinancialHighlight
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
                    if i in ['지배주주순이익', '지배주주지분', '자산총계', '매출액', '이자수익', '보험료수익', '순영업수익', '영업수익']:
                        for idx2, yyyymm in enumerate(columns):
                            # print(idx2, yyyymm)
                            # print(yyyymm[:4], dateDict['yyyy'], i, values[idx][idx2])
                            if yyyymm[:4] == dateDict['yyyy'] and values[idx][idx2] != '':
                                data['Period'] = yyyymm
                                data[i] = float(values[idx][idx2].replace(',', '')) * 100000000
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
                if not set(['지배주주순이익', '지배주주지분', '자산총계']).issubset(data.keys()): continue
                daily = fnguide.select_by_attr(soup, 'div', 'id', 'svdMainGrid1')  # Snapshot 시세현황1
                columns, items, values = fnguide.setting(
                    fnguide.get_table_contents(daily, 'table thead tr th')[1:],
                    fnguide.get_table_contents(daily, 'table tbody tr th'),
                    fnguide.get_table_contents(daily, 'table tbody tr td'))
                # if DEBUG: print(columns, items, values)
                for idx, col in enumerate(columns):
                    # print(col, values[idx])
                    if col in ['종가', '외국인 보유비중', '비율', '거래량']:
                        data[col] = float(values[idx].replace(',', '')) if (values[idx] is not None and values[idx] != '') else 0.0
                        # break
                    if col in ['발행주식수-보통주'] and data['발행주식수'] != float(values[idx].replace(',', '')):
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
                if 'X지배주주순이익' not in data.keys(): data['X지배주주순이익'] = 0.0
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
            if treasure[d]['X지배주주순이익'] < 1 or \
               treasure[d]['ROE'] < 15 or \
               treasure[d]['지배주주지분'] / treasure[d]['자산총계'] < 0.51 or \
               treasure[d]['ROE'] < treasure[d]['요구수익률'] or \
               treasure[d]['업종구분'].replace('\n', '') in ['코스닥제조', '코스피제조업', '코스피건설업', '코스닥건설'] or \
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
        print(HIGH_ROS)
        if os.path.exists(r'%s\result.%s.json' % (JsonDir, yyyymmdd)):
            os.remove(r'%s\result.%s.json' % (JsonDir, yyyymmdd))
        with open(r'%s\result.%s.json' % (JsonDir, yyyymmdd), 'w') as fp:
            json.dump(treasure, fp)
    except Exception as e:
        print('error', e, '\n', stock)
        if os.path.exists(r'%s\result.%s.json' % (JsonDir, yyyymmdd)):
            os.remove(r'%s\result.%s.json' % (JsonDir, yyyymmdd))
        with open(r'%s\result.%s.json' % (JsonDir, yyyymmdd), 'w') as fp:
            json.dump(treasure, fp)


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

        print("[TargetStocks][%s] information Deleted successfully" % yyyymmdd)
        # print("[%s][%s][%s] information stored successfully" % (report_name, crp_cd, crp_nm))
    except Exception as e:
        print('[Error on TargetStockDataDelete]\n', '*' * 50, e)


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

        print("[TargetStocks][%s][%s] information stored successfully" % (crp_cd, data['회사명']))
        # print("[%s][%s][%s] information stored successfully" % (report_name, crp_cd, crp_nm))
    except Exception as e:
        print('[Error on TargetStockDataStore]\n', '*' * 50, e)

if __name__ == '__main__':
    # get_high_ranked_stock_with_closeprice()
    # find_hidden_pearl()
    # messeage_to_telegram()
    # find_hidden_pearl()
    # test_find_hidden_pearl()
    new_find_hidden_pearl()
    # msgr.messeage_to_telegram(get_high_ranked_stock())
    # new_get_dateDict()
    # getConfig()
    # report_type = 'financeRatio'
    # crp_nm = '삼성전자'
    # crp_cd = '005930'
    # aa = get_soup_from_file(report_type, yyyymmdd, crp_nm, crp_cd)
    # print(len(aa.find_all('div')))
