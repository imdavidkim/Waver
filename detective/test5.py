# import mechanize
# br = mechanize.Browser()
# response = br.open("http://comp.fnguide.com/SVO2/ASP/SVD_Consensus.asp?pGB=1&gicode=A005930&cID=&MenuYn=Y&ReportGB=&NewMenuID=108&stkGb=701")
# print(response)
import requests
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import numpy as np
import string


# alphabet = string.ascii_uppercase
# print(alphabet)
# 참고사이트
# https://m.blog.naver.com/21ahn/221329219163

if __name__ == '__main__':
    # import detective.fnguide_collector as fnguide
    # import detective.crawler as crwlr
    import requests
    # url = 'https://api.nasdaq.com/api/company/AAPL/company-profile'
    # header = {
    #     "Accept": "application/json, text/plain, */*",
    #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36 Edg/84.0.522.49",
    #     "Origin": "https://www.nasdaq.com",
    #     "Sec-Fetch-Site": "same-site",
    #     "Sec-Fetch-Mode": "cors",
    #     "Sec-Fetch-Dest": "empty",
    #     "Accept-Encoding": "gzip, deflate, br",
    #     "Accept-Language": "ko,en;q=0.9,en-US;q=0.8",
    # }
    url = 'http://compglobal.wisereport.co.kr/miraeassetdaewoo/Company/Snap?cmp_cd=AAPL-US&en=57390072434531'
    header = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36 Edg/84.0.522.49",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "ko,en;q=0.9,en-US;q=0.8",
    }
    res = requests.get(url=url, headers=header)
    # print(res.content)
    soup = BeautifulSoup(res.content.decode('utf-8'), 'lxml')
    print(soup.text)
    print(res.cookies)
    # a = httpRequest(url=url, header=header, method='GET')

    """
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36 Edg/84.0.522.49",
    "Origin": "https://www.nasdaq.com",
    "Sec-Fetch-Site": "same-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "ko,en;q=0.9,en-US;q=0.8",

    """
    # url = 'http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp'
    # data = {
    #         'pGB': 1,
    #         'gicode': 'A007630',
    #         'cID': '',
    #         'MenuYn': 'Y',
    #         'ReportGB': 'D',  # D: 연결, B: 별도
    #         'NewMenuID': 101,
    #         'stkGb': 701,
    #     }
    #
    # CHROMEDRIVER_PATH = r'D:\Waver\chromedriver_win32\chromedriver.exe'
    # options = Options()
    # options.headless = True
    # driver = webdriver.Chrome(CHROMEDRIVER_PATH, chrome_options=options)
    # # driver.implicitly_wait(3)
    # req = request(driver)
    # d = json.dumps(data)
    # # driver.get('http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A003490&cID=&MenuYn=Y&ReportGB=D&NewMenuID=101&stkGb=701')
    # # print(driver.page_source)
    # res = req.post(url, data)
    # print(res.text)
    # stocks = {}
    # tt = requests.get('https://www.nasdaq.com/market-activity/stocks/aacqu')
    #
    # # tt = requests.get('https://www.nasdaq.com/nasdaq_symbol/168136')
    # # print(tt.content)
    # soup = BeautifulSoup(tt.content.decode('utf-8'), 'lxml')
    # print(soup)

    # usstocks = fnguide.select_by_attr(soup, 'div', 'id', 'ctl00_cph1_divSymbols')  # Snapshot FinancialHighlight
    # dd = usstocks.find_all('tr')
    # for idx, d in enumerate(dd):
    #     if idx == 0:
    #         # hh = d.find_all('th')
    #         # print(idx, len(hh), hh)
    #         # for h in hh:
    #         #     print(h.text)
    #         pass
    #     else:
    #         ss = d.find_all('td')
    #         # [code, name, high, low, close, volume, change, direction, pct, down]
    #         stocks[ss[0].text] = {'ticker': ss[0].text, 'security': ss[1].text}
    #
    # print(stocks)
    #
    # import telegram
    # # my_token = '577949495:AAFk3JWQjHlbJr2_AtZeonjqQS7buu8cYG4'
    # # my_token = '781845768:AAEG55_jbdDIDlmGXWHl8Ag2aDUg-YAA8fc'
    # my_token = '866257502:AAH3zxEzlNT-venJnI-ZacJBwrnh2nxLsNk'
    # telegram.Bot(token=my_token)
    # bot = telegram.Bot(token=my_token)
    #
    # updates = bot.getUpdates()
    # for u in updates:
    #     print(u.message)


#
# select a.security, a.ticker, b.security, b.ticker from detective_app_usstocks a , detective_app_usnasdaqstocks b where a.listing = 'Y' and b.listing = 'Y' and a.ticker = b.ticker
