"""Run with python part5_backtest.py REPOSITORY OUTPUT_DIRECTORY."""
import argparse
from dataclasses import replace
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.special import xlogy
from scipy.stats import chi2, binomtest
import yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def log_likelihood(events, total, probability=None):
    probability = events / total if probability is None and total else probability
    if not total:
        return 0.0
    return xlogy(events, probability) + xlogy(total-events, 1-probability)


def coverage(hits, nominal):
    hits = np.asarray(hits, dtype=int)
    n, k = len(hits), int(hits.sum())
    uc = 2*(log_likelihood(k, n)-log_likelihood(k, n, nominal))
    n00, n01, n10, n11 = np.bincount(2*hits[:-1]+hits[1:], minlength=4)
    ind = 2*(log_likelihood(n01,n00+n01)+log_likelihood(n11,n10+n11)
             -log_likelihood(n01+n11,n-1))
    identifiable = bool((n00+n01) and (n10+n11))
    return dict(n=n, exceptions=k, rate=k/n, nominal=nominal,
                expected=n*nominal, lr_uc=uc, p_uc=chi2.sf(uc,1),
                p_exact=binomtest(k,n,nominal).pvalue,
                lr_ind=ind if identifiable else np.nan,
                p_ind=chi2.sf(ind,1) if identifiable else np.nan,
                p_cc=chi2.sf(uc+ind,2) if identifiable else np.nan,
                n00=n00,n01=n01,n10=n10,n11=n11)


def main(root, destination):
    sys.path[:0] = [str(root/"src"), str(root/"outputs/part4")]
    from part4_analysis import (Settings, calibrate, garch_paths,
                                read_returns, student_shocks, verify_frozen_input)
    from leveraged_etf_risk.risk import value_at_risk
    settings = Settings.from_repo(root)
    print("SHA256", verify_frozen_input(settings, root))
    frame = read_returns(settings)
    cfg = yaml.safe_load((root/"config/project.yaml").read_text())
    window = cfg["backtest"]["estimation_window"]
    primary = cfg["backtest"]["horizon_days"]
    ten = 10
    simulation = replace(settings, horizons=(ten,))
    actual = frame.tqqq_simple_return.to_numpy()
    rows = []
    for i in range(window,len(frame)):
        train = frame.iloc[i-window:i]
        fit = calibrate(train, settings)
        rng = np.random.default_rng(np.random.SeedSequence([settings.seed, i]))
        use_ten = (i-window)%ten==0 and i+ten<=len(frame)
        local = simulation if use_ten else replace(settings,horizons=(primary,))
        paths = garch_paths(student_shocks(rng,local,fit.nu),fit.forecast_vol_pct,fit)
        wealth = np.cumprod(np.maximum(settings.nav_floor,
                          1+settings.bull_beta*np.expm1(paths)-fit.tqqq_drag),axis=1)
        for h in ((primary,ten) if use_ten else (primary,)):
            realized = np.prod(1+actual[i:i+h])-1
            for side,sign in (("Long",-1),("Short",1)):
                losses = sign*(wealth[:,h-1]-1)
                for confidence in settings.confidence:
                    var = value_at_risk(losses, confidence)
                    rows.append((train.index[0],train.index[-1],frame.index[i],
                                 frame.index[i+h-1],h,side,confidence,sign*realized,
                                 var,sign*realized>var))
    forecasts = pd.DataFrame(rows,columns=["train_start","origin","start","end","horizon",
                                           "side","confidence","loss","var","exception"])
    assert (forecasts.origin < forecasts.start).all()
    blocks = forecasts.query("horizon == 10 and side == 'Long' and confidence == 0.95")
    assert (blocks.start.iloc[1:].to_numpy()>blocks.end.iloc[:-1].to_numpy()).all()
    summary = pd.DataFrame([dict(horizon=h,side=s,confidence=c,
                                 **coverage(g.exception,round(1-c,10)))
                            for (h,s,c),g in forecasts.groupby(["horizon","side","confidence"])])
    destination.mkdir(parents=True,exist_ok=True)
    forecasts.to_csv(destination/"part5_forecasts.csv",index=False)
    summary.to_csv(destination/"part5_backtest_results.csv",index=False)

    source = root/"outputs/part4/tables"
    base = pd.read_csv(source/"part4_base_var_es.csv").query(
        "case == 'GARCH-t' and asset == 'TQQQ' and horizon_days == 10 and confidence == 0.99")
    stress = pd.read_csv(source/"part4_volatility_scenarios.csv").query(
        "case == 'Turbulent' and asset == 'TQQQ' and horizon_days == 10 and confidence == 0.99")
    limits = base.set_index("position")[["as_of","var_loss","es_loss"]].join(
        stress.set_index("position").es_loss.rename("stress_es_loss"))
    limits["budget_usd"] = 1000
    for column in ("var","es","stress_es"):
        limits[f"{column}_cap_usd"] = limits.budget_usd / limits[f"{column}_loss"]
    limits["combined_cap_usd"] = np.floor(limits.filter(like="_cap_usd").min(axis=1))
    limits.to_csv(destination/"part5_limits.csv")

    fig, axes = plt.subplots(2,2,figsize=(13,5.6),sharex=True,layout="constrained")
    for (h,s),ax in zip([(1,"Long"),(1,"Short"),(10,"Long"),(10,"Short")],axes.flat):
        g = forecasts[(forecasts.horizon==h)&(forecasts.side==s)&(forecasts.confidence==.99)]
        x = g[g.exception]
        ax.plot(g.end,100*g.loss,color="#9aabba",linewidth=.6,label="Realized loss")
        ax.plot(g.end,100*g['var'],color="#127773",linewidth=1.1,label="99% VaR")
        ax.scatter(x.end,100*x.loss,color="#c94832",s=19,zorder=3,label="Exception")
        ax.set_title(f"{h}D {s}   ·   {len(x)}/{len(g)} exceptions",loc="left",fontsize=11)
        ax.set_ylabel("Loss (%)")
        ax.grid(alpha=.2)
    axes[0,0].legend(loc="lower left",ncols=3,fontsize=8)
    fig.savefig(destination/"part5_exceptions.png",dpi=180)
    print(summary.round(5).to_string(index=False))
    print(limits.to_string())
    print(forecasts.groupby("horizon")[["origin","start","end"]].agg(["min","max"]))


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository",type=Path)
    parser.add_argument("output",type=Path)
    args=parser.parse_args()
    main(args.repository.resolve(),args.output.resolve())
