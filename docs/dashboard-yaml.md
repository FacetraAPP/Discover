# Dashboard YAML

Dashboards compose chart instances from one workspace. A panel references
metadata.id, not a path or a dataset. Save as
workspaces/<topic>/dashboards/<optional-folders>/<id>.yaml.
Read the [workspace/parameter guide](workspace-yaml.md) and inspect the charts
before binding them. [The starter dashboard](starter/dashboards/overview.yaml)
is a complete file, paired with [its chart](starter/charts/sales.yaml).

## Document fields

| Field | Requirement |
| --- | --- |
| version | Required integer 1 |
| kind | Required string Dashboard (case-sensitive) |
| i18n | Optional resource-local message catalog; see [display text](localization.md) |
| metadata | Required object with id/title and optional notes/tags |
| metadata.id | Required ID matching the filename |
| metadata.title | Required nonempty fixed string or `{i18n: key}` reference |
| params | Required parameter list; use [] when none |
| tabs | Required nonempty list of tab objects |
| metadata.notes | Optional fixed string or display reference describing this dashboard; defaults to "" |
| metadata.tags | Optional string list; defaults to [] |

Metadata accepts only id, title, notes and tags. version/kind identify the document
format and stay at the root. Resource fields at the root are rejected. Tab and
panel IDs/titles describe layout elements and stay within those elements.

A tab has required id, title and panels, with optional layout.
Tab IDs are unique within the dashboard. Each panel has required id/chart,
optional params and height, and grid-only width/row_span/responsive.
Panel IDs are unique across every tab, including repeated instances of the same
chart. All IDs follow the workspace ID rules; titles are nonempty fixed strings or display references.
Unknown fields fail validation.

For existing files, move the root id/title/notes/tags into metadata and remove
their former keys. Keep version/kind/params/tabs at the root and retain all
resource IDs, filenames and panel references. This is a breaking change paired
with Facetra's metadata schema; old and mixed document structures are rejected.

## Explicit shared parameters

~~~yaml
version: 1
kind: Dashboard
metadata:
  id: overview
  title: Sales overview
  notes: One shared threshold and one fixed comparison.
params:
  - {name: threshold, label: Minimum revenue, type: number, default: 0, minimum: 0}
tabs:
  - id: summary
    title: Summary
    panels:
      - id: filtered_sales
        chart: sales
        height: 240
        params:
          min_revenue: {param: threshold}
      - id: fixed_sales
        chart: sales
        height: 240
        params:
          min_revenue: 100
~~~

This is a complete dashboard for the starter sales chart. The first panel maps
the chart's min_revenue parameter to the dashboard's threshold; the second uses
a number literal. A matching parameter name does not automatically bind anything.

Dashboard parameter definitions use the same type/default/range/options rules as
charts. A {param: name} binding requires a declared dashboard parameter with the
same type as the target chart parameter; its default must satisfy that chart's
constraints. Literal values must have the right type and satisfy the chart's
bounds/options. Unknown chart parameter names, extra binding keys and required
chart parameters without a binding/default fail validation.

Unbound chart parameters use chart defaults. Panels refer to charts in the same
topic; their source/dataset dependencies must also remain there. See
[parameter definitions](workspace-yaml.md#parameter-definitions) for all fields.

## Vertical layout

Omit layout to stack panels in declared order. height is the plotting area height,
defaults to 240 points and must be 160–600. Grid-only fields are invalid here.
A single tab displays directly; multiple tabs use a tab selector.

## Responsive grid

This complete dashboard uses the starter chart twice:

~~~yaml
version: 1
kind: Dashboard
metadata:
  id: sales_grid
  title: Sales comparison
  notes: Compare a shared threshold with a fixed revenue filter.
params:
  - {name: threshold, type: number, default: 0, minimum: 0}
tabs:
  - id: comparison
    title: Comparison
    layout:
      type: grid
      columns: 12
      row_height: 40
      gap: 12
      min_width: 1200
    panels:
      - id: shared_sales
        chart: sales
        width: 7
        row_span: 6
        responsive: {compact: {card_height: 320}}
        params:
          min_revenue: {param: threshold}
      - id: fixed_sales
        chart: sales
        width: 5
        row_span: 6
        responsive: {compact: {card_height: 260}}
        params:
          min_revenue: 100
~~~

layout.type is required and must be grid; the other fields have defaults:

| Field | Default | Range |
| --- | --- | --- |
| columns | 12 | Integer 1–12 |
| row_height | 40 | 24–120 points |
| gap | 12 | 0–32 points |
| min_width | 1200 | 320–2400 points, greater than (columns − 1) × gap |
| panel.width | All columns | Integer 1–columns |
| panel.row_span | 4 | Integer 1–24 |
| panel.height | 240 | 160–600 points |
| panel.responsive.compact.card_height | Computed fallback | 160–600 points when specified |

Numbers must be finite. A wide grid panel's whole-card height is:

~~~text
row_span × row_height + (row_span − 1) × gap
~~~

It must be at least 160 points. This example's cards are 300 points tall.
The whole card includes header/padding; the plotting area fills the remainder.
height does not control the wide grid card.

At a container width below min_width, or with accessibility text sizing, cards
stack full-width in YAML order. compact.card_height sets the whole card height
for this layout. Without it, Facetra uses height + 80, clamped to 160–420 points.
Grid-only fields are never valid on a tab without layout.

The grid places panels in declaration order, supports row/column spans and does
not rearrange earlier gaps; arbitrary spans can leave holes. Preserve a useful
reading order for narrow screens. The
[Mosaic example](../workspaces/example/dashboards/example_mosaic_dashboard.yaml) demonstrates
a larger dashboard with both native and ECharts charts.

## Validation

Run the [contributor commands](contributing.md#verify-and-submit). They verify
chart existence, bindings, ID uniqueness and layout dimensions without executing
charts. When Facetra is available, apply shared parameters and preview wide and
compact layouts. Document any required local connections in the workspace README.

## Tags

Charts and dashboards accept optional `metadata.tags: [股票, 行情]`.
Omission means no tags. Metadata fields at their former locations are rejected. Tags must be strings of 1–64 characters
after trimming, without control characters. Display spelling and order are
preserved; duplicates are merged ignoring case and accents. Quote numeric or
boolean-looking names (`"2026"`, `"on"`).

Discover publishes resource tags in its generated catalog. Workspace cards and
filters use the union of their resources' tags. Cards display one compact line
with overflow counts, and details show all tags. Search matches words across
names, descriptions and tags, including `#tag` queries. The tag picker supports
search and multiple selections, matching **any** selected tag; search, resource
type, folders and favorites combine with that selection. Counts in the picker
reflect the current search and other filters, before the tag selection. Active
tags remain visible and removable even if another filter yields no results.

Local chart/dashboard action menus offer **Edit Tags**, including existing tag
suggestions. Saving uses the regular revision/conflict and read-only checks;
block YAML keeps its other fields, comments and formatting. Flow-style YAML
may be reserialized. Tags are retained when duplicating or importing resources.

## Bilingual dashboards

Dashboard titles/notes, parameter labels and tab titles may use `{i18n: key}` references
into the Dashboard’s own catalog. Panel charts resolve their own catalogs independently.
See [Chinese and English display text](localization.md) for complete syntax and fallback rules.
