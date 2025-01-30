#!/usr/bin/env python

from datenraum import create_datenraum_session


def main():
    session = create_datenraum_session().session
    session.update_token()
    token = session.token

    assert token and "access_token" in token

    print(token["access_token"])


if __name__ == "__main__":
    main()
