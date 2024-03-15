#!/usr/bin/env python

import json
import re
import sys

from typing import Dict, Any
from datetime import timedelta, datetime

import requests

from serlo_api_client import fetch_content, fetch_metadata
from utils import current_time, has_description, pick


def main(output_filename: str):
    records = list(fetch_all_metadata())

    description_cache = load_description_cache_from_last_run()
    start_time = current_time()

    for record in records:
        time_passed = current_time() - start_time

        if not has_description(record) and time_passed < timedelta(minutes=30):
            record["description"] = get_description(record, description_cache)

    with open("public/description-cache.json", "w", encoding="utf-8") as output_file:
        json.dump(description_cache, output_file)

    with open(output_filename, "w", encoding="utf-8") as output_file:
        json.dump(records, output_file)


def fetch_all_metadata():
    after = None

    while True:
        response = fetch_metadata(first=500, after=after)
        resources = response["metadata"]["resources"]  # pylint: disable=E1136
        yield from resources["nodes"]

        if resources["pageInfo"]["hasNextPage"]:
            after = resources["pageInfo"]["endCursor"]
        else:
            break


def get_description(resource: Dict[str, Any], description_cache: Dict[str, Any]):
    resource_id = resource["id"]

    if has_description(resource):
        return resource["description"]

    cached_value = description_cache.get(resource_id, {})

    # Update time in fromisoformat() to ensure all descriptions are updated
    if (
        cached_value.get("version", None) == resource["version"]
        and has_description(cached_value)
        and "dateCreated" in cached_value
        and datetime.fromisoformat(cached_value["dateCreated"])
        > datetime.fromisoformat("2024-03-15T18:19:53.758746")
    ):
        return cached_value["description"]

    new_description = get_description_from_content(resource)

    description_cache[resource_id] = {
        "description": new_description,
        "version": resource["version"],
        "dateCreated": current_time().isoformat(),
    }

    if new_description:
        print(f"updated description for {resource_id}")

    return new_description


def get_description_from_content(record: Dict[str, Any]):
    identifier = pick(["identifier", "value"], record)

    if not isinstance(identifier, int):
        return None

    content_raw = fetch_content(identifier)

    if not isinstance(content_raw, str):
        return None

    try:
        content = json.loads(content_raw)

        content_text = get_text(content)

        first_paragraph = content_text.split("\n", maxsplit=1)[0]

        if first_paragraph.isspace():
            return None

        return re.sub(" +", " ", first_paragraph)
    except json.JSONDecodeError:
        return None


def get_text(data) -> str:
    if isinstance(data, list):
        return "".join(get_text(child) for child in data)
    if isinstance(data, dict):
        get_text_from_dict(data)
    return ""


def get_text_from_dict(data):
    if "plugin" in data and data["plugin"] == "text" and "state" in data:
        return get_text(data["state"]) + "\n"
    if "type" in data and data["type"] == "h" and "children" in data:
        return get_text(data["children"]) + "\n"
    if "type" in data and data["type"] == "p" and "children" in data:
        return get_text(data["children"]) + " "
    if "type" in data and data["type"] == "math" and "src" in data:
        return "$" + data["src"] + "$"
    if "text" in data and isinstance(data["text"], str):
        return data["text"]
    return "".join(get_text(child) for child in data.values())


def load_description_cache_from_last_run():
    try:
        response = requests.get(
            "https://serlo.github.io/metadata-exports/description-cache.json",
            timeout=60,
        )

        return response.json()
    except (requests.exceptions.ReadTimeout, json.JSONDecodeError, TypeError):
        return {}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: download_metadata.py OUTPUT_FILENAME")
        sys.exit(1)

    main(sys.argv[1])
