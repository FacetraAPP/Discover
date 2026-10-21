# HTML and Vega-Lite Gallery · 渲染器示例

Requires [Facetra PR #78](https://github.com/FacetraAPP/Facetra/pull/78).
Older clients do not recognize `html` or `vega_lite`.

The 36 records in `data/sales.csv` are fictional monthly product sales for
January–June 2026, across two regions and three products. Revenue and profit use
demonstration units; units are counts. No network, credentials or connections
are needed. Values are explicitly cast in SQL; dates retain ISO calendar values.

The gallery contains bar, line, stacked area, scatter, heatmap, pie, histogram,
boxplot, layered, faceted, concatenated and interactive region-filter examples.
`vega_bar` owns the shared source and typed Dataset. Other Vega-Lite charts
reference that Dataset by resource ID. Native Vega-Lite mark/encoding/transform/
composition/params options remain editable YAML. Bindings expand to SQL row objects.

Two HTML examples show regional summary cards and a report table. HTML uses
Mustache escaped placeholders and sections (`{{#rows}}…{{/rows}}`), CSS theme
variables and bound data. Authored JavaScript is unsupported and the document
blocks scripts and network access. SQL owns all aggregation.

Open `renderer_gallery` for the three-tab dashboard. Charts can also be imported
individually; dependency closures retain the provider chart and local CSV.
Titles and Notes support English and Simplified Chinese. Expand Notes to see
Markdown and a Mermaid data-flow diagram. In the chart's table view, select
**Dataset Result** to inspect transformed output and switch back to a source to
compare raw data. Source display settings do not affect the Dataset table.

## 中文

本工作区提供 12 种 Vega-Lite 图表、2 个 HTML 示例与一个三页看板。
数据完全虚构，单位为演示单位；无需连接、凭据或网络。
HTML 仅支持 HTML/CSS 和声明式绑定，不执行自定义 JavaScript。
所有示例依赖 Facetra PR #78 的新渲染器支持。
