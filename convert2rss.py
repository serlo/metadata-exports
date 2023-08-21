#!/usr/bin/env python

import json
import os
import re
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Callable

import requests

from serlo_api_client import fetch_publisher

GERMAN_LANGUAGE_CODE = "de"
VIDEO_RESOURCE_TYPE = "VideoObject"
MATHEMATICS_SUBJECT_ID = "http://w3id.org/kim/schulfaecher/s1017"
DESCRIPTION_CACHE_FILENAME = "description-cache.json"


def main(input_filename: str, output_filename: str):
    with open(input_filename, "r", encoding="utf-8") as input_file:
        metadata = json.load(input_file)

    description_cache = get_description_cache()

    with open(output_filename, "w", encoding="utf-8") as output_file:
        publisher = get_publisher()
        rss_export = generate_rss(
            metadata, publisher, description_cache, datetime.utcnow
        )
        print(rss_export, file=output_file)

    description_cache_target = os.path.join("public", DESCRIPTION_CACHE_FILENAME)
    with open(description_cache_target, "w", encoding="utf-8") as output_file:
        json.dump(description_cache, output_file)


def generate_rss(
    metadata: List[Dict[str, Any]],
    publisher: Dict[str, Any],
    description_cache: Dict[str, Any],
    get_current_time: Callable[[], datetime],
) -> str:
    published_date = get_current_time()
    serlo_url = escape(publisher["url"])
    serlo_description = escape(publisher["description"])
    serlo_name = escape(publisher["name"])

    rss = """<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:sdx="sodix.dtd" version="2.0">
<channel>
"""

    rss += f"  <title>{serlo_name}</title>\n"
    rss += f"  <link>{serlo_url}</link>\n"
    rss += f"  <description>{serlo_description}</description>\n"
    rss += "  <language>de-DE</language>\n"
    rss += f"  <copyright>{serlo_name}</copyright>\n"
    rss += f"  <pubDate>{format_date(published_date)}</pubDate>\n"

    for resource in filtered_data(metadata):
        rss += converted_resource(
            resource, publisher, description_cache, get_current_time() - published_date
        )

    rss += """</channel>
</rss>
"""

    return rss


