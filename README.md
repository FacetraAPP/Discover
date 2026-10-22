# Facetra Discover

Public, importable workspaces for [Facetra](https://github.com/FacetraAPP/Facetra).
Browse Discover in the app to import a workspace, chart or dashboard. Imported
charts and dashboards are editable local copies.

## Workspaces

- [Examples](workspaces/example/README.md): 68 charts and six dashboards covering
  stock prices, business data, financial indicators and chart galleries. Includes
  Chinese and English display text. The HTTP examples require internet; the other examples run offline
  with fictional data.
- [FTShare · Chinese macroeconomics](workspaces/ftshare/README.md): 18 online charts
  for economic indicators and interest rates, with data definitions and setup guidance.

Each workspace README explains its data sources, units, license, required
connections and limitations. Connection values stay on your device; this
repository contains no credentials.

## Contributing

Start with [AGENTS.md](AGENTS.md) and the [contributor guide](docs/contributing.md).
Use the [complete starter](docs/starter/) to create a workspace. Format references
cover [workspaces and parameters](docs/workspace-yaml.md), [charts](docs/chart-yaml.md),
[dashboards](docs/dashboard-yaml.md) and [Chinese and English text](docs/localization.md).

Published workspaces live under `workspaces/<topic>/`:

```text
workspace.yaml       # Title, description, license and connection requirements
README.md            # User guide displayed in Facetra
charts/**/*.yaml
dashboards/**/*.yaml
data/**/*
previews/<id>.png     # Optional chart or dashboard preview
previews/workspace.png
```

Each topic is independent. Keep chart references and data within its workspace.
Write user guides and resource notes for readers using the content; keep format
instructions in `docs/` and change history in PRs and commits.

Repository skills are available for
[charts](.agents/skills/create-chart-yaml/SKILL.md) and
[dashboards](.agents/skills/create-dashboard-yaml/SKILL.md).

## Validation and publishing

Requires Python 3.12 or newer:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/build_catalog.py --revision "$(git rev-parse HEAD)" --validate-only
```

Validation checks YAML, references, parameters, layouts and file limits offline.
SQL, remote data and rendering need a Facetra preview. See the contributor guide
for submission and validation details.

Pull requests run validation. Successful `main` builds publish the catalog to
the `catalog` branch. Commit source content, not generated catalog files.

Published catalog:

```text
https://cdn.jsdelivr.net/gh/FacetraAPP/Discover@catalog/discover.json
```

Content is licensed under [Apache-2.0](LICENSE) unless a workspace states otherwise.
Remote data remains subject to its provider's terms.
