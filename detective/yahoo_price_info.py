from yahoofinancials import YahooFinancials
import pandas as pd
import os
from datetime import datetime, timedelta
import detective.messenger as msgr


def getConfig():
    import configparser

    global path, django_path, main_path, yyyymmdd
    config = configparser.ConfigParser()
    config.read('config.ini')
    path = config['COMMON']['REPORT_PATH']
    django_path = path + r'\MainBoard'
    main_path = django_path + r'\MainBoard'
    yyyymmdd = str(datetime.now())[:10]


class YFPrice():
    ticker = None
    yf_obj = None
    prices = None
    data = {}

    def setting(self, ticker):
        self.ticker = ticker
        self.yf_obj = YahooFinancials(self.ticker)
        self.prices = None
        self.data = {}

    def get_data(self, fromdt, todt, period, srch_term):
        self.prices = self.yf_obj.get_historical_price_data(fromdt, todt, period)
        for key in self.prices.keys():
            # print(key, prices[key])
            if isinstance(self.prices[key], dict):
                for inner_key in self.prices[key].keys():
                    # print(inner_key, self.prices[key][inner_key])
                    if inner_key == 'prices':
                        for d in self.prices[key][inner_key]:
                            self.data[pd.to_datetime(d['formatted_date'], format='%Y-%m-%d').to_pydatetime()] = d[srch_term]
        return pd.Series(self.data)

    def close(self):
        self.ticker = None
        self.yf_obj = None
        self.prices = None
        self.data = {}

# def make_USDKRWKOSPI_graph():
#     import matplotlib.pyplot as plt
#     from detective.naver_api import getNaverPrice
#     getConfig()
#     daydiff = 180
#     fromdt = datetime.strptime(yyyymmdd, "%Y-%m-%d") - timedelta(days=daydiff)
#     obj = YFPrice()
#     obj.setting('KRW=X')
#     retVal = obj.get_data(fromdt.strftime("%Y-%m-%d"), yyyymmdd, 'daily', 'close')
#     obj.close()
#     retVal2 = getNaverPrice('INDEX', 'KPI200', 21)
#     # print(retVal2)
#     fig, ax1 = plt.subplots()
#     ax2 = ax1.twinx()
#     ax1.plot(retVal, 'r-')
#     ax2.plot(retVal2, 'b-')
#     ax1.set_xlabel('Date')
#     ax1.set_ylabel('USD/KRW', color='r')
#     ax2.set_ylabel('KOSPI200', color='b')
#     plt.show()


def make_USDKRW_graph():
    # from importlib import reload
    import matplotlib.pyplot as plt
    # reload(plt)
    from detective.naver_api import getNaverPrice
    getConfig()
    daydiff = 180
    try:
        fromdt = datetime.strptime(yyyymmdd, "%Y-%m-%d") - timedelta(days=daydiff)
        obj = YFPrice()
        obj.setting('KRW=X')
        retVal = obj.get_data(fromdt.strftime("%Y-%m-%d"), yyyymmdd, 'daily', 'close')
        obj.close()
        retVal2 = getNaverPrice('INDEX', 'KPI200', 21)
        # print(retVal)
        # print(retVal2)
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        ax1.plot(retVal, 'r-')
        ax2.plot(retVal2, 'b-')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('USD/KRW', color='r')
        ax2.set_ylabel('KOSPI200', color='b')
        plt.xticks(rotation=45)
        plt.grid(True, axis='y', color='gray', alpha=0.5, linestyle='--')
        img_path = r'{}\{}\{}'.format(path, 'EX_RATE', yyyymmdd)
        print(img_path)
        if not os.path.exists(img_path):
            os.makedirs(img_path)
        plt.savefig(img_path + '\\result.png')
        msgr.img_messeage_to_telegram(img_path + '\\result.png')
        plt.close('all')
    except Exception as e:
        print(e)
        plt.close('all')


def getISMIndexDataSet():
    from detective.fnguide_collector import httpRequest
    import json
    getConfig()
    retArrayDate = []
    retArrayData = []
    url = 'https://sbcharts.investing.com/events_charts/us/173.json'  # ISM Index
    jo = json.loads(httpRequest(url, None, 'GET', None).decode('utf-8'))
    for key in jo.keys():
        if key == 'data':
            for d in jo[key]:
                retArrayDate.append(datetime.strptime(datetime.fromtimestamp(d[0] / 1000).strftime('%Y-%m-%d'), '%Y-%m-%d'))
                retArrayData.append(d[1])
    return retArrayDate, retArrayData
    # return pd.Series(retArrayData, retArrayDate).tail(120)

