#!/usr/bin/env python

import sys
from typing import Dict, Any

from serlo_api_client import fetch_metadata
from enhance_metadata import enhance_and_print_metadata


def main(output_filename: str):
    metadata = list(fetch_all_metadata())

    enhance_and_print_metadata(metadata, output_filename)


def fetch_all_metadata() -> Dict[str, Any]:
    after = None

    while True:
        response = fetch_metadata(first=500, after=after)
        resources = response["metadata"]["resources"]  # pylint: disable=E1136
        yield from resources["nodes"]

        if resources["pageInfo"]["hasNextPage"]:
            after = resources["pageInfo"]["endCursor"]
        else:
            break


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: download_metadata.py OUTPUT_FILENAME")
        sys.exit(1)

    main(sys.argv[1])
