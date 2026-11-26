"""Compute Part 4 risk measures from the frozen project snapshot."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from leveraged_etf_risk.risk import expected_shortfall, value_at_risk


MODEL_FILES = {
    "GBM": "gbm",
    "Historical bootstrap": "historical",
    "GARCH-t": "garch_t",
}
START_VOLS = {"Calm": 0.15, "Normal": 0.25, "Turbulent": 0.45}
SIDES = ("Long", "Short")
SHORT_TQQQ = "Short TQQQ"
LONG_INVERSE = "Long ideal -3x"
LONG_SQQQ = "Long SQQQ"
MAIN_MODEL = "GARCH-t"
OBSERVED = "Historical adjusted closes"
BASE_CASE = "Part 3 calibrated TQQQ drag"
ZERO_COST = "Zero drag on both simulated funds"
DRAW_CUTOFFS = (0.50, 1.00)


@dataclass(frozen=True)
class Settings:
    """Simulation and risk settings from the shared project configuration."""

    historical_file: Path
    start: pd.Timestamp
    end: pd.Timestamp
    paths: int
    horizons: tuple[int, ...]
    confidence: tuple[float, ...]
    seed: int
    annual_days: int
    bull_beta: float
    bear_beta: float
    nav_floor: float

    @property
    def days(self) -> int:
        return max(self.horizons)

    @classmethod
    def from_repo(cls, root: Path) -> "Settings":
        config = yaml.safe_load((root / "config/project.yaml").read_text(encoding="utf-8"))
        return cls(
            root / config["data"]["processed_file"],
            pd.Timestamp(config["part1"]["analysis_start_date"]),
            pd.Timestamp(config["part1"]["analysis_end_date"]),
            config["simulation"]["paths"],
            tuple(config["risk"]["horizon_days"]),
            tuple(config["risk"]["confidence_levels"]),
            config["project"]["random_seed"],
            config["project"]["trading_days_per_year"],
            config["products"]["bull_beta"],
            config["products"]["bear_beta"],
            config["simulation"]["nav_floor"],
        )


@dataclass(frozen=True)
class Calibration:
    """Part 3 estimates. Mean, innovation scale and volatility use percent units."""

    mean_pct: float
    sd_pct: float
    omega: float
    alpha: float
    beta: float
    nu: float
    forecast_vol_pct: float
    tqqq_drag: float


def read_returns(settings: Settings) -> pd.DataFrame:
    """Load the aligned decimal-return snapshot and validate the sample."""
    frame = pd.read_csv(settings.historical_file, parse_dates=["date"], index_col="date")
    frame = frame.loc[settings.start:settings.end]
    columns = [f"{ticker}_{kind}_return" for ticker in ("qqq", "tqqq", "sqqq")
               for kind in ("simple", "log")]
    if (frame.empty or not frame.index.is_unique or not frame.index.is_monotonic_increasing
            or frame.index.hasnans or frame.index[-1] != settings.end):
        raise ValueError("The frozen sample needs ascending unique dates and the configured end date.")
    if not np.isfinite(frame[columns].to_numpy(dtype=float)).all():
        raise ValueError("The frozen sample contains invalid returns.")
    for ticker in ("qqq", "tqqq", "sqqq"):
        np.testing.assert_allclose(np.expm1(frame[f"{ticker}_log_return"]),
                                   frame[f"{ticker}_simple_return"], rtol=1e-11, atol=1e-13)
    return frame


def verify_frozen_input(settings: Settings, root: Path) -> str:
    """Match the canonical input to its manifest, allowing Git newline conversion."""
    manifest = pd.read_csv(root / "data/metadata/part1_checksums.csv").set_index("path")
    entry = manifest.loc[settings.historical_file.relative_to(root).as_posix()]
    raw = settings.historical_file.read_bytes()
    for candidate in (raw, raw.replace(b"\r\n", b"\n")):
        if len(candidate) == int(entry["bytes"]) and sha256(candidate).hexdigest() == entry["sha256"]:
            return entry["sha256"]
    raise ValueError("The canonical returns differ from the reviewed Part 1 checksum.")


def calibrate(frame: pd.DataFrame, settings: Settings) -> Calibration:
    """Refit the exact Part 3 specification to recover unrounded GARCH parameters."""
    from arch import arch_model

    log_pct = frame["qqq_log_return"] * 100.0
    mean_pct = log_pct.mean()
    fitted = arch_model(log_pct - mean_pct, mean="Zero", vol="GARCH",
                        p=1, q=1, dist="t").fit(disp="off")
    if fitted.convergence_flag:
        raise RuntimeError(f"The Part 3 GARCH fit did not converge: {fitted.convergence_flag}")
    omega, alpha, beta, nu = fitted.params[["omega", "alpha[1]", "beta[1]", "nu"]]
    forecast = np.sqrt(fitted.forecast(horizon=1).variance.iloc[-1, 0])
    drag = (settings.bull_beta * frame["qqq_simple_return"] - frame["tqqq_simple_return"]).mean()
    return Calibration(mean_pct, log_pct.std(), omega, alpha, beta, nu, forecast, drag)


def student_shocks(rng: np.random.Generator, settings: Settings, nu: float) -> np.ndarray:
    """Return variance-one Student-t innovations shaped (days, paths)."""
    return rng.standard_t(nu, size=(settings.days, settings.paths)) * np.sqrt((nu - 2) / nu)


def garch_paths(shocks: np.ndarray, start_vol_pct: float, fit: Calibration) -> np.ndarray:
    """Return decimal log paths shaped (paths, days) from pre-drawn innovations."""
    variance = np.full(shocks.shape[1], start_vol_pct ** 2)
    paths = np.empty(shocks.T.shape)
    for day, shock in enumerate(shocks):
        residual = np.sqrt(variance) * shock
        paths[:, day] = (fit.mean_pct + residual) / 100.0
        variance = fit.omega + fit.alpha * residual ** 2 + fit.beta * variance
    return paths


def replay_part3_paths(frame: pd.DataFrame, settings: Settings, fit: Calibration) -> dict:
    """Replay the Notebook's baseline RNG order using frozen data and its fitted specification."""
    rng = np.random.default_rng(settings.seed)
    shape = (settings.paths, settings.days)
    gbm = rng.normal(fit.mean_pct, fit.sd_pct, shape) / 100.0
    history = rng.choice(frame["qqq_log_return"].to_numpy() * 100.0, shape) / 100.0
    garch = garch_paths(student_shocks(rng, settings, fit.nu), fit.forecast_vol_pct, fit)
    return dict(zip(MODEL_FILES, (gbm, history, garch), strict=True))


