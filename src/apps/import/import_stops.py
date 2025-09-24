#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import logging
import partridge as ptg
import sys
from typing import Any

import pandas as pd
from logging.handlers import RotatingFileHandler
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# Load the Stop model (no further action needed)
from src.data_model.stop import Stop, LocationType, WheelchairBoarding  # noqa: F401

def main(feed: Any, session: Session, logger: logging.Logger) -> None:
    # Helper at the beginning of the function (readable: handles NaN, pd.NA, None)
    def none_if_nan(v):
        return None if pd.isna(v) else v

    # First: only try to load the stops DataFrame
    # noinspection PyBroadException
    try:
        stops_df = feed.stops
    except AttributeError:
        logger.error("The GTFS feed does not contain a 'stops' table.")
        return
    except Exception:
        logger.exception(f"Error retrieving stops from the GTFS feed")
        return

    if stops_df is None or stops_df.empty:
        logger.warning("No stops found in the GTFS feed.")
        return

    logger.info(f"Loaded {len(stops_df)} stops from the GTFS feed.")

    # Second: separate try for creating Stop models from the entire DataFrame
    # Note: When iterating rows (Series), both row['col'] and row.get('col') work.
    # - Use row['col'] for required columns to fail fast if missing.
    # - Use row.get('col') for optional columns to avoid KeyError when absent.
    # We use row.get(...) below and validate required fields explicitly.
    # noinspection PyBroadException
    try:
        has_parent_station_id = "parent_station_id" in stops_df.columns
        stops_models = []
        created = 0
        skipped = 0

        for idx, row in stops_df.iterrows():
            # Ensure we have a primary key
            sid = none_if_nan(row.get("stop_id"))
            if sid is None or str(sid).strip() == "":
                skipped += 1
                logger.debug(f"Skipping row {idx}: missing stop_id")
                continue

            # Map enums safely
            loc_type_val = none_if_nan(row.get("location_type"))
            # noinspection PyBroadException
            try:
                location_type_enum = LocationType(int(loc_type_val)) if loc_type_val is not None else None
            except Exception:
                location_type_enum = None

            wh_val = none_if_nan(row.get("wheelchair_boarding"))
            # noinspection PyBroadException
            try:
                wheelchair_enum = WheelchairBoarding(int(wh_val)) if wh_val is not None else None
            except Exception:
                wheelchair_enum = None

            parent_station_val = (
                none_if_nan(row.get("parent_station_id")) if has_parent_station_id
                else none_if_nan(row.get("parent_station"))
            )

            stop_kwargs = {
                "stop_id": str(sid),
                "stop_code": none_if_nan(row.get("stop_code")),
                "stop_name": none_if_nan(row.get("stop_name")),
                "tts_stop_name": none_if_nan(row.get("tts_stop_name")),
                "stop_desc": none_if_nan(row.get("stop_desc")),
                "stop_lat": none_if_nan(row.get("stop_lat")),
                "stop_lon": none_if_nan(row.get("stop_lon")),
                "zone_id": none_if_nan(row.get("zone_id")),
                "stop_url": none_if_nan(row.get("stop_url")),
                "location_type": location_type_enum,
                "parent_station_id": parent_station_val,
                "stop_timezone": none_if_nan(row.get("stop_timezone")),
                "wheelchair_boarding": wheelchair_enum,
                "level_id": none_if_nan(row.get("level_id")),
                "platform_code": none_if_nan(row.get("platform_code")),
            }

            # Remove None values to rely on column nullability defaults
            stop_kwargs = {k: v for k, v in stop_kwargs.items() if v is not None}

            try:
                stop_obj = Stop(**stop_kwargs)
            except Exception as e:
                skipped += 1
                logger.debug(f"Skipping row {idx} due to model init error: {e}")
                continue

            stops_models.append(stop_obj)
            created += 1

        logger.info(f"Prepared {created} Stop models ({skipped} skipped).")

        # Not persisting unless requested:
        session.add_all(stops_models)
        session.commit()
        logger.info(f"Persisted {created} Stop records to the database.")

    except Exception:
        logger.exception(f"Error creating Stop models from stops data")

if __name__ == "__main__":  # pragma: no cover
    # Config the program arguments
    # noinspection DuplicatedCode
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', help='Host name were the database cluster is located', required=True)
    parser.add_argument('-p', '--port', type=int, help='Database cluster port', required=True)
    parser.add_argument('-d', '--database', help='Database name', required=True)
    parser.add_argument('-u', '--username', help='Database username', required=True)
    parser.add_argument('-w', '--password', help='Database password', required=True)
    parser.add_argument('-g', '--gtfs-file', help='File to retrieve data from', required=True)
    parser.add_argument('-l', '--log-file', help='File to log progress or errors', required=False)
    args = parser.parse_args()

    # Set up the Logger
    logger_main = logging.getLogger(__name__)
    if args.log_file is not None:
        handler = RotatingFileHandler(args.log_file, mode='a', maxBytes=5*1024*1024, backupCount=15, encoding='utf-8', delay=False)
        logging.basicConfig(
            format='%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s',
            handlers=[handler],
            encoding='utf-8',
            level=logging.DEBUG,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        handler = logging.StreamHandler()
        logging.basicConfig(
            format='%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s',
            handlers=[handler],
            encoding='utf-8',
            level=logging.DEBUG,
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    # Read the GTFS file with exception handling
    # noinspection PyBroadException
    try:
        feed_main = ptg.load_feed(args.gtfs_file, view=None)
    except FileNotFoundError:
        logger_main.error(f"GTFS file not found: {args.gtfs_file}")
        sys.exit(1)
    except Exception:
        logger_main.exception(f"Failed to load GTFS feed from {args.gtfs_file}")
        sys.exit(1)

    # Create the database engine using SQLAlchemy URL, covered with try/except
    # noinspection PyBroadException
    try:
        url = URL.create(
            drivername="postgresql+psycopg",
            username=args.username,
            password=args.password,
            host=args.host,
            port=args.port,
            database=args.database,
        )
        engine = create_engine(url)
        logger_main.info("Database engine created successfully.")
    except SQLAlchemyError:
        logger_main.exception(f"Failed to create database engine for {args.username}@{args.host}:{args.port}/{args.database}")
        sys.exit(1)
    except Exception:
        logger_main.exception(f"Unexpected error creating database engine")
        sys.exit(1)

    # Create a database session
    # noinspection PyBroadException
    try:
        session_main = Session(engine)
        logger_main.info("Database session created successfully.")
    except SQLAlchemyError:
        logger_main.exception(f"Failed to create database session")
        sys.exit(1)

    # Call main with feed, session, and logger
    main(feed_main, session_main, logger_main)

    # Close session
    # noinspection PyBroadException
    try:
        session_main.close()
    except Exception:
        logger_main.exception(f"Failed to close database session")
        sys.exit(1)