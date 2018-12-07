# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import requests
from io import BytesIO
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import csv
import xmltodict
import json

down_header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36'
        , 'Accept-Encoding': 'gzip, deflate'
        , 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
        , 'Content-Type': 'application/x-www-form-urlencoded'}

class ecosData:
    dicArray = {}

    class dicToCls(object):
        def __init__(self, dic):
            for key in dic:
                setattr(self, key, dic[key])

    def SetData(self, service_name, dic):
        if service_name in self.dicArray.keys():
            self.dicArray[service_name].append(self.ECosDataParser(dic))
        else:
            self.dicArray[service_name] = []
            self.dicArray[service_name].append(self.ECosDataParser(dic))


    def ECosDataParser(self, dic):
        return self.dicToCls(dic)

    def EcosService1(self, dic):
        cls = self.ecosService1
        cls.CLASS_NAME = dic['CLASS_NAME']  # 통계그룹명
        cls.KEYSTAT_NAME = dic['KEYSTAT_NAME']  # 통계명
        cls.DATA_VALUE = dic['DATA_VALUE']  # 값
        cls.CYCLE = dic['CYCLE']  # 주기
        cls.UNIT_NAME = dic['UNIT_NAME']  # 단위
        return cls

    class ecosService1:         # 100대 통계지표
        CLASS_NAME = None       # 통계그룹명
        KEYSTAT_NAME = None     # 통계명
        DATA_VALUE = None       # 값
        CYCLE = None            # 주기
        UNIT_NAME = None        # 단위

    def EcosService2(self, dic):         # 서비스 통계 목록
        cls = self.ecosService2
        cls.P_STAT_CODE = dic['P_STAT_CODE']      # 부모통계코드
        cls.STAT_CODE = dic['STAT_CODE']        # 통계코드
        cls.STAT_NAME = dic['STAT_NAME']        # 통계명
        cls.CYCLE = dic['CYCLE']            # 주기
        cls.SRCH_YN = dic['SRCH_YN']          # 검색가능여부
        cls.ORG_NAME = dic['ORG_NAME']         # 출처
        return cls

    class ecosService2:         # 서비스 통계 목록
        P_STAT_CODE = None      # 부모통계코드
        STAT_CODE = None        # 통계코드
        STAT_NAME = None        # 통계명
        CYCLE = None            # 주기
        SRCH_YN = None          # 검색가능여부
        ORG_NAME = None         # 출처

    def EcosService3(self, dic):         # 통계 세부항목 목록
        cls = self.ecosService3
        cls.STAT_CODE = dic['STAT_CODE']        # 통계코드
        cls.STAT_NAME = dic['STAT_NAME']        # 통계명
        cls.GRP_NAME = dic['GRP_NAME']         # 항목그룹
        cls.ITEM_CODE = dic['ITEM_CODE']        # 항목코드
        cls.ITEM_NAME = dic['ITEM_NAME']        # 항목명
        cls.CYCLE = dic['CYCLE']            # 주기
        cls.START_TIME = dic['START_TIME']       # 수록시작일자
        cls.END_TIME = dic['END_TIME']         # 수록종료일자
        cls.DATA_CNT = dic['DATA_CNT']         # 자료수
        return cls

    class ecosService3:         # 통계 세부항목 목록
        STAT_CODE = None        # 통계코드
        STAT_NAME = None        # 통계명
        GRP_NAME = None         # 항목그룹
        ITEM_CODE = None        # 항목코드
        ITEM_NAME = None        # 항목명
        CYCLE = None            # 주기
        START_TIME = None       # 수록시작일자
        END_TIME = None         # 수록종료일자
        DATA_CNT = None         # 자료수

    def EcosService4(self, dic):         # 통계 조회 조건 설정
        cls = self.ecosService4
        cls.STAT_CODE = dic['STAT_CODE']        # 통계코드
        cls.STAT_NAME = dic['STAT_NAME']        # 통계명
        cls.ITEM_CODE1 = dic['ITEM_CODE1']       # 항목코드1
        cls.ITEM_NAME1 = dic['ITEM_NAME1']       # 항목명1
        cls.ITEM_CODE2 = dic['ITEM_CODE2']       # 항목코드2
        cls.ITEM_NAME2 = dic['ITEM_NAME2']       # 항목명2
        cls.ITEM_CODE3 = dic['ITEM_CODE3']       # 항목코드3
        cls.ITEM_NAME3 = dic['ITEM_NAME3']       # 항목명3
        cls.UNIT_NAME = dic['UNIT_NAME']        # 단위
        cls.TIME = dic['TIME']             # 시점
        cls.DATA_VALUE = dic['DATA_VALUE']       # 값
        return cls

    class ecosService4:         # 통계 조회 조건 설정
        STAT_CODE = None        # 통계코드
        STAT_NAME = None        # 통계명
        ITEM_CODE1 = None       # 항목코드1
        ITEM_NAME1 = None       # 항목명1
        ITEM_CODE2 = None       # 항목코드2
        ITEM_NAME2 = None       # 항목명2
        ITEM_CODE3 = None       # 항목코드3
        ITEM_NAME3 = None       # 항목명3
        UNIT_NAME = None        # 단위
        TIME = None             # 시점
        DATA_VALUE = None       # 값

    def EcosService5(self, dic):         # 통계메타DB
        cls = self.ecosService5
        cls.LVL = dic['LVL']              # 레벨
        cls.P_CONT_CODE = dic['P_CONT_CODE']      # 부모항목코드
        cls.CONT_CODE = dic['CONT_CODE']        # 항목코드
        cls.CONT_NAME = dic['CONT_NAME']        # 항목명
        cls.META_DATA = dic['META_DATA']        # 메타데이터
        return cls

    class ecosService5:  # 통계메타DB
        LVL = None  # 레벨
        P_CONT_CODE = None  # 부모항목코드
        CONT_CODE = None  # 항목코드
        CONT_NAME = None  # 항목명
        META_DATA = None  # 메타데이터

    def EcosService6(self, dic):         # 통계용어사전
        cls = self.ecosService6
        cls.WORD = dic['WORD']             # 용어
        cls.CONTENT = dic['CONTENT']          # 용어설명
        return cls

    class ecosService6:         # 통계용어사전
        WORD = None             # 용어
        CONTENT = None          # 용어설명


