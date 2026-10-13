# Authoring public Discover content

Discover contains portable configuration and data, not application source code.
Each top-level topic becomes a workspace card in Facetra. Users can import the
whole workspace, one chart or one dashboard together with its dependencies.
All instructions and examples needed to contribute are in this repository.

## Set up validation

Use Python 3.12 or newer. From the repository root:

~~~sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/build_catalog.py --revision "$(git rev-parse HEAD)" --validate-only
~~~

No application checkout, connection library, credentials or network services are
needed after installing the Python dependency. If you use a different virtual
environment, substitute its Python executable in these commands.

## Start a workspace

Choose a unique topic directory containing only letters, digits, underscores and
hyphens. The following starter is a complete fictional sales workspace:

~~~sh
cp -R docs/starter sales
.venv/bin/python scripts/build_catalog.py --revision "$(git rev-parse HEAD)" --validate-only
~~~

Use an unused destination; do not copy into an existing topic. Rename the topic,
workspace ID/title and resource IDs for your use case. If you rename sales.yaml
or overview.yaml, update chart.id/dashboard.id and all references to those IDs.
The CSV contains month/revenue columns, the chart filters by min_revenue, and
the dashboard explicitly binds that parameter.

For an existing topic, inspect its manifest, README, charts and data before adding
files. Use the [workspace guide](workspace-yaml.md) for metadata and parameters,
the [chart guide](chart-yaml.md) for source/SQL/rendering, and the
[dashboard guide](dashboard-yaml.md) for composition and layout.

## Verify and submit

Run both validation commands after editing. Validation scans every workspace,
including charts and dashboards in nested folders. Errors name the offending
workspace/file and, where relevant, the field. Example:

~~~text
sales/charts/sales.yaml: chart.dataset must equal dataset.id
~~~

CI checks parsing (including duplicate keys), supported fields/types,
parameters/defaults/options, source and renderer variants, dataset targets,
reference/parameter bindings, cycles, dashboard layouts, IDs, local files and
installation size. .yml resources and topics missing a manifest are rejected
instead of silently omitted. Existing workspace.json manifests remain supported.

Validation never executes SQL, requests HTTP data, opens a database connection,
runs JavaScript or renders charts. Result-column names, SQL behavior, remote
response shape and visual correctness must be checked in Facetra when available.
State which runtime checks were performed in your PR. Public service examples
should also explain response expectations and connection setup in the topic README.

To inspect the generated catalog locally:

~~~sh
.venv/bin/python scripts/build_catalog.py --revision "$(git rev-parse HEAD)" --output dist
~~~

dist/ is ignored by Git. Commit source files and documentation, not generated
catalog files. Describe the new content, data provenance/license, connection
requirements and validation result in the PR.

Pull requests run the same offline checks without publishing. Successful main
workflows generate discover.json and LICENSE on the catalog branch, with file
digests and the immutable source commit. Do not edit that branch manually.

## Agent skills

Repository skills live in .agents/skills/create-chart-yaml and
.agents/skills/create-dashboard-yaml. In agents supporting repository skill
discovery, invoke $create-chart-yaml or $create-dashboard-yaml. Otherwise read
their SKILL.md entrypoints directly. Both link only to instructions and examples
in this repository and use the same validation command as CI.
