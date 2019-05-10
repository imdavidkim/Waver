# -*- coding: utf-8 -*-
import pandas as pd
from sqlalchemy.orm.query import Query
from sqlalchemy import and_, or_, not_, desc, asc
from sqlalchemy.orm import sessionmaker
from detective.models.base import Base, engine, session_factory
from detective.models.stock import Stocks


def get_query_object(session: sessionmaker, model: Base) -> Query:
    query = session.query(model)

    return query


def title(msg):
    print('')
    print('> ' + msg)
    print('=' * 100)


if __name__ == '__main__':
    session = session_factory()
    stock_query = get_query_object(session, Stocks)

    # whenever modification of Model, you need session.commit() to update your table
    title('case 1: Insert new item')
    stock = stock_query.filter(Stocks.code == '0000321').first()
    if not stock:
        print('stock not found(0000321) insert new row')
        stock = Stocks(code='0000321')
        session.add(stock)
        session.commit()
    else:
        print('stock using old one')

    title('case 2: delete item')
    session.delete(stock)
    session.commit()

    title('case 3: delete using where condition(multiple delete')
    delete_query = Stocks.__table__.delete().where(Stocks.code == '0000321')
    session.execute(delete_query)
    session.commit()

    title('case 3: select one item and update values')
    queryset = stock_query.filter(Stocks.code == '000001')
    item: Stocks = queryset.one()
    print(item)
    print(item.tel)
    item.tel = '91999'
    session.commit()
