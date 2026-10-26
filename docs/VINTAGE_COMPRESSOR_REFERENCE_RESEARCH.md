# Vintage Compressor Reference Research and Validation Plan

**Status:** research plan; not a claim of completed exhaustive review  
**Purpose:** define a source-traceable reference dataset and objective for Brute Genius experiments  
**Reference rule:** hardware documentation and independent measurements are ground truth. A neural or DSP model is a hypothesis to test, never its own validator.

## 1. Scope and evidence policy

Build a manual-by-manual inventory before fitting parameters. "Vintage compressor" is not one topology: FET, optical, variable-mu, VCA, and feedback/feed-forward designs have different detector dynamics, nonlinearities, and control interactions. Do not transfer one model's timing, knee, or harmonic signature to another.

For each source, record:
- manufacturer, model, revision/serial applicability, publication date, document title and URL;
- page/figure/table number, exact parameter and units, test conditions, load, input/output level, bandwidth, and uncertainty;
- whether each item is a manufacturer specification, schematic inference, secondary-source claim, or independently measured result;
- rights/access notes. Link to manuals and cite figures rather than copying whole copyrighted manuals or drawings into this repository.

Do not call the source review "complete" until the source register is populated, each relevant section/figure is checked, and gaps are explicitly listed. Web search snippets are discovery aids, not a substitute for reading the source document.

## 2. Initial primary-source register

### UREI / Universal Audio 1176LN (FET limiter)
- Manufacturer product/specifications: https://www.uaudio.com/hardware/compressors/1176ln.html
- Manufacturer manual PDF: https://media.uaudio.com/assetlibrary/1/1/1176ln_manual.pdf
- Additional manual scan with service and technical sections: https://www.manualslib.com/manual/4166721/Universal-Audio-1176LN.html
- Record: ratio switches (4:1, 8:1, 12:1, 20:1), input-controlled drive/threshold interaction, independent output level, attack/release control direction, revision differences, transfer curve, THD test conditions, and schematics/service adjustment notes.
- Initial reported ranges in manufacturer material: attack about 20–800 microseconds; release about 50 ms–1.1 s. Verify against the exact revision and document before treating these as universal.

### Teletronix LA-2A (electro-optical, program-dependent recovery)
- Start with manufacturer/authorized manual sources and archived schematics; distinguish revisions and optical-cell variants.
- Required extraction: peak reduction and gain controls, meter calibration, optical detector and amplifier signal path, program-dependent attack/release/recovery, frequency response, distortion versus level/frequency, and the effect of level before the optical cell.
- Do not substitute a single fixed release constant for program-dependent recovery without evidence.

### Fairchild 660 / 670 (variable-mu tube limiter)
- Manufacturer manual and schematic PDF: https://www.historyofrecording.com/Manuals/Fairchild/Fairchild_670_stereo_limiting_amplifier_instructions_Schematics.pdf
- Additional manual source: https://fairchildusa.com/wp-content/uploads/2023/12/Fairchild-Model-670-Manual.pdf
- Record the six time-constant positions, fixed versus program-dependent release behavior, threshold/limiting curves, AC/DC threshold adjustments, channel linking and vertical/lateral matrix mode, balance/bias adjustment, frequency response, distortion test conditions, and tube/transformer stages.
- Published manual descriptions include attack settings around 0.2, 0.4, and 0.8 ms and release behavior from sub-second to long program-dependent recovery. Confirm exact values from the relevant table and revision.

### dbx 160 family (VCA; OverEasy knee)
- Manual with transfer curves and cited patents: https://www.barryrudolph.com/recall/manuals/dbx166.pdf
- Record hard-knee and OverEasy transfer curves, ratio/threshold calibration conventions, detector behavior, and patent numbers as printed for the exact model. Do not assume dbx 160, 160A, 166, and later models share the same circuit or controls.

