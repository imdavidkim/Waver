# -*- coding: utf-8 -*-

# import pandas as pd
# import numpy as np
# import requests
# from io import BytesIO
# from datetime import datetime, timedelta
# from bs4 import BeautifulSoup
# import pprint
# import csv
# import xmltodict
# import os



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
    sys.path.append(r'E:\Github\Waver\MainBoard')
    sys.path.append(r'E:\Github\Waver\MainBoard\MainBoard')
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    from django.db import connection
    cursor = connection.cursor()
    sql = "SELECT strftime('%Y','now') as yyyy, strftime('%m','now') as mm, strftime('%d','now') as dd, strftime('%Y-%m-%d','now') as yyyymmdd"
    cursor.execute(sql)
    return dictfetchall(cursor)[0]


def get_max_date_on_dailysnapshot(crp_cd):
    import sys
    import os
    import django
    sys.path.append(r'E:\Github\Waver\MainBoard')
    sys.path.append(r'E:\Github\Waver\MainBoard\MainBoard')
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


def align_string(switch, text, digit):
    if switch == 'L':
        return format(text, " <%d" % digit)
    elif switch == 'R':
        return format(text, " >%d" % digit)
    elif switch == ',':
        return format(format(float(text), ','), " >%d" % digit)
    else:
        return None


def messeage_to_telegram():
    import telegram
    my_token = '577949495:AAFk3JWQjHlbJr2_AtZeonjqQS7buu8cYG4'
    chat_id = '568559695'
    bot = telegram.Bot(token=my_token)
    bot.sendMessage(chat_id=chat_id, text="GG")
    # updates = bot.getUpdates()
    # for u in updates:
    #     print(u.message)


def get_dailysnapshot_objects(rpt_nm, rpt_tp, column_nm, crp_cd, dateDict):
    import sys
    import os
    import django
    sys.path.append(r'E:\Github\Waver\MainBoard')
    sys.path.append(r'E:\Github\Waver\MainBoard\MainBoard')
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
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
    sys.path.append(r'E:\Github\Waver\MainBoard')
    sys.path.append(r'E:\Github\Waver\MainBoard\MainBoard')
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


