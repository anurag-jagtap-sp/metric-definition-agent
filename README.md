# Metric Definition Agent

An agent built on Google ADK and Gemini that reads Confluence pages, SOPs, and related documents, drafts metric definitions as MetricFlow YAML with cited evidence, and opens them for human review. Approved definitions are compiled and made queryable by a consumer agent through governed metric tools.

## Status

Planning. See [docs/development-plan.md](docs/development-plan.md) for phases, stack, and scope.

## Planned layout

```text
metric-agent/     agent code: ingestion, index, ADK agents, validators, tools
semantic-layer/   dbt project with MetricFlow YAML (approved definitions)
docs/             plan and design notes
```
