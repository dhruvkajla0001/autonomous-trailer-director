
### Step 1 — Create the architecture note
# Autonomous Trailer Director — Architecture

## 1. System Overview

The Autonomous Trailer Director converts an episode package and audience definitions into validated, audience-specific trailer plans.

The pipeline is:

Episode Package
    ↓
Story Agent
    ↓
Story Map + Spoiler Map
    ↓
Constraint Repository
    ↓
Constraint Map
    ↓
Planner Agent
    ↓
Audience-specific Trailer Plans
    ↓
Verifier Agent
    ↓
PASS ───────────────→ Final Trailer Plan
    │
    FAIL
    ↓
Repair Agent
    ↓
Selective Segment Repair / Replanning
    ↓
Verifier Agent
    ↓
PASS → Final Plan
```

## 2. Core Components

### Story Agent

The Story Agent reads the supplied episode package and constructs a structured story representation.

It captures:

* scenes
* scene descriptions
* dialogue
* characters
* source timecodes
* spoiler information
* narrative relationships

The Story Map is the grounding source for trailer planning.

### Constraint Repository

The Constraint Repository loads:

* contracts
* territory restrictions
* content policies
* audience definitions

These are converted into a structured Constraint Map.

Policies and contracts are treated as decision rules rather than instructions passed only to an LLM.

### Planner Agent

The Planner Agent creates audience-specific trailer plans.

Each plan contains:

* audience
* audience promise
* emotional journey
* selected scenes
* exact source timecodes
* dialogue
* audio/music
* subtitles
* evidence
* planning rationale

The planner creates separate plans for different audiences rather than simply reusing one trailer.

### Verifier Agent

The Verifier Agent independently checks the generated plan.

Deterministic checks include:

* scene existence
* source timecode validity
* evidence grounding
* spoiler protection
* rights constraints
* policy constraints
* duration
* budget constraints

The verifier is authoritative for deterministic constraints.

An optional semantic verifier can additionally review:

* unsupported implications
* spoiler risk
* promise mismatch
* cultural stereotyping
* unsafe framing
* misleading audience targeting

The semantic model is not treated as the sole authority for deterministic validation.

### Repair Agent

When verification fails, the Repair Agent identifies affected segments and asks the Planner Agent to repair only those segments.

Unaffected segments are preserved.

Each repair increments the trailer revision.

The repaired plan is then sent through verification again.

This creates the loop:

```text
Plan
  ↓
Verify
  ↓
Failure?
  ├── No → Final
  └── Yes
        ↓
      Identify affected segments
        ↓
      Repair / Replan
        ↓
      Verify again
```

## 3. Memory and State

The system keeps structured state in:

* Story Map
* Constraint Map
* Trailer Plan
* Validation Result
* Decision Log

The trailer revision number records plan evolution.

Validation results record:

* failures
* warnings
* evidence
* affected segments
* recommended repair

This allows changes and repairs to remain observable.

## 4. Multimodal Grounding

The current implementation uses structured episode metadata containing scene, dialogue, audio and timecode information.

Important trailer decisions retain source evidence such as:

```text
scene:scene_02
dialogue:dialogue_02_01
contract:actor_nila
contract:track_licensed_uk_only
```

The architecture is designed so additional media-analysis providers can be introduced without changing the planning and verification interfaces.

The current mock mode intentionally prioritizes deterministic evaluation and reproducibility.

## 5. Verification and Failure Recovery

The system does not assume that a generated plan is correct.

Examples covered by automated tests include:

* nonexistent scene
* spoiler-protected scene
* expired music rights
* policy violation
* changed contract

Failures identify affected segments and trigger selective repair.

The repaired plan is independently verified before being accepted.

## 6. Audience Personalization

Audience definitions influence:

* audience promise
* emotional journey
* scene selection
* pacing
* dialogue emphasis
* music choice

The system does not treat historical engagement alone as sufficient evidence for creative decisions.

Audience-specific plans therefore represent different creative strategies while remaining grounded in the same episode.

## 7. Observability

The system records structured decision information including:

* selected segments
* planning rationale
* evidence
* validation results
* failures
* warnings
* revisions
* repair decisions

The generated `decision_log.json` provides an audit trail of trailer planning and verification.

## 8. Mock / Replay Mode

The repository supports deterministic mock execution so evaluators do not need personal API keys.

Example:

```bash
python -m src.pipeline --mode mock
```

This produces reproducible trailer plans and validation artifacts.

## 9. Human Control

The following decisions should remain subject to human editorial, legal or cultural review:

* final approval of trailer creative direction
* interpretation of ambiguous cultural context
* legal/contractual exceptions
* final spoiler classification where evidence is ambiguous
* final marketing claims
* approval of culturally sensitive edits
* approval of externally sourced music or media

The system is intended to assist these decisions, not silently override human approval.

## 10. Design Tradeoffs

The implementation prioritizes:

1. deterministic verification
2. source grounding
3. constraint enforcement
4. selective recovery
5. reproducibility
6. observability

Video rendering is intentionally not required. The output is an executable edit decision plan with exact source timecodes.

The current implementation also uses a mock provider so the complete workflow can be evaluated without external API dependencies.




