# Evaluation and Non0 Reporting Protocol

This note clarifies the metric rules for the AMBER results in Tables 2 and 3. It is based on the manuscript's evaluation description, the supplied GCNet, MMGCN, and MM-DFN evaluation implementations, and the released run logs. The public package does not yet include per-example predictions or the complete model code.

## CMU-MOSEI: Non0 binary metrics

Let `y` be an example's continuous ground-truth sentiment score and `s` the model's continuous predicted score.

1. Retain an example for binary metric calculation if and only if `y != 0`. This decision uses the ground truth alone; a prediction of zero does not remove an example.
2. For retained examples, the true class is **Positive** when `y > 0` and **Negative** when `y < 0`.
3. The predicted class is **Positive** when `s > 0` and **Negative** when `s <= 0`. A predicted score exactly equal to zero is therefore Negative.
4. Compute accuracy and support-weighted F1 on the same retained examples. The evaluation implementations use `accuracy_score` and `f1_score(..., average="weighted", zero_division=0)` for validation and test metrics.

The same Non0 filtering is applied when calculating the CMU-MOSEI validation weighted F1 used to select the best checkpoint. The final test Acc and w-F1 are measured on that checkpoint. Test results are not used to choose the checkpoint.

## IEMOCAP

IEMOCAP is evaluated as a six-class emotion classification task. The CMU-MOSEI Non0 exclusion does not apply. Accuracy and support-weighted F1 are calculated over the test examples in the corresponding run.

## Why some GCNet classification reports differ

For CMU-MOSEI, the GCNet evaluation implementation returns Non0-filtered Acc and weighted F1, but prints `classification_report` from the unfiltered ground-truth and prediction arrays. Zero-ground-truth examples are consequently present in that printed report and are mapped to Negative by its `> 0` threshold. The final `Best test Acc` and `Best test F1` log lines use the filtered metrics recorded in [runs.csv](./runs.csv) and the paper tables.

This reporting difference is visible in all 30 released CMU-MOSEI GCNet+AMBER logs: their printed classification reports have support **4,659**, and their report metrics differ from the final scalar lines. The corresponding MMGCN+AMBER and MM-DFN+AMBER reports apply Non0 filtering before printing; each has support **3,634**, and its report metrics agree with the final scalar lines. These observations are indexed in [run_log_index.csv](./run_log_index.csv).

## Across-run statistics

For each dataset, backbone, and missing-rate condition, the reported AMBER mean and sample standard deviation are calculated from the five run-level metrics after checkpoint selection. The standard deviation uses `ddof = 1`. See [summary.csv](./summary.csv) and [cell_trace.csv](./cell_trace.csv) for the contributing run IDs and recomputed statistics.
