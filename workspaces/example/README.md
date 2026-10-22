# 示例工作区 · Example workspace

68 个图表和 6 个看板，涵盖股票行情、经营数据、常用图形与金融技术指标。可从 Discover 导入，在本地查看和编辑。

68 charts and six dashboards covering stock prices, business data, common chart types and financial indicators. Import from Discover to view and edit local copies.

## 使用 · Getting started

1. 在 Discover 中导入本工作区，打开图表或看板；除 HTTP 示例外，全部可离线查看，无需连接。
2. 在「设置 → 通用 → 应用语言」选择简体中文或 English，切换图表与看板的标题、说明和参数标签。数据名称与代码保持原文。
3. 需要调整示例时，打开图表或看板的 YAML 编辑器。

Import this workspace from Discover and open a chart or dashboard. The HTTP examples require internet; the other examples work offline without connections. Choose **Settings → General → App Language** to switch chart and dashboard display text between English and Simplified Chinese. Data names and codes remain as authored. Open the YAML editor to adapt an example.

## 内容 · What's included

| 内容 · Content | 用途 · Purpose |
| --- | --- |
| 行情与月度数据 · Prices and monthly data | 比较股价、均线、成交量和月度均价 · Compare prices, moving averages, volume and monthly average prices |
| [股票分析 · Stock analysis](dashboards/example_dashboard.yaml) | 选择股票与时间窗口，查看行情与成交量 · Choose a stock and time window to explore prices and volume |
| [ECharts 配置示例 · ECharts examples](dashboards/example_echarts_dashboard.yaml) | 价格走势、K 线、收入与利润率、渠道热力图 · Prices, candles, revenue and margin, and a channel heatmap |
| [Mosaic 布局示例 · Mosaic layout](dashboards/example_mosaic_dashboard.yaml) | 宽屏多列排列，窄屏顺序阅读 · A multi-column dashboard that stacks on narrow screens |
| [Vela 金融图表 · Vela financial charts](dashboards/example_vela_dashboard.yaml) | 蜡烛图、成交量、均线、布林带、RSI 与 MACD · Candles, volume, moving averages, Bollinger Bands, RSI and MACD |
| [图表原型库 · Chart Gallery](dashboards/example_chart_gallery.yaml) | 37 个离线图形示例 · 37 offline chart examples |
| [HTML 与 Vega-Lite · Renderer gallery](dashboards/renderer_gallery.yaml) | 地区汇总卡片、报表及 12 种统计图示例 · Regional cards, a report table and 12 statistical chart examples |

## 图表原型库

37 个图形示例均可独立打开，无需参数、连接或网络。

- **Swift Charts**：折线、面积、柱状、饼图、散点、热力图与任务区间；另有数值卡片。
- **ECharts**：常用统计图、层级图、关系图、流向图、地图、仪表盘，以及极坐标、日历与矩阵等示例。

地图中的两个岛屿为虚构区域。任务区间以天为单位；其他示例的数值和单位见各图说明。
弦图与矩阵示例需要内置 ECharts 6 或更新版本的 Facetra。

The gallery contains seven native chart types, a value card and 29 ECharts examples. The two mapped islands are fictional. Task intervals use days; other units are described in each chart. Chord and matrix examples require Facetra with ECharts 6 or later.

## Vela 金融图表

使用同一份 40 个交易日的虚构行情，比较蜡烛图、成交量与技术指标。价格为虚构价格点，成交量为虚构成交单位。
均线周期可通过参数调整；历史不足以计算指标的初始区间留空。不补周末，也不自动重新采样。
小高度卡片仅显示主图；查看完整指标请使用较大的图表区域。图内临时设置不会保存，长期修改请使用 YAML 编辑器。

Compare candles, volume and technical indicators over forty fictional trading days. Prices and volume use fictional units. Adjust moving-average periods with parameters. Initial indicator values remain blank until enough history is available; weekends are not filled and data are not resampled. Small cards show only the main chart. Use a larger view for all indicators, and the YAML editor for saved settings.

需要支持 Vela 金融图表的 Facetra 版本。Requires Facetra with Vela financial charts.

## HTML 与 Vega-Lite · HTML and Vega-Lite

卡片与表格按地区汇总收入和利润。12 个 Vega-Lite 示例包括柱状、折线、堆叠面积、散点、热力图、饼图、直方图、箱线图，以及组合、分面和地区交互筛选。

Cards and a table summarize revenue and profit by region. The twelve Vega-Lite examples include bar, line, stacked area, scatter, heatmap, pie, histogram and boxplot charts, plus combined views, regional facets and an interactive region filter.

需要支持 HTML 和 Vega-Lite 图表的 Facetra 版本。Requires Facetra with HTML and Vega-Lite charts.

## HTTP 示例 · HTTP example

**HTTP · IPv4 分段** 需要联网与本地连接。在连接库创建 Key-Value 连接，别名为 `http_example`，添加 `endpoint` 字段并设为 `https://api.ipify.org`。服务需返回 IPv4 地址；饼图按地址四段数字的相对大小显示，属于图形演示。

