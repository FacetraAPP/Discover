# 示例工作区 · Example workspace

这个工作区包含 47 个图表、5 个看板和 8 份 CSV 数据，可以在 Facetra 的 Discover 中导入为可编辑的本地副本。

股票行情、销售与 OHLCV 数据均为虚构示例。工作区不包含任何凭据。

All 47 charts and five dashboards include Chinese and English display text. Stock prices, sales and OHLCV
values are fictional; no credentials are included.

## 中英切换 · Chinese and English

导入后，在 Facetra「设置 → 通用 → 应用语言」选择简体中文或 English，图表标题、说明、参数标签、
看板分页及 ECharts 业务文案会随之切换。每份 YAML 自带 `i18n.messages` 文案表，显示位置使用
`{i18n: key}`；缺少某种语言时回退到 `defaultLocale: zh-Hans`。资源 ID、SQL、数据列和参数值不参与翻译。

After importing, choose **Settings → General → App Language → English / 简体中文**. Titles, notes,
parameter labels, dashboard tabs and ECharts business labels follow that choice. Each resource carries
its own translation catalog and falls back to Simplified Chinese. IDs, queries, data fields, ticker
symbols, metric codes and fictional sample identifiers remain stable. Language changes reuse loaded data
and preserve chart interactions and parameter drafts.