def getConfig():
    import configparser
    global auth_key, auth_key_valid_until, api_url, api_service1, api_service2, api_service3, api_service4, api_service5, api_service6
    config = configparser.ConfigParser()
    config.read('config.ini')
    auth_key = config['ECOS']['AUTH-KEY']
    auth_key_valid_until = config['ECOS']['AUTH-KEY-VALID-UNTIL']
    api_url = config['ECOS']['API_URL']
    api_service1 = config['ECOS']['API_SERVICE1']
    api_service2 = config['ECOS']['API_SERVICE2']
    api_service3 = config['ECOS']['API_SERVICE3']
    api_service4 = config['ECOS']['API_SERVICE4']
    api_service5 = config['ECOS']['API_SERVICE5']
    api_service6 = config['ECOS']['API_SERVICE6']

def getKeyStatisticListData():  # 100대 통계지표
    global down_header
    getConfig()
    api_url_full = makeApiUrl(api_url, api_service1, auth_key)
    print(api_url_full)
    json_str = httpRequest(api_url_full, None, down_header, 'GET').decode('utf-8')
    json_obj = json.loads(json_str)

    tmp = ecosData()
    if api_service1 in json_obj.keys():
        for dic in json_obj[api_service1]['row']:
            tmp.SetData(api_service1, dic)
            print(dic)
        # for cls in tmp.dicArray[api_service1]:
        #     print(cls.CLASS_NAME, cls.KEYSTAT_NAME, cls.DATA_VALUE, cls.CYCLE, cls.DATA_VALUE, '\n')

def getStatisticTableListData():  # 서비스 통계 목록
    global down_header
    getConfig()

    try:
        api_url_full = makeApiUrl(api_url, api_service2, auth_key)
        print(api_url_full)
        json_str = httpRequest(api_url_full, None, down_header, 'GET').decode('utf-8')
        json_obj = json.loads(json_str)

        tmp = ecosData()
        if api_service2 in json_obj.keys():
            for dic in json_obj[api_service2]['row']:
                tmp.SetData(api_service2, dic)
                print(dic)
            for cls in tmp.dicArray[api_service2]:
                EcosServiceListDataStore(cls.P_STAT_CODE
                                         , cls.STAT_CODE
                                         , cls.STAT_NAME
                                         , cls.CYCLE
                                         , cls.SRCH_YN
                                         , cls.ORG_NAME)
        else:
            pass
    except Exception as e:
        print(e)

def getStatisticItemListData():  # 통계 세부항목 목록
    global down_header
    getConfig()
    sl = EcosServiceListDataSelect()
    # print(sl)
    try:
        if sl is not None:
            for l in sl:
                # print(dir(l))
                api_url_full = makeApiUrl(api_url, api_service3, auth_key, l.STAT_CODE)
                print(api_url_full)
                json_str = httpRequest(api_url_full, None, down_header, 'GET').decode('utf-8')
                json_obj = json.loads(json_str)

                tmp = ecosData()
                if api_service3 in json_obj.keys():
                    for dic in json_obj[api_service3]['row']:
                        tmp.SetData(api_service3, dic)
                        print(dic)
                    for cls in tmp.dicArray[api_service3]:
                        EcosStatDetailItemListDataStore(cls.STAT_CODE
                                                        , cls.STAT_NAME
                                                        , cls.GRP_NAME
                                                        , cls.ITEM_CODE
                                                        , cls.ITEM_NAME
                                                        , cls.CYCLE
                                                        , cls.START_TIME
                                                        , cls.END_TIME
                                                        , cls.DATA_CNT)
                else:
                    continue
    except Exception as e:
        print(e)

