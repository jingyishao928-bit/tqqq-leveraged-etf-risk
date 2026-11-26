# Part 4 — Risk results

## English slide bullets and speaker cues

Each slide has three short slide bullets and cues for roughly one minute of spoken delivery.

### Slide 1 — How risk changes with the holding period

[Figure 1](figures/fig01_risk_by_horizon.png) · Course Chapter 7, slides 54–55

- Full revaluation on 10,000 shared QQQ paths
- 99% sample ES multiples at 1 day of 3.00× long and 3.00× short
- At 21 days, 2.32× long and 4.04× short

**Speaker cues**

- Part 3 gave us 10,000 simulated paths for QQQ. I applied TQQQ's daily reset rule to each path, then valued both funds at day 1, 10 and 21. We start each position at one dollar of exposure and rank its losses, just as in the course's Monte Carlo VaR example.
- Start with the dotted 3× line. The one-day ES multiples are close to three on both sides. At 21 days, long TQQQ has sample ES of 74.0%, compared with 31.9% for long QQQ. Short TQQQ reaches 237.5%, against 58.8% for short QQQ.
- Daily rebalancing changes how gains and losses compound. The next slide shows where the long and short results come from.

### Slide 2 — The two tails of one-month TQQQ risk

[Figure 2](figures/fig02_tqqq_loss_tails.png) · Course Chapters 1 and 5

- Long TQQQ 99% VaR 65.0%, sample ES 74.0%
- Short TQQQ 99% VaR 152.0%, sample ES 237.5%
- The short position has the larger sample ES

**Speaker cues**

- Focus on 21-day TQQQ losses. The dashed lines mark the 99% VaR for each position. The shaded observations form the sample ES. VaR gives us the loss threshold, and ES tells us how large the losses were once we were in that tail.
- The long position loses when TQQQ falls, and its loss stops at the amount invested. A fixed-share short loses when TQQQ rises. The gap between its VaR of 152.0% and its sample ES of 237.5% shows why the threshold alone gives an incomplete picture.
- These ES values summarize the simulated sample. The next question is how that tail changes when the market starts out more volatile.

### Slide 3 — Historical stress and initial volatility

[Figure 3](figures/fig03_volatility_scenarios.png) · Course Chapter 5, slides 40–45 and 56–57

- COVID sell-off drawdown of 69.9% for TQQQ and 28.6% for QQQ
- GARCH-t initial QQQ volatility at 15%, 25% and 45% annualized
- Short TQQQ sample ES rises from 68.3% to 231.7%

| Annualized initial QQQ volatility | Long TQQQ 99% sample ES | Short TQQQ 99% sample ES |
|---|---:|---:|
| 15% | 36.62% | 68.29% |
| 25% | 51.18% | 110.86% |
| 45% (high-volatility scenario) | 73.80% | 231.69% |

**Speaker cues**

- On the left, two historical stress episodes stand out. TQQQ drew down about 70% in the acute 2020 COVID sell-off. The 2022 rate-hike cycle reached the deepest drawdown shown, about 81%. Market direction and volatility both shape those drawdowns.
- On the right, we use a one-factor sensitivity. We hold the model and shocks fixed and start QQQ volatility at 15%, 25% or 45% annualized. At 25%, sample ES is 51.18% long and 110.86% short.
- Across the calm and turbulent settings, long TQQQ sample ES moves from 36.6% to 73.8%. The short moves from 68.3% to 231.7%, about 3.4 times its calm value.

### Slide 4 — Reverse stress test for a bearish position

[Figure 4](figures/fig04_inverse_reverse_stress.png) · Course Chapter 5, slide 58

- Short TQQQ, excluding borrow fees. Loss >50% in 10.81% of paths. Loss >100% in 2.67%. Maximum sample loss 899.9%.
- Long ideal −3×. Loss >50% in 7.34% of paths. Loss >100% in 0.00%. Maximum sample loss 100.0%.
- A fixed-share short reaches a 100% loss when TQQQ doubles.

**Speaker cues**

- When does a fixed-share TQQQ short lose its entire initial notional? When TQQQ doubles. The table shows how often the 21-day paths exceeded losses of 50% and 100%, and the largest loss observed.
- The curves cross near a 38% loss threshold. Smaller thresholds are crossed more often by the inverse position, consistent with daily-reset volatility drag. At larger thresholds, the fixed-share short overtakes it. Short losses have no upper bound.
- The short exceeded 100% in 267 paths, excluding borrow fees. The inverse position can lose up to the amount invested. Part 5 now takes up forecast validation and position limits.

## Q&A backup

**Why is the 45% scenario's ES slightly lower than the forecast baseline?**

