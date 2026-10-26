# Skill Effectiveness Evidence Protocol

This protocol adapts the useful idea of paired "with skill / without skill" task runs to the vintage-compressor research workflow. It is a test design, not a claim that an agent benchmark has already been executed.

## Purpose

Measure whether the Vintage Compressor Evidence Skill improves the correctness and reproducibility of research artifacts, rather than judging the prose quality of the answer.

## Paired-run design

1. Freeze a task fixture, repository commit, input references, config, tool permissions, model/version, and scoring rubric.
2. Run the same task once without loading `.github/skills/vintage-compressor-evidence/SKILL.md` and once with it loaded.
3. Randomize run order and use fresh workspaces. Keep all external provider/accelerator actions disabled.
4. Give both runs identical source documents and synthetic fixtures. Do not let one run see the other's output.
5. Have a deterministic verifier score artifacts, then conduct a blinded human review for source interpretation where deterministic checking is insufficient.
6. Publish both outputs, the verifier version, rubric, failures, and hashes. Do not cherry-pick only successful tasks.

## Required checks

Each run receives pass/fail results for:

- Reference identity, revision/serial handling, source URI, page/figure/table locator, measurement conditions, raw-capture SHA-256, calibration notes, and uncertainty.
- Correct separation of manual/patent data, physical measurement, software reference, simulation, and synthetic test fixtures.
- Rejection of missing or non-finite metrics and refusal to turn missing data into zero.
- Correctly normalized, disclosed weights and publication of component metrics alongside any composite.
- Calibration/holdout disjointness and explicit leakage detection.
- Stable manifest/config/input/reference hashes and UTC JSONL logs.
- Secret redaction and adherence to dry-run, one-node, 1,000-combination, USD $0 defaults.
- Honest statements about whether weights, benchmarks, curves, and hardware validation actually exist.

## Scoring and reporting

Report raw pass counts and per-check outcomes, not only a weighted aggregate. If a composite is useful, publish its rubric and weights before the runs. Record task and run IDs, skill-present boolean, prompt/input hashes, source commit, software/model versions, verifier hash, wall-clock duration, and any failure. Treat missing artifacts as failures, not implicit passes.

A skill improvement is supported only if repeated paired runs show an improvement on the predeclared checks without increasing severe errors. One successful example is anecdotal evidence, not a benchmark result.

## Safety and interpretation

This protocol evaluates process compliance, evidence completeness, and artifact integrity. It does not demonstrate audio quality, vintage authenticity, or that the skill improves every agent/model. No network access or paid execution is required for the initial synthetic fixture suite.
