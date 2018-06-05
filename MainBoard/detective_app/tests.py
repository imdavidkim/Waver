from django.test import TestCase

# Create your tests here.
'''
select * from detective_app_fnguidedailysnapshot
where crp_cd = '005930'
;

select * from detective_app_fnguidesnapshot
where rpt_nm = 'FinancialHighlight'
and rpt_tp = 'IFRS(연결)'
and crp_cd = '005930'
and accnt_nm = '지배주주순이익'
--and disc_categorizing = 'QUARTERLY'
and disc_categorizing = 'YEARLY'
--and fix_or_prov_or_estm = 'E'


select * from detective_app_fnguidesnapshot 
where rpt_nm = 'FinancialHighlight'
and rpt_tp = 'IFRS(연결)'
and crp_cd = '005930'
and accnt_nm = '영업이익'
and disc_categorizing = 'YEARLY'
and fix_or_prov_or_estm = 'F'
order by disc_year desc
limit 4


select * from detective_app_fnguidefinancialreport
where rpt_nm like '%포괄손익계산서%'
and rpt_tp = 'IFRS(연결)'
and crp_cd = '002620'
and disc_categorizing = 'YEARLY'
and fix_or_prov_or_estm = 'F'
and accnt_nm = '중단영업이익'

"487379.0"
"478136.0"
"479937.0"

https://amazon.qwiklab.com/users/sign_in?locale=en

select code, name, curr, last_price, target_price2, target_price, return_on_equity, ratio, target_price2 / last_price * 100 as ratio2 from detective_app_targetstocks
where ratio2 > 100
order by return_on_equity desc
limit 20;

select code, name, curr, last_price, target_price2, target_price, return_on_equity, ratio, target_price2 / last_price * 100 as ratio2 from detective_app_targetstocks
where ratio2 > 100
and return_on_equity > 14
order by ratio2 desc
limit 20;
'''