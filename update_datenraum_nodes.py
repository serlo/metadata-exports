import gzip
import json
import sys
import time

from example_taxonomies import taxonomies
from datenraum import (
    create_datenraum_session,
    PotsdamEnvironment,
    current_time,
    get_current_environment,
)
from serlo_api_client import fetch_current_content
from utils import has_description, pick

# See https://github.com/serlo/evaluations/blob/main/src/2025/2025-01-28-cache-current-revisions.ipynb
# for the generation of this file
CACHED_CONTENT_FILE = "cache/current-content.json.gz"
MAX_CONTENT_DOWNLOAD_TIME = 20 * 60


def main(metadata_file, nodes_file):
    with open(metadata_file, "r", encoding="utf-8") as input_file:
        records = json.load(input_file)

    datenraum_nodes = {}

    with open(nodes_file, "r", encoding="utf-8") as input_file:
        nodes = json.load(input_file)

        for node in nodes:
            datenraum_nodes[node["externalId"]] = node

    env = get_current_environment()
    session = create_datenraum_session()

    if isinstance(env, PotsdamEnvironment):
        records = add_content_to_records(records)

        for record in records:
            if "description" not in record:
                record["description"] = record.get("name", None)

    filtered_records = [record for record in records if has_description(record)]

    if isinstance(env, PotsdamEnvironment):
        records = [
            record
            for record in records
            if "content" in record
            and isinstance(record["content"], dict)
            and isinstance(record["content"]["document"], dict)
            and "plugin" in record["content"]["document"]
            and record["content"]["document"]["plugin"]
            in ["article", "course", "exercise", "exerciseGroup"]
            and "description" in record
            and record["description"]
        ]
    else:
        records = filtered_records + taxonomies

    if isinstance(env, PotsdamEnvironment):
        update_session_potsdam(session, records)
    else:
        update_session(session, records, datenraum_nodes)

    delete_deprecated_ids(session, records, datenraum_nodes)


def add_content_to_records(records):
    print("INFO: Load cached content")

    with gzip.open(CACHED_CONTENT_FILE, "rt", encoding="utf-8") as gzip_file:
        cached_content = json.load(gzip_file)

    start_time = current_time()

    print("INFO: Start content download")
    for record in records:
        if (current_time() - start_time) > MAX_CONTENT_DOWNLOAD_TIME:
            print("INFO: Stop content download due to time limit")
            break

        if version_url := record.get("version", {}).get("id"):
            current_revision_id = version_url.split("/")[-1]

            if current_revision_id in cached_content:
                content = cached_content[current_revision_id]
            else:
                print(f"INFO: Download content for {current_revision_id}")

                content = fetch_current_content(int(current_revision_id))
                cached_content[current_revision_id] = content

                # Do not hammer the API
                time.sleep(0.1)

            if content is not None:
                record["content"] = content
        else:
            print(f"INFO: No version URL found for {record['id']}")

    print("INFO: Save cached content")

    with gzip.open(CACHED_CONTENT_FILE, "wt", encoding="utf-8") as gzip_file:
        json.dump(cached_content, gzip_file)

    print("INFO: Finish content download")

    return records


def update_session_potsdam(session, records):
    for record in records:
        record_id = record["id"]

        print(f"INFO: Create/update node {record_id}")

        session.create_or_update_node(record)


def update_session(session, records, datenraum_nodes):
    for record in records:
        record_id = record["id"]
        datenraum_node = datenraum_nodes.get(record["id"], None)

        datenraum_amb = pick(["metadata", "Amb"], datenraum_node)

        if datenraum_node is None or datenraum_amb is None:
            print(f"INFO: Add new node for {record_id}")

            result = session.add_node(record)

            if not result:
                external_node = session.get_node_from_external_id(record["id"])
                datenraum_node_id = (
                    external_node["id"] if external_node is not None else None
                )

                if datenraum_node_id is not None:
                    print(f"INFO: Lets update node {record_id} instead")
                    print()
                    session.update_node(record, datenraum_node_id)
        else:
            # We change the `@context` before update => thus we need to
            # rechange it before checking whether an update is necessary
            datenraum_amb["@context"] = record["@context"]

            # Ignore creation and modified time of metadata
            try:
                datenraum_amb["mainEntityOfPage"][0]["dateCreated"] = record[
                    "mainEntityOfPage"
                ][0]["dateCreated"]
                datenraum_amb["mainEntityOfPage"][0]["dateModified"] = record[
                    "mainEntityOfPage"
                ][0]["dateModified"]
            except (KeyError, IndexError):
                pass

            if datenraum_amb != record:
                datenraum_node_id = datenraum_node["id"]
                print(f"INFO: Update node {datenraum_node_id} for {record_id}")

                session.update_node(record, datenraum_node_id)


def delete_deprecated_ids(session, records, datenraum_nodes):
    stored_serlo_org_ids = set(node["externalId"] for node in datenraum_nodes.values())
    current_ids = set(record["id"] for record in records)

    for ressource_id in stored_serlo_org_ids - current_ids:
        datenraum_id = datenraum_nodes[ressource_id]["id"]

        print(f"INFO: Delete node {datenraum_id}")

        session.delete_node(datenraum_id)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: update_datenraum.py SERLO_METADATA_FILE DATENRAUM_NODES_FILE")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