需要包含 [Facetra PR #61](https://github.com/FacetraAPP/Facetra/pull/61) 多语言支持的应用版本。
This content requires the application support in Facetra PR #61; older development builds cannot read
the new references. See the [authoring guide](../../docs/localization.md) for complete YAML syntax.

## English guide

Import **Examples** from Discover, then open a chart or dashboard. The 37 prototypes in **Chart Gallery**
are completely offline and require no parameters or connections. They cover seven Swift Charts marks,
Facetra's value card, all 23 core ECharts 6.1.0 series and six additional variants or coordinate systems.
The stock, business, OHLCV and gallery CSV files contain small fictional datasets licensed under Apache-2.0.

**Stock analysis** demonstrates shared parameters and chart-to-chart source/dataset references.
**ECharts · Configuration examples** combines prices, candlesticks, revenue/margin and a monthly channel
heatmap. **Mosaic · Layout examples** demonstrates wide grid layouts and narrow stacked cards.
**Vela · OHLCV and technical indicators** compares candles and volume with moving averages, Bollinger
Bands, RSI and MACD using the same forty trading days. Prices and volume use fictional units; business
amounts are in units of CNY 10,000. The same numeric values and units apply in both languages.

Only **HTTP example · IPv4 segments** needs a local Key-Value connection: assign alias `http_example`,
add an `endpoint` field and set it to `https://api.ipify.org`. This service must return an IPv4 address.
Connection values stay on your device. All resource and local-data references remain within this workspace.

Open a chart's YAML editor to copy or adapt its recipe. Files under `charts/` and `dashboards/` keep
complete translations when copied; `data/` holds the CSV assets. Edit this README to customize the
workspace guide shown in Facetra. Fixed data names and category codes are not automatically translated.

## 图表原型库

[图表原型看板](dashboards/example_chart_gallery.yaml) 包含 **37 个新增原型**，全部无需参数、连接或网络。打开图表的「编辑 YAML」即可复制配置；重点是 `chart` 区块。

Swift Charts 按 Apple 文档的 **7 种基础 Mark** 分类：AreaMark、LineMark、PointMark、RectangleMark、RuleMark、BarMark、SectorMark。
向量化 Plot 是这些 Mark 的批量 API，并非额外图形类别；iOS 26+ 的 Chart3D/SurfacePlot 不在本次兼容 iOS 17 的 YAML 原生接口范围。
另有 Facetra 的 value 数值卡片原型，它不属于 Swift Charts。

ECharts 固定到 **6.1.0**，覆盖 **23 种核心 series**；另提供面积、环形、柱线组合、极坐标、日历、matrix 六个原型。
GL 3D、GL 流场、第三方插件和在线地图底图需要独立渲染扩展，不属于核心离线 SVG 原型库。

| 引擎 | 原型（每个名称对应独立 YAML） |
| --- | --- |
| Swift Charts | line、area、bar、pie、scatter、heatmap、rule；另有 value |
| ECharts 核心 | line、bar、pie、scatter、effectScatter、radar、tree、treemap、sunburst、boxplot、candlestick、heatmap、map、lines、parallel、graph、sankey、funnel、gauge、pictorialBar、themeRiver、custom、chord |
| ECharts 变体/坐标 | area、doughnut、mixed、polar、calendar、matrix |

新增文件在 `charts/Example/Gallery/SwiftCharts/` 和 `charts/Example/Gallery/ECharts/`。图表 ID 采用 `example_gallery_<swift|echarts>_<类型>`。
`gallery-categories.csv` 只有 4 行，`gallery-scatter.csv` 5 行、`gallery-heatmap.csv` 6 行、`gallery-intervals.csv` 3 行；均为本项目创作的虚构数据（Apache-2.0）。数值单位、K 线顺序和区间含义写在各图 notes 中。
层级、网络、箱线图等结构化样本直接内嵌 `chart.option`，共享小 CSV 作为可执行 dataset；无需外部资产。
地图使用本项目创作的两个虚构岛屿 GeoJSON，通过内嵌表达式 `echarts.registerMap` 注册，不代表真实地理区域。
自定义图使用可复制的 `renderItem` 表达式，矩形裁剪在绘图区内。
散点使用真实数值 X 轴；原生热力图以 `chart.color` 绑定颜色；原生区间以 `chart.x_end` 绑定终点。这三类原生配置需要支持相应字段的 Facetra 版本。
弦图与 matrix 需要 Facetra 内置 ECharts 6+。

来源：[Apple Swift Charts](https://developer.apple.com/documentation/charts)、[ECharts 官方示例](https://echarts.apache.org/examples/en/index.html)、[ECharts 6.1.0](https://github.com/apache/echarts/releases/tag/6.1.0)。

## 内容

- **行情与月度数据**：股票价格、成交量和月度统计，展示本地 CSV、SQL 与图表间数据引用。
- **HTTP**：通过 HTTP 请求展示 IP 分布，演示连接别名与请求模板。
- **ECharts**：价格走势、K 线、热力图与经营数据。
- **Vela**：[OHLCV 蜡烛图](charts/Example/Vela/example_vela_candlestick.yaml)与[技术指标](charts/Example/Vela/example_vela_indicators.yaml)，共享已有的 40 日虚构 `echarts-ohlcv.csv`，无需新增数据或连接。
- **看板**：常规、ECharts 与 Mosaic 布局，可以查看并编辑各分页的图表组合。

## Vela 金融图表

[Vela · OHLCV 与技术指标](dashboards/example_vela_dashboard.yaml)看板分两页：基础蜡烛图展示开高低收与成交量；技术指标页展示 SMA、EMA、布林带、RSI 与 MACD，SMA 周期显式绑定看板参数。价格单位为虚构价格点，成交量为虚构成交单位。

需要支持 `renderer: vela` 的 Facetra 版本（应用支持见 [Facetra PR #51](https://github.com/FacetraAPP/Facetra/pull/51)）。数据先由 SQL 转成日期与数值列，再交给离线 Vela 计算指标；40 行历史的预热期会保留空值。`timeframe: 1d` 设置日线刻度，不重采样、不补周末。窄屏可查看完整副图，小高度卡片只显示主图指标。

扩展时可在 `chart.option.indicators` 添加 Vela 内置类型，`inputs` 配置周期、价格来源及颜色，也可绑定普通参数。修改 YAML 才会持久保存；图内临时设置不会回写文件。完整字段见 [Vela 配置](../../docs/chart-yaml.md#vela-ohlcv)。

## 使用

工作区本身无需连接；只有保留的 HTTP 演示单独需要 `http_example` 连接，图表原型看板完全离线。

1. 在 Discover 中选择本工作区并点击 **导入**。
2. 打开导入工作区的图表或看板；本地 CSV 示例可以直接查看。
3. 使用 HTTP 示例前，在连接库中创建一个 Key-Value 连接，设置别名 `http_example`，添加字段 `endpoint`，值为 `https://api.ipify.org`。

连接值仅保存在你的设备上。所有图表、看板和本地文件引用都位于本工作区内。

## 文件

工作区信息存储在 [workspace.yaml](workspace.yaml)，图表、看板和数据分别位于 `charts/`、`dashboards/` 与 `data/`。你可以编辑本文件，为工作区补充用途和使用说明；Facetra 的工作区菜单与 Discover 详情会显示这些 Markdown 内容。

## License

Apache-2.0，详见 [仓库许可证](../../LICENSE)。

## 标签

图表和看板按股票行情、经营、网络与布局标记主题，并补充均线、成交量、K线、热力图等内容标签。ECharts 图表也带有 ECharts 标签；标签在导入后保留。
