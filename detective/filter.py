# -*- coding: utf-8 -*-

# import pandas as pd
# import numpy as np
# import requests
# from io import BytesIO
# from datetime import datetime, timedelta
# from bs4 import BeautifulSoup
# import pprint
# import csv
# import xmltodict
# import os


def sales_check(crp_cd, market, disc_categorizing):
    import sys
    import os
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    rpt_nm = 'FinancialHighlight'
    rpt_tp = 'IFRS(연결)'
    accnt_nm = '매출액'
    fix_or_prov_or_estm = 'E'
    retGrade = 'F'
    try:
        if disc_categorizing == 'YEARLY':
            result = detective_db.FnGuideSnapShot.objects.filter(rpt_nm=rpt_nm,
                                                                 rpt_tp=rpt_tp,
                                                                 accnt_nm=accnt_nm,
                                                                 disc_categorizing=disc_categorizing,
                                                                 fix_or_prov_or_estm=fix_or_prov_or_estm,
                                                                 crp_cd=crp_cd
                                                                 ).order_by('disc_year', 'disc_month')[:1].values()
        else:
            result = detective_db.FnGuideSnapShot.objects.filter(rpt_nm=rpt_nm,
                                                                 rpt_tp=rpt_tp,
                                                                 accnt_nm=accnt_nm,
                                                                 disc_categorizing=disc_categorizing,
                                                                 crp_cd=crp_cd
                                                                 ).order_by('-disc_year', '-disc_month')[:4].values()
            # result2 = detective_db.FnGuideSnapShot.objects.filter(rpt_nm=rpt_nm,
            #                                                       rpt_tp=rpt_tp,
            #                                                       accnt_nm=accnt_nm,
            #                                                       disc_categorizing=disc_categorizing,
            #                                                       crp_cd=crp_cd
            #                                                       ).order_by('-disc_year', '-disc_month')[4:].values()
        if market == 'KOSPI':  # 50억 미만
            # print('KOSPI', result)
            if disc_categorizing == 'YEARLY':
                if result[0]['value'] < 50:
                    retGrade = 'D'
                else:
                    if 100 > result[0]['value'] >= 50:
                        retGrade = 'C'
                    else:
                        retGrade = 'A'
            else:
                # print('KOSPI', result2)
                value = 0
                for r in result[0]:
                    value += r['value']
                if value < 50:
                    retGrade = 'D'
                else:
                    if 100 > value >= 50:
                        retGrade = 'C'
                    else:
                        retGrade = 'A'
        elif market == 'KOSDAQ':  # 30억 미만
            # print('KOSDAQ', result)
            if disc_categorizing == 'YEARLY':
                if result['value'] < 30:
                    retGrade = 'D'
                else:
                    if 40 > result['value'] >= 30:
                        retGrade = 'C'
                    else:
                        retGrade = 'A'
            else:
                value = 0
                for r in result:
                    value += r['value']
                if value < 30:
                    retGrade = 'D'
                else:
                    if 40 > value >= 30:
                        retGrade = 'C'
                    else:
                        retGrade = 'A'
    except Exception as e:
        print(e)
    return retGrade


def operation_profit_check(crp_cd, market):
    import sys
    import os
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MainBoard.settings")
    django.setup()
    import detective_app.models as detective_db
    rpt_nm = 'FinancialHighlight'
    rpt_tp = 'IFRS(연결)'
    accnt_nm = '영업이익'
    fix_or_prov_or_estm = 'F'
    retGrade = 'F'
    point = 0
    try:
        if market:
            result = detective_db.FnGuideSnapShot.objects.filter(rpt_nm=rpt_nm,
                                                                 rpt_tp=rpt_tp,
                                                                 accnt_nm=accnt_nm,
                                                                 crp_cd=crp_cd
                                                                 ).order_by('-disc_year', '-disc_month')[:4].values()
        for r in result[0]:
            if r['value'] > 0:
                pass
    except Exception as e:
        print(e)
    return retGrade

def kospi_risky_stock_filter():
    '''
    # 관리종목 편입조건
    # 1. 매출액 50억 미만
    # 2. 법인세비용차감전계속사업손실 해당없음
    # 3. 장기간 영업손실 해당없음
    # 4. 자본금 50% 이상 잠식
    :return:
    '''


def kospi_unlisting_filter():
    '''
    # 상장폐지 조건
    # 1. 매출액 50억 미만 2년 연속
    # 2. 법인세비용차감전계속사업손실 해당없음
    # 3. 장기간 영업손실 해당없음
    # 4. 자본금 전액잠식 또는 자본금 2년 연속 50% 이상 잠식
    :return:
    '''


def kosdaq_risky_stock_filter():
    '''
    # 관리종목 편입조건
    # 1. 매출액 30억 미만
    # 2. 자기자본의 50%를 초과(하면서 10억 이상)하는 법인세비용차감전계속사업손실이 최근 3년간 2회 이상
    # 3. 최근 4개년 사업연도 영업손실
    # 4. A) 사업연도(반기)말 자본잠식률 50% 이상
         B) 사업연도(반기)말 자기자본 10억원 미만
         C) 반기보고서 제출기한 경과 후 10일내 반기검토(감사)보고서 미제출 or 검토(감사)의견 부적정-의견거절-범위제한한정
    :return:
    '''


def kosdaq_unlisting_filter():
    '''
    # 상장폐지 조건
    # 1. 매출액 30억 미만 2년 연속
    # 2. 관리종목 지정후 자기자본의 50%를 초과(하면서 10억 이상)하는 법인세비용차감전계속사업손실 발생시
    # 3. 5년 연속 영업손실
    # 4. 최근년말 자본금 전액잠식 또는
         관리A or 관리C 후 사업연도(반기)말 자본잠식률 50% 이상
         관리B or 관리C 후 사업연도(반기)말 자본잠식률 50% 이상
         관리A or 관리B or 관리C 후 반기말 반기보고서 기한 경과후 10일내 미제출 or 검토(감사)의견 부적정-의견거절-범위제한한정
    :return:
    '''


if __name__ == '__main__':
    mkt = 'KOSPI'
    # condition = 'QUARTERLY'
    condition = 'YEARLY'
    for a in sales_check('005930', mkt, condition):
        print(a)