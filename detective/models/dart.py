# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, BigInteger, Integer, Text

from .base import Base


class DartRequestIndex(Base):
    __tablename__ = 'DartRequestIndex'
    req_id = Column(BigInteger, primary_key=True)
    err_code = Column(String(3))
    err_msg = Column(Text)
    page_no = Column(Integer)
    total_page = Column(Integer)
    total_count = Column(Integer)
    req_time = Column(DateTime)


class DartRequestResult(Base):
    __tablename__ = 'DartRequestResult'
    rcp_no = Column(String(20), unique=True, primary_key=True)
    crp_cls = Column(String(1))
    crp_nm = Column(Text)
    crp_cd = Column(String(20))
    rpt_nm = Column(Text)
    flr_nm = Column(Text)
    rcp_dt = Column(String(8))
    rmk = Column(Text, nullable=True)
