import sys
import json

from datenraum import create_datenraum_session


def main(metadata_file, nodes_file):
    with open(metadata_file, "r", encoding="utf-8") as input_file:
        ressources = json.load(input_file)

    datenraum_id_to_serlo_id = {}

    with open(nodes_file, "r", encoding="utf-8") as input_file:
        nodes = json.load(input_file)

        for node in nodes:
            datenraum_id_to_serlo_id[node["externalId"]] = node["id"]

    session = create_datenraum_session()

    for ressource in ressources[:1010]:
        ressource_id = ressource["id"]
        datenraum_id = datenraum_id_to_serlo_id.get(ressource["id"], None)

        if datenraum_id is None:
            print(f"INFO: Add new node for {ressource_id}")

            # Add a new node
            try:
                session.add_node(ressource)
            except AssertionError:
                print(f"ERROR: {ressource_id} couldn't be added")
        else:
            pass


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: update_datenraum.py SERLO_METADATA_FILE DATENRAUM_NODES_FILE")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
