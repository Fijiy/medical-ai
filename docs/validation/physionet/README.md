# PhysioNet recording validation evidence

Work for [Validate PhysioNet channel mapping, signal units, and recording completeness](https://github.com/Fijiy/medical-ai/issues/49), under the existing EEG–fNIRS Wayfinder map.

**Status: full recording inventory complete; physical mapping and units remain unresolved.** All 35 paired CSVs match their published checksums. 33 have assigned boundaries for every selected task period; p11 is unresolved and p16 is incomplete. Final eligibility is not decided. See the [validation report](../../research/physionet-recording-validation.md).

## Files

- `source-metadata/`: release manifest, README, license, coordinate files, and participant notes, checked against the published SHA-256 manifest. A checksum is a fingerprint used to check that a downloaded file matches the published file.
- `provenance.json`: source version, environment, declared row groups, unknown fields, and indexing conventions.
- `recording-summary.csv`: one row per participant, including phase coverage and unresolved eligibility.
- `optical-consistency.json`: measured numerical row pairings and full-sample residuals, without physical label assignments.
- `conversion-fingerprint.json`: comparison of all 280 recovered conversion matrices with published coefficients; wavelength/HbO/HbR identities remain conditional and units unassigned.
- `waveform-diagnostics.json`: hash-backed waveform summaries, candidate EEG geometry scores, optical grouping and update checks. See [data-level inference and limits](../../research/physionet-waveform-metadata-inference.md).
- `pXX.json`: created only after the corresponding complete recording passes its published SHA-256 check. These inventories contain structural summaries, not signal samples.
- `GATES.md`: current acceptance-check status; all gates must be assessed before a completion report.
- [Channel metadata investigation](../../research/physionet-channel-metadata-evidence.md): source evidence and unresolved mapping, units, and processing history.
- [Manufacturer follow-up](../../research/physionet-manufacturer-output-followup.md): completed search for software output conventions and the precise configuration still needed.

Downloaded participant recordings remain in the Git-ignored `data/physionet/` directory. The archive is `data/physionet/release-1.0.0.zip`; verified recordings are retained under `data/physionet/neuro-stress-resilience-hci/1.0.0/`. Files ending `.partial` are unfinished transfers and must not be used as complete recordings.

## Reproduce

Run from the repository root with Python 3.9+ and NumPy:

```sh
python3 -m pip install -r docs/validation/physionet/requirements.txt
python3 tests/test_physionet_inventory.py
python3 scripts/physionet_inventory.py --archive data/physionet/release-1.0.0.zip --cache-dir data/physionet/neuro-stress-resilience-hci/1.0.0
python3 scripts/physionet_inventory.py --verify-inventory docs/validation/physionet
python3 scripts/physionet_optical_checks.py
python3 scripts/physionet_optical_checks.py --verify-existing
python3 scripts/physionet_conversion_fingerprint.py
python3 scripts/physionet_waveform_diagnostics.py
python3 scripts/physionet_waveform_diagnostics.py --verify-existing
```

The archive command requires the saved manifest and required small metadata files. To fetch them and scan individual CSVs instead:

```sh
python3 scripts/physionet_inventory.py --cache-dir data/physionet/neuro-stress-resilience-hci/1.0.0 --workers 3
```

`--participant p16` limits that command to one participant. Without `--cache-dir`, raw recording samples are scanned without retaining files. An archive scan reads only manifest-named recording members, verifies their ZIP checksums and published SHA-256 hashes, and never extracts arbitrary archive paths.

## Interpretation limits

Row numbers start at 1; sample indices start at 0. Every row records its field count, malformed and nonfinite counts, first problematic sample indices, exact zero count, minimum/maximum stored values, and whether the entire row is constant. Nonfinite means a value such as NaN or infinity that cannot represent an ordinary finite measurement. Malformed fields are included in nonfinite totals; do not add those counts together.

The time check compares stored increments with 0.004 seconds using a numerical tolerance of 1e-9. That tolerance handles floating-point arithmetic; it is not a biological quality threshold. A 250 Hz stored grid does not establish native optical sampling rate or device delay.

The observed 66-row layout is recognized only for p25–p37; its final row 66 supplies events and the discrepancy with the declared 74-row layout remains recorded. Other unexpected row counts remain structural failures.

The event check applies only the documented p15/p25/p26 exceptions. Unexpected marker counts remain unresolved; p11 has six pulses without a correction note. Unknown phase starts are stored as null, separately from known missing starts. The four observed p16 starts are recorded in protocol order; Stress 2 has no following boundary and Recovery 2 has no start. No missing samples or boundaries are fabricated. The last marked phase has no experiment-end marker, even for other participants.

A phase bounded by two markers uses a start-inclusive, end-exclusive sample interval. The unbounded final phase reports extent to the final recorded sample only. The inventory does not certify nominal six-minute duration, signal quality, or eligibility for the chosen target. No amplitude exclusion threshold, prediction model, or channel-name assignment is introduced.

Source: Roy and Nuamah (2026), [Neurophysiological Dataset of Stress Resilience During Human-Computer Interaction, version 1.0.0](https://doi.org/10.13026/x3vc-p627). Preserve the release license and attribution with reused data.
