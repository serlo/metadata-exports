import time
import os
import sys

from enum import Enum
from dataclasses import dataclass

import requests

from requests.auth import HTTPBasicAuth


def create_datenraum_session():
    env = get_current_environment()
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")

    assert client_id is not None
    assert client_secret is not None

    session = Session(env, Credentials(client_id, client_secret))
    client = Client(session)

    return client.create_source(
        slug="serlo", name="Serlo Education e.V.", organization="Serlo Education e.V."
    )


class Source:
    """
    Represents a source in the Datenraum for creating, updating, or deleting nodes or edges
    """

    def __init__(self, session, source_id):
        self.session = session
        self.source_id = source_id

    def add_node(self, node, node_type="LearningOpportunity", log_error=True):
        data = self.convert_node_to_request_body(node, node_type)

        response = self.session.post_json(
            "/api/core/nodes", json=data, params={"metadataValidation": "Amb"}
        )

        is_success = response.status_code == 201

        if not is_success and log_error:
            log_response(response, "Could not add " + node["id"])

        return is_success

    def update_node(
        self, node, node_id, node_type="LearningOpportunity", log_error=True
    ):
        data = self.convert_node_to_request_body(node, node_type)

        response = self.session.put_json(
            f"/api/core/nodes/{node_id}",
            json=data,
            params={"metadataValidation": "Amb"},
        )

        is_success = response.status_code == 204

        if not is_success and log_error:
            log_response(response, "Could not update " + node["id"] + " for " + node_id)

        return is_success

    def delete_node(self, node_id, log_error=True):
        response = self.session.delete(f"/api/core/nodes/{node_id}")

        is_success = response.status_code == 204

        if not is_success and log_error:
            log_response(response, "Could not delete " + node_id)

        return is_success

    def get_nodes(self, offset, limit=100):
        result = self.session.get_json(
            "/api/core/nodes",
            params={"sourceId": self.source_id, "limit": limit, "offset": offset},
        )

        assert result is not None

        return result["_embedded"]["nodes"]

    def get_node_from_external_id(self, external_id):
        return self.session.get_json(
            f"/api/core/nodes/external/{self.source_id}",
            params={"externalId": external_id},
        )

    def get_nodes_by_taxonomy(self, taxonomy_id, limit=100):
        result = self.session.get_json(
            "/api/core/nodes",
            params={
                "sourceId": self.source_id,
                "limit": limit,
                "referencedByTail": taxonomy_id,
            },
        )

        assert result is not None

        return result["_embedded"]["nodes"]

    def get_node_by_id(self, node_id):
        result = self.session.get_json(f"/api/core/nodes/{node_id}")

        assert result is not None

        return result

    def convert_node_to_request_body(self, node, node_type="LearningOpportunity"):
        language = node.get("inLanguage", [])[:1]

        node["@context"] = [
            "https://w3id.org/kim/amb/context.jsonld",
            "https://schema.org",
            {"@language": language[0] if language else "de"},
        ]

        assert "id" in node and isinstance(node["id"], str)
        assert "name" in node and isinstance(node["name"], str)

        data = {
            "title": node["name"],
            "sourceId": self.source_id,
            "externalId": node["id"],
            "metadata": {"Amb": node},
            "nodeClass": node_type,
        }

        if "description" in node:
            data["description"] = node["description"]

        return data

    def add_edge_type(self, name, description, slug):
        response = self.session.post_json(
            "/api/core/edge-types",
            json={
                "name": name,
                "description": description,
                "slug": slug,
            },
        )
        assert response.status_code == 201

    def get_edge_types(self):
        return self.session.get_json("/api/core/edge-types")

    def add_edge(self, edge_type_id, tail_node_id, head_node_id):
        response = self.session.put_json(
            f"/api/core/edges/{edge_type_id}/{tail_node_id}/{head_node_id}",
            json={
                "metadata": {
                    "isAiGenerated": False,
                }
            },
        )

        assert response.status_code in (201, 204)

    def delete_edge_type(self, edge_type_id):
        self.session.delete(f"/api/core/edge-types/{edge_type_id}")

    def get_edges(self):
        response = self.session.get_json("/api/core/edges")
        return response

    def delete_edge(self, edge_type_id, tail_node_id, head_node_id):
        response = self.session.delete(
            f"/api/core/edges/{edge_type_id}/{tail_node_id}/{head_node_id}"
        )
        assert response.status_code in (201, 204)


