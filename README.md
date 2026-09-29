
# 🎬 Autonomous Trailer Director

> **An agentic AI system that plans, verifies, and selectively repairs audience-specific trailers from a single episode package.**

The **Autonomous Trailer Director** transforms one episode into multiple audience-specific trailer strategies while preserving story truth, spoiler boundaries, cultural respect, contractual rights, policy compliance, source accuracy, accessibility, and budget constraints.

The system does not simply generate plausible trailer ideas.  
It **plans → verifies → repairs → re-verifies** before accepting a trailer plan.

---

## ✨ Key Capabilities

- 🎯 **Audience-specific trailer planning**
- 🧠 **Story-grounded creative reasoning**
- 🗺️ **Structured Story Map and Constraint Map**
- 🚫 **Spoiler protection**
- ⚖️ **Policy and contractual constraint enforcement**
- 🎵 **Rights-aware audio selection**
- 🔎 **Source evidence and exact timecode grounding**
- 🛠️ **Selective failure recovery**
- 🔄 **Automatic repair and re-verification**
- 🧪 **Deterministic mock/replay mode**
- 📋 **Machine-readable trailer plans**
- 📊 **Decision logging and traceability**
- 👤 **Human-in-the-loop controls**

---

# 🧩 Problem

Given:

- one episode package
- multiple audience definitions
- contracts and rights
- policy rules
- source metadata

the system must create **distinct trailer strategies** without compromising:

| Requirement | Protected By |
|---|---|
| Story truth | Story Map + source evidence |
| Spoiler boundaries | Spoiler Map + verifier |
| Audience relevance | Audience-specific planning |
| Cultural respect | Semantic verification |
| Contractual rights | Constraint Repository + rights checker |
| Policy compliance | Policy checker |
| Source accuracy | Exact scene/timecode evidence |
| Accessibility | Subtitle/audio planning |
| Budget | Constraint verification |

The system must also recover when a previously valid trailer becomes invalid because of a changed constraint, unavailable scene, expired rights, or policy issue.

---

# 🏗️ System Architecture

```text
                         ┌───────────────────┐
                         │  Episode Package  │
                         └─────────┬─────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │    Story Agent    │
                         └─────────┬─────────┘
                                   │
                                   ▼
                    ┌──────────────────────────┐
                    │ Story Map + Spoiler Map  │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Constraint Repository    │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │      Constraint Map      │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                         ┌───────────────────┐
                         │   Planner Agent   │
                         └─────────┬─────────┘
                                   │
                                   ▼
                    ┌──────────────────────────┐
                    │ Audience Trailer Plans   │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                         ┌───────────────────┐
                         │   Verifier Agent  │
                         └─────────┬─────────┘
                                   │
                        ┌──────────┴──────────┐
                        │                     │
                       PASS                  FAIL
                        │                     │
                        ▼                     ▼
                 ┌─────────────┐      ┌─────────────┐
                 │ Final Plan  │      │ Repair Agent│
                 └─────────────┘      └──────┬──────┘
                                             │
                                             ▼
                                      Selective Repair
                                             │
                                             ▼
                                        Re-verify
                                             │
                                             ▼
                                      Accepted Plan
````

### Core principle

> **The system does not accept an LLM-generated trailer simply because it is plausible.**

Creative plans must pass explicit validation before they are accepted.

---

# 🤖 Agent Responsibilities

## Story Agent

Builds the structured representation of the episode:

* scenes
* dialogue
* story beats
* spoiler boundaries
* source evidence

Output:

```text
Story Map
+
Spoiler Map
```

---

## Planner Agent

Creates audience-specific trailer strategies.

The planner considers:

* audience promise
* emotional journey
* scene selection
* pacing
* dialogue
* audio
* subtitles
* constraints
* source evidence

It produces machine-readable trailer plans with exact source timecodes.

---

## Verifier Agent

Acts independently from the creative planner.

It validates:

* scene existence
* source timecodes
* source evidence
* spoiler boundaries
* rights
* policy
* budget
* duration

Semantic verification can additionally evaluate:

* unsupported implications
* spoiler risk
* promise mismatch
* cultural stereotyping
* unsafe framing
* misleading audience targeting

The LLM is **not treated as the authority for deterministic constraints**.

---

## Repair Agent

When a trailer fails verification, the Repair Agent:

1. Identifies affected segments
2. Repairs only those segments
3. Increments the revision
4. Preserves unaffected segments
5. Re-verifies the repaired plan
6. Accepts the plan only after successful validation

```text
Invalid Plan
     │
     ▼
Identify Affected Segments
     │
     ▼
Repair Affected Segments
     │
     ▼
Increment Revision
     │
     ▼
Re-verify
     │
     ▼
