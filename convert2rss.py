#!/usr/bin/env python

import json
import sys
from datetime import datetime
from typing import Dict, Any, List, Callable

from serlo_api_client import fetch_publisher
from utils import has_description

GERMAN_LANGUAGE_CODE = "de"
VIDEO_RESOURCE_TYPE = "VideoObject"
QUIZ_RESOURCE_TYPE = "Quiz"
MATHEMATICS_SUBJECT_ID = "http://w3id.org/kim/schulfaecher/s1017"


def main(input_filename: str, output_filename: str):
    with open(input_filename, "r", encoding="utf-8") as input_file:
        metadata = json.load(input_file)

    with open("keywords.json", "r", encoding="utf-8") as input_file:
        keywords = json.load(input_file)

    with open(output_filename, "w", encoding="utf-8") as output_file:
        publisher = get_publisher()
        rss_export = generate_rss(metadata, publisher, datetime.utcnow, keywords)
        print(rss_export, file=output_file)


def generate_rss(
    metadata: List[Dict[str, Any]],
    publisher: Dict[str, Any],
    get_current_time: Callable[[], datetime],
    keywords,
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
            resource,
            publisher,
            keywords,
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

    def is_a_quiz_resource(res):
        return QUIZ_RESOURCE_TYPE in res["type"]

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
        and has_description(res)
        and not is_a_video_resource(res)
        and not "Course" in res["type"]
        and not is_a_quiz_resource(res)
        and is_the_subject_math(res)
        and get_license_name(res["license"]["id"]) is not None
    ]


def converted_resource(
    resource: Dict[str, Any],
    publisher: Dict[str, Any],
    keywords,
) -> str:
    rss = "<item>\n"

    rss += f'  <title>{escape(resource["name"])}</title>\n'
    rss += f"  <sdx:language>{GERMAN_LANGUAGE_CODE}</sdx:language>\n"

    if has_description(resource):
        description = resource["description"]
        rss += f"  <description>{escape(description)}</description>\n"

    resource_keywords = keywords.get(resource["id"], [])

    if len(resource_keywords) > 0:
        rss += f'  <itunes:keywords>{", ".join(resource_keywords)}</itunes:keywords>\n'

    rss += f'  <link>{escape(resource["id"])}</link>\n'

    authors = ", ".join(escape(author["name"]) for author in resource["creator"])

    rss += f"  <author>{authors}</author>\n"
    rss += f'  <sdx:authorsWebsite>{escape(publisher["url"])}</sdx:authorsWebsite>\n'

    rss += f'  <sdx:producer>{escape(publisher["name"])}</sdx:producer>\n'
    rss += f'  <guid isPermaLink="true">{escape(resource["id"])}</guid>\n'

    date_created = format_date(datetime.fromisoformat(resource["dateCreated"]))
    rss += f"  <pubDate>{date_created}</pubDate>\n"

    rss += '  <itunes:image href="https://de.serlo.org/_assets/img/meta/mathe.png"></itunes:image>\n'

    rss += """  <sdx:userGroups>learner, teacher</sdx:userGroups>
  <sdx:educationalLevel>Sekundarstufe I, Sekundarstufe II</sdx:educationalLevel>
  <sdx:classLevel>5-13</sdx:classLevel>
"""

    rss += f"  <sdx:learnResourceType>{escape(get_resource_type(resource))}</sdx:learnResourceType>\n"

    rss += "  <sdx:schoolType>Realschule, Gymnasium, Mittel- / Hauptschule, Fachoberschule</sdx:schoolType>\n"

    # This need to be updated when we add additional subjects
    rss += "  <sdx:subject>380</sdx:subject>\n"

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


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: convert2rss.py INPUT_FILENAME OUTPUT_FILENAME")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