def getStatisticSearchData():  #  통계 조회 조건 설정
    getConfig()

def getStatisticMetaData():  # 통계메타DB
    getConfig()

def getStatisticWordData():  # 통계용어사전
    getConfig()

def makeApiUrl(url, service_name, auth_key, qry_key=None):
    if service_name in [api_service1, api_service2]:
        retStr = url
        retStr += service_name + '/'
        retStr += auth_key + '/'
        retStr += 'json/kr/1/1000/'
    else:
        retStr = url
        retStr += service_name + '/'
        retStr += auth_key + '/'
        retStr += 'json/kr/1/1000/'
        if qry_key is not None:
            retStr += qry_key + '/'
    return retStr

def httpRequest(url, data=None, header=None, method='POST'):
    try:
        if method == 'POST':
            if header is not None and data is None:
                r = requests.post(url)
            elif data is None:
                session = requests.session()
                session.headers.update(header)
                r = session.post(url)
            elif header is not None:
                session = requests.session()
                session.headers.update(header)
                r = session.post(url, data)
            else:
                r = requests.post(url, data)
            return r.content
        else:
            if data is None:
                r = requests.get(url)
            elif header is not None:
                session = requests.session()
                session.headers.update(header)
                r = session.get(url, data)
            else:
                r = requests.get(url, data)
            return r.content
    except:
        return None


def EcosServiceListDataStore(P_STAT_CODE, STAT_CODE, STAT_NAME, CYCLE, SRCH_YN, ORG_NAME):
    import sys
    import os
    import django
    sys.path.append(r'E:\Github\Waver\MainBoard')
    sys.path.append(r'E:\Github\Waver\MainBoard\MainBoard')
    # getConfig()
    # sys.path.append(django_path)
    # sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    try:
        info = detective_db.EcosServiceList.objects.update_or_create(P_STAT_CODE=P_STAT_CODE,
                                                                     STAT_CODE=STAT_CODE,
                                                                     defaults={
                                                                         'STAT_NAME': STAT_NAME,
                                                                         'CYCLE': CYCLE,
                                                                         'SRCH_YN': SRCH_YN,
                                                                         'ORG_NAME': ORG_NAME,
                                                                         }
                                                                     )

        # print("[%s][%s][%s] %s information stored successfully" % (report_name, crp_cd, crp_nm, key))
        # print("[%s][%s][%s] information stored successfully" % (report_name, crp_cd, crp_nm))
    except Exception as e:
        print('[Error on EcosServiceListDataStore]\n', '*' * 50, e)


def EcosServiceListDataSelect():
    import sys
    import os
    import django
    sys.path.append(r'E:\Github\Waver\MainBoard')
    sys.path.append(r'E:\Github\Waver\MainBoard\MainBoard')
    # getConfig()
    # sys.path.append(django_path)
    # sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    info = None
    import detective_app.models as detective_db
    try:
        # info = detective_db.EcosServiceList.objects.filter(SRCH_YN='Y')
        info = detective_db.EcosServiceList.objects.filter(SRCH_YN='Y', id__gte=547)
    except Exception as e:
        print('[Error on EcosServiceListDataSelect]\n', '*' * 50, e)
    finally:
        return info


def EcosStatDetailItemListDataStore(STAT_CODE, STAT_NAME, GRP_NAME, ITEM_CODE, ITEM_NAME, CYCLE, START_TIME, END_TIME, DATA_CNT):
    import sys
    import os
    import django
    sys.path.append(r'E:\Github\Waver\MainBoard')
    sys.path.append(r'E:\Github\Waver\MainBoard\MainBoard')
    # getConfig()
    # sys.path.append(django_path)
    # sys.path.append(main_path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    try:
        info = detective_db.EcosStatDetailItemList.objects.update_or_create(STAT_CODE=STAT_CODE,
                                                                            ITEM_CODE=ITEM_CODE,
                                                                            defaults={
                                                                                'STAT_NAME': STAT_NAME,
                                                                                'GRP_NAME': GRP_NAME,
                                                                                'ITEM_NAME': ITEM_NAME,
                                                                                'CYCLE': CYCLE,
                                                                                'START_TIME': START_TIME,
                                                                                'END_TIME': END_TIME,
                                                                                'DATA_CNT': DATA_CNT,
                                                                            }
                                                                            )

    except Exception as e:
        print('[Error on EcosStatDetailItemListDataStore]\n', '*' * 50, e)


if __name__ == '__main__':
    # getKeyStatisticListData()
    # getStatisticTableListData()
    getStatisticItemListData()
    # dictionary = {'a':'b'}
    # print(type(dictionary) == dict)
