# PhysioNet channel metadata: evidence and remaining blockers

Checked September 4, 2026 (America/Los_Angeles; September 5 UTC), for [Validate PhysioNet channel mapping, signal units, and recording completeness](https://github.com/Fijiy/medical-ai/issues/49), against release **1.0.0**.

## Follow-up from complete recording inspection

The [full recording validation report](physionet-recording-validation.md) adds evidence obtained after this source investigation: p25–p37 have 66 rather than 74 rows, and all 35 files support consistent empirical optical row pairings. Physical locations, wavelength/HbO/HbR labels and units remain unresolved. Read that report for the current file findings; this document records the source-document investigation.

## Finding

**Keep the channel-metadata validation blocked.** The public sources inspected do not establish the complete connection from CSV rows to named measurement locations, signal units, or the recording-specific conversion and resampling settings. File integrity and completeness can still be checked. Neither a successful parser nor a matching file hash resolves these scientific metadata gaps.

This is a bounded source investigation, separate from the full recording inventory. It extends [the earlier label-verification report](https://github.com/Fijiy/medical-ai/issues/41). No large recordings were downloaded, no mapping was invented, no authors were contacted, and no prediction target or exclusion threshold was selected.

EEG measures electrical activity at the scalp. fNIRS uses light to measure changes related to blood oxygenation. An optical measurement channel combines a light source and a detector. HbO and HbR mean oxygenated and deoxygenated hemoglobin, respectively. They are two forms of the oxygen-carrying protein in blood.

## What is actually numbered

The release describes these **one-based CSV row ranges**, with time running across columns: [release Data Description](https://physionet.org/content/neuro-stress-resilience-hci/1.0.0/#description).

| Rows | Declared contents |
| --- | --- |
| 1 | Time |
| 2–17 | Optical density |
| 18–33 | Derived concentration |
| 34–65 | EEG |
| 66–73 | Eye measurements |
| 74 | Events |

The numbered EEG metadata agree with one another; the Methods list has a different sequence. AFz is identified as ground. Ground is not evidence of the reference electrode, which supplies the comparison voltage for EEG. [Release Methods and channel sections](https://physionet.org/content/neuro-stress-resilience-hci/1.0.0/).

| EEG position | Numbered `.xyz` label | Label at that position in Methods list |
| --- | --- | --- |
| 4 | F8 | F3 |
| 5 | F3 | FZ |
| 6 | FZ | F4 |
| 7 | F4 | F8 |
| 20 | CP4 | CP1 |
| 21 | CP1 | CP2 |
| 22 | CP2 | CP4 |

Comparison source: [EEG coordinate file](https://physionet.org/files/neuro-stress-resilience-hci/1.0.0/EEG_32_Channel_mapping.xyz) and [release Methods](https://physionet.org/content/neuro-stress-resilience-hci/1.0.0/#methods). Capitalization is preserved.

The numbered file is the stronger **candidate** because its numbers are explicit. However, the Methods prose may simply list the montage without intending an acquisition order. Thus this discrepancy does not prove which list was exported. The missing evidence is the acquisition/export channel selection connecting EEG number 1 to CSV row 34, number 2 to row 35, and so on, including confirmation that it stayed consistent across participants. Do not silently apply either sequence as a validated CSV lookup. The other 25 positions agreeing does not independently verify their acquisition wiring.

For optical sensors, the release names T1–T8 at Fp2, AFF6, AF8, AF4, Fp1, AFF5, AF3, AF7, and R1/R2 at AF6/AF5; it declares 760/850 nm light and eight measurement channels. [Release optical section](https://physionet.org/content/neuro-stress-resilience-hci/1.0.0/).

The [optical coordinate file](https://physionet.org/files/neuro-stress-resilience-hci/1.0.0/fNIRS_frontal.xyz) instead orders its ten entries as `R2, R1, T6, T2, T5, T1, T8, T4, T7, T3`. These are component positions, not ten measurement channels. It has no columns for a source–detector pair, wavelength, HbO/HbR identity, or CSV row. Sorting its entries, grouping by hemisphere, or assuming alternating wavelength rows would introduce unsupported metadata.

Neither coordinate file declares its length unit or coordinate frame. Their numerical scales differ: the EEG file reaches approximately −103 on one axis; optical coordinates have magnitudes below 1. This is observable in the files, not evidence that one is millimeters and the other is a normalized head model. A shared physical coordinate system cannot be assumed. [EEG coordinates](https://physionet.org/files/neuro-stress-resilience-hci/1.0.0/EEG_32_Channel_mapping.xyz), [optical coordinates](https://physionet.org/files/neuro-stress-resilience-hci/1.0.0/fNIRS_frontal.xyz).

## Sampling evidence: product capability is not session provenance

The release README reports 250 Hz for paired recordings. Hz means samples per second. The earlier five-recording inspection found a 0.004-second stored time step, consistent with that rate. This report does not extend that numerical check to the other participants. [README](https://physionet.org/files/neuro-stress-resilience-hci/1.0.0/README.txt), [earlier inspection](https://github.com/Fijiy/medical-ai/issues/41).

Two manufacturer sources distinguish the modalities:

- The current g.tec specification gives EEG at 250/500 Hz for its 8/16/32-channel configurations and fNIRS at 10 Hz. [Official product specifications](https://www.gtec.at/product/gnautilus-wireless-eeg-fnirs/).
- The manufacturer's 2018 catalog also specifies 10 Hz for eight-channel fNIRS. Its software section describes configurable sampling and filtering in Simulink. [Official catalog, printed pages 32 and 59–60](https://www.gtec.at/wp-content/uploads/2019/10/gtec-Product-Catalog-2018-web.pdf).

A separate experiment provides a concrete example: *A Bimodal Deep Learning Architecture for EEG-fNIRS Decoding of Overt and Imagined Speech*, Methods II.C, explicitly reports optical acquisition at 10 Hz followed by upsampling to 250 Hz. Upsampling puts measurements onto a denser time grid; it does not create new independent optical observations. That study also specifies online conversion by the modified Beer–Lambert law, micromolar concentration, a path-length factor of 6, and 30 mm source–detector spacing. These are **that experiment's settings**, not this release's metadata. [Authors' university-hosted paper, printed pages 1985–1986](https://pure.ulster.ac.uk/ws/portalfiles/portal/101693172/A_Bimodal_Deep_Learning_Architecture_for_EEG_fNIRS_Decoding_of_Overt_and_Imagined_Speech.pdf).

**Inference:** a slower optical stream placed on an EEG time grid is a plausible explanation here. It remains a hypothesis. Do not set the dataset's native optical rate to 10 Hz from a product page, infer repeated-sample handling from amplitude patterns, or claim 250 independent optical measurements per second. The exact hardware/software versions, native update timestamps, interpolation or sample-hold rule, filtering, and inter-device delay remain unverified.

## Exact information needed before analysis

The following are open requirements, not assumed values. The inspected release and README do not supply the needed acquisition configuration. The release says acquisition scripts are available on request. [Usage Notes](https://physionet.org/content/neuro-stress-resilience-hci/1.0.0/#usage-notes), [README](https://physionet.org/files/neuro-stress-resilience-hci/1.0.0/README.txt).

| Missing information | Work it blocks | Minimum useful evidence |
| --- | --- | --- |
| EEG CSV row → acquisition channel → electrode | Named-location comparisons, scalp maps, brain-region interpretation | Actual channel-selection/export configuration and montage, with participant exceptions |
| Optical CSV row → source/detector and wavelength or HbO/HbR | Location budgets, HbO-only/HbR-only selection, matching two wavelengths for conversion | Row table identifying every optical stream and pair |
| EEG numerical unit and scale | Voltage thresholds, calibrated amplitude/power, imports that require volts | Export unit and scale declaration; distinguish V from µV |
| EEG reference and processing history | Reproducing preprocessing or interpreting reference-dependent measurements | Reference position/scheme, amplifier and software filters, later rereferencing and artifact treatment |
| Meaning and scaling of optical-density numbers | Reapplying intensity-to-density conversion or assuming a standard density definition | Whether streams are intensity, attenuation, or change in optical density; logarithm convention, baseline, scaling, and invalid-value codes |
| Concentration definition, unit, and conversion parameters | Calibrated HbO/HbR amplitudes and reproducible conversion | Concentration versus concentration change; unit; extinction coefficients, path-length factors, distances, baseline and software version |
| Native optical timing and resampling | Claims about optical temporal resolution and EEG–fNIRS delays | Native rates/timestamps, time-grid conversion method, synchronization and delay details |
| Coordinate scale, axes, and registration | Physical distances, combined sensor overlays, spatial localization | Units and head-coordinate frame for each file; transform if needed |

A path-length factor accounts for light scattering through tissue; an extinction coefficient describes how strongly a substance absorbs light. Their settings affect the converted concentration. These terms identify what must be documented, not a proposed conversion recipe.

Calling a row “optical density” does not establish its software encoding. Likewise, a plausible voltage range cannot distinguish all possible scaling and preprocessing choices. No units were inferred from amplitudes in this investigation.

## Publication and code search boundary

| Source checked | What it contributes and does not resolve |
| --- | --- |
| [Roy and Nuamah, 2025](https://journals.sagepub.com/doi/10.1177/10711813251364795), full publisher text | Same authors, closely matching protocol and equipment. Methods states that physiological recordings were collected but are not reported; the analysis uses task performance and questionnaire data. It supplies no EEG/optical row lookup or calibration settings. Similarity does not prove a participant-by-participant file match. |
| [Nuamah, 2024](https://pubmed.ncbi.nlm.nih.gov/38447701/), release reference 5 | Accessible indexed abstract concerns task performance, heart-rate variability and pupil response. Publisher full-text fetch failed. No conclusion about uninspected full-text metadata is claimed. |
| [Uba and Nuamah, 2023](https://journals.sagepub.com/doi/10.1177/21695067231192596), release reference 6 | Publisher abstract concerns heart rate and pupil response in 32 subjects. Full text is restricted at that endpoint. The accessible evidence does not connect this release's EEG/optical CSV rows. |
| [Release manifest](https://physionet.org/files/neuro-stress-resilience-hci/1.0.0/SHA256SUMS.txt) | All 383 paths checked: 316 CSV, 52 TXT, 13 XLSX, two XYZ. No `.m`, `.slx`, `.mdl`, Python file, or code archive is listed. Metadata TXT files inspected earlier contain no acquisition/export configuration. |

Targeted web searches used the release title/slug with “code” or “github,” the two authors with EEG/resilience, and the manufacturer with fNIRS sampling. No dataset-specific public acquisition/export repository was identified. This is a bounded negative search result, not proof that no repository exists anywhere. Other experiments' device settings cannot repair absent session provenance.

## Blocker recommendation and safe narrower work

Keep **Validate PhysioNet channel mapping, signal units, and recording completeness** open as **metadata unresolved** after saving the independent structural inventory. A complete file is not automatically a usable participant, and a complete inventory is not successful validation of sensor locations or units.

Work that can proceed without these mappings:

1. Verify hashes, row/sample counts, numerical parsing, finite values, time continuity, event pulses, documented marker corrections, and recording coverage. Retain literal CSV row numbers.
2. Plot streams against stored time with labels such as `CSV row 34 — EEG, unit unverified`. Report exact missing values, constants, and repeated-value runs descriptively; these are not automatic quality exclusions.
3. Explore task logs and questionnaire distributions separately. The chosen preliminary target is working baseline versus both stress-task periods; questionnaire-derived targets were not selected.
4. If a later task authorizes modeling, an anonymous-row, within-release exploratory analysis may be considered after structural and signal-quality checks. It must state the unknown scale/reference/timing, hold out whole participants, and avoid claims about named locations, physical fNIRS channel budgets, or calibrated physiology. Normalizing values cannot recover missing locations or processing history.

The minimal unblock package is the original acquisition/export model plus the row table and settings identified above, explicitly tied to version 1.0.0 and covering participant exceptions. Author contact would require separate authorization; none was undertaken.

## Verification record

The current published manifest was fetched and matched the existing cached manifest byte-for-byte. The following complete cached metadata files matched its SHA-256 hashes. README was also fetched again and matched the cache. A fresh EEG-coordinate fetch returned HTTP 502; the verified cached file was used instead. Cache: `/tmp/physionet-41-evidence-mgws3ijm` (temporary, not a durable dependency).

| File | SHA-256 |
| --- | --- |
| `README.txt` | `1edf32eda537806695f8e3789c80b2149e16c7533a0ccf404d223368a4c0e1a5` |
| `EEG_32_Channel_mapping.xyz` | `862f234b15bfa49db6fba04fcaf1a62c3e3427cde7c86151804f3faa2df36318` |
| `fNIRS_frontal.xyz` | `074281ae778c55e474adc8fd5e89efe6c35f639362261dea641e9fb976702b01` |

These hashes establish file identity, not the correctness of the metadata. The report's claims concern the sources inspected on the date above. Later author clarification or a revised release can change the blocker status.
