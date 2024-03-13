#!/usr/bin/env python

import json
import sys

from typing import Dict, Any
from datetime import datetime, timedelta, timezone

import requests

from load_json_ld import load_json_ld
from serlo_api_client import fetch_metadata


def main(output_filename: str):
    records = list(fetch_all_metadata())

    description_cache = load_description_cache_from_last_run()
    start_time = datetime.now(timezone.utc)

    for record in records:
        record["description"] = get_description(
            record, description_cache, datetime.now(timezone.utc) - start_time
        )

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


def get_description(
    resource: Dict[str, Any], description_cache: Dict[str, Any], time_passed: timedelta
):
    resource_id = resource["id"]
    if (
        "description" in resource
        and isinstance(resource["description"], str)
        and not resource["description"] == ""
        and not resource["description"].isspace()
    ):
        return resource["description"]

    cached_value = description_cache.get(resource_id, {})

    if (
        cached_value.get("version", None) == resource["version"]
        and isinstance(cached_value.get("description", None), str)
        and not cached_value["description"] == ""
        and not cached_value["description"].isspace()
    ):
        return cached_value["description"]

    if time_passed > timedelta(minutes=20):
        return None

    new_description = load_description_from_website(resource)

    description_cache[resource_id] = {
        "description": new_description,
        "version": resource["version"],
    }

    if new_description:
        print(f"updated description for {resource_id}")

    return new_description


def load_description_from_website(resource: Dict[str, Any]):
    identifier = resource.get("identifier", {}).get("value", None)

    if not isinstance(identifier, int):
        return None

    data = load_json_ld(f"https://serlo.org/{identifier}")

    if (
        data is not None
        and "description" in data
        and isinstance(data["description"], str)
        and not data["description"] == ""
        and not data["description"].isspace()
    ):
        return data["description"]

    return None


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
