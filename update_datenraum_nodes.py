import sys
import json

from datenraum import create_datenraum_session
from utils import has_description


def main(metadata_file, nodes_file):
    with open(metadata_file, "r", encoding="utf-8") as input_file:
        records = json.load(input_file)

    serlo_id_to_datenraum_id = {}

    with open(nodes_file, "r", encoding="utf-8") as input_file:
        nodes = json.load(input_file)

        for node in nodes:
            serlo_id_to_datenraum_id[node["externalId"]] = node["id"]

    session = create_datenraum_session()

    filtered_records = [record for record in records if has_description(record)]

    update_session(session, filtered_records, serlo_id_to_datenraum_id)

    delete_deprecated_ids(session, filtered_records, serlo_id_to_datenraum_id)


def update_session(session, records, serlo_id_to_datenraum_id):
    for record in records:
        record_id = record["id"]
        datenraum_id = serlo_id_to_datenraum_id.get(record["id"], None)

        if datenraum_id is None:
            print(f"INFO: Add new node for {record_id}")

            result = session.add_node(record)

            if not result:
                datenraum_id = session.get_node_from_external_id(record["id"])["id"]

                if datenraum_id:
                    session.update_node(record, datenraum_id)
        else:
            print(f"INFO: Update node {datenraum_id} for {record_id}")

            session.update_node(record, datenraum_id)


def delete_deprecated_ids(session, records, serlo_id_to_datenraum_id):
    stored_ids = set(serlo_id_to_datenraum_id.keys())
    current_ids = set(record["id"] for record in records)

    for ressource_id in stored_ids - current_ids:
        datenraum_id = serlo_id_to_datenraum_id[ressource_id]

        print(f"INFO: Delete node {datenraum_id}")

        session.delete_node(datenraum_id)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: update_datenraum.py SERLO_METADATA_FILE DATENRAUM_NODES_FILE")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
