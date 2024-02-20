import time
import requests

from requests.auth import HTTPBasicAuth


class Datenraum:
    def __init__(self, client_id, client_secret):
        self.token = None
        self.client_id = client_id
        self.client_secret = client_secret

    def update_token(self):
        url = "https://aai.demo.meinbildungsraum.de/realms/nbp-aai/protocol/openid-connect/token"

        response = requests.post(
            url,
            auth=HTTPBasicAuth(self.client_id, self.client_secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials"},
        )

        if response.status_code != 200:
            raise Exception(response.text)

        self.token = response.json()
        self.token["created_at"] = current_time()


def current_time():
    return int(time.time())
