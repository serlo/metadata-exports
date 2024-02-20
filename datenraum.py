import time
import requests

from requests.auth import HTTPBasicAuth


class Datenraum:
    def __init__(self, base_url, client_id, client_secret, slug):
        self.token = None
        self.base_url = base_url
        self.slug = slug
        self.client_id = client_id
        self.client_secret = client_secret
        self.session = requests.Session()

    def get_source(self):
        return self.get_json(f"/api/core/sources/slug/{self.slug}")

    def get_json(self, endpoint):
        response = self.call("GET", endpoint, headers={"Accept": "application/json"})

        if response.status_code == 404:
            return None

        return response.json()

    def call(self, method, endpoint, headers=None):
        return self.send(
            requests.Request(method, self.base_url + endpoint, headers=headers)
        )

    def send(self, req, no_retries=0):
        if self.is_token_expired():
            self.update_token()

        assert self.token is not None

        access_token = self.token["access_token"]
        req.headers.update({"Authorization": f"Bearer {access_token}"})

        response = self.session.send(req.prepare())

        if response.status_code == 401 and no_retries == 0:
            # Authorization has failed -> retry the call with an updated token once
            self.update_token()

            return self.send(req, no_retries=no_retries + 1)

        return response

    def update_token(self):
        url = "https://aai.demo.meinbildungsraum.de/realms/nbp-aai/protocol/openid-connect/token"

        response = self.session.post(
            url,
            auth=HTTPBasicAuth(self.client_id, self.client_secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials"},
        )

        if response.status_code != 200:
            raise Exception(response.text)

        self.token = response.json()
        self.token["expires_at"] = current_time() + self.token["expires_in"] - 20

    def is_token_expired(self):
        return self.token == None or self.token["expires_at"] >= current_time()


def current_time():
    return int(time.time())
