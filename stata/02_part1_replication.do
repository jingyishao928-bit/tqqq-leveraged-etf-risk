version 18.0
clear all
set more off

/*
Create the idealized daily-reset TQQQ replication outputs in Stata.

Run after 01_clean_part1_data.do:
    do "stata/02_part1_replication.do" "`c(pwd)'" 3
*/

args project_root leverage
if `"`project_root'"' == "" local project_root "`c(pwd)'"
if `"`leverage'"' == "" local leverage 3

local processed_dir "`project_root'/data/processed"
local outputs_dir   "`project_root'/outputs"
local part1_dir     "`outputs_dir'/part1"
local table_dir     "`part1_dir'/tables"
capture mkdir "`outputs_dir'"
capture mkdir "`part1_dir'"
capture mkdir "`table_dir'"

capture confirm file "`processed_dir'/part1_clean_prices.dta"
if _rc {
    display as error "Missing input: data/processed/part1_clean_prices.dta"
    exit 601
}

use "`processed_dir'/part1_clean_prices.dta", clear
sort Date
isid Date

generate double TQQQ_simple_ret = TQQQ_price / TQQQ_price[_n-1] - 1 if _n > 1
generate double NDX_simple_ret = NDX_price / NDX_price[_n-1] - 1 if _n > 1
generate double target_daily_ret = `leverage' * NDX_simple_ret
assert 1 + target_daily_ret > 0 if !missing(target_daily_ret)

generate double TQQQ_adjusted_price_wealth_index = TQQQ_price / TQQQ_price[1]
generate double TQQQ_idealized_3x_wealth_index = .
replace TQQQ_idealized_3x_wealth_index = 1 in 1
replace TQQQ_idealized_3x_wealth_index = TQQQ_idealized_3x_wealth_index[_n-1] ///
    * (1 + target_daily_ret) in 2/L
generate double tracking_gap_pct = ///
    TQQQ_adjusted_price_wealth_index / TQQQ_idealized_3x_wealth_index - 1

local price_rows = _N
local return_observations = _N - 1
local analysis_start = string(Date[1], "%tdCCYY-NN-DD")
local analysis_end = string(Date[_N], "%tdCCYY-NN-DD")
local adjusted_price_final = TQQQ_adjusted_price_wealth_index[_N]
local idealized_final = TQQQ_idealized_3x_wealth_index[_N]
local final_gap = tracking_gap_pct[_N]

quietly correlate TQQQ_simple_ret target_daily_ret
local daily_correlation = r(rho)
generate double actual_minus_ideal = TQQQ_simple_ret - target_daily_ret
quietly summarize actual_minus_ideal, detail
local mean_gap = r(mean)
local median_gap = r(p50)

preserve
keep Date TQQQ_adjusted_price_wealth_index TQQQ_idealized_3x_wealth_index tracking_gap_pct ///
    NDX_simple_ret
order Date TQQQ_adjusted_price_wealth_index TQQQ_idealized_3x_wealth_index tracking_gap_pct ///
    NDX_simple_ret
format Date %tdCCYY-NN-DD
label data "Part 1 adjusted-price and idealized wealth paths"
save "`table_dir'/part1_replication_path.dta", replace
restore

clear
set obs 11
generate str48 metric = ""
generate str80 value = ""
replace metric = "analysis_start" in 1
replace value = "`analysis_start'" in 1
replace metric = "analysis_end" in 2
replace value = "`analysis_end'" in 2
replace metric = "leverage_target" in 3
replace value = strtrim(string(`leverage', "%9.1f")) in 3
replace metric = "common_price_rows" in 4
replace value = strtrim(string(`price_rows', "%12.0f")) in 4
replace metric = "return_observations" in 5
replace value = strtrim(string(`return_observations', "%12.0f")) in 5
replace metric = "adjusted_price_final_wealth_index" in 6
replace value = strtrim(string(`adjusted_price_final', "%24.17g")) in 6
replace metric = "idealized_3x_final_wealth_index" in 7
replace value = strtrim(string(`idealized_final', "%24.17g")) in 7
replace metric = "final_tracking_gap_pct" in 8
replace value = strtrim(string(`final_gap', "%24.17g")) in 8
replace metric = "daily_return_correlation_actual_vs_3x_ndx" in 9
replace value = strtrim(string(`daily_correlation', "%24.17g")) in 9
replace metric = "mean_daily_actual_minus_ideal_return" in 10
replace value = strtrim(string(`mean_gap', "%24.17g")) in 10
replace metric = "median_daily_actual_minus_ideal_return" in 11
replace value = strtrim(string(`median_gap', "%24.17g")) in 11
label data "Part 1 replication summary"
save "`table_dir'/table_part1_replication.dta", replace

display as result "Replication path and summary DTA files created."
