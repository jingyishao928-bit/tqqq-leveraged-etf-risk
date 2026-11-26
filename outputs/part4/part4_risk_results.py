"""Run the complete, offline Part 4 risk analysis."""

import argparse
from datetime import datetime
from pathlib import Path
import sys

import numpy as np
import pandas as pd


PART4 = Path(__file__).resolve().parent
ROOT = PART4.parents[1]
sys.path[:0] = [str(ROOT / path) for path in ("src", "scripts", "outputs/part2")]

from analyze_part2 import REGIMES  # noqa: E402
from export_part1_stata import prepare_frame, verify_round_trip  # noqa: E402
from part4_analysis import (  # noqa: E402
    BASE_CASE, LONG_INVERSE, MAIN_MODEL, SHORT_TQQQ, START_VOLS, Settings, asset_nav,
    calibrate, empirical_regimes, garch_paths, inverse_comparison, load_baseline,
    position_episodes, quantile_audit, read_returns, risk_grid, risk_multipliers,
    student_shocks, verify_frozen_input,
)
from part4_figures import inverse_positions, risk_overview, tqqq_tails, volatility_regimes  # noqa: E402
from part4_presentation import write_summary  # noqa: E402


ALL_REGIMES = (("2021 up market", "2021-01-01", "2021-12-31"), *REGIMES)
PART3_TABLES = ROOT / "outputs/part3/tables"


def published_parameters(fit, settings: Settings) -> float:
    """Cross-check the refit against the exported parameters and use the published drag."""
    path = PART3_TABLES / "table_part3_model_params.csv"
    if not path.is_file():
        return fit.tqqq_drag
    published = pd.read_csv(path, index_col=0, float_precision="round_trip")["estimate"]
    np.testing.assert_allclose([fit.omega, fit.alpha, fit.beta, fit.nu],
                               published[["omega", "alpha[1]", "beta[1]", "nu"]],
                               rtol=0.0, atol=1e-4, err_msg="Part 3 GARCH calibration mismatch")
    np.testing.assert_allclose([fit.mean_pct, fit.sd_pct, fit.tqqq_drag, settings.seed, settings.paths],
                               published[["mu", "sigma", "daily_cost", "seed", "n_paths"]],
                               rtol=1e-10, atol=1e-12, err_msg="Part 3 settings mismatch")
    np.testing.assert_allclose(fit.forecast_vol_pct, published["today_vol"], rtol=1e-4)
    return float(published["daily_cost"])


def baseline_quantiles(paths_by_model: dict, settings: Settings, drag: float,
                       sources: dict) -> dict:
    """Validate the full set of 21-day Notebook summary statistics when available."""
    source = PART3_TABLES / "table_part3_21d_results.csv"
    reported = pd.read_csv(source, index_col=0, float_precision="round_trip") if source.is_file() else None
    data = {}
    for model, paths in paths_by_model.items():
        values = asset_nav(paths, settings, drag)
        tqqq_return = values["TQQQ"][:, -1] - 1.0
        qqq_return = values["QQQ"][:, -1] - 1.0
        stats = [np.quantile(qqq_return, 0.01), tqqq_return.mean(),
                 np.quantile(tqqq_return, 0.05), np.quantile(tqqq_return, 0.01)]
        key = "Historical" if model == "Historical bootstrap" else model
        if reported is not None:
            # Optimizer and floating-point variation can affect replayed estimates.
            tolerance = 1e-11 if sources[model] == "Published Part 3 CSV" else 1e-4
            np.testing.assert_allclose(stats, reported.loc[key].to_numpy(), rtol=0.0, atol=tolerance,
                                       err_msg=f"Published Part 3 path statistics for {model}")
            data[model] = -float(reported.loc[key, "3x ETF 1% quantile"])
        else:
            data[model] = None
    return data


def write_table(name: str, frame: pd.DataFrame, folder: Path) -> None:
    """Write full-precision CSV and a verified, deterministic Stata mirror."""
    csv = folder / f"{name}.csv"
    dta = csv.with_suffix(".dta")
    frame.to_csv(csv, index=False)
    stata, labels, date_formats = prepare_frame(csv)
    stata.to_stata(dta, version=118, write_index=False, convert_dates=date_formats,
                   variable_labels=labels, data_label=f"Exported from {csv.name}"[:80],
                   time_stamp=datetime(2000, 1, 1))
    verify_round_trip(stata, dta)


