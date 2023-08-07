#!/usr/bin/env python

import json
import sys
from typing import Dict, Any

from serlo_api_client import fetch_metadata


def main():
    metadata = list(fetch_all_metadata())

    with open(sys.argv[1], "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)


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
    main()
