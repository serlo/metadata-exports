import json
import re
import requests


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