# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, Date, DateTime, BigInteger, Integer, Float, Text
from sqlalchemy.sql import func

from .base import Base


class FnGuideDailySnapShot(Base):
    __tablename__ = 'FnGuideDailySnapShot'
    id = Column(BigInteger, primary_key=True)
    rpt_nm = Column(Text, default='', primary_key=True)
    rpt_tp = Column(Text, default='', primary_key=True)
    crp_cd = Column(String(20), primary_key=True)
    crp_nm = Column(Text)
    disc_date = Column(Date, primary_key=True)
    column_nm = Column(String(100), primary_key=True)
    key = Column(Text, primary_key=True)
    value = Column(Float, nullable=True)
    value_rmk = Column(Text, nullable=True)
    CREATE_AT = Column(DateTime(timezone=True), server_default=func.now())
    UPDATED_AT = Column(DateTime(timezone=True), onupdate=func.now())


class FnGuideSnapShot(Base):
    __tablename__ = 'FnGuideSnapShot'

    id = Column(BigInteger, primary_key=True)
    rpt_nm = Column(Text, default='', primary_key=True)
    rpt_tp = Column(Text, default='', primary_key=True)
    crp_cd = Column(String(20), primary_key=True)
    crp_nm = Column(Text)
    disc_year = Column(String(4), primary_key=True)
    disc_month = Column(String(2), primary_key=True)
    disc_quarter = Column(Integer, primary_key=True)
    disc_categorizing = Column(Text, default='', primary_key=True)
    fix_or_prov_or_estm = Column(String(1), default='F', primary_key=True)
    accnt_cd = Column(String(20))
    accnt_nm = Column(String(100), primary_key=True)
    value = Column(Float, nullable=True)
    rmk = Column(Text, nullable=True)
    CREATE_AT = Column(DateTime(timezone=True), server_default=func.now())
    UPDATED_AT = Column(DateTime(timezone=True), onupdate=func.now())


class FnGuideFinancialReport(Base):
    __tablename__ = 'FnGuideFinancialReport'

    id = Column(BigInteger, primary_key=True)
    rpt_nm = Column(Text, default='', primary_key=True)
    rpt_tp = Column(Text, default='', primary_key=True)
    crp_cd = Column(String(20), primary_key=True)
    crp_nm = Column(Text)
    disc_year = Column(String(4), primary_key=True)
    disc_month = Column(String(2), primary_key=True)
    disc_quarter = Column(Integer, primary_key=True)
    disc_categorizing = Column(Text, default='', primary_key=True)
    fix_or_prov_or_estm = Column(String(1), default='F', primary_key=True)
    accnt_cd = Column(String(20))
    accnt_nm = Column(String(100), primary_key=True)
    value = Column(Float, nullable=True)
    rmk = Column(Text, nullable=True)
    CREATE_AT = Column(DateTime(timezone=True), server_default=func.now())
    UPDATED_AT = Column(DateTime(timezone=True), onupdate=func.now())


class FnGuideFinancialRatio(Base):
    __tablename__ = 'FnGuideFinancialRatio'

    id = Column(BigInteger, primary_key=True)
    rpt_nm = Column(Text, default='', primary_key=True)
    rpt_tp = Column(Text, default='', primary_key=True)
    crp_cd = Column(String(20), primary_key=True)
    crp_nm = Column(Text)
    disc_year = Column(String(4), primary_key=True)
    disc_month = Column(String(2), primary_key=True)
    disc_quarter = Column(Integer, primary_key=True)
    disc_categorizing = Column(Text, default='', primary_key=True)
    fix_or_prov_or_estm = Column(String(1), default='F', primary_key=True)
    ratio_cd = Column(String(20))
    ratio_nm = Column(String(100), primary_key=True)
    value = Column(Float, nullable=True)
    rmk = Column(Text, nullable=True)
    CREATE_AT = Column(DateTime(timezone=True), server_default=func.now())
    UPDATED_AT = Column(DateTime(timezone=True), onupdate=func.now())
