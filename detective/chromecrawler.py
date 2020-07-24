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
    ua = [
        'user-agent=Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko'
        ,
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'
        ,
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36 Edg/84.0.522.40'
    ]
    def set_path(self):
        self.chrome_path = "D:\Waver\chromedriver_win32\chromedriver.exe"

    def set_option(self):
        self.options.headless = True

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
        drv.options.add_argument(drv.ua[(int(0 / 5) % len(drv.ua))])
        drv.set_option()
        drv.set_driver()
        drv.set_waiting()
        # drv.implicitly_wait(15)
        drv.set_url("http://compglobal.wisereport.co.kr/miraeassetdaewoo/Company/Snap?cmp_cd=AMZN-US&en=57304072434524")
        # time.sleep(5)
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
