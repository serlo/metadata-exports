"""A client to send requests to the Serlo GraphQL API"""

from typing import Dict, Any, Optional

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

from utils import pick


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


def fetch_publisher() -> Dict[str, Any]:
    query = """
        query {
            metadata {
                publisher
            }
        }
    """
    return execute(query)


def fetch_content(uuid):
    query = """
        query($id: Int) {
          uuid(id: $id) {
            ... on Article {
              currentRevision {
                content
              }
            }
            ... on Applet {
              currentRevision {
                content
              }
            }
            ... on Course {
              currentRevision {
                content
              }
            }
            ... on Event {
              currentRevision {
                content
              }
            }
            ... on Exercise {
              currentRevision {
                content
              }
            }
            ... on ExerciseGroup {
              currentRevision {
                content
              }
            }
            ... on Video {
              currentRevision {
                content
              }
            }
          }
        }"""

    result = execute(query, {"id": uuid})

    return pick(["uuid", "currentRevision", "content"], result)


def execute(query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    transport = RequestsHTTPTransport(url="https://api.serlo.org/graphql")
    client = Client(transport=transport, fetch_schema_from_transport=True)
    graphql_query = gql(query)
    return client.execute(graphql_query, variable_values=params)
