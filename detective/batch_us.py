# -*- coding: utf-8 -*-

# from multiprocessing import Pool
from detective.fnguide_collector import getFinanceData
from detective.crawler import getStockInfo
from detective.crawler import getSnP500StockInfo
# from detective.crawler import getNasdaq100StockInfo
from detective.crawler import getNasdaqStockInfo
from detective.detector import new_find_hidden_pearl
from detective.detector import get_high_ranked_stock
from detective.detector import get_high_ranked_stock_with_closeprice
from detective.detector import hidden_pearl_in_usmarket
from detective.detector import get_nasdaq_high_ranked_stock
from detective.detector import get_nasdaq_high_ranked_stock_with_closeprice
from detective.messenger import messeage_to_telegram
from detective.kofiabond import get_list_day
from detective.fred import make_graph as fred_make_graph
from detective.kofia import make_graph as kofia_make_graph
# import multiprocessing
import multiprocessing.pool

# from multiprocessing import Pool


class NoDaemonProcess(multiprocessing.Process):
    # make 'daemon' attribute always return False
    def _get_daemon(self):
        return False

    def _set_daemon(self, value):
        pass
    daemon = property(_get_daemon, _set_daemon)


class NonDaemonicPool(multiprocessing.pool.Pool):
    Process = NoDaemonProcess


if __name__ == '__main__':
    getSnP500StockInfo()
    getNasdaqStockInfo()

    run_info = [300, 301]
    agents = 2

    with NonDaemonicPool(processes=agents) as pool:
        result = pool.map(getFinanceData, run_info)

    hidden_pearl_in_usmarket()
    messeage_to_telegram(get_nasdaq_high_ranked_stock())
    get_nasdaq_high_ranked_stock_with_closeprice()
