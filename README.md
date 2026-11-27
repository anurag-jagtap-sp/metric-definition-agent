# Metric Definition Agent

An agent built on Google ADK and Gemini that finds the metric formulas stated in Confluence pages and SOPs, drafts a MetricFlow YAML definition for each one with cited evidence, and opens a pull request. A human reviewer approves each PR before it is merged into `main`. Merged definitions are compiled and made queryable by a consumer agent through governed metric tools.

## How it works

1. **Find formulas.** Ingested pages are scanned for sections that state a formula (equations, "calculated as" statements, formula tables). Sections that only mention a metric name are skipped and listed in a run report.
2. **Draft.** For each formula, the agent drafts a definition that keeps the formula verbatim in `formula_text`, alongside the generated expression and the source page URL, version and quote.
3. **Check.** Automated checks run before review: the quote exists in the stored page version, every column exists in the warehouse, every term in the formula is mapped, the YAML passes `dbt parse` and `mf validate-configs`, and there are no duplicates. A Gemini formula critic flags mismatches between the formula and the expression as open questions; it never edits the draft.
4. **Review and merge.** Each source page gets its own PR with a reviewer checklist. CODEOWNERS routes it to metric owners, CI re-runs on every edit, and branch protection on `main` requires an approval and passing checks. The bot can open PRs but cannot approve or merge.

There is no hand-written reference set. The reviewer judges correctness, and every merged metric becomes a regression case for future runs.

## Storage layers

- **Layer 1, authoring:** MetricFlow YAML in Git, changed only through approved PRs.
- **Layer 2, runtime:** CI compiles `main` into `semantic_manifest.json`, which MetricFlow executes for the consumer agent's `list_metrics`, `get_metric` and `query_metric` tools.

## Status

Phase 0 (scope and foundations). See [docs/development-plan.md](docs/development-plan.md) for phases, stack and scope, and [docs/Metric_Definition_Agent_Development_Phases.pptx](docs/Metric_Definition_Agent_Development_Phases.pptx) for the presentation.

## Layout

```text
metric-agent/metric_agent/   Python package (import name metric_agent)
  ingest/ detect/ store/ tools/ authoring/ models/ consumer/ runtime/
  config.py                  settings from .env
  cli.py                     `metric-agent` command
semantic-layer/              dbt project (dbt-core, dbt-duckdb, MetricFlow); approved YAML in models/
tests/                       pytest; fixtures/ holds the formula detector test cases
.github/                     CODEOWNERS and the PR template with the reviewer checklist
docs/                        plan and presentation
```

## Setup

Requires [uv](https://docs.astral.sh/uv/) (`brew install uv`).

```bash
uv sync --python 3.12
cp .env.example .env              # then fill in Confluence, Vertex AI, GitHub and BigQuery values
gcloud auth application-default login   # for Gemini via Vertex AI
```

Model IDs are read only from `GEMINI_PRO_MODEL`, `GEMINI_FLASH_MODEL` and `GEMINI_EMBED_MODEL`; none are hard-coded.

## Commands

```bash
uv run metric-agent check-config        # which setting groups are configured (never prints values)
uv run metric-agent check-confluence    # every in-scope space exists and has readable pages
uv run pytest                           # unit tests (Confluence, Gemini and GitHub are mocked)
cd semantic-layer && uv run dbt parse --profiles-dir .   # writes target/semantic_manifest.json
```

## Formula examples

`tests/fixtures/formula_examples.template.yaml` defines what counts as a formula and the fixture format. The real detector test cases are in `tests/fixtures/formula_examples.local.yaml`, which is gitignored while this repository is public because it quotes internal Confluence pages. They are detector test cases, not an answer key for metric definitions.

## Merge gate

`main` is protected: pull request with one approval from a code owner, approvals dismissed on new commits, the last push must be approved by someone else, admins included, linear history, no force pushes or deletions. Required CI status checks are added in Phase 2. The settings were applied with:

```bash
gh api -X PUT repos/anurag-jagtap-sp/metric-definition-agent/branches/main/protection --input - <<'EOF'
{
  "required_status_checks": null,
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "require_code_owner_reviews": true,
    "dismiss_stale_reviews": true,
    "require_last_push_approval": true
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
```

Check the current settings with `gh api repos/anurag-jagtap-sp/metric-definition-agent/branches/main/protection`. The bot account must have write access only (never admin), so it can open PRs but cannot approve its own or bypass protection.
