#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations  # Needed to allow returning the type of enclosing class PEP 563

import enum

from sqlalchemy import String
from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy import Integer
from sqlalchemy import Enum
from sqlalchemy.orm import mapped_column, relationship

from src.data_model import Base
from src.data_model.stop import Stop

from sqlalchemy.orm import Mapped
from typing import Union
from typing import Dict
from typing import Any
from typing import TypedDict
from typing_extensions import Unpack
from typing_extensions import NotRequired


class URLType(enum.Enum):
    ADIF_WEB = 0
    ADIF_JS_INFO = 1


class URLParams(TypedDict):
    url: str
    url_type: URLType
    stop: Union[Stop, str]


class URLScrap(Base):
    __tablename__ = "url_scrap"
    __table_args__ = (
        UniqueConstraint("url"),
    )
    url_id: Mapped[int] = mapped_column('url_id', Integer, primary_key=True, autoincrement=True)
    url: Mapped[String] = mapped_column('url', String, nullable=False)
    url_type: Mapped[URLType] = mapped_column('url_type', Enum(URLType, name='url_type_enum'), nullable=False)
    stop_id: Mapped[str] = mapped_column('stop_id', ForeignKey('stop.stop_id'), nullable=True)
    stop: Mapped["Stop"] = relationship("Stop", back_populates="urls")

    def __init__(self, **kwargs: Unpack[URLParams]) -> None:
        super().__init__()
        for key, value in kwargs.items():
            if hasattr(self, key):
                if key == 'stop' and isinstance(value, str):
                    self.stop_id = value
                else:
                    setattr(self, key, value)

    @staticmethod
    def object_hook(dct: Dict[str, Any]) -> Union[URLScrap, None]:
        if all(k in dct for k in ('url', 'url_type', 'stop')):
            return URLScrap(
                url=dct['url'],
                url_type=URLType[dct['url_type']],
                stop=dct['stop'],
            )
        return None