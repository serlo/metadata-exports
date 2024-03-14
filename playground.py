from datenraum import create_datenraum_session


def main():
    session = create_datenraum_session()
    edges = session.get_edges()["_embedded"]["edges"]
    print(edges)
    # Spieltheorie taxonomy_id "b8f566a7-5c2e-49e9-a029-b1f5e4eb9a18"
    # Big Data taxonomy_id "0119d2c8-bf46-46e6-928e-02138803d150"

    # node = session.get_node_by_id("0119d2c8-bf46-46e6-928e-02138803d150")
    # print(node)
    # for edge in edges:
    #    session.delete_edge(edge["edgeTypeId"], edge["tailNodeId"], edge["headNodeId"])

    # edge_types = session.get_edge_types()
    # print(edge_types)


main()
