"""Verify anonymous result records and arithmetic. No training/model dependencies."""
import csv
import hashlib
import json
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent


def read_csv(name):
    with (BASE / name).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def close(a, b, tol=1e-8):
    return math.isclose(float(a), float(b), abs_tol=tol, rel_tol=0)


def main():
    failures = []
    checks = 0

    def check(condition, description):
        nonlocal checks
        checks += 1
        if not condition:
            failures.append(description)

    manifest = json.loads((BASE / 'checksums.json').read_text(encoding='utf-8'))
    for name, expected in manifest.items():
        path = BASE / name
        check(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected, 'File hash: ' + name)

    runs = read_csv('runs.csv')
    summaries = read_csv('summary.csv')
    cells = read_csv('cell_trace.csv')
    groups = defaultdict(list)
    by_id = {}
    for row in runs:
        check(row['run_id'] not in by_id, 'Duplicate run ID: ' + row['run_id'])
        by_id[row['run_id']] = row
        groups[row['group_id']].append(row)
        check(bool(re.fullmatch(r'seed\d+', row['seed_alias'])), 'Invalid anonymous alias')
    for row in summaries:
        group = groups[row['group_id']]
        check(len(group) == int(row['run_count']) == 5, 'Run count: ' + row['group_id'])
        check({r['seed_alias'] for r in group} == {f'seed{i}' for i in range(1, 6)}, 'Alias coverage: ' + row['group_id'])
        for prefix, key in [('acc', 'acc_pct'), ('wf1', 'wf1_pct')]:
            values = [float(r[key]) for r in group]
            check(close(statistics.mean(values), row[prefix + '_mean']), 'Mean: ' + row['group_id'])
            check(close(statistics.stdev(values), row[prefix + '_std']), 'Sample SD: ' + row['group_id'])
    for cell in cells:
        relevant = [by_id[rid] for rid in cell['run_ids'].split(';')]
        key = 'acc_pct' if cell['metric'] == 'Acc' else 'wf1_pct'
        values = [float(r[key]) for r in relevant]
        calc = statistics.mean(values) if cell['statistic'] == 'mean' else statistics.stdev(values)
        check(close(calc, cell['recomputed_value']), 'Cell computation: ' + cell['cell_id'])
        matches = close(round(calc, 2), cell['reported_value'])
        check(str(matches) == cell['matches_2dp'], 'Cell status: ' + cell['cell_id'])

    evidence = [json.loads(line) for line in (BASE / 'metric_excerpts.jsonl').read_text(encoding='utf-8').splitlines() if line]
    for item in evidence:
        row = by_id[item['run_id']]
        extracted = {}
        for line in item['retained_lines']:
            for label, key in [('Best test F1:', 'wf1_pct'), ('Best test Acc:', 'acc_pct')]:
                if line['text'].startswith(label):
                    extracted[key] = float(line['text'].split(':', 1)[1]) * 100
        actual_match = all(k in extracted and close(extracted[k], row[k]) for k in ['acc_pct', 'wf1_pct'])
        check(actual_match or row['log_metrics_match'] == 'False', 'Excerpt metrics: ' + item['run_id'])
        check(item['evidence_id'] == row['evidence_id'], 'Evidence link: ' + item['run_id'])

    paper = read_csv('paper_table_values.csv')
    by_cell = {(r['table'], r['row_label'], r['imr'], r['metric']): r for r in paper}
    by_group = {r['group_id']: r for r in summaries}
    for item in read_csv('delta_audit.csv'):
        group = by_group[item['group_id']]
        prefix = 'acc' if item['metric'] == 'Acc' else 'wf1'
        if item['comparison'] == 'original':
            ref = float(group['original_' + prefix])
        else:
            names = ['MMIN', 'GCNet', 'MoMKE', 'Ada2I', 'RedCore', 'Mi-CGA', 'SDR-GNN']
            if group['table'] == '2':
                names.append('MCE')
            ref = statistics.mean(float(by_cell[(group['table'], name, group['imr'], item['metric'])]['reported_value']) for name in names)
        calc = float(group['paper_' + prefix + '_mean']) - ref
        check(close(calc, item['recomputed_from_printed_means']), 'Delta computation: ' + item['group_id'])
        check(str(close(round(calc, 2), item['reported_delta'])) == item['matches_2dp'], 'Delta status: ' + item['group_id'])
        full_calc = float(group[prefix + '_mean']) - ref
        check(close(full_calc, item['recomputed_from_unrounded_amber']), 'Unrounded delta: ' + item['group_id'])
        check(str(close(round(full_calc, 2), item['reported_delta'])) == item['matches_unrounded_amber_2dp'], 'Unrounded delta status: ' + item['group_id'])
    print(json.dumps({'checks': checks, 'failures': len(failures), 'groups': len(groups),
                      'run_count': len(runs),
                      'reported_cell_mismatches': sum(r['matches_2dp'] != 'True' for r in cells),
                      'failure_details': failures}, indent=2))
    raise SystemExit(1 if failures else 0)


if __name__ == '__main__':
    main()
