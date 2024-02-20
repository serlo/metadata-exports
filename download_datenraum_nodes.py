import json
import sys

from datenraum import create_datenraum_session


def main(output_file):
    session = create_datenraum_session()

    nodes = []

    while True:
        new_nodes = session.get_nodes(offset=len(nodes))

        nodes.extend(new_nodes)

        print(f"Update: {len(nodes)} nodes downloaded")

        if len(new_nodes) == 0:
            break

    with open(output_file, "w", encoding="utf8") as fd:
        json.dump(nodes, fd, indent=2)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: download_datenraum_nodes.py OUTPUT_FILE")
        sys.exit(1)

    main(sys.argv[1])
