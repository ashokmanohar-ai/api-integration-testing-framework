"""Header helpers that never expose token values."""

from framework.auth.token_provider import TokenProvider


def bearer_headers(provider: TokenProvider) -> dict[str, str]:
    return {"Authorization": f"Bearer {provider.get_token()}"}