class Client:
    """
    A client for accessing the Datenraum.
    """

    def __init__(self, session):
        self.session = session

    def create_source(self, slug, name, organization):
        source = self.get_source(slug)

        if source is None:
            self.register_source(slug, name, organization)
            source = self.get_source(slug)

        assert source is not None

        if name not in source or organization not in source:
            print(source)

        if (
            "name" not in source
            or "organization" not in source
            or name != source["name"]
            or organization != source["organization"]
        ):
            self.update_source(source["id"], name, organization)

        return Source(self.session, source["id"])

    def register_source(self, slug, name, organization):
        response = self.session.post_json(
            "/api/core/sources",
            {"organization": organization, "name": name, "slug": slug},
        )

        assert response.status_code == 201

    def update_source(self, source_id, name, organization):
        response = self.session.patch_json(
            f"/api/core/sources/{source_id}",
            {"organization": organization, "name": name},
        )

        assert response.status_code == 204

    def get_source(self, slug):
        return self.session.get_json(f"/api/core/sources/slug/{slug}")


class Session:
    """
    Class for handling API calls to the Datenraums. Manages authentication token creation and renewal.
    """

    def __init__(self, env, credentials):
        self.token = None
        self.env = env
        self.credentials = credentials
        self.session = requests.Session()

    def post_json(self, endpoint, json, params=None):
        return self.send(
            requests.Request("POST", self.base_url + endpoint, json=json, params=params)
        )

    def put_json(self, endpoint, json, params=None):
        return self.send(
            requests.Request("PUT", self.base_url + endpoint, json=json, params=params)
        )

    def patch_json(self, endpoint, json):
        return self.send(
            requests.Request(
                "PATCH",
                self.base_url + endpoint,
                json=json,
                headers={"Content-Type": "application/json-patch+json"},
            )
        )

    def get_json(self, endpoint, params=None):
        response = self.send(
            requests.Request(
                "GET",
                self.base_url + endpoint,
                params=params,
                headers={"Accept": "application/json"},
            )
        )

        if response.status_code == 404:
            return None

        try:
            return response.json()
        except requests.exceptions.RequestException as error:
            sys.stderr.write(str(response.status_code) + "\n")
            sys.stderr.write(response.text + "\n")

            raise error

    def delete(self, endpoint):
        return self.send(requests.Request("DELETE", self.base_url + endpoint))

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
        response = self.session.post(
            self.authentication_url,
            auth=HTTPBasicAuth(self.credentials.identifier, self.credentials.secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials"},
        )

        if response.status_code != 200:
            raise IOError(response.text)

        self.token = response.json()
        self.token["expires_at"] = current_time() + self.token["expires_in"] - 20

    def is_token_expired(self):
        return self.token is None or self.token["expires_at"] <= current_time()

    @property
    def base_url(self):
        return (
            "https://dam.demo.meinbildungsraum.de/datenraum"
            if self.env == Environment.DEMO
            else "https://dam-dev.nbpdev.de/datenraum"
        )

    @property
    def authentication_url(self):
        return (
            "https://aai.demo.meinbildungsraum.de/realms/nbp-aai/protocol/openid-connect/token"
            if self.env == Environment.DEMO
            else "https://aai-dev.nbpdev.de/realms/nbp-aai/protocol/openid-connect/token"
        )


@dataclass
class Credentials:
    """
    Data class for storing client credentials.
    """

    identifier: str
    secret: str


class Environment(Enum):
    """
    Enum representing different environments.
    """

    DEV = 1
    DEMO = 2


def get_current_environment():
    env = os.environ.get("DATENRAUM_ENVIRONMENT")
    env = env.strip().lower() if env is not None else None

    if env == "demo":
        return Environment.DEMO
    if env == "dev":
        return Environment.DEV

    raise ValueError("Illegal state: DATENRAUM_ENVIRONMENT must be defined")


def current_time():
    return int(time.time())


def log_response(response, message):
    print(f"ERROR: {message}")
    print("Status code: ", response.status_code)
    print("Response text: ", response.text)
    print()
