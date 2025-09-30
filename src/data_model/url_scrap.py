#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Data model for externally scraped (or defined) URLs associated with railway stops.

This module defines:
- URLType: Enumeration of supported external URL categories.
- URLParams: TypedDict describing initialization parameters for URLScrap.
- URLScrap: SQLAlchemy ORM model representing a unique URL linked (optionally) to a Stop.

The JSON seed/example structure can be seen in data/urls_r2nord.json, where each entry contains:
{
  "url_type": "ADIF_WEB",
  "url": "https://www.adif.es/w/71801-barcelona-sants",
  "stop": "71801"
}

Notes
-----
The `stop` field in the JSON can be provided either as a `Stop` instance (when constructing programmatically)
or as a station identifier string (primary key of Stop). When a string is provided, it is stored in `stop_id`
and the relationship is resolved by SQLAlchemy when the object is attached to a session.
"""

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
    """
    Enumeration of supported external URL types.

    Attributes
    ----------
    ADIF_WEB : URLType
        Human-facing public webpage (station descriptive page).
    ADIF_JS_INFO : URLType
        JavaScript-enabled embedded info page (e.g., dynamic station info).
    """
    ADIF_WEB = 0
    ADIF_JS_INFO = 1


class URLScrapParams(TypedDict):
    """
    Typed dictionary of parameters accepted when constructing a URLScrap instance.

    Parameters
    ----------
    url : str
        Full external URL.
    url_type : URLType
        Category of the URL (see URLType).
    stop : Union[Stop, str]
        Either a Stop ORM instance or the stop primary key (string). If a string is passed it is
        assigned directly to `stop_id`.
    """
    url: str
    url_type: URLType
    stop: Union[Stop, str]


class URLScrap(Base):
    """
    ORM entity representing a unique external URL associated with a stop.

    The combination of URL uniqueness is enforced through a table-level UniqueConstraint.

    Attributes
    ----------
    url_id : int
        Surrogate primary key (autoincrement).
    url : str
        External URL string (must be unique).
    url_type : URLType
        Classification of the URL (see URLType).
    stop_id : str | None
        Foreign key to Stop.stop_id (may be null if not associated yet).
    stop : Stop
        SQLAlchemy relationship to the Stop entity.
    """
    __tablename__ = "url_scrap"
    __table_args__ = (
        UniqueConstraint("url"),
    )
    url_id: Mapped[int] = mapped_column('url_id', Integer, primary_key=True, autoincrement=True)
    url: Mapped[String] = mapped_column('url', String, nullable=False)
    url_type: Mapped[URLType] = mapped_column('url_type', Enum(URLType, name='url_type_enum'), nullable=False)
    stop_id: Mapped[str] = mapped_column('stop_id', ForeignKey('stop.stop_id'), nullable=True)
    stop: Mapped["Stop"] = relationship("Stop", back_populates="urls")

    def __init__(self, **kwargs: Unpack[URLScrapParams]) -> None:
        """
        Construct a URLScrap instance using keyword parameters defined in URLParams.

        Parameters
        ----------
        **kwargs : URLScrapParams
            The fields: `url`, `url_type`, and `stop`. The `stop` value can be:
            - A Stop instance (assigned to relationship)
            - A station ID string (assigned to `stop_id`)
        """
        super().__init__()
        for key, value in kwargs.items():
            if hasattr(self, key):
                if key == 'stop' and isinstance(value, str):
                    self.stop_id = value
                else:
                    setattr(self, key, value)

    @staticmethod
    def object_hook(dct: Dict[str, Any]) -> Union[URLScrap, None]:
        """
        JSON object hook helper to build a URLScrap instance from a dictionary.

        This is intended for use when loading structured JSON arrays such as
        data/urls_r2nord.json. It detects if the required keys are present
        and returns a populated model instance.

        Parameters
        ----------
        dct : dict
            Raw dictionary possibly representing a URL entry. Expected keys:
            'url', 'url_type', 'stop'.

        Returns
        -------
        URLScrap or None
            A populated URLScrap instance if all required keys are present;
            otherwise None.

        Examples
        --------
        >>> URLScrap.object_hook({
        ...     "url": "https://www.adif.es/w/71801-barcelona-sants",
        ...     "url_type": "ADIF_WEB",
        ...     "stop": "71801"
        ... })

        Notes
        -----
        The 'url_type' value in the input dictionary must match a member name
        of URLType (e.g., "ADIF_WEB", "ADIF_JS_INFO").
        """
        if all(k in dct for k in ('url', 'url_type', 'stop')):
            return URLScrap(
                url=dct['url'],
                url_type=URLType[dct['url_type']],
                stop=dct['stop'],
            )
        return None