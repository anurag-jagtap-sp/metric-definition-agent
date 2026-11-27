"""Confluence Cloud access for the in-scope spaces, via the REST v2 API."""

from dataclasses import dataclass
from typing import Any, Protocol

from atlassian import Confluence
from atlassian.errors import ApiError
from requests import HTTPError

from metric_agent.config import Settings

CONFLUENCE_SETTINGS = (
    "confluence_url",
    "confluence_username",
    "confluence_api_token",
    "confluence_spaces",
)

API_V2 = "wiki/api/v2"


class RestClient(Protocol):
    def get(self, path: str, params: dict[str, Any] | None = None, **kwargs: Any) -> Any: ...


@dataclass(frozen=True)
class SpaceCheck:
    key: str
    ok: bool
    name: str | None = None
    detail: str = ""


def site_root(url: str) -> str:
    """Cloud site root; the client adds the `/wiki/...` API paths itself."""
    return url.rstrip("/").removesuffix("/wiki")


def connect(settings: Settings) -> Confluence:
    settings.require(*CONFLUENCE_SETTINGS)
    assert settings.confluence_url and settings.confluence_api_token
    return Confluence(
        url=site_root(settings.confluence_url),
        username=settings.confluence_username,
        password=settings.confluence_api_token.get_secret_value(),
        cloud=True,
    )


def _results(response: Any) -> list[dict]:
    if not isinstance(response, dict) or not isinstance(response.get("results"), list):
        raise ValueError("unexpected response, not Confluence JSON (check CONFLUENCE_URL)")
    return response["results"]


def check_space(client: RestClient, key: str) -> SpaceCheck:
    """Confirm the space exists and at least one page in it is readable."""
    try:
        spaces = _results(client.get(f"{API_V2}/spaces", params={"keys": key, "limit": 1}))
        if not spaces:
            return SpaceCheck(key, ok=False, detail="space not found or not visible to this user")
        space = spaces[0]
        pages = _results(client.get(f"{API_V2}/spaces/{space['id']}/pages", params={"limit": 1}))
    except HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "error"
        return SpaceCheck(key, ok=False, detail=f"HTTP {status}")
    except (ApiError, ValueError) as exc:
        return SpaceCheck(key, ok=False, detail=str(exc))

    if not pages:
        return SpaceCheck(key, ok=False, name=space.get("name"), detail="no readable pages")
    return SpaceCheck(key, ok=True, name=space.get("name"), detail="readable")


def check_spaces(client: RestClient, space_keys: list[str]) -> list[SpaceCheck]:
    return [check_space(client, key) for key in space_keys]
