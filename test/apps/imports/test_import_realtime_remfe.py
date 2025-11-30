import re
import json
import logging
import datetime
from pathlib import Path

import pytest
import requests
from requests.exceptions import ConnectionError

# Import the module under test
# Adjust import path if test layout differs; assuming src is on PYTHONPATH via pytest.ini or env
from src.apps.imports.import_realtime_renfe import (
    build_headers,
    save_json_to_file,
    download_json,
)


class DummyUA:
    """Simple stand‑in for fake_useragent.UserAgent to avoid network dependency."""
    random = "DummyUserAgent/1.0"


def test_build_headers_contains_user_agent():
    headers = build_headers(DummyUA())
    assert "User-Agent" in headers
    assert headers["User-Agent"] == DummyUA.random
    # Ensure minimal headers (only User-Agent as per implementation)
    assert len(headers) == 1


def test_save_json_to_file_creates_timestamped_file(tmp_path):
    data = {"k": "v"}
    path = save_json_to_file(data, str(tmp_path))
    assert Path(path).exists()
    # Filename pattern: YYYY-MM-DD-HH-MM-SS-renfe.json
    pattern = r"^\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-renfe\.json$"
    assert re.match(pattern, Path(path).name), f"Unexpected filename '{Path(path).name}'"
    saved = json.loads(Path(path).read_text(encoding="utf-8"))
    assert saved == data


def test_download_json_success(requests_mock, tmp_path, caplog):
    url = "https://example.com/vehicle_positions.json"
    payload = {"vehicles": []}
    requests_mock.get(url, json=payload, status_code=200, headers={"Content-Type": "application/json"})
    logger = logging.getLogger("test_success")

    caplog.set_level(logging.DEBUG)
    ok = download_json(url=url, save_dir=str(tmp_path), max_attempts=1, verify_tls=True, logger=logger)
    assert ok is True

    # One call only (success on first attempt)
    assert requests_mock.call_count == 1

    # File exists
    files = list(tmp_path.glob("*-renfe.json"))
    assert len(files) == 1
    assert json.loads(files[0].read_text(encoding="utf-8")) == payload


def test_download_json_success_non_json_content_type(requests_mock, tmp_path):
    """Content-Type not indicating JSON but body is JSON; should still parse and save."""
    url = "https://example.com/data"
    payload = {"ok": True}
    requests_mock.get(url, text=json.dumps(payload), status_code=200, headers={"Content-Type": "text/plain"})
    logger = logging.getLogger("test_non_json_ct")

    ok = download_json(url=url, save_dir=str(tmp_path), max_attempts=1, verify_tls=True, logger=logger)
    assert ok is True
    files = list(tmp_path.glob("*-renfe.json"))
    assert len(files) == 1
    assert json.loads(files[0].read_text(encoding="utf-8")) == payload


def test_download_json_access_denied_403(requests_mock, tmp_path):
    url = "https://example.com/forbidden"
    requests_mock.get(url, status_code=403)
    logger = logging.getLogger("test_access_denied")

    ok = download_json(url=url, save_dir=str(tmp_path), max_attempts=2, verify_tls=True, logger=logger)
    assert ok is False
    # Should stop on first 403 (no retries beyond)
    assert requests_mock.call_count == 1
    assert list(tmp_path.glob("*-renfe.json")) == []


def test_download_json_retries_then_success(requests_mock, tmp_path):
    url = "https://example.com/flaky"
    payload = {"final": "ok"}
    # First two attempts: 500, third: 200
    requests_mock.get(url, [
        {'status_code': 500},
        {'status_code': 500},
        {'json': payload, 'status_code': 200, 'headers': {'Content-Type': 'application/json'}}
    ])
    logger = logging.getLogger("test_retries")

    ok = download_json(url=url, save_dir=str(tmp_path), max_attempts=3, verify_tls=True, logger=logger)
    assert ok is True
    assert requests_mock.call_count == 3
    files = list(tmp_path.glob("*-renfe.json"))
    assert len(files) == 1
    assert json.loads(files[0].read_text(encoding="utf-8")) == payload


def test_download_json_all_attempts_fail(requests_mock, tmp_path):
    url = "https://example.com/alwaysfail"
    # All attempts 500
    requests_mock.get(url, status_code=500)
    logger = logging.getLogger("test_all_fail")

    ok = download_json(url=url, save_dir=str(tmp_path), max_attempts=2, verify_tls=True, logger=logger)
    assert ok is False
    assert requests_mock.call_count == 2
    assert list(tmp_path.glob("*-renfe.json")) == []


def todo_test_download_json_exception_then_success(requests_mock, tmp_path):
    url = "https://example.com/unstable"
    payload = {"after": "recovery"}

    # Simulate connection error first, then success
    def _request_callback(request, context):
        if requests_mock.call_count == 0:
            raise ConnectionError("Simulated network issue")
        context.status_code = 200
        context.headers["Content-Type"] = "application/json"
        return json.dumps(payload)

    requests_mock.get(url, text=_request_callback)
    logger = logging.getLogger("test_exception_then_success")

    ok = download_json(url=url, save_dir=str(tmp_path), max_attempts=3, verify_tls=True, logger=logger)
    assert ok is True
    # At least 2 calls (one exception, one success)
    assert requests_mock.call_count >= 2
    files = list(tmp_path.glob("*-renfe.json"))
    assert len(files) == 1
    assert json.loads(files[0].read_text(encoding="utf-8")) == payload


def test_filename_timestamp_is_utc(tmp_path):
    """Indirectly verify timestamp uses UTC by comparing with current UTC time window."""
    data = {"utc": True}
    path = save_json_to_file(data, str(tmp_path))
    fname = Path(path).name
    ts_part = fname.split("-renfe.json")[0]
    # Parse back
    dt = datetime.datetime.strptime(ts_part, "%Y-%m-%d-%H-%M-%S")
    # Compare with current UTC within reasonable skew (e.g., 5 seconds)
    now_utc = datetime.datetime.utcnow()
    delta = abs((now_utc - dt).total_seconds())
    assert delta < 5, f"Timestamp {dt} not within 5s of current UTC {now_utc}"


@pytest.mark.parametrize("status_code", [500, 502, 503])
def test_download_json_transient_failures(status_code, requests_mock, tmp_path):
    """Ensure transient server errors are retried until attempts exhausted."""
    url = f"https://example.com/transient/{status_code}"
    requests_mock.get(url, status_code=status_code)
    logger = logging.getLogger(f"test_transient_{status_code}")

    ok = download_json(url=url, save_dir=str(tmp_path), max_attempts=2, verify_tls=True, logger=logger)
    assert ok is False
    assert requests_mock.call_count == 2
    assert list(tmp_path.glob("*-renfe.json")) == []


def test_download_json_invalid_json_body(requests_mock, tmp_path):
    """Invalid JSON should cause ValueError and retries; final failure returns False."""
    url = "https://example.com/invalidjson"
    requests_mock.get(url, text="NOT_JSON", status_code=200, headers={"Content-Type": "application/json"})
    logger = logging.getLogger("test_invalid_json")

    ok = download_json(url=url, save_dir=str(tmp_path), max_attempts=2, verify_tls=True, logger=logger)
    assert ok is False
    assert requests_mock.call_count == 2
    assert list(tmp_path.glob("*-renfe.json")) == []