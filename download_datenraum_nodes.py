import json
import sys

from datenraum import create_datenraum_session


def main(output_file):
    session = create_datenraum_session()

    limit = 20
    offset = 0
    nodes = []

    while True:
        try:
            new_nodes = session.get_nodes(offset=offset, limit=limit)

            nodes.extend(new_nodes)

            print(f"Update: {len(nodes)} nodes downloaded")

            if len(new_nodes) == 0:
                break
        except json.JSONDecodeError:
            pass
        finally:
            offset += limit

    with open(output_file, "w", encoding="utf8") as new_file:
        json.dump(nodes, new_file, indent=2)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: download_datenraum_nodes.py OUTPUT_FILE")
        sys.exit(1)

    main(sys.argv[1])
