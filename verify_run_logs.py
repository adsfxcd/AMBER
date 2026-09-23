"""Verify the redacted run-log supplement using Python's standard library."""
import csv
import hashlib
import json
import math
from pathlib import Path
import re


BASE = Path(__file__).resolve().parent


def read_csv(name):
    with (BASE / name).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def main():
    failures = []
    checks = 0

    def check(condition, message):
        nonlocal checks
        checks += 1
        if not condition:
            failures.append(message)

    runs = {row['run_id']: row for row in read_csv('runs.csv')}
    index = read_csv('run_log_index.csv')
    evidence = {row['run_id']: row for row in
                (json.loads(line) for line in
                 (BASE / 'metric_excerpts.jsonl').read_text(encoding='utf-8').splitlines() if line)}
    check(len(index) == len(runs) == 180, 'Run count')
    check({row['run_id'] for row in index} == set(runs), 'Run coverage')
    check(len({row['log_file'] for row in index}) == len(index), 'Unique log files')
    manifest = json.loads((BASE / 'run_log_checksums.json').read_text(encoding='utf-8'))
    for relative, expected in manifest['files'].items():
        file = BASE / relative
        check(file.is_file() and hashlib.sha256(file.read_bytes()).hexdigest() == expected,
              'Supplement hash: ' + relative)
    check({file.relative_to(BASE).as_posix() for file in (BASE / 'run_logs').glob('*/*.log')}
          == {row['log_file'] for row in index}, 'Log inventory')

    report_differences = []
    total_epochs = 0
    for row in index:
        rid = row['run_id']
        run = runs[rid]
        log = BASE / row['log_file']
        text = log.read_text(encoding='utf-8')
        check(hashlib.sha256(log.read_bytes()).hexdigest() == row['redacted_log_sha256'], 'Log hash: ' + rid)
        check(row['original_log_sha256'] == evidence[rid]['original_log_sha256'], 'Source hash link: ' + rid)
        for key in ['group_id', 'dataset', 'model', 'imr', 'seed_alias', 'process_return_code']:
            check(row[key] == run[key], 'Run metadata ' + key + ': ' + rid)
        original_lines = {}
        cursor = 1
        originals = sanitized = removed = 0
        for line in text.splitlines():
            if line.startswith('#') or not line:
                continue
            match = re.fullmatch(r'L(\d+)(?:-L(\d+))? \| (.*)', line)
            check(match is not None, 'Line format: ' + rid)
            if match is None:
                continue
            start = int(match[1])
            end = int(match[2] or match[1])
            body = match[3]
            check(start == cursor and end >= start, 'Source line order: ' + rid)
            cursor = end + 1
            if body.startswith('[REDACTED:'):
                removed += end - start + 1
            elif body.startswith('[SANITIZED] '):
                check(start == end, 'Sanitized line span: ' + rid)
                sanitized += 1
            else:
                check(start == end, 'Original line span: ' + rid)
                originals += 1
                original_lines[start] = body
        check(cursor == int(row['original_line_count']) + 1, 'Full source line accounting: ' + rid)
        check(originals == int(row['retained_original_line_count']), 'Original line count: ' + rid)
        check(sanitized == int(row['sanitized_line_count']), 'Sanitized line count: ' + rid)
        check(removed == int(row['removed_line_count']), 'Removed line count: ' + rid)
        for item in evidence[rid]['retained_lines']:
            check(original_lines.get(item['line_number']) == item['text'], 'Final excerpt match: ' + rid)
        joined = '\n'.join(original_lines.values())
        for label, key in [('Best test F1', 'wf1_pct'), ('Best test Acc', 'acc_pct'), ('Best dev F1', 'recorded_dev_wf1_pct')]:
            found = re.findall(r'^' + re.escape(label) + r': ([0-9.eE+\-]+)$', joined, re.M)
            check(len(found) == 1 and math.isclose(float(found[0]) * 100, float(run[key]), abs_tol=1e-8),
                  'Final metric ' + key + ': ' + rid)
        epochs = re.findall(r'^\[Epoch (\d+)\] \[Time: [^\]]+\]$', joined, re.M)
        check(len(epochs) == int(row['epoch_summary_count']) and len(epochs) > 0, 'Epoch count: ' + rid)
        check([int(value) for value in epochs] == list(range(len(epochs))), 'Epoch continuity: ' + rid)
        total_epochs += len(epochs)
        for label in ['Train Loss', 'Train F1', 'Train Acc', 'Dev Loss', 'Dev F1', 'Dev Acc']:
            check(len(re.findall(r'^\[' + label + r': [^\]]+\]$', joined, re.M)) == len(epochs),
                  'Epoch metric coverage ' + label + ': ' + rid)
        check(re.search(r'\bseed(?:_\d+|\s*[:=]\s*\d+|\s+set\s+\d+)', text, re.I) is None,
              'No numeric seed fields: ' + rid)
        check(re.search(r'[A-Za-z]:[\\/]|Namespace\(|--[a-zA-Z_]', text) is None, 'No commands or original paths: ' + rid)
        if row['best_report_matches_final_scalars_4dp'] != 'True':
            report_differences.append(rid)

    result = {'checks': checks, 'verification_failures': len(failures), 'run_logs': len(index),
              'epoch_summaries': total_epochs,
              'observed_report_scalar_differences': len(report_differences),
              'observed_nonzero_process_return_codes': sum(row['process_return_code'] != '0' for row in index),
              'scope': 'File consistency and links to provided run records; not training reproduction or resolution of source anomalies.',
              'failure_details': failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    raise SystemExit(bool(failures))


if __name__ == '__main__':
    main()
