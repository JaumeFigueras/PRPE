#!/usr/bin/env python3
"""
Download M2M JSON using a randomized User-Agent from fake-useragent.

Behavior:
- Asks for a directory (positional argument) where the JSON will be saved.
- The saved filename is always "renfe.json" prefixed with the current UTC timestamp
  in the format: YYYY-MM-DD-HH-MM-SS (UTC)
  Example: 2025-11-28-14-30-05-renfe.json
- Uses only User-Agent (generated via fake_useragent.ua.random)
- Minimal headers (User-Agent only)
- No requests.Session, no proxies
- Retries a fixed number of times with a small randomized pause between attempts

Install dependencies:
    pip install requests fake-useragent

Usage:
    python download_json.py https://gtfsrt.renfe.com/vehicle_positions.json /path/to/save/dir
"""
import argparse
import json
import logging
import os
import random
import sys
import time
import requests
import datetime

from fake_useragent import UserAgent
from zoneinfo import ZoneInfo
from logging.handlers import RotatingFileHandler

from typing import Dict
from typing import Optional
from logging import Logger


def build_headers(ua: UserAgent) -> Dict[str, str]:
    """
    Build minimal headers using ua.random for User-Agent only.
    """
    return {"User-Agent": ua.random}


def save_json_to_file(data, directory: str):
    """
    Save `data` to a UTC timestamped filename in `directory`.
    Filename format: YYYY-MM-DD-HH-MM-SS_renfe.json (UTC)
    """
    ts = datetime.datetime.now(ZoneInfo("UTC")).strftime("%Y-%m-%d-%H-%M-%S")
    filename = f"{ts}-renfe.json"
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def download_json(url: str, save_dir: str, logger: Logger, max_attempts: int = 5, verify_tls: bool = True) -> bool:
    """
    Download JSON from url and save to save_dir with a UTC timestamped 'renfe.json' filename.

    Returns True on success, False on failure.
    """
    ua = UserAgent()  # uses random UAs internally

    attempt = 0
    last_exception: Optional[Exception] = None
    while attempt < max_attempts:
        attempt += 1
        headers = build_headers(ua=ua)
        timeout = random.uniform(5.0, 20.0)
        try:
            logger.debug(f"Attempt {attempt}: GET {url} headers={headers} timeout={timeout:.1f}")
            resp = requests.get(url, headers=headers, timeout=timeout, verify=verify_tls, allow_redirects=True)
            logger.debug(f"Response status: {resp.status_code}")
            if resp.status_code == 200:
                content_type = resp.headers.get("Content-Type", "")
                if "json" not in content_type.lower() and not resp.text.strip().startswith(("{", "[")):
                    logger.warning(f"Response doesn't look like JSON (Content-Type: {content_type}). Attempting to parse anyway.")
                data = resp.json()
                saved_path = save_json_to_file(data, save_dir)
                logger.info(f"Saved JSON to {saved_path}")
                return True
            elif resp.status_code in (401, 403):
                logger.error(f"Access denied (status {resp.status_code}). Aborting.", )
                return False
            else:
                logger.warning(f"Status {resp.status_code} received; will retry (attempt {attempt}/{max_attempts}).")
        except (requests.exceptions.RequestException, ValueError) as xcpt:
            last_exception = xcpt
            logger.warning(f"Attempt {attempt} failed: {xcpt}")

        # Fixed small randomized retry pause
        sleep_seconds = random.uniform(1.0, 3.0)
        logger.debug(f"Sleeping {sleep_seconds:.2f} seconds before next attempt")
        time.sleep(sleep_seconds)

    logging.error(f"All attempts failed. Last exception: {last_exception}")
    return False


def main(argv=None):
    parser = argparse.ArgumentParser(description="Download M2M JSON using fake-useragent randomized User-Agent and save it as a UTC-timestamped renfe.json in the provided directory.")
    parser.add_argument("-u", "--url", help="URL of the JSON resource to download.")
    parser.add_argument("-d", "--directory", help="Directory where the timestamped renfe.json will be saved.")
    parser.add_argument("-a", "--attempts", type=int, default=5, help="Maximum download attempts")
    parser.add_argument('-l', '--log-file', help='File to log progress or errors', required=False)
    args = parser.parse_args(argv)

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
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)  # si uses httpx
    logging.getLogger("asyncio").setLevel(logging.ERROR)

    success = download_json(url=args.url, save_dir=args.directory, max_attempts=args.attempts, logger=logger_main)
    if not success:
        sys.exit(2)


if __name__ == "__main__":
    main()