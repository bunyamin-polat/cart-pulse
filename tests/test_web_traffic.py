import pytest

from cartpulse.web_traffic import MalformedLogError, parse_line, parse_log

LINE = (
    '83.149.9.216 - - [17/May/2015:10:05:03 +0000] "GET /index.html HTTP/1.1" '
    '200 203023 "-" "Mozilla/5.0"'
)
NO_BODY = '46.105.14.53 - - [20/May/2015:21:05:15 +0000] "GET /x HTTP/1.1" 304 -'
EXCLUDED = LINE.replace("83.149.9.216", "198.46.149.143")


def test_parse_line_reads_every_field():
    ip, requested_at, method, path, status, size = parse_line(LINE)

    assert ip == "83.149.9.216"
    assert requested_at.year == 2015
    assert method == "GET"
    assert path == "/index.html"
    assert status == 200
    assert size == 203023


def test_missing_size_becomes_null():
    assert parse_line(NO_BODY)[-1] is None


def test_unreadable_line_returns_none():
    assert parse_line("not a log line") is None


def test_excluded_clients_are_dropped_and_counted():
    parsed = parse_log([LINE, EXCLUDED], {"198.46.149.143"})

    assert len(parsed.rows) == 1
    assert parsed.excluded == 1
    assert parsed.total == 2


def test_a_few_bad_lines_are_tolerated():
    parsed = parse_log([LINE] * 199 + ["garbage"], set())

    assert parsed.malformed == 1
    assert len(parsed.rows) == 199


def test_a_changed_log_format_stops_the_load():
    with pytest.raises(MalformedLogError):
        parse_log(["garbage", LINE], set())
