"""Command-line entry points."""

import typer

from metric_agent.config import ConfigError, get_settings
from metric_agent.ingest import confluence

app = typer.Typer(no_args_is_help=True, help="Metric Definition Agent")

SETTING_GROUPS = {
    "Confluence": confluence.CONFLUENCE_SETTINGS,
    "Gemini (Vertex AI)": (
        "google_cloud_project",
        "google_cloud_location",
        "gemini_pro_model",
        "gemini_flash_model",
        "gemini_embed_model",
    ),
    "GitHub bot": ("github_token", "github_repo"),
    "BigQuery": ("bigquery_project", "bigquery_datasets"),
}


@app.command("check-config")
def check_config() -> None:
    """Show which setting groups are configured, without printing values."""
    settings = get_settings()
    for group, fields in SETTING_GROUPS.items():
        missing = settings.missing(*fields)
        status = "set" if not missing else f"missing {', '.join(missing)}"
        typer.echo(f"{group:<20} {status}")


@app.command("check-confluence")
def check_confluence() -> None:
    """Check that every in-scope Confluence space is readable with the configured token."""
    settings = get_settings()
    try:
        client = confluence.connect(settings)
    except ConfigError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc

    results = confluence.check_spaces(client, settings.confluence_spaces)
    for result in results:
        mark = "OK  " if result.ok else "FAIL"
        typer.echo(f"{mark} {result.key:<10} {result.name or '':<45} {result.detail}")
    if not all(result.ok for result in results):
        raise typer.Exit(1)
