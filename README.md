# AMBER Results Evidence

Supporting results, redacted run logs, and verification scripts for the AMBER entries in Tables 2 and 3 of the paper.

The package contains 180 runs across 36 experimental conditions, with five runs per condition. It links 144 AMBER mean and standard-deviation cells to their contributing runs. Baseline and BALM values are transcribed from the paper; their individual run records are not included.

## Quick start

Open [results_summary.xlsx](./results_summary.xlsx) to browse the results, or use the CSV files for analysis.

To verify the package, run the following commands from this directory with Python 3. Both scripts use only the Python standard library.

```bash
python verify_tables.py
python verify_run_logs.py
```

Each script prints a JSON report and returns a nonzero exit status if a verification check fails.

## Results and traceability

| File | Contents and purpose |
| --- | --- |
| [results_summary.xlsx](./results_summary.xlsx) | Four worksheets: `Summary`, `Runs`, `Paper Values`, and `Cell Trace`. Provides a readable view of results and their supporting records. |
| [runs.csv](./runs.csv) | Metrics and metadata for 180 runs, including condition, seed alias, accuracy, weighted F1, selected epoch, recorded validation metric, and process status. Join other records using `run_id`. |
| [summary.csv](./summary.csv) | Means and sample standard deviations for 36 conditions, together with the values reported in the paper. |
| [cell_trace.csv](./cell_trace.csv) | Links each of 144 AMBER mean or standard-deviation cells to five contributing run IDs. Includes recomputed values and comparisons at two decimal places. |
| [paper_table_values.csv](./paper_table_values.csv) | Values transcribed from Tables 2 and 3, including baseline comparisons. The `evidence_scope` field distinguishes transcription from support by run records. |
| [delta_audit.csv](./delta_audit.csv) | Reported and recomputed Delta and Delta1 values, with checks using printed means and unrounded AMBER means. |
| [audit_summary.json](./audit_summary.json) | Counts of runs, log matches, metric cells, and delta comparisons. |

## Run logs

| File or directory | Contents and purpose |
| --- | --- |
| [run_logs/](./run_logs/) | 180 redacted log copies, organized into groups `G01` through `G36`, with five files per group. Includes per-epoch metrics, classification reports, and final outputs. |
| [run_log_index.csv](./run_log_index.csv) | Maps runs to relative log paths and records source and redacted-file hashes, line counts, final metrics, and classification-report comparison fields. |
| [metric_excerpts.jsonl](./metric_excerpts.jsonl) | Four final metric lines per run, with source line numbers and source-file hashes. Provides direct access to the selected epoch, validation F1, test F1, and accuracy. |

A log filename matches its run ID. For example, `run_logs/G01/G01-seed1.log` corresponds to `G01-seed1` in `runs.csv`. The `L` prefixes in logs refer to line numbers in the source text. Redaction markers account for omitted source lines.

## Definitions and identifiers

- `group_id` identifies a dataset, model, and missing-rate condition. A group contains five runs.
- `run_id` identifies one run, such as `G01-seed1`.
- `seed_alias` values `seed1` through `seed5` are aliases within a group. They do not disclose the original numeric random seeds.
- `imr` lists the missing rates in audio, language, and visual order: `(A, L, V)`.
- `Acc` is accuracy and `w-F1` is weighted F1. The workbook and CSV metric fields ending in `_pct` store percentage values, such as `61.85`, rather than fractions, such as `0.6185`. Retained log excerpts preserve their source scale.
- `SD` is the sample standard deviation across the five runs, with `ddof = 1`.
- `2dp` means comparison after rounding to two decimal places. Full-precision values remain available in the CSV files.

## Verification files

| File | Checks |
| --- | --- |
| [verify_tables.py](./verify_tables.py) | Package hashes, run records, final metric excerpts, means, sample standard deviations, and delta arithmetic. |
| [verify_run_logs.py](./verify_run_logs.py) | Log hashes, run metadata, source-line accounting, final excerpts, and per-epoch metric coverage. |
| [checksums.json](./checksums.json) | SHA-256 hashes for every distributed file except this manifest itself. |
| [run_log_checksums.json](./run_log_checksums.json) | SHA-256 hashes for the log files, log index, and log verification script. |

Verification establishes file consistency, arithmetic, and links between the supplied records. Source observations, including classification-report/scalar differences and nonzero process exit codes, remain visible in the index, audit data, and verification output. Training reproduction and resolution of those observations are outside the scripts' scope.

## Repository conventions

Data and script filenames use lowercase English words separated by underscores. `README.md` follows the GitHub convention. Group directories and log filenames retain their stable run identifiers.

All file references are relative to this directory. Text files use UTF-8. The [Git attributes](./.gitattributes) preserve file bytes during checkout so that line-ending conversion does not invalidate the SHA-256 manifests. The [ignore rules](./.gitignore) exclude common local caches and temporary files.
