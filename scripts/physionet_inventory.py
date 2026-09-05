"""Stream the pinned PhysioNet release into a structural inventory, with an optional local recording cache.

Requires Python 3.9+ and NumPy. CSV rows are measurement streams; columns are time.
This inventories stored rows; it does not assign electrode names or physical units.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import warnings
import zipfile

import numpy as np

BASE = 'https://physionet.org/files/neuro-stress-resilience-hci/1.0.0/'
PHASES = ['working_baseline', 'stress_1', 'recovery_1', 'stress_2', 'recovery_2']
SCHEMA_VERSION = 2


def manifest_entries(data):
    entries = {}
    for line in data.decode('utf-8').splitlines():
        digest, path = line.split(None, 1)
        path = path.removeprefix('*')
        if not re.fullmatch('[a-f0-9]{64}', digest) or path.startswith('/') or '..' in Path(path).parts:
            raise ValueError('Unsafe or malformed manifest entry')
        if path in entries:
            raise ValueError('Duplicate manifest path')
        entries[path] = digest
    return entries


def recording_paths(entries):
    return sorted(p for p in entries if re.fullmatch(r'EEGfNIRSeye_[^/]+/(p\d{2})/\1\.csv', p))


def parse_row(raw, row_number):
    """Strictly account for every comma-separated field, including empty final fields."""
    payload = raw.rstrip(b'\r\n')
    count = payload.count(b',') + 1
    malformed = []
    try:
        if any(c in payload for c in (b' ', b'\t', b'\r', b'\n', b'\v', b'\f')) and re.search(rb'(?:^|,)\s*(?:,|$)', payload):
            raise ValueError('Empty numeric field')
        with warnings.catch_warnings():
            warnings.simplefilter('error')
            values = np.fromstring(payload.decode('ascii'), sep=',', dtype=np.float64)
        if len(values) != count:
            raise ValueError('Incomplete numeric parse')
    except (ValueError, UnicodeDecodeError, Warning):
        parsed = []
        for index, token in enumerate(payload.split(b',')):
            try:
                parsed.append(float(token))
            except ValueError:
                parsed.append(float('nan'))
                malformed.append(index)
        values = np.asarray(parsed, dtype=np.float64)
    finite = np.isfinite(values)
    nonfinite = np.flatnonzero(~finite)
    valid = values[finite]
    stats = {
        'row_1based': row_number, 'field_count': count,
        'malformed_count': len(malformed), 'malformed_indices_first20': malformed[:20],
        'nonfinite_count': int(nonfinite.size), 'nonfinite_indices_first20': nonfinite[:20].tolist(),
        'zero_count': int(np.count_nonzero(values == 0)),
        'minimum_stored_value': float(valid.min()) if valid.size else None,
        'maximum_stored_value': float(valid.max()) if valid.size else None,
        'constant_finite_row': bool(valid.size == count and valid.min() == valid.max()),
    }
    return values, stats


def corrected_markers(participant, indices):
    """Corrections are explicit note rules, never inferred from marker spacing."""
    expected_count = {'p15': 6, 'p25': 6, 'p26': 7, 'p16': 4}.get(participant, 5)
    if len(indices) != expected_count:
        return [], 'unresolved_marker_count'
    if participant == 'p15':
        return [indices[i] for i in [0, 2, 3, 4, 5]], 'p15_note_drop_second_marker'
    if participant in ('p25', 'p26'):
        return indices[-5:], 'participant_note_keep_last_five'
    if participant == 'p16':
        return list(indices), 'p16_four_starts_incomplete_recording'
    return list(indices), 'five_markers_in_protocol_order'


def timing_summary(times):
    finite = np.isfinite(times)
    deltas = np.diff(times)
    grid_errors = np.flatnonzero(~np.isfinite(deltas) | (np.abs(deltas - 0.004) > 1e-9))
    valid = bool(len(times) > 1 and finite.all() and times[0] == 0 and not grid_errors.size)
    return {
        'sample_count': len(times),
        'first_stored_time': float(times[0]) if len(times) and finite[0] else None,
        'last_stored_time': float(times[-1]) if len(times) and finite[-1] else None,
        'strictly_increasing': bool(len(times) > 1 and finite.all() and (deltas > 0).all()),
        'grid_004_valid': valid,
        'bad_step_count': int(grid_errors.size), 'bad_step_indices_first20': grid_errors[:20].tolist(),
        'stored_rate_hz_if_seconds': 250 if valid else None,
    }


def event_summary(participant, values, times):
    nonbinary = np.flatnonzero(~np.isfinite(values) | ((values != 0) & (values != 1)))
    indices = np.flatnonzero(values == 1).tolist()
    adjacent = any(b == a + 1 for a, b in zip(indices, indices[1:]))
    corrected, rule = corrected_markers(participant, indices)
    valid = not nonbinary.size and not adjacent and len(values) == len(times)
    valid = valid and timing_summary(times)['grid_004_valid']
    if not valid:
        corrected, rule = [], 'invalid_event_row'
    def timestamp(index):
        return float(times[index]) if index < len(times) and np.isfinite(times[index]) else None
    phases = []
    for phase_index, start in enumerate(corrected):
        end = corrected[phase_index + 1] if phase_index + 1 < len(corrected) else None
        phases.append({
            'phase': PHASES[phase_index], 'start_index': start, 'start_seconds': timestamp(start),
            'next_marker_index': end, 'next_marker_seconds': timestamp(end) if end is not None else None,
            'boundary_status': 'bounded_by_next_marker' if end is not None else 'no_end_marker',
            'observed_span_seconds': timestamp(end) - timestamp(start) if end is not None else timestamp(len(times)-1) - timestamp(start),
        })
    return {
        'nonbinary_count': int(nonbinary.size), 'nonbinary_indices_first20': nonbinary[:20].tolist(),
        'adjacent_one_samples': adjacent, 'raw_marker_indices': indices,
        'raw_marker_seconds': [timestamp(i) for i in indices],
        'corrected_marker_indices': corrected, 'correction_rule': rule, 'phases': phases,
        'phase_assignment_status': 'assigned_in_protocol_order' if corrected else 'unresolved',
        'missing_phase_starts': PHASES[len(corrected):] if corrected else None,
        'unassigned_phase_names': [] if corrected else PHASES,
    }


def scan_stream(stream, participant, sink=None):
    """Hash every original byte while keeping only a row plus time/event arrays in memory."""
    digest = hashlib.sha256()
    byte_count = 0
    rows = []
    times = None
    event_values = None
    pending = b''
    ended_with_newline = False
    def consume(raw):
        nonlocal times, event_values
        values, stats = parse_row(raw, len(rows) + 1)
        rows.append(stats)
        if len(rows) == 1:
            times = values
        event_values = values
    while True:
        chunk = stream.read(1024 * 1024)
        if not chunk:
            break
        if sink is not None:
            sink.write(chunk)
        byte_count += len(chunk)
        digest.update(chunk)
        ended_with_newline = chunk.endswith(b'\n')
        pieces = (pending + chunk).split(b'\n')
        pending = pieces.pop()
        for raw in pieces:
            consume(raw)
    if pending:
        consume(pending)
    errors = []
    observed_compact_layout = bool(re.fullmatch(r'p(?:2[5-9]|3[0-7])', participant) and len(rows) == 66)
    recognized_layout = len(rows) == 74 or observed_compact_layout
    if not recognized_layout:
        errors.append(f'unrecognized_row_layout_observed_{len(rows)}')
    n = len(times) if times is not None else 0
    unequal = [r['row_1based'] for r in rows if r['field_count'] != n]
    if unequal:
        errors.append('unequal_row_lengths')
    if any(r['malformed_count'] for r in rows):
        errors.append('malformed_numeric_fields')
    signal_bad = [r['row_1based'] for r in rows[1:65] if r['nonfinite_count']]
    time_info = timing_summary(times) if times is not None else None
    if time_info is None or not time_info['grid_004_valid']:
        errors.append('invalid_time_grid')
    event_info = event_summary(participant, event_values, times) if recognized_layout and event_values is not None and times is not None else None
    if event_info is None or event_info['correction_rule'] in ('invalid_event_row', 'unresolved_marker_count'):
        errors.append('invalid_or_unresolved_events')
    return {
        'schema_version': SCHEMA_VERSION, 'participant': participant, 'bytes_read': byte_count,
        'sha256': digest.hexdigest(), 'physical_row_count': len(rows),
        'declared_row_count': 74,
        'observed_layout': '66_rows_separate_eye_recording' if observed_compact_layout else ('74_rows' if recognized_layout else 'unrecognized'),
        'documentation_discrepancies': ['release_declares_74_rows_but_file_has_66'] if observed_compact_layout else [],
        'event_row_1based': len(rows) if recognized_layout else None,
        'final_newline': ended_with_newline, 'rows': rows, 'unequal_length_rows': unequal,
        'eeg_fnirs_nonfinite_rows': signal_bad, 'structural_failures': errors,
        'time': time_info, 'events': event_info,
        'model_eligibility': 'not_decided_requires_metadata_and_quality_policy',
    }


def request(url):
    for attempt in range(3):
        try:
            return urlopen(Request(url, headers={'User-Agent': 'medical-ai-structural-inventory/1.0', 'Accept-Encoding': 'identity'}), timeout=120)
        except (HTTPError, URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(2)


def write_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def scan_remote(path, expected_hash, output, cache_dir=None):
    participant = Path(path).stem
    target = output / f'{participant}.json'
    cached = cache_dir / path if cache_dir else None
    scanner_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if target.exists() and cached is None:
        previous = json.loads(target.read_text())
        if previous.get('schema_version') == SCHEMA_VERSION and previous.get('sha256') == expected_hash and previous.get('integrity_verified') and previous.get('source_url') == BASE + path and previous.get('scanner_sha256') == scanner_hash and (cached is None or cached.exists()):
            print(f'{participant}: retained verified inventory', flush=True)
            return previous
    for attempt in range(3):
        try:
            print(f'{participant}: scan attempt {attempt + 1}', flush=True)
            if cached is not None and cached.exists():
                with cached.open('rb') as source:
                    result = scan_stream(source, participant)
                headers = {'Content-Length': str(cached.stat().st_size)}
                transport = 'local_cache_reverified'
            else:
                with request(BASE + path) as response:
                    if response.status != 200:
                        raise ValueError(f'Expected whole-file HTTP 200, received {response.status}')
                    headers = {k: response.headers.get(k) for k in ('Content-Length', 'Last-Modified', 'ETag', 'Content-Type')}
                    if cached is None:
                        result = scan_stream(response, participant)
                    else:
                        cached.parent.mkdir(parents=True, exist_ok=True)
                        with cached.with_suffix('.partial').open('wb') as sink:
                            result = scan_stream(response, participant, sink)
                transport = 'http_200_full_file'
            result.update(source_url=BASE + path, expected_sha256=expected_hash, http_headers=headers,
                          scanner_sha256=scanner_hash, transport=transport,
                          inspected_at_utc=datetime.now(timezone.utc).isoformat())
            result['integrity_verified'] = result['sha256'] == expected_hash
            if not result['integrity_verified']:
                raise ValueError('Full-file SHA-256 mismatch')
            if headers['Content-Length'] is not None and result['bytes_read'] != int(headers['Content-Length']):
                raise ValueError('HTTP byte-length mismatch')
            if cached is not None and not cached.exists():
                cached.with_suffix('.partial').replace(cached)
            write_json(target, result)
            print(f"{participant}: verified {result['bytes_read']} bytes, {result['physical_row_count']} rows; failures={result['structural_failures']}", flush=True)
            return result
        except Exception as error:
            print(f'{participant}: attempt {attempt + 1} failed: {type(error).__name__}: {error}', flush=True)
            if attempt == 2:
                raise
            time.sleep(2)



def scan_archive(archive_path, paths, entries, output, cache_dir=None):
    """Read only manifest-named recordings; never extract arbitrary archive paths."""
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        for path in paths:
            matches = [name for name in names if name == path or name.endswith('/' + path)]
            if len(matches) != 1:
                raise ValueError(f'Expected one archive member for {path}, found {len(matches)}')
            participant = Path(path).stem
            cached = cache_dir / path if cache_dir else None
            print(f'{participant}: inspect archive member', flush=True)
            with archive.open(matches[0]) as source:
                if cached is None:
                    result = scan_stream(source, participant)
                else:
                    cached.parent.mkdir(parents=True, exist_ok=True)
                    with cached.with_suffix('.partial').open('wb') as sink:
                        result = scan_stream(source, participant, sink)
            if result['sha256'] != entries[path]:
                raise ValueError(f'Archive member SHA-256 mismatch: {path}')
            result.update(source_url=BASE + path, expected_sha256=entries[path], integrity_verified=True,
                          transport='official_zip_member_crc_and_sha256_verified', archive_member=matches[0],
                          archive_source_url='https://physionet.org/content/neuro-stress-resilience-hci/get-zip/1.0.0/',
                          scanner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                          inspected_at_utc=datetime.now(timezone.utc).isoformat())
            if cached is not None:
                cached.with_suffix('.partial').replace(cached)
            write_json(output / f'{participant}.json', result)
            print(f"{participant}: verified {result['bytes_read']} bytes, {result['physical_row_count']} rows; failures={result['structural_failures']}", flush=True)


def verify_inventory(output):
    entries = manifest_entries((output / 'source-metadata/SHA256SUMS.txt').read_bytes())
    paths = recording_paths(entries)
    results = []
    for path in paths:
        result = json.loads((output / (Path(path).stem + '.json')).read_text())
        assert result['schema_version'] == SCHEMA_VERSION
        assert result['source_url'] == BASE + path
        assert result['expected_sha256'] == result['sha256'] == entries[path]
        assert result['integrity_verified']
        assert result['physical_row_count'] == len(result['rows'])
        assert result['bytes_read'] > 0
        assert result['time'] is not None or 'invalid_time_grid' in result['structural_failures']
        assert result['events'] is not None or 'invalid_or_unresolved_events' in result['structural_failures']
        for i, row in enumerate(result['rows'], 1):
            assert row['row_1based'] == i and row['field_count'] > 0
            assert 0 <= row['malformed_count'] <= row['nonfinite_count'] <= row['field_count']
        results.append(result)
    assert paths, 'No recordings discovered'
    observed = {p.stem for p in output.glob('p[0-9][0-9].json')}
    assert observed == {Path(p).stem for p in paths}, 'Inventory does not match release'
    for path, digest in entries.items():
        local = output / 'source-metadata' / path
        if local.exists():
            assert hashlib.sha256(local.read_bytes()).hexdigest() == digest, path
    print(f"INVENTORY VERIFIED: {len(results)} complete file scans, {sum(r['bytes_read'] for r in results)} bytes")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('docs/validation/physionet'))
    parser.add_argument('--archive', type=Path, help='Inspect a downloaded official ZIP instead of individual HTTP recordings')
    parser.add_argument('--cache-dir', type=Path, help='Keep verified whole recordings here; keep this directory out of Git')
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--participant', action='append', help='Optional IDs for a bounded scan; default is all')
    parser.add_argument('--verify-inventory', type=Path)
    args = parser.parse_args()
    if args.verify_inventory:
        verify_inventory(args.verify_inventory)
        return
    args.output.mkdir(parents=True, exist_ok=True)
    metadata = args.output / 'source-metadata'
    metadata.mkdir(exist_ok=True)
    manifest_path = metadata / 'SHA256SUMS.txt'
    if args.archive:
        manifest = manifest_path.read_bytes()
    else:
        with request(BASE + 'SHA256SUMS.txt') as response:
            manifest = response.read()
    if manifest_path.exists() and manifest_path.read_bytes() != manifest:
        raise ValueError('Pinned release manifest changed; inspect before mixing evidence')
    manifest_path.write_bytes(manifest)
    entries = manifest_entries(manifest)
    for path, digest in entries.items():
        if path in ('README.txt', 'LICENSE.txt', 'EEG_32_Channel_mapping.xyz', 'fNIRS_frontal.xyz') or re.fullmatch(r'EEGfNIRSeye_[^/]+/p\d{2}/Notes?\.txt', path):
            local = metadata / path
            if not local.exists():
                if args.archive:
                    raise ValueError(f'Fetch required source metadata before an offline archive scan: {path}')
                with request(BASE + path) as response:
                    data = response.read()
                if hashlib.sha256(data).hexdigest() != digest:
                    raise ValueError(f'Metadata hash mismatch: {path}')
                local.parent.mkdir(parents=True, exist_ok=True)
                local.write_bytes(data)
            elif hashlib.sha256(local.read_bytes()).hexdigest() != digest:
                raise ValueError(f'Cached metadata hash mismatch: {path}')
    paths = recording_paths(entries)
    if args.participant:
        requested = set(args.participant)
        if not requested <= {Path(p).stem for p in paths}:
            raise ValueError('Unknown participant ID')
        paths = [p for p in paths if Path(p).stem in requested]
    if args.workers < 1:
        parser.error('--workers must be positive')
    if args.archive:
        scan_archive(args.archive, paths, entries, args.output, args.cache_dir)
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(scan_remote, p, entries[p], args.output, args.cache_dir) for p in paths]
            for future in as_completed(futures):
                future.result()
    if not args.participant:
        verify_inventory(args.output)


if __name__ == '__main__':
    main()
