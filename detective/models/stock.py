# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, Integer, Float, Text, PrimaryKeyConstraint
from sqlalchemy.sql import func

from .base import Base, BaseUtil


class Stocks(BaseUtil, Base):
    __tablename__ = 'Stock'
    __table_args__ = (PrimaryKeyConstraint('code'), {})

    code = Column(String(20))
    name = Column(Text)
    category_code = Column(String(20))
    category_name = Column(Text)
    issued_shares = Column(Float)
    capital = Column(Float)
    par_value = Column(Integer)
    curr = Column(String(3))
    tel = Column(String(20))
    address = Column(Text)
    market_text = Column(Text, nullable=True)
    listing = Column(String(1), default='N')

    CREATE_AT = Column(DateTime(timezone=True), server_default=func.now())
    UPDATED_AT = Column(DateTime(timezone=True), onupdate=func.now())

