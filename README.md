# NGO Nutrition Program Briefing & Automated Monday Report

A Python reporting workflow for a Nairobi NGO tracking six-month nutrition outcomes across three counties (`Nairobi`, `Kitui`, `Machakos`), pairing plain-language donor headlines with a self-contained weekly HTML briefing.

## Key Headlines & Charts
1. **Kitui delivered the strongest weight recovery across the program** — Horizontal bar chart (`charts/county_performance.png`)
2. **Families who showed up regularly saw steadier weight gains** — Scatter plot with trend line (`charts/attendance_outcomes.png`)
3. **Younger children bounced back faster than older participants** — Grouped bar chart (`charts/age_differences.png`)

## What the Output Looks Like
Running `nutrition_report.py` creates `reports/report_YYYY-MM-DD.html` (for example, `reports/report_2026-11-16.html`). Each file is self-contained:
* Displays the report date in the page title and header.
* Opens with a one-paragraph plain-language summary for non-technical leadership and donors.
* Embeds all three PNG charts as Base64 data URIs inside the HTML, so the program director can open it in any browser, print it to PDF, or forward the single `.html` file without attaching separate image folders.
