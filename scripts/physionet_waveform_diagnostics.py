"""Data-level metadata clues; all physical interpretations remain hypotheses.

Run from the repository root. Reads and hashes cached recordings; no network calls.
EEG geometry uses eight 4096-sample windows spread after the first 60 seconds.
Optical update counts use all samples after 60 seconds. No quality exclusions.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np

from physionet_inventory import manifest_entries, recording_paths

ROOT = Path('docs/validation/physionet')
CACHE = Path('data/physionet/neuro-stress-resilience-hci/1.0.0')
BANDS = {'1_4_Hz': (1, 4), '8_13_Hz': (8, 13), '1_30_Hz': (1, 30)}


def geometries():
    rows = [line.split() for line in (ROOT/'source-metadata/EEG_32_Channel_mapping.xyz').read_text().splitlines()]
    labels = [r[4].upper() for r in rows]
    xyz = np.array([[float(v) for v in r[1:4]] for r in rows])
    methods = labels.copy()
    methods[3:7] = ['F3', 'FZ', 'F4', 'F8']
    methods[19:22] = ['CP1', 'CP2', 'CP4']
    return {'numbered': xyz, 'methods': xyz[[labels.index(label) for label in methods]]}


def geometry_score(correlation, xyz):
    distance = np.linalg.norm(xyz[:, None] - xyz[None, :], axis=2)
    upper = np.triu_indices(len(xyz), 1)
    return float(np.corrcoef(correlation[upper], -distance[upper])[0, 1])


def reference_ratio(eeg):
    return float(np.sqrt(np.mean(eeg.mean(axis=0)**2) / np.mean(eeg**2)))


def histogram(values):
    unique, counts = np.unique(values, return_counts=True)
    return {str(int(k)): int(v) for k, v in zip(unique, counts)}


def inspect(item):
    relative, expected = item
    participant = Path(relative).stem
    inventory = json.loads((ROOT/(participant+'.json')).read_text())
    n = inventory['time']['sample_count']
    starts = np.linspace(15000, n-4096, 8, dtype=int)
    indices = starts[:, None] + np.arange(4096)
    eeg, optical, changes, statistics = [], [], [], []
    digest = hashlib.sha256()
    with (CACHE/relative).open('rb') as source:
        for row, line in enumerate(source, 1):
            digest.update(line)
            if not (2 <= row <= 17 or 34 <= row <= 65):
                continue
            a = np.fromstring(line.decode('ascii'), sep=',')
            assert len(a) == n and np.isfinite(a).all(), (participant, row)
            later = a[15000:]
            statistics.append({
                'row': row, 'after_60s_quantiles_1_50_99': np.quantile(later, [.01, .5, .99]).tolist(),
                'first_60s_max_abs': float(np.max(np.abs(a[:15000]))),
                'after_60s_max_abs': float(np.max(np.abs(later))),
                'float32_roundtrip_within_1e_12_relative_fraction': float(np.mean(
                    np.abs(a-a.astype('float32').astype('float64')) <= 1e-12*np.maximum(np.abs(a), 1e-30))),
            })
            if row <= 17:
                optical.append(a[:n//25*25].reshape(-1, 25).mean(axis=1))
                changes.append(np.diff(later) != 0)
            else:
                eeg.append(a[indices])
    if digest.hexdigest() != expected:
        raise ValueError(f'Current recording checksum mismatch: {participant}')
    eeg = np.array(eeg)
    spectral = np.fft.rfft(eeg-eeg.mean(axis=2, keepdims=True), axis=2)
    frequency = np.fft.rfftfreq(4096, .004)
    correlations, scores = {}, {}
    for name, (low, high) in BANDS.items():
        filtered = np.fft.irfft(spectral*((frequency >= low) & (frequency <= high)), n=4096, axis=2)
        correlation = np.mean([np.corrcoef(filtered[:, w, :]) for w in range(8)], axis=0)
        assert np.isfinite(correlation).all()
        correlations[name] = correlation.tolist()
        scores[name] = {key: geometry_score(correlation, xyz) for key, xyz in geometries().items()}
    changes = np.array(changes)
    any_change = np.flatnonzero(changes.any(axis=0)) + 15001
    per_row_changes = [np.flatnonzero(c)+15001 for c in changes]
    # Remove drift by first differences of one-second optical means.
    optical = np.array(optical)[:, 600:]
    optical = optical[:, :optical.shape[1]//10*10].reshape(16, -1, 10).mean(axis=2)
    optical_corr = np.corrcoef(np.diff(optical, axis=1))
    centered = eeg.reshape(32, -1)
    centered = centered-centered.mean(axis=1, keepdims=True)
    eigenvalues = np.linalg.eigvalsh(centered @ centered.T)
    result = {
        'participant': participant, 'source_sha256': digest.hexdigest(), 'sample_count': n,
        'eeg_window_starts_samples': starts.tolist(), 'row_statistics': statistics,
        'eeg_channel_mean_rms_over_channel_rms': reference_ratio(eeg),
        'eeg_smallest_over_largest_covariance_eigenvalue': float(eigenvalues[0]/eigenvalues[-1]),
        'eeg_geometry_scores': scores, 'eeg_correlations': correlations,
        'optical_difference_correlations': optical_corr.tolist(),
        'optical_any_value_change_gap_samples': histogram(np.diff(any_change)),
        'optical_rows_changed_per_sample': histogram(changes.sum(axis=0)),
        'optical_per_row_change_counts': [len(c) for c in per_row_changes],
        'optical_per_row_change_phase_mod25': [np.bincount(c % 25, minlength=25).tolist() for c in per_row_changes],
    }
    print(participant, 'waveforms inspected and checksum verified', flush=True)
    return result


def self_check():
    rng = np.random.default_rng(49)
    eeg = rng.normal(size=(32, 2048))
    assert reference_ratio(eeg-eeg.mean(axis=0)) < 1e-14
    assert reference_ratio(eeg) > .1
    xyz = rng.normal(size=(32, 3))
    distance = np.linalg.norm(xyz[:, None]-xyz[None, :], axis=2)
    correlation = np.exp(-distance)
    assert geometry_score(correlation, xyz) > .85
    assert geometry_score(correlation, xyz[rng.permutation(32)]) < .3
    assert histogram(np.diff(np.arange(0, 100, 25))) == {'25': 3}
    print('WAVEFORM CONTROLS PASSED')


def optical_partition_summary(records):
    """Compare all 35 unordered four-plus-four partitions; never name a side."""
    upper = np.triu_indices(8, 1)
    splits = [(0,) + rest for rest in itertools.combinations(range(1, 8), 3)]
    output = []
    for wavelength in [0, 1]:
        correlations = [np.array(r['optical_difference_correlations'])[wavelength::2, wavelength::2]
                        for r in records]
        scores = []
        for subset in splits:
            within = np.array([(a in subset) == (b in subset) for a, b in zip(*upper)])
            scores.append([float(c[upper][within].mean()-c[upper][~within].mean())
                           for c in correlations])
        scores = np.array(scores)
        output.append({'input_pair_offset': wavelength,
                       'sequential_split_best_count': int(np.sum(np.argmax(scores, axis=0) == 0)),
                       'sequential_split_advantages': scores[0].tolist(),
                       'tested_partition_count': len(splits)})
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-existing', action='store_true')
    args = parser.parse_args()
    self_check()
    entries = manifest_entries((ROOT/'source-metadata/SHA256SUMS.txt').read_bytes())
    for name in ['EEG_32_Channel_mapping.xyz', 'fNIRS_frontal.xyz']:
        assert hashlib.sha256((ROOT/'source-metadata'/name).read_bytes()).hexdigest() == entries[name]
    paths = recording_paths(entries)
    destination = ROOT/'waveform-diagnostics.json'
    script_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if args.verify_existing:
        saved = json.loads(destination.read_text())
        assert saved['script_sha256'] == script_hash
        records = saved['records']
        assert len(records) == len(paths)
        assert {r['participant'] for r in records} == {Path(p).stem for p in paths}
        expected = {Path(p).stem: entries[p] for p in paths}
        assert saved['optical_partition_summary'] == optical_partition_summary(records)
        for record in records:
            assert record['source_sha256'] == expected[record['participant']]
            assert len(record['row_statistics']) == 48
            assert {s['row'] for s in record['row_statistics']} == set(range(2, 18)) | set(range(34, 66))
            inventory = json.loads((ROOT/(record['participant']+'.json')).read_text())
            assert record['sample_count'] == inventory['time']['sample_count']
            assert len(record['eeg_window_starts_samples']) == 8
            for band in BANDS:
                correlation = np.array(record['eeg_correlations'][band])
                assert correlation.shape == (32, 32) and np.isfinite(correlation).all()
                for key, xyz in geometries().items():
                    assert np.isclose(geometry_score(correlation, xyz), record['eeg_geometry_scores'][band][key])
        print('WAVEFORM EVIDENCE VERIFIED')
        return
    with ProcessPoolExecutor(max_workers=3) as pool:
        records = list(pool.map(inspect, [(p, entries[p]) for p in paths]))
    destination.write_text(json.dumps({
        'script_sha256': script_hash,
        'interpretation': 'Exploratory waveform diagnostics; no physical units or anatomical labels verified.',
        'optical_partition_summary': optical_partition_summary(records),
        'records': records,
    }, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
