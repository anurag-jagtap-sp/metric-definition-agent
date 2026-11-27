import pytest

from metric_agent.config import ConfigError, Settings

CONFLUENCE_ENV = {
    "CONFLUENCE_URL": "https://example.atlassian.net/wiki",
    "CONFLUENCE_USERNAME": "someone@example.com",
    "CONFLUENCE_API_TOKEN": "secret-token",
    "CONFLUENCE_SPACES": "IT, BT,REVOPS ,CSO",
}


@pytest.fixture
def env(monkeypatch):
    def apply(values):
        for key, value in values.items():
            monkeypatch.setenv(key, value)

    return apply


def test_comma_separated_lists_are_split(env):
    env(CONFLUENCE_ENV | {"BIGQUERY_DATASETS": "sales,  finance"})
    settings = Settings(_env_file=None)
    assert settings.confluence_spaces == ["IT", "BT", "REVOPS", "CSO"]
    assert settings.bigquery_datasets == ["sales", "finance"]
    assert settings.confluence_labels == []


def test_model_ids_come_from_env(env):
    env(
        {
            "GEMINI_PRO_MODEL": "pro-model-from-env",
            "GEMINI_FLASH_MODEL": "flash-model-from-env",
            "GEMINI_EMBED_MODEL": "embed-model-from-env",
        }
    )
    settings = Settings(_env_file=None)
    assert settings.gemini_pro_model == "pro-model-from-env"
    assert settings.gemini_flash_model == "flash-model-from-env"
    assert settings.gemini_embed_model == "embed-model-from-env"


def test_model_ids_have_no_defaults(monkeypatch):
    for key in ("GEMINI_PRO_MODEL", "GEMINI_FLASH_MODEL", "GEMINI_EMBED_MODEL"):
        monkeypatch.delenv(key, raising=False)
    settings = Settings(_env_file=None)
    assert settings.missing("gemini_pro_model", "gemini_flash_model", "gemini_embed_model") == [
        "GEMINI_PRO_MODEL",
        "GEMINI_FLASH_MODEL",
        "GEMINI_EMBED_MODEL",
    ]


def test_token_is_not_exposed_in_repr(env):
    env(CONFLUENCE_ENV)
    settings = Settings(_env_file=None)
    assert "secret-token" not in repr(settings)
    assert settings.confluence_api_token.get_secret_value() == "secret-token"


def test_require_names_missing_env_vars(monkeypatch):
    monkeypatch.delenv("CONFLUENCE_API_TOKEN", raising=False)
    monkeypatch.setenv("CONFLUENCE_URL", "https://example.atlassian.net/wiki")
    settings = Settings(_env_file=None)
    with pytest.raises(ConfigError, match="CONFLUENCE_API_TOKEN"):
        settings.require("confluence_url", "confluence_api_token")