def find_hidden_pearl():
    import sys
    import os
    import django
    sys.path.append(r'E:\Github\Waver\MainBoard')
    sys.path.append(r'E:\Github\Waver\MainBoard\MainBoard')
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    treasure = {}
    data = {}
    # 날짜 정보 셋팅
    dateDict = get_dateDict()
    # 종목 정보 셋팅
    stockInfo = detective_db.Stocks.objects.filter(listing='Y')
    # stockInfo = detective_db.Stocks.objects.filter(code='005930', listing='Y')
    print(align_string('R', 'Code', 10),
          align_string('R', 'Name', 20),
          align_string('R', 'Issued Shares', 20),
          align_string('R', 'Capital', 20),
          align_string('R', 'ParValue', 10),
          '\n')
    # 예상되는 당기순이익 조회 조건 셋팅
    rpt_nm = 'FinancialHighlight'
    rpt_tp = 'IFRS(연결)'
    disc_categorizing = 'YEARLY'
    # disc_categorizing = 'QUARTERLY'
    fix_or_prov_or_estm = 'E'
    # ----------------------------------
    try:
        for stock in stockInfo:
            data = {}
            # print(dir(stock))
            print(align_string('R', stock.code, 10),
                  align_string('R', stock.name, 20-len(stock.name)),
                  align_string(',', stock.issued_shares, 20),
                  align_string(',', stock.capital, 20),
                  align_string('R', stock.par_value, 10),
                  )
            # data['회사명'] = stock.name
            # data['발행주식수'] = stock.issued_shares
            # data['자본금'] = stock.capital
            # data['액면가'] = stock.par_value
            accnt_nm = '지배주주순이익'
            snapshot = get_snapshot_objects(rpt_nm,
                                            rpt_tp,
                                            accnt_nm,
                                            disc_categorizing,
                                            fix_or_prov_or_estm,
                                            stock.code,
                                            dateDict)
            accnt_nm = '지배주주지분'
            snapshot2 = get_snapshot_objects(rpt_nm,
                                             rpt_tp,
                                             accnt_nm,
                                             disc_categorizing,
                                             fix_or_prov_or_estm,
                                             stock.code,
                                             dateDict)
            accnt_nm = 'ROE'
            snapshot3 = get_snapshot_objects(rpt_nm,
                                             rpt_tp,
                                             accnt_nm,
                                             disc_categorizing,
                                             fix_or_prov_or_estm,
                                             stock.code,
                                             dateDict)
            rpt_nm2 = '시세현황1'
            rpt_tp2 = ''
            column_nm = '종가'
            daily = get_dailysnapshot_objects(rpt_nm2, rpt_tp2, column_nm, stock.code, dateDict)
            # print(snapshot)
            # print(snapshot2)
            # print(snapshot3)
            if len(snapshot) > 0 and len(snapshot2) > 0 and len(snapshot3) > 0:
                data['회사명'] = stock.name
                data['발행주식수'] = stock.issued_shares
                data['자본금'] = stock.capital
                data['액면가'] = stock.par_value
                data['통화'] = stock.curr
                data[snapshot[0]['accnt_nm']] = snapshot[0]['value'] * 100000000
                data[snapshot2[0]['accnt_nm']] = snapshot2[0]['value'] * 100000000
                data[snapshot3[0]['accnt_nm']] = snapshot3[0]['value']
                data['RAW_ROE'] = data['지배주주순이익'] / data['지배주주지분'] * 100
                data['ADJ_ROE'] = (data['ROE'] + data['RAW_ROE']) / 2
                data['주주가치'] = data['지배주주지분'] + (data['지배주주지분'] * (data['ADJ_ROE'] - 10.0) / 10.0)
                data['NPV'] = data['주주가치'] / data['발행주식수']
                data['종가'] = daily[0]['value']
                treasure[stock.code] = data
            # print(data)
        # print(treasure)
        print('='*50, '마이너스', '='*50)
        for d in treasure.keys():
            if treasure[d]['NPV'] < 0:
                print(align_string('R', d, 10),
                      align_string('R', treasure[d]['회사명'], 20 - len(treasure[d]['회사명'])),
                      align_string(',', treasure[d]['RAW_ROE'], 20),
                      align_string(',', treasure[d]['지배주주지분'], 20),
                      align_string(',', treasure[d]['주주가치'], 20),
                      align_string(',', treasure[d]['NPV'], 20),
                      align_string(',', treasure[d]['종가'], 10),
                      )
                continue
            # print(d, treasure[d]['회사명'])
            TargetStockDataStore(d, treasure[d])
    except Exception as e:
        print('error', e)


def TargetStockDataStore(crp_cd, data):
    import sys
    import os
    import django
    from datetime import datetime
    sys.path.append(r'E:\Github\Waver\MainBoard')
    sys.path.append(r'E:\Github\Waver\MainBoard\MainBoard')
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    try:
        info = detective_db.TargetStocks.objects.update_or_create(code=crp_cd,
                                                                  name=data['회사명'],
                                                                  curr=data['통화'],
                                                                  last_price=data['종가'],
                                                                  target_price=data['NPV'],
                                                                  ratio=data['NPV']/data['종가']*100
                                                                  )

        # print("[TargetStocks][%s][%s] information stored successfully" % (crp_cd, data['회사명']))
        # print("[%s][%s][%s] information stored successfully" % (report_name, crp_cd, crp_nm))
    except Exception as e:
        print('[Error on TargetStockDataStore]\n', '*' * 50, e)

if __name__ == '__main__':
    # find_hidden_pearl()
    # messeage_to_telegram()
    find_hidden_pearl()