# Data Engineering — Working Standards

## What This Project Type Demands
Data pipelines are the infrastructure of trust. Corrupt data propagates silently and corrupts every downstream decision, model, and report. Every pipeline must be idempotent, observable, and recoverable. Bad data must be quarantined, not silently dropped or corrupted. The most important property of a data pipeline is correctness, not performance.

## Before Starting Any Pipeline
- Define the data contract: source schema, expected frequency, acceptable latency, and downstream consumers.
- Define data quality rules before writing any transformation code: what makes a record valid? What is done with invalid records?
- Establish the idempotency strategy: how does re-running the pipeline for the same time window produce the same result?
- Identify all PII fields and their handling requirements (masking, encryption, exclusion) before writing any code.
- Plan the backfill strategy: how do you reprocess historical data if logic changes?

## Architecture Standards
- Raw data is always immutable. Never overwrite or modify raw source data.
- Medallion architecture: raw → validated → transformed → serving. Each stage has quality gates.
- Pipelines are idempotent by design: delete-and-replace output, not append-only, unless the use case specifically requires append semantics.
- All transformations are pure functions where possible: same input always produces same output.
- Schema is defined and enforced explicitly at every stage — not inferred or assumed.
- Incremental processing over full scans wherever possible. Full scans are justified and documented.

## How to Approach Any Task
1. Define and validate the input schema before writing transformation logic.
2. Write the transformation as a testable function — not as a monolithic script.
3. Add data quality checks at the output boundary before the result is made available to consumers.
4. Test with: happy path data, missing fields, null values, schema violations, and duplicate records.
5. Verify idempotency: run the pipeline twice and confirm the output is identical.

## Non-Negotiable Rules
- Every pipeline re-run for the same input produces the same output (idempotent). No exceptions.
- Invalid records are never silently dropped. They go to a quarantine/dead-letter store with the reason.
- PII fields are identified and handled at the point of ingestion — not as an afterthought.
- Schema changes must be backward-compatible, or handled through explicit versioning.
- Row counts are logged at every stage: input count, output count, quarantined count.
- All pipelines are tested in a staging environment with production-representative data volumes before deployment.
- No pipeline reads from and writes to the same table in the same run. This creates corruption risk.

## Observability Standards
Every pipeline run logs:
- Start time, end time, pipeline name, pipeline version.
- Input record count, output record count, quarantined record count.
- Any schema violations encountered and their count.
- Data freshness: timestamp of the latest record processed.

Alerts are configured for:
- Pipeline failure.
- SLA breach (data not available within the defined window).
- Anomalous row counts (>50% deviation from baseline).
- Data quality threshold violations.

## Testing Standards
- Unit test all transformation functions with representative inputs and known expected outputs.
- Include edge cases: empty input, all-null fields, max-length strings, duplicate keys.
- Integration test: run the full pipeline with a small representative dataset and validate the output schema and record counts.
- Verify idempotency in tests: run twice, compare outputs.
- Test late-arriving data for streaming pipelines.

## Definition of Done
- [ ] Input schema validated at ingestion.
- [ ] Output schema validated before serving.
- [ ] Data quality checks pass (no violations above threshold).
- [ ] Invalid records quarantined with reason, not silently dropped.
- [ ] Pipeline is idempotent (verified by running twice and comparing outputs).
- [ ] PII fields identified and handled according to data classification policy.
- [ ] Row counts logged at every stage.
- [ ] Backfill strategy documented.
- [ ] Tested at production-representative data volume in staging.
- [ ] Alerts configured for failure, SLA breach, and anomalous row counts.
