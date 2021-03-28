# -*- coding: utf-8 -*-

from detective.fnguide_collector import getFinanceData
from detective.crawler import getSnP500StockInfo
from detective.crawler import getNasdaqStockInfo
from detective.detector import new_hidden_pearl_in_usmarket
from detective.detector import get_nasdaq_high_ranked_stock
from detective.detector import get_nasdaq_high_ranked_stock_with_closeprice
from detective.messenger import messeage_to_telegram
import multiprocessing.pool


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
    # getSnP500StockInfo()
    getNasdaqStockInfo()

    run_info = [300, 301, 302]
    agents = 3

    with NonDaemonicPool(processes=agents) as pool:
        result = pool.map(getFinanceData, run_info)

    new_hidden_pearl_in_usmarket()
    messeage_to_telegram(get_nasdaq_high_ranked_stock())
    get_nasdaq_high_ranked_stock_with_closeprice()
