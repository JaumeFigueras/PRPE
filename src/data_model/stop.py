#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations  # Needed to allow returning the type of enclosing class PEP 563

import enum

from sqlalchemy import String, ForeignKey
from sqlalchemy import Float
from sqlalchemy import Enum
from sqlalchemy.orm import mapped_column, relationship

from src.data_model import Base
from src.data_model.level import Level

from sqlalchemy.orm import Mapped
from typing import List
from typing import TypedDict
from typing_extensions import Unpack
from typing_extensions import NotRequired

class LocationType(enum.Enum):
    """
    GTFS `location_type` field values.

    Attributes
    ----------
    STOP_OR_PLATFORM : int
        A location where passengers board or disembark from a transit vehicle.
    STATION : int
        A physical structure or area containing one or more stops.
    ENTRANCE_EXIT : int
        A location where passengers can enter or exit a station.
    GENERIC_NODE : int
        A location that is neither a stop nor a station, typically used for path linking.
    BOARDING_AREA : int
        A specific boarding location within a station or platform.

    Notes
    -----
    The definition od location_type and its characteristics can be found in the stop.txt GTFS Spec

    References
    ----------
    GTFS Reference:
        https://gtfs.org/documentation/schedule/reference/#stopstxt
    """
    STOP_OR_PLATFORM = 0
    STATION = 1
    ENTRANCE_EXIT = 2
    GENERIC_NODE = 3
    BOARDING_AREA = 4

class WheelchairBoarding(enum.Enum):
    """
    GTFS `wheelchair_boarding` accessibility values.

    Attributes
    ----------
    NO_INFORMATION : int
        No accessibility information is provided.
    SOME_YES : int
        At least some vehicles at this location can accommodate wheelchairs.
    NO : int
        Wheelchair boarding is not possible at this location.

    Notes
    -----
    The definition od wheelchair_boarding and its characteristics can be found in the stop.txt GTFS Spec

    References
    ----------
    GTFS Reference:
        https://gtfs.org/documentation/schedule/reference/#stopstxt
    """
    NO_INFORMATION = 0
    SOME_YES = 1
    NO = 2

class StopParams(TypedDict):
    """
    Parameters accepted by the `Stop` constructor.

    stop_id : str
        Unique identifier for the stop.
    stop_code : str, optional
        Short code for the stop, often used in rider-facing systems.
    stop_name : str, optional
        Name of the stop as displayed to riders.
    tts_stop_name : str, optional
        Text-to-speech version of the stop name.
    stop_desc : str, optional
        Description of the stop.
    stop_lat : float, optional
        Latitude of the stop in WGS 84.
    stop_lon : float, optional
        Longitude of the stop in WGS 84.
    zone_id : str, optional
        Fare zone for the stop.
    stop_url : str, optional
        URL with more information about the stop.
    location_type : LocationType, optional
        Type of the location (see `LocationType`).
    parent_station_id : str, optional
        ID of the parent station if applicable.
    stop_timezone : str, optional
        Timezone of the stop if different from the agency.
    wheelchair_boarding : WheelchairBoarding, optional
        Accessibility information (see `WheelchairBoarding`).
    level_id : str, optional
        ID of the level in which this stop is located.
    platform_code : str, optional
        Platform identifier for rider information.
    parent_station : Stop, optional
        Parent station relationship object.
    level : Level, optional
        Level relationship object.
    """
    stop_id: str
    stop_code: NotRequired[str]
    stop_name: NotRequired[str]
    tts_stop_name: NotRequired[str]
    stop_desc: NotRequired[str]
    stop_lat: NotRequired[float]
    stop_lon: NotRequired[float]
    zone_id: NotRequired[str]
    stop_url: NotRequired[str]
    location_type: NotRequired[LocationType]
    parent_station_id: NotRequired[str]
    stop_timezone: NotRequired[str]
    wheelchair_boarding: NotRequired[WheelchairBoarding]
    level_id: NotRequired[str]
    platform_code: NotRequired[str]
    parent_station: NotRequired[Stop]
    level: NotRequired[Level]

class Stop(Base):
    """
    GTFS Stop entity.

    Represents a location where passengers board or alight from transit
    vehicles, or a related facility such as a station, entrance, or boarding area.

    Parameters
    ----------
    **kwargs : StopParams
        Initialization parameters matching GTFS stop fields.

    Attributes
    ----------
    stop_id : str
        Primary key, unique identifier for the stop.
    stop_code : str, optional
        Short rider-facing code for the stop.
    stop_name : str, optional
        Name of the stop.
    tts_stop_name : str, optional
        Text-to-speech stop name.
    stop_desc : str, optional
        Description of the stop.
    stop_lat : float, optional
        Latitude in WGS 84.
    stop_lon : float, optional
        Longitude in WGS 84.
    zone_id : str, optional
        Fare zone ID.
    stop_url : str, optional
        URL with details about the stop.
    location_type : LocationType, optional
        Type of location.
    parent_station_id : str, optional
        Foreign key to another `Stop` if this is a child location.
    stop_timezone : str, optional
        Timezone for the stop.
    wheelchair_boarding : WheelchairBoarding, optional
        Accessibility indicator.
    level_id : str, optional
        Foreign key to `Level`.
    platform_code : str, optional
        Platform identifier.
    parent_station : Stop, optional
        Parent station if applicable. It is a SQLAlchemy relation.
    children_stop : list of Stop
        Stops that have this stop as their parent. It is a SQLAlchemy relation.
    level : Level, optional
        Level object linked to the stop. It is a SQLAlchemy relation.

    Examples
    --------
    >>> stop = Stop(
    ...     stop_id="STOP123",
    ...     stop_name="Main Street",
    ...     stop_lat=40.7128,
    ...     stop_lon=-74.0060,
    ...     location_type=LocationType.STOP_OR_PLATFORM
    ... )

    References
    ----------
    GTFS Reference:
        https://gtfs.org/documentation/schedule/reference/#stopstxt
    """
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
    location_type: Mapped[LocationType] = mapped_column('location_type', Enum(LocationType, name='location_type_enum'), nullable=True)
    parent_stop_id: Mapped[str] = mapped_column('parent_stop_id', ForeignKey('stop.stop_id'), nullable=True)
    stop_timezone: Mapped[str] = mapped_column('stop_timezone', String, nullable=True)
    wheelchair_boarding: Mapped[WheelchairBoarding] = mapped_column('wheelchair_boarding', Enum(WheelchairBoarding, name='wheelchair_boarding_enum'), nullable=True)
    level_id: Mapped[str] = mapped_column('level_id', ForeignKey('level.level_id'), nullable=True)
    platform_code: Mapped[str] = mapped_column('platform_code', String, nullable=True)

    children_stops: Mapped[List[Stop]] = relationship("Stop", back_populates="parent_stop")
    parent_stop: Mapped[Stop] = relationship("Stop", back_populates="children_stops", remote_side=[stop_id])
    level: Mapped["Level"] = relationship(back_populates='stop')
    urls: Mapped[List["URLScrap"]] = relationship(back_populates="stop")

    def __init__(self, **kwargs: Unpack[StopParams]) -> None:
        """
        Initialize a Stop instance.

        Assigns provided keyword arguments to attributes if they match
        model fields.

        Parameters
        ----------
        **kwargs : StopParams
            Field values corresponding to GTFS stop attributes.
        """
        super().__init__()
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
