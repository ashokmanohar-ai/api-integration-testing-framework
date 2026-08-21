"""Typed domain clients."""

from framework.clients.auth_client import AuthClient
from framework.clients.base_client import BaseApiClient
from framework.clients.customer_client import CustomerClient
from framework.clients.graphql_client import GraphQLClient
from framework.clients.order_client import OrderClient
from framework.clients.product_client import ProductClient

__all__ = [
    "AuthClient",
    "BaseApiClient",
    "CustomerClient",
    "GraphQLClient",
    "OrderClient",
    "ProductClient",
]
