# Realism calibration data specification — 2026-10-25

## Goal

This is a data request and validation protocol for a separately versioned `REALISM_CALIBRATED_MODEL`. It does not modify the reference-compliant model, add guessed parameters, or authorize a trial/checkpoint. The current official 5×5 matrix remains a reference-scenario exercise; it is not automatically a market forecast.

## Required separation

1. `REFERENCE_COMPLIANT_BASELINE`: implements the currently approved business rules and reports results conditional on those assumptions.
2. `REALISM_CALIBRATED_MODEL`: an independent model version calibrated and back-tested against lawful, representative operational or external data.

Never label the first as locally calibrated. Never silently move assumptions or empirical parameters from the second into the first.

## Minimum dataset and fields

Use pseudonymous IDs rather than names, phone numbers, national IDs, addresses or other direct identifiers. A data owner must confirm lawful use and provide the extraction date, covered geography, record completeness and known selection bias.

| Data domain | Required fields | Purpose |
|---|---|---|
| Contract and fleet | pseudonymous bike/contract ID, contract type, start/end dates, status transitions, rent due, actual receipt date and amount | Reconstruct contract states and rental cash flow |
| Collection behavior | due date, full/partial/missed payment, days in arrears, amount recovered later, write-off amount/date | Estimate empirical payment/arrears dynamics rather than a single assumed probability |
| Guarantee recovery | claim date, claim reason, gross claim, recovered amount/date, administrative/legal collection cost, unresolved/denied claims | Estimate recovery rate, delay, and collection cost distributions |
| Vacancy and demand | return/termination date, available date, re-rent date, days vacant, inquiries/offers/rejections where reliably recorded | Estimate downtime and re-leasing probability by season and location |
| Repair and utilization | repair/service event date, category, downtime start/end, parts/labour cost, mileage/use proxy if recorded | Estimate maintenance cost and availability impact |
| Loss, damage and insurance | incident date/type, repair/write-off cost, insurance premium/deductible/claim/payment delay, theft/loss | Capture material risk omitted by a simple rent-only model |
| Asset purchase and disposition | acquisition invoice/date, customs/registration/prep costs, depreciation policy, resale date/value/fees | Reconcile cash cost, book value and actual sale recovery |
| Financing and overhead | debt draw/repayment, interest/fees, taxes/licenses, admin/marketing costs, management hours/pay, dates | Separate operating return from financing and overhead |
| Macro and market covariates | geography, calendar date, documented rent/parts/vehicle price indices and exchange rates from named, dated, credible sources | Test inflation/currency scenarios; don't substitute countrywide projections for local realized costs without approval |
| Accounting control | opening/closing cash, assets/liabilities/equity by period, transaction ledger reference, reconciliation exceptions | Validate financial identities and avoid double counting |

## Data quality requirements

- Declare coverage period and geographical footprint; identify gaps, censoring, duplicate contracts and changed business processes.
- Distinguish contractual rent from cash received, recognized revenue, receivable, guarantee recovery and sale proceeds.
- Preserve event dates, not only month-end totals, where timing affects closure/cash.
- Reconcile sampled records back to source ledgers/invoices/bank statements where permitted.
- Document missingness and exclude neither bad outcomes nor unsuccessful collection attempts silently.
- Freeze a versioned raw-data extract and record hashes, schema, transformation code and row counts. Keep personally identifying data out of model artifacts.
- Split data chronologically into calibration, validation and untouched out-of-time test periods; avoid random row splits that leak the same contract or episode across sets.

## Calibration and validation plan

1. Descriptive checks: contract durations, arrears, recovery delays, vacancy, maintenance costs and net cash flow distributions with sample counts and uncertainty intervals.
2. Parameterize only quantities supported by sufficient data; mark rare/high-severity events as evidence-limited rather than assigning an invented probability.
3. Fit collection and recovery dynamics at contract/episode level while accounting for repeated behavior within a tenant/vehicle, calendar seasonality and relevant covariates only where supported.
4. Calibrate on the earliest period; validate on a later period; evaluate final performance on an untouched time period.
5. Compare predicted versus realized: collection rates by days past due, recovery amount/timing, contract termination, vacancy duration, maintenance/down-time costs, fleet utilization, cash balances, and net project cash flow.
6. Use calibration plots, proper scoring rules for probabilities, interval coverage, absolute/relative error for financials, and predeclared tolerance limits. Report uncertainty and sample size rather than a single apparent accuracy score.
7. Compare baseline and calibrated model side by side under the same explicitly defined policy; explain each difference by changed parameter/model equation and show sensitivity scenarios.
8. Do not use the same data both to tune the model and to claim independent accuracy. Record all exceptions and retain a model card with limitations.

## Release conditions for the realism version

- Owner approves the target decision/use, geography, population and forecast horizon.
- Data provenance, lawful access, completeness and privacy review pass.
- Every calibrated parameter cites a dataset, observation window, sample size, estimate, interval and transformation.
- Independent out-of-time validation meets tolerances agreed before seeing test results.
- Financial ledgers reconcile and all simulation/uncertainty gates for the new version pass.
- The new model has a new source/version identity, manifest and acceptance report; it cannot overwrite the reference-compliant baseline or its historic results.

## Current disposition

`DATA_NOT_PROVIDED / CALIBRATION_NOT_STARTED`. No actual operational dataset supporting these fields was available during this review. Public macro data may provide scenario context, but it cannot replace the project's own rental, collection, vacancy, maintenance and asset-disposition records.
