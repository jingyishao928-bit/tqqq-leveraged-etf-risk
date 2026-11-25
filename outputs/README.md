# Output folders by presentation part

Generated results are stored with the part that produces them. Shared raw
data, cleaned inputs and audit metadata stay under `data/`.

```text
outputs/
  part1/
    analyze_part1.py         # full Python analysis source
    figures/
      fig_part1_replication.png
      fig_part1_daily_leverage_check.png
    tables/
      part1_replication_path.csv
      part1_replication_path.dta
      table_part1_replication.csv
      table_part1_replication.dta
      table_part1_descriptive_statistics.csv
      table_part1_descriptive_statistics.dta
      table_part1_daily_leverage_check.csv
      table_part1_daily_leverage_check.dta
  part2/
    analyze_part2.py
    check_part2.py
    figures/
    tables/
    part2_report_section.md
    part2_ppt_slides.md
  part3/                    # reserved
  part4/                    # reserved
  part5/                    # reserved
```

- Part 1: product mechanics, data foundations and basic daily compounding.
- Part 2: return mechanics and empirical decomposition.
- Part 3: models and simulation.
- Part 4: risk results and comparisons.
- Part 5: backtesting and risk management.

中文：Part 1 和 Part 2 的产出分别保存在各自目录。其他目录中的 `.gitkeep` 用于保留预定路径。

When another part starts generating results, create `figures/` and/or
`tables/` inside its own folder. Keep CSV tables and their corresponding DTA
files together. The ignore rules exclude unreviewed generated files; add
reviewed outputs explicitly when making a release.

Part 1's output root is `part1.output_dir` in
`config/project.yaml`. The Python analysis/replication scripts, native Stata workflow
and documentation use the new layout. The Stata export helper discovers
tracked CSVs automatically, so it follows the moved tables without a
separate file list.

Run `python outputs/part1/analyze_part1.py` from the repository root to regenerate
the descriptive table, daily OLS table and daily-leverage scatter. This also
creates and verifies the two same-folder DTA exports. It does not download
data or regenerate the separate replication-path diagnostic.

中文：完整 Python 分析代码也在 `part1/` 内，与 `tables/` 和 `figures/`
放在一起。在本地完整仓库的 `outputs/part1/` 文件夹内，也可以直接运行
`python analyze_part1.py`。脚本会自动定位仓库根目录，读取共享配置和清洗数据。
`scripts/analyze_part1.py` 保留为旧命令入口，调用的是这里的同一份代码。

The descriptive table stores daily returns in percent (`1` means `1%`);
the regression table labels decimal-return metrics and dimensionless
metrics separately. Both include actual analysis dates. The scatter uses
the same sample, percent axes and both flagged dates. See
[`Part 1 reproduction guide`](../docs/part1_deliverables.md#5-reproduction-and-slide-preparation-code)
for interpretation and input validation.

Part 2 may reuse the existing Part 1 replication diagnostic by referring to
it in `part1/`; no duplicate copy is needed. Any new Part 2 analysis belongs
in `part2/`. The directory move does not change the existing output contents.

See the [Part 2 guide](part2/README.md) for the output schemas and self-check.
