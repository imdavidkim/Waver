# -*- coding: utf-8 -*-

from sqlalchemy.orm.attributes import InstrumentedAttribute

from detective.models.base import Base
from detective.models.base import session_factory


def get_column_description(model: Base, col: InstrumentedAttribute):
    session = session_factory()
    query = session.query(model, col)
    session.close()

    return query.column_descriptions


if __name__ == '__main__':
    from detective.models.stock import Stocks

    print(get_column_description(Stocks, Stocks.address))

