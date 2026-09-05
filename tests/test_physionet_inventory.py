"""Synthetic structure tests; no participant signals are included."""
import hashlib
import io
from pathlib import Path
import sys
import unittest
import tempfile
import zipfile
import json
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from physionet_inventory import (corrected_markers, event_summary, manifest_entries,
                                  parse_row, scan_stream, scan_archive, scan_remote, timing_summary)


class InventoryTests(unittest.TestCase):
    def fixture(self, length=16):
        rows = [','.join(str(i * .004) for i in range(length))]
        rows += [','.join(['2'] * length)] * 72
        rows += [','.join('1' if i in [1, 4, 7, 10, 13] else '0' for i in range(length))]
        return ('\r\n'.join(rows) + '\r\n').encode()

    def test_complete_stream_and_integrity(self):
        data = self.fixture()
        sink = io.BytesIO()
        result = scan_stream(io.BytesIO(data), 'p01', sink)
        self.assertEqual(sink.getvalue(), data)
        self.assertEqual(result['sha256'], hashlib.sha256(data).hexdigest())
        self.assertEqual(result['bytes_read'], len(data))
        self.assertEqual(result['physical_row_count'], 74)
        self.assertEqual(result['structural_failures'], [])
        self.assertTrue(result['time']['grid_004_valid'])
        self.assertEqual(result['events']['raw_marker_indices'], [1, 4, 7, 10, 13])
        self.assertEqual(result['events']['phases'][3]['boundary_status'], 'bounded_by_next_marker')
        self.assertEqual(result['events']['phases'][-1]['boundary_status'], 'no_end_marker')

    def test_malformed_nonfinite_and_uneven(self):
        for raw in [b'1,,2', b'1,2,', b'1,garbage,2', b'1,2x,3', b'1, ,2', b'1,\r,2', b'1,\v,2', b'1,\f,2']:
            with self.subTest(raw=raw):
                _, row = parse_row(raw, 2)
                self.assertGreater(row['malformed_count'], 0)
        _, row = parse_row(b'1,nan,inf,-inf', 2)
        self.assertEqual(row['nonfinite_count'], 3)
        self.assertEqual(row['malformed_count'], 0)
        rows = self.fixture().splitlines()
        rows[33] = b'1,nan,broken'
        result = scan_stream(io.BytesIO(b'\n'.join(rows)), 'p01')
        self.assertIn('unequal_row_lengths', result['structural_failures'])
        self.assertIn('malformed_numeric_fields', result['structural_failures'])
        self.assertIn(34, result['eeg_fnirs_nonfinite_rows'])
        result = scan_stream(io.BytesIO(b'\n'.join(rows[:-1])), 'p01')
        self.assertIn('unrecognized_row_layout_observed_73', result['structural_failures'])
        self.assertIn('invalid_or_unresolved_events', result['structural_failures'])

    def test_observed_compact_layout_and_truncation(self):
        rows = self.fixture().splitlines()
        compact = b'\n'.join(rows[:65] + rows[-1:])
        result = scan_stream(io.BytesIO(compact), 'p27')
        self.assertEqual(result['physical_row_count'], 66)
        self.assertEqual(result['event_row_1based'], 66)
        self.assertEqual(result['structural_failures'], [])
        self.assertEqual(len(result['events']['corrected_marker_indices']), 5)
        self.assertTrue(result['documentation_discrepancies'])
        earlier = scan_stream(io.BytesIO(compact), 'p01')
        self.assertIsNone(earlier['events'])
        truncated = scan_stream(io.BytesIO(b'\n'.join(rows[:66])), 'p27')
        self.assertIn('invalid_or_unresolved_events', truncated['structural_failures'])

    def test_note_exceptions_and_p16(self):
        self.assertEqual(corrected_markers('p15', [1,3,5,7,9,11])[0], [1,5,7,9,11])
        self.assertEqual(corrected_markers('p25', [1,3,5,7,9,11])[0], [3,5,7,9,11])
        self.assertEqual(corrected_markers('p26', [1,3,5,7,9,11,13])[0], [5,7,9,11,13])
        self.assertEqual(corrected_markers('p01', [1,3,5,7,9,11])[0], [])
        values = np.zeros(315164)
        values[[34878,124852,215483,304826]] = 1
        result = event_summary('p16', values, np.arange(len(values)) * .004)
        self.assertEqual(result['missing_phase_starts'], ['recovery_2'])
        self.assertEqual(result['phases'][3]['phase'], 'stress_2')
        self.assertEqual(result['phases'][3]['boundary_status'], 'no_end_marker')
        self.assertAlmostEqual(result['phases'][3]['observed_span_seconds'], 41.348)
        self.assertIsNone(result['phases'][3]['next_marker_index'])

    def test_bad_timing_and_events_are_not_labeled(self):
        times = np.arange(16) * .004
        values = np.zeros(16)
        values[[1,4,7,10,13]] = 1
        for bad_times in [np.zeros(16), times + 1, np.where(np.arange(16)==5, np.nan, times)]:
            self.assertFalse(timing_summary(bad_times)['grid_004_valid'])
            self.assertEqual(event_summary('p01', values, bad_times)['phases'], [])
        for bad_values in [np.append(values,0), np.where(np.arange(16)==2, 1, values), np.where(np.arange(16)==2, .5, values)]:
            self.assertEqual(event_summary('p01', bad_values, times)['phases'], [])

    def test_archive_hash_verification_and_safe_cache(self):
        data = self.fixture()
        path = 'EEGfNIRSeye_p1-p5/p01/p01.csv'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / 'release.zip'
            with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
                z.writestr('release/' + path, data)
                z.writestr('../must-not-extract', b'unrelated')
            digest = hashlib.sha256(data).hexdigest()
            scan_archive(archive, [path], {path: digest}, root, root/'data')
            self.assertEqual((root/'data'/path).read_bytes(), data)
            self.assertTrue(json.loads((root/'p01.json').read_text())['integrity_verified'])
            self.assertFalse((root.parent/'must-not-extract').exists())
            with self.assertRaises(ValueError):
                scan_archive(archive, [path], {path: '0'*64}, root)

    def test_modified_cache_is_not_certified_and_unknown_is_not_missing(self):
        data = self.fixture()
        path = 'EEGfNIRSeye_p1-p5/p01/p01.csv'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cached = root/'data'/path
            cached.parent.mkdir(parents=True)
            cached.write_bytes(data)
            digest = hashlib.sha256(data).hexdigest()
            scan_remote(path, digest, root, root/'data')
            cached.write_bytes(b'corrupted')
            with patch('physionet_inventory.time.sleep'), self.assertRaises(ValueError):
                scan_remote(path, digest, root, root/'data')
        times = np.arange(16) * .004
        values = np.zeros(16)
        values[[1,3,5,7,9,11]] = 1
        events = event_summary('p11', values, times)
        self.assertIsNone(events['missing_phase_starts'])
        self.assertEqual(events['phase_assignment_status'], 'unresolved')

    def test_manifest_rejects_unsafe_paths(self):
        for path in ['../../data.csv', '/data.csv']:
            with self.assertRaises(ValueError):
                manifest_entries(('a'*64 + '  ' + path).encode())


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(InventoryTests)
    outcome = unittest.TextTestRunner().run(suite)
    if not outcome.wasSuccessful():
        raise SystemExit(1)
    print('IMPORTER CHECKS PASSED')
