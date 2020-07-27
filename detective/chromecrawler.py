# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
import time

class ChromeDriver:
    chrome_path = ""
    options = Options()
    driver = None
    wait = None

    def set_path(self):
        self.chrome_path = r"C:\Users\imkhk\Waver\chromedriver_win32\chromedriver.exe"

    def set_option(self):
        self.options.headless = True

    def set_user_agent(self):
        self.options.add_argument("User-Agent=Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.2; WOW64; Trident/7.0; .NET4.0C; .NET4.0E; .NET CLR 2.0.50727; .NET CLR 3.0.30729; .NET CLR 3.5.30729; iftNxParam=1.0.1)")

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
        drv = ChromeDriver()
        drv.set_path()
        drv.options.add_argument("User-Agent=Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.2; WOW64; Trident/7.0; .NET4.0C; .NET4.0E; .NET CLR 2.0.50727; .NET CLR 3.0.30729; .NET CLR 3.5.30729; iftNxParam=1.0.1)")
        drv.set_option()
        drv.set_driver()
        drv.set_waiting()
        # drv.implicitly_wait(15)
        drv.set_url("http://compglobal.wisereport.co.kr/miraeassetdaewoo/Company/Snap?cmp_cd=MSFT-US&en=08854076681227")
        ck = drv.driver.get_cookies()
        drv.driver.delete_all_cookies()
        for k in ck:
            print(k)
            drv.driver.add_cookie(k)
        # drv.driver.add_cookie(ck)

        drv.set_url("http://compglobal.wisereport.co.kr/miraeassetdaewoo/Company/Snap?cmp_cd=AMZN-US&en=08854076681227")
        ck = drv.driver.get_cookies()

        drv.set_url("http://compglobal.wisereport.co.kr/miraeassetdaewoo/Company/Snap?cmp_cd=PTON-US&en=08854076681227")
        ck = drv.driver.get_cookies()

        drv.set_url("http://compglobal.wisereport.co.kr/miraeassetdaewoo/Company/Snap?cmp_cd=ADP-US&en=08854076681227")

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
