from django.db import models
from datetime import datetime

# Create your models here.
class Stocks(models.Model):
    class Meta:
        # unique_together = (('name', 'code', 'listing'),)
        unique_together = (('code', 'name', 'listing'),)
    code = models.CharField(max_length=20, primary_key=True)
    name = models.TextField()
    category_code = models.CharField(max_length=20)
    category_name = models.TextField()
    issued_shares = models.FloatField()
    capital = models.FloatField()
    par_value = models.IntegerField()
    curr = models.CharField(max_length=3)
    tel = models.CharField(max_length=20)
    address = models.TextField()
    market_text = models.TextField(null=True)
    market_text_detail = models.TextField(null=True)
    settlement_month = models.TextField(null=True)
    listing = models.CharField(max_length=1, default='N')
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class USStocks(models.Model):
    class Meta:
        unique_together = (('cik', 'security', 'listing'),)
    cik = models.CharField(max_length=10, primary_key=True)
    security = models.TextField()
    security_wiki_link = models.URLField(null=True)
    ticker = models.CharField(max_length=20, default='')
    ticker_symbol_link = models.URLField(null=True)
    category_code = models.CharField(max_length=20, null=True)
    category_name = models.TextField()
    category_detail = models.TextField()
    category_name_kr = models.TextField(null=True)
    category_detail_kr = models.TextField(null=True)
    settlement_month = models.TextField(null=True)
    sec_filing = models.URLField(null=True)
    issued_shares = models.FloatField(null=True)
    capital = models.FloatField(null=True)
    par_value = models.IntegerField(null=True)
    curr = models.CharField(max_length=3, null=True)
    tel = models.CharField(max_length=20, null=True)
    address = models.TextField(null=True)
    location = models.TextField(null=True)
    location_link = models.URLField(null=True)
    date_first_added = models.TextField(null=True)
    listing = models.CharField(max_length=1, default='Y')
    founded = models.TextField(null=True)
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class USNasdaqStocks(models.Model):
    class Meta:
        unique_together = (('security', 'listing'),)
    security = models.TextField(primary_key=True)
    security_wiki_link = models.URLField(null=True)
    ticker = models.CharField(max_length=20, default='')
    ticker_symbol_link = models.URLField(null=True)
    category_code = models.CharField(max_length=20, null=True)
    category_name = models.TextField()
    category_detail = models.TextField()
    category_name_kr = models.TextField(null=True)
    category_detail_kr = models.TextField(null=True)
    settlement_month = models.TextField(null=True)
    sec_filing = models.URLField(null=True)
    issued_shares = models.FloatField(null=True)
    capital = models.FloatField(null=True)
    par_value = models.IntegerField(null=True)
    curr = models.CharField(max_length=3, null=True)
    tel = models.CharField(max_length=20, null=True)
    address = models.TextField(null=True)
    location = models.TextField(null=True)
    location_link = models.URLField(null=True)
    date_first_added = models.TextField(null=True)
    listing = models.CharField(max_length=1, default='Y')
    founded = models.TextField(null=True)
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class TargetStocks(models.Model):
    class Meta:
        unique_together = (('valuation_date', 'code'),)
    id = models.AutoField(primary_key=True)
    valuation_date = models.CharField(max_length=10, default=str(datetime.now())[:10])
    # code = models.CharField(max_length=20, unique=True, primary_key=True)
    code = models.CharField(max_length=20)
    name = models.TextField()
    curr = models.CharField(max_length=3)
    last_price = models.FloatField(null=True)
    price_gap = models.TextField(null=True)
    target_price = models.FloatField(null=True)
    target_price2 = models.FloatField(null=True)
    ratio = models.FloatField(null=True)
    valuation = models.CharField(max_length=1, default='B')
    permanence = models.CharField(max_length=1, default='B')
    audit = models.CharField(max_length=1, default='B')
    required_yield = models.FloatField(null=True)
    return_on_equity = models.FloatField(null=True)
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    plus_npv = models.CharField(max_length=1, default='Y')
    liquidity_rate = models.FloatField(null=True)
    holders_share = models.FloatField(null=True)
    holders_profit = models.FloatField(null=True)
    holders_value = models.FloatField(null=True)
    impairment_profit = models.FloatField(null=True)
    issued_shares = models.FloatField(null=True)
    return_on_sales = models.FloatField(null=True)
    foreign_holding = models.FloatField(null=True)
    trade_amount = models.FloatField(null=True)


