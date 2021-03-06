# -*- coding: utf-8 -*-

from detective.fnguide_collector import getFinanceData
from detective.crawler import getStockInfoNew

from detective.detector import new_find_hidden_pearl
from detective.detector import get_high_ranked_stock
from detective.detector import get_high_ranked_stock_with_closeprice

from detective.messenger import messeage_to_telegram
from detective.kofiabond import get_list_day
from detective.fred import make_graph as fred_make_graph
from detective.kofia import make_graph as kofia_make_graph
from detective.yahoo_price_info import make_USDKRW_graph as usdkrw_make_graph
from detective.oecd_api import make_CLI_graph as cli_make_graph
from detective.yahoo_price_info import make_ISMIndex_graph as ism_make_graph
from detective.yahoo_price_info import make_SvcPMIIndex_graph as svc_pmi_make_graph
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
    getStockInfoNew()
    # get_list_day(None)
    cli_make_graph()
    ism_make_graph()
    svc_pmi_make_graph()
    usdkrw_make_graph()
    kofia_make_graph()
    fred_make_graph()

    # run_info = [101, 200]
    # agents = 2
    #
    # with NonDaemonicPool(processes=agents) as pool:
    #     result = pool.map(getFinanceData, run_info)
    # new_find_hidden_pearl()
    # messeage_to_telegram(get_high_ranked_stock())
    # get_high_ranked_stock_with_closeprice()


