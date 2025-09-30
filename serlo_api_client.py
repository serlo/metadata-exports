"""A client to send requests to the Serlo GraphQL API"""

import json
import os
import time

from typing import Dict, Any, Optional

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.exceptions import TransportError


def fetch_metadata(first=500, after=None) -> Dict[str, Any]:
    query = graphql(
        """
        query ($first: Int, $after: String) {
            metadata {
                resources(first: $first, after: $after) {
                    nodes
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                }
            }
        }
        """
    )

    params = {"first": first, "after": after}
    return execute(query, params)


def fetch_publisher() -> Dict[str, Any]:
    query = graphql(
        """
        query {
            metadata {
                publisher
            }
        }
        """
    )
    return execute(query)


def fetch_current_content(revision_id):
    query = graphql(
        """
        query ($id: Int) {
            uuid(id: $id) {
                ...on AbstractRevision {
                    content
                }
            }
        }
        """
    )
    result = execute(query, {"id": revision_id})

    if content_text := result.get("uuid", {}).get("content", None):
        try:
            return json.loads(content_text)
        except json.JSONDecodeError:
            pass
    return None


def execute(query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    api_url = "https://api.serlo.org/graphql"
    if os.getenv("USE_LOCAL_API"):
        api_url = "http://localhost:3001/graphql"
    transport = RequestsHTTPTransport(url=api_url)
    client = Client(transport=transport, fetch_schema_from_transport=True)
    graphql_query = gql(query)

    max_retries = 3
    last_exception = None

    for attempt in range(max_retries):
        try:
            return client.execute(graphql_query, variable_values=params)
        except TransportError as error:
            last_exception = error

            if attempt < max_retries - 1:
                sleep_time = 2**attempt * 10
                time.sleep(sleep_time)

    raise (
        last_exception
        if last_exception
        else Exception("max_retries must be at least 1")
    )


def graphql(query):
    """
    Marker to detect graphql statements in https://github.com/serlo/unused-graphql-properties.
    """
    return query
