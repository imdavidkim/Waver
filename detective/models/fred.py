# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, Integer, Text

from .base import Base


class FredStatisticCategory(Base):
    __tablename__ = 'FredStatisticCategory'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    parent_id = Column(Integer)
    notes = Column(Text, default=None, nullable=True)