### SSL G-Series bus compressor (console bus topology)
- SSL SiX guide with block diagram and G-Series bus compressor description: https://www.solidstatelogic.com/assets/uploads/downloads/six/SSL_SiX_User_Guide%20V1.0%20March_2019.pdf
- SSL current support/document index: https://support.solidstatelogic.com/hc/en-gb/articles/4414101800849-G-Series-Stereo-Bus-Compressor-User-Documents
- Record ratio/attack/release choices by revision, threshold/makeup interaction, stereo detector/linking behavior, sidechain filtering by revision, and block-diagram topology. Do not infer a harmonic signature from a block diagram alone.

This is a starting register, not a claim that these are every vintage compressor or every relevant manual. Expand by topology, manufacturer, and revision; include classic broadcast, mastering, studio, and console designs where source material is available.

## 3. What to extract from every manual, patent, and schematic

### Transfer curves and macros
1. Static input/output transfer curve: input level, output level, gain reduction, threshold, ratio, knee shape, makeup gain, and whether curves are calibrated at a stated frequency/load.
2. Dynamic envelope response: attack and release definitions, detector topology, overshoot/undershoot, recovery after isolated versus repeated peaks, program-dependent time constants, and inter-channel linking.
3. Control interactions: input drive, threshold, ratio, attack/release, sidechain filters, stereo link, bias/balance, output stage, and bypass. "Macro" here means a user-facing control or coordinated parameter set; document how each maps to circuit behavior.
4. Level-dependent behavior: input/output headroom, clipping onset, soft saturation, hysteresis or memory effects, and changes in detector behavior as drive increases.
5. Frequency-dependent behavior: frequency response at several levels, sidechain weighting, low-frequency modulation/pumping, high-frequency transient response, and bandwidth changes under drive.
6. Nonlinearity: THD and individual harmonic levels versus frequency and level; intermodulation distortion; polarity/asymmetry; residual spectrum; noise and hum. Record the analyzer bandwidth, weighting, fundamental level, and measurement chain.
7. Circuit evidence: signal-flow/block diagrams, schematic topology, detector/control-voltage path, gain element, tube/transistor/opto/VCA stage, transformers, coupling capacitors, bias networks, and calibration/test points.
8. Patent evidence: patent number, inventor, assignee, filing/publication/grant dates, claims relevant to the circuit, and cited figures. A patent is evidence of disclosed design, not proof that every production revision used it unchanged.
9. Revision caveats: component substitutions, service bulletins, serial-number cutoffs, and differences between a manual's idealized curves and measured units.

## 4. Harmonic and saturation measurement protocol

Use a calibrated loopback and retain raw recordings plus a machine-readable manifest. For each unit/revision:
- establish input/output calibration and bypass/null behavior;
- measure steady-state frequency response at low level and at multiple operating levels;
- capture sine sweeps or stepped tones at several frequencies and input levels, with fixed gain-reduction targets as well as fixed input levels;
- report H2, H3, H4… individually in dBc, THD, and noise floor; do not reduce "warmth" to one THD number;
- measure two-tone intermodulation and transient bursts;
- capture isolated transients and repeated pulses to estimate attack/release and program-dependent recovery;
- repeat at several control settings and document unit temperature, warm-up time, line voltage where applicable, output load, and sample-rate/converter details;
- repeat measurements to estimate repeatability and report uncertainty.

Separate distortion generated by the compressor from the test DAC/ADC, preamp, cables, and measurement chain. Level-match processed and reference audio for listening comparisons; preserve unlevel-matched captures as evidence too. Never claim a model's added harmonics are hardware-authentic without measurements under comparable conditions.

## 5. Brute Genius experiment design

Brute Genius currently performs discrete Cartesian enumeration and only accepts registered objective names. It has generic mathematical objectives, not a validated audio-reference objective. The initial work should therefore define and test a bounded, offline objective before launching any accelerator workload.

Candidate parameter axes (only where supported by source or measurements):
- detector topology / detector time constants;
- static curve threshold, ratio, knee width, and makeup gain;
- attack/release envelope parameters, including program-dependent modes;
- gain-cell nonlinearity and level-dependent saturation;
- harmonic coefficients or a physically motivated circuit model;
- transformer/coupling response and sidechain filtering;
- stereo link and channel interaction.

