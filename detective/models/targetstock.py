# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, Integer, Float, Text, PrimaryKeyConstraint
from sqlalchemy.sql import func
from .base import Base


class TargetStocks(Base):
    __tablename__ = 'TargetStocks'

    valuation_date = Column(String(10), default=str(func.now())[:10])
    code = Column(String(20), unique=True, primary_key=True)
    name = Column(Text)
    curr = Column(String(3))
    last_price = Column(Float, nullable=True)
    target_price = Column(Float, nullable=True)
    target_price2 = Column(Float, nullable=True)
    ratio = Column(Float, nullable=True)
    valuation = Column(String(1), default='B')
    permanence = Column(String(1), default='B')
    audit = Column(String(1), default='B')
    required_yield = Column(Float, nullable=True)
    return_on_equity = Column(Float, nullable=True)
    CREATE_AT = Column(DateTime(timezone=True), server_default=func.now())
    UPDATED_AT = Column(DateTime(timezone=True), onupdate=func.now())

    plus_npv = Column(String(1), default='Y')
    liquidity_rate = Column(Float, nullable=True)
    holders_share = Column(Float, nullable=True)
    holders_profit = Column(Float, nullable=True)
    holders_value = Column(Float, nullable=True)
    impairment_profit = Column(Float, nullable=True)
    issued_shares = Column(Float, nullable=True)
