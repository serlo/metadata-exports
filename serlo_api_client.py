"""A client to send requests to the Serlo GraphQL API"""
from typing import Dict, Any

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport


def fetch_metadata(first=500, after=None) -> Dict[str, Any]:
    query = """
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

    params = {"first": first, "after": after}
    return execute(query, params)


def execute(query: str, params: Dict[str, Any]) -> Dict[str, Any]:
    transport = RequestsHTTPTransport(url="https://api.serlo.org/graphql")
    client = Client(transport=transport, fetch_schema_from_transport=True)
    graphql_query = gql(query)
    return client.execute(graphql_query, variable_values=params)
