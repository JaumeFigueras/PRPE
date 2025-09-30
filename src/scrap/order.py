#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime

from typing import TypedDict
from typing import Unpack


class ScrapOrderParams(TypedDict):
    scheduled_at: datetime.datetime
    stop_id: str


class ScrapOrder:

    def __init__(self, **kwargs: Unpack[ScrapOrderParams]):
        self.scheduled_at = kwargs.get("scheduled_at")
        self.stop_id = kwargs.get("stop_id")