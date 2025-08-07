#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import partridge as ptg
import pandas as pd

if __name__ == "__main__":

    gtfs_path = './fomento_transit.zip'
    feed = ptg.load_feed(gtfs_path, view=None)
    matching_routes = feed.routes[feed.routes['route_short_name'] == 'R2N']
    route_trips = feed.trips[feed.trips['route_id'] == '51T0003R2N']
    trip_id = '5177V28556R2N'
    # 1. Get the service_id for this trip
    service_id = feed.trips.loc[feed.trips['trip_id'] == trip_id, 'service_id'].values[0]

    # 2. Get all service dates in the feed
    service_dates = ptg.read_service_ids_by_date(gtfs_path)

    # 3. Find dates where this service_id is active
    active_dates = [date for date, ids in service_dates.items() if service_id in ids]

    # Convert to sorted list of datetime.date
    active_dates = sorted(active_dates)


    stop_times = feed.stop_times[feed.stop_times['trip_id'] == trip_id]
    stop_times_sorted = stop_times.sort_values('stop_sequence')
    start_time = stop_times_sorted.iloc[0]['departure_time']
    print(matching_routes[['route_id', 'route_short_name', 'route_long_name']])
    print(route_trips)
    print(f"Trip {trip_id} (service_id: {service_id}) runs on:")
    for date in active_dates:
        print(f" - {date}")
    print(stop_times_sorted)
    print(f"Trip {trip_id} starts at {start_time}")