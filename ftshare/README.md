# FTShare · 国内宏观

本工作区包含 18 张在线 ECharts 图表，直接查询 [FTShare 国内宏观 API](https://market.ft.tech/gateway/doc/p/1x61fcn7)，不包含 dashboard 或本地数据副本。

## 导入

在 Facetra 的「创建 / 加载工作区」选择 GitHub，填写：

- 仓库：`https://github.com/FacetraAPP/Discover`
- Prefix：`ftshare`
- 分支：`feat/ftshare-china-macro`（PR 合并后使用 `main`）
- GitHub connection：不选择，公开仓库支持匿名读取。

导入后打开「图表」并选择「国内宏观」文件夹。月度图表默认显示最近 60 期，GDP 默认显示最近 20 季；参数可调整至 1–200 期。LPR 原始历史包含按日填充记录，SQL 按月保留最后一次报价，避免重复月份。

日度利率图默认使用已经发布数据的固定区间 `20260801`–`20260831`，不是自动滚动到今天。可以修改开始/结束日期（YYYYMMDD）、曲线名称或报价行；日期结束不能早于开始。每次加载一页，最多 1000 条；较长区间应缩短日期窗口或调整高级参数「页码」，本工作区不自动跨页合并。中债默认「中债国债收益率曲线」，SHIBOR 报价默认「中国银行」，名称必须精确匹配。

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
| `ftshare_china_chinabond` | [中债国债收益率 · 期限比较](https://market.ft.tech/gateway/doc/p/fubopatp) | % |
| `ftshare_china_shibor` | [SHIBOR · 期限比较](https://market.ft.tech/gateway/doc/p/3jnxyzmy) | % |
| `ftshare_china_shibor_quote` | [SHIBOR · 报价行利率](https://market.ft.tech/gateway/doc/p/optr82sd) | % |
| `ftshare_china_wenzhou` | [温州民间融资 · 综合与分项利率](https://market.ft.tech/gateway/doc/p/e4w9tgm2) | % |

增速、利率与价格指数的同比/环比均以百分比显示，PMI 为指数点。GDP 的 Q1/Q2/Q3/Q4 标签分别指年初至该季度的累计数据，不是单季度数据。信贷接口只提供新增信贷，不能视为社会融资规模总量。税收当月同比为服务端计算值。

金额单位、币种在不同接口中可能为空或与文档描述不同，因此这些图表选择同比增速，不擅自把金额当作人民币亿元或美元。`national_cpi`/`ppi` 指数值不混入增速曲线。所有字符串数值用 `TRY_CAST` 转为数值，缺失值保持 null，曲线不跨缺失值连接、不补零。中文月份转换为 YYYY-MM，季度转换为 YYYY-Qn，再按时间升序展示。

CPI、PMI、PPI、信贷、货币供应实际返回 `data.items`；日度利率返回 `data.records`；其余历史序列返回 `data` 数组。信贷、货币供应文档开头曾写 `data.records`，本工作区按在线响应使用 `data.items`。

国内宏观目录中的两种财经日历为事件列表，混合指标和单位，当前没有转换为时序图表。

## 可选 FTShare connection

`connections/ftshare.yaml` 是连接类型的字段定义，随完整工作区导入，仅包含字段名，不包含任何凭据。国内宏观接口在验证时支持匿名请求，所以当前图表不依赖 connection，`requiredConnections` 为空。

如需在个人副本中使用认证接口或服务要求 API Key，在连接库新建 `FTShare<工作区名称>` 类型，添加本工作区别名 `ftshare`，在本机填写：

| 字段 | 用途 |
| --- | --- |
| `endpoint` | API 根地址：`https://market.ft.tech/gateway`，不带末尾 `/` |
| `api_key` | 自己的 FTShare API Key，仅存于本机 Keychain |

然后将需要认证的图表 HTTP source 改为类似下面的配置（其余字段保留）。这一步会让该图表需要本机 `ftshare` connection：

```yaml
url: "{{ connections.ftshare.endpoint }}/api/v1/market/data/economic/china-cpi"
headers:
  FTSHARE_API_KEY: "{{ connections.ftshare.api_key }}"
```

认证请求头与 [官方 Python SDK](https://github.com/FTShare-Lab/FTShare-python-sdk/blob/main/src/ftshare/base.py) 一致。GitHub connection 与 FTShare connection 用途独立；读取公开仓库不需要 GitHub token。

## 来源与许可

配置与说明采用 Apache-2.0。远程指标来自 FTShare 托管数据服务，数据权利、访问额度和使用范围以 FTShare 与原始来源的条款为准；本仓库不再分发服务端数据，也不声称配置许可覆盖远程数据。指标发布时间、源数据缺失和后续修订由服务端决定。公共接口可能限流（HTTP 429），出现错误时稍后刷新。
