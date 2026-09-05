# Gates: PhysioNet recording validation

OWNS: scripts/physionet_inventory.py, scripts/physionet_optical_checks.py, tests/test_physionet_inventory.py, docs/validation/physionet/**, docs/research/physionet-recording-validation.md

Scope: inspect all released paired CSVs, retain integrity and structural evidence, test importer and marker exceptions, and establish metadata or explicitly preserve its blockers on the existing Wayfinder ticket.

- [x] G1: Importer checks detect malformed, nonfinite, uneven, and truncated data and preserve documented marker exceptions
  CHECK: python3 tests/test_physionet_inventory.py
  EXPECT: IMPORTER CHECKS PASSED
  EVIDENCE: automatic-evidence=v1; definition-sha256=136aaf48f59335fb2c8fb9aba2167aa3a1b33b14199c5ef7adc19e88188d620a; exit=0; EXPECT=matched; output-sha256=ff9449f2445372ec2259901e946c8e48eed915436078297b0a98b17c03a38f36; output-bytes=546; shell=/bin/sh; cwd=/Users/kairos/repos/josh/medical-ai; path=7540f1eb1c7b/29 entries

- [x] G2: Every paired recording in the pinned manifest has a full-file hash-verified inventory with per-row and timing evidence
  CHECK: python3 scripts/physionet_inventory.py --verify-inventory docs/validation/physionet
  EXPECT: INVENTORY VERIFIED
  EVIDENCE: automatic-evidence=v1; definition-sha256=962ea13c9a8ec1d371dc98d705e9c2f0ba481fb2787982c8a46aa201ba4d7102; exit=0; EXPECT=matched; output-sha256=68e90771552e8ff074272a79414e4fc7c4d260016f92586c7830c955e9f877f9; output-bytes=62; shell=/bin/sh; cwd=/Users/kairos/repos/josh/medical-ai; path=7540f1eb1c7b/29 entries

- [x] G3: Report distinguishes measured file structure, condition coverage, eligibility still awaiting policy, and unresolved mapping/units with source evidence
  EVIDENCE: Full report reconciled against 35 final schema 2 inventories and 560 optical equations; report counts verified independently. 33 target-boundary records distinguished from eligibility, p11 unknown from p16 missing, and all physical labels/units left unresolved. Independent review findings fixed and rechecked.

- [x] G4: Existing ticket and map accurately record results and any remaining blockers without a new map or premature validation claim
  EVIDENCE: Results posted at https://github.com/Fijiy/medical-ai/issues/49#issuecomment-5552139442; issue reread OPEN and assigned to Fijiy. Existing map and native blocking edges unchanged; no successful full-validation or closure claim.

- [x] G5: Empirical optical dependency checks recover known synthetic pairings and report every real recording without assigning physical labels
  CHECK: python3 scripts/physionet_optical_checks.py --verify-existing
  EXPECT: OPTICAL EVIDENCE VERIFIED
  EVIDENCE: automatic-evidence=v1; definition-sha256=9617ff4a86dd44bbc718bfa670c8a1e1a0de002a6a9e6e27f480de4c8a193638; exit=0; EXPECT=matched; output-sha256=b979886afef6d5533a6b3b5d85d035171751423e081cf8673c8384bd65bd9468; output-bytes=48; shell=/bin/sh; cwd=/Users/kairos/repos/josh/medical-ai; path=7540f1eb1c7b/29 entries
