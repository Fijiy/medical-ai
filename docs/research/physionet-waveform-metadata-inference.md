# PhysioNet: what careful waveform inspection can recover

September 5, 2026. Follow-up for [Validate PhysioNet channel mapping, signal units, and recording completeness](https://github.com/Fijiy/medical-ai/issues/49). No email, new recordings, or new Wayfinder map.

**The data support more than the earlier documentation search established.** The numbered EEG order has independent spatial support. Optical conversion order remains strongly supported mathematically. The recordings also exclude a simple 10 Hz repeated-value export and a simple average reference across all 32 saved EEG channels. Exact physical optical wiring and numerical units still cannot be uniquely recovered from these tests.

## Data and method

The [diagnostic script](../../scripts/physionet_waveform_diagnostics.py) reread all 35 cached paired recordings and recomputed each full-file SHA-256 against the release manifest. It inspected all values in the 32 EEG and 16 optical-input rows. The saved [diagnostic evidence](../validation/physionet/waveform-diagnostics.json) contains source/script checksums, row summaries, correlation matrices, and optical update counts.

For EEG spatial comparison, it uses eight 4,096-sample windows spread from 60 seconds through the recording's end: 131.072 seconds per person. Each window is analyzed separately in three frequency ranges, and its channel correlations are averaged with the other seven windows. Correlation describes how similarly two signals vary. The spatial score compares those correlations with negative distances between electrodes: a higher score means nearby electrodes tend to have more similar signals. Distances use the supplied coordinates without assigning their physical length unit.

This is an exploratory consistency test, not an anatomical measurement, a classifier, or an eligibility rule. Shared reference, movement, poor contacts, and genuine brain activity can all affect it. The first 60 seconds are omitted from these comparisons to examine behavior after startup, not to establish a preprocessing cutoff for the eventual experiment. No participant or channel is excluded.

## EEG order: a stronger working interpretation

Two fixed hypotheses were compared: the numbered electrode order in the coordinate file and the different sequence in the Methods prose. The numbered order won in **33 of 35 people in every frequency range**. The exceptions were p01 and p03.

| Frequency range | Median score, numbered order | Median score, Methods order | People favoring numbered order |
| --- | ---: | ---: | ---: |
| 1–4 Hz | 0.563 | 0.482 | 33/35 |
| 8–13 Hz | 0.616 | 0.525 | 33/35 |
| 1–30 Hz | 0.558 | 0.487 | 33/35 |

The result is not driven by a single electrode: recomputing scores after leaving out each electrode in turn gives 32–34 wins in 1–4 Hz and 33–34 in the other two ranges. These are sensitivity checks, not additional independent participants or significance tests. The three frequency ranges overlap and are not independent replications.

Together with the release's explicitly numbered metadata, this supports the following **inferred working order** for CSV rows 34–65:

```text
AF3 AF4 F7 F8 F3 FZ F4 FT7
FT8 FC5 FC3 FC4 FC6 C5 C1 CZ
C2 C6 CP3 CP4 CP1 CP2 P7 P3
PZ P4 P8 PO7 PO3 PO4 PO8 OZ
```

The [release's numbered channel section](https://physionet.org/content/neuro-stress-resilience-hci/1.0.0/#description) agrees with this order. The Methods list need not have been intended as an export order. The waveform result strengthens this interpretation, but does not establish every participant's wiring or justify changing p01/p03 to another order. A geometry score also cannot resolve all mirrored or nearby-location alternatives. The importer continues to retain literal row numbers; this inference is not silently substituted for verified metadata.

## Reference and numerical scale

If each exported EEG channel had exactly the mean of all 32 saved channels subtracted, their sample-by-sample mean would be zero, apart from rounding. Instead, the RMS size of that mean is **0.150–0.989** of the RMS size of individual channel values across the sampled windows. RMS measures the typical size of a varying signal. Synthetic positive and negative controls confirm this check detects an imposed average reference. Thus **simple common-average-referenced final output across these 32 channels is inconsistent with the data**. This does not identify the hardware reference or exclude earlier rereferencing followed by different channel processing.

Every inspected EEG value round-trips through 32-bit floating point within a relative tolerance of 1e-12, accommodating the CSV's decimal rounding. Most optical values do not. This supports a 32-bit numerical stage in the EEG path, with a different numerical path for optical values; it does not reveal V versus mV versus µV. A floating-point format stores numbers, not physical units.

There is a suggestive hardware-scale clue: some startup peaks are around 187,800 stored units. The manufacturer lists ±187.5 mV among available amplifier ranges; that is ±187,500 µV. This makes µV a plausible interpretation, but the peaks are transients rather than verified calibration plateaus, and the applied range, filter gain, and export scale are unknown. **No unit is assigned from this amplitude resemblance.** [Manufacturer catalog, g.Nautilus sensitivity specifications](https://www.gtec.at/wp-content/uploads/2019/10/gtec-Product-Catalog-2018-web.pdf).

The [previous optical conversion fingerprint](physionet-recording-validation.md#follow-up-a-numerical-fingerprint-for-optical-signal-identities) supports 850/760 nm inputs followed by HbO/HbR outputs under its stated coefficient convention. It cannot distinguish ordinary optical-density inputs with millimolar outputs from inputs scaled by 1,000 with micromolar outputs. Both conventions preserve the same numerical matrix. Optical density describes attenuation of light; millimolar and micromolar are different concentration units.

A caution from an original study using this device family is concrete: it describes odd optical channels as 760 nm and even ones as 850 nm, opposite to the first/second input interpretation suggested by our coefficient match. That study is not this release, but it demonstrates why generic port-order descriptions cannot certify the physical wavelength labels here. [*Using Concurrent fNIRS and EEG Measurements to Study Consumer's Preference*](https://www.researchgate.net/publication/356829617_Using_Concurrent_fNIRS_and_EEG_Measurements_to_Study_Consumer%27s_Preference).

## Optical locations and timing

The eight optical groups were already recovered from exact numerical dependencies. To check whether the first four and last four behave like two groups of neighboring channels, we compared their first differences after one-second averaging, separately for each candidate wavelength. All 35 possible unordered four-plus-four partitions were tested. The sequential split had the highest within-group versus between-group similarity in **16/35** people for the first input and **18/35** for the second. Its median advantage was 0.120 and 0.161 respectively. This supports a useful grouping hypothesis, but not a unique physical wiring map. In particular, similarity alone cannot label either group left or right.

The coordinate file supplies another unresolved clue: T7's coordinates are the left-right reflection of T3, and T8's are the reflection of T4. However, the page labels T3/T4 as AF8/AF4 and T7/T8 as AF3/AF7. Under symmetric anatomical naming, the latter two positions would be reversed. This is a **possible T7/T8 inconsistency**, not permission to swap their physical labels. A coordinate-distance comparison after swapping groups 7/8 did not consistently improve the optical result. [Release optical labels](https://physionet.org/content/neuro-stress-resilience-hci/1.0.0/#description), [released optical coordinates](https://physionet.org/files/neuro-stress-resilience-hci/1.0.0/fNIRS_frontal.xyz).

Across all **560 optical input rows**, after the first 60 seconds, recorded values change **20.334–48.493 times per second**; median 28.866. Therefore the export cannot simply repeat each 10 Hz optical measurement unchanged until the next one. Interpolation or filtering of a slower stream could generate extra changes; repeated values could conceal updates in a faster stream. These counts are **stored-value change rates**, not independently verified native measurement rates. Historical 50 Hz hardware is compatible with this evidence but is not established by it.

## Signal problems missed by whole-row structural checks

Some EEG rows vary enormously at startup and then occupy an extremely narrow range. Examples below use the central 98% of values after 60 seconds, in unverified stored units:

| Participant, CSV row | First-60-second maximum absolute value | Later 1st–99th percentile range |
| --- | ---: | --- |
| p01, row 48 | 187,844.609 | 0.00022834 to 0.00027933 |
| p03, row 44 | 29,975.117 | 0.00035507 to 0.00040741 |
| p28, row 42 | 187,857.125 | −0.00053322 to −0.00048277 |
| p31, row 61 | 187,818.094 | −0.00027931 to −0.00022832 |

These examples explain why “no completely constant rows” was insufficient to establish useful signals. They need investigation during signal-quality decisions. We do not assign a cause, adopt an amplitude threshold, exclude channels, or certify 33 eligible participants. Both p01 and p03 also contain such narrow-range rows, which may affect their spatial scores; causation has not been shown.

## What can proceed without email

The numbered EEG order and optical conversion order are now evidence-backed **working hypotheses**, with the limits above. Analyses that use anonymous rows and relative variation can avoid requiring an absolute voltage or concentration scale, provided their later preprocessing and evaluation choices respect participant separation. Named optical-location comparisons and calibrated amplitude thresholds still require an explicit assumption or stronger evidence; the data checks do not turn those into established facts.

The original GitHub investigation is [closed with declared working assumptions](https://github.com/Fijiy/medical-ai/issues/49#issuecomment-5623550192); full physical mapping and unit verification were not achieved. Remaining comparison and protocol questions belong to the existing sensor-configuration and preprocessing decisions. The data investigation and diagnostic checks are complete. An independent review reproduced the headline figures and tested the diagnostic pipeline with known synthetic signals; no actionable correctness or provenance defect was found. No outreach is needed to preserve or use these findings within their stated limits.

## September 10: paper-supported working assumptions

The user asked whether reasonable assumptions could let the project proceed without email. **Use µV (microvolts) as the working EEG unit and the numbered EEG order above as the working row interpretation.** Label both as assumed/inferred in analyses. This is an explicit analysis convention, not newly verified acquisition metadata; the inventory's verified-unit and verified-mapping fields remain unknown.

The distinction matters: the electrode positions themselves are published. What we inferred is their connection to CSV rows. The [PhysioNet dataset article](https://physionet.org/content/neuro-stress-resilience-hci/1.0.0/#description) supplies the 32 numbered electrode names and coordinates, places the eight optical channels over the prefrontal region (forehead), and identifies AFz as ground. It does not declare the saved voltage/concentration units or identify the EEG reference. Ground and reference are different electrical roles; AFz must not be relabeled as the reference.

| Quantity | Working convention | Evidence and scope |
| --- | --- | --- |
| EEG amplitude | Treat one saved unit as 1 µV; label plots “EEG (assumed µV)” | An original study using the g.Nautilus EEG–fNIRS device family explicitly reports EEG measurements in microvolts. This supports the convention, but is a different experiment. [Consumer-preference study](https://www.researchgate.net/publication/356829617_Using_Concurrent_fNIRS_and_EEG_Measurements_to_Study_Consumer%27s_Preference). |
| EEG positions | Numbered list above, assigned provisionally to CSV rows 34–65 | Published numbered metadata plus the 33/35 waveform comparison. Use “inferred” for row labels; the comparison does not prove every participant's wiring. |
| Optical-density inputs | Dimensionless OD if the saved values are unscaled OD | The release calls these rows optical density. The missing export scale still permits milli-OD. [Manufacturer's equation convention](https://artinis.com/theory-of-nirs). |
| Derived optical concentrations | Treat saved values as **assumed mM**; multiply by 1,000 to display assumed µM | Following the user's further request for a concrete convention, select the unscaled-OD interpretation: matched coefficients in mM⁻¹·cm⁻¹ and an assumed effective path length of 14 cm imply mM. Scaled milli-OD would instead imply µM using the identical numerical matrix; that alternative remains unexcluded. |

With the EEG assumption, software requiring volts would receive saved values multiplied by `1e-6`; variance or power expressed in volts squared would use `1e-12`. These are unit conversions under the assumption, not an implemented importer change. Absolute amplitude thresholds still need a separate justified quality decision; the µV assumption alone does not validate them.

The paper check also rules out two tempting shortcuts. Roy and Nuamah's [2025 stress-resilience study](https://journals.sagepub.com/doi/full/10.1177/10711813251364795) says the physiological recordings were collected but not reported, so it supplies no missing EEG/fNIRS scale. Its task-performance abbreviation “OD” means overall deviation, not optical density. The release's cited [2024 working-memory graph paper](https://www.sciencedirect.com/science/article/pii/S1389041724000329) uses a different 26-person, 28-channel dataset; its settings cannot establish this release's settings.

A newer [Arduino prototype paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC13259060/) cites this exact release's p01 directory and reports band power in µV². It is weak additional precedent for the EEG convention, since it provides no reproducible import scaling or selected CSV row. Its prototype electrode placements are not this dataset's electrode map. See the [bounded paper inspection](physionet-manufacturer-output-followup.md#september-10-follow-up-downstream-arduino-paper).

This permits clearly labeled exploratory EEG interpretation without email. It does not resolve optical source–detector wiring, establish anatomical conclusions, or certify absolute physiological amplitudes. The original ticket's closure records this limited investigation outcome; it does not certify its initially sought full physical-validation outcome.

### Optical unit decision following the user's further request

Adopt **ordinary dimensionless OD → mM** as the working optical convention, rather than leaving every exploratory plot in unspecified stored units. This is a dimensional interpretation of the recovered equation, not a new declaration found in the paper. The release calls rows 2–17 optical density, without specifying a multiplier. With the matched extinction coefficients expressed in mM⁻¹·cm⁻¹ and the numerical factor 14 interpreted as an effective light path in centimeters, the resulting concentration unit is mM. The [manufacturer's theory page](https://artinis.com/theory-of-nirs), rechecked September 10, explicitly uses dimensionless OD, those coefficient units, and mM concentration.

The already saved waveform evidence provides a scale check: across all 560 optical input rows, the median of their after-60-second medians is 1.5976832, with row medians from 0.5346515 to 1.8324029. Large startup transients must not be mistaken for typical values. These ranges do not identify a unit by themselves or rule out hidden scaling; the decision rests on taking the published OD description literally together with the dimensional equation. No new raw-file scan was needed.

For presentation, `0.001` saved concentration units becomes **1 assumed µM**; `0.05` becomes **50 assumed µM**. Label plots “Derived hemoglobin signal (assumed µM)” when multiplied by 1,000. A numerical offset is not a verified absolute tissue concentration, and this unit convention does not establish the original baseline. Preserve raw values and verified metadata fields. This explicitly supersedes the earlier recommendation to leave primary optical exploration in unspecified stored units. It does not remove the remaining physical-mapping requirements from the ticket.

## Reproduce

```sh
python3 scripts/physionet_waveform_diagnostics.py
python3 scripts/physionet_waveform_diagnostics.py --verify-existing
```

The first command reads existing cached recordings and verifies their current hashes. The second tests the spatial/reference controls, checks saved coverage and provenance declarations, and independently recomputes stored geometry scores and optical partition summaries. It does not rehash current raw recordings. All synthetic controls and measured findings are distinct from the still-unresolved physical metadata.
