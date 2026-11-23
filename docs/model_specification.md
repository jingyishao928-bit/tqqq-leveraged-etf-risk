# Model Specification

## Baseline

Use a constant-volatility model as a transparent benchmark. State whether the model is estimated from log returns or simple returns and how the simulated output is transformed.

## Main conditional-volatility model

The planned main model is GARCH(1,1) with Student-t innovations fitted to the underlying return series. Report parameter estimates, uncertainty or standard errors when available, persistence, distributional assumptions, and residual diagnostics.

## Leveraged mapping

For each simulated underlying log return `g_t`, first compute the simple return:

```text
r_t = exp(g_t) - 1
```

Then apply the documented daily product mapping:

```text
R_L,t = beta * r_t - daily_fee - daily_financing + tracking_adjustment
```

Any cost or tracking term must be sourced or estimated and documented. Apply the NAV floor consistently. Do not embed an empirical conclusion into the model specification.

## Risk definitions

For a long position, horizon loss is the negative of the position return. For a short position initiated at unit notional, horizon loss equals the ETF terminal wealth relative to initial wealth minus one. Short losses are not capped at 100 percent.

Compute VaR as a positive loss quantile and ES as the mean of losses at or beyond the VaR threshold. State how ties and empirical quantiles are handled.

## Backtesting

Generate forecasts chronologically using only information available at the forecast date. Use VaR exceptions for Kupiec and Christoffersen tests. Treat overlapping multi-day forecasts as dependent unless a justified method is used.

