#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations  # Needed to allow returning the type of enclosing class PEP 563

import enum

from sqlalchemy import String, ForeignKey
from sqlalchemy import Float
from sqlalchemy import Enum
from sqlalchemy.orm import mapped_column, relationship

from src.data_model import Base

from sqlalchemy.orm import Mapped
from typing import List
from typing import Dict
from typing import Any


class LocationType(enum.Enum):
    STOP_OR_PLATFORM = 0
    STATION = 1
    ENTRANCE_EXIT = 2
    GENERIC_NODE = 3
    BOARDING_AREA = 4

class WheelchairBoarding(enum.Enum):
    NO_INFORMATION = 0
    SOME_YES = 1
    NO = 2

class Stop(Base):
    # https://gtfs.org/documentation/schedule/reference/#stopstxt
    __tablename__ = 'stop'
    stop_id: Mapped[str] = mapped_column('stop_id', String, primary_key=True)
    stop_code: Mapped[str] = mapped_column('stop_code', String, nullable=True)
    stop_name: Mapped[str] = mapped_column('stop_name', String, nullable=True)
    tts_stop_name: Mapped[str] = mapped_column('tts_stop_name', String, nullable=True)
    stop_desc: Mapped[str] = mapped_column('stop_desc', String, nullable=True)
    stop_lat: Mapped[float] = mapped_column('stop_lat', Float, nullable=True)
    stop_lon: Mapped[float] = mapped_column('stop_lon', Float, nullable=True)
    zone_id: Mapped[str] = mapped_column('zone_id', String, nullable=True)
    stop_url: Mapped[str] = mapped_column('stop_url', String, nullable=True)
    location_type: Mapped[LocationType] = mapped_column('location_type', Enum(LocationType), nullable=True)
    parent_station_id: Mapped[str] = mapped_column('parent_station_id', ForeignKey('stop.stop_id'), nullable=True)
    stop_timezone: Mapped[str] = mapped_column('stop_timezone', String, nullable=True)
    wheelchair_boarding: Mapped[WheelchairBoarding] = mapped_column('wheelchair_boarding', Enum(WheelchairBoarding), nullable=True)
    level_id: Mapped[str] = mapped_column('level_id', ForeignKey('level.level_id'), nullable=True)
    platform_code: Mapped[str] = mapped_column('platform_code', String, nullable=True)

    parent_station: Mapped[Stop] = relationship("Stop", back_populates="children_stop", remote_side=[stop_id])
    children_stop: Mapped[List[Stop]] = relationship("Stop", back_populates="parent_station")
    level: Mapped["Level"] = relationship(back_populates='stop')

    def __init__(self, **kwargs: Dict[str, Any]) -> None:
        super().__init__(**kwargs)
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)