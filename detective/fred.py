from fredapi import Fred
import detective.crawler as tool
import json

import pandas
import numpy as np
# import matplotlib.pyplot as plt
import os
from datetime import datetime
import detective.messenger as msgr

from matplotlib import font_manager, rc

# 각종 필요지표
# 10-Year Treasury Constant Maturity Minus 2-Year Treasury Constant Maturity
# https://fred.stlouisfed.org/series/T10Y2Y
# 10-Year Breakeven Inflation Rate(물가변화)
# https://fred.stlouisfed.org/series/T10YIE
# 5-Year, 5-Year Forward Inflation Expectation Rate(예측물가)
# https://fred.stlouisfed.org/series/T5YIFR
# ICE BofAML US High Yield Master II Option-Adjusted Spread
# https://fred.stlouisfed.org/series/BAMLH0A0HYM2
# ICE BofAML Emerging Markets Corporate Plus Index Option-Adjusted Spread (BAMLEMCBPIOAS)
# https://fred.stlouisfed.org/series/BAMLEMCBPIOAS
db_fred_category = []

def getConfig():
    import configparser

    global path, django_path, main_path, api_key, yyyymmdd
    config = configparser.ConfigParser()
    config.read('config.ini')
    path = config['COMMON']['REPORT_PATH']
    django_path = path + r'\MainBoard'
    main_path = django_path + r'\MainBoard'
    api_key = config['FRED']['FREDAPI_KEY']
    yyyymmdd = str(datetime.now())[:10]


def getSeriesDataFromFRED(key):
    getConfig()
    fred = Fred(api_key=api_key)
    result = fred.get_series(key)
    return result


def getRootDataFromFRED():
    getConfig()
    fred = Fred(api_key=api_key)
    # result = fred.search_by_category(33446, limit=5, order_by="popularity")
    url = 'https://api.stlouisfed.org/fred/category/children?api_key={}&file_type={}'.format(api_key, 'json')
    print(url)
    # result = fred.get_series('T10Y2Y')
    result = tool.httpRequest(url, None, None, 'GET')
    data_trans = result.decode('utf8').replace("'", '"')
    # print(result.decode('utf8').replace("'", '"'))
    data = json.loads(data_trans)
    # print(data)
    # print(result)
    for d in data['categories']:
        FredStatisticCategoryStore(d['id'], d['name'], d['parent_id'])
        getDataFromParentId(d['id'])
        # print(a, data[a])


def getDataFromParentId(parent_id, check=None):
    global db_fred_category
    # import ast
    getConfig()
    fred = Fred(api_key=api_key)
    # result = fred.search_by_category(33446, limit=5, order_by="popularity")
    url = 'https://api.stlouisfed.org/fred/category/children?category_id={}&api_key={}&file_type={}'.format(parent_id, api_key, 'json')
    print(url)
    # result = fred.get_series('T10Y2Y')
    result = tool.httpRequest(url, None, None, 'GET')
    data_trans = result.decode('utf8').replace("'", '"')
    # print(result.decode('utf8').replace("'", '"'))
    print(data_trans.replace("s\" ", "s\' "))
    if check is not None:
        return json.loads(data_trans.replace("\"s", "\'s").replace("s\" ", "s\' ").replace("\"t", "\'t"))
    else:
        data = json.loads(data_trans.replace("\"s", "\'s").replace("s\" ", "s\' ").replace("\"t", "\'t"))
    # print(data)
    # print(result)
    for d in data['categories']:
        if 'notes' in d.keys():
            FredStatisticCategoryStore(d['id'], d['name'], d['parent_id'], d['notes'])
        else:
            FredStatisticCategoryStore(d['id'], d['name'], d['parent_id'])
        if d['parent_id'] in [9, 11, 13, 12, 21, 22, 23, 24, 46, 64, 83, 97, 100, 101, 104, 106, 107, 108, 109, 110, 112, 158, 32361, 32379, 32388, 32397, 32406, 32241, 32349, 32370, 33697, 33045, 32251, 32429, 33583, 33584, 32264]:
            continue
        if d['id'] in db_fred_category:
            continue
        if getDataFromParentId(d['id'], True)['categories']:
            getDataFromParentId(d['id'])


def FredStatisticCategoryStore(id, name, parent_id, notes=None):
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
        info = detective_db.FredStatisticCategory.objects.update_or_create(id=id,
                                                                           name=name,
                                                                           parent_id=parent_id,
                                                                           defaults={
                                                                                'notes': notes
                                                                           })

    except Exception as e:
        print('[Error on FredStatisticCategoryStore]\n', '*' * 50, e)


def getFredStatisticCategory(id=None):
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
        if id is not None:
            info = detective_db.FredStatisticCategory.objects.filter(id=id).values_list('id')
        else:
            info = detective_db.FredStatisticCategory.objects.all().values_list('id')
        return info
    except Exception as e:
        print('[Error on FredStatisticCategoryStore]\n', '*' * 50, e)


def make_graph():
    import matplotlib.pyplot as plt
    getConfig()
    retVal = getSeriesDataFromFRED('BAMLEMCBPIOAS')
    retVal2 = getSeriesDataFromFRED('T10Y2Y')
    retVal3 = getSeriesDataFromFRED('T10YIE')
    retVal4 = getSeriesDataFromFRED('BAMLH0A0HYM2')
    fig = plt.figure()
    BAMLEMCBPIOAS = fig.add_subplot(4, 1, 1)
    BAMLH0A0HYM2 = fig.add_subplot(4, 1, 2)
    T10Y2Y = fig.add_subplot(4, 1, 3)
    T10YIE = fig.add_subplot(4, 1, 4)
    BAMLEMCBPIOAS.plot(retVal.tail(180), label="EM OAS")
    BAMLEMCBPIOAS.legend(loc='upper left')
    BAMLH0A0HYM2.plot(retVal4.tail(180), label="US HighYield")
    BAMLH0A0HYM2.legend(loc='upper left')
    T10Y2Y.plot(retVal2.tail(180), label="10Y-2Y")
    T10Y2Y.legend(loc='upper left')
    T10YIE.plot(retVal3.tail(180), label="10Y BEI")
    T10YIE.legend(loc='upper left')
    # plt.show()
    # for id in getFredStatisticCategory():
    #     db_fred_category.append(id[0])
    # getRootDataFromFRED()
    # import Image
    img_path = r'{}\{}\{}'.format(path, 'FRED', yyyymmdd)
    print(img_path)
    if not os.path.exists(img_path):
        os.makedirs(img_path)
    plt.xticks(rotation=45)
    plt.savefig(img_path+'\\result.png')
    msgr.img_messeage_to_telegram(img_path+'\\result.png')
    plt = None


if __name__ == '__main__':
    make_graph()
    # import numpy as np
    # print(np.random.randn(3))
    # print(pandas.core.series.Series())
    # print(type(getSeriesDataFromFRED('BAMLEMCBPIOAS')), getSeriesDataFromFRED('BAMLEMCBPIOAS'))
