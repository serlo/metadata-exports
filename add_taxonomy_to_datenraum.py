from datenraum import create_datenraum_session
from taxonomy_node_examples import BIG_DATA_TAXONOMY, GAME_THEORY_TAXONOMY


def main():
    session = create_datenraum_session()
    session.add_node(BIG_DATA_TAXONOMY, "Taxonomy")
    # session.update_node(BIG_DATA_TAXONOMY, "04141a5e-cc07-4508-af38-703b42680149", "Taxonomy")
    # session.delete_node("d8f481cb-3be6-4a91-9f5b-c22b35b918ae")
    session.add_node(GAME_THEORY_TAXONOMY, "Taxonomy")


main()
