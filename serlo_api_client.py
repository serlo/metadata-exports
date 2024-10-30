"""A client to send requests to the Serlo GraphQL API"""

from typing import Dict, Any, Optional

import os
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport


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


def execute(query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    api_url = "https://api.serlo.org/graphql"
    if os.getenv("USE_LOCAL_API"):
        api_url = "http://localhost:3001/graphql"
    transport = RequestsHTTPTransport(url=api_url)
    client = Client(transport=transport, fetch_schema_from_transport=True)
    graphql_query = gql(query)
    return client.execute(graphql_query, variable_values=params)


def graphql(query):
    """
    Marker to detect graphql statements in https://github.com/serlo/unused-graphql-properties.
    """
    return query
