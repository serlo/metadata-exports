import json
import re
import requests

from datetime import datetime, timezone


def has_description(record):
    return (
        record is not None
        and "description" in record
        and isinstance(record["description"], str)
        and not record["description"].isspace()
    )


def load_json_ld(url):
    try:
        response = requests.get(url, timeout=60)
    except requests.exceptions.ReadTimeout:
        return None

    if not response.ok:
        return None

    pattern = r'<script type="application/ld\+json">(.*?)</script>'
    matches = re.findall(pattern, response.text, re.DOTALL)

    if len(matches) == 0:
        return None

    match = matches[0]

    try:
        return json.loads(match.strip())
    except (TypeError, json.JSONDecodeError):
        pass

    return None


def current_time():
    return datetime.now(timezone.utc)


def pick(path, data):
    if len(path) == 0:
        return data

    key = path[0]

    if key in data:
        return pick(path[1:], data[key])
    else:
        return None
