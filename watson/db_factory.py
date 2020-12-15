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


def ResultMajorShareholderDataStore(retJson):
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
        report_nm__contains="대량보유").values("corp_code", "corp_name").distinct()
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
        report_nm__contains="무상").values("corp_code", "corp_name").distinct()
    # result = detective_db.DartRequestListResult.objects.filter(rcept_dt__gte=date).filter(corp_cls="Y").filter(report_nm__contains="대량보유").values("corp_code").distinct()

    return result

