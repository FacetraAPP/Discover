# Facetra Discover

Public, portable workspaces for [Facetra](https://github.com/FacetraAPP/Facetra).
Each topic directory under `workspaces/` **is a workspace**. Charts, dashboards and local
data dependencies may reference only files in their own workspace. Required
connections refer to values configured on the user's device; never commit tokens,
API keys, private data or personal health records.

Published content lives in `workspaces/`. Repository documentation and the
non-published starter live in `docs/`; catalog tooling and regression tests live
in `scripts/` and `tests/`. Only direct topic folders in `workspaces/` are
discovered by the publisher.

```text
workspaces/example/
  workspace.yaml       # Portable localPath manifest with title, description and license
  README.md            # Markdown overview shown in Facetra workspace details
  charts/**/*.yaml
  dashboards/**/*.yaml
  data/**/*
  previews/<id>.png    # Optional preview for a chart or dashboard
  previews/workspace.png
```

Resource filenames must match their YAML IDs. IDs are unique across charts and
dashboards within one workspace. External source/dataset references use
`<chart-id>.yaml#/sources/<name>` or `<chart-id>.yaml#/dataset`, resolved by ID
inside that workspace. Different workspaces may reuse the same IDs. Symlinks,
hidden paths, path traversal, missing dependency targets and cycles are rejected.

Workspace metadata is defined in `workspace.yaml`: `title`, optional `description`
and optional `license` (defaults to this repository's Apache-2.0 license). The
catalog uses these directly. Chart and dashboard names and descriptions come from
their own YAML `title` and `notes` fields.

Workspace documentation lives in `README.md` (legacy `readme.md` is also accepted).
Describe the purpose, included charts and dashboards, required connections and setup
steps in Markdown. The catalog lists this file with its size and SHA-256 digest;
Facetra downloads it at the catalog's source revision for the workspace detail and
retains it in complete workspace imports. Individual resource imports do not copy it.
README contents are not embedded in the index.

Legacy `workspace.json` remains accepted; a topic must contain exactly one manifest.
For migration, preserve the same metadata in `workspace.yaml` and remove the JSON file.

## Contributing and agent skills

Start with [AGENTS.md](AGENTS.md) and the [contributor guide](docs/contributing.md).
This repository includes a [complete minimal starter](docs/starter/) and
self-contained specifications for [workspaces and parameters](docs/workspace-yaml.md),
[charts](docs/chart-yaml.md) and [dashboards](docs/dashboard-yaml.md).
No Facetra source checkout or private documentation is required.

The [FTShare workspace](workspaces/ftshare/README.md) includes 18 online charts covering
Chinese macroeconomic indicators and interest rates, plus an optional FTShare
connection type. Its public macro endpoints and GitHub import can be used
without a connection.

Repository skills are available at
[create-chart-yaml](.agents/skills/create-chart-yaml/SKILL.md) and
[create-dashboard-yaml](.agents/skills/create-dashboard-yaml/SKILL.md).
Agents supporting repository skill discovery can invoke $create-chart-yaml or
$create-dashboard-yaml; others can read the same SKILL.md files.

## Catalog publishing

Pushes to `main` run `.github/workflows/catalog.yml`. Pull requests run validation
without publishing. The workflow builds a deterministic, compact `discover.json`
and publishes it with `LICENSE` to the `catalog` branch. It does not change `main`.
Publication is serialized and outdated source builds do not replace the catalog.

The index includes workspace and resource metadata, recursive installation
closures, local connection requirements, file sizes and SHA-256 digests. Its
`sourceRevision` is the exact main commit containing all referenced files. PNGs
are optional, never embedded in the index, and downloaded only in resource details.

Catalog URL:

```text
https://cdn.jsdelivr.net/gh/FacetraAPP/Discover@catalog/discover.json
```

Content URL:

```text
https://cdn.jsdelivr.net/gh/FacetraAPP/Discover@<sourceRevision>/<workspace.path>/<file.path>
```

Workspace entries keep stable topic IDs such as `ftshare` and publish a separate
repository-relative `path`, such as `workspaces/ftshare`. File and resource paths
remain relative to that workspace. Resource IDs and references do not change
when a topic moves. Clients must use the workspace `path` for downloads, source
links and the GitHub checkout prefix; older catalogs without it use the topic ID.

The app falls back to the corresponding `raw.githubusercontent.com` URL when
the CDN times out, returns an error, or serves invalid content. Both origins use
the same source commit. Branch URLs can remain cached for hours; a cached index
still resolves to a consistent, immutable content snapshot. Chart/dashboard
imports create local editable copies. Full workspace imports clone/load this
GitHub repository on `main` and register the workspace's `path` as its prefix;
subsequent workspace updates use the app's ordinary Git workflow.

## Local validation

Requires Python 3.12 or newer:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/build_catalog.py --revision "$(git rev-parse HEAD)" --validate-only
.venv/bin/python scripts/build_catalog.py --revision "$(git rev-parse HEAD)" --output dist
```

Individual files are limited to 20 MiB; an installed workspace is limited to
100 MiB. The complete exported built-in [example workspace](workspaces/example/README.md)
contains 8 charts, 3 dashboards and four fictional-data CSV files.
CI uses the same tests and --validate-only command on every PR and main push.
It checks YAML structure/types, parameters, references and dashboard layouts in
addition to catalog dependencies and file limits. Validation is offline; SQL
execution, remote responses and visual rendering still require a Facetra preview.
