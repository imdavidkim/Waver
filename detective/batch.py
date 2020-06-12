# -*- coding: utf-8 -*-

from multiprocessing import Pool
from detective.fnguide_collector import getFinanceData
from detective.crawler import getStockInfo
from detective.crawler import getSnP500StockInfo
from detective.detector import new_find_hidden_pearl
from detective.detector import get_high_ranked_stock
from detective.detector import get_high_ranked_stock_with_closeprice
from detective.messenger import messeage_to_telegram
from detective.kofiabond import get_list_day
from detective.fred import make_graph as fred_make_graph
from detective.kofia import make_graph as kofia_make_graph

if __name__ == '__main__':
    getStockInfo()
    getSnP500StockInfo()
    get_list_day(None)
    # get_list_day('20200413')
    kofia_make_graph()
    fred_make_graph()

    run_info = [101, 200]
    agents = 2
    with Pool(processes=agents) as pool:
        result = pool.map(getFinanceData, run_info)
    new_find_hidden_pearl()
    messeage_to_telegram(get_high_ranked_stock())
    get_high_ranked_stock_with_closeprice()

