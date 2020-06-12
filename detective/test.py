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


def request(driver):
    s = requests.Session()
    # cookies = driver.get_cookies()
    # for cookie in cookies:
    #     s.cookies.set(cookie['name'], cookie['value'])
    return s

if __name__ == '__main__':

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
    CHROMEDRIVER_PATH = r'D:\Waver\chromedriver_win32\chromedriver.exe'
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(CHROMEDRIVER_PATH, chrome_options=options)
    # driver.implicitly_wait(3)
    req = request(driver)
    # d = json.dumps(data)
    # # driver.get('http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A003490&cID=&MenuYn=Y&ReportGB=D&NewMenuID=101&stkGb=701')
    # # print(driver.page_source)
    # # res = req.post(url, data)
    for i in range(10):
        en = ''
        n = 5
        en += ''.join(["{}".format(np.random.randint(0, 9)) for num in range(0, n)])
        en += '06'
        en += ''.join(["{}".format(np.random.randint(0, 9)) for num in range(0, n)])
        en += '11'
        url = 'http://compglobal.wisereport.co.kr/miraeassetdaewoo/company/get_snap_financial_summary?ticker=MSFT-US&freq_typ=A&en={}'.format(en)
        print(url)
        res = req.get(url)
        print(res.text)
    # # soup = BeautifulSoup(driver.page_source, 'lxml')
    # # print(soup)




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
