import json
import re

import requests


def has_description(record):
    return (
        record is not None
        and "description" in record
        and isinstance(record["description"], str)
        and len(record["description"].strip()) > 0
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


def pick(path, data):
    if len(path) == 0:
        return data

    key = path[0]

    if isinstance(data, dict) and isinstance(key, str) and key in data:
        return pick(path[1:], data[key])

    if isinstance(data, list) and isinstance(key, int) and len(data) > key:
        return pick(path[1:], data[key])

    return None
