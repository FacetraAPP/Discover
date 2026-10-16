# Chinese and English display text

Charting Contract v1 supports a resource-local message catalog and explicit display
references. This pre-release extension requires the application support in
[Facetra PR #61](https://github.com/FacetraAPP/Facetra/pull/61). Older development
clients cannot read these new fields. Existing fixed-string resources still work. The top-level `i18n` block is optional,
not a business parameter: omit it to keep titles and labels fixed across languages.
Only explicit references require a catalog and an existing key.

The [example workspace](../workspaces/example/README.md) includes both `zh-Hans`
and `en` translations for every chart and dashboard. Import it and change
**Settings → General → App Language** to see the same resources in either language.

## Complete chart

```yaml
i18n:
  defaultLocale: zh-Hans
  messages:
    title: {zh-Hans: 月度收入, en: Monthly revenue}
    notes: {zh-Hans: 虚构销售数据，单位为元。, en: Fictional sales data in yuan.}
    months: {zh-Hans: 月数, en: Months}
    revenue: {zh-Hans: 收入（元）, en: Revenue (yuan)}
metadata:
  id: sales
  title: {i18n: title}
  notes: {i18n: notes}
params:
  - {name: months, type: integer, default: 12, minimum: 1, label: {i18n: months}}
sources:
  sales: {source: duckdb, file: data/sales.csv}
dataset:
  id: sales
  sources: [{id: raw, ref: '#/sources/sales'}]
  sql: SELECT month, CAST(revenue AS DOUBLE) AS revenue FROM raw ORDER BY month LIMIT $months
chart:
  dataset: sales
  renderer: echarts
  option:
    legend: {}
    tooltip: {trigger: axis}
    xAxis: {type: category, data: {from: sales, field: month}}
    yAxis: {type: value, name: {i18n: revenue}}
    series:
      - id: revenue
        name: {i18n: revenue}
        type: bar
        data: {from: sales, field: revenue}
```

This file requires `data/sales.csv` with numeric `revenue` and text `month` columns.
For a complete existing recipe, inspect the [business chart](../workspaces/example/charts/Example/ECharts/example_echarts_business.yaml).

## Supported locations and fallback

- `metadata.title`, `metadata.notes`, `params[].label` and Dashboard `tabs[].title`
  accept a fixed string or an object containing only `i18n: key`.
- ECharts option display positions accept the same object: series names, axis
  names/category labels, legend entries, radar indicators and tree labels, for example.
  Use references only where the renderer accepts text. Vela's title, notes and
  parameter labels support localization; its column/indicator configuration stays stable.
- Each Chart or Dashboard owns its `i18n` table. A panel chart does not inherit the
  Dashboard's translations, even when both use a key named `title`.
- Keys contain 1–120 ASCII letters, digits, underscores, dots or hyphens. Locale
  tags use hyphens, such as `en`, `en-GB`, `zh-Hans` and `zh-Hant-TW`.
  Matching ignores case; duplicate locale spellings that differ only by case fail validation.
- Every key must have a nonblank translation in `defaultLocale`. Other locales
  may be omitted. The app tries the requested tag, removes trailing subtags to
  try parents, then uses that message's declared default. `zh-Hans` and `zh-Hant`
  do not match one another, except through an explicitly selected default fallback.
- Unknown keys, malformed references, missing defaults and invalid locale maps
  fail offline validation with the resource file and field context.

## Keep data and rendering identities stable

Resource IDs, parameter names/values, SQL, data columns, dates, ticker symbols,
connection aliases and source/dataset references are independent of language.
Ordinary strings remain fixed; the app does not translate data values or scan
SQL, HTTP bodies or JavaScript source for Chinese words.

For ECharts, provide stable series IDs. When an authored legend list repeats a
translated series name, reference the same message in both places. The same
applies to static theme-river data and its legend. A translated node name must
not break a link targeting an old name; use stable IDs or consistent references.
The examples retain language-neutral A/B/C/D and fictional geographic identifiers.

Avoid hard-coded Chinese in formatters. Use a localized string template, a
locale-neutral date representation, or the renderer's default tooltip with a
translated series name/unit. Do not put JavaScript in translations: a resolved
string beginning with `js:` stays text and is never compiled as a script.
Data binding results are also never parsed again as references or scripts.

Switching app language retains loaded data, parameter drafts and chart
interactions. Saving or copying keeps the original references and every locale.
Changing language does not convert currencies, rescale values or alter units.

## Catalog and portable imports

Catalog `title` and `description` remain default-language strings. The publisher
also emits `localizations: {locale: {title, description}}` from each resource's
title/notes references, resolving each field with the same parent/default fallback
as Facetra. Discover can switch summaries immediately using one catalog download,
including offline browsing; it does not have to fetch every YAML definition first.
The downloadable YAML retains all authored references and translations.

Workspace manifests keep their original string fields and may provide an explicit
summary map, copied into the catalog and preserved by portable imports:

```yaml
title: 示例 · Examples
description: Default workspace description
localizations:
  zh-Hans:
    title: 示例
    description: 中文工作区说明
  en:
    title: Examples
    description: English workspace description
```

Locale tags follow the same rules as resource messages. Each summary requires a
nonblank title; description is optional and can be empty. Unsupported languages
fall back to the original strings. Workspace IDs, paths and device-local names
stay independent of the displayed language. This optional format requires
[Facetra PR #63](https://github.com/FacetraAPP/Facetra/pull/63) for display support.
Older apps ignore the summary map and continue to use the original strings.

Both public workspaces and all chart/dashboard summaries include Chinese and
English. FTShare's title/notes translations cover Discover and imported resource
headings; its parameter labels, axes and API data remain authored text. README
files are author-supplied documents and are not automatically translated.

Run the [contributor checks](contributing.md#verify-and-submit). Offline validation
does not execute a formatter or render the chart; test both languages in Facetra
when changing display code and record the tested scope in the PR.
