#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import logging
import sys
import json

from pathlib import Path
from logging.handlers import RotatingFileHandler
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.data_model.stop import Stop
from src.scrap.order import ScrapOrder
from typing import List

def main(stops_file: str, session: Session, logger: logging.Logger) -> None:
    stops_to_scrap: List[str] = list()
    with open(stops_file) as file:
        stops_to_scrap: List[str] = json.load(file)
        logger.info(f'Found {len(stops_to_scrap)} Stops to scrap')


if __name__ == "__main__":  # pragma: no cover
    # Config the program arguments
    # noinspection DuplicatedCode
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', help='Host name were the database cluster is located', required=True)
    parser.add_argument('-p', '--port', type=int, help='Database cluster port', required=True)
    parser.add_argument('-d', '--database', help='Database name', required=True)
    parser.add_argument('-u', '--username', help='Database username', required=True)
    parser.add_argument('-w', '--password', help='Database password', required=True)
    parser.add_argument('-s', '--stops-file', help='Stops file to retrieve data from', required=True)
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

    # Check stops file existence
    stops_file_path = Path(args.stops_file)
    if not stops_file_path.exists():
        logger_main.error(f"JSON URLs file not found: {args.stops_file}")
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
    main(args.stops_file, session_main, logger_main)

    # Close session
    # noinspection PyBroadException
    try:
        session_main.close()
    except Exception:
        logger_main.exception(f"Failed to close database session")
        sys.exit(1)