"""Check numerical dependencies between optical rows; never assign anatomy or units.

Fit candidate two-row equations on at most 4096 spread-out samples, then measure
residuals across every sample. This is an export consistency check, not a
prediction model or an independent physiological validation.
"""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path

import numpy as np

from physionet_inventory import manifest_entries, recording_paths, write_json


def dependencies(optical, concentration):
    if optical.shape != concentration.shape or optical.shape[0] != 16:
        raise ValueError('Expected two blocks of 16 rows with equal sample counts')
    if not np.isfinite(optical).all() or not np.isfinite(concentration).all():
        return {'status': 'nonfinite_input_no_equations_fitted'}
    indices = np.linspace(0, optical.shape[1] - 1, min(4096, optical.shape[1]), dtype=int)
    x = optical[:, indices].T
    y = concentration[:, indices].T
    mean_x, scale_x = x.mean(0), x.std(0)
    mean_y, scale_y = y.mean(0), y.std(0)
    if (scale_x == 0).any() or (scale_y == 0).any():
        return {'status': 'constant_input_or_output_no_equations_fitted'}
    normalized_x = (x - mean_x) / scale_x
    normalized_y = (y - mean_y) / scale_y
    design = np.column_stack((normalized_x, np.ones(len(indices))))
    coefficients, _, rank, _ = np.linalg.lstsq(design, normalized_y, rcond=None)
    if rank != 17:
        return {'status': 'rank_deficient_mapping_not_identifiable', 'design_rank': int(rank)}
    equations = []
    for output in range(16):
        pair = np.sort(np.argsort(np.abs(coefficients[:-1, output]))[-2:])
        pair_design = np.column_stack((normalized_x[:, pair], np.ones(len(indices))))
        fitted, _, pair_rank, _ = np.linalg.lstsq(pair_design, normalized_y[:, output], rcond=None)
        full_x = (optical[pair].T - mean_x[pair]) / scale_x[pair]
        prediction = np.einsum('ij,j->i', full_x, fitted[:2]) + fitted[2]
        actual = (concentration[output] - mean_y[output]) / scale_y[output]
        error = prediction - actual
        raw_coefficients = fitted[:2] * scale_y[output] / scale_x[pair]
        intercept = mean_y[output] + fitted[2] * scale_y[output] - np.sum(mean_x[pair] * raw_coefficients)
        equations.append({
            'concentration_row_1based': output + 18,
            'candidate_input_rows_1based': (pair + 2).tolist(),
            'pair_design_rank': int(pair_rank),
            'raw_coefficients': raw_coefficients.tolist(), 'raw_intercept': float(intercept),
            'all_samples_rms_error_in_fit_output_sd': float(np.sqrt(np.mean(error**2))),
            'all_samples_max_error_in_fit_output_sd': float(np.max(np.abs(error))),
        })
    updates = []
    for index, row in enumerate(optical, 2):
        changes = np.flatnonzero(np.diff(row) != 0) + 1
        spacing, counts = np.unique(np.diff(changes), return_counts=True)
        updates.append({
            'row_1based': index, 'change_count': len(changes),
            'first_change_index': int(changes[0]) if len(changes) else None,
            'change_spacing_samples': {str(int(s)): int(c) for s,c in zip(spacing,counts)},
        })
    return {'status': 'equations_measured_not_physical_metadata', 'design_rank': int(rank),
            'fit_sample_count': len(indices), 'checked_sample_count': optical.shape[1],
            'equations': equations, 'stored_value_updates': updates}



def load_verified_optical(path, expected_sha256):
    with path.open('rb') as source:
        digest = hashlib.sha256()
        while True:
            chunk = source.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        if digest.hexdigest() != expected_sha256:
            raise ValueError(f'Current recording SHA-256 mismatch: {path.name}')
        source.seek(0)
        return np.loadtxt(source, delimiter=',', max_rows=33)


