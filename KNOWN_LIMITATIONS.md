# Known Limitations and Human Decisions

## 1. Current Media Representation

The current implementation operates primarily on structured episode metadata containing:

- scene descriptions
- dialogue
- characters
- audio references
- source timecodes
- spoiler metadata
- contract information

It does not perform full production-grade video/audio understanding.

Actual frame-level visual analysis, speech recognition, speaker diarization, OCR, and waveform-level audio analysis would require dedicated multimodal processing components.

---

## 2. Video Rendering

The system produces an Edit Decision List-style trailer plan with exact source timecodes.

It does not currently render the final video.

Rendering was intentionally kept outside the core scope because the assignment prioritizes:

- agent decisions
- grounding
- constraint reasoning
- verification
- recovery

---

## 3. Semantic Verification

Deterministic checks are the primary source of truth for:

- scene existence
- timecodes
- evidence
- spoiler rules
- rights
- policies
- duration
- budget

An optional semantic verifier can review higher-level creative and safety concerns.

Semantic model judgments can still be imperfect.

Therefore, ambiguous cases should be escalated to human review rather than treated as automatically resolved.

---

## 4. Cultural Context

The system cannot reliably determine every cultural nuance from structured metadata alone.

In particular, dialect, regional identity, language and cultural context should not be used as shortcuts for assumptions about:

- personality
- behavior
- values
- socioeconomic status
- audience preferences

Culturally sensitive decisions may require review by an appropriate human editor or cultural reviewer.

---

## 5. Contract Interpretation

The system can enforce structured contract information supplied in the constraint map.

It cannot independently determine the legal meaning of an ambiguous contract.

Legal interpretation, exceptions, disputed rights and contractual ambiguity require human legal or rights-team review.

---

## 6. Spoiler Classification

The deterministic spoiler mechanism depends on the supplied spoiler map and story representation.

It can reliably reject explicitly protected scenes, but identifying every possible spoiler implication is harder.

A scene that appears harmless in isolation could reveal information through:

- dialogue context
- ordering
- juxtaposition
- music
- subtitles
- marketing copy

Ambiguous spoiler decisions should therefore remain reviewable by an editor.

---

## 7. Audience Data

Audience definitions are treated as planning signals rather than absolute truth.

The system does not assume that historical engagement automatically represents the preferences of an entire audience.

Audience-level correlations can contain sampling bias, demographic bias or historical production bias.

Creative decisions should therefore remain grounded in the supplied story and constraints.

---

## 8. External Model Availability

External LLM or multimodal providers may be unavailable, rate-limited or return unexpected output.

The system therefore includes a deterministic mock mode.

The mock mode allows the complete planning and verification workflow to be evaluated without requiring personal API credentials.

---

## 9. Adversarial or Untrusted Content

Episode descriptions, dialogue and other content should be treated as data rather than executable instructions.

An instruction appearing inside a scene description must not automatically override:

- system constraints
- contracts
- policies
- verifier rules
- human approval requirements

The current implementation provides the architectural separation for this behavior, but broader adversarial testing would be required for production deployment.

---

## 10. Cost and Scale

The demonstration dataset is intentionally small.

Production deployment would require additional controls for:

- large episode libraries
- media processing costs
- model-call budgets
- caching
- parallel processing
- storage
- observability
- retries
- provider failures

The architecture allows these concerns to be added without changing the core planning/verification responsibilities.

---

# Human-Controlled Decisions

The following decisions should remain with humans:

1. Final editorial approval of a trailer.
2. Legal interpretation of ambiguous rights or contracts.
3. Approval of culturally sensitive edits.
4. Final decision on ambiguous spoiler risk.
5. Approval of marketing claims.
6. Exceptions to policy or contractual constraints.
7. Final approval of music and third-party media rights.
8. Resolution of disagreements between creative objectives and safety/legal requirements.

The system should surface these decisions clearly rather than silently making them on behalf of the responsible human.

---

# Intentional Tradeoffs

Given the assignment time and scope, the implementation prioritizes:

1. Agentic planning
2. Source grounding
3. Deterministic verification
4. Selective failure recovery
5. Constraint enforcement
6. Reproducible mock execution
7. Structured observability

A full production media-analysis and rendering stack was intentionally not implemented.