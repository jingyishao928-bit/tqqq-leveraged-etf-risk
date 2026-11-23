# Product Profile

This profile records the Part 1 product facts verified from current issuer
pages and prospectuses on 2026-11-24. It is separate from the historical price
source record because product terms and market observations come from
different sources.

## Verified product set

| Ticker | Formal name | Project role | Benchmark and stated objective | Inception | Expense-ratio snapshot |
|---|---|---|---|---:|---:|
| QQQ | Invesco QQQ Trust, Series 1 | Unleveraged investable comparator | Passively managed; tracks the Nasdaq-100 Index | 1999-03-10 | 0.18% total |
| TQQQ | ProShares UltraPro QQQ | Main leveraged ETF | Before fees and expenses, 3x the **daily** performance of the Nasdaq-100 Index | 2010-02-09 | 0.94% gross; 0.78% net |
| SQQQ | ProShares UltraPro Short QQQ | Inverse-product comparison | Before fees and expenses, 3x the inverse (-3x) of the **daily** performance of the Nasdaq-100 Index | 2010-02-09 | 0.94% gross; 0.94% net |

QQQ is sponsored by Invesco Capital Management LLC. TQQQ and SQQQ are
ProShares products advised by ProShare Advisors LLC.

## How to interpret the objectives

TQQQ and SQQQ specify one-day targets measured from one NAV calculation to the
next. They do not promise that a multi-day cumulative return will equal `3x`
or `-3x` the index's cumulative return. Daily rebalancing and compounding make
multi-day results path-dependent.

SQQQ is also not a substitute for the P&L from shorting TQQQ. SQQQ follows its
own daily inverse-reset path and has its own fees, financing and tracking. A
short TQQQ position instead has the negative P&L of TQQQ shares and can involve
borrow costs and margin requirements.

## Fee details

The TQQQ summary prospectus dated 2026-09-28 reports total annual fund
operating expenses of 0.94% before fee waivers and expense reimbursements, a
0.16% contractual reduction, and 0.78% after that reduction. The applicable
contractual arrangements continue through **2027-09-30**.

The SQQQ product page reports both gross and net expense ratios of 0.94%. Its
summary prospectus states that the adviser caps operating expenses at 0.95%
through 2027-09-30. Because currently disclosed expenses are already 0.94%,
that cap does not create a current gross-to-net reduction.

For both leveraged products, the operating-expense table excludes transaction
and financing costs associated with securities and derivatives. Therefore,
0.78% for TQQQ and 0.94% for SQQQ must not be described as an all-in cost of
obtaining leverage. QQQ's 0.18% is likewise an expense ratio rather than its
complete cost of ownership; trading costs and premiums or discounts can also
matter.

## Official sources

All pages and documents below were accessed on 2026-11-24.

| Product | Official source | Facts used |
|---|---|---|
| QQQ | [Invesco product detail](https://www.invesco.com/us/en/financial-products/etfs/invesco-qqq-trust-series-1.html) | Formal name, inception date and expense ratio |
| QQQ | [Invesco QQQ site](https://www.invesco.com/qqq-etf/en/home.html) | Sponsor, benchmark and passive tracking description |
| TQQQ | [ProShares product page](https://www.proshares.com/our-etfs/leveraged-and-inverse/tqqq) | Formal name, benchmark, daily objective, inception and current ratios |
| TQQQ | [Summary prospectus dated 2026-09-28](https://www.proshares.com/globalassets/proshares/prospectuses/tqqq_summary_prospectus.pdf) | Adviser, fee table, waiver amount, waiver expiry and excluded costs |
| SQQQ | [ProShares product page](https://www.proshares.com/our-etfs/leveraged-and-inverse/sqqq) | Formal name, benchmark, daily inverse objective, inception and current ratios |
| SQQQ | [Summary prospectus dated 2026-09-28](https://www.proshares.com/globalassets/proshares/prospectuses/sqqq_summary_prospectus.pdf) | Adviser, expense cap, cap expiry and excluded costs |

The machine-readable record is
`data/metadata/part1_product_facts.csv`. Fees and contractual waivers can
change, so these dated facts should be rechecked if the final report is updated
after 2026-11-24.
