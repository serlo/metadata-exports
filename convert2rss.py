#!/usr/bin/env python

import json
import sys
from datetime import datetime
from serlo_api_client import fetch_publisher


def main():
    json_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(json_file, "r", encoding="utf-8") as file:
        metadata = json.load(file)

    with open(output_file, "w", encoding="utf-8") as output_file:
        convert(output_file, metadata)


def convert(file, metadata):
    publisher = get_publisher()

    serlo_url = escape(publisher["url"])
    serlo_description = escape(publisher["description"])
    serlo_name = escape(publisher["name"])

    print('<?xml version="1.0" encoding="UTF-8"?>', file=file)
    print(
        '<rss xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:sdx="sodix.dtd" version="2.0">',
        file=file,
    )
    print("<channel>", file=file)
    print(f"  <title>{serlo_name}</title>", file=file)
    print(f"  <link>{serlo_url}</link>", file=file)
    print(f"  <description>{serlo_description}</description>", file=file)
    print("  <language>de-DE</language>", file=file)
    print(f"  <copyright>{serlo_name}</copyright>", file=file)
    print(f"  <pubDate>{format_date(datetime.utcnow())}</pubDate>", file=file)

    for resource in metadata:
        convert_resource(file, resource, publisher)

    print("</channel>", file=file)
    print("</rss>", file=file)


def convert_resource(file, resource, publisher):
    print("<item>", file=file)
    print(f'  <title>{escape(resource["name"])}</title>', file=file)
    print(
        f'  <sdx:language>{escape(resource["inLanguage"][0])}</sdx:language>', file=file
    )

    if "description" in resource and resource["description"]:
        print(
            f'  <description>{escape(resource["description"])}</description>', file=file
        )

    print(f'  <link>{escape(resource["id"])}</link>', file=file)

    authors = ", ".join(escape(author["name"]) for author in resource["creator"])

    print(f"  <author>{authors}</author>", file=file)
    print(
        f'  <sdx:authorsWebsite>{escape(publisher["url"])}</sdx:authorsWebsite>',
        file=file,
    )
    print(f'  <sdx:producer>{escape(publisher["name"])}</sdx:producer>', file=file)

    print(f'  <guid isPermaLink="true">{escape(resource["id"])}</guid>', file=file)

    date_created = format_date(datetime.fromisoformat(resource["dateCreated"]))
    print(f"  <pubDate>{date_created}</pubDate>", file=file)

    print("  <sdx:userGroups>learner, teacher</sdx:userGroups>", file=file)
    print(
        "  <sdx:educationalLevel>Sekundarstufe I, Sekundarstufe II</sdx:educationalLevel>",
        file=file,
    )
    print("  <sdx:classLevel>5-13</sdx:classLevel>", file=file)

    print(
        f"  <sdx:learnResourceType>{escape(get_resource_type(resource))}</sdx:learnResourceType>",
        file=file,
    )
    print(
        "  <sdx:schoolType>Realschule, Gymnasium, Mittel- / Hauptschule, Fachoberschule</sdx:schoolType>",
        file=file,
    )

    # TODO # pylint: disable=W0511
    # print('  <category domain="eaf-classification-coded">38002</category>', file=file)
    # print('  <sdx:subject>38002</sdx:subject>', file=file)

    resource_license = resource["license"]["id"]
    license_name = get_license_name(resource_license)

    if license_name:
        print(f"  <sdx:licenseName>{escape(license_name)}</sdx:licenseName>", file=file)
        print("  <sdx:licenseCountry>de</sdx:licenseCountry>", file=file)

        version = get_license_version(resource_license)

        if version:
            print(
                f"  <sdx:licenseVersion>{escape(version)}</sdx:licenseVersion>",
                file=file,
            )

    print("  <sdx:costs>FREE</sdx:costs>", file=file)
    print("</item>", file=file)


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
    if "/sa-by/" in resource_license:
        return "CC BY-SA"

    return None


def get_resource_type(resource):
    schema_type = resource["type"][1]

    if schema_type == "Article":
        return "Arbeitsblatt, Text, Unterrichtsbaustein, Veranschaulichung, Webseite"
    if schema_type == "Course":
        return "Kurs, Entdeckendes Lernen, Text, Unterrichtsbaustein, Veranschaulichung, Webseite"
    if schema_type == "Quiz":
        return "Übung, Test/Prüfung, Lernkontrolle, Webseite"
    if schema_type == "VideoObject":
        return "Video, Audiovisuelles Medium"

    return "App, Interaktion, Entdeckendes Lernen, Webtool"


def escape(input_string):
    escape_dict = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&apos;"}

    for char, escaped_char in escape_dict.items():
        input_string = input_string.replace(char, escaped_char)

    return input_string


def format_date(date):
    return escape(date.strftime("%a, %d %b %Y %H:%M:%S +0000"))


def get_publisher():
    response = fetch_publisher()
    return response["metadata"]["publisher"]  # pylint: disable=E1136


if __name__ == "__main__":
    main()
