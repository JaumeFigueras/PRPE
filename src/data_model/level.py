#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
from typing import TypedDict
from typing_extensions import Unpack
from typing_extensions import NotRequired

class Level(Base):
    __tablename__ = "level"
    level_id: Mapped[str] = mapped_column('level_id', String, primary_key=True)