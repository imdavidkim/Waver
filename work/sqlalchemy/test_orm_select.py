# -*- coding: utf-8 -*-
import pandas as pd
from sqlalchemy.orm.query import Query
from sqlalchemy import and_, or_, not_, desc, asc

from detective.models.base import Base, engine, session_factory
from detective.models.stock import Stocks


def get_query_object(model: Base) -> Query:
    session = session_factory()
    query = session.query(model)
    session.close()

    return query


def title(msg):
    print('')
    print('> ' + msg)
    print('=' * 100)


if __name__ == '__main__':
    session = session_factory()
    stock_query = get_query_object(Stocks)

    # case 1 : get select 1 case
    queryset = stock_query.filter(Stocks.code == '000001')
    title('case 1: get select 1 case')
    print(Stocks.df(queryset))

    queryset = stock_query.filter(Stocks.name == '종목명')
    title('case 1-1: get select 1 case with name filter')
    print(Stocks.df(queryset))

    # with condition and multiple filter
    queryset = stock_query.filter(or_(Stocks.code == '000001',
                                      Stocks.name == '종목명')) \
        .filter(Stocks.address.isnot(None)) \
        .order_by(desc(Stocks.code))
    title('case 3: with condition and multiple filter and ordering')
    print(Stocks.df(queryset))

    # select all
    rlt = queryset.all()

    values = ([[getattr(r, x.__str__().split('.')[1]) for x in r.__table__.columns] for r in rlt])
    title('case 4: extract values to array')
    print(values)

    a: Stocks = rlt[0]
    title('case 5: select all from queryset')
    print(a.code)

    # select one
    b: Stocks = queryset.one()
    title('case 6: select one from queryset')
    print(b)

    # select direct call from query
    cursor = engine.execute("""SELECT * from Stock""")
    title('case 7: direct query call')
    print(pd.DataFrame(cursor.fetchall(), columns=cursor.keys()))
