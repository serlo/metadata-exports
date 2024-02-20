import sys
import json

from datenraum import create_datenraum_session


def main(metadata_file):
    with open(metadata_file, "r", encoding="utf-8") as input_file:
        ressources = json.load(input_file)

    session = create_datenraum_session()

    for ressource in ressources[:1000]:
        try:
            session.add_node(ressource)
        except AssertionError:
            # TODO: Update ressource
            print(ressource["id"])

    print(session.token["access_token"])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: update_datenraum.py SERLO_METADATA_FILE")
        sys.exit(1)

    main(sys.argv[1])
