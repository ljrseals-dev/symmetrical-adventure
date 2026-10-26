---
name: vintage-compressor-evidence
description: Use when changing the Vintage Comprehensive Logging Harness, collecting compressor references, scoring candidates, or reporting vintage compressor results. Enforces evidence provenance, fail-closed metrics, reproducibility, and honest model-status claims.
---

# Vintage Compressor Evidence Skill

## Ground truth hierarchy

1. Revision-specific hardware manuals, service documents, schematics, patents, and documented physical measurements.
2. Repeated, calibrated measurements from a named physical unit with chain-of-custody and uncertainty notes.
3. Software references and independently documented simulations.
4. Candidate DSP or neural outputs, which are hypotheses under test.

Never treat a candidate's own output, synthetic fixture, generated curve, or a model's learned prior as hardware ground truth.

## Required workflow

1. Inspect the current branch and tests before changing behavior. Preserve existing Brute Genius APIs unless a migration is explicitly requested.
2. Start in dry-run mode. Keep accelerator launches disabled, node count at one, combinations at or below 1,000, and the default cost ceiling at USD $0.
3. Identify every reference by model and revision/serial (redact private serial details if needed), source URI, page/figure/table, measurement conditions, raw-capture SHA-256, calibration notes, and uncertainty/repeatability.
4. Record input and reference hashes, config hash, source commit, objective name/version, software environment, UTC times, and run settings in a manifest.
5. Log one structured JSON object per line. Redact credentials recursively. Reject NaN/Infinity and unsupported object types.
6. Keep raw capture and aligned/processed copy separate. Record every alignment or gain-matching transform; never overwrite the original.
7. Keep calibration and holdout sets disjoint. Reject leakage. Do not report a composite score unless all required components are present and weights are finite, non-negative, normalized, and disclosed.
8. Report component metrics and units beside any composite. A synthetic fixture verifies plumbing only; it is not hardware validation.
9. Label every curve as manual/patent-derived, physical measurement, software reference, or simulation. Digitized curves need source locator, axis calibration, units, and digitization uncertainty.
10. Do not claim trained weights, successful hardware validation, perceptual similarity, latency, or measured results without corresponding artifacts and reproducible test output.

## Acceptance checks

- Missing reference metadata fails closed.
- Missing/non-finite metric values fail closed; never replace missing values with zero.
- Stable canonical JSON hashes are independent of key order.
- Secrets are redacted from logs and manifests.
- Holdout leakage is rejected.
- Scores cannot be generated from incomplete component sets or non-normalized weights.
- Dry-run defaults remain safe; external providers are not invoked by evidence-only tests.
- Tests are run and the exact outcome is reported; do not claim a pass unless it was actually observed.

## Output report template

For each experiment report: run ID; commit/config/input/reference hashes; reference class and citation; calibration and holdout identifiers; test signal and measurement conditions; component metrics with units and uncertainty; objective version and weights; failures/warnings; and an explicit evidence-status label.

Use `provenance_recorded_not_hardware_validated` until independent hardware comparison has actually been completed.