def load_baseline(folder: Path, frame: pd.DataFrame, settings: Settings,
                  fit: Calibration) -> tuple[dict, dict]:
    """Prefer published paths, replaying the Notebook only for missing files."""
    sources = {}
    paths_by_model = {}
    fallback = None
    day_columns = [f"day_{day}" for day in range(1, settings.days + 1)]
    for name, key in MODEL_FILES.items():
        path = folder / f"sim_qqq_log_returns_{key}.csv"
        if path.is_file():
            data = pd.read_csv(path, index_col="path", float_precision="round_trip")
            if (list(data.columns) != day_columns
                    or not np.array_equal(data.index, np.arange(settings.paths))):
                raise ValueError(f"Unexpected path IDs or day columns in {path.name}.")
            paths = data.to_numpy(dtype=float)
            sources[name] = "Published Part 3 CSV"
        else:
            if fallback is None:
                fallback = replay_part3_paths(frame, settings, fit)
            paths = fallback[name]
            sources[name] = "Part 3 Notebook replay"
        if paths.shape != (settings.paths, settings.days) or not np.isfinite(paths).all():
            raise ValueError(f"Invalid simulation paths for {name}.")
        paths_by_model[name] = paths
    return paths_by_model, sources


def daily_reset(log_returns: np.ndarray, leverage: float, drag: float,
                nav_floor: float = 0.0) -> np.ndarray:
    """Map decimal log returns to daily-reset NAV paths per initial dollar."""
    simple = np.expm1(log_returns)
    gross = 1.0 + leverage * simple - drag
    if nav_floor != 0.0:
        raise ValueError("The Part 3 daily-reset convention uses a zero NAV floor.")
    return np.cumprod(np.maximum(gross, 0.0), axis=-1)


def position_loss(terminal: np.ndarray, side: str) -> np.ndarray:
    """Return signed losses per initial dollar, with a fixed number of short shares."""
    return 1.0 - terminal if side == "Long" else terminal - 1.0


