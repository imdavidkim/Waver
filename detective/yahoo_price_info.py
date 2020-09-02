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

def make_USDKRWKOSPI_graph():
    import matplotlib.pyplot as plt
    from detective.naver_api import getNaverPrice
    getConfig()
    daydiff = 180
    fromdt = datetime.strptime(yyyymmdd, "%Y-%m-%d") - timedelta(days=daydiff)
    obj = YFPrice()
    obj.setting('KRW=X')
    retVal = obj.get_data(fromdt.strftime("%Y-%m-%d"), yyyymmdd, 'daily', 'close')
    obj.close()
    retVal2 = getNaverPrice('INDEX', 'KPI200', 21)
    # print(retVal2)
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    ax1.plot(retVal, 'r-')
    ax2.plot(retVal2, 'b-')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('USD/KRW', color='r')
    ax2.set_ylabel('KOSPI200', color='b')
    plt.show()


def make_USDKRW_graph():
    import matplotlib.pyplot as plt
    from detective.naver_api import getNaverPrice
    getConfig()
    daydiff = 180
    fromdt = datetime.strptime(yyyymmdd, "%Y-%m-%d") - timedelta(days=daydiff)
    obj = YFPrice()
    obj.setting('KRW=X')
    retVal = obj.get_data(fromdt.strftime("%Y-%m-%d"), yyyymmdd, 'daily', 'close')
    obj.close()
    retVal2 = getNaverPrice('INDEX', 'KPI200', 21)
    # print(retVal2)
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    ax1.plot(retVal, 'r-')
    ax2.plot(retVal2, 'b-')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('USD/KRW', color='r')
    ax2.set_ylabel('KOSPI200', color='b')
    plt.xticks(rotation=45)
    # plt.show()
    img_path = r'{}\{}\{}'.format(path, 'EX_RATE', yyyymmdd)
    print(img_path)
    if not os.path.exists(img_path):
        os.makedirs(img_path)
    plt.savefig(img_path + '\\result.png')
    msgr.img_messeage_to_telegram(img_path + '\\result.png')
    fig = None
    ax1 = None
    ax2 = None
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
