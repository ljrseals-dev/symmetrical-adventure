Copyright © 2026 Lewis James Seals Jr. All rights reserved.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT.

# Vintage Compressor Research — Brute Genius

**Status: research / instrumentation scaffold, not a trained or validated compressor model.**

This branch documents an experimental workflow for studying vintage compressor behaviour and, eventually, comparing a parameterized or learned compressor against documented reference behaviour. Brute Genius is the combinatorial-search component: it can enumerate a bounded discrete parameter space and rank candidates against registered objectives. It does **not**, by itself, emulate analogue hardware, train a neural network, or establish that a candidate sounds like a particular unit.

The intended research targets are vintage compressor families and their documented behaviours: static input/output transfer curves, threshold and ratio, knee, attack/release envelopes, makeup gain, program dependence, saturation, harmonic/intermodulation products, transient response, and stereo-link behaviour. A named hardware model should only be claimed as a target when its source material and measurement provenance are recorded.

## What is in this branch

The branch has been scoped around a **Vintage Comprehensive Logging Harness** and a conservative, reproducible experiment plan. The documented defaults are:

- Dry-run by default; accelerator execution disabled unless explicitly enabled.
- Maximum of 1,000 parameter combinations and one worker/node per run.
- A hard cost ceiling of USD $0 for the default dry-run.
- Stereo, 48 kHz, float32 as the proposed reference signal format.
- JSONL event logging and hashes/manifests intended to make runs auditable.
- Separate artifact categories for run manifests, candidate results, measurements, logs, and failures.
- Separate measurements for static curves, envelope behaviour, frequency response, harmonic distortion, intermodulation, transient response, and stereo behaviour. These must not be collapsed into a single score without publishing the scoring definition.

These are **configuration and design targets**, not proof that every logger, validator, objective, artifact writer, test, or accelerator path is implemented or has passed. Review the actual source and test output before relying on any capability.

## What changed

This research branch is intended to separate reference collection, candidate evaluation, and evidence reporting rather than presenting an unverified model as finished. The logging plan makes the experiment limits explicit, separates different measurement classes, and calls for hashes and manifests to connect results to their exact inputs and configuration.

No claim is made here that vintage hardware was physically measured, that a complete manual or patent survey was finished, that Brute Genius completed a search run, or that an emulator has been validated against a hardware unit. The presence of a plan or configuration is not the same as a working end-to-end implementation.

## Weights, training, and model status

**No trained weights or verified model checkpoint are reported by this README.** No weight file, architecture, training dataset, optimizer history, checkpoint hash, or validation split is identified here. Consequently:

- There is no defensible claim of a trained neural compressor in this branch.
- There are no published training-loss or validation-loss results.
- There is no verified checkpoint to download or use for inference.
- Any future weights must be accompanied by a checkpoint hash, architecture/configuration, dataset provenance and licensing, training procedure, and held-out evaluation results.

Do not interpret parameter-search candidates or a configuration file as neural-network weights.

## Results and curves

**Measured results and reference curves are currently unverified / not published in this README.** No numeric benchmark table, measured transfer-curve dataset, plotted comparison, blind listening test, or error metric is provided here. We therefore do not report invented values for THD, IMD, attack/release timing, frequency response, curve error, latency, CPU use, or perceptual similarity.

When runs are implemented and executed, publish the following for each reference and candidate:

| Evidence | Required report |
|---|---|
| Static transfer curve | Input level and output level in dB, test conditions, threshold, ratio, knee, and makeup gain |
| Dynamic envelope | Attack/release settings and measured gain-reduction trajectory for specified test signals |
| Frequency response | Frequency, input/output level, sample rate, and measurement method |
| Harmonics / intermodulation | Test tones, levels, sample rate, FFT/window settings, and per-product results |
| Transients | Defined test signal, peak/overshoot, recovery time, and gain-reduction trace |
| Stereo behaviour | Channel correlation/link settings and left/right gain-reduction difference |
| Candidate comparison | Error metric, baseline, normalization, objective weights, and held-out test cases |
| Reproducibility | Source commit, configuration hash, input-signal hashes, software versions, seed, and complete run log |

Curves must label whether they come from a published manual/patent, a physical hardware measurement, a software reference, or a simulation. Those evidence classes are not interchangeable. Any digitized curve should include its source citation, axis calibration, units, and digitization uncertainty.

### Objective weights

No empirically validated objective-weight vector is reported yet. For transparency, the eventual objective should publish each metric's normalization and weight, for example:

`score = w_curve E_curve + w_envelope E_envelope + w_spectrum E_spectrum + w_transient E_transient + w_stereo E_stereo`

This is a proposed reporting shape, **not an implemented or validated scoring formula**. The weights must be selected and justified on training/validation references, then frozen before held-out evaluation. Report per-metric errors alongside the aggregate score so that one good metric cannot hide a poor match elsewhere.

## Safe, bounded workflow

1. Collect and cite reference documentation and any lawfully obtained measurements.
2. Define the parameter grid and a named, registered objective.
3. Run the planning/dry-run stage first; inspect combination count and estimated cost.
4. Execute only with explicit limits and only after confirming that the implementation and objectives are available.
5. Preserve JSONL logs, manifests, input hashes, candidate outputs, and failures.
6. Compare against held-out signals and report curves and per-metric errors.
7. Publish only reproducible results; distinguish simulated behaviour from physical hardware measurements.

The existing Brute Genius design describes a registry-only objective model (caller-provided code is not executed), cost-ceiling checks, and hard limits of 64 nodes and (10^9) combinations. These are stated design guarantees and should be verified against the checked-out implementation and tests before deployment. The conservative vintage-research defaults above are stricter than those general engine limits.

## Connect to Claude Desktop

Install the project from the repository root:

```bash
pip install -e ".[test]"
```

Add the server to Claude Desktop's MCP configuration, replacing the path with the absolute path to this checkout:

```json
{
  "mcpServers": {
    "brute-genius": {
      "command": "python",
      "args": ["/absolute/path/to/brute-genius/server.py"]
    }
  }
}
```

Restart the MCP client and confirm that the tools are exposed. For another MCP client, configure the same local stdio command. Do not expose an HTTP server publicly without an explicit security review; binding to `0.0.0.0` makes a service reachable on network interfaces and is not a safe default for a local research harness.

## Tests and release evidence

The repository's original quick-test commands are:

```bash
pytest test_server.py -v
npx @modelcontextprotocol/inspector python server.py
```

No test pass, full search run, hardware comparison, training run, or release artifact is asserted by this README. Attach the actual CI/test output and experiment manifest to a release before marking those checks complete.

## Current limitations

- This is not a plug-in or production audio processor.
- No validated vintage-compressor emulation is claimed.
- No trained weights, measured curves, or verified result tables are published here.
- A research plan does not establish code completeness or audio quality.
- Hardware-specific claims require cited source material or documented measurements.

The project is provided for research and development. Validate all results independently before using them to make engineering, purchasing, or sound-quality decisions.
