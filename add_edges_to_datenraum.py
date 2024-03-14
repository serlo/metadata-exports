import json
from datenraum import create_datenraum_session


def process_node(session, node, taxonomy):
    if "externalId" not in node or "metadata" not in node:
        return

    metadata = node["metadata"]
    if "Amb" not in metadata or "isPartOf" not in metadata["Amb"]:
        return

    for part in metadata["Amb"]["isPartOf"]:
        if part.get("id") == taxonomy:
            print(node["id"])
            # for taxonomy we need "id": "b8f566a7-5c2e-49e9-a029-b1f5e4eb9a18" or "sourceId"?
            session.add_edge(
                "4ea05b3f-7780-44b5-84e2-2edcdbae7ae0",
                "b8f566a7-5c2e-49e9-a029-b1f5e4eb9a18",
                node["id"],
            )


def main():
    session = create_datenraum_session()

    # delete edge types added for testing
    # session.delete_edge_type("1887db3f-18cd-456b-97d5-a5cd6681198e")
    # session.delete_edge_type("fe12c38e-d18a-4850-badf-c6f74d56b6dd")
    # session.delete_edge_type("0e6a0f8d-bf1a-452a-9de7-730c476c3999")

    # the edge type to be used
    # session.add_edge_type("content -> taxonomy", "points to a content node to its taxonomy node", "isPartOf")

    with open("datenraum_nodes_0314.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    # iterate over all ids of nodes part of the two taxonomies
    for taxonomy in ["https://serlo.org/155948", "https://serlo.org/192971"]:
        for node in data:
            process_node(session, node, taxonomy)


main()
