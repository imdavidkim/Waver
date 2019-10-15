# -*- coding: utf-8 -*-

from multiprocessing import Pool
from detective.fnguide_collector import getFinanceData
from detective.crawler import getStockInfo
from detective.detector import new_find_hidden_pearl
from detective.detector import get_high_ranked_stock
from detective.messenger import messeage_to_telegram
from detective.kofiabond import get_list_day
from detective.fred import make_graph as fred_make_graph
from detective.kofia import make_graph as kofia_make_graph

if __name__ == '__main__':
    # get_list_day(None)
    # # get_list_day('20191001')
    kofia_make_graph()
    fred_make_graph()
    getStockInfo()
    run_info = [101, 200]
    agents = 2
    # chunksize = 3
    with Pool(processes=agents) as pool:
        result = pool.map(getFinanceData, run_info)
    new_find_hidden_pearl()
    messeage_to_telegram(get_high_ranked_stock())
