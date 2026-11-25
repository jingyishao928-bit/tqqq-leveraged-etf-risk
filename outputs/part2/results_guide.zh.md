# Part 2 结果文件索引

主分析和稳健性分析的表格在 `tables/`，图在 `figures/`。CSV 中无百分号的收益率、波动、回撤和差额通常用小数表示。指标总账明确标注了转换后的单位和汇报写法。

## 主分析表

| CSV 文件 | 用途 |
|---|---|
| part2_daily_paths.csv | 逐日收益、净值、回撤、做多做空损益和损耗 |
| part2_cumulative_path.csv | 含初始交易日的净值序列，可直接绘制历史路径 |
| part2_rolling_metrics.csv | 21 日和 63 日滚动波动、杠杆斜率和损耗 |
| table_part2_performance.csv | 三只 ETF 的收益、波动及最大回撤 |
| table_part2_positions.csv | 每美元初始头寸的最佳、最差与期末损益 |
| table_part2_regime_attribution.csv | 疫情、加息、关税波动期间的路径比较 |
| table_part2_tracking.csv | QQQ 与纳斯达克 100 两种基准下的日度跟踪误差 |
| table_part2_two_day_example.csv | 两日示例，展示每日重置的复利效果 |
| table_part2_holding_period.csv | 每个 1、10 和 21 日窗口的回报及路径差异 |
| table_part2_holding_period_summary.csv | 各持有期偏离与损耗的汇总 |
| table_part2_fee_sensitivity.csv | 净费率、总费率与无费用三种情景 |
| table_part2_benchmark_sensitivity.csv | 正式基准与 QQQ 的杠杆偏离分解 |
| table_part2_key_metrics.csv | 报告和汇报数字的指标总账 |

## 稳健性分析表

| 文件 | 用途 |
|---|---|
| part2_research_disjoint_windows.csv | 使用互不重叠的 21 日窗口，列出收益、波动和重置差额 |
| part2_research_conditional_summary.csv | 按持有期、涨跌范围和波动高低分组的统计结果 |
| part2_research_log_bridge.csv | 把基准的杠杆增长与重置损耗、费率和剩余偏差联系起来 |
| analysis_values.json | 将报告使用的数值打包，供内部自动对照 |

## 图表

| PNG 文件 | 内容 |
|---|---|
| fig_part2_cumulative_returns.png | 三种策略和 QQQ 基准的历史表现 |
| fig_part2_drawdown_and_pnl.png | 回撤与多空头寸损益 |
| fig_part2_return_decomposition.png | 累计收益差额如何拆给重置与估值偏差 |
| fig_part2_rolling_volatility_and_leverage.png | 21 日和 63 日滚动波动与实际杠杆暴露 |
| fig_part2_two_day_example.png | 两日涨跌情形下的复利效果 |
| fig_part2_volatility_decay.png | 波动率损耗与 2025 年 4 月案例 |
| part2_conditional_reset_gap.png | 把 21 日重置差额与方向、波动关联 |
| part2_qqq_normal_qq.png | QQQ 日对数收益与正态分位数的比较 |
| part2_wealth_log.png | 对数纵轴上的 QQQ 基准相关净值路径 |
