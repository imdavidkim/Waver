# -*- coding: utf-8 -*-

from multiprocessing import Pool
from detective.fnguide_collector import getFinanceData
from detective.crawler import getStockInfo
from detective.detector import new_find_hidden_pearl
from detective.detector import get_high_ranked_stock
from detective.detector import messeage_to_telegram
from detective.kofiabond import get_list_day

if __name__ == '__main__':
    get_list_day()
    getStockInfo()
    run_info = [101, 200]
    agents = 2
    # chunksize = 3
    with Pool(processes=agents) as pool:
        result = pool.map(getFinanceData, run_info)
    new_find_hidden_pearl()
    messeage_to_telegram(get_high_ranked_stock())
