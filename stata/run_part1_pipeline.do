version 18.0
clear all
set more off

/* Run the complete Stata cleaning and replication pipeline. */
args project_root
if `"`project_root'"' == "" local project_root "`c(pwd)'"

do "`project_root'/stata/01_clean_part1_data.do" "`project_root'"
do "`project_root'/stata/02_part1_replication.do" "`project_root'" 3

display as result "Part 1 Stata pipeline completed successfully."
