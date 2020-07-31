# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
import time
import random
class ChromeDriver:
    chrome_path = ""
    options = Options()
    driver = None
    wait = None
    def set_path(self):
        self.chrome_path = "D:\Waver\chromedriver_win32\chromedriver.exe"

    def set_option(self):
        self.options.headless = True

    def set_user_agent(self):
        self.options.add_argument(
            "User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36 Edg/84.0.522.44")

    def set_driver(self):
        self.driver = webdriver.Chrome(self.chrome_path, chrome_options=self.options)

    def set_waiting(self):
        self.wait = WebDriverWait(self.driver, 30)

    def set_url(self, url):
        self.driver.get(url)

    def findElementById(self, elementid):
        return self.driver.find_element_by_id(elementid)

    def findElementByClassName(self, name):
        return self.driver.find_element_by_class_name(name)

    def findElementByXpath(self, path):
        return self.driver.find_element_by_xpath(path)

    def switchFrame(self, frm):
        return self.driver.switch_to.frame(frm)

    def switchOrgFrame(self):
        return self.driver.switch_to.default_content()

    def driverClose(self):
        self.driver.close()

    def driverQuit(self):
        self.driver.quit()

    def executeScriptWithoutObj(self, script):
        return self.driver.execute_script(script)

    def executeScript(self, script, obj):
        self.driver.execute_script(script, obj)

    def implicitly_wait(self, sec):
        self.driver.implicitly_wait(sec)


