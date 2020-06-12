# import mechanize
# br = mechanize.Browser()
# response = br.open("http://comp.fnguide.com/SVO2/ASP/SVD_Consensus.asp?pGB=1&gicode=A005930&cID=&MenuYn=Y&ReportGB=&NewMenuID=108&stkGb=701")
# print(response)
import requests
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import urllib3, urllib

def httpRequestWithDriver(driver, url, data, method='POST'):
    try:
        req = request(driver)
        if method == 'POST':
            r = req.post(url, data)
            return r.content
        else:
            r = req.get(url, params=data)
            return r.content
    except Exception as e:
        print(e)




def request(driver):
    s = requests.Session()
    # cookies = driver.get_cookies()
    # for cookie in cookies:
    #     s.cookies.set(cookie['name'], cookie['value'])
    return s

if __name__ == '__main__':

    url = 'http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp'
    data = {
            'pGB': 1,
            'gicode': 'A007630',
            'cID': '',
            'MenuYn': 'Y',
            'ReportGB': 'D',  # D: 연결, B: 별도
            'NewMenuID': 101,
            'stkGb': 701,
        }

    CHROMEDRIVER_PATH = r'D:\Waver\chromedriver_win32\chromedriver.exe'
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(CHROMEDRIVER_PATH, chrome_options=options)
    driver.implicitly_wait(3)
    req = request(driver)
    # d = json.dumps(data)
    # driver.get('http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A003490&cID=&MenuYn=Y&ReportGB=D&NewMenuID=101&stkGb=701')
    # print(driver.page_source)
    # res = req.post(url, data)
    url = 'https://indexes.nasdaqomx.com/Index/Weighting/NDX'
    # url = 'https://indexes.nasdaqomx.com/Index/ExportWeightings/NDX?tradeDate=2020-06-11T00:00:00.000&timeOfDay=SOD'
    try:
        url = 'https://indexes.nasdaqomx.com/Scripts/Weighting.js'
        connection_pool = urllib3.PoolManager()
        resp = connection_pool.request('GET', url)
        with open('tmp.js', 'w+') as js:
            print(resp.data, file=js)
            res = req.get(url)
            # f = open('https://indexes.nasdaqomx.com/Scripts/Weighting.js', 'r')
            driver.execute_script(js.read())

        # driver.execute_script(script)
        driver.execute_script("javascript:UpdateTable();")
        time.sleep(2)
        print(res.text)
        js.close()
        driver.close()
    except Exception as e:
        print(e)
        driver.close()
    # soup = BeautifulSoup(driver.page_source, 'lxml')
    # print(soup)





    # import telegram
    # my_token = '577949495:AAFk3JWQjHlbJr2_AtZeonjqQS7buu8cYG4'
    # my_token = '781845768:AAEG55_jbdDIDlmGXWHl8Ag2aDUg-YAA8fc'
    # telegram.Bot(token=my_token)
    # bot = telegram.Bot(token=my_token)
    # updates = bot.getUpdates()
    # for u in updates:
    #     print(u.message)
