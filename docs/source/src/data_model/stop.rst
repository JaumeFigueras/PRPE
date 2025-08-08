STOP
====

In the GTFS (General Transit Feed Specification), ``stops.txt`` defines all the physical locations in
your transit system where passengers can board, alight, or interact with the system.

It is not limited to just bus stops or train platforms — it can also include stations, entrances,
and special boarding areas.

This class and its associated enumerations model the ``stops.txt`` file in SQLAlchemy in order to store
the data needed

Code
----

.. autoclass:: src.data_model.stop.Stop
   :members:
   :exclude-members: __tablename__, stop_id, stop_code, stop_name, tts_stop_name, stop_desc, stop_lat,
                     stop_lon, zone_id, stop_url, location_type, parent_station_id, stop_timezone,
                     wheelchair_boarding, level_id, platform_code, parent_station, children_stop, level
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

.. autoclass:: src.data_model.stop.LocationType
   :members:
   :exclude-members: STOP_OR_PLATFORM, STATION, ENTRANCE_EXIT, GENERIC_NODE, BOARDING_AREA
   :undoc-members:
   :show-inheritance:
   :private-members:

.. autoclass:: src.data_model.stop.WheelchairBoarding
   :members:
   :exclude-members: NO_INFORMATION, SOME_YES, NO
   :undoc-members:
   :show-inheritance:
   :private-members:
