# 示例工作区 · Example workspace

这个工作区包含 8 个图表、3 个看板和 4 份 CSV 数据，可以在 Facetra 的 Discover 中导入为可编辑的本地副本。

股票行情、销售与 OHLCV 数据均为虚构示例。工作区不包含任何凭据。

## 内容

- **行情与月度数据**：股票价格、成交量和月度统计，展示本地 CSV、SQL 与图表间数据引用。
- **HTTP**：通过 HTTP 请求展示 IP 分布，演示连接别名与请求模板。
- **ECharts**：价格走势、K 线、热力图与经营数据。
- **看板**：常规、ECharts 与 Mosaic 布局，可以查看并编辑各分页的图表组合。

## 使用

1. 在 Discover 中选择本工作区并点击 **导入**。
2. 打开导入工作区的图表或看板；本地 CSV 示例可以直接查看。
3. 使用 HTTP 示例前，在连接库中创建一个 Key-Value 连接，设置别名 `http_example`，添加字段 `endpoint`，值为 `https://api.ipify.org`。

连接值仅保存在你的设备上。所有图表、看板和本地文件引用都位于本工作区内。

## 文件

工作区信息存储在 [workspace.yaml](workspace.yaml)，图表、看板和数据分别位于 `charts/`、`dashboards/` 与 `data/`。你可以编辑本文件，为工作区补充用途和使用说明；Facetra 的工作区菜单与 Discover 详情会显示这些 Markdown 内容。

## License

Apache-2.0，详见 [仓库许可证](../LICENSE)。
