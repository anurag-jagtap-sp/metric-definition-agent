import pytest
from requests import HTTPError, Response
from typer.testing import CliRunner

from metric_agent import cli
from metric_agent.config import Settings
from metric_agent.ingest import confluence


class FakeConfluence:
    """Answers the two v2 calls the space check makes."""

    def __init__(self, spaces=None, pages=None, error_status=None, html=False):
        self.spaces = spaces or {}
        self.pages = pages or {}
        self.error_status = error_status
        self.html = html
        self.calls = []

    def get(self, path, params=None, **kwargs):
        self.calls.append((path, params))
        if self.error_status:
            response = Response()
            response.status_code = self.error_status
            raise HTTPError(response=response)
        if self.html:
            return "<!DOCTYPE html><html></html>"
        if path == "wiki/api/v2/spaces":
            space = self.spaces.get(params["keys"])
            return {"results": [space] if space else []}
        space_id = path.split("/")[-2]
        return {"results": self.pages.get(space_id, [])}


IT_SPACE = {"id": "1", "key": "IT", "name": "IT"}


def test_readable_space_passes():
    client = FakeConfluence(spaces={"IT": IT_SPACE}, pages={"1": [{"id": "10"}]})
    [result] = confluence.check_spaces(client, ["IT"])
    assert result == confluence.SpaceCheck("IT", ok=True, name="IT", detail="readable")
    assert client.calls[1] == ("wiki/api/v2/spaces/1/pages", {"limit": 1})


def test_unknown_space_fails():
    [result] = confluence.check_spaces(FakeConfluence(), ["NOPE"])
    assert not result.ok
    assert "not found" in result.detail


def test_space_without_readable_pages_fails():
    client = FakeConfluence(spaces={"IT": IT_SPACE}, pages={"1": []})
    [result] = confluence.check_spaces(client, ["IT"])
    assert not result.ok
    assert result.detail == "no readable pages"


def test_http_error_is_reported():
    [result] = confluence.check_spaces(FakeConfluence(error_status=401), ["IT"])
    assert not result.ok
    assert result.detail == "HTTP 401"


def test_html_response_is_not_treated_as_success():
    [result] = confluence.check_spaces(FakeConfluence(html=True), ["IT"])
    assert not result.ok
    assert "CONFLUENCE_URL" in result.detail


@pytest.mark.parametrize(
    "url",
    [
        "https://example.atlassian.net/wiki",
        "https://example.atlassian.net/wiki/",
        "https://example.atlassian.net",
    ],
)
def test_site_root_strips_wiki(url):
    assert confluence.site_root(url) == "https://example.atlassian.net"


def configured_settings(**overrides):
    values = {
        "confluence_url": "https://example.atlassian.net/wiki",
        "confluence_username": "someone@example.com",
        "confluence_api_token": "secret-token",
        "confluence_spaces": ["IT", "BT"],
    } | overrides
    return Settings(_env_file=None, **values)


def test_cli_exits_nonzero_when_a_space_fails(monkeypatch):
    client = FakeConfluence(spaces={"IT": IT_SPACE}, pages={"1": [{"id": "10"}]})
    monkeypatch.setattr(cli, "get_settings", configured_settings)
    monkeypatch.setattr(confluence, "connect", lambda settings: client)
    result = CliRunner().invoke(cli.app, ["check-confluence"])
    assert result.exit_code == 1
    assert "OK   IT" in result.output
    assert "FAIL BT" in result.output


def test_cli_reports_missing_settings(monkeypatch):
    monkeypatch.setattr(cli, "get_settings", lambda: configured_settings(confluence_api_token=None))
    result = CliRunner().invoke(cli.app, ["check-confluence"])
    assert result.exit_code == 2
    assert "CONFLUENCE_API_TOKEN" in result.output


def test_check_config_never_prints_secret_values(monkeypatch):
    monkeypatch.setattr(cli, "get_settings", configured_settings)
    result = CliRunner().invoke(cli.app, ["check-config"])
    assert result.exit_code == 0
    assert "secret-token" not in result.output
    assert "someone@example.com" not in result.output
