#!/usr/bin/env python

import json
import sys

from datenraum import get_current_environment, Environment
from serlo_api_client import fetch_entity_content, fetch_metadata


def main(output_filename: str):
    records = list(fetch_all_metadata())

    print(f"INFO: {len(records)} metadata records downloaded")

    if get_current_environment() == Environment.POSTDAM:
        for record in records:
            serlo_uuid = int(record["id"].replace("https://serlo.org/", ""))
            print(f"fetching content of {serlo_uuid}")
            response = fetch_entity_content(serlo_uuid)
            if "currentRevision" in response["uuid"] and (
                "content" in response["uuid"]["currentRevision"]
            ):
                record["content"] = response["uuid"]["currentRevision"]["content"]

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

    return ""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: download_metadata.py OUTPUT_FILENAME")
        sys.exit(1)

    main(sys.argv[1])
