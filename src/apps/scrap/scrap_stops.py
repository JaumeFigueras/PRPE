#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import logging
import sys
import json
import heapq
import datetime
import time

from pathlib import Path
from logging.handlers import RotatingFileHandler
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent

from src.data_model.stop import Stop
from src.data_model.url_scrap import URLScrap
from src.data_model.url_scrap import URLType
from src.scrap.order import ScrapOrder
from typing import List

def scrap_stop(order: ScrapOrder, session: Session, logger: logging.Logger) -> ScrapOrder:
    stop: Stop = session.scalar(select(Stop).where(Stop.stop_id == order.stop_id))
    urls: List[URLScrap] = list(session.scalars(select(URLScrap).where(URLScrap.stop_id == stop.stop_id)).all())
    for url in urls:
        try:
            ua = UserAgent()
            url_to_scrap = url.url
            options = Options()
            options.add_argument("--headless")
            options.add_argument(f'user-agent={ua.random}')
            driver = webdriver.Chrome(options=options)
            driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})
            driver.get(url_to_scrap)
            if url.url_type == URLType.ADIF_JS_INFO:
                iframe_locator = (By.CSS_SELECTOR, f"iframe[src*='gravita.html'][src*='IdEstacion={stop.stop_id}']")
                WebDriverWait(driver, 20).until(
                    EC.frame_to_be_available_and_switch_to_it(iframe_locator)
                )
                # Now inside; wait for internal content
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.train-row"))  # tailor this selector
                )
                html_to_write = driver.page_source
            else:
                WebDriverWait(driver, 20).until(
                    lambda d: len(d.find_elements(By.CSS_SELECTOR, "#tab-salidas tr.horario-row")) >= 1
                )
                html_to_write = driver.page_source
        except Exception as e:
            driver.quit()
            logger.error(f'Failed to scrap stop {stop.stop_id}: {e}')
            return ScrapOrder(scheduled_at=order.scheduled_at + datetime.timedelta(minutes=1), stop_id=order.stop_id)
        with open(f"{stop.stop_id}_{order.scheduled_at.strftime('%Y_%m_%d_%H_%M_%S')}_{url.url_type.name}.html", 'w') as file:
            file.write(html_to_write)
        driver.quit()
    return ScrapOrder(scheduled_at=order.scheduled_at + datetime.timedelta(minutes=5), stop_id=order.stop_id)

def main(stops_file: str, session: Session, logger: logging.Logger) -> None:
    queue: List[ScrapOrder] = list()
    stops_to_scrap: List[str] = list()
    with open(stops_file) as file:
        stops_to_scrap: List[str] = json.load(file)
        logger.info(f'Found {len(stops_to_scrap)} Stops to scrap')

    base_time = datetime.datetime.now()
    for i, stop_id in enumerate(stops_to_scrap):
        scrap_order = ScrapOrder(scheduled_at=base_time + datetime.timedelta(seconds=10*1), stop_id=stop_id)
        heapq.heappush(queue, scrap_order)
    logger.info(f'Added {len(queue)} new scraping orders')

    while queue:
        if queue[0].scheduled_at > datetime.datetime.now():
            logger.info(f'Sleeping for {(queue[0].scheduled_at - datetime.datetime.now()).total_seconds()} seconds')
            time.sleep((queue[0].scheduled_at - datetime.datetime.now()).total_seconds())
        order: ScrapOrder = heapq.heappop(queue)
        logger.info(f'Processing order for {order.stop_id} planned at {order.scheduled_at.strftime("%Y-%m-%d %H:%M:%S")}')
        next_order = scrap_stop(order, session, logger)
        heapq.heappush(queue, next_order)
        logger.info(f'Added new order for {next_order.stop_id} planned at {next_order.scheduled_at.strftime("%Y-%m-%d %H:%M:%S")}')


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
    from selenium.webdriver.remote.remote_connection import LOGGER
    LOGGER.setLevel(logging.WARNING)
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)  # si uses undetected_chromedriver o httpx
    logging.getLogger("asyncio").setLevel(logging.ERROR)

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