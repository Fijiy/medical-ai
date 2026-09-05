# PhysioNet full-recording validation

Evidence for [Validate PhysioNet channel mapping, signal units, and recording completeness](https://github.com/Fijiy/medical-ai/issues/49), using release **1.0.0**. This extends the earlier five-recording fragment inspection; it does not choose signal-quality thresholds or fit a task classifier.

## Result

**The full recording inventory is complete. Physical channel mapping and units remain partly unresolved, so the Wayfinder ticket remains open.** All 35 released paired CSVs were downloaded, scanned in full, and matched to their published SHA-256 checksums. A checksum verifies that the downloaded bytes match the published file; it does not prove that the original experiment was complete or scientifically well calibrated.

The files themselves resolved two important questions: there are two actual row layouts, and the optical streams have a consistent numerical pairing. They also exposed an undocumented extra marker in p11. No authors were contacted.

## What was checked

| Measured item | Result |
| --- | --- |
| Released paired recording files | 35, p01–p37 excluding p14 and p23 |
| Complete recording bytes inspected | 20,308,899,390 |
| Published whole-file SHA-256 matches | 35 of 35 |
| Numeric fields inspected | 1,229,418,804 |
| Stored time samples, summed across people | 17,319,790; repeated measurement points, not independent participants |
| Malformed or empty numeric fields | 0 |
| NaN or infinite numeric fields | 0 |
| Unequal row lengths within a recording | 0 |
| Entire rows constant across the whole recording | 0 |
| Stored time grid | All start at zero and increase by 0.004 seconds, within 1e-9 numerical tolerance |
| Last stored time | 1,260.652–2,125.888 seconds after recording start |
| Eye-inclusive layout | 22 files contain 74 rows |
| Separate-eye layout | 13 files, p25–p37, contain 66 rows |

These numbers come from the saved [per-recording inventory and summary](../validation/physionet/README.md), matched to the [published manifest](https://physionet.org/files/neuro-stress-resilience-hci/1.0.0/SHA256SUMS.txt). The ZIP has 384 members and 4,979,989,467 compressed bytes. Only the paired EEG–fNIRS CSVs received this complete signal scan; wristband signals, separate eye workbooks, and task logs are not newly certified by it.

The absence of malformed values or entire constant rows is a limited structural result. It does not exclude movement artifacts, electrical noise, shorter flat sections, clipping, or unusable channels. The tolerance above handles floating-point arithmetic; it is not a signal-quality threshold. The stored 250 Hz grid does not establish native optical acquisition rate or synchronization delay.

## Actual row layouts

Rows run across time; row numbers below start at 1. The [release description](https://physionet.org/content/neuro-stress-resilience-hci/1.0.0/#description) declares 74 rows for all paired CSVs. Complete-file inspection contradicts that for p25–p37.

| Content | p01–p24, excluding p14/p23 | p25–p37 |
| --- | --- | --- |
| Time | 1 | 1 |
| Declared optical-density block | 2–17 | 2–17 |
| Declared concentration block | 18–33 | 18–33 |
| Declared EEG block | 34–65 | 34–65 |
| Eye block | 66–73 | Absent from paired CSV |
| Observed binary event pulses | 74 | **66** |

The later participant notes document separate eye acquisition. The final row of each actual 66-row file contains isolated binary task pulses. The stable optical dependencies below also support continuity of the optical blocks across both layouts. This establishes a useful observed layout, not a complete acquisition/export specification.

The importer recognizes this 66-row variant only for p25–p37, retains the published-layout discrepancy, and tests the final row's event content. It does not relabel a truncated earlier participant's row 66 as events. Literal row numbers are retained throughout; no electrode names are silently attached.

## Task markers and recording coverage

The agreed target is Working Baseline versus both Stress 1 and Stress 2. A selected period has an observed end only when the next phase marker is present. Intervals include the start sample and exclude the next marker's sample. The final marker starts Recovery 2; there is no experiment-end marker. Therefore “five starts found” must not be reported as proof that the entire planned protocol was completed.

| Coverage category | Count | Meaning |
| --- | ---: | --- |
| Available paired files | 35 | The release supplies a file |
| Complete, checksum-matched copies | 35 | Every byte of that published file was inspected |
| Assigned starts and following boundaries for all three selected periods | **33** | Marker order or an explicit note supports the selected-period boundaries |
| Unresolved assignment | **1: p11** | Six pulses, but no correction note |
| Incomplete selected-period coverage | **1: p16** | Stress 2 begins but has no following boundary; Recovery 2 has no start |
| Finally eligible participants | **Not decided** | Requires the agreed treatment of timing, incomplete periods, signal quality, and remaining metadata |

All event rows contain only 0/1 values, and observed pulses are one sample wide. The importer applies the release notes for p15 (drop marker 2) and p25/p26 (keep the last five). It makes no spacing-based correction for other participants.

**p11:** six observed pulse times are 248.848, 325.028, 688.160, 1,044.704, 1,404.708, and 1,769.068 seconds. Treating the last five as the protocol sequence is a possible explanation, but the package supplies no note authorizing it. Its phase assignments remain unknown. The inventory explicitly distinguishes unknown starts from confirmed missing starts.

**p16:** the four pulse times are 139.512, 499.408, 861.932, and 1,219.304 seconds. Under the documented protocol order, the final pulse starts Stress 2. The recording ends at 1,260.652 seconds, leaving only **41.348 seconds of observed span after that start**. No missing period is fabricated. The [participant note](https://physionet.org/files/neuro-stress-resilience-hci/1.0.0/EEGfNIRSeye_p11-p16/p16/Notes.txt) says the session stopped after 24 minutes; that differs from the file's 21.01-minute time extent.

Observed intervals also differ from the nominal six-minute schedule. Among assigned boundaries, Working Baseline spans 359.060–376.112 seconds, Stress 1 spans 347.504–374.032, Recovery 1 spans 309.856–364.152, and bounded Stress 2 spans 355.716–365.236. In particular, p02's Recovery 1 interval is 309.856 seconds. These are recorded discrepancies, not automatic exclusions or evidence of a specific cause. Pre-marker time is not automatically labeled resting baseline.

The [machine-readable summary](../validation/physionet/recording-summary.csv) preserves every participant's counts, marker times, correction rule, period spans, end status, structural findings, and undecided model eligibility. Per-row lengths and numerical checks remain in the corresponding `pXX.json` files.

## What the optical values establish

We checked whether each derived concentration row can be reconstructed from two optical input rows. The check first identifies two candidate inputs from all 16, estimates their equation on up to 4,096 evenly spread samples, and measures the residual error across **every stored sample**. Each current recording is independently checksum-verified before this check. It is a consistency test of exported numbers, not a classifier, held-out prediction result, or proof of physiology.

All 35 recordings show the same eight numerical groups:

| Empirical group | Optical-density rows | Concentration rows |
| --- | --- | --- |
| 1 | 2, 3 | 18, 19 |
| 2 | 4, 5 | 20, 21 |
| 3 | 6, 7 | 22, 23 |
| 4 | 8, 9 | 24, 25 |
| 5 | 10, 11 | 26, 27 |
| 6 | 12, 13 | 28, 29 |
| 7 | 14, 15 | 30, 31 |
| 8 | 16, 17 | 32, 33 |

Across all 560 output equations, the largest root-mean-square reconstruction error is about **2.28 × 10⁻¹²** times the fitting output's standard deviation; the largest single-sample normalized error is below **1.77 × 10⁻¹⁰**. Standard deviation measures the spread of the stored values; normalizing by it allows errors from differently scaled rows to be compared. These are very small numerical errors, consistent with direct two-input conversion relationships in the export.

For example, across participants the first group approximately satisfies:

```text
row 18 =  0.0817802215 × row 2 − 0.0383920168 × row 3
row 19 = −0.0297720054 × row 2 + 0.0566332307 × row 3
```

The saved evidence retains coefficients, offsets, design ranks, full-sample residuals, and exact stored-value update-spacing counts for each participant: [optical-consistency.json](../validation/physionet/optical-consistency.json). Update spacings vary and must not be used to claim a native optical rate. The 4,096 fitting samples are included in the all-sample check; no independence claim is made.

**What this resolves:** empirical grouping of input and derived optical rows is strongly supported across the entire release. Counting the two derived outputs as unrelated spatial measurements would ignore their shared numerical inputs.

**What the equations alone do not resolve:** the physical source and detector for each group, wavelength order, which output is HbO versus HbR, physical units, baseline definition, or conversion parameters. Comparing their coefficients with an external physical model supplies the additional conditional evidence below. These groups are not yet verified named sensor locations or a calibrated physical sensor budget.

## Follow-up: a numerical fingerprint for optical signal identities

Checked September 5, 2026. The conversion numbers provide more information than grouping alone. Inverting each two-input conversion gives the following matrix, consistently across all **280 groups (35 people × 8 groups)**:

```text
optical inputs = B × concentration outputs, apart from fitted offsets
B ≈ [[16.2344, 11.0054],
     [ 8.5344, 23.4430]]
  = 14 × [[1.1596, 0.7861],
          [0.6096, 1.6745]]
```

The four coefficients in the smaller matrix appear in a published modified Beer–Lambert conversion: the rows correspond to 850 then 760 nm light, and the columns to oxygenated then deoxygenated hemoglobin (HbO and HbR). These coefficients describe how strongly the two forms of hemoglobin absorb each wavelength. This is an external coefficient table, not this release's acquisition configuration. [Janani and Sasikala, *Classification of fNIRS Signals for Decoding Right- and Left-Arm Movement Execution Using SVM for BCI Applications*, Section 2.2](https://www.researchgate.net/publication/324157869_Classification_of_fNIRS_Signals_for_Decoding_Right-_and_Left-Arm_Movement_Execution_Using_SVM_for_BCI_Applications).

**Inference:** assuming that table and one shared positive conversion scale, the data strongly support this order:

| CSV rows, one-based | Conditional identity |
| --- | --- |
| 2, 4, 6, 8, 10, 12, 14, 16 | 850 nm optical inputs |
| 3, 5, 7, 9, 11, 13, 15, 17 | 760 nm optical inputs |
| 18, 20, 22, 24, 26, 28, 30, 32 | HbO outputs |
| 19, 21, 23, 25, 27, 29, 31, 33 | HbR outputs |

We tested all four wavelength/output order combinations with a separately fitted common scale for each group. The matching order's maximum relative matrix error was **5.31 × 10⁻¹³**, with scale from 13.9999999999988 to 14.000000000004704. Each alternative had relative error above 0.33. This error is the size of the matrix discrepancy divided by the size of the recovered matrix; it is not physiological accuracy or a probability that the labels are correct. The largest absolute discrepancy from `14 × reference` was 1.91 × 10⁻¹¹.

This is a strong numerical fingerprint, not proof of which acquisition software produced it. The search tests four orderings of one published table; it does not cover arbitrary coefficients, export scaling, or software mistakes. The factor **14** is established numerically, but cannot be split uniquely into source–detector distance, light-path factor, optical encoding, and concentration unit. For example, multiplying both the optical and concentration numerical scales by 1,000 preserves exactly the same conversion matrix while changing their interpretation. A matching matrix therefore cannot distinguish the original unit conventions. Nor does it identify the source and detector attached to each of the eight groups.

The [runnable fingerprint check](../../scripts/physionet_conversion_fingerprint.py) validates the existing evidence and compares all 280 matrices; it does not reread or download raw recordings. It saves [the four ordering comparisons and input/script checksums](../validation/physionet/conversion-fingerprint.json). Run from the repository root:

```sh
python3 scripts/physionet_conversion_fingerprint.py
```

The earlier pairing evidence remains unchanged. The new wavelength/HbO/HbR labels are explicitly **conditional**, not silently applied as verified importer metadata. Physical locations, units, reference and recording-specific timing remain open requirements of the ticket.

## Remaining metadata and safe next work

The [primary-source metadata investigation](physionet-channel-metadata-evidence.md) holds the detailed source comparison. Its numbered EEG coordinate file is a plausible mapping candidate, while the Methods list uses a different sequence. Neither the waveform shapes nor the numerical optical groups establish the actual CSV-to-electrode export order.

Still needed: release-specific EEG export order/unit/reference/filter history; physical optical pair and wavelength/HbO/HbR lookup; optical units and conversion settings; and coordinate scale/frame. Native optical rate, resampling, and device delay remain unverified. These block validated named-location comparisons and calibrated interpretations; they do not block structural checks or clearly labeled anonymous-row inspection.

The existing sensor-configuration and preprocessing/evaluation decisions can use this inventory to discuss limitations and policies. They should not declare 33 participants finally usable, silently fix p11, fill p16's missing data, or transfer these stress-task findings to depression. A [draft clarification request](../validation/physionet/metadata-request.md) is saved but has not been sent. No further author contact is authorized by this ticket.

## Reproduction and limits

[Reproduction commands, file locations, and the acceptance ledger](../validation/physionet/README.md) accompany the inventory. Eight importer tests cover parsing, layouts, integrity, cached-file changes, timing, and known marker exceptions. Optical self-checks cover known pair recovery, constant/nonfinite input, and modified-file rejection. An independent code review found and prompted fixes to whitespace parsing, stale-cache verification, unknown-versus-missing phase reporting, and optical evidence provenance.

All raw recordings stay outside Git under `data/physionet/`. Only source metadata, aggregate diagnostics, code, tests, and reports are suitable for the evidence commit. No prediction model was trained, no signal-quality exclusion threshold chosen, and no internship checkpoint marked complete.

Source attribution: Roy, S., and Nuamah, J. (2026). [Neurophysiological Dataset of Stress Resilience During Human-Computer Interaction, version 1.0.0](https://doi.org/10.13026/x3vc-p627). The release license is retained with the saved metadata.
