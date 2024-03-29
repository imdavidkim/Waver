from datetime import datetime


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


def getInstrumentInfo():
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
    result = detective_db.Instrument.objects.filter(in_use=True)

    retDic = {}
    for r in result:
        retDic[str(r.external_id)] = {'id': r.id, 'name': r.name, 'new': False}

    return retDic


def getMarketInfo():
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
    result = detective_db.Market.objects.filter(in_use=True)

    retDic = {}
    for r in result:
        retDic[r.name] = r.id

    return retDic

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
                                                                    'dart_corp_code': retDict[key]['DART코드'],
                                                                    'issued_shares': float(
                                                                        retDict[key]['상장주식수'].replace(',', '')),
                                                                    'capital': float(
                                                                        retDict[key]['자본금'].replace(',', '')),
                                                                    'par_value': float(
                                                                        retDict[key]['액면가'].replace(',', '')) if
                                                                    retDict[key]['액면가'] != "무액면" else 0,
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


def InstrumentResister(ins_info):
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
        info = detective_db.Instrument.objects.update_or_create(external_id=ins_info['id']
                                                                , name=ins_info['name']
                                                                , in_use=ins_info['new']
                                                                )

        print("[InstrumentResister][%s][%s] information stored successfully" % (ins_info['id'], ins_info['name']))
    except Exception as e:
        print('[Error on InstrumentResister]\n', '*' * 50, e)


def KofiaBondDataStore(base_date, instrument_id, market_id, value):
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
        info = detective_db.MarketDataValue.objects.update_or_create(base_date=base_date
                                                                     , instrument_id=instrument_id
                                                                     , market_id=market_id
                                                                     , value=value
                                                                     )

        # print("[KofiaBondDataStore][%s][%s][%s] information stored successfully" % (base_date, instrument_id, value))
    except Exception as e:
        print('[Error on KofiaBondDataStore]\n', '*' * 50, e)


def KofiaBondMarketStore(mkt_name):
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
        info = detective_db.Market.objects.update_or_create(name=mkt_name)

        print("[KofiaBondMarketStore][%s] information stored successfully" % mkt_name)
    except Exception as e:
        print('[Error on KofiaBondMarketStore]\n', '*' * 50, e)


def UpdateFnguideExist(ticker):
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
        info = detective_db.USNasdaqStocks.objects.filter(ticker=ticker).update(fnguide_exist='N')
        print("[UpdateFnguideExist][%s] information updated not to use successfully" % ticker)
    except Exception as e:
        print('[Error on UpdateFnguideExist]\n', '*' * 50, e)


def ResultListDataStore(retJson):
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
        for jsonData in retJson["list"]:
            info = detective_db.DartRequestListResult.objects.update_or_create(rcept_no=jsonData['rcept_no'],
                                                                               defaults={
                                                                                   'corp_cls': jsonData['corp_cls'],
                                                                                   'stock_code': jsonData['stock_code'],
                                                                                   'corp_name': jsonData['corp_name'],
                                                                                   'corp_code': jsonData['corp_code'],
                                                                                   'report_nm': jsonData['report_nm'],
                                                                                   'flr_nm': jsonData['flr_nm'],
                                                                                   'rcept_dt': jsonData['rcept_dt'],
                                                                                   'rm': jsonData['rm'],
                                                                                   'link': "http://dart.fss.or.kr/dsaf001/main.do?rcpNo=" +
                                                                                           jsonData['rcept_no'],
                                                                               }
                                                                               )
            print("[{}][{}][{}][{}] information stored successfully".format(jsonData['rcept_dt'], jsonData['rcept_no'],
                                                                            jsonData['corp_name'],
                                                                            jsonData['report_nm']))
    except Exception as e:
        print('[Error on ResultListDataStore]\n', '*' * 50, e)


def ResultMajorShareholderDataStore(jsonData):
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
        # for jsonData in retJson["list"]:
        info = detective_db.DartRequestMajorStockResult.objects.update_or_create(rcept_no=jsonData['rcept_no'],
                                                                                 defaults={
                                                                                     'rcept_dt': jsonData['rcept_dt'],
                                                                                     'corp_code': jsonData['corp_code'],
                                                                                     'corp_name': jsonData['corp_name'],
                                                                                     'report_tp': jsonData['report_tp'],
                                                                                     'repror': jsonData['repror'],
                                                                                     'stkqy': jsonData['stkqy'],
                                                                                     'stkqy_irds': jsonData['stkqy_irds'],
                                                                                     'stkrt': jsonData['stkrt'],
                                                                                     'stkrt_irds': jsonData['stkrt_irds'],
                                                                                     'ctr_stkqy': jsonData['ctr_stkqy'],
                                                                                     'ctr_stkrt': jsonData['ctr_stkrt'],
                                                                                     'report_resn': jsonData['report_resn'],
                                                                                     'link': "http://dart.fss.or.kr/dsaf001/main.do?rcpNo=" +
                                                                                             jsonData['rcept_no'],
                                                                                 }
                                                                                 )
        print("[{}][{}][{}][{}][{}({})][{}][{}][{}] {}".format(jsonData['rcept_dt'], jsonData['corp_name'],
                                                           jsonData['repror'], jsonData['stkqy'], jsonData['stkrt'],
                                                           jsonData['stkrt_irds'], jsonData['ctr_stkqy'],
                                                           jsonData['ctr_stkrt'],
                                                           "http://dart.fss.or.kr/dsaf001/main.do?rcpNo=" +
                                                           jsonData['rcept_no'],
                                                           jsonData['report_resn']))

        #     rcept_no = models.CharField(max_length=20, unique=True, primary_key=True)
        #     rcept_dt = models.CharField(max_length=8)
        #     stock_code = models.CharField(max_length=20)
        #     cmpny_nm = models.TextField(default='')
        #     report_tp = models.TextField(default='')
        #     repror = models.TextField(default='')
        #     stkqy = models.TextField(default='')
        #     stkqy_irds = models.TextField(default='')
        #     stkrt = models.TextField(default='')
        #     stkrt_irds = models.TextField(default='')
        #     ctr_stkqy = models.TextField(default='')
        #     ctr_stkrt = models.TextField(default='')
        #     report_resn = models.TextField(default='')
    except Exception as e:
        print('[Error on ResultListDataStore]\n', '*' * 50, e)


