version 18.0
clear all
set more off

/*
Rebuild the Part 1 cleaned Stata data from the frozen raw DTA files.

Run from the repository root:
    do "stata/01_clean_part1_data.do" "`c(pwd)'"

The script uses adjusted close for TQQQ and QQQ, close for NDX, keeps only
common trading dates, and calculates returns from adjacent observations.
*/

args project_root
if `"`project_root'"' == "" local project_root "`c(pwd)'"

local raw_dir       "`project_root'/data/raw"
local processed_dir "`project_root'/data/processed"
capture mkdir "`processed_dir'"

foreach ticker in TQQQ QQQ NDX {
    capture confirm file "`raw_dir'/`ticker'_raw.dta"
    if _rc {
        display as error "Missing input: data/raw/`ticker'_raw.dta"
        exit 601
    }
}

tempfile tqqq qqq ndx

/* TQQQ: adjusted close represents the ETF total-return price series. */
use "`raw_dir'/TQQQ_raw.dta", clear
confirm numeric variable Date Adj_Close Volume
sort Date
quietly duplicates drop Date, force
assert !missing(Date, Adj_Close, Volume)
assert Adj_Close > 0
generate double TQQQ_price = Adj_Close
generate double TQQQ_volume = Volume
keep Date TQQQ_price TQQQ_volume
isid Date
save "`tqqq'", replace

/* QQQ: adjusted close represents the unleveraged ETF total-return series. */
use "`raw_dir'/QQQ_raw.dta", clear
confirm numeric variable Date Adj_Close Volume
sort Date
quietly duplicates drop Date, force
assert !missing(Date, Adj_Close, Volume)
assert Adj_Close > 0
generate double QQQ_price = Adj_Close
generate double QQQ_volume = Volume
keep Date QQQ_price QQQ_volume
isid Date
save "`qqq'", replace

/* NDX: the downloaded index series uses the unadjusted close. */
use "`raw_dir'/NDX_raw.dta", clear
confirm numeric variable Date Close Volume
sort Date
quietly duplicates drop Date, force
assert !missing(Date, Close, Volume)
assert Close > 0
generate double NDX_price = Close
generate double NDX_volume = Volume
keep Date NDX_price NDX_volume
isid Date
save "`ndx'", replace

/* Inner joins retain only dates observed for all three series. */
use "`tqqq'", clear
merge 1:1 Date using "`qqq'", keep(3) nogen
merge 1:1 Date using "`ndx'", keep(3) nogen
keep if inrange(Date, td(01jan2019), td(20nov2026))
sort Date
isid Date
assert !missing(TQQQ_price, QQQ_price, NDX_price)
assert TQQQ_price > 0 & QQQ_price > 0 & NDX_price > 0
format Date %tdCCYY-NN-DD
order Date TQQQ_price TQQQ_volume QQQ_price QQQ_volume NDX_price NDX_volume
label data "Part 1 common-date cleaned prices"
save "`processed_dir'/part1_clean_prices.dta", replace
local price_rows = _N

/* Adjacent-row lags are used because weekends and holidays are absent. */
generate double TQQQ_simple_ret = TQQQ_price / TQQQ_price[_n-1] - 1 if _n > 1
generate double TQQQ_log_ret = ln(1 + TQQQ_simple_ret) if _n > 1
generate double QQQ_simple_ret = QQQ_price / QQQ_price[_n-1] - 1 if _n > 1
generate double QQQ_log_ret = ln(1 + QQQ_simple_ret) if _n > 1
generate double NDX_simple_ret = NDX_price / NDX_price[_n-1] - 1 if _n > 1
generate double NDX_log_ret = ln(1 + NDX_simple_ret) if _n > 1
drop in 1

assert !missing(TQQQ_simple_ret, TQQQ_log_ret)
assert !missing(QQQ_simple_ret, QQQ_log_ret)
assert !missing(NDX_simple_ret, NDX_log_ret)

generate byte manual_review_flag = abs(TQQQ_simple_ret) > 0.30 ///
    | abs(QQQ_simple_ret) > 0.15 | abs(NDX_simple_ret) > 0.15
label define review_flag 0 "No" 1 "Review"
label values manual_review_flag review_flag
label variable manual_review_flag "Large move retained for manual review"

order Date TQQQ_simple_ret TQQQ_log_ret QQQ_simple_ret QQQ_log_ret ///
    NDX_simple_ret NDX_log_ret TQQQ_price TQQQ_volume QQQ_price QQQ_volume ///
    NDX_price NDX_volume manual_review_flag
label data "Part 1 common-date returns and prices"
save "`processed_dir'/part1_clean_returns.dta", replace

quietly count if manual_review_flag == 1
display as result "Cleaned prices: `price_rows' observations"
display as result "Cleaned returns: " _N " observations"
display as result "Manual-review rows: " r(N)
