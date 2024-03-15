import json

import requests

from utils import load_json_ld

SEARCH_URL = "https://repository.staging.openeduhub.net/edu-sharing/rest/search/v1/queries/-home-/mds_oeh/ngsearch/lrmi"


def main():
    lrmis = list(load_serlo_lrmis())

    print(f"Number of lrmis: {len(lrmis)}")
    keywords = {}

    for index, lrmi in enumerate(lrmis):
        if "keywords" in lrmi:
            uuid = get_uuid(lrmi.get("sourceUrl", None))

            if uuid:
                print(f"Store Uuid: {uuid}, index: {index}")

                keywords[uuid] = lrmi.get("keywords", [])
        else:
            print(lrmi["sourceUrl"], index)

    with open("keywords.json", "w", encoding="utf-8") as file:
        json.dump(keywords, file, indent=2)


def get_uuid(url):
    if url is None:
        return None

    data = load_json_ld(url.rstrip("?contentOnly"))

    if data is not None and "id" in data and isinstance(data["id"], str):
        return data["id"]

    return None


def load_serlo_lrmis():
    skip_count = 0

    while True:
        print(f"Loaded LRMIs: {skip_count}")

        results = fetch_lrmis(skip_count=skip_count, max_items=500)

        yield from results

        skip_count += len(results)

        if len(results) < 1:
            break


def fetch_lrmis(skip_count=0, max_items=1):
    response = requests.post(
        SEARCH_URL,
        params={
            "maxItems": max_items,
            "skipCount": skip_count,
            "propertyFilter": "-all-",
        },
        headers={"Content-Type": "application/json", "accept": "application/json"},
        json={
            "criteria": [
                {"property": "ccm:replicationsource", "values": ["serlo_spider"]}
            ]
        },
        timeout=60,
    )

    nodes = response.json()["nodes"]

    return [json.loads(node) for node in nodes]


if __name__ == "__main__":
    main()
