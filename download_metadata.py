#!/usr/bin/env python

import json
import sys
import requests


def main():
    metadata = list(fetch_all_metadata())

    with open(sys.argv[1], "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)


def fetch_all_metadata():
    after = None

    while True:
        response = fetch_metadata(first=500, after=after)

        if "data" not in response or "metadata" not in response["data"]:
            break

        resources = response["data"]["metadata"]["resources"]

        yield from resources["nodes"]

        if resources["pageInfo"]["hasNextPage"]:
            after = resources["pageInfo"]["endCursor"]
        else:
            break


def fetch_metadata(first=500, after=None):
    req = requests.post(
        "https://api.serlo.org/graphql",
        headers={
            "Content-Type": "application/json",
        },
        json={
            "query": """
                query($first: Int, $after: String) {
                    metadata {
                        resources(first: $first, after: $after) {
                            nodes
                            pageInfo {
                                hasNextPage
                                endCursor
                            }
                        }
                    }
                }
            """,
            "variables": {"first": first, "after": after},
        },
        timeout=60
    )

    return req.json()


if __name__ == "__main__":
    main()