Accept Only If Valid
```

---

# 🎯 Audience Personalization

The system generates three distinct trailer strategies:

### 👨‍👩‍👧 Family

Focuses on:

* accessible emotional framing
* family-safe material
* appropriate pacing
* clear narrative promise

### 🎓 Young Adult

Focuses on:

* stronger emotional momentum
* character tension
* faster pacing
* dialogue-driven hooks

### 🌎 Dialect / Regional Audience

Focuses on:

* culturally appropriate framing
* regional dialogue
* authentic emotional context
* respectful representation

Audience definitions influence:

* narrative promise
* emotional journey
* scene selection
* pacing
* dialogue emphasis
* audio strategy

The system does **not** simply select scenes based on historical engagement scores.

All trailers remain grounded in the same source episode while adapting the creative strategy to the target audience.

---

# 🔎 Grounding & Evidence

Important trailer decisions retain traceable source evidence.

Example:

```text
scene:scene_02
dialogue:dialogue_02_01
contract:actor_nila
contract:track_licensed_uk_only
```

This allows decisions to be traced back to the supplied episode and constraint data.

Each trailer segment can retain:

* scene ID
* source timecodes
* dialogue reference
* contract evidence
* audio evidence
* source evidence
* validation results

The current implementation uses **structured episode metadata as its primary grounding representation**.

---

# 🛡️ Verification & Safety

Deterministic verification covers:

* ✅ Scene existence
* ✅ Source timecode validity
* ✅ Source evidence
* ✅ Spoiler protection
* ✅ Rights restrictions
* ✅ Policy restrictions
* ✅ Duration
* ✅ Budget

Semantic verification can additionally examine:

* unsupported implications
* spoiler risk
* promise mismatch
* cultural stereotyping
* unsafe framing
* misleading audience targeting

This creates a separation between:

```text
Creative Generation
        │
        ▼
Independent Verification
        │
        ├── PASS ──► Accept
        │
        └── FAIL ──► Repair
```

---

# 🔄 Failure Recovery

The system supports selective recovery rather than regenerating an entire trailer.

Automated recovery coverage includes:

* ❌ Missing scene
* 🎵 Expired music rights
* 🚫 Policy violation
* 📜 Changed contract
* ⚠️ Spoiler rejection

When a failure occurs:

```text
Validation Failure
       │
       ▼
Identify Affected Segment
       │
       ▼
Repair Segment
       │
       ▼
Preserve Unaffected Segments
       │
       ▼
Increment Revision
       │
       ▼
Re-verify
```

This allows the system to respond to changing constraints without unnecessarily rebuilding the entire trailer.

---

# 📦 Repository Structure

```text
STAGE_TRAILER_DIRECTOR/
│
├── data/
│   ├── audience/
│   │   └── audiences_demo.json
│   ├── contracts/
│   │   └── contracts_demo.json
│   ├── episode/
│   │   └── episode_demo.json
│   └── policies/
│       └── policies_demo.json
│
├── sample_run/
│   ├── story_map.json
│   ├── constraint_map.json
│   ├── family_trailer.json
│   ├── young_adult_trailer.json
│   ├── dialect_region_trailer.json
│   └── decision_log.json
│
├── src/
│   ├── agents/
│   │   ├── planner_agent.py
│   │   ├── repair_agent.py
│   │   ├── story_agent.py
│   │   └── verifier_agent.py
│   │
│   ├── models/
│   │   ├── constraints.py
│   │   ├── story.py
│   │   └── trailer.py
│   │
│   ├── providers/
│   │   ├── base.py
│   │   ├── llm.py
│   │   └── mock.py
│   │
│   ├── repository/
│   │   ├── constraint_repository.py
│   │   └── episode_repository.py
│   │
│   └── tools/
│       ├── constraint_lookup.py
│       ├── policy_checker.py
│       ├── rights_checker.py
│       ├── scene_search.py
│       └── spoiler_checker.py
│
├── tests/
│   ├── test_constraint_repository.py
│   ├── test_llm_reasoning.py
│   ├── test_missing_scene.py
│   ├── test_models_and_demo_data.py
│   ├── test_pipeline_scaffold.py
│   ├── test_planner_agent.py
│   ├── test_policy.py
│   ├── test_policy_recovery.py
│   ├── test_providers.py
│   ├── test_repair_recovery.py
│   ├── test_rights.py
│   ├── test_rights_recovery.py
│   ├── test_scene_search.py
│   ├── test_spoiler.py
│   ├── test_spoiler_recovery.py
│   ├── test_story_agent.py
│   ├── test_verifier_agent.py
│   └── test_changed_contract_recovery.py
│
├── ARCHITECTURE.md
├── AI_COLLABORATION.md
├── KNOWN_LIMITATIONS.md
├── pyproject.toml
└── README.md
```

---

# ⚙️ Requirements

* Python **3.12+**
* pytest for development/testing

Install the project:

```bash
pip install -e .
```

Install development dependencies:

```bash
pip install -e ".[dev]"
```

---

# ▶️ Run the System

The repository includes a deterministic **mock mode** that requires no external API key.

```bash
python -m src.pipeline --mode mock
```

The pipeline:

1. Loads the episode package
2. Builds the Story Map
3. Loads contracts, policies, and audience definitions
4. Builds the Constraint Map
5. Generates three audience-specific trailer plans
6. Verifies every plan
7. Repairs invalid plans when necessary
8. Re-verifies repaired plans
9. Writes structured artifacts and decision logs

---

# 📊 Example Run

```text
============================================================
AUTONOMOUS TRAILER DIRECTOR
============================================================

