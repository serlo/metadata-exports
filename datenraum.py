import time
import requests

from requests.auth import HTTPBasicAuth


class Datenraum:
    def __init__(self, base_url, client_id, client_secret, slug, name):
        self.token = None
        self.source = None
        self.base_url = base_url
        self.slug = slug
        self.client_id = client_id
        self.client_secret = client_secret
        self.name = name
        self.session = requests.Session()

    def get_source_id(self):
        source = self.get_source()

        if source is None:
            self.register_source()
            source = self.get_source()

        assert source is not None

        return source["id"]

    def register_source(self):
        response = self.post_json(
            "/api/core/sources",
            {"organization": self.name, "name": self.name, "slug": self.slug},
        )

        assert response.status_code == 201

    def get_source(self):
        return self.get_json(f"/api/core/sources/slug/{self.slug}")

    def post_json(self, endpoint, json):
        return self.call("POST", endpoint, json=json)

    def get_json(self, endpoint):
        response = self.call("GET", endpoint, headers={"Accept": "application/json"})

        if response.status_code == 404:
            return None

        return response.json()

    def call(self, method, endpoint, headers=None, json=None):
        return self.send(
            requests.Request(
                method, self.base_url + endpoint, headers=headers, json=json
            )
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
