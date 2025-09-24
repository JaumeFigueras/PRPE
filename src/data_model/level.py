#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlalchemy import String, ForeignKey
from sqlalchemy import Float
from sqlalchemy.orm import mapped_column

from src.data_model import Base

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import relationship
from typing import TypedDict
from typing_extensions import Unpack
from typing_extensions import NotRequired

class LevelParams(TypedDict):
    level_id: str
    level_index: NotRequired[float]
    level_name: NotRequired[str]


class Level(Base):
    __tablename__ = "level"
    level_id: Mapped[str] = mapped_column('level_id', String, primary_key=True)
    level_index: Mapped[float] = mapped_column('level_index', Float, nullable=False)
    level_name: Mapped[str] = mapped_column('level_name', String, nullable=True)

    stop: Mapped["Stop"] = relationship(back_populates='level')

    def __init__(self, **kwargs: Unpack[LevelParams]) -> None:
        """
        Initialize a Level instance.

        Assigns provided keyword arguments to attributes if they match
        model fields.

        Parameters
        ----------
        **kwargs : LevelParams
            Field values corresponding to GTFS level attributes.
        """
        super().__init__()
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)