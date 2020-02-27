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