def tail_records(loss: np.ndarray, levels: tuple[float, ...]) -> list[dict]:
    """Apply the shared nearest-rank VaR and inclusive threshold ES, retaining tail counts."""
    result = []
    for confidence in levels:
        var = value_at_risk(loss, confidence)
        es = expected_shortfall(loss, confidence)
        result.append({
            "confidence": confidence, "var_loss": var, "es_loss": es,
            "observations": loss.size, "tail_observations": int(np.count_nonzero(loss >= var)),
        })
    return result


def asset_nav(paths: np.ndarray, settings: Settings, drag: float) -> dict:
    """Return comparable TQQQ and QQQ NAV paths on the same underlying innovations."""
    return {
        "TQQQ": daily_reset(paths, settings.bull_beta, drag, settings.nav_floor),
        "QQQ": np.exp(np.cumsum(paths, axis=-1)),
    }


def risk_grid(paths_by_case: dict, settings: Settings, drag: float) -> pd.DataFrame:
    """Calculate normalized tail losses for each model, fund, side and horizon."""
    rows = []
    for case, paths in paths_by_case.items():
        for asset, nav in asset_nav(paths, settings, drag).items():
            for days in settings.horizons:
                for side in SIDES:
                    loss = position_loss(nav[:, days - 1], side)
                    for record in tail_records(loss, settings.confidence):
                        rows.append(dict(case=case, asset=asset, position=side, horizon_days=days,
                                         daily_drag=drag if asset == "TQQQ" else 0.0, **record))
    return pd.DataFrame(rows)


def risk_multipliers(risks: pd.DataFrame) -> pd.DataFrame:
    """Compute like-for-like TQQQ/QQQ VaR and ES ratios on common paths."""
    keys = ["case", "horizon_days", "position", "confidence"]
    tqqq = risks.loc[risks.asset.eq("TQQQ"), keys + ["var_loss", "es_loss"]]
    qqq = risks.loc[risks.asset.eq("QQQ"), keys + ["var_loss", "es_loss"]]
    matched = tqqq.merge(qqq, on=keys, suffixes=("_tqqq", "_qqq"), validate="one_to_one")
    for measure in ("var", "es"):
        denominator = matched[f"{measure}_loss_qqq"]
        matched[f"{measure}_multiple"] = matched[f"{measure}_loss_tqqq"].div(
            denominator.where(denominator > 0.0)
        )
    return matched


def empirical_regimes(frame: pd.DataFrame, settings: Settings, regimes: tuple) -> tuple:
    """Calculate rebased wealth, annualized sample volatility and daily historical tail risk."""
    phases = []
    tails = []
    for label, start, end in (*regimes, ("Full sample", frame.index[0], frame.index[-1])):
        window = frame.loc[start:end]
        if len(window) < 2:
            raise ValueError(f"Too few returns in historical window {label}.")
        meta = dict(regime=label, analysis_start=window.index[0].date(),
                    analysis_end=window.index[-1].date())
        for asset in ("QQQ", "TQQQ"):
            daily = window[f"{asset.lower()}_simple_return"].to_numpy()
            wealth = np.r_[1.0, np.cumprod(1.0 + daily)]
            phases.append(dict(
                **meta, asset=asset, observations=daily.size, cumulative_return=wealth[-1] - 1.0,
                annualized_volatility=daily.std(ddof=1) * np.sqrt(settings.annual_days),
                max_drawdown_loss=np.max(1.0 - wealth / np.maximum.accumulate(wealth)),
            ))
            for side in SIDES:
                loss = -daily if side == "Long" else daily
                tails.extend(dict(**meta, asset=asset, position=side, horizon_days=1, **record)
                             for record in tail_records(loss, settings.confidence))
    return pd.DataFrame(phases), pd.DataFrame(tails)


def rolling_terminal(returns: np.ndarray, days: int) -> np.ndarray:
    """Return wealth from each complete rolling window of decimal log returns."""
    windows = np.lib.stride_tricks.sliding_window_view(returns, days)
    return np.exp(windows.sum(axis=-1))


