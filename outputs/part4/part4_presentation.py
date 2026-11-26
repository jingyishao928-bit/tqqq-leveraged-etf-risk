"""Write slide bullets, speaker cues and the Chinese handoff from verified estimates."""

from pathlib import Path

import pandas as pd

from part4_analysis import BASE_CASE, LONG_INVERSE, MAIN_MODEL, SHORT_TQQQ


def write_summary(output: Path, settings, inputs: pd.DataFrame, risk: pd.DataFrame,
                  multipliers: pd.DataFrame, phases: pd.DataFrame, conditional: pd.DataFrame,
                  inverse: pd.DataFrame, episodes: pd.DataFrame, audit: pd.DataFrame) -> None:
    """Write the English presentation and Chinese audit from the same tables as the charts."""
    days = settings.days
    risk99 = risk.query("case == @MAIN_MODEL and confidence == 0.99")
    tail = risk99.query("asset == 'TQQQ' and horizon_days == @days").set_index("position")
    tqqq_long, tqqq_short = tail.loc["Long"], tail.loc["Short"]
    qqq = risk99.query("asset == 'QQQ' and horizon_days == @days").set_index("position")
    qqq_long, qqq_short = qqq.loc["Long"], qqq.loc["Short"]
    ratios = multipliers.query("case == @MAIN_MODEL and confidence == 0.99")
    es_1 = ratios.query("horizon_days == 1").set_index("position").es_multiple
    es_h = ratios.query("horizon_days == @days").set_index("position").es_multiple
    scenarios = conditional.query(
        "asset == 'TQQQ' and horizon_days == @days and confidence == 0.99"
    ).pivot(index="case", columns="position", values="es_loss")
    historical = phases.pivot(index="regime", columns="asset", values="max_drawdown_loss")
    selloff = historical.loc["COVID sell-off"]
    rate_hikes = historical.loc["Rate-hike bear market", "TQQQ"]
    upmarket = phases.query("regime == '2021 up market' and asset == 'QQQ'").iloc[0]
    whole_history = phases.query("regime == 'Full sample' and asset == 'QQQ'").iloc[0]
    calm_label = ("低波动上涨阶段" if upmarket.cumulative_return > 0.0 and
                  upmarket.annualized_volatility < whole_history.annualized_volatility
                  else "上涨阶段候选")
    sim = inverse.query("model == @MAIN_MODEL and cost_basis == @BASE_CASE and "
                        "horizon_days == @days and confidence == 0.99").set_index("position")
    short, inverse_long = sim.loc[SHORT_TQQQ], sim.loc[LONG_INVERSE]
    april = episodes.set_index("regime").loc["April tariff volatility"]
    metrics = audit.iloc[0]
    source = inputs.set_index("model").loc[MAIN_MODEL]
    gap = metrics.shared_minus_notebook
    if pd.notna(metrics.notebook_published_loss):
        published_display = f"{metrics.notebook_published_loss:.12%}"
        published_gap = (f"{metrics.shared_minus_published * 100:+.10f} 个百分点，"
                         f"{metrics.shared_minus_published * 1e4:+.8f} bp")
    else:
        published_display = "原表缺失"
        published_gap = "原表缺失"
    ranking = "short" if tqqq_short.es_loss > tqqq_long.es_loss else "long"
    tail_counts = f"{int(tqqq_long.tail_observations)} long and {int(tqqq_short.tail_observations)} short"
    baseline_sources = "、".join(f"{row.model}（{row.source}）" for row in inputs.itertuples(index=False))

    markdown = f"""# Part 4 — Risk results

## English slide bullets and speaker cues

Each slide has three short slide bullets and cues for roughly one minute of spoken delivery.

### Slide 1 — How risk changes with the holding period

[Figure 1](figures/fig01_risk_by_horizon.png) · Course Chapter 7, slides 54–55

- Full revaluation on {settings.paths:,} shared QQQ paths
- 99% sample ES multiples at 1 day of {es_1["Long"]:.2f}× long and {es_1["Short"]:.2f}× short
- At {days} days, {es_h["Long"]:.2f}× long and {es_h["Short"]:.2f}× short

**Speaker cues**

- Part 3 gave us {settings.paths:,} simulated paths for QQQ. I applied TQQQ's daily reset rule to each path, then valued both funds at day 1, 10 and {days}. We start each position at one dollar of exposure and rank its losses, just as in the course's Monte Carlo VaR example.
- Start with the dotted 3× line. The one-day ES multiples are close to three on both sides. At {days} days, long TQQQ has sample ES of {tqqq_long.es_loss:.1%}, compared with {qqq_long.es_loss:.1%} for long QQQ. Short TQQQ reaches {tqqq_short.es_loss:.1%}, against {qqq_short.es_loss:.1%} for short QQQ.
- Daily rebalancing changes how gains and losses compound. The next slide shows where the long and short results come from.

### Slide 2 — The two tails of one-month TQQQ risk

[Figure 2](figures/fig02_tqqq_loss_tails.png) · Course Chapters 1 and 5

- Long TQQQ 99% VaR {tqqq_long.var_loss:.1%}, sample ES {tqqq_long.es_loss:.1%}
- Short TQQQ 99% VaR {tqqq_short.var_loss:.1%}, sample ES {tqqq_short.es_loss:.1%}
- The {ranking} position has the larger sample ES

**Speaker cues**

- Focus on {days}-day TQQQ losses. The dashed lines mark the 99% VaR for each position. The shaded observations form the sample ES. VaR gives us the loss threshold, and ES tells us how large the losses were once we were in that tail.
- The long position loses when TQQQ falls, and its loss stops at the amount invested. A fixed-share short loses when TQQQ rises. The gap between its VaR of {tqqq_short.var_loss:.1%} and its sample ES of {tqqq_short.es_loss:.1%} shows why the threshold alone gives an incomplete picture.
- These ES values summarize the simulated sample. The next question is how that tail changes when the market starts out more volatile.

### Slide 3 — Historical stress and initial volatility

[Figure 3](figures/fig03_volatility_scenarios.png) · Course Chapter 5, slides 40–45 and 56–57

- COVID sell-off drawdown of {selloff["TQQQ"]:.1%} for TQQQ and {selloff["QQQ"]:.1%} for QQQ
- GARCH-t initial QQQ volatility at 15%, 25% and 45% annualized
- Short TQQQ sample ES rises from {scenarios.loc["Calm", "Short"]:.1%} to {scenarios.loc["Turbulent", "Short"]:.1%}

| Annualized initial QQQ volatility | Long TQQQ 99% sample ES | Short TQQQ 99% sample ES |
|---|---:|---:|
| 15% | {scenarios.loc["Calm", "Long"]:.2%} | {scenarios.loc["Calm", "Short"]:.2%} |
| 25% | {scenarios.loc["Normal", "Long"]:.2%} | {scenarios.loc["Normal", "Short"]:.2%} |
| 45% (high-volatility scenario) | {scenarios.loc["Turbulent", "Long"]:.2%} | {scenarios.loc["Turbulent", "Short"]:.2%} |

**Speaker cues**

- On the left, two historical stress episodes stand out. TQQQ drew down about {selloff["TQQQ"]:.0%} in the acute 2020 COVID sell-off. The 2022 rate-hike cycle reached the deepest drawdown shown, about {rate_hikes:.0%}. Market direction and volatility both shape those drawdowns.
- On the right, we use a one-factor sensitivity. We hold the model and shocks fixed and start QQQ volatility at 15%, 25% or 45% annualized. At 25%, sample ES is {scenarios.loc["Normal", "Long"]:.2%} long and {scenarios.loc["Normal", "Short"]:.2%} short.
- Across the calm and turbulent settings, long TQQQ sample ES moves from {scenarios.loc["Calm", "Long"]:.1%} to {scenarios.loc["Turbulent", "Long"]:.1%}. The short moves from {scenarios.loc["Calm", "Short"]:.1%} to {scenarios.loc["Turbulent", "Short"]:.1%}, about {scenarios.loc["Turbulent", "Short"] / scenarios.loc["Calm", "Short"]:.1f} times its calm value.

### Slide 4 — Reverse stress test for a bearish position

[Figure 4](figures/fig04_inverse_reverse_stress.png) · Course Chapter 5, slide 58

- Short TQQQ, excluding borrow fees. Loss >50% in {short.prob_loss_gt_50:.2%} of paths. Loss >100% in {short.prob_loss_gt_100:.2%}. Maximum sample loss {short.max_sample_loss:.1%}.
- Long ideal −3×. Loss >50% in {inverse_long.prob_loss_gt_50:.2%} of paths. Loss >100% in {inverse_long.prob_loss_gt_100:.2%}. Maximum sample loss {inverse_long.max_sample_loss:.1%}.
- A fixed-share short reaches a 100% loss when TQQQ doubles.

**Speaker cues**

- When does a fixed-share TQQQ short lose its entire initial notional? When TQQQ doubles. The table shows how often the {days}-day paths exceeded losses of 50% and 100%, and the largest loss observed.
- The curves cross near a 38% loss threshold. Smaller thresholds are crossed more often by the inverse position, consistent with daily-reset volatility drag. At larger thresholds, the fixed-share short overtakes it. Short losses have no upper bound.
- The short exceeded 100% in {int(short.count_loss_gt_100)} paths, excluding borrow fees. The inverse position can lose up to the amount invested. Part 5 now takes up forecast validation and position limits.

## Q&A backup

**Why is the 45% scenario's ES slightly lower than the forecast baseline?**

> The forecast baseline was already at {source.annual_volatility:.2%} annualized volatility. On this slide, we hold the shocks fixed across the three scenarios, so the comparison to focus on is how risk changes from 15% to 25% to 45%.

If asked about the exact difference, the Part 3 forecast starts slightly above 45% and uses a separate set of simulated shocks. The three scenario points share the same shocks. The small differences in the refitted GARCH parameters have a negligible effect on ES.

**Can you give a historical example of the two bearish positions diverging?**

> In April 2025, QQQ ended up {april.qqq_return:.1%}, while the TQQQ short returned {april.short_tqqq_return:+.1%} and long SQQQ returned {april.long_sqqq_return:+.1%}.

## 中文对接说明

### 数据、模型与计量口径

- Part 1 的冻结样本有 {int(source.historical_rows):,} 个共同日收益，从 {source.estimation_start} 到 {source.as_of}。输入按 Part 1 清单核验 SHA-256，兼容 Windows 和 Linux 的换行格式。QQQ 是 Part 3 的建模标的和 Part 4 的 1× 基准。NDX 是基金目标对应的指数，TQQQ 与 SQQQ 历史收益使用复权价格。
- Part 2 已做净值、回撤和固定股数持仓比较。延用它的 COVID 抛售、COVID 反弹、2022 加息、2025 年 4 月关税四个历史阶段。另加 2021 作为{calm_label}，该年 QQQ 复合收益 {upmarket.cumulative_return:+.1%}，年化实现波动 {upmarket.annualized_volatility:.1%}，全样本是 {whole_history.annualized_volatility:.1%}。每个阶段以前一交易日收盘为净值 1，最大回撤以正的损失比例报告。
- 基准模拟来源为 {baseline_sources}。每组 {settings.paths:,} 条路径取前 1／10／{days} 个交易日，置信度为 95%／99%，种子为 {settings.seed}。日对数收益先转为日简单收益，再按每日杠杆复利，基金净值下限为零。Part 3 估计的 TQQQ 综合日拖累为 {source.tqqq_daily_drag:.9%}，涵盖历史上相对 3× QQQ 的综合差额。QQQ 路径已由该 ETF 的实际收益校准。
- 15%／25%／45% 情景在原上传中只有做多的两个分位数。Part 4 按相同冻结数据和同一 Student-t GARCH(1,1) 规格重新拟合。三档情景固定模型和随机冲击，只改变起始波动率。Part 3 基准从 {source.annual_volatility:.2%} 年化初始波动率出发，沿用原上传的另一批随机冲击。重新拟合的全精度参数存在微小差异，对 ES 的影响可忽略。
- 模拟反向产品是同一路径上的理想 −3×，日成本为零。主比较保留原 TQQQ 日拖累，另有双边零拖累敏感性。历史对照使用真实 SQQQ。模拟和历史做空均按固定初始股数标记损益，**excluding borrow fees**，亦未建模保证金强平。阈值是期末损失严格超过初始名义金额 50% 或 100%。样本最大值是观察到的期末损失。历史滚动窗口重叠，频率是样本描述统计。
- 课上可用 2025 年 4 月作震荡例子。QQQ 累计 {april.qqq_return:+.2%}，实际做空 TQQQ 损益 {april.short_tqqq_return:+.2%}，实际做多 SQQQ 损益 {april.long_sqqq_return:+.2%}。完整历史阶段和两条理想路径的收益见下方交接表。

### 21 日做多 99% VaR 口径核对

| 算法 | GARCH-t 做多 TQQQ 21 日 99% VaR（正损失） |
|---|---:|
| 共用 `risk.py`，损失最近秩 | {metrics.shared_var_loss:.12%} |
| Notebook，收益 1% 线性插值后取负号 | {metrics.notebook_recomputed_loss:.12%} |
| Part 3 已上传原表，收益分位数取负号 | {published_display} |
| 共用函数值减 Notebook 重算值 | {gap * 100:+.10f} 个百分点，{gap * 1e4:+.8f} bp |
| 共用函数值减 Part 3 已上传原表 | {published_gap} |

共用 ES 是所有损失大于或等于 VaR 的均值。该规则保留阈值上的观测与并列值，基准主模型的 21 日 99% ES 实际样本数为 {tail_counts}。短历史阶段（例如 23 个日收益的疫情抛售）应结合尾部观测数读数。按课件 Chapter 6 的有限均值条件，未截断 Student-t 对数右尾在指数化后使固定股数做空价格的理论 ES 发散。表格及图中 GARCH-t ES 是有限模拟样本统计，GBM 和历史 bootstrap 提供不同尾部假设的对照。

### 给 Part 5 的 CSV

所有持仓按初始 USD 1 的名义金额归一化。表内收益、损失、置信度、频率和波动率均为小数，0.50 表示 50%。倍数无量纲，日期是纽约交易日标签。正式回测应在各历史预测时点用当时可获得的数据重新估计，Part 4 的汇总风险以 {source.as_of} 为样本截止日。同名 DTA 也提供对应数据。

| 文件 | 内容 |
|---|---|
| [Baseline risk](tables/part4_base_var_es.csv) | 3 模型、2 产品、2 方向、3 持有期、2 置信度 |
| [Risk multipliers](tables/part4_risk_multipliers.csv) | 相同模型、方向、持有期和置信度下的 TQQQ／QQQ 比值 |
| [Historical regimes](tables/part4_historical_regimes.csv) · [Historical VaR and ES](tables/part4_historical_var_es.csv) | 阶段收益、波动率、回撤和日度多空 VaR／ES、尾部计数 |
| [Conditional volatility](tables/part4_volatility_scenarios.csv) | 三档初始波动率下的完整 VaR／ES |
| [Short versus inverse](tables/part4_inverse_comparison.csv) · [Historical episodes](tables/part4_inverse_episodes.csv) | 多持有期模拟和历史比较、阈值计数、样本最大亏损、历史阶段损益 |
| [Quantile audit](tables/part4_quantile_audit.csv) · [Input provenance](tables/part4_simulation_inputs.csv) | 分位数对账、样本日期、路径来源、种子和输入哈希 |

### 复现

在仓库根目录、安装 `requirements.txt` 后运行 `python outputs/part4/part4_risk_results.py`。脚本读取本地冻结数据，下载步骤不参与运行。可用 `--output-dir` 指向临时输出目录作复核。金融口径测试用 `python -m unittest discover -s outputs/part4 -v` 运行。

全组整合事项。在原始提交 `3896ef6` 上，`tests/test_stata_exports.py` 会报告 Part 3 的八个 CSV 缺少同名 DTA。启用 Windows 自动换行转换时，Part 2 的原始字节哈希检查也会报错。Part 4 在自身目录生成并核验 CSV／DTA 配对，读取冻结 CSV 时校验清单中的 LF 或原始字节。仓库默认忽略新的 Part 4 文件，合并时需显式纳入已审阅的产出和源码。
"""
    output.write_text(markdown, encoding="utf-8", newline="\n")
