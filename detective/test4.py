# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
import matplotlib.dates as mdates

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

def getMarketData(instrument_id, market_id, count, is_desc, want_sorting):
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
    tmp = None
    result = None
    if is_desc:
        tmp = detective_db.MarketDataValue.objects.filter(instrument_id=instrument_id).filter(
            market_id=market_id).order_by('-base_date').values_list('base_date', 'value')
    else:
        tmp = detective_db.MarketDataValue.objects.filter(instrument_id=instrument_id).filter(
            market_id=market_id).order_by('base_date').values_list('base_date', 'value')
    if count > 0:
        result = list(tmp)[-count:]
    else:
        result = list(tmp)

    if want_sorting:
        sorted_by_date = sorted(result, key=lambda tup: tup[0])
    else:
        sorted_by_date = result
    result1 = [date for date, rate in sorted_by_date]
    result2 = [rate for date, rate in sorted_by_date]
    return result1, result2


if __name__ == '__main__':
    # 폰트 경로
    font_path = r"C:/Windows/Fonts/LGDisplayLight.ttf"
    # 폰트 이름 얻어오기
    font_name = font_manager.FontProperties(fname=font_path).get_name()
    # font 설정
    day = 180
    rc('font', family=font_name)
    date1, data1 = getMarketData(16, 2, day, False, True)
    date2, data2 = getMarketData(1, 2, day, False, True)
    date3, data3 = getMarketData(2, 2, day, False, True)
    date4, data4 = getMarketData(4, 2, day, False, True)
    date5, data5 = getMarketData(14, 2, day, False, True)
    date6, data6 = getMarketData(15, 2, day, False, True)
    a = np.asarray(data1, dtype=np.float32)
    b = np.asarray(data2, dtype=np.float32)
    c = np.asarray(data3, dtype=np.float32)
    d = np.asarray(data4, dtype=np.float32)
    e = np.asarray(data5, dtype=np.float32)
    f = np.asarray(data6, dtype=np.float32)

    g = d - c  # 10년 - 3년(장단기금리차1)
    h = c - a  # 3년 - CD(장단기금리차2)
    i = e - c  # AA - 3년(AA신용스프레드)
    k = f - c  # BBB - 3년(BBB신용스프레드)
    t = np.arange(0, len(a), 1)
    plt.plot(date1, a, label="CD(91일)")
    # plt.plot(t, b, label="국고채권(1년)")
    plt.plot(date1, c, label="국고채권(3년)")
    plt.plot(date1, d, label="국고채권(10년)")
    # plt.plot(t, e, label="회사채(무보증3년)AA-")
    # plt.plot(date1, f, label="회사채(무보증3년)BBB-")
    plt.plot(date1, g, label="10년 - 3년(장단기금리차1)")
    plt.plot(date1, h, label="3년 - CD(장단기금리차2)")
    # plt.plot(t, i, label="AA - 3년(AA신용스프레드)")
    # plt.plot(date1, k, label="BBB - 3년(BBB신용스프레드)")
    # "3006"	"국고채권(1년)"	        "1"
    # "3000"	"국고채권(3년)"	        "2"
    # "3007"	"국고채권(5년)"	        "3"
    # "3013"	"국고채권(10년)"	    "4"
    # "3014"	"국고채권(20년)"	    "5"
    # "3017"	"국고채권(30년)"	    "6"
    # "3018"	"국고채권(50년)"	    "7"
    # "3008"	"국민주택1종(5년)"	    "8"
    # "3015"	"통안증권(91일)"	    "9"
    # "3016"	"통안증권(1년)"	        "10"
    # "3003"	"통안증권(2년)"	        "11"
    # "3002"	"한전채(3년)"	        "12"
    # "3004"	"산금채(1년)"	        "13"
    # "3009"	"회사채(무보증3년)AA-"	"14"
    # "3010"	"회사채(무보증3년)BBB-"	"15"
    # "4000"	"CD(91일)"	            "16"
    # "5000"	"CP(91일)"	            "17"
    plt.legend(loc='upper left')
    plt.show()