def position_records(losses: dict, settings: Settings, **metadata) -> list[dict]:
    """Summarize terminal losses; exceedances use strict greater-than thresholds."""
    rows = []
    for position, loss in losses.items():
        low, high = (int(np.count_nonzero(loss > level)) for level in DRAW_CUTOFFS)
        for tail in tail_records(loss, settings.confidence):
            rows.append(dict(**metadata, position=position, median_return=-np.median(loss),
                             max_sample_loss=np.max(loss), count_loss_gt_50=low,
                             count_loss_gt_100=high, prob_loss_gt_50=low / loss.size,
                             prob_loss_gt_100=high / loss.size, **tail))
    return rows


def inverse_comparison(paths_by_model: dict, frame: pd.DataFrame,
                       settings: Settings, drag: float) -> tuple:
    """Return simulated and historical fixed-share short and inverse daily-reset risk."""
    rows = []
    for model, paths in paths_by_model.items():
        bull = daily_reset(paths, settings.bull_beta, drag, settings.nav_floor)
        bull_without_drag = daily_reset(paths, settings.bull_beta, 0.0, settings.nav_floor)
        bear = daily_reset(paths, settings.bear_beta, 0.0, settings.nav_floor)
        for days in settings.horizons:
            day = days - 1
            rows.extend(position_records(
                {SHORT_TQQQ: bull[:, day] - 1.0, LONG_INVERSE: 1.0 - bear[:, day]},
                settings, model=model, cost_basis=BASE_CASE, horizon_days=days))
            rows.extend(position_records(
                {SHORT_TQQQ: bull_without_drag[:, day] - 1.0, LONG_INVERSE: 1.0 - bear[:, day]},
                settings, model=model, cost_basis=ZERO_COST, horizon_days=days))
    for days in sorted(settings.horizons):
        observed_loss = {
            SHORT_TQQQ: rolling_terminal(frame.tqqq_log_return.to_numpy(), days) - 1.0,
            LONG_SQQQ: 1.0 - rolling_terminal(frame.sqqq_log_return.to_numpy(), days),
        }
        rows.extend(position_records(observed_loss, settings, model=OBSERVED,
                                     cost_basis="Observed fund returns", horizon_days=days))

    paths = paths_by_model[MAIN_MODEL]
    garch_losses = {
        SHORT_TQQQ: daily_reset(paths, settings.bull_beta, drag, settings.nav_floor)[:, -1] - 1.0,
        LONG_INVERSE: 1.0 - daily_reset(paths, settings.bear_beta, 0.0, settings.nav_floor)[:, -1],
    }
    return pd.DataFrame(rows), garch_losses


def position_episodes(frame: pd.DataFrame, settings: Settings, regimes: tuple) -> pd.DataFrame:
    """Compare fixed-share returns over entire historical episodes and idealized replications."""
    rows = []
    for label, start, end in regimes:
        episode = frame.loc[start:end]
        simple_log = episode["qqq_log_return"].to_numpy()
        tqqq = np.exp(episode["tqqq_log_return"].sum())
        sqqq = np.exp(episode["sqqq_log_return"].sum())
        ideal_bull = daily_reset(simple_log, settings.bull_beta, 0.0, settings.nav_floor)[-1]
        ideal_bear = daily_reset(simple_log, settings.bear_beta, 0.0, settings.nav_floor)[-1]
        rows.append(dict(regime=label, analysis_start=episode.index[0].date(),
                         analysis_end=episode.index[-1].date(), observations=len(episode),
                         qqq_return=np.expm1(simple_log.sum()),
                         short_tqqq_return=1.0 - tqqq, long_sqqq_return=sqqq - 1.0,
                         short_ideal_bull_return=1.0 - ideal_bull,
                         long_ideal_inverse_return=ideal_bear - 1.0))
    return pd.DataFrame(rows)


def quantile_audit(long_loss: np.ndarray, published_loss: float | None) -> pd.DataFrame:
    """Compare risk.py's nearest rank with the Notebook's linear return quantile."""
    confidence = 0.99
    shared = value_at_risk(long_loss, confidence)
    linear = -np.quantile(-long_loss, 0.01, method="linear")
    published = np.nan if published_loss is None else published_loss
    return pd.DataFrame([dict(
        asset="TQQQ", position="Long", model=MAIN_MODEL, horizon_days=21, confidence=confidence,
        observations=long_loss.size, shared_var_loss=shared, notebook_recomputed_loss=linear,
        notebook_published_loss=published, shared_minus_notebook=shared - linear,
        shared_minus_published=shared - published,
        recomputed_minus_published=linear - published,
    )])
