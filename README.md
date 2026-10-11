# Facetra Discover

Public, portable workspaces for [Facetra](https://github.com/BoringHappy/Facetra).
Each top-level topic directory **is a workspace**. Charts, dashboards and local
data dependencies may reference only files in their own workspace. Required
connections refer to values configured on the user's device; never commit tokens,
API keys, private data or personal health records.

```text
example/
  workspace.json       # Facetra portable localPath manifest
  discover.yaml        # Optional description, tags and license
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
https://cdn.jsdelivr.net/gh/FacetraAPP/Discover@<sourceRevision>/<workspace>/<path>
```

The app falls back to the corresponding `raw.githubusercontent.com` URL when
the CDN times out, returns an error, or serves invalid content. Both origins use
the same source commit. Branch URLs can remain cached for hours; a cached index
still resolves to a consistent, immutable content snapshot. App imports create
editable copies and do not overwrite them automatically.

## Local validation

Requires Python 3.12 or newer:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/build_catalog.py --revision "$(git rev-parse HEAD)" --output dist
```

Individual files are limited to 20 MiB; an installed workspace is limited to
100 MiB. The complete exported built-in [example workspace](example/README.md)
contains 11 charts, 4 dashboards and four fictional-data CSV files. HealthKit
charts read on-device health records only after the user enables access.
