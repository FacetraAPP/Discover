# Workspaces, paths and parameters

## Directory layout

Every topic directory under `workspaces/` is one independent workspace:

~~~text
workspaces/sales/
  workspace.yaml
  README.md
  charts/sales.yaml
  dashboards/overview.yaml
  data/sales.csv
  previews/sales.png        # Optional chart preview
  previews/overview.png     # Optional dashboard preview
  previews/workspace.png    # Optional workspace preview
~~~

charts/ and dashboards/ can contain nested folders. File extensions are .yaml.
The filename without its extension equals metadata.id. IDs use
1–80 ASCII letters, digits, underscores or hyphens and are unique across charts
and dashboards in the workspace. Do not use the reserved builtin_example_ prefix.
Different topics may reuse resource IDs.

The catalog identifies a topic by its directory name, for example `sales`, and
exports its repository-relative location separately as `path: workspaces/sales`.
Catalog file paths stay workspace-relative. GitHub workspace imports use the
catalog path as their checkout prefix. Root-level `docs/`, `scripts/`, `tests/`
and `docs/starter/` are not publishable content.

Local references resolve by chart ID within the topic, regardless of folders.
No cross-topic references, symlinks, hidden path segments, empty segments,
backslashes, absolute paths or .. traversal are allowed. Files may be at most
20 MiB; a complete workspace may be at most 100 MiB.

## Workspace manifest

[The complete starter manifest](starter/workspace.yaml) uses these fields:

| Field | Type / requirement | Meaning |
| --- | --- | --- |
| title | Required nonempty string | Workspace card and detail title |
| description | Optional string | Workspace card/detail description |
| license | Optional string, defaults to Apache-2.0 | License for redistributed content |
| requiredConnections | Optional list of unique alias/type maps, defaults to [] | Local connection IDs or aliases needed by this workspace |

Workspace names identify workspaces inside Facetra. The catalog's topic key comes
from the directory name under `workspaces/`; it is independent of the display title.
Do not publish `id`, `kind` or `isPersonal` in workspace.yaml. Storage kind is
device-local Facetra metadata, and workspaces have no special personal role.

For new topics, use workspace.yaml. Legacy workspace.json may still contain
`id`, `kind: localPath` and `isPersonal` for compatibility, but a topic must have
exactly one manifest. To migrate, retain the portable fields in the table above,
write YAML and remove the old JSON manifest. Device paths,
connection values and imported discoverOrigin metadata do not belong in a
public manifest. Optional description/license may be null to use their defaults.

README.md explains the workspace purpose, chart/dashboard list, column names,
units, data provenance/license and any setup. Legacy readme.md is accepted,
but keep only one of the two. Facetra displays this Markdown in workspace details
and includes it in complete workspace imports.

## YAML conventions

Use two-space indentation, explicit true/false booleans and typed numeric
values. Quote strings that look like numbers, dates or YAML booleans:
default: "001", x: "date" and option labels such as "on".
Use | or |- for SQL and multiline notes. Numeric fields accept scientific
notation such as 1e+0. Quoted "240" is a string and is invalid for panel height.
Duplicate keys are rejected, including collisions introduced by YAML merges.
Avoid YAML aliases/merge tricks in public examples; explicit definitions are easier
to review. Unknown fields fail validation rather than being ignored.

## Parameter definitions

Chart and dashboard params use the same list-of-objects format:

~~~yaml
params:
  - name: min_revenue
    label: Minimum revenue
    type: number
    default: 0
    minimum: 0
    maximum: 1000
    options: [0, 100, 200]
    required: true
    advanced: false
~~~

| Field | Rule |
| --- | --- |
| name | Required ID; unique in this document |
| type | Required: string, integer, number, boolean or date |
| label | Optional fixed string or `{i18n: key}` display reference; defaults to name |
| default | Optional scalar of the declared type |
| required | Optional boolean, defaults to true |
| minimum / maximum | Optional finite numeric bounds; minimum must not exceed maximum; unsupported for date |
| options | Optional list of typed permitted scalar values |
| advanced | Optional boolean, defaults to false |

All defaults and options must satisfy the type/range rules; a default with options
must be one of them. number accepts integers and decimals; integer accepts
integral numbers. Boolean values are not integers. Required string values cannot
be empty. Date values are quoted ISO calendar dates (`YYYY-MM-DD`), validated as
real dates, and remain strings in SQL and request parameters. Facetra presents
them with a native date picker. Optional date parameters may use an empty string.
Dates do not accept numeric bounds. API-specific date formatting belongs in the
HTTP source template, not in a compact-date default. Give charts useful defaults so a single-chart
import works independently.
A required parameter without a default must receive a value before execution;
dashboard panels and external references must bind it.

There are two binding forms:

~~~yaml
params:
  min_revenue: {param: threshold}  # Use a caller/dashboard parameter
  region: "west"                 # Use a typed fixed value
~~~

The left-hand name belongs to the target chart. The param name belongs to the
caller or dashboard and must have the same type. Fixed values and passed defaults
must satisfy the target's ranges/options. Bindings cannot contain extra keys.
Dashboard params and a reference's with follow these rules. Same-file source
references inherit chart parameters; references to another chart receive only
explicit with values plus that chart's defaults.

## Connections

Connections are configured on the user's device. A database source uses
connection: business; an HTTP source can use templates such as
"{{ connections.market.endpoint }}" and "{{ connections.market.token }}".
requiredConnections lists typed requirements without their values, for example
`[{alias: market, type: key-value}]`. `type` defaults to `key-value`; custom type
IDs are supported. Aliases must be unique. String lists are not accepted. The catalog
also discovers dependencies from chart source definitions and referenced charts.

The topic README must explain what each connection means and which local fields
are needed. Do not commit tokens, API keys, private data, personal health records
or machine-specific paths. Offline validation does not need real connections.

### Optional connection type definitions

A workspace may include `connections/<type-id>.yaml` to offer a Key-Value
connection form in Facetra. Definitions are included in complete workspace
imports; they do not create a connection or store values. A definition alone
does not make the workspace require a connection. For example:

~~~yaml
name: FTShare
notes: Optional credentials for FTShare hosted APIs.
fields:
  - key: endpoint
  - key: api_key
~~~

`fields` is required and contains objects with only `key`. Keys must be unique
IDs. Optional `name` is a nonempty string (defaults to the filename); optional
`notes` is a string. Field values and defaults are not permitted. Definitions
must be directly inside `connections/`, use `.yaml`, and follow the same file,
path and symlink restrictions as other content. Single-resource imports include
only their chart/data dependencies; use a complete workspace import to obtain
these optional forms. Configure actual values in the device's connection library.

## Bilingual resources

Charts and dashboards can include their own `i18n` message table. Titles, notes, parameter labels,
tab titles and ECharts display text may reference its keys. Workspace manifest fields remain fixed
strings. See [Chinese and English display text](localization.md) for syntax, fallback and catalog behavior.
