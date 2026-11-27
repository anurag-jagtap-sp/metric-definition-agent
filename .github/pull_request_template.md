## Summary

<!-- What this PR changes. For agent-drafted metric PRs, the publisher fills in one section per metric:
quoted formula, generated expression, source link and page version, critic findings, conflicts, open questions. -->

## Reviewer checklist

For every metric in this PR:

- [ ] **Formula matches source:** the generated expression and filters implement the quoted `formula_text` exactly
- [ ] **Filters and exclusions correct:** nothing added, dropped or inverted compared with the source
- [ ] **Grain correct:** the time grain, entity and aggregation match the source definition
- [ ] **Owner correct:** `meta.owner` is the team or person accountable for this metric
- [ ] Every citation links the right page and version, and the quote is verbatim
- [ ] Every open question and conflict is resolved, or explicitly accepted with a comment
