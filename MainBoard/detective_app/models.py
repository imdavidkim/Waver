from django.db import models


# Create your models here.
class Stocks(models.Model):
    class Meta:
        unique_together = (('name', 'code', 'listing'),)
        # unique_together = (('code', 'name', 'listing'),)
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
    listing = models.CharField(max_length=1, default='Y')
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class USStocks(models.Model):
    class Meta:
        unique_together = (('cik', 'security'),)
    cik = models.CharField(max_length=10, unique=True, primary_key=True)
    security = models.TextField()
    security_wiki_link = models.URLField(null=True)
    ticker = models.CharField(max_length=20, default='')
    ticker_symbol_link = models.URLField(null=True)
    category_code = models.CharField(max_length=20, null=True)
    category_name = models.TextField()
    category_detail = models.TextField()
    sec_filing = models.URLField()
    issued_shares = models.FloatField(null=True)
    capital = models.FloatField(null=True)
    par_value = models.IntegerField(null=True)
    curr = models.CharField(max_length=3, null=True)
    tel = models.CharField(max_length=20, null=True)
    address = models.TextField(null=True)
    location = models.TextField(null=True)
    location_link = models.URLField(null=True)
    date_first_added = models.DateField(null=True)
    listing = models.CharField(max_length=1, default='Y')
    founded = models.TextField(null=True)
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class TargetStocks(models.Model):
    code = models.CharField(max_length=20, unique=True, primary_key=True)
    name = models.TextField()
    curr = models.CharField(max_length=3)
    last_price = models.FloatField(null=True)
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
