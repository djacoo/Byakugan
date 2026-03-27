# Machine Learning Project — Working Standards

## What This Project Type Demands
ML projects fail most often due to data quality issues, data leakage, and lack of reproducibility — not because the model choice was wrong. Before thinking about algorithms, get the data right, establish reproducibility, and define how you will measure success. Code quality standards apply fully: notebooks are for exploration, not for production pipeline logic.

## Before Starting Any Work
- Define the success metric in precise, measurable terms (F1 ≥ 0.85 on held-out test set). If no metric is defined, establish one before writing code.
- Define the baseline: what does the current solution achieve? What does a naive baseline (majority class, mean prediction) achieve?
- Define the data contract: what features are available at inference time? Any feature not available at inference time is data leakage.
- Establish reproducibility upfront: random seeds, dependency versions, data versioning, and experiment tracking.
- Determine the evaluation split strategy before any data is seen: time-based for temporal data, group-based for grouped data, stratified for imbalanced classes.

## Project Structure Standards
- Raw data is read-only. Never modify raw data files. Document where raw data comes from.
- Code goes in `src/`, notebooks go in `notebooks/` (exploration only). Notebooks must not be the authoritative implementation of any pipeline step.
- All parameters (hyperparameters, file paths, thresholds) live in config files or CLI arguments. No hardcoded values in source code.
- Experiments are tracked: every run records the model version, data version, hyperparameters, and all metrics.

## How to Approach Any Task
1. Validate the data first. Understand distributions, missing values, and class balance before modeling.
2. Start with the simplest possible model that could work. Establish a baseline before adding complexity.
3. Use a proper train/validation/test split. Apply all preprocessing transforms fit only on training data.
4. Track every experiment. If it is not tracked, it did not happen.
5. Evaluate on the held-out test set only at the very end, after all decisions are made. Never use the test set to guide modeling decisions.

## Non-Negotiable Rules
- Never use future information as a feature. If a feature would not be known at inference time, it must not be used in training.
- The train/validation/test split must be established before any data is seen. Never adjust the split after seeing results.
- Preprocessing must be fit on training data only. The same fitted transformer is applied to validation and test data.
- Every experiment must be reproducible from a git commit hash + a config file + a data version.
- No notebook code in production pipelines. All production logic is in proper Python modules with tests.
- Validate data quality at every pipeline stage boundary. Do not assume the previous step produced clean data.

## Evaluation Standards
- Report multiple metrics. Accuracy alone is insufficient for any real problem.
- Perform error analysis: examine the hardest failures manually. Document what you find.
- Evaluate across subgroups (age, region, category) if the system's decisions affect different groups differently.
- Compare against the established baseline in every experiment report.
- Document the evaluation methodology completely: split strategy, metrics, subgroup analysis.

## Reproducibility Checklist
- [ ] All random seeds set: `numpy`, `random`, `torch`, `sklearn`, framework-specific.
- [ ] All dependencies version-pinned in `requirements.txt` or `pyproject.toml`.
- [ ] Data version documented (hash, DVC tag, or S3 path with version).
- [ ] Git commit hash recorded with every experiment.
- [ ] Experiment tracked in MLflow, W&B, or equivalent.
- [ ] Config files committed and linked to experiment runs.

## Definition of Done
- [ ] No data leakage (verified by checking that no future or inference-unavailable information is used as a feature).
- [ ] Train/validation/test split is reproducible and was established before modeling.
- [ ] Preprocessing fit only on training data.
- [ ] Experiment tracked with all hyperparameters and metrics recorded.
- [ ] Evaluation includes multiple metrics and error analysis.
- [ ] All pipeline logic is in tested Python modules (not notebooks).
- [ ] Model can be serialized, loaded, and produces identical predictions.
- [ ] Results compared against baseline and documented.
