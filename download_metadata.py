#!/usr/bin/env python

import json
import requests
import sys


def main():
    metadata = list(fetch_all_metadata())

    with open(sys.argv[1], "w") as fd:
        json.dump(metadata, fd, indent=2)


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
    )

    return req.json()


if __name__ == "__main__":
    main()
