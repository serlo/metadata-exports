import json
import time
import os
import requests

from requests.auth import HTTPBasicAuth


def create_datenraum_session():
    base_url = os.environ.get("DATENRAUM_BASE_URL")
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")

    return DatenraumSession(
        base_url, client_id, client_secret, "serlo", "Serlo Education e.V."
    )


class DatenraumSession:
    def __init__(self, base_url, client_id, client_secret, slug, name):
        self.token = None
        self.source_id = None
        self.base_url = base_url
        self.slug = slug
        self.client_id = client_id
        self.client_secret = client_secret
        self.name = name
        self.session = requests.Session()

    def add_node(self, node, node_type="LearningOpportunity"):
        data = self.convert_node_to_request_body(node, node_type)

        response = self.post_json(
            "/api/core/nodes", json=data, params={"metadataValidation": "Amb"}
        )

        assert response.status_code == 201

    def update_node(self, node, node_id, node_type="LearningOpportunity"):
        data = self.convert_node_to_request_body(node, node_type)

        response = self.put_json(
            f"/api/core/nodes/{node_id}",
            json=data,
            params={"metadataValidation": "Amb"},
        )

        assert response.status_code == 204

    def delete_node(self, node_id):
        self.delete(f"/api/core/nodes/{node_id}")

    def get_nodes(self, offset, limit=100):
        result = self.get_json(
            "/api/core/nodes",
            params={"sourceSlug": self.slug, "limit": limit, "offset": offset},
        )

        assert result is not None

        return result["_embedded"]["nodes"]

    def get_source_id(self):
        if self.source_id is None:
            self.source_id = self.register_and_get_source_id()

        assert isinstance(self.source_id, str)

        return self.source_id

    def register_and_get_source_id(self):
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

    def post_json(self, endpoint, json, params=None):
        return self.call("POST", endpoint, json=json, params=params)

    def put_json(self, endpoint, json, params=None):
        return self.call("PUT", endpoint, json=json, params=params)

    def get_json(self, endpoint, params=None):
        response = self.call(
            "GET", endpoint, params=params, headers={"Accept": "application/json"}
        )

        if response.status_code == 404:
            return None

        try:
            return response.json()
        except requests.exceptions.JSONDecodeError as error:
            print(response.status_code)
            print(response.text)

            raise error

    def delete(self, endpoint):
        response = self.call("DELETE", endpoint)

        assert response.status_code == 204

    def call(self, method, endpoint, headers=None, json=None, params=None):
        return self.send(
            requests.Request(
                method,
                self.base_url + endpoint,
                headers=headers,
                json=json,
                params=params,
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

    def convert_node_to_request_body(self, node, node_type="LearningOpportunity"):
        node["@context"] = [
            "https://w3id.org/kim/amb/context.jsonld",
            "https://schema.org",
            {"@language": "de"},
        ]

        assert "id" in node and isinstance(node["id"], str)
        assert "name" in node and isinstance(node["name"], str)

        data = {
            "title": node["name"],
            "sourceId": self.get_source_id(),
            "externalId": node["id"],
            "metadata": {"Amb": node},
            "nodeClass": node_type,
        }

        if "description" in node:
            data["description"] = node["description"]

        return data

    def is_token_expired(self):
        return self.token == None or self.token["expires_at"] >= current_time()


def current_time():
    return int(time.time())
