from fredapi import Fred
import detective.crawler as tool
import json

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

def getConfig():
    import configparser
    global path, django_path, main_path, api_key
    config = configparser.ConfigParser()
    config.read('config.ini')
    path = config['COMMON']['PROJECT_PATH']
    django_path = path + r'\MainBoard'
    main_path = django_path + r'\MainBoard'
    api_key = config['FRED']['FREDAPI_KEY']

def getDataFromFRED():
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
    for a in data['categories']:
        print(a)
        # print(a, data[a])

if __name__ == '__main__':
    getDataFromFRED()
