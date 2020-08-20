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
        prices = self.yf_obj.get_historical_price_data(fromdt, todt, period)
        for key in prices.keys():
            # print(key, prices[key])
            if isinstance(prices[key], dict):
                for inner_key in prices[key].keys():
                    # print(inner_key, prices[key][inner_key])
                    if inner_key == 'prices':
                        for d in prices[key][inner_key]:
                            self.data[pd.to_datetime(d['formatted_date'], format='%Y-%m-%d').to_pydatetime()] = d[srch_term]
        return pd.Series(self.data)


def make_USDKRW_graph():
    import matplotlib.pyplot as plt
    getConfig()
    obj = YFPrice()
    obj.setting('KRW=X')
    daydiff = 180
    fromdt = datetime.strptime(yyyymmdd, "%Y-%m-%d") - timedelta(days=daydiff)
    retVal = obj.get_data(fromdt.strftime("%Y-%m-%d"), yyyymmdd, 'daily', 'close')
    fig = plt.figure()
    usdkrw = fig.add_subplot(1, 1, 1)
    usdkrw.plot(retVal, label="USD/KRW")
    usdkrw.legend(loc='upper center')
    # plt.show()
    img_path = r'{}\{}\{}'.format(path, 'EX_RATE', yyyymmdd)
    print(img_path)
    if not os.path.exists(img_path):
        os.makedirs(img_path)
    plt.savefig(img_path + '\\result.png')
    msgr.img_messeage_to_telegram(img_path + '\\result.png')
    plt = None

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
