import datetime
import pandas as pd
from urllib.request import urlopen
from bs4 import BeautifulSoup


def getNaverPrice(code, r_page=1):
    url = 'http://finance.naver.com/item/sise_day.nhn?code=' + code
    html = urlopen(url)
    source = BeautifulSoup(html.read(), "html.parser")

    maxPage = source.find_all("table", align="center")
    mp = maxPage[0].find_all("td", class_="pgRR")
    mpNum = int(mp[0].a.get('href').split('=')[2])
    if r_page == 1 and mpNum > 0:
        # print(r_page)
        mpNum = 1
    elif r_page == 0:
        # print("전체뽑기")
        pass
    elif mpNum > 0:
        # print(mpNum)
        if mpNum > r_page:
            mpNum = r_page
        else:
            pass
    else:
        print("ERROR")
        return None
    retArray = []
    retArrayDate = []
    retArrayData = []
    for page in range(1, mpNum + 1):
        # print(str(page))
        url = 'http://finance.naver.com/item/sise_day.nhn?code=' + code + '&page=' + str(page)
        html = urlopen(url)
        source = BeautifulSoup(html.read(), "html.parser")
        srlists = source.find_all("tr")

        # if ((page % 1) == 0):
        #     time.sleep(1.50)

        for i in range(1, len(srlists) - 1):
            if srlists[i].span is not None:
                # srlists[i].td.text
                # print(datetime.datetime.strptime(srlists[i].find_all("td", align="center")[0].text.replace('.', '-'), "%Y-%m-%d"))
                retArray.append([datetime.datetime.strptime(srlists[i].find_all("td", align="center")[0].text.replace('.', '-'), "%Y-%m-%d"), int(srlists[i].find_all("td", class_="num")[0].text.replace(',', ''))])
    retArray.sort(key=lambda x: x[0])
    for i in retArray:
        retArrayDate.append(i[0])
        retArrayData.append(i[1])
    retVal = pd.core.series.Series(retArrayData, retArrayDate)
    return retVal

if __name__ == '__main__':
    stockItem = '005930'
    print(getNaverPrice(stockItem, 1))

