# FTShare · 国内宏观

本工作区包含 18 张在线 ECharts 图表，直接查询 [FTShare 国内宏观 API](https://market.ft.tech/gateway/doc/p/1x61fcn7)，不包含 dashboard 或本地数据副本。

18 张图表的标题、说明支持中英文切换。工作区名称、参数标签、坐标轴与接口数据保持原文。

Chart titles and descriptions follow the app's Chinese or English setting.
The workspace name, parameter labels, axes and API data remain as authored.

## 导入

在 Facetra 的「创建 / 加载工作区」选择 GitHub，填写：

- 仓库：`https://github.com/FacetraAPP/Discover`
- Prefix：`workspaces/ftshare`
- 分支：`main`
- GitHub connection：不选择，公开仓库支持匿名读取。

导入后打开「图表」并选择「国内宏观」文件夹。月度图表默认显示最近 24 期已发布指标，GDP 默认显示最近 20 季；使用下拉选项切换常用时间窗口，月度最多 200 期、GDP 最多 100 季。LPR 按月保留最后一次报价。

日度利率图默认使用已经发布数据的固定区间 `2026-08-01`–`2026-08-31`，不是自动滚动到今天。使用日历选择开始与结束日期，结束日期不能早于开始日期。曲线和报价行使用下拉选项，其中 18 家报价行支持搜索。报价行选项以 2026-08-03 的数据为准，可能不覆盖此后的变化；中债默认「中债国债收益率曲线」，SHIBOR 报价默认「中国银行」。每次加载一页，最多 1000 条；较长区间应缩短日期窗口或调整高级参数「页码」，本工作区不自动跨页合并。

## 图表与口径

| Chart ID | 指标 / 文档 | 纵轴单位 |
| --- | --- | --- |
| `ftshare_china_cpi` | [CPI · 同比与环比](https://market.ft.tech/gateway/doc/p/0v982m8z) | % |
| `ftshare_china_gdp` | [GDP · 累计同比](https://market.ft.tech/gateway/doc/p/egodfcdg) | % |
| `ftshare_china_lpr` | [LPR · 贷款市场报价利率](https://market.ft.tech/gateway/doc/p/wg95club) | % |
| `ftshare_china_pmi` | [PMI · 制造业与非制造业](https://market.ft.tech/gateway/doc/p/s4xvqnu0) | 指数点 |
| `ftshare_china_ppi` | [PPI · 同比与环比](https://market.ft.tech/gateway/doc/p/n6lijleg) | % |
| `ftshare_china_fixed_asset` | [固定资产投资 · 同比与环比](https://market.ft.tech/gateway/doc/p/vp2bmxs5) | % |
| `ftshare_china_reserve_ratio` | [存款准备金率](https://market.ft.tech/gateway/doc/p/cl9tjf4p) | % |
| `ftshare_china_industrial` | [工业增加值 · 同比](https://market.ft.tech/gateway/doc/p/2tsc1z6m) | % |
| `ftshare_china_credit` | [新增信贷 · 同比](https://market.ft.tech/gateway/doc/p/89eo4u6b) | % |
| `ftshare_china_retail` | [社会消费品零售 · 同比](https://market.ft.tech/gateway/doc/p/hped3tpp) | % |
| `ftshare_china_tax` | [税收收入 · 同比](https://market.ft.tech/gateway/doc/p/ht6ox0mg) | % |
| `ftshare_china_fiscal` | [财政收入 · 同比](https://market.ft.tech/gateway/doc/p/w515ivba) | % |
| `ftshare_china_money_supply` | [货币供应 · M0/M1/M2 同比](https://market.ft.tech/gateway/doc/p/twl6t7h1) | % |
| `ftshare_china_trade` | [进出口 · 同比](https://market.ft.tech/gateway/doc/p/n6bu5izh) | % |
| `ftshare_china_chinabond` | [中债收益率 · 期限比较](https://market.ft.tech/gateway/doc/p/fubopatp) | % |
| `ftshare_china_shibor` | [SHIBOR · 期限比较](https://market.ft.tech/gateway/doc/p/3jnxyzmy) | % |
| `ftshare_china_shibor_quote` | [SHIBOR · 报价行利率](https://market.ft.tech/gateway/doc/p/optr82sd) | % |
| `ftshare_china_wenzhou` | [温州民间融资 · 综合与分项利率](https://market.ft.tech/gateway/doc/p/e4w9tgm2) | % |

增速、利率与价格指数的同比/环比均以百分比显示，PMI 为指数点。点击图表查看日期和带单位的数值，点击图例可隐藏曲线。日度利率及存在缺报月份的月度指标使用真实时间轴，日期空档不压缩；利率纵轴按数据范围缩放，比较变化时应同时查看刻度。PMI 以 50 为荣枯分界。新增信贷的当月/累计同比使用上下两个独立纵轴，避免当月同比的极端值压平累计走势。GDP 的 Q1/Q2/Q3/Q4 标签分别指年初至该季度的累计数据，不是单季度数据。信贷接口只提供新增信贷，不能视为社会融资规模总量。税收当月同比采用数据源提供的计算值。

这些图表展示增速、利率或指数点，不展示币种与金额单位尚不明确的金额序列。价格指数值与同比、环比增速分别理解。
缺失数据留空、不补零；日期按时间升序展示。

## 可选 FTShare connection

当前国内宏观图表使用公共接口，无需配置连接。完整工作区导入包含可选的 FTShare 连接表单；表单不包含凭据。

如需在个人副本中使用认证接口或服务要求 API Key，在连接库新建 `FTShare<工作区名称>` 类型，添加本工作区别名 `ftshare`，在本机填写：

| 字段 | 用途 |
| --- | --- |
| `endpoint` | API 根地址：`https://market.ft.tech/gateway`，不带末尾 `/` |
| `api_key` | 自己的 FTShare API Key，仅存于本机 Keychain |

为个人副本添加认证时，按 [HTTP 数据源说明](../../docs/chart-yaml.md#http) 编辑对应图表，使用本机连接中的地址，并通过 `FTSHARE_API_KEY` 请求头传递 API Key。
读取本公开仓库无需 GitHub token。

## 来源与许可

配置与说明采用 Apache-2.0。远程指标来自 FTShare 托管数据服务，数据权利、访问额度和使用范围以 FTShare 与原始来源的条款为准；本仓库不再分发服务端数据，也不声称配置许可覆盖远程数据。指标发布时间、源数据缺失和后续修订由服务端决定。公共接口可能限流（HTTP 429），出现错误时稍后刷新。

## 标签

所有图表包含「国内宏观」标签，并按实际指标补充物价、经济增长、利率、财政、贸易等主题和 CPI、GDP、LPR、SHIBOR 等名称。可在发现页或导入后的图表页搜索、组合筛选；标签不改变数据口径。
