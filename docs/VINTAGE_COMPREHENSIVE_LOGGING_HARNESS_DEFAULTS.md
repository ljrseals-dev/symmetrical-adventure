# Vintage Comprehensive Logging Harness — Project Defaults

**Status:** initial defaults for review; not evidence of a completed build, hardware test, or validated score.

## Goal

Create repeatable, auditable runs for comparing compressor candidates with revision-specific vintage hardware references. The reference unit, its manual/schematic, and independent measurements are authoritative. Candidate DSP/neural implementations are hypotheses, not ground truth.

## Files

- `config/vintage_comprehensive_logging_harness.json` — machine-readable default configuration.
- `artifacts/vintage-comprehensive-logging-harness/` — default local output directory; generated results should not be committed unless explicitly curated.
- Brute Genius objective registry — objectives must be named, registered, deterministic, and tested. Do not pass caller-provided executable code.

## Safe initial defaults

- Starts in `dry_run`; accelerator launch is disabled.
- Cost ceiling is USD 0.00 and node cap is 1. This intentionally prevents paid execution until an operator reviews a concrete plan and opts in.
- Search is capped at 1,000 combinations for the initial profile, below the server's hard cap.
- No telemetry, automatic uploads, remote configuration, or update checks.
- Each run should record the repository commit, config hash, input/reference hashes, environment, UTC timestamps, and failure details.
- Reject NaN/Infinity and incomplete reference metadata. Never score a candidate against its own training/calibration data as the only validation.
- Keep raw captures and derived/aligned copies distinct. Any level alignment must be recorded; preserve original captures.
- Listening tests should be blind and level matched. The configured 0.1 dB tolerance is a target for the test harness, not proof that a test achieved it.

## Metrics and interpretation

The defaults define a reporting contract, not a claim that these measurements are already implemented. Report component errors individually: static transfer curve, envelope trajectory/timing, frequency response, harmonic spectrum, intermodulation, transients, and stereo behavior. Harmonics are reported individually in dBc, alongside THD and test conditions. A composite score is valid only when every required component is present and the calibration/holdout split is respected.

The default weights are provisional starting values. They must be justified against repeatability, measurement uncertainty, listening results, and use case before being treated as a ranking standard. Never label a result “authentic vintage” from a composite score alone.

## Expected run artifacts

### `run_manifest.json`

Include schema version, run ID, start/end time, git commit, config SHA-256, environment, objective name/version, reference unit/model/revision or serial, source URL and page/figure, calibration/holdout identifiers, input/reference SHA-256 hashes, sample rate, channels, and explicit launch/cost settings.

### `candidate_results.jsonl`

One JSON object per candidate with candidate ID, parameter values and units, objective version, evaluation status, each component metric, composite error (only when valid), runtime, and warnings. Lower error is better for the configured composite. Do not silently omit missing metrics or turn them into zero.

### `measurements.jsonl`

One record per measurement with test type, frequency/level/control settings, units, measured value, uncertainty/repeatability, analyzer bandwidth, calibration chain, and source capture IDs.

### `run.log.jsonl` and `failures.jsonl`

Structured UTC events. Errors should include stable error codes, stage, candidate/run IDs, and a concise diagnostic. Credentials, access tokens, private keys, and environment secrets must never be logged.

## Build and validation sequence

1. Install the existing project in a clean Python 3.10+ environment: `pip install -e ".[test]"`.
2. Run the current suite: `pytest -q`.
3. Validate the JSON config against a strict schema in a subsequent implementation step; reject unknown keys and non-finite numbers.
4. Add tests for deterministic serialization, stable hashes, missing metadata, invalid units, non-finite values, holdout leakage, and cost/combination limits.
5. Implement and test a bounded reference-metric objective before registering it in Brute Genius.
6. Use synthetic fixtures for unit tests; do not claim hardware accuracy from synthetic fixtures.
7. Run hardware capture and blind listening validation only when real reference recordings, calibration notes, and test conditions are available.
8. Call `brute_genius_plan` before any accelerator run. Do not launch unless the operator explicitly opts in, reviews the estimate, and supplies a nonzero approved cost ceiling.

## Acceptance gates

- [ ] Existing Brute Genius tests pass unchanged.
- [ ] Configuration is validated strictly and deterministically.
- [ ] Logs/results contain enough metadata to reproduce a run without secrets.
- [ ] Invalid/missing data fails closed; no fabricated zero metrics.
- [ ] Every score includes component metrics and clear units.
- [ ] Held-out measurements and blind, level-matched listening results are kept separate from calibration.
- [ ] No claim of vintage authenticity without independently measured hardware agreement and listening evidence.