def filtered_data(metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def is_in_german(res):
        return escape(res["inLanguage"][0]) == GERMAN_LANGUAGE_CODE

    def is_a_video_resource(res):
        return VIDEO_RESOURCE_TYPE in res["type"]

    def is_the_subject_math(res):
        return (
            "about" in res
            and len(res["about"]) == 1
            and res["about"][0]["id"] == MATHEMATICS_SUBJECT_ID
        )

    return [
        res
        for res in metadata
        if is_in_german(res)
        and not is_a_video_resource(res)
        and is_the_subject_math(res)
        and get_license_name(res["license"]["id"]) is not None
    ]


def converted_resource(
    resource: Dict[str, Any],
    publisher: Dict[str, Any],
    description_cache: Dict[str, Any],
    time_passed: timedelta,
) -> str:
    rss = "<item>\n"

    rss += f'  <title>{escape(resource["name"])}</title>\n'
    rss += f"  <sdx:language>{GERMAN_LANGUAGE_CODE}</sdx:language>\n"

    description = get_description(resource, description_cache, time_passed)

    if description:
        rss += f"  <description>{escape(description)}</description>\n"

    rss += f'  <link>{escape(resource["id"])}</link>\n'

    authors = ", ".join(escape(author["name"]) for author in resource["creator"])

    rss += f"  <author>{authors}</author>\n"
    rss += f'  <sdx:authorsWebsite>{escape(publisher["url"])}</sdx:authorsWebsite>\n'

    rss += f'  <sdx:producer>{escape(publisher["name"])}</sdx:producer>\n'
    rss += f'  <guid isPermaLink="true">{escape(resource["id"])}</guid>\n'

    date_created = format_date(datetime.fromisoformat(resource["dateCreated"]))
    rss += f"  <pubDate>{date_created}</pubDate>\n"

    rss += f'  <itunes:image href="{escape(publisher["logo"])}"></itunes:image>\n'

    rss += """  <sdx:userGroups>learner, teacher</sdx:userGroups>
  <sdx:educationalLevel>Sekundarstufe I, Sekundarstufe II</sdx:educationalLevel>
  <sdx:classLevel>5-13</sdx:classLevel>
"""

    rss += f"  <sdx:learnResourceType>{escape(get_resource_type(resource))}</sdx:learnResourceType>\n"

    rss += "  <sdx:schoolType>Realschule, Gymnasium, Mittel- / Hauptschule, Fachoberschule</sdx:schoolType>\n"

    # This need to be updated when we add additional subjects
    rss += "  <sdx:subject>380</sdx:subject>\n"
    rss += '  <category domain="eaf-classification-coded">380</category>\n'

    resource_license = resource["license"]["id"]
    license_name = get_license_name(resource_license)

    if license_name:
        rss += f"  <sdx:licenseName>{escape(license_name)}</sdx:licenseName>\n"
        rss += "  <sdx:licenseCountry>de</sdx:licenseCountry>\n"

        version = get_license_version(resource_license)

        if version:
            rss += f"  <sdx:licenseVersion>{escape(version)}</sdx:licenseVersion>\n"

    rss += """  <sdx:costs>FREE</sdx:costs>
</item>
"""

    return rss


def get_description(
    resource: Dict[str, Any],
    description_cache: Dict[str, Any],
    time_passed: timedelta,
):
    if "description" in resource and isinstance(resource["description"], str):
        return resource["description"]

    if time_passed > timedelta(minutes=30):
        return None

    cached_value = description_cache.get(resource["id"], {})

    if cached_value.get("version", None) == resource["version"] and isinstance(
        cached_value.get("description", None), str
    ):
        return cached_value["description"]

    new_description = load_description_from_website(resource)

    description_cache[resource["id"]] = {
        "description": new_description,
        "version": resource["version"],
    }

    return new_description


def load_description_from_website(resource: Dict[str, Any]):
    identifier = resource.get("identifier", {}).get("value", None)

    if not isinstance(identifier, int):
        return None

    try:
        response = requests.get(f"https://serlo.org/{identifier}", timeout=60)
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
        data = json.loads(match.strip())

        if "description" in data and isinstance(data["description"], str):
            return data["description"]
    except (TypeError, json.JSONDecodeError):
        pass

    return None


def get_license_version(resource_license):
    for version in ["4.0", "3.0", "2.5", "2.0"]:
        if version in resource_license:
            return version

    return None


def get_license_name(resource_license):
    if "/by/" in resource_license:
        return "CC BY"
    if "/zero/" in resource_license:
        return "CC0"
    if "/by-sa/" in resource_license:
        return "CC BY-SA"

    return None


def get_resource_type(resource):
    resource_types = resource["type"]

    if "Article" in resource_types:
        return "Arbeitsblatt, Text, Unterrichtsbaustein, Veranschaulichung, Webseite"
    if "Course" in resource_types:
        return "Kurs, Entdeckendes Lernen, Text, Unterrichtsbaustein, Veranschaulichung, Webseite"
    if "Quiz" in resource_types:
        return "Übung, Test/Prüfung, Lernkontrolle, Webseite"

    return "App, Interaktion, Entdeckendes Lernen, Webtool"


def escape(input_string):
    escape_dict = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&apos;"}

    for char, escaped_char in escape_dict.items():
        input_string = input_string.replace(char, escaped_char)

    return input_string


def format_date(date):
    return escape(date.strftime("%a, %d %b %Y %H:%M:%S +0000"))


def get_publisher() -> Dict[str, Any]:
    response = fetch_publisher()
    return response["metadata"]["publisher"]  # pylint: disable=E1136


def get_description_cache():
    try:
        response = requests.get(
            "https://serlo.github.io/metadata-exports/description-cache.json",
            timeout=60,
        )

        return response.json()
    except (requests.exceptions.ReadTimeout, json.JSONDecodeError, TypeError):
        return {}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: convert2rss.py INPUT_FILENAME OUTPUT_FILENAME")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
