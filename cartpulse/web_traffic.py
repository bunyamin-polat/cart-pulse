"""Parse the web server access log and load it into the warehouse."""

import re
from dataclasses import dataclass
from datetime import datetime

from cartpulse.warehouse import copy_rows, record_load

SOURCE = "web_traffic"
MAX_MALFORMED_SHARE = 0.01
COLUMNS = ("client_ip", "requested_at", "method", "path", "status", "bytes")

LOG_LINE = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] "(?P<method>[A-Z]+) (?P<path>\S+)'
    r'[^"]*" (?P<status>\d{3}) (?P<bytes>\d+|-)'
)


class MalformedLogError(ValueError):
    """Too many lines failed to parse, so the log format has probably changed."""


@dataclass(frozen=True)
class ParsedLog:
    rows: list
    total: int
    excluded: int
    malformed: int


def parse_line(line):
    """Return the columns for one log line, or None when it does not match."""
    match = LOG_LINE.match(line)
    if match is None:
        return None

    size = match["bytes"]
    return (
        match["ip"],
        datetime.strptime(match["time"], "%d/%b/%Y:%H:%M:%S %z"),
        match["method"],
        match["path"],
        int(match["status"]),
        None if size == "-" else int(size),
    )


def parse_log(lines, excluded_ips):
    """Parse every line, dropping excluded clients and counting what cannot be read."""
    rows, excluded, malformed, total = [], 0, 0, 0

    for line in lines:
        total += 1
        row = parse_line(line)
        if row is None:
            malformed += 1
        elif row[0] in excluded_ips:
            excluded += 1
        else:
            rows.append(row)

    if total and malformed / total > MAX_MALFORMED_SHARE:
        raise MalformedLogError(f"{malformed} of {total} lines could not be parsed")

    return ParsedLog(rows, total, excluded, malformed)


def sync(log_path, target, excluded_ips):
    """Replace the warehouse copy of the log in one transaction."""
    with log_path.open(encoding="utf-8", errors="replace") as lines:
        parsed = parse_log(lines, excluded_ips)

    with target, target.cursor() as cursor:
        cursor.execute("TRUNCATE staging.web_requests")
        copy_rows(cursor, "staging.web_requests", COLUMNS, parsed.rows)
        record_load(
            cursor,
            SOURCE,
            parsed.total,
            len(parsed.rows),
            rows_excluded=parsed.excluded,
            rows_rejected=parsed.malformed,
        )

    return parsed