def build(output: Path) -> None:
    """Verify upstream inputs, compute risk, and create the handoff and four figures."""
    settings = Settings.from_repo(ROOT)
    input_hash = verify_frozen_input(settings, ROOT)
    frame = read_returns(settings)
    fit = calibrate(frame, settings)
    drag = published_parameters(fit, settings)
    paths_by_model, sources = load_baseline(PART3_TABLES, frame, settings, fit)
    published = baseline_quantiles(paths_by_model, settings, drag, sources)

    risk = risk_grid(paths_by_model, settings, drag)
    multipliers = risk_multipliers(risk)
    phases, empirical_tail = empirical_regimes(frame, settings, ALL_REGIMES)
    common_shocks = student_shocks(np.random.default_rng(settings.seed), settings, fit.nu)
    conditional_paths = {case: garch_paths(common_shocks, vol * 100.0 / np.sqrt(settings.annual_days), fit)
                         for case, vol in START_VOLS.items()}
    conditional = risk_grid(conditional_paths, settings, drag)
    conditional.insert(1, "initial_vol_annual", conditional.case.map(START_VOLS))
    inverse, losses = inverse_comparison(paths_by_model, frame, settings, drag)
    episodes = position_episodes(frame, settings, ALL_REGIMES)
    tqqq_losses = {"Long": -losses[SHORT_TQQQ], "Short": losses[SHORT_TQQQ]}
    audit = quantile_audit(tqqq_losses["Long"], published[MAIN_MODEL])

    as_of = frame.index[-1].date()
    initial_vols = {MAIN_MODEL: fit.forecast_vol_pct * np.sqrt(settings.annual_days) / 100.0}
    paths_meta = pd.DataFrame([
        dict(model=model, source=source, seed=settings.seed, paths=settings.paths,
             horizon_days=settings.days, estimation_start=frame.index[0].date(), as_of=as_of,
             annual_volatility=initial_vols.get(model, fit.sd_pct * np.sqrt(settings.annual_days) / 100.0),
             tqqq_daily_drag=drag, historical_rows=len(frame),
             input_sha256=input_hash)
        for model, source in sources.items()
    ])
    output.mkdir(parents=True, exist_ok=True)
    figures = output / "figures"
    tables = output / "tables"
    figures.mkdir(exist_ok=True)
    tables.mkdir(exist_ok=True)
    table_data = {
        "part4_base_var_es": risk.assign(as_of=as_of),
        "part4_risk_multipliers": multipliers.assign(as_of=as_of),
        "part4_historical_regimes": phases,
        "part4_historical_var_es": empirical_tail,
        "part4_volatility_scenarios": conditional.assign(model=MAIN_MODEL, seed=settings.seed, as_of=as_of),
        "part4_inverse_comparison": inverse.assign(analysis_start=frame.index[0].date(), as_of=as_of),
        "part4_inverse_episodes": episodes,
        "part4_quantile_audit": audit.assign(as_of=as_of),
        "part4_simulation_inputs": paths_meta,
    }
    for name, table in table_data.items():
        write_table(name, table.assign(initial_notional_usd=1.0) if name != "part4_simulation_inputs" else table,
                    tables)

    baseline_note = (f"Part 3 forecast baseline: {initial_vols[MAIN_MODEL]:.2%} "
                     "annualized initial QQQ volatility.")
    risk_overview(risk, multipliers, figures / "fig01_risk_by_horizon.png", baseline_note)
    tqqq_tails(tqqq_losses, risk, settings.days, figures / "fig02_tqqq_loss_tails.png", baseline_note)
    volatility_regimes(phases, conditional, settings.days, figures / "fig03_volatility_scenarios.png")
    inverse_positions(losses, inverse, settings.days, figures / "fig04_inverse_reverse_stress.png",
                      baseline_note)
    write_summary(output / "part4_summary.md", settings, paths_meta, risk, multipliers,
                  phases, conditional, inverse, episodes, audit)

    print(f"Historical input: {len(frame):,} returns from {frame.index[0].date()} to {as_of}")
    print(f"GARCH-t: {settings.paths:,} x {settings.days} trading days, seed {settings.seed}")
    print(f"Calibrated TQQQ daily drag: {drag:.9%}")
    print(f"21-day long 99% VaR: shared {audit.shared_var_loss.iloc[0]:.9%}, "
          f"Notebook {audit.notebook_recomputed_loss.iloc[0]:.9%}, "
          f"difference {audit.shared_minus_notebook.iloc[0] * 1e4:+.6f} bp")
    cols = ["position", "var_loss", "es_loss", "prob_loss_gt_50", "prob_loss_gt_100", "max_sample_loss"]
    headline = inverse.loc[(inverse.model == MAIN_MODEL) & (inverse.cost_basis == BASE_CASE)
                           & (inverse.horizon_days == settings.days) & np.isclose(inverse.confidence, 0.99)]
    print(headline[cols].to_string(index=False, float_format=lambda number: f"{number:.4%}"))
    print(f"Wrote {len(table_data)} CSV/DTA pairs and 4 presentation figures to {output}")


def main() -> None:
    """Run Part 4 from any directory using paths resolved from the script."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=PART4,
                        help="Directory for the Part 4 outputs")
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output == ROOT or ROOT in output.parents and PART4 not in (*output.parents, output):
        parser.error("Choose the Part 4 folder or an output directory outside the project.")
    build(output)


if __name__ == "__main__":
    main()
