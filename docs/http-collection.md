# HTTP collection sources

Requires Facetra with state-driven HTTP pagination, foreach and HTML/XML
extraction. Upgrade clients before importing these examples.
[The application contract](https://github.com/FacetraAPP/Facetra/blob/main/Contracts/charting/v1/http-collection.md)
defines execution and limits. Python validation here checks shapes, bounds,
local references and expression text length. Facetra compiles expressions,
executes requests and checks resulting columns.

## State transitions

~~~yaml
source: http
url: https://example.com/items
params: {cursor: '{{ page.cursor }}'}
pagination:
  initial: {cursor: null}
  records: response.json.items
  next: 'if response.json.next != () { #{cursor: response.json.next} } else { () }'
  max_pages: 100
~~~

initial is an object; request templates read page. After accepting each page's
records, next returns a replacement state object or unit () to stop. Short
or empty pages do not imply termination. A nonterminal state at max_pages is
an error, not a truncated success. Repeated state/request is also an error.
State may contain multiple fields. Inject it into URL, query, headers or nested
JSON/form body. Null query/form substitutions omit fields; JSON null stays typed.

Expressions use strict Rhai expression syntax: arithmetic/comparisons,
short-circuit booleans, .len, .contains(key), indexing, map literals
and if condition { expression } else { expression }. Expressions do not use
template braces. There are no loops, assignments, modules, I/O or dynamic eval.
Scopes are page, item and response; next additionally sees this page's records.
response contains status, headers (lowercase), final url, json, text, links
(parsed Link relations) and extracted (document-level markup fields).
Use url_join(response.url, response.json.next) for body-relative URLs.
Missing paths fail unless explicitly handled. The application bounds expression
source length, computation, depth and result size.

[Page number](../workspaces/example/charts/Example/HTTP/example_http_page.yaml),
[offset](../workspaces/example/charts/Example/HTTP/example_http_offset.yaml),
[Link URL](../workspaces/example/charts/Example/HTTP/example_http_links.yaml)
and [GraphQL cursor](../workspaces/example/charts/Example/HTTP/example_http_cursor.yaml)
examples share this executor. GraphQL's first cursor is explicit null; later
cursors are opaque values.

## Per-item acquisition

~~~yaml
depends_on: [categories]
foreach: {source: categories, max_items: 200, include_item: true}
params: {id: '{{ item.id }}'}
~~~

The upstream must be an explicit direct dependency. Each normalized record
becomes item; pagination state resets per item. include_item appends the original
record as _item (conflicting fields fail). Primitive arrays become records
with a value field, as in the [category example](../workspaces/example/charts/Example/HTTP/example_http_foreach.yaml).
An empty list sends no child requests. Dependency cycles through either
depends_on or ref aliases are invalid. Ordinary HTTP JSON templates read
the original response; collection modes expose the merged record array.

## Markup

HTML uses CSS row/field selectors. XML uses XPath 1.0 and explicit namespace
aliases, including an alias for Atom's default namespace.

~~~yaml
format: html
extract:
  rows: article.product_pod
  fields:
    title: {selector: h3 a, attribute: title}
  context:
    next: {selector: '.pager .next a', attribute: href, required: false, resolve_url: true}
~~~

Fields accept selector, attribute, all, required, json and resolve_url.
Required defaults true. Optional missing values are null (or [] with all).
json parses embedded JSON/JSON-LD without executing scripts; resolve_url uses
the final response URL. Context fields are selected at document scope and
exposed as response.extracted. Ordinary fields are trimmed strings; use SQL
for explicit numeric/date conversion. Markup must be UTF-8, is bounded to
8 MiB per response, and cannot load scripts/resources or XML DTDs/entities.
See the [book sample](../workspaces/example/charts/Example/HTTP/example_http_html.yaml)
and [Atom example](../workspaces/example/charts/Example/HTTP/example_http_xml.yaml).

## Bounds and failures

limits defaults: max_requests 1000, max_bytes 104857600, max_rows 100000,
timeout_ms 60000. All items/pages share that acquisition budget; retries and
redirects count too. Upstream acquisitions have their own limits. Limits cannot
be bypassed by expressions. Iteration is sequential, preserves input order and
stays on the initial HTTPS origin.

retry is opt-in: max_attempts (default 3, at most 5), delay_ms (default 250,
at most 10000), retry_post (default false). GET can retry transport failures
and 429/502/503/504, honoring Retry-After. POST needs explicit retry_post: true
asserting safe replay. A retried page is appended once after success.

Failed collections publish no partial result. Refresh restarts them; there are
no persistent checkpoints or accumulated history. A complete local result does
not make the remote API transactional. Prefer stable ordering, server snapshots
or cursors when rows can change. SQL dedup cannot recover skipped rows.
State sample windows, service limits and incomplete-feed coverage in both
translations; do not describe a bounded sample as the whole remote dataset.