Avoid treating arbitrary polynomial coefficients as physical components. Keep parameters interpretable and constrain values to source-supported or measurement-supported bounds. Separate calibration parameters from held-out validation recordings.

### Multi-objective score

Do not collapse everything into a single "sounds vintage" score without reporting its components. For each candidate, report:
- static transfer-curve error (dB versus input level);
- envelope/attack-release error (time-domain and gain-reduction trajectory);
- frequency-response error (dB versus frequency and level);
- harmonic-spectrum error (per harmonic and THD under matched tests);
- intermodulation error;
- transient waveform/residual error;
- stereo/link behavior error where applicable;
- complexity/regularization penalty;
- confidence and measurement uncertainty.

Use a documented weighted score only for ranking. Publish component metrics, units, test conditions, weights, and Pareto alternatives so a low score in one dimension cannot hide a serious failure in another. Reserve entire test signals, levels, settings, and preferably a separate hardware unit for held-out evaluation.

### Compute and safety gates
1. Inspect the source code and tests; test with the mock provider first.
2. Add a named objective to the registry only after unit tests cover input schema, finite values, units, and deterministic scoring.
3. Call `brute_genius_plan` before every run. Use a conservative cost ceiling and the smallest possible parameter grid initially.
4. Do not launch large accelerator jobs just because the theoretical ceiling permits them. The server's throughput estimate is explicitly a heuristic; verify actual provider behavior and actual cost.
5. Keep any hardware captures local unless the owner explicitly approves sharing. Never upload copyrighted manuals, private measurements, or reference audio to a provider by default.
6. Make no claim of exhaustive manual review, hardware fidelity, or successful model fitting until it has actually been performed and the evidence is recorded.

## 6. Patent and diagram research checklist

For each candidate model, search official patent databases (USPTO, Google Patents, Espacenet/WIPO where relevant) using manufacturer, inventor, assignee, model, and circuit terms. Follow citations both backward and forward. Cross-check:
- patent claims and drawings against the production schematic;
- filing dates and patent term/status;
- whether the patent covers the compressor's core gain-control principle or only one subcircuit;
- whether the drawing is conceptual or gives component-level values;
- whether later revisions changed the topology.

Keep patent summaries factual and concise; link the source patent rather than reproducing its full text or figures.

## 7. Acceptance gates

- [ ] Source register contains model, revision, date, URL, pages/figures reviewed, and unresolved gaps.
- [ ] Every claimed curve or specification has a page/figure/table citation and stated test conditions.
- [ ] Static curve, dynamics, frequency response, harmonics, and intermodulation are measured independently.
- [ ] Training/reference and held-out test data are separated before parameter search.
- [ ] Objective functions are deterministic, tested, bounded, and interpretable.
- [ ] Cost plan reviewed before launch; mock-provider tests pass before any paid provider.
- [ ] Model results are compared against hardware evidence and a simple deterministic baseline.
- [ ] Claims are limited to the tested models/revisions and operating range.

## 8. Source links discovered during initial scoping

- Universal Audio 1176LN product specifications: https://www.uaudio.com/hardware/compressors/1176ln.html
- Universal Audio 1176LN manual: https://media.uaudio.com/assetlibrary/1/1/1176ln_manual.pdf
- Fairchild 670 instruction manual and schematics: https://www.historyofrecording.com/Manuals/Fairchild/Fairchild_670_stereo_limiting_amplifier_instructions_Schematics.pdf
- Fairchild Model 670 manual: https://fairchildusa.com/wp-content/uploads/2023/12/Fairchild-Model-670-Manual.pdf
- dbx 166 manual (OverEasy curves and printed patent references): https://www.barryrudolph.com/recall/manuals/dbx166.pdf
- SSL SiX user guide: https://www.solidstatelogic.com/assets/uploads/downloads/six/SSL_SiX_User_Guide%20V1.0%20March_2019.pdf
- SSL G-Series compressor document index: https://support.solidstatelogic.com/hc/en-gb/articles/4414101800849-G-Series-Stereo-Bus-Compressor-User-Documents
