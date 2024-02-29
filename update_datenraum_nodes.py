import sys
import json
from datetime import datetime

from datenraum import create_datenraum_session
from convert2rss import get_description

DESCRIPTION_PATH = "public/description-cache.json"


def main(metadata_file, nodes_file):

    published_date = datetime.utcnow()

    with open(metadata_file, "r", encoding="utf-8") as input_file:
        ressources = json.load(input_file)

    serlo_id_to_datenraum_id = {}

    with open(nodes_file, "r", encoding="utf-8") as input_file:
        nodes = json.load(input_file)

        for node in nodes:
            serlo_id_to_datenraum_id[node["externalId"]] = node["id"]

    with open(DESCRIPTION_PATH, "r", encoding="utf-8") as input_file:
        description_cache = json.load(input_file)

    session = create_datenraum_session()

    update_session(
        session, ressources, serlo_id_to_datenraum_id, description_cache, published_date
    )

    delete_deprecated_ids(session, serlo_id_to_datenraum_id, ressources)

    with open(DESCRIPTION_PATH, "w", encoding="utf-8") as output_file:
        json.dump(description_cache, output_file)


def update_session(
    session, resources, serlo_id_to_datenraum_id, description_cache, published_date
):
    for ressource in resources:
        ressource_id = ressource["id"]
        datenraum_id = serlo_id_to_datenraum_id.get(ressource["id"], None)

        if (
            "descriptopn" not in ressource
            or not ressource["description"]
            or ressource["description"].isspace()
        ):
            ressource["description"] = get_description(
                ressource, description_cache, datetime.utcnow() - published_date
            )
            print(f"description updated for {ressource_id} with node id {datenraum_id}")

        if datenraum_id is None:
            print(f"INFO: Add new node for {ressource_id}")

            try:
                session.add_node(ressource)
            except AssertionError:
                print(f"ERROR: {ressource_id} couldn't be added")
        else:
            print(f"INFO: Update node {datenraum_id} for {ressource_id}")

            try:
                session.update_node(ressource, datenraum_id)
            except AssertionError:
                print(
                    f"ERROR: {ressource_id} with node {datenraum_id} couldn't be updated"
                )


def delete_deprecated_ids(session, serlo_id_to_datenraum_id, resources):
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
