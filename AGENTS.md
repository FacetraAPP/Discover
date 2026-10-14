# Contributing to Facetra Discover

This is the public content repository for Facetra, a native chart and dashboard
application. Each topic under `workspaces/` is an independent, importable workspace.
Contributors need only this repository and Python 3.12+ to author and validate
content; no application checkout, private documentation or credentials are needed.

## Start here

- [Contributor guide](docs/contributing.md): setup, a complete starter workspace,
  validation commands and the pull request/publishing process.
- [Workspace and parameter format](docs/workspace-yaml.md): directory layout,
  manifest fields, metadata, parameter types and connection requirements.
- [Chart format](docs/chart-yaml.md): acquisition sources, datasets, references,
  native/value/ECharts renderers and complete examples.
- [Chart authoring lessons](LESSONS.md): metric interpretation, ISO dates, axes,
  parameter controls and visual checks learned from actual chart usage. Read
  before creating or changing charts.
- [Dashboard format](docs/dashboard-yaml.md): tabs, panels, explicit parameter
  bindings and responsive grid dimensions.
- [Working examples](workspaces/example/README.md): 45 charts and four dashboards, including an offline chart prototype gallery.
- [Minimal starter](docs/starter/): a CSV, chart, dashboard and manifest that can
  be copied together into a new topic under `workspaces/`.

For chart authoring, use [.agents/skills/create-chart-yaml/SKILL.md](.agents/skills/create-chart-yaml/SKILL.md).
For dashboard authoring, use [.agents/skills/create-dashboard-yaml/SKILL.md](.agents/skills/create-dashboard-yaml/SKILL.md).
These repository skills are self-contained entrypoints. Agents that discover
repository skills can invoke them as $create-chart-yaml and $create-dashboard-yaml;
other tools can read the same instructions directly.

## Content rules

- Publish one manifest per topic: workspace.yaml for new content; workspace.json
  remains readable for legacy content. Publish title, description, license and
  requiredConnections only; workspace IDs, kind and personal roles are app metadata.
- Use .yaml for charts and dashboards, including nested folders. Filenames match
  chart.id or dashboard.id. IDs contain 1–80 ASCII letters, digits, underscores
  or hyphens; chart and dashboard IDs share one namespace inside each workspace.
- Keep all dependencies in the same topic. References use chart IDs, for example
  price.yaml#/dataset, regardless of the chart's folder. Do not use relative
  folder paths or refer to another topic.
- Put CSV/SQLite assets in data/. CSV file paths start with data/; SQLite
  file_path is relative to data/. Hidden paths, symlinks, traversal, missing
  files and reference cycles are rejected.
- Chart titles/notes describe that chart; dashboard titles/notes describe that
  dashboard. Workspace title/description/license belong in workspace.yaml.
  Document purpose, data provenance, units and required connections in README.md.
- Use fictional or redistributable public data. Store connection IDs/aliases and
  templates, never tokens, API keys or device paths. Explain local connection
  setup without requiring credentials for validation.
- Source kinds are duckdb (CSV), http, database and sqlite. HealthKit is not
  supported. Unknown fields and renderer-specific field mixtures fail validation.
- Individual files are limited to 20 MiB, and a complete workspace to 100 MiB.
  Optional previews are previews/<resource-id>.png and previews/workspace.png.

## Checks and implementation changes

Run from the repository root:

~~~sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/build_catalog.py --revision "$(git rev-parse HEAD)" --validate-only
~~~

Validation is offline: it checks document structure, parameters, layout, references,
data paths and dependency closures. It does not execute SQL, contact HTTP/database
services, verify result columns or render charts. For runtime changes, test the
resource in Facetra when available and describe any unverified behavior in the PR.

scripts/validate_yaml.py owns document and binding validation.
scripts/build_catalog.py owns workspace discovery, file checks and catalog assembly.
scripts/publish_catalog.py owns publication to the catalog branch. When changing a
format rule, update its documentation and add a regression test for observable
acceptance/rejection behavior. Keep existing examples and legacy JSON manifests
working unless the task explicitly includes a migration.

PR CI validates all workspaces and runs tests. Only a successful main-branch
workflow publishes the catalog. Do not hand-edit discover.json, publish generated
files on main or update an application's submodule pointer as part of a content PR.