class DartRequestIndex(models.Model):
    req_id = models.BigAutoField(primary_key=True)
    err_code = models.CharField(max_length=3)
    err_msg = models.TextField()
    page_no = models.IntegerField()
    total_page = models.IntegerField()
    total_count = models.IntegerField()
    req_time = models.DateTimeField()


class DartRequestResult(models.Model):
    rcp_no = models.CharField(max_length=20, unique=True, primary_key=True)
    crp_cls = models.CharField(max_length=1)
    crp_nm = models.TextField()
    crp_cd = models.CharField(max_length=20)
    rpt_nm = models.TextField()
    flr_nm = models.TextField()
    rcp_dt = models.CharField(max_length=8)
    rmk = models.TextField(null=True)


class FnGuideDailySnapShot(models.Model):
    class Meta:
        unique_together = (('id', 'rpt_nm', 'rpt_tp', 'crp_cd', 'disc_date', 'column_nm', 'key'),)
        index_together = (
            ('rpt_nm', 'rpt_tp', 'crp_cd', 'disc_date', 'column_nm', 'key'),)
    id = models.BigAutoField(primary_key=True)
    rpt_nm = models.TextField(default='')
    rpt_tp = models.TextField(default='')
    crp_cd = models.CharField(max_length=20)
    crp_nm = models.TextField()
    disc_date = models.DateField()
    column_nm = models.CharField(max_length=100)
    key = models.TextField(max_length=100)
    value = models.FloatField(null=True)
    value_rmk = models.TextField(null=True)
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FnGuideSnapShot(models.Model):
    class Meta:
        unique_together = (('id', 'rpt_nm', 'rpt_tp', 'crp_cd', 'disc_year', 'disc_month', 'disc_quarter',
                            'disc_categorizing', 'fix_or_prov_or_estm', 'accnt_nm'),)
        index_together = (
            ('rpt_nm', 'rpt_tp', 'crp_cd', 'disc_year', 'disc_month', 'disc_quarter', 'disc_categorizing',
             'fix_or_prov_or_estm', 'accnt_nm'),)
    id = models.BigAutoField(primary_key=True)
    rpt_nm = models.TextField(default='')
    rpt_tp = models.TextField(default='')
    crp_cd = models.CharField(max_length=20)
    crp_nm = models.TextField()
    disc_year = models.CharField(max_length=4)
    disc_month = models.CharField(max_length=2)
    disc_quarter = models.IntegerField()
    disc_categorizing = models.TextField(default='')
    fix_or_prov_or_estm = models.CharField(default='F', max_length=1)
    accnt_cd = models.CharField(max_length=20)
    accnt_nm = models.CharField(max_length=100)
    value = models.FloatField(null=True)
    rmk = models.TextField(null=True)
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FnGuideFinancialReport(models.Model):
    class Meta:
        unique_together = (('id', 'rpt_nm', 'rpt_tp', 'crp_cd', 'disc_year', 'disc_month', 'disc_quarter',
                            'disc_categorizing', 'fix_or_prov_or_estm', 'accnt_nm'),)
        index_together = (
            ('rpt_nm', 'rpt_tp', 'crp_cd', 'disc_year', 'disc_month', 'disc_quarter', 'disc_categorizing',
             'fix_or_prov_or_estm', 'accnt_nm'),)
    id = models.BigAutoField(primary_key=True)
    rpt_nm = models.TextField(default='')
    rpt_tp = models.TextField(default='')
    crp_cd = models.CharField(max_length=20)
    crp_nm = models.TextField()
    disc_year = models.CharField(max_length=4)
    disc_month = models.CharField(max_length=2)
    disc_quarter = models.IntegerField()
    disc_categorizing = models.TextField(default='')
    fix_or_prov_or_estm = models.CharField(default='F', max_length=1)
    accnt_cd = models.CharField(max_length=20)
    accnt_nm = models.CharField(max_length=100)
    value = models.FloatField(null=True)
    rmk = models.TextField(null=True)
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FnGuideFinancialRatio(models.Model):
    class Meta:
        unique_together = (('id', 'rpt_nm', 'rpt_tp', 'crp_cd', 'disc_year', 'disc_month', 'disc_quarter',
                            'disc_categorizing', 'fix_or_prov_or_estm', 'ratio_nm'),)
        index_together = (
            ('rpt_nm', 'rpt_tp', 'crp_cd', 'disc_year', 'disc_month', 'disc_quarter', 'disc_categorizing',
             'fix_or_prov_or_estm', 'ratio_nm'),)
    id = models.BigAutoField(primary_key=True)
    rpt_nm = models.TextField(default='')
    rpt_tp = models.TextField(default='')
    crp_cd = models.CharField(max_length=20)
    crp_nm = models.TextField()
    disc_year = models.CharField(max_length=4)
    disc_month = models.CharField(max_length=2)
    disc_quarter = models.IntegerField()
    disc_categorizing = models.TextField(default='')
    fix_or_prov_or_estm = models.CharField(default='F', max_length=1)
    ratio_cd = models.CharField(max_length=20)
    ratio_nm = models.CharField(max_length=100)
    value = models.FloatField(null=True)
    rmk = models.TextField(null=True)
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class EcosServiceList(models.Model):
    class Meta:
        unique_together = (('P_STAT_CODE', 'STAT_CODE'),)
        index_together = (('P_STAT_CODE', 'STAT_CODE'),)
    P_STAT_CODE = models.CharField(max_length=20)
    STAT_CODE = models.CharField(max_length=20)
    STAT_NAME = models.CharField(max_length=100)
    CYCLE = models.CharField(max_length=20)
    SRCH_YN = models.CharField(max_length=1)
    ORG_NAME = models.CharField(max_length=100)
    CREATE_AT = models.DateTimeField(auto_now_add=True)
    UPDATED_AT = models.DateTimeField(auto_now=True)


