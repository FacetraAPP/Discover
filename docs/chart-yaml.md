# Chart YAML

A chart file describes acquisition, transformation and rendering in one document:
params → sources → dataset → chart. Save it as
workspaces/<topic>/charts/<optional-folders>/<chart.id>.yaml.
Read [workspace paths and parameters](workspace-yaml.md) first.

The [complete starter chart](starter/charts/sales.yaml), together with its
[CSV](starter/data/sales.csv), is ready to copy into a workspace.

## Top-level fields

| Field | Rule |
| --- | --- |
| params | Optional parameter list; defaults to [] |
| sources | Optional mapping of source IDs to source definitions; defaults to {}; at most 32 |
| dataset | Required object: one local dataset or a reference to another dataset |
| chart | Required object: resource metadata and renderer configuration |

No other top-level fields are allowed. Metadata such as title, notes and renderer
belongs inside chart. Source/dataset IDs follow the ID rules in the workspace
guide; dataset input IDs must be unique without regard to case.

## Acquisition sources

A concrete source contains source, provider fields, and optional display.
display is df (default), json or text and controls its raw preview.
A reference source instead contains ref, optional with and optional display.
Do not mix acquisition fields into a reference.

### CSV through DuckDB

~~~yaml
sources:
  sales:
    source: duckdb
    file: data/sales.csv
~~~

file is required, points into this topic's data/ directory, and must exist.
source: duckdb means a CSV acquisition source; transforms still run in the
dataset. Do not add source.sql, format, URL or connection fields.

### HTTP

~~~yaml
sources:
  remote:
    source: http
    method: get
    url: "{{ connections.market.endpoint }}"
    headers:
      Authorization: "Bearer {{ connections.market.token }}"
    params:
      symbol: "{{ params.symbol }}"
    format: json
    recordsPath: [data, records]
~~~

This is a source fragment. It requires a declared symbol chart parameter and
a locally configured market connection with endpoint/token fields. The public
endpoint must return the expected response; this repository cannot provide or
test that service. [The HTTP example](../workspaces/example/charts/Example/HTTP/example_http_ip_pie.yaml)
is a complete chart whose connection setup is in [the example README](../workspaces/example/README.md).

| Field | Rule |
| --- | --- |
| url | Required nonempty string; resolved URL must be HTTPS without user info or fragment |
| method | get or post, case-insensitive; defaults to get |
| headers | Optional mapping of strings to strings |
| params | Optional query mapping with scalar values |
| json | Optional nested JSON POST body; objects, lists, scalars and null are supported |
| data | Optional POST form mapping with scalar values; mutually exclusive with json |
| format | json or csv; defaults to json |
| recordsPath | Optional list of object-key strings for a nested JSON record collection; requires explicit format: json |

GET has no json/data body. JSON can be one object or an object array; for a nested
record collection supply recordsPath. CSV responses become tabular data directly.
For POST, add method: post and either a json body or data form fields.
Templates support "{{ params.name }}" and "{{ connections.id.field }}".
To format an ISO date parameter for an API, explicitly use
"{{ params.start_date | date_format('yyyyMMdd') }}". The supported output formats
are `yyyyMMdd` and `yyyy-MM-dd`; the input must be a valid ISO date string.
Unfiltered date parameters retain `YYYY-MM-DD`, and the filter does not change
the saved parameter value. Filters apply only to parameter references.
An entire JSON value consisting of a parameter template preserves its scalar
type; a template embedded in other text produces a string. Template syntax and
resolved response fields still need runtime verification.

### Database query

~~~yaml
sources:
  orders:
    source: database
    connection: business
    sql: |
      SELECT order_date, revenue FROM orders WHERE region = $region
~~~

connection is a local connection ID/alias backed by a PostgreSQL or MySQL
connection. sql is required and uses the remote database's dialect. Define
region in chart params. Only source, connection, sql and optional display belong
here; put credentials and endpoint details in the local connection library.

### SQLite file

~~~yaml
sources:
  orders:
    source: sqlite
    file_path: orders.sqlite
    sql: |
      SELECT order_date, revenue FROM orders
~~~

file_path is relative to this workspace's data/ directory, so this example needs
data/orders.sqlite. sql is required and uses SQLite syntax. There is no connection
field, file field or HTTP configuration.

## Dataset

Each file has exactly one dataset, with a required ID. chart.dataset must equal it.

~~~yaml
dataset:
  id: monthly_sales
  sources:
    - id: raw
      ref: "#/sources/sales"
  sql: |
    SELECT month, CAST(revenue AS DOUBLE) AS revenue
    FROM raw
    WHERE CAST(revenue AS DOUBLE) >= $min_revenue
    ORDER BY month
~~~

The dataset.sources list has 1–32 objects, each with id, ref and optional with.
id becomes a SQL table name; ref selects an acquisition source, not a dataset.
SQL is a DuckDB SELECT or WITH query over those table names. Use a single query,
without a semicolon, positional ? placeholders, file/network readers or mutating
statements. Bind chart parameter values with $name; do not interpolate values
into SQL. For SQL use parameter names beginning with a letter or underscore,
followed by letters, digits or underscores. Explicitly cast fields where useful.

sql is optional with exactly one input: that input passes through unchanged.
Multiple inputs require sql. Keep filtering, aggregation and moving averages in
SQL, and select the column names referenced by the renderer.
CI checks the document's SQL field type but does not compile or execute SQL.

### Reusing definitions

All references stay within the workspace and resolve by chart ID, even if the
target file lives in a different charts/ subfolder:

| Form | Use |
| --- | --- |
| "#/sources/sales" | Source in this chart |
| "sales.yaml#/sources/sales" | Source exported by another chart |
| "sales.yaml#/dataset" | Dataset defined by another chart |

