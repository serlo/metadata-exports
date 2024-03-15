import sys
import json

from datenraum import create_datenraum_session
from utils import has_description


def main(metadata_file, nodes_file):
    with open(metadata_file, "r", encoding="utf-8") as input_file:
        resources = json.load(input_file)

    serlo_id_to_datenraum_id = {}

    with open(nodes_file, "r", encoding="utf-8") as input_file:
        nodes = json.load(input_file)

        for node in nodes:
            serlo_id_to_datenraum_id[node["externalId"]] = node["id"]

    session = create_datenraum_session()

    filtered_resources = [
        resource for resource in resources if has_description(resource)
    ]

    update_session(session, filtered_resources, serlo_id_to_datenraum_id)

    delete_deprecated_ids(session, filtered_resources, serlo_id_to_datenraum_id)


def update_session(session, resources, serlo_id_to_datenraum_id):
    for ressource in resources:
        ressource_id = ressource["id"]
        datenraum_id = serlo_id_to_datenraum_id.get(ressource["id"], None)

        if datenraum_id is None:
            print(f"INFO: Add new node for {ressource_id}")

            try:
                session.add_node(ressource)
            except AssertionError:
                datenraum_id = session.get_node_from_external_id(ressource["id"])

                if datenraum_id:
                    try:
                        session.update_node(ressource, datenraum_id)
                    except AssertionError:
                        print(
                            f"ERROR: {ressource_id} with node {datenraum_id} couldn't be updated"
                        )
                else:
                    print(f"ERROR: {ressource_id} couldn't be added")
        else:
            print(f"INFO: Update node {datenraum_id} for {ressource_id}")

            try:
                session.update_node(ressource, datenraum_id)
            except AssertionError:
                print(
                    f"ERROR: {ressource_id} with node {datenraum_id} couldn't be updated"
                )


def delete_deprecated_ids(session, resources, serlo_id_to_datenraum_id):
    stored_ids = set(serlo_id_to_datenraum_id.keys())
    current_ids = set(ressource["id"] for ressource in resources)

    for ressource_id in stored_ids - current_ids:
        datenraum_id = serlo_id_to_datenraum_id[ressource_id]

        print(f"INFO: Delete node {datenraum_id}")

        try:
            session.delete_node(datenraum_id)
        except AssertionError:
            print(f"ERROR: {datenraum_id} couldn't be deleted")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: update_datenraum.py SERLO_METADATA_FILE DATENRAUM_NODES_FILE")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
