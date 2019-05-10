# -*- coding: utf-8 -*-
import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import sessionmaker, Query
from detective.settings import config

engine = create_engine(f'sqlite:///{os.path.join(config.project_path, "waver_db.sqlite3")}')

_SessionFactory = sessionmaker(bind=engine)

Base = declarative_base()


class BaseUtil(object):
    @classmethod
    def df(cls, queryset: Query) -> pd.DataFrame:
        return pd.read_sql(queryset.statement,
                           queryset.session.bind,
                           index_col=[key.name for key in inspect(cls).primary_key])

    def __repr__(self):
        keys = [key.name for key in inspect(self.__class__).primary_key]
        info = ", ".join([f'{key}={getattr(self, key)}' for key in keys])
        return f'<{self.__class__.__name__} {info}>'


def session_factory() -> sessionmaker:
    Base.metadata.create_all(engine)
    return _SessionFactory()
