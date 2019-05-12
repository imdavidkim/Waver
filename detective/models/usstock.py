# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, Date, DateTime, Integer, Float, Text, PrimaryKeyConstraint
from sqlalchemy.sql import func
from .base import Base


class USStocks(Base):
    __tablename__ = 'USStocks'

    cik = Column(String(10), unique=True, primary_key=True)
    security = Column(Text)
    security_wiki_link = Column(Text, nullable=True)
    ticker = Column(String(20), default='')
    ticker_symbol_link = Column(Text, nullable=True)
    category_code = Column(String(20), nullable=True)
    category_name = Column(Text)
    category_detail = Column(Text)
    sec_filing = Column(Text)
    issued_shares = Column(Float, nullable=True)
    capital = Column(Float, nullable=True)
    par_value = Column(Integer, nullable=True)
    curr = Column(String(3), nullable=True)
    tel = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    location = Column(Text, nullable=True)
    location_link = Column(Text, nullable=True)
    date_first_added = Column(Date, nullable=True)
    listing = Column(String(1), default='Y')
    founded = Column(Text, nullable=True)

    CREATE_AT = Column(DateTime(timezone=True), server_default=func.now())
    UPDATED_AT = Column(DateTime(timezone=True), onupdate=func.now())
