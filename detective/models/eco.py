# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, DateTime, Integer, PrimaryKeyConstraint
from sqlalchemy.sql import func
from .base import Base


class EcosServiceList(Base):
    __tablename__ = 'EcosServiceList'
    __table_args__ = (PrimaryKeyConstraint('P_STAT_CODE', 'STAT_CODE'), {})

    P_STAT_CODE = Column(String(20))
    STAT_CODE = Column(String(20))
    STAT_NAME = Column(String(100))
    CYCLE = Column(String(20))
    SRCH_YN = Column(String(1))
    ORG_NAME = Column(String(100))
    CREATE_AT = Column(DateTime(timezone=True), server_default=func.now())
    UPDATED_AT = Column(DateTime(timezone=True), onupdate=func.now())


class EcosStatDetailItemList(Base):
    __tablename__ = 'EcosStatDetailItemList'

    STAT_CODE = Column(String(20), primary_key=True)
    STAT_NAME = Column(String(100))
    GRP_NAME = Column(String(20))
    ITEM_CODE = Column(String(20), primary_key=True)
    ITEM_NAME = Column(String(100))
    CYCLE = Column(String(20))
    START_TIME = Column(String(20))
    END_TIME = Column(String(20))
    DATA_CNT = Column(Integer)
    CREATE_AT = Column(DateTime(timezone=True), server_default=func.now())
    UPDATED_AT = Column(DateTime(timezone=True), onupdate=func.now())


class EcosStatisticSearchData(Base):
    __tablename__ = 'EcosStatisticSearchData'

    STAT_CODE = Column(String(20), primary_key=True)
    STAT_NAME = Column(String(100))
    ITEM_CODE1 = Column(String(20), primary_key=True)
    ITEM_NAME1 = Column(String(100), primary_key=True)
    ITEM_CODE2 = Column(String(20), primary_key=True)
    ITEM_NAME2 = Column(String(100), primary_key=True)
    ITEM_CODE3 = Column(String(20), primary_key=True)
    ITEM_NAME3 = Column(String(100))
    UNIT_NAME = Column(String(20), primary_key=True)
    TIME = Column(String(20), primary_key=True)
    DATA_VALUE = Column(String(20))
