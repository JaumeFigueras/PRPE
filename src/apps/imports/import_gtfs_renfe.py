#!/usr/bin/env python3
"""
Download a large GTFS file (e.g., 600MB) with robust streaming, resume support, and retries.

Key features:
- Streams to disk (no large memory usage)
- Resume incomplete downloads using HTTP Range requests
- Randomized User-Agent via fake_useragent (M2M style minimal headers)
- Retries with backoff on transient errors
- Progress logging (size, speed, ETA) to stdout
- Configurable chunk size
- Date-based output structure:
  - Saves to <base_dir>/<YYYY-MM-DD>/<YYYY-MM-DD>_<basename>
- Optional comparison and deduplication:
  - Compares today's file with yesterday's using SHA256
  - If equal, deletes today's file and creates a symlink to yesterday's

Install dependencies:
    pip install requests fake-useragent

Usage example:
    python src/apps/import/import_gtfs_large.py \
        --url https://example.com/gtfs.zip \
        --out /tmp/gtfs/gtfs.zip \
        --compare
"""
from __future__ import annotations

import argparse
import hashlib
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple

import requests
from fake_useragent import UserAgent  # type: ignore

from logging import Logger


def build_headers(ua: UserAgent) -> Dict[str, str]:
    """Minimal headers with randomized User-Agent."""
    return {"User-Agent": ua.random}


