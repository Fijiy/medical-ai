# PhysioNet manufacturer output follow-up

Investigated 2026-09-05 for [Validate PhysioNet channel mapping, signal units, and recording completeness](https://github.com/Fijiy/medical-ai/issues/49). This bounded follow-up checks manufacturer documentation for the remaining channel-order, unit, reference, and sampling questions. No recordings were downloaded, authors contacted, or channel map created.

**Result:** historical manufacturer material explains how slower optical measurements could appear on the faster EEG sample grid. It does not establish this release’s optical update rate, export units, physical wiring, or processing settings. The numerical conversion fingerprint in [the recording validation report](physionet-recording-validation.md) remains separate evidence; no manufacturer source found here independently confirms its exact constants or scaling.

## Evidence that narrows the uncertainty

| Question | Primary evidence | Limit for this dataset |
|---|---|---|
| Historical optical hardware and rate | The manufacturer-uploaded 2020 presentation *Wireless EEG and fNIRS recordings* identifies Artinis OctaMon, eight optical channels, 760/850 nm, and 50 Hz alongside g.Nautilus EEG at 500 Hz. [Presentation](https://www.researchgate.net/publication/340886076_Wireless_EEG_and_fNIRS_recordings) | This establishes a historical configuration, not which hardware or settings produced the release. The presentation’s Simulink diagram was not available at readable detail in the retrieved text. |
| Synchronization and output grid | The companion Spring School Q&A says g.Nautilus drives Simulink at 250/500 Hz and fNIRS is sampled at that same rate. g.tec’s practical guide likewise says the faster EEG amplifier acts as master. [Manufacturer Q&A](https://www.researchgate.net/publication/340885835_Questions_and_Answers_of_Day_4_of_the_Spring_School_2020), [g.tec guide](https://www.gtec.at/2021/04/12/combined-fnirs-eeg-recordings/) | A shared exported sample grid does not establish the rate of new optical measurements. Neither source specifies this release’s interpolation, repeated-sample behavior, clock handling, or delay correction. |
| Current optical rate | The current g.tec product page specifies 10 Hz optical acquisition and 250/500 Hz EEG. [Specifications](https://www.gtec.at/product/gnautilus-wireless-eeg-fnirs/) | The 10 Hz specification and historical 50 Hz presentation differ. Neither is sufficient to assign this dataset a native optical rate or prove a hardware revision. |
| EEG reference | The manufacturer’s *g.Recorder User Manual* 5.16.00, pp. 89–90, documents selectable bipolar derivations and common average reference (subtracting the average of selected EEG channels), plus selectable channel filters. [Manufacturer manual hosted by distributor](https://cdn.prod.website-files.com/67e282af90833afc9f8a6c39/6859aee6145091c5072d4866_grecorderusermanual.pdf) | Product identity alone does not determine the recording’s reference. This is g.Recorder documentation, not the original study’s saved Simulink configuration. |
| EEG unit displays | The same manual, p. 37, permits µV, mV, or V in channel display settings and explicitly limits sensitivity settings to visualization. [Manual](https://cdn.prod.website-files.com/67e282af90833afc9f8a6c39/6859aee6145091c5072d4866_grecorderusermanual.pdf) | A display-unit selector is not a declaration of units for these CSV numbers. No release-specific EEG export scale was recovered. |

## Optical units and the exact conversion constants

The suggested 2017 catalog is an **Artinis** catalog, rather than a g.tec Simulink output manual. Its indexed theory section describes concentration changes in micromolar (µM), with optical density defined using a base-10 logarithm. The full PDF could not be downloaded from this historical URL during this pass; this finding rests on the indexed PDF excerpt and publisher identification. It must not be treated as an inspected export specification. [Artinis Product Catalogue 2017, indexed p. 12 and publisher page](https://neurolite.ch/sites/default/files/Product%20Catalogue.pdf)

Artinis’s accessible theory page instead writes its equation with concentration in millimolar (mM), extinction coefficients in mM⁻¹·cm⁻¹, distance in centimeters, and a dimensionless differential pathlength factor (DPF, accounting for the longer path scattered light travels). Optical density (OD) is dimensionless. These are conventions for expressing the equation, not contradictory measurements: 1 mM equals 1,000 µM. Neither document specifies the scale of this study’s saved arrays. [Artinis theory](https://artinis.com/theory-of-nirs)

The [recording validation](physionet-recording-validation.md) establishes a conversion fingerprint with inverse matrix:

```text
14 × [[1.1596, 0.7861],
      [0.6096, 1.6745]]
```

That result and the matching wavelength/chromophore interpretation belong to the separately executed validation, not this documentation search. No retrieved manufacturer block description confirms these four constants, their default row order, the factor 14, or an OD/mOD input convention. Here HbO means oxygenated hemoglobin and HbR means deoxygenated hemoglobin.

The scale ambiguity survives an exact numerical match. **Conditionally**, if the coefficients use mM⁻¹·cm⁻¹ and 14 represents distance × DPF in centimeters, ordinary OD inputs produce mM concentration changes. Feeding numbers expressed in milli-OD (mOD, one thousandth of an OD unit) through the same numerical matrix produces numbers expressed in µM. Thus identical numerical coefficients cannot distinguish these two unit conventions. Likewise, a product of 14 does not identify distance and DPF separately; 3.5 cm × 4 is only one possible factorization. No inference here uses signal amplitude.

## What the software search did and did not recover

The manufacturer’s publicly accessible *Highspeed Library* 3.16.01 manual describes general Simulink processing blocks and installed example models, but its searchable text has no fNIRS block specification. It does not supply the study’s acquisition model or an optical output-port table. [Manufacturer library manual](https://cdn.prod.website-files.com/67e282af90833afc9f8a6c39/6859d2649bb13d34fc62d8c6_ghisyslibrarydescription.pdf)

The manufacturer’s public Python integration delegates g.Nautilus acquisition to `gtec_gds`. Inspecting that package’s g.Nautilus source found configurable reference/filter options, but no optical conversion constants or fNIRS output specification. This modern implementation cannot establish defaults used by the earlier Simulink recording. [Manufacturer source documentation](https://gtec-medical-engineering.github.io/gpype/_modules/gpype/backend/sources/g_nautilus.html), [inspected package version 1.6.0](https://pypi.org/project/gtec-gds/1.6.0/)

These are bounded negative findings about the inspected public material, not a claim that a suitable manual cannot exist.

## Concrete remaining unblock requirement

Recover the **recording-specific acquisition/export model and configuration**, with enough information to establish:

- Optical output port order and scale: wavelength signals versus concentration changes, OD versus mOD, and mM versus µM; coefficient table, logarithm convention, baseline, distance and DPF.
- Physical source/detector wiring and its connection to exported channel indices, including confirmation of consistency across participants. The observed 74-to-66-row change removes the eye block; it does not change the number of optical rows.
- EEG channel-selection order, hardware/software reference, filters, and voltage scale at CSV export.
- Hardware/software versions, native optical update rate, and how optical samples were placed on the exported time grid.

A contemporaneous saved model, channel configuration, and matching driver documentation could resolve these together. Generic product specifications cannot substitute for that evidence. No outreach was performed.

Until then, preserve any validated numerical pair/order inference as **conditional**, not a verified anatomical map or unit declaration. Structural completeness checks and analyses using anonymous channel indices and relative, within-recording variation can proceed within their own limits. Defer physical localization, absolute concentration claims, microvolt threshold checks, and EEG–optical delay claims that depend on the missing metadata.
