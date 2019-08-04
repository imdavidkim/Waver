from yahoofinancials import YahooFinancials
import yahoofinancials as yf
yahoo_financials = YahooFinancials('AAPL')
print(yahoo_financials)
#
# tech_stocks = ['AAPL', 'MSFT', 'INTC']
# yahoo_financials_tech = YahooFinancials(tech_stocks)
# tech_cash_flow_data_an = yahoo_financials_tech.get_financial_stmts('annual', 'cash')
# for s in tech_cash_flow_data_an["cashflowStatementHistory"]:
#     for date in tech_cash_flow_data_an["cashflowStatementHistory"][s][0]:
#         print(s, date, tech_cash_flow_data_an["cashflowStatementHistory"][s][0][date])
yahoo_financials.get_historical_stock_data("2017-09-10", "2017-10-10", "monthly")