if __name__ == '__main__':
    try:
        import json
        from bs4 import BeautifulSoup
        drv = ChromeDriver()
        drv.set_path()
        # drv.options.add_argument("User-Agent=Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.2; WOW64; Trident/7.0; .NET4.0C; .NET4.0E; .NET CLR 2.0.50727; .NET CLR 3.0.30729; .NET CLR 3.5.30729; iftNxParam=1.0.1)")
        drv.set_option()
        drv.set_user_agent()
        drv.set_driver()
        drv.set_waiting()
        # drv.implicitly_wait(15)
        # https://api.nasdaq.com/api/quote/AACQU/info?assetclass=stocks 주식정보
        drv.set_url("https://api.nasdaq.com/api/company/IBB/company-profile")
        soup = BeautifulSoup(drv.driver.page_source, "lxml")
        response = soup.find("body").text
        json_msg = json.loads(response)
        print(type(json_msg), json_msg)
        if json_msg['data'] is not None:
            category_name = json_msg['data']['Sector']['value']
            category_detail = json_msg['data']['Industry']['value']
            tel = json_msg['data']['Phone']['value']
            address = json_msg['data']['Address']['value']
            location = json_msg['data']['Region']['value']
            description = json_msg['data']['CompanyDescription']['value']
            drv.set_url("https://api.nasdaq.com/api/quote/IBB/info?assetclass=stocks")
            soup = BeautifulSoup(drv.driver.page_source, "lxml")
            response = soup.find("body").text
            json_msg = json.loads(response)
            category_code = json_msg['data']['exchange']
            if json_msg['data']['keyStats']['MarketCap']['value'] != 'N/A':
                issued_shares = round(
                    float(str(json_msg['data']['keyStats']['MarketCap']['value']).replace(',', '')) / float(
                        str(json_msg['data']['primaryData']['lastSalePrice']).replace('$', '')), 1)
            else:
                issued_shares = 0.0


        # category_name = json_msg['data']['Sector']['value']
        # category_detail = json_msg['data']['Industry']['value']
        # tel = json_msg['data']['Phone']['value']
        # address = json_msg['data']['Address']['value']
        # location = json_msg['data']['Region']['value']
        # description = json_msg['data']['CompanyDescription']['value']

        # category_code = json_msg['data']['exchange']
        # issued_shares = float(str(json_msg['data']['keyStats']['MarketCap']['value']).replace(',', ''))/float(str(json_msg['data']['primaryData']['lastSalePrice']).replace('$', ''))

        #     security = models.TextField(primary_key=True)
        #     security_wiki_link = models.URLField(null=True)
        #     ticker = models.CharField(max_length=20, default='')
        #     ticker_symbol_link = models.URLField(null=True)
        #     category_code = models.CharField(max_length=20, null=True)
        #     category_name = models.TextField()
        #     category_detail = models.TextField()
        #     category_name_kr = models.TextField(null=True)
        #     category_detail_kr = models.TextField(null=True)
        #     settlement_month = models.TextField(null=True)
        #     sec_filing = models.URLField(null=True)
        #     issued_shares = models.FloatField(null=True)
        #     capital = models.FloatField(null=True)
        #     par_value = models.IntegerField(null=True)
        #     curr = models.CharField(max_length=3, null=True)
        #     tel = models.CharField(max_length=20, null=True)
        #     address = models.TextField(null=True)
        #     location = models.TextField(null=True)
        #     location_link = models.URLField(null=True)

        # {"data":{"symbol":"AACQU","companyName":"Artius Acquisition Inc. Unit ","stockType":"Unit consisting of one ordinary share and one third redeemable warrant","exchange":"NASDAQ-CM","isNasdaqListed":true,"isNasdaq100":false,"isHeld":false,"primaryData":{"lastSalePrice":"$10.40","netChange":"-0.03","percentageChange":"-0.29%","deltaIndicator":"down","lastTradeTimestamp":"DATA AS OF Jul 28, 2020","isRealTime":false},"secondaryData":null,"keyStats":{"Volume":{"label":"Volume","value":"537,219"},"PreviousClose":{"label":"Previous Close","value":"$10.43"},"OpenPrice":{"label":"Open","value":"$10.37"},"MarketCap":{"label":"Market Cap","value":"N/A"}},"marketStatus":"Market Closed","assetClass":"STOCKS"},"message":null,"status":{"rCode":200,"bCodeMessage":null,"developerMessage":null}}
        # drv.set_url("https://api.nasdaq.com/api/company/AAPL/company-profile")  # 전화번호 등등 회사
        # {"data":{"ModuleTitle":{"label":"Module Title","value":"Company Description"},"CompanyName":{"label":"Company Name","value":"Artius Acquisition Inc."},"Symbol":{"label":"Symbol","value":"AACQU"},"Address":{"label":"Address","value":"3 COLUMBUS CIRCLE SUITE 2215, NEW YORK, New York, 10019, United States of America"},"Phone":{"label":"Phone","value":"212-309-7668"},"Industry":{"label":"Industry","value":"Business Services"},"Sector":{"label":"Sector","value":"Finance"},"Region":{"label":"Region","value":"North America"},"CompanyDescription":{"label":"Company Description","value":"We are a newly incorporated Cayman Island exempted company structured as a blank\r\ncheck company incorporated for the purpose of effecting a merger, share\r\nexchange, asset acquisition, share purchase, reorganization or similar business\r\ncombination with one or more businesses, which we refer to throughout this\r\nprospectus as our initial business combination. We have not selected any\r\nspecific business combination target and we have not, nor has anyone on our\r\nbehalf, initiated any substantive discussions, directly or indirectly, with any\r\nbusiness combination target. While we may pursue an initial business combination\r\nin any sector, we intend to focus our efforts on technology enabled businesses\r\nthat directly or indirectly offer specific technology solutions, broader\r\ntechnology software and services, or financial services to companies of all\r\nsizes.&nbsp;&nbsp;... <a href=\"http://secfilings.nasdaq.com/edgar_conv_html%2f2020%2f07%2f02%2f0001193125-20-186768.html#FIS_BUSINESS\" target=\"_blank\">More</a> ...&nbsp;&nbsp;\r\n"},"KeyExecutives":{"label":"Key Executives","value":[]}},"message":null,"status":{"rCode":200,"bCodeMessage":null,"developerMessage":null}}
        # print(drv.driver.page_source)
        # ck = drv.driver.get_cookies()
        # drv.driver.delete_all_cookies()
        # for k in ck:
        #     print(k)
        #     drv.driver.add_cookie(k)
        # # drv.driver.add_cookie(ck)
        #
        # drv.set_url("http://compglobal.wisereport.co.kr/miraeassetdaewoo/Company/Snap?cmp_cd=AMZN-US&en=08854076681227")
        # ck = drv.driver.get_cookies()
        #
        # drv.set_url("http://compglobal.wisereport.co.kr/miraeassetdaewoo/Company/Snap?cmp_cd=PTON-US&en=08854076681227")
        # ck = drv.driver.get_cookies()
        #
        # drv.set_url("http://compglobal.wisereport.co.kr/miraeassetdaewoo/Company/Snap?cmp_cd=ADP-US&en=08854076681227")

        # time.sleep(1)
        # print(drv.driver.window_handles)
        # drv.driver.switch_to.window(drv.driver.window_handles[-1])
        # drv.driverClose()
        # # print(drv.driver.window_handles)
        # drv.set_url("http://compglobal.wisereport.co.kr/miraeassetdaewoo/Company/Snap?cmp_cd=AMZN-US&en=08854076681215")
        # time.sleep(5)
        # print(drv.driver.window_handles)
        # drv.driver.switch_to.window(drv.driver.window_handles[-1])
        drv.driverClose()
        # print(drv.driver.window_handles)
        drv.driverQuit()
    except Exception as e:
        print(e)
        drv.driverClose()
        drv.driverQuit()

