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
'''