def format_bytes(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    f = float(n)
    while f >= 1024 and i < len(units) - 1:
        f /= 1024.0
        i += 1
    return f"{f:.2f} {units[i]}"


def sha256_file(path: str, chunk_size: int = 8 * 1024 * 1024) -> str:
    """Compute SHA256 checksum for a file in chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def stream_download(url: str, out_path: str, chunk_size: int, max_attempts: int, logger: Logger) -> bool:
    """
    Stream download with resume support:
    - If <final_path>.partial exists, resume from its size.
    - Download to <final_path>.partial and rename to <final_path> when complete.

    Path and filename behavior:
    - Create a subdirectory under the provided out_path's directory named YYYY-MM-DD.
    - Save the final file with name YYYY-MM-DD_<basename-of-out_path>.
      For example, if out_path=/tmp/gtfs/gtfs.zip and now is 2025-11-30,
      the file will be saved as /tmp/gtfs/2025-11-30/2025-11-30_gtfs.zip.
    """
    # Derive dated directory and date-based filename
    now = datetime.now()
    date_dir = now.strftime("%Y-%m-%d")
    date_name = now.strftime("%Y-%m-%d")

    base_dir = os.path.dirname(out_path)
    base_name = os.path.basename(out_path)

    dated_dir = os.path.join(base_dir, date_dir)
    final_out_path = os.path.join(dated_dir, f"{date_name}_{base_name}")

    ua = UserAgent()
    headers = build_headers(ua)

    # Ensure directories exist
    os.makedirs(dated_dir, exist_ok=True)

    # Use .partial file alongside final_out_path
    partial_path = final_out_path + ".partial"

    # Determine resume offset
    resume_from = 0
    if os.path.exists(partial_path):
        resume_from = os.path.getsize(partial_path)

    attempt = 0
    last_exc: Optional[Exception] = None
    while attempt < max_attempts:
        attempt += 1

        # Add Range header if resuming
        req_headers = dict(headers)
        if resume_from > 0:
            req_headers["Range"] = f"bytes={resume_from}-"

        logger.info(
            f"Attempt {attempt}/{max_attempts}: GET {url} -> {final_out_path} "
            f"(resume_from={resume_from} bytes, chunk_size={format_bytes(chunk_size)})"
        )

        start_time = time.time()
        try:
            with requests.get(url, headers=req_headers, stream=True, timeout=(10, 60), verify=verify_tls) as resp:
                status = resp.status_code
                # Status handling:
                # 200 OK for full download; 206 Partial Content for resume
                if not (status == 200 or (status == 206 and resume_from > 0)):
                    logger.warning(f"Unexpected status {status}; will retry")
                    time.sleep(min(3.0, 0.25 * attempt))
                    continue

                # Get total length if server provides it
                content_length = resp.headers.get("Content-Length")
                try:
                    total_bytes = int(content_length) if content_length is not None else None
                except ValueError:
                    total_bytes = None

                # Open file in append or write mode
                mode = "ab" if resume_from > 0 else "wb"
                downloaded = resume_from
                last_log_t = start_time

                with open(partial_path, mode) as f:
                    for chunk in resp.iter_content(chunk_size=chunk_size):
                        if not chunk:
                            continue
                        f.write(chunk)
                        downloaded += len(chunk)

                        # Progress log roughly every second
                        now_t = time.time()
                        if now_t - last_log_t >= 1.0:
                            elapsed = now_t - start_time
                            speed_bps = (downloaded - resume_from) / elapsed if elapsed > 0 else 0
                            speed_str = f"{format_bytes(int(speed_bps))}/s"
                            total_str = format_bytes(downloaded)
                            if total_bytes is not None:
                                size_str = f"{total_str} / {format_bytes(resume_from + total_bytes)}"
                                remaining = resume_from + total_bytes - downloaded
                                eta = remaining / speed_bps if speed_bps > 0 else float("inf")
                                eta_str = f"{int(eta)}s" if eta != float("inf") else "∞"
                                logger.info(f"Progress: {size_str} at {speed_str}, ETA ~ {eta_str}")
                            else:
                                logger.info(f"Progress: {total_str} at {speed_str}")
                            last_log_t = now_t

                # Completed successfully; rename partial to final
                os.replace(partial_path, final_out_path)
                logger.info(f"Downloaded file saved to {final_out_path} ({format_bytes(downloaded)})")
                return True

        except (requests.exceptions.RequestException, OSError) as e:
            last_exc = e
            logger.warning(f"Attempt {attempt} failed: {e}")
            # brief backoff
            time.sleep(min(3.0, 0.5 * attempt))

    logger.error(f"All attempts failed. Last exception: {last_exc}")
    return False


def find_latest_file_in_dir(dir_path: str, basename: str) -> Optional[str]:
    """
    Find the latest date-stamped file for a given basename inside dir_path.

    Files are expected in format: YYYY-MM-DD_<basename>
    Returns the full file path or None if none found.

    If the latest file is a symlink, resolve and return the symlink target path.
    """
    if not os.path.isdir(dir_path):
        return None
    try:
        candidates = [
            f for f in os.listdir(dir_path)
            if f.endswith(f"_{basename}") and len(f.split("_", 1)[0]) == 10  # "YYYY-MM-DD"
        ]
    except OSError:
        return None
    if not candidates:
        return None

    # Lexical sort works with date prefix (YYYY-MM-DD)
    candidates.sort()
    latest = os.path.join(dir_path, candidates[-1])

    # If latest is a symlink, resolve to its target (absolute)
    try:
        if os.path.islink(latest):
            target = os.readlink(latest)
            if not os.path.isabs(target):
                target = os.path.abspath(os.path.join(dir_path, target))
            return target
    except OSError:
        # If resolving fails, fall back to the symlink path itself
        return latest

    return latest


def compare_today_with_previous_day_checksum(out_base_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Compare today's latest downloaded file against yesterday's latest using SHA256 checksum.

    Inputs:
    - out_base_path: The original 'out' path used for downloads (e.g., /tmp/gtfs/gtfs.zip).
      Files are stored under:
        <dirname(out_base_path)>/<YYYY-MM-DD>/<YYYY-MM-DD>_<basename(out_base_path)>

    Returns:
    - (is_same, today_file, yesterday_file)
      where is_same is True if both files exist and their SHA256 hashes match,
      False otherwise. today_file and yesterday_file are the paths used for comparison
      (or None if not found).
    """
    base_dir = os.path.dirname(out_base_path) or "."
    base_name = os.path.basename(out_base_path)

    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    today_dir = os.path.join(base_dir, today)
    yesterday_dir = os.path.join(base_dir, yesterday)

    today_file = find_latest_file_in_dir(today_dir, base_name)
    yesterday_file = find_latest_file_in_dir(yesterday_dir, base_name)

    if not today_file or not yesterday_file:
        return (False, today_file, yesterday_file)

    try:
        hash_today = sha256_file(today_file)
        hash_yesterday = sha256_file(yesterday_file)
        return (hash_today == hash_yesterday, today_file, yesterday_file)
    except OSError:
        return (False, today_file, yesterday_file)


def deduplicate_today_with_symlink(today_file: str, yesterday_file: str, logger: logging.Logger) -> bool:
    """
    When today's file is identical to yesterday's, replace today's file with a symlink to yesterday's.

    Behavior:
    - Deletes today's file.
    - Creates a symbolic link at the same path (today_file) pointing to yesterday_file.
    - If today_file already exists as a symlink, it will be replaced.
    - Returns True on success, False on failure.

    Notes:
    - The symlink target uses an absolute path to yesterday_file for robustness.
    - Ensure the filesystem supports symlinks and the process has sufficient permissions.
    """
    try:
        # Remove today's file if it exists (regular file or symlink)
        if os.path.exists(today_file) or os.path.islink(today_file):
            os.remove(today_file)
            logger.info(f"Removed today's file: {today_file}")

        # Use absolute path for target
        target = os.path.abspath(yesterday_file)
        os.symlink(target, today_file)
        logger.info(f"Created symlink: {today_file} -> {target}")
        return True
    except OSError as e:
        logger.error(f"Failed to create symlink from '{today_file}' to '{yesterday_file}': {e}")
        return False


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Stream download a large GTFS file with resume support.")
    parser.add_argument("-u", "--url", required=True, help="GTFS file URL (e.g., https://example.com/gtfs.zip)")
    parser.add_argument("-o", "--out", required=True, help="Destination base file path (e.g., /tmp/gtfs/gtfs.zip)")
    parser.add_argument("-a", "--attempts", type=int, default=5, help="Maximum attempts (default: 5)")
    parser.add_argument("--chunk-size", type=int, default=4 * 1024 * 1024, help="Chunk size in bytes (default: 4MB)")
    parser.add_argument("--insecure", action="store_true", help="Disable TLS verification")
    parser.add_argument("--verbose", action="store_true", help="Enable info-level logging")
    parser.add_argument("--compare", action="store_true", help="After download, compare today's latest file with yesterday's latest via checksum and deduplicate with a symlink")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    logger = logging.getLogger("gtfs_downloader")

    ok = stream_download(
        url=args.url,
        out_path=args.out,
        chunk_size=args.chunk_size,
        max_attempts=args.attempts,
        verify_tls=not args.insecure,
        logger=logger,
    )
    if not ok:
        return 2

    if args.compare:
        same, today_fp, yest_fp = compare_today_with_previous_day_checksum(args.out)
        if same and today_fp and yest_fp:
            logger.info(f"Today's file is identical to yesterday's (SHA256 match): {today_fp} == {yest_fp}")
            if deduplicate_today_with_symlink(today_fp, yest_fp, logger):
                logger.info("Deduplication successful: today's file replaced with symlink to yesterday's.")
            else:
                logger.warning("Deduplication attempted but failed.")
        else:
            logger.info(f"Today's file differs from yesterday's or missing. Today: {today_fp}, Yesterday: {yest_fp}")

    return 0


if __name__ == "__main__":
    sys.exit(main())