> The forecast baseline was already at 45.35% annualized volatility. On this slide, we hold the shocks fixed across the three scenarios, so the comparison to focus on is how risk changes from 15% to 25% to 45%.

If asked about the exact difference, the Part 3 forecast starts slightly above 45% and uses a separate set of simulated shocks. The three scenario points share the same shocks. The small differences in the refitted GARCH parameters have a negligible effect on ES.

**Can you give a historical example of the two bearish positions diverging?**

> In April 2025, QQQ ended up 1.4%, while the TQQQ short returned +4.2% and long SQQQ returned -19.0%.

## 中文对接说明

### 数据、模型与计量口径

- Part 1 的冻结样本有 1,983 个共同日收益，从 2019-01-03 到 2026-11-20。输入按 Part 1 清单核验 SHA-256，兼容 Windows 和 Linux 的换行格式。QQQ 是 Part 3 的建模标的和 Part 4 的 1× 基准。NDX 是基金目标对应的指数，TQQQ 与 SQQQ 历史收益使用复权价格。
- Part 2 已做净值、回撤和固定股数持仓比较。延用它的 COVID 抛售、COVID 反弹、2022 加息、2025 年 4 月关税四个历史阶段。另加 2021 作为低波动上涨阶段，该年 QQQ 复合收益 +27.4%，年化实现波动 18.2%，全样本是 24.1%。每个阶段以前一交易日收盘为净值 1，最大回撤以正的损失比例报告。
- 基准模拟来源为 GBM（Published Part 3 CSV）、Historical bootstrap（Published Part 3 CSV）、GARCH-t（Published Part 3 CSV）。每组 10,000 条路径取前 1／10／21 个交易日，置信度为 95%／99%，种子为 42。日对数收益先转为日简单收益，再按每日杠杆复利，基金净值下限为零。Part 3 估计的 TQQQ 综合日拖累为 0.034557243%，涵盖历史上相对 3× QQQ 的综合差额。QQQ 路径已由该 ETF 的实际收益校准。
- 15%／25%／45% 情景在原上传中只有做多的两个分位数。Part 4 按相同冻结数据和同一 Student-t GARCH(1,1) 规格重新拟合。三档情景固定模型和随机冲击，只改变起始波动率。Part 3 基准从 45.35% 年化初始波动率出发，沿用原上传的另一批随机冲击。重新拟合的全精度参数存在微小差异，对 ES 的影响可忽略。
- 模拟反向产品是同一路径上的理想 −3×，日成本为零。主比较保留原 TQQQ 日拖累，另有双边零拖累敏感性。历史对照使用真实 SQQQ。模拟和历史做空均按固定初始股数标记损益，**excluding borrow fees**，亦未建模保证金强平。阈值是期末损失严格超过初始名义金额 50% 或 100%。样本最大值是观察到的期末损失。历史滚动窗口重叠，频率是样本描述统计。
- 课上可用 2025 年 4 月作震荡例子。QQQ 累计 +1.40%，实际做空 TQQQ 损益 +4.22%，实际做多 SQQQ 损益 -18.99%。完整历史阶段和两条理想路径的收益见下方交接表。

### 21 日做多 99% VaR 口径核对

| 算法 | GARCH-t 做多 TQQQ 21 日 99% VaR（正损失） |
|---|---:|
| 共用 `risk.py`，损失最近秩 | 64.994501921917% |
| Notebook，收益 1% 线性插值后取负号 | 64.994861754887% |
| Part 3 已上传原表，收益分位数取负号 | 64.994861754887% |
| 共用函数值减 Notebook 重算值 | -0.0003598330 个百分点，-0.03598330 bp |
| 共用函数值减 Part 3 已上传原表 | -0.0003598330 个百分点，-0.03598330 bp |

共用 ES 是所有损失大于或等于 VaR 的均值。该规则保留阈值上的观测与并列值，基准主模型的 21 日 99% ES 实际样本数为 101 long and 101 short。短历史阶段（例如 23 个日收益的疫情抛售）应结合尾部观测数读数。按课件 Chapter 6 的有限均值条件，未截断 Student-t 对数右尾在指数化后使固定股数做空价格的理论 ES 发散。表格及图中 GARCH-t ES 是有限模拟样本统计，GBM 和历史 bootstrap 提供不同尾部假设的对照。

### 给 Part 5 的 CSV

所有持仓按初始 USD 1 的名义金额归一化。表内收益、损失、置信度、频率和波动率均为小数，0.50 表示 50%。倍数无量纲，日期是纽约交易日标签。正式回测应在各历史预测时点用当时可获得的数据重新估计，Part 4 的汇总风险以 2026-11-20 为样本截止日。同名 DTA 也提供对应数据。

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
