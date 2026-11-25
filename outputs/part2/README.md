# Part 2 | Historical returns and daily reset

Run from the repository root after installing the project requirements.

~~~bash
python outputs/part2/analyze_part2.py > /tmp/part2-console.csv
python outputs/part2/check_part2.py --console /tmp/part2-console.csv
python outputs/part2/part2_research.py --output-dir outputs/part2
python -m unittest discover -s tests -v
~~~

The analysis uses the frozen canonical CSV and project configuration. The first price date is the starting wealth anchor. The first canonical return is included. The expense-ratio sensitivity comes from Part 1's product metadata. To regenerate into another directory, pass the same --output-dir to both scripts. For a pre-submission Git audit, include the intended Part 2 files in the review diff and pass --git-base with the base commit.

| Deliverable | Contents and units |
|---|---|
| [Report section](report/Part2_Report.md) ([Word](report/Part2_Report.docx), [PDF](report/Part2_Report.pdf)) | Report section for the group submission, with a Chinese abstract |
| [Presentation](presentation/Part2_Presentation.pptx) ([PDF](presentation/Part2_Presentation.pdf)) | Group-template slides with speaker notes and editable subscript formatting |
| [Chinese overview](report/Part2_Overview.zh.md) · [中文结果索引](results_guide.zh.md) | Teammate summary and lookup for every CSV and figure |
| [Technical notes](part2_report_section.md) · [Presenter outline](part2_ppt_slides.md) | Core analysis notes generated from the metrics table |
| [Research supplement](tables/part2_research_conditional_summary.csv) | Disjoint-window summary, NDX log-growth bridge, and Q–Q diagnostic |
| [Daily paths](tables/part2_daily_paths.csv) | One row per canonical return date. Decimal simple returns, wealth per unit, decimal drawdowns and USD P&L per initial USD. The prior-close plotting anchor does not create a return row. |
| [Rolling metrics](tables/part2_rolling_metrics.csv) | One row per complete trailing date/window pair. Annualized volatilities and QQQ holding-period returns are decimal fractions. OLS slopes are exposure multiples. The exact drag is in natural-log units. |
| [Performance](tables/table_part2_performance.csv) | ETF-level daily, cumulative and annualized decimal returns, drawdown and peak/trough dates |
| [Regime attribution](tables/table_part2_regime_attribution.csv) | Decimal returns, wealth-index point gaps, relative gaps as fractions and drag in natural-log units. Each period is rebased to its prior trading close. |
| [Tracking](tables/table_part2_tracking.csv) | Decimal daily TQQQ-versus-target errors and annualized volatility of those errors for QQQ and NDX |
| [Positions](tables/table_part2_positions.csv) | Fixed-share marks and mark changes in USD per initial USD. The worst and best daily moves are changes in marks from the preceding close. |
| [Cumulative path](tables/part2_cumulative_path.csv) | Wealth-only series with the true prior-close anchor and one row per common price date |
| [Two-day example](tables/table_part2_two_day_example.csv) | Three hypothetical paths with decimal returns and reset gaps |
| [Holding periods](tables/table_part2_holding_period.csv) | Trailing 1, 10 and 21 trading-day windows for NDX and QQQ, including actual, ideal and linear returns, decimal gaps, squared-return sums, annualized RMS and log drag |
| [Holding summary](tables/table_part2_holding_period_summary.csv) | Mean differences, share of windows with negative reset gaps, and approximate-drag errors by benchmark and horizon |
| [Fee sensitivity](tables/table_part2_fee_sensitivity.csv) | No-fee, net-rate and gross-rate scenarios for both benchmark paths |
| [Benchmark sensitivity](tables/table_part2_benchmark_sensitivity.csv) | Full-sample NDX versus QQQ arithmetic and log attribution |
| [Key metrics](tables/table_part2_key_metrics.csv) | Values with explicit units and presentation strings used in the console and both documents |

The tables have same-folder Stata copies. Percentages in the key metrics ledger are already multiplied by 100. Values in the underlying analysis tables retain decimal precision. Displayed components can differ from displayed totals by a hundredth of a percentage point due to independent rounding.

The dated rolling outputs use information through the date's close. The market phases are retrospective examples. Part 3 should continue to take model inputs from the [canonical returns](../../data/processed/clean_returns.csv) and can use the Part 2 tables to cross-check historical paths. Parts 4 and 5 retain responsibility for VaR/ES, backtesting and trading limits.


## Rebuild the documents

Install `requirements-presentation.txt` alongside the project dependencies.
The Word export requires Pandoc. The slide builder accepts the group's original
PowerPoint file and uses its Part 2 section divider and example layout. Run the
core and supplementary analysis above before building the slides.

~~~bash
python -m pip install -r outputs/part2/requirements-presentation.txt
python outputs/part2/build_part2_report.py
python outputs/part2/build_part2_presentation.py --template path/to/group-template.pptx
~~~

Export the resulting documents as PDF with PowerPoint/Word or LibreOffice.
The release deck contains four main slides and four backup slides after the
section divider. It preserves the approved content and layout and uses a
generic presenter label for public repository copies.
