import json
import requests
from typing import Dict, Any

from datetime import datetime, timedelta, timezone
from load_json_ld import load_json_ld

DESCRIPTION_PATH = "public/description-cache.json"


def enhance_and_print_metadata(resources, enhanced_metadata_path: str):
    description_cache = load_description_cache_from_last_run()
    start_time = datetime.now(timezone.utc)

    for resource in resources:
        resource["description"] = get_description(
            resource, description_cache, datetime.now(timezone.utc) - start_time
        )

    with open(DESCRIPTION_PATH, "w", encoding="utf-8") as output_file:
        json.dump(description_cache, output_file)

    with open(enhanced_metadata_path, "w", encoding="utf-8") as output_file:
        json.dump(resources, output_file)


def get_description(
    resource: Dict[str, Any], description_cache: Dict[str, Any], time_passed: timedelta
):
    resource_id = resource["id"]
    if "description" in resource and isinstance(resource["description"], str):
        return resource["description"]

    cached_value = description_cache.get(resource_id, {})

    if cached_value.get("version", None) == resource["version"] and isinstance(
        cached_value.get("description", None), str
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