class EcosStatDetailItemList(models.Model):
    class Meta:
        unique_together = (('STAT_CODE', 'ITEM_CODE'),)
        index_together = (('STAT_CODE', 'ITEM_CODE'),)
    STAT_CODE = models.CharField(max_length=20)
    STAT_NAME = models.CharField(max_length=100)
    GRP_NAME = models.CharField(max_length=20)
    ITEM_CODE = models.CharField(max_length=20)
    ITEM_NAME = models.CharField(max_length=100)
    CYCLE = models.CharField(max_length=20)
    START_TIME = models.CharField(max_length=20)
    END_TIME = models.CharField(max_length=20)
    DATA_CNT = models.IntegerField()
    CREATE_AT = models.DateTimeField(auto_now_add=True)
    UPDATED_AT = models.DateTimeField(auto_now=True)


class EcosStatisticSearchData(models.Model):
    class Meta:
        unique_together = (('STAT_CODE', 'ITEM_CODE1', 'ITEM_CODE2', 'ITEM_CODE3', 'UNIT_NAME', 'TIME'),)
        index_together = (('STAT_CODE', 'ITEM_CODE1', 'ITEM_CODE2', 'ITEM_CODE3', 'UNIT_NAME', 'TIME'),)
    STAT_CODE = models.CharField(max_length=20)
    STAT_NAME = models.CharField(max_length=100)
    ITEM_CODE1 = models.CharField(max_length=20)
    ITEM_NAME1 = models.CharField(max_length=100)
    ITEM_CODE2 = models.CharField(max_length=20)
    ITEM_NAME2 = models.CharField(max_length=100)
    ITEM_CODE3 = models.CharField(max_length=20)
    ITEM_NAME3 = models.CharField(max_length=100)
    UNIT_NAME = models.CharField(max_length=20)
    TIME = models.CharField(max_length=20)
    DATA_VALUE = models.CharField(max_length=20)


class FredStatisticCategory(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    parent_id = models.IntegerField()
    notes = models.TextField(default=None, null=True)


class Instrument(models.Model):
    id = models.AutoField(primary_key=True)
    external_id = models.IntegerField(default=0)
    name = models.TextField()
    in_use = models.BooleanField(default=True)


class Market(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField()
    in_use = models.BooleanField(default=True)


class MarketDataValue(models.Model):
    id = models.AutoField(primary_key=True)
    base_date = models.DateTimeField()
    instrument_id = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    market_id = models.ForeignKey(Market, on_delete=models.CASCADE)
    value = models.FloatField()
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class OECDServiceCatalog(models.Model):
    id = models.AutoField(primary_key=True)
    type = models.TextField()
    key_family = models.TextField()
    key_description = models.TextField()