def getSvcPMIIndexDataSet():
    from detective.fnguide_collector import httpRequest
    import json
    getConfig()
    retArrayDate = []
    retArrayData = []
    url = 'https://sbcharts.investing.com/events_charts/us/1062.json'  # ISM Index
    jo = json.loads(httpRequest(url, None, 'GET', None).decode('utf-8'))
    for key in jo.keys():
        if key == 'data':
            for d in jo[key]:
                retArrayDate.append(datetime.strptime(datetime.fromtimestamp(d[0] / 1000).strftime('%Y-%m-%d'), '%Y-%m-%d'))
                retArrayData.append(d[1])
    return retArrayDate, retArrayData

def make_ISMIndex_graph():
    # from importlib import reload
    import matplotlib.pyplot as plt
    # reload(plt)
    import os
    from matplotlib import font_manager, rc
    import detective.messenger as msgr
    getConfig()

    font_path = r"C:/Windows/Fonts/KoPubDotum_Pro_Light.otf"
    # 폰트 이름 얻어오기
    font_name = font_manager.FontProperties(fname=font_path).get_name()
    # font 설정
    rc('font', family=font_name)

    try:
        retArrayDate, retArrayData = getISMIndexDataSet()
        retVal = pd.core.series.Series(retArrayData, retArrayDate)[-60:]
        # retVal = getISMIndexDataSet()[-60:]
        obj = YFPrice()
        obj.setting('^IXIC')
        retVal2 = obj.get_data(retArrayDate[-60].strftime("%Y-%m-%d"), yyyymmdd, 'monthly', 'close')
        obj.close()
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        ax1.plot(retVal, 'm-')
        ax2.plot(retVal2, 'g-')
        ax1.set_ylabel('ISM PMI', color='m')
        ax2.set_ylabel('Nasdaq Comp.', color='g')
        # plt.legend(loc='upper center')
        # plt.xticks(rotation=45)
        plt.grid(True, axis='y', color='gray', alpha=0.5, linestyle='--')
        plt.title("미국ISM 제조업구매자지수 & Nasdaq")
        # plt.show()
        img_path = r'{}\{}\{}'.format(path, 'ISM_PMI', yyyymmdd)
        print(img_path)
        if not os.path.exists(img_path):
            os.makedirs(img_path)
        plt.savefig(img_path + '\\result.png')
        msgr.img_messeage_to_telegram(img_path + '\\result.png')
        plt.close('all')
    except Exception as e:
        print(e)
        plt.close('all')

def make_SvcPMIIndex_graph():
    # from importlib import reload
    import matplotlib.pyplot as plt
    # reload(plt)
    import os
    from matplotlib import font_manager, rc
    import detective.messenger as msgr
    getConfig()

    font_path = r"C:/Windows/Fonts/KoPubDotum_Pro_Light.otf"
    # 폰트 이름 얻어오기
    font_name = font_manager.FontProperties(fname=font_path).get_name()
    # font 설정
    rc('font', family=font_name)

    try:
        retArrayDate, retArrayData = getSvcPMIIndexDataSet()
        retVal = pd.core.series.Series(retArrayData, retArrayDate)[-60:]
        # retVal = getISMIndexDataSet()[-60:]
        obj = YFPrice()
        obj.setting('^GSPC')
        retVal2 = obj.get_data(retArrayDate[-60].strftime("%Y-%m-%d"), yyyymmdd, 'monthly', 'close')
        obj.close()
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        ax1.plot(retVal, 'm-')
        ax2.plot(retVal2, 'g-')
        ax1.set_ylabel('Service PMI', color='m')
        ax2.set_ylabel('S&P500.', color='g')
        # plt.legend(loc='upper center')
        # plt.xticks(rotation=45)
        plt.grid(True, axis='y', color='gray', alpha=0.5, linestyle='--')
        plt.title("미국 서비스 제조업구매자지수 & S&P500지수")
        # plt.show()
        img_path = r'{}\{}\{}'.format(path, 'SVC_PMI', yyyymmdd)
        print(img_path)
        if not os.path.exists(img_path):
            os.makedirs(img_path)
        plt.savefig(img_path + '\\result.png')
        msgr.img_messeage_to_telegram(img_path + '\\result.png')
        plt.close('all')
    except Exception as e:
        print(e)
        plt.close('all')

if __name__ == '__main__':
    # print(yahoo_financials)
    #
    # tech_stocks = ['AAPL', 'MSFT', 'INTC']
    # yahoo_financials_tech = YahooFinancials(tech_stocks)
    # tech_cash_flow_data_an = yahoo_financials_tech.get_financial_stmts('annual', 'cash')
    # for s in tech_cash_flow_data_an["cashflowStatementHistory"]:
    #     for date in tech_cash_flow_data_an["cashflowStatementHistory"][s][0]:
    #         print(s, date, tech_cash_flow_data_an["cashflowStatementHistory"][s][0][date])
    make_USDKRW_graph()
    # make_USDKRWKOSPI_graph()
