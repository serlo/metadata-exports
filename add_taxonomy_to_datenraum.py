from datenraum import create_datenraum_session
from taxonomy_node_examples import BIG_DATA_TAXONOMY

def main():
    session = create_datenraum_session()
    session.add_node(BIG_DATA_TAXONOMY, "Taxonomy")


main()