**HTTP example · IPv4 segments** requires a network connection and local setup. Create a Key-Value connection with alias `http_example`, add `endpoint` and set it to `https://api.ipify.org`. The service must return IPv4. The pie compares the address's four numeric segments as a chart demonstration.

## 数据与许可 · Data and license

股票行情、经营、OHLCV 与图形示例使用本项目创作的虚构数据，存于 9 份 CSV 及部分图形样本中。经营示例金额以万元为单位；HTML 和 Vega-Lite 使用 2026 年 1–6 月的虚构产品销售数据，收入与利润为演示单位，销量为件。语言切换不改变数值或单位。

Stock, business, OHLCV and gallery data are fictional, held in nine CSV files and chart samples. Business examples use CNY 10,000. HTML and Vega-Lite examples cover January–June 2026 product sales; revenue and profit use demonstration units, and units sold are counts. Changing language does not change values or units.

示例配置与虚构数据采用 [Apache-2.0](../../LICENSE)。连接值仅保存在你的设备上。
Example configurations and fictional data are licensed under [Apache-2.0](../../LICENSE). Connection values stay on your device.


## HTTP 采集示例 · HTTP collection examples

需要支持状态驱动分页、逐项请求及 HTML/XML 提取的 Facetra。旧客户端需先升级。
这些示例联网读取远端数据；除 GitHub REST 与游标示例外，新增示例无需本地连接。

Requires Facetra with state-driven pagination, per-item requests and HTML/XML extraction.
Upgrade older clients before importing these charts. They read remote data; among these
examples, only the GitHub REST and cursor charts need a local connection.

| 图表 · Chart | 内容与范围 · Content and scope |
| --- | --- |
| [角色状态 · Character status](charts/Example/HTTP/example_http_page.yaml) | Rick and Morty API 当前全部页的虚构角色数量，最多 100 页 · Fictional character counts across all current pages, at most 100 pages |
| [商品类别 · Product categories](charts/Example/HTTP/example_http_offset.yaml) | DummyJSON 全部模拟商品，30 件/页，最多 100 页 · All synthetic products, 30 per page, at most 100 pages |
| [公开仓库星标 · Repository stars](charts/Example/HTTP/example_http_links.yaml) | FacetraAPP 公开仓库当前星标，最多 20 页 · Current stars for public repositories, at most 20 pages |
| [三个类别商品 · Three categories](charts/Example/HTTP/example_http_foreach.yaml) | DummyJSON 返回的前三个类别，各类别读取全部商品 · All products in the first three category slugs returned by the service |
| [演示图书评分 · Demo book ratings](charts/Example/HTTP/example_http_html.yaml) | Books to Scrape 前三页、最多 60 本演示图书的随机评分数量 · Random ratings for at most 60 demo books on the first three catalog pages |
| [近期发布条目 · Recent release entries](charts/Example/HTTP/example_http_xml.yaml) | GitHub 当前 Rust Atom 订阅按更新月统计，非完整发布历史 · Current Rust Atom feed grouped by update month; not complete release history |
| [拉取请求状态 · Pull request states](charts/Example/HTTP/example_http_cursor.yaml) | FacetraAPP/Facetra 全部拉取请求当前状态，50 条/页，最多 20 页 · All current pull request states, 50 per page, at most 20 pages |

GitHub REST 与游标示例需在连接库创建别名为 github_example 的 Key-Value 连接，添加 token，
其 GitHub token 需可读取该公开仓库。凭据仅保存在本机，请勿写进 YAML。
GitHub 请求仍受访问限额约束；服务失败时不会显示部分采集结果。
固定范围的图书样本不代表整个目录。订阅仅反映当前保留的条目，不能用于推断完整月度发布量。
接口数据与排列可能变化，配置不会自动保存历史或补回采集中漏掉的记录。

For the GitHub REST and cursor charts, create a Key-Value connection aliased github_example with a token
field containing a GitHub token permitted to read the public repository. Keep it on the
device, outside YAML. GitHub requests remain subject to rate limits; failed collections
do not display partial totals. The book sample covers a fixed part of the catalog. A feed
contains only its retained entries and cannot establish complete monthly release counts.
Remote data/order may change; the examples do not store history or recover missing records.

数据来源：[Rick and Morty API](https://rickandmortyapi.com/documentation)、
[DummyJSON](https://dummyjson.com/docs/products)、
[GitHub API](https://docs.github.com/en/rest)、
[Books to Scrape](https://books.toscrape.com/)。
Books to Scrape 的价格和评分为随机演示数据，没有现实意义。远端数据的权利与使用条件
由各提供方决定，本仓库的 Apache-2.0 许可覆盖示例配置，不授予远端数据的再分发许可。

Sources are linked above. Books to Scrape prices/ratings are random demo values with no
real-world meaning. Providers retain their data rights and terms; this repository's
Apache-2.0 license covers the example configurations and does not relicense remote data.