def self_check():
    generator = np.random.default_rng(49)
    optical = generator.normal(size=(16, 500))
    concentration = np.empty_like(optical)
    for i in range(0,16,2):
        concentration[i] = 2 * optical[i] - .3 * optical[i+1] + 5
        concentration[i+1] = -.4 * optical[i] + 3 * optical[i+1] - 7
    result = dependencies(optical, concentration)
    for i, equation in enumerate(result['equations']):
        assert equation['candidate_input_rows_1based'] == [2+2*(i//2),3+2*(i//2)]
        assert equation['all_samples_max_error_in_fit_output_sd'] < 1e-10
    assert dependencies(np.zeros_like(optical), concentration)['status'].startswith('constant')
    optical[0,0] = np.nan
    assert dependencies(optical, concentration)['status'].startswith('nonfinite')
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory)/'recording.csv'
        np.savetxt(path, np.zeros((33, 4)), delimiter=',')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert load_verified_optical(path, digest).shape == (33, 4)
        np.savetxt(path, np.ones((33, 4)), delimiter=',')
        try:
            load_verified_optical(path, digest)
        except ValueError:
            pass
        else:
            raise AssertionError('Modified recording was accepted')
    print('OPTICAL CHECKS PASSED')



def verify_evidence(inventory_directory):
    self_check()
    entries = manifest_entries((inventory_directory/'source-metadata/SHA256SUMS.txt').read_bytes())
    paths = recording_paths(entries)
    evidence = json.loads((inventory_directory/'optical-consistency.json').read_text())
    assert evidence['script_sha256'] == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    records = evidence['results']
    assert len(records) == len(paths)
    assert {r['participant'] for r in records} == {Path(p).stem for p in paths}
    by_id = {Path(p).stem: entries[p] for p in paths}
    for record in records:
        assert record['source_recording_sha256'] == by_id[record['participant']]
        base = json.loads((inventory_directory/(record['participant']+'.json')).read_text())
        assert record['checked_sample_count'] == base['time']['sample_count']
        assert record['status'] == 'equations_measured_not_physical_metadata'
        assert len(record['equations']) == 16
        for i, equation in enumerate(record['equations'], 18):
            assert equation['concentration_row_1based'] == i
            pair = equation['candidate_input_rows_1based']
            assert len(set(pair)) == 2 and all(2 <= x <= 17 for x in pair)
            assert np.isfinite(equation['all_samples_max_error_in_fit_output_sd'])
            assert np.isfinite(equation['all_samples_rms_error_in_fit_output_sd'])
    print('OPTICAL EVIDENCE VERIFIED')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-existing', action='store_true')
    parser.add_argument('--self-check', action='store_true')
    parser.add_argument('--cache-dir', type=Path, default=Path('data/physionet/neuro-stress-resilience-hci/1.0.0'))
    parser.add_argument('--inventory', type=Path, default=Path('docs/validation/physionet'))
    args = parser.parse_args()
    if args.verify_existing:
        verify_evidence(args.inventory)
        return
    if args.self_check:
        self_check()
        return
    entries = manifest_entries((args.inventory/'source-metadata/SHA256SUMS.txt').read_bytes())
    results = []
    for path in recording_paths(entries):
        participant = Path(path).stem
        inventory = json.loads((args.inventory/f'{participant}.json').read_text())
        if not inventory['integrity_verified'] or inventory['sha256'] != entries[path]:
            raise ValueError(f'No verified recording inventory: {participant}')
        values = load_verified_optical(args.cache_dir/path, entries[path])
        result = dependencies(values[1:17], values[17:33])
        result.update(participant=participant, source_recording_sha256=entries[path])
        results.append(result)
        print(participant, result['status'], flush=True)
    write_json(args.inventory/'optical-consistency.json', {
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'interpretation': 'Empirical numerical dependencies only; electrode/source/detector names, wavelengths, HbO/HbR and physical units remain unassigned.',
        'method': 'Discover two strongest standardized predictors from all 16 inputs, refit that pair on up to4096 equally spaced samples, evaluate every recorded sample. Fit samples are included in evaluation; this is not prediction performance.',
        'results': results,
    })


if __name__ == '__main__':
    main()