Validated story map: PASS (8 scenes)
Constraint Map  : PASS (9 contracts, 5 rules)

Family Trailer
  Planning       : PASS
  Verification   : PASS
  Segments       : 4
  Duration       : 29.00s
  Revision       : 0
  Problems       : None

Young Adult Trailer
  Planning       : PASS
  Verification   : PASS
  Segments       : 4
  Duration       : 30.00s
  Revision       : 0
  Problems       : None

Dialect Region Trailer
  Planning       : PASS
  Verification   : PASS
  Segments       : 4
  Duration       : 31.00s
  Revision       : 0
  Problems       : None

============================================================
FINAL STATUS: PASS
============================================================
```

Generated artifacts are written to:

```text
sample_run/
```

---

# 📁 Generated Artifacts

## Story Map

```text
sample_run/story_map.json
```

Contains:

* structured story information
* scenes
* dialogue
* story beats
* spoiler boundaries

---

## Constraint Map

```text
sample_run/constraint_map.json
```

Contains:

* contracts
* policy rules
* audience definitions
* constraint information

---

## Trailer Plans

```text
sample_run/family_trailer.json
sample_run/young_adult_trailer.json
sample_run/dialect_region_trailer.json
```

Each plan contains:

* audience promise
* emotional journey
* selected segments
* exact source timecodes
* dialogue
* audio
* subtitles
* source evidence
* validation results
* revision information

---

## Decision Log

```text
sample_run/decision_log.json
```

Provides structured information about:

* planning decisions
* evidence
* validation
* repair decisions
* revisions

---

# 🧪 Testing

Run the complete test suite:

```bash
python -m pytest -q
```

The test suite covers:

* data/model validation
* story-map construction
* constraint loading
* scene search
* planner behavior
* verifier behavior
* policy checking
* rights checking
* spoiler checking
* provider behavior
* missing-scene recovery
* rights recovery
* policy recovery
* changed-contract recovery
* repair and re-verification

Expected result:

```text
31 passed
```

> **Windows/OneDrive note:** pytest may emit a `.pytest_cache` permission warning. This does not indicate a test failure.

---

# 🧠 Mock / Replay Mode

Mock mode is deterministic and requires no personal API key.

```bash
python -m src.pipeline --mode mock
```

This makes the project reproducible for evaluation.

The provider layer is separated from planning and verification logic so that an external model provider can be introduced without redesigning the entire system.

---

# 📚 Documentation

### Architecture

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for details on:

* planning
* memory/state
* multimodal grounding
* constraints
* verification
* repair
* observability
* human control
* design tradeoffs

### AI Collaboration

See [`AI_COLLABORATION.md`](AI_COLLABORATION.md) for how AI tools were used for:

* architecture
* implementation
* debugging
* test generation
* verification
* documentation

AI-generated code was treated as a draft and checked against the actual repository and executable tests.

### Known Limitations

See [`KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md) for limitations involving:

* video/audio rendering
* multimodal understanding
* semantic spoiler detection
* cultural-context interpretation
* contract ambiguity
* external model availability
* production-scale media processing

---

# 👤 Human-in-the-Loop

The system is designed to **assist rather than silently replace human decision-making**.

Human review remains appropriate for:

* final editorial approval
* ambiguous spoiler decisions
* legal interpretation
* contractual exceptions
* culturally sensitive decisions
* final marketing claims
* third-party media rights
* policy exceptions

---

# 🎬 Scope

This project focuses on **agentic decision-making and verification**, rather than building a complete production video-rendering platform.

The implementation prioritizes:

* agentic planning
* structured story representation
* constraint enforcement
* independent verification
* failure recovery
* machine-readable trailer plans
* reproducible evaluation
* observability
* human control

A production system could extend this foundation with:

* full video/audio analysis
* multimodal media models
* video rendering
* distributed processing
* richer production observability
* large-scale media pipelines

---

# 🧭 Design Philosophy

The project prioritizes:

1. **Story-grounded creative planning**
2. **Explicit constraint reasoning**
3. **Independent verification**
4. **Selective recovery**
5. **Reproducibility**
6. **Observability**
7. **Human control**

> **AI proposes; evidence, deterministic checks, tests, and human review determine what is accepted.**

---

## ⭐ Project Status

**Implementation:** Complete
**Mock Pipeline:** Passing
**Automated Tests:** 31 passing
**Recovery Tests:** Covered
**Machine-readable Outputs:** Available
**Documentation:** Complete

---

## 🔗 Repository

**GitHub:**
[https://github.com/dhruvkajla0001/autonomous-trailer-director](https://github.com/dhruvkajla0001/autonomous-trailer-director)



