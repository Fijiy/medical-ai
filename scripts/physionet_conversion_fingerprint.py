"""Compare saved optical equations with published coefficients, without assigning units.

Run from the repository root. This checks existing evidence, not current raw CSVs.
Coefficient source and inference limits: docs/research/physionet-recording-validation.md.
"""
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np

from physionet_optical_checks import verify_evidence


def compare(matrix, candidate):
    scale = float(np.sum(matrix * candidate) / np.sum(candidate ** 2))
    error = float(np.linalg.norm(matrix - scale * candidate) / np.linalg.norm(matrix))
    return scale, error


def main():
    directory = Path('docs/validation/physionet')
    verify_evidence(directory)
    source = directory / 'optical-consistency.json'
    source_bytes = source.read_bytes()
    evidence = json.loads(source_bytes)
    # Rows: 850, 760 nm. Columns: HbO, HbR. These are comparison hypotheses.
    reference = np.array([[1.1596, .7861], [.6096, 1.6745]])
    assert np.allclose(compare(14 * reference, reference), (14, 0))
    assert compare(14 * reference, reference[:, ::-1])[1] > .6
    matrices = []
    for record in evidence['results']:
        for offset in range(0, 16, 2):
            equations = record['equations'][offset:offset + 2]
            assert all(e['candidate_input_rows_1based'] == [offset + 2, offset + 3]
                       for e in equations)
            matrices.append(np.linalg.inv([e['raw_coefficients'] for e in equations]))
    results = []
    for rows, columns in itertools.product([(0, 1), (1, 0)], repeat=2):
        candidate = reference[np.ix_(rows, columns)]
        comparisons = np.array([compare(matrix, candidate) for matrix in matrices])
        results.append({
            'candidate_wavelength_order_nm': [850 if i == 0 else 760 for i in rows],
            'candidate_output_order': ['HbO' if i == 0 else 'HbR' for i in columns],
            'fitted_scale_range': [float(comparisons[:, 0].min()), float(comparisons[:, 0].max())],
            'relative_matrix_error_range': [float(comparisons[:, 1].min()), float(comparisons[:, 1].max())],
        })
    assert len(matrices) == 280
    assert results[0]['relative_matrix_error_range'][1] < 1e-9
    assert all(r['relative_matrix_error_range'][0] > .3 for r in results[1:])
    output = {
        'status': 'conditional_coefficient_match_not_verified_physical_metadata',
        'source_evidence_sha256': hashlib.sha256(source_bytes).hexdigest(),
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'participant_count': len(evidence['results']), 'matrix_count': len(matrices),
        'reference_matrix': reference.tolist(), 'comparisons': results,
        'limitations': 'Four orderings of one published coefficient table with a common scale; not an exhaustive identification. No physical pair locations, signal units, path length, baseline, or acquisition history are assigned.',
    }
    (directory / 'conversion-fingerprint.json').write_text(json.dumps(output, indent=2) + '\n')
    print('CONVERSION FINGERPRINT VERIFIED: 280 matrices; labels remain conditional')


if __name__ == '__main__':
    main()
