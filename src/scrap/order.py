#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime

from typing import TypedDict
from typing import Unpack


class ScrapOrderParams(TypedDict):
    scheduled_at: datetime.datetime
    stop_id: str


class ScrapOrder:
    __slots__ = ("scheduled_at", "stop_id")

    def __init__(self, **kwargs: Unpack[ScrapOrderParams]):
        self.scheduled_at = kwargs.get("scheduled_at")
        self.stop_id = kwargs.get("stop_id")


    def __eq__(self, other):
        if not isinstance(other, ScrapOrder):
            return NotImplemented
        return (self.scheduled_at, self.stop_id) == (other.scheduled_at, other.stop_id)

    def __lt__(self, other):
        if not isinstance(other, ScrapOrder):
            return NotImplemented
        if self.scheduled_at != other.scheduled_at:
            return self.scheduled_at < other.scheduled_at
        return self.stop_id < other.stop_id