A source reference:

~~~yaml
sources:
  shared:
    ref: "sales.yaml#/sources/sales"
    with:
      min_revenue: {param: threshold}
~~~

A dataset input uses the same source ref/with form, plus its input id.
To reuse a dataset, replace the entire dataset block:

~~~yaml
dataset:
  id: reused_sales
  ref: "sales.yaml#/dataset"
  with:
    min_revenue: {param: threshold}
~~~

This referenced dataset permits only id, ref and optional with; it cannot also
define sources or sql. The caller chart must declare threshold, and chart.dataset
must be reused_sales. Same-file references inherit chart parameters. Cross-file
references receive only explicit with arguments plus the target chart's defaults,
including when reusing one of its sources. See the
[binding rules](workspace-yaml.md#parameter-definitions). Missing targets and
both same-file and cross-file cycles fail validation.

## Resource metadata and renderers

Every chart block needs id, title and dataset. notes is an optional string
describing data provenance, units or interpretation. renderer defaults to default.
Renderer variants cannot mix each other's fields, even when a field is null.

### Native renderer

~~~yaml
chart:
  id: sales
  title: Monthly revenue
  dataset: monthly_sales
  renderer: default
  plot: bar
  x: month
  y: revenue
  notes: Fictional revenue in thousands of currency units.
~~~

plot is line, area, bar, pie, scatter, heatmap or rule. x/y are required nonempty result-column names.
For pie, x is the category and y its numeric value. An optional average names an
SQL-generated overlay column; pie cannot use it. Do not add value, option or scripts.

Coordinate marks require the Facetra version that adds these YAML plots:

| plot | Mark / bindings |
| --- | --- |
| scatter | PointMark; x and y are numeric columns, with true numeric X spacing |
| heatmap | RectangleMark; x/y are categories; required color names a numeric intensity column |
| rule | RuleMark; x and required x_end are numeric start/end; y is a category; end must be at least start |

`color` belongs only to heatmap, `x_end` only to rule. These three plots do not accept
`average`. Missing/null/nonnumeric coordinate values fail execution instead of
becoming zero. See the [seven native prototypes](../workspaces/example/charts/Example/Gallery/SwiftCharts/).

### Value card

~~~yaml
chart:
  id: total_revenue
  title: Total revenue
  dataset: total
  renderer: value
  value: total_revenue
~~~

value is the required result-column name. Configure the dataset to return the
intended scalar, for example SELECT SUM(revenue) AS total_revenue FROM raw.
Do not add native plot/x/y fields, ECharts option or scripts.

### ECharts

~~~yaml
chart:
  id: sales
  title: Monthly revenue
  dataset: monthly_sales
  renderer: echarts
  option:
    tooltip: {trigger: axis}
    xAxis:
      type: category
      data: {from: monthly_sales, field: month}
    yAxis: {type: value}
    series:
      - type: bar
        data: {from: monthly_sales, field: revenue}
~~~

option must be a nonempty object. Ordinary ECharts option objects/lists/scalars
are preserved. An object with from is a Facetra binding and follows this table:

| Binding | Result |
| --- | --- |
| {from: monthly_sales, field: revenue} | One result column as a value array |
| {from: monthly_sales, fields: [month, revenue]} | Ordered tuples of result fields |
| {from: monthly_sales, x: month, y: revenue} | Ordered x/y pairs |
| {from: monthly_sales, rows: true} | Row objects containing every result field |
| {from: params, name: show_labels} | Current value of a declared chart parameter |
| {from: script, name: formatter} | Named expression from chart.scripts |

Dataset bindings must use chart.dataset and exactly one mode. fields is a
nonempty list of column-name strings; x/y need both fields. rows must be true.
Dataset IDs params and script are reserved for ECharts.

Optional color_by_sign: true selects colors by the last bound numeric value's
sign. color_by: [close, open] compares two numeric columns instead; it cannot
combine with an enabled color_by_sign. Neither color mode works with rows.
Names and column types must be verified against actual dataset results.

Inline expressions are strings beginning with "js:". Named scripts are a mapping
inside chart.scripts, with nonempty JavaScript expressions and identifier-like
names (letters, digits, underscore or dollar sign; no leading digit):

~~~yaml
scripts:
  formatter: "(v) => Number(v).toFixed(1)"
~~~

Use {from: script, name: formatter} at the intended option property. Scripts are
restored as expressions by Facetra; ordinary data strings do not become scripts.
Do not add native plot/x/y/average or value fields to an ECharts chart.
The [business](../workspaces/example/charts/Example/ECharts/example_echarts_business.yaml),
[candlestick](../workspaces/example/charts/Example/ECharts/example_echarts_candlestick.yaml)
and [heatmap](../workspaces/example/charts/Example/ECharts/example_echarts_heatmap.yaml)
examples show complete configurations.

The [chart gallery](../workspaces/example/README.md#图表原型库) covers all 23 ECharts
6.1.0 core series. Chord and matrix need ECharts 6+; GL extensions are separate.
The app's bundled SVG renderer loads no remote assets. Offline maps can register
inline fictional GeoJSON in a `js:` expression before the option is applied.

## Validation

Use the [contributor commands](contributing.md#verify-and-submit). Validate the
whole repository so missing data and referenced charts are caught together.
Preview output columns, parameters and rendering in Facetra when available;
offline validation does not prove SQL or JavaScript correctness.

## Tags

Charts accept optional `chart.tags: [股票, 行情]`; dashboards accept optional
`tags: [股票, 分析]` at the document root. Omission means no tags, and old YAML
and cached catalogs remain readable. Tags must be strings of 1–64 characters
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
