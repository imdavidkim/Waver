import datetime
import pandas as pd
from urllib.request import urlopen
from bs4 import BeautifulSoup


def getNaverPrice(url_type, code, r_page=1):
    base_url = None
    if url_type.upper() == 'INDEX':
        base_url = "https://finance.naver.com/sise/sise_index_day.nhn?code={}".format(code)
    elif url_type.upper() == 'STOCK':
        base_url = "http://finance.naver.com/item/sise_day.nhn?code={}".format(code)

    html = urlopen(base_url)
    source = BeautifulSoup(html.read(), "html.parser")

    if url_type.upper() == 'STOCK':
        maxPage = source.find_all("table", align="center")
        mp = maxPage[0].find_all("td", class_="pgRR")
        mpidx = 0
        if mp == []:
            mp = maxPage[0].find_all("td", class_="pgR")
            if len(mp) != 0: mpidx = 1
            if mp == []:
                mp = maxPage[0].find_all("td")
                if len(mp) != 0: mpidx = 2
        if mpidx == 2:
            mpNum = int(mp[0].a.get('href').split('=')[2])
        else:
            mpNum = int(mp[-1].a.get('href').split('=')[2])

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
            url = base_url + '&page=' + str(page)
            html = urlopen(url)
            source = BeautifulSoup(html.read(), "html.parser")
            srlists = source.find_all("tr")
            # print(len(srlists), srlists)
            # for s in srlists:
            #     if s.span is None: print('*' * 100, "\n", s)
            #     else: print('-' * 100, "\n", s.span)
            # if ((page % 1) == 0):
            #     time.sleep(1.50)

            for i in range(1, len(srlists) - 1):
                if srlists[i].span is not None:
                    # srlists[i].td.text
                    # print(datetime.datetime.strptime(srlists[i].find_all("td", align="center")[0].text.replace('.', '-'), "%Y-%m-%d"))
                    retArray.append([datetime.datetime.strptime(srlists[i].find_all("td", align="center")[0].text.replace('.', '-'), "%Y-%m-%d"), int(srlists[i].find_all("td", class_="num")[0].text.replace(',', ''))])
        retArray.sort(key=lambda x: x[0])
        for i in retArray:
            if abs((retArray[-1][0]-i[0]).days) > 365:
                continue
            retArrayDate.append(i[0])
            retArrayData.append(i[1])
        retVal = pd.core.series.Series(retArrayData, retArrayDate)
        return retVal
    elif url_type.upper() == 'INDEX':
        maxPage = source.find_all("table", align="center")
        mp = maxPage[0].find_all("td", class_="pgRR")
        mpidx = 0
        if mp == []:
            mp = maxPage[0].find_all("td", class_="pgR")
            if len(mp) != 0: mpidx = 1
            if mp == []:
                mp = maxPage[0].find_all("td")
                if len(mp) != 0: mpidx = 2
        if mpidx == 2:
            mpNum = int(mp[0].a.get('href').split('=')[2])
        else:
            mpNum = int(mp[-1].a.get('href').split('=')[2])

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
            url = base_url + '&page=' + str(page)
            html = urlopen(url)
            source = BeautifulSoup(html.read(), "html.parser")
            datelists = source.find_all("td", class_='date')
            tmplists = source.find_all("td", class_='number_1')
            pricelists = [t for t in tmplists if t.span is None and not t.has_attr('style')]
            # print(pricelists)
            for i in range(0, len(pricelists)):
                retArray.append([datetime.datetime.strptime(
                    datelists[i].text.replace('.', '-'), "%Y-%m-%d"),
                                 float(pricelists[i].text.replace(',', ''))])
        retArray.sort(key=lambda x: x[0])
        for i in retArray:
            if abs((retArray[-1][0] - i[0]).days) > 365:
                continue
            retArrayDate.append(i[0])
            retArrayData.append(i[1])
        retVal = pd.core.series.Series(retArrayData, retArrayDate)
        return retVal
if __name__ == '__main__':
    stockItem = '013890'
    page = 1
    stockItem = '005930'
    # print(getNaverPrice('stock', stockItem, page))
    getNaverPrice('INDEX', 'KPI200', 21)
    # for index, value in getNaverPrice(stockItem, page).items():
    #     print(index, value)

