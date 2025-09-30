#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import logging
import json
import sys

from pathlib import Path
from logging.handlers import RotatingFileHandler
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy import func
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.data_model.url_scrap import URLScrap
from src.data_model.stop import Stop

from typing import List

def main(json_file: str, skip: bool, session: Session, logger: logging.Logger) -> None:
    with open(json_file) as file:
        urls: List[URLScrap] = json.load(file, object_hook=URLScrap.object_hook)
        logger.info(f'Found {len(urls)} URLs')
        count_urls = 0
        for url in urls:
            count_url = session.scalar(select(func.count()).select_from(URLScrap).where(URLScrap.url == url.url))
            count_stop  = session.scalar(select(func.count()).select_from(Stop).where(Stop.stop_id == url.stop_id))
            if count_url == 0 and count_stop == 1:
                session.add(url)
                count_urls += 1
            elif count_url == 1:
                if not skip:
                    logger.error(f'Found existing URL {url.url} for stop {url.stop_id}')
                    return
            elif count_stop == 0:
                logger.error(f'Stop not found for URL {url.url} with stop {url.stop_id}')
                return
    logger.info(f'Adding {count_urls} new URLs')
    session.commit()

if __name__ == "__main__":  # pragma: no cover
    # Config the program arguments
    # noinspection DuplicatedCode
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', help='Host name were the database cluster is located', required=True)
    parser.add_argument('-p', '--port', type=int, help='Database cluster port', required=True)
    parser.add_argument('-d', '--database', help='Database name', required=True)
    parser.add_argument('-u', '--username', help='Database username', required=True)
    parser.add_argument('-w', '--password', help='Database password', required=True)
    parser.add_argument('-f', '--url-file', help='JSON File with the URLs', required=True)
    parser.add_argument('-s', '--skip-existing', help='Skip existing URLs', required=False, action=argparse.BooleanOptionalAction)
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
    url_file_path = Path(args.url_file)
    if not url_file_path.exists():
        logger_main.error(f"JSON URLs file not found: {args.url_file}")
        sys.exit(1)

    # Create the database engine using SQLAlchemy URL, covered with try/except
    # noinspection PyBroadException
    try:
        url_db = URL.create(
            drivername="postgresql+psycopg",
            username=args.username,
            password=args.password,
            host=args.host,
            port=args.port,
            database=args.database,
        )
        engine = create_engine(url_db)
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
    main(args.url_file, args.skip_existing, session_main, logger_main)

    # Close session
    # noinspection PyBroadException
    try:
        session_main.close()
    except Exception:
        logger_main.exception(f"Failed to close database session")
        sys.exit(1)
