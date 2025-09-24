#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations  # Needed to allow returning the type of enclosing class PEP 563

import enum

from sqlalchemy import String, ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Enum
from sqlalchemy.orm import mapped_column, relationship

from src.data_model import Base
from src.data_model.level import Level

from sqlalchemy.orm import Mapped
from typing import List
from typing import TypedDict
from typing_extensions import Unpack
from typing_extensions import NotRequired

class URLType(enum.Enum):
    ADIF_WEB = 0
    ADIF_JS_INFO = 1

class URLScrap(Base):
    __tablename__ = "url_scrap"
    url_id: Mapped[int] = mapped_column('url_id', Integer, primary_key=True, autoincrement=True)
    url: Mapped[String] = mapped_column('url', String, nullable=False)
    url_type: Mapped[URLType] = mapped_column('url_type', Enum(URLType, name='url_type_enum'), nullable=False)
    stop_id: Mapped[str] = mapped_column('stop_id', ForeignKey('stop.stop_id'), nullable=True)
    stop: Mapped["Stop"] = relationship("Stop", back_populates="urls")