def getMajorShareholderReportingInfo(date):
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
    result = detective_db.DartRequestListResult.objects.filter(rcept_dt__gte=date).filter(
        report_nm__contains="대량보유").values("rcept_no", "stock_code", "corp_code", "corp_name", "report_nm").distinct()
    # result = detective_db.DartRequestListResult.objects.filter(rcept_dt__gte=date).filter(corp_cls="Y").filter(report_nm__contains="대량보유").values("corp_code").distinct()

    return result


def getFreeCapitalIncreaseEventReportingInfo(date):
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
    result = detective_db.DartRequestListResult.objects.filter(rcept_dt__gte=date).filter(
        report_nm__contains="무상").values("rcept_no", "stock_code", "corp_code", "corp_name", "report_nm").exclude(report_nm__contains="정정").distinct()
    # result = detective_db.DartRequestListResult.objects.filter(rcept_dt__gte=date).filter(corp_cls="Y").filter(report_nm__contains="대량보유").values("corp_code").distinct()

    return result

def getRegularReportingInfo(rcept_no, date, target_date=None):
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
    if target_date is None:
        if rcept_no:
            result = detective_db.DartRequestListResult.objects.filter(rcept_dt__gte=date).filter(
                rcept_dt__lte=target_date).filter(
                rcept_no__gte=rcept_no).filter(
                report_nm__contains="보고서").values("rcept_no", "stock_code", "corp_code", "corp_name",
                                                  "report_nm").exclude(
                report_nm__contains="정정").order_by("rcept_no").distinct()
        else:
            result = detective_db.DartRequestListResult.objects.filter(rcept_dt__gte=date).filter(
                rcept_dt__lte=target_date).filter(
                report_nm__contains="보고서").values("rcept_no", "stock_code", "corp_code", "corp_name", "report_nm").exclude(
                report_nm__contains="정정").order_by("rcept_no").distinct()
    else:
        if rcept_no:
            result = detective_db.DartRequestListResult.objects.filter(rcept_dt__gte=date).filter(
                rcept_no__gte=rcept_no).filter(
                report_nm__contains="보고서").values("rcept_no", "stock_code", "corp_code", "corp_name",
                                                  "report_nm").exclude(
                report_nm__contains="정정").order_by("rcept_no").distinct()
        else:
            result = detective_db.DartRequestListResult.objects.filter(rcept_dt__gte=date).filter(
                report_nm__contains="보고서").values("rcept_no", "stock_code", "corp_code", "corp_name", "report_nm").exclude(
                report_nm__contains="정정").order_by("rcept_no").distinct()
    # result = detective_db.DartRequestListResult.objects.filter(rcept_dt__gte=date).filter(corp_cls="Y").filter(report_nm__contains="대량보유").values("corp_code").distinct()

    return result

def getProvisionalPerformanceReportingInfo(date, target_date=None):
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
    result = None
    if target_date is None:
        result = detective_db.DartRequestListResult.objects.filter(rcept_dt__gte=date).filter(
            report_nm__contains="(잠정)실적").values("rcept_no", "stock_code", "corp_code", "corp_name", "report_nm").distinct()
    else:
        result = detective_db.DartRequestListResult.objects.filter(rcept_dt__gte=date).filter(
            rcept_dt__lte=target_date).filter(
            report_nm__contains="(잠정)실적").values("rcept_no", "stock_code", "corp_code", "corp_name", "report_nm").distinct()
    return result


def getProvisionalPerformanceReportingInfoWithStockCode(code, date, target_date=None):
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
    result = None
    if target_date is None:
        result = detective_db.DartRequestListResult.objects.filter(stock_code=code, rcept_dt__gte=date).filter(
            report_nm__contains="(잠정)실적").values("rcept_no", "stock_code", "corp_code", "corp_name", "report_nm").distinct()
    else:
        result = detective_db.DartRequestListResult.objects.filter(stock_code=code, rcept_dt__gte=date, rcept_dt__lte=target_date).filter(
            report_nm__contains="(잠정)실적").values("rcept_no", "stock_code", "corp_code", "corp_name", "report_nm").distinct()
    return result
