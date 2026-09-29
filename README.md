````markdown
# Autonomous Trailer Director

An agentic AI system that plans, verifies, and selectively repairs audience-specific trailers from a single episode package.

The system is designed around four principles:

- Story-grounded creative planning
- Explicit policy and contract constraints
- Independent verification
- Selective repair and re-planning

It produces executable trailer plans with exact source timecodes rather than requiring final video rendering.

---

## 1. Problem

Given one episode and multiple audience definitions, the system must create distinct trailer strategies while preserving:

- story truth
- spoiler boundaries
- audience relevance
- cultural respect
- contractual rights
- policy compliance
- source accuracy
- accessibility considerations
- budget constraints

The system must also recover when a planned trailer becomes invalid.

---

## 2. System Workflow

```text
                    Episode Package
                          |
                          v
                   +--------------+
                   | Story Agent  |
                   +--------------+
                          |
                          v
              Story Map + Spoiler Map
                          |
                          v
               +---------------------+
               | Constraint Repository|
               +---------------------+
                          |
                          v
                  Constraint Map
                          |
                          v
                +----------------+
                | Planner Agent  |
                +----------------+
                          |
                          v
              Audience Trailer Plans
                          |
                          v
                +----------------+
                | Verifier Agent |
                +----------------+
                     /          \
                  PASS          FAIL
                   |              |
                   v              v
             Final Plan     +-------------+
                            | Repair Agent|
                            +-------------+
                                  |
                                  v
                         Selective Replanning
                                  |
                                  v
                              Re-verify
````

The system does not accept an LLM-generated trailer simply because it is plausible.

Plans must pass explicit validation before being accepted.

---

## 3. Repository Structure

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

## 4. Requirements

* Python 3.12+
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

## 5. Run the System

The repository includes a deterministic mock mode that does not require an API key.

```bash
python -m src.pipeline --mode mock
```

The pipeline:

1. Loads the episode package.
2. Builds the Story Map.
3. Loads contracts, policies and audience definitions.
4. Builds the Constraint Map.
5. Generates three audience-specific trailer plans.
6. Verifies every plan.
7. Repairs invalid plans when necessary.
8. Re-verifies repaired plans.
9. Writes structured artifacts and decision logs.

---

## 6. Example Output

A successful run produces output similar to:

```text
AUTONOMOUS TRAILER DIRECTOR

Validated story map: PASS
Constraint Map: PASS

Family Trailer
  Planning   : PASS
  Validation : PASS
  Segments   : 4
  Revision   : 0

Young Adult Trailer
  Planning   : PASS
  Validation : PASS
  Segments   : 4
  Revision   : 0

Dialect Region Trailer
  Planning   : PASS
  Validation : PASS
  Segments   : 4
  Revision   : 0

FINAL STATUS: PASS
```

The exact generated plans are stored in `sample_run/`.

---

## 7. Generated Artifacts

### Story Map

```text
sample_run/story_map.json
```

Contains structured story information and spoiler boundaries.

### Constraint Map

```text
sample_run/constraint_map.json
```

Contains:

* contracts
* policy rules
* audience definitions
* constraint information

### Trailer Plans

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

### Decision Log

```text
sample_run/decision_log.json
```

Provides structured information about planning, evidence, validation and repair decisions.

---

## 8. Verification

The verifier is independent from the creative planning process.

Deterministic checks cover:

* scene existence
* source timecode validity
* source evidence
* spoiler protection
* rights restrictions
* policy restrictions
* duration
* budget

Semantic verification can additionally examine:

* unsupported implications
* spoiler risk
* promise mismatch
* cultural stereotyping
* unsafe framing
* misleading audience targeting

The LLM is not treated as the authority for deterministic constraints.

---

## 9. Failure Recovery

The system supports selective repair.

When verification fails:

```text
Invalid Plan
     |
     v
Identify affected segments
     |
     v
Repair only affected segments
     |
     v
Increment revision
     |
     v
Verify repaired plan
     |
     v
Accept only after validation
```

Automated recovery coverage includes:

* missing scene
* expired music rights
* policy violation
* changed contract

Spoiler protection also has deterministic rejection coverage.

Unaffected segments are preserved during selective repair.

---

## 10. Audience Personalization

The system creates different trailer strategies for:

* Family
* Young Adult
* Dialect/Regional audience

Audience definitions influence:

* narrative promise
* emotional journey
* scene selection
* pacing
* dialogue emphasis
* audio strategy

The system does not simply select scenes based on historical engagement scores.

The trailer plans are grounded in the same episode while adapting the creative strategy to the target audience.

---

## 11. Grounding and Evidence

Important trailer decisions retain source evidence.

Example:

```text
scene:scene_02
dialogue:dialogue_02_01
contract:actor_nila
contract:track_licensed_uk_only
```

This makes important decisions traceable back to the supplied episode and constraint data.

The current implementation uses structured episode metadata as its primary grounding representation.

---

## 12. Mock Mode

Mock mode is deterministic and requires no personal API key.

```bash
python -m src.pipeline --mode mock
```

This makes the project reproducible for evaluation.

The provider layer is separated from the planning and verification logic so an external model provider can be introduced without redesigning the complete system.

---

## 13. Testing

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

The expected repository state is a fully passing test suite.

On Windows/OneDrive, pytest may emit a `.pytest_cache` permission warning. This warning does not indicate a test failure.

---

## 14. Architecture Documentation

See:

```text
ARCHITECTURE.md
```

for details on:

* planning
* memory/state
* multimodal grounding
* constraints
* verification
* repair
* observability
* human control
* design tradeoffs

---

## 15. AI Collaboration

See:

```text
AI_COLLABORATION.md
```

This documents how AI tools were used for:

* architecture
* implementation
* debugging
* test generation
* verification
* documentation

AI-generated code was treated as a draft and checked against the actual repository and executable tests.

---

## 16. Known Limitations

See:

```text
KNOWN_LIMITATIONS.md
```

Important limitations include:

* no production video rendering
* structured metadata rather than complete multimodal media understanding
* imperfect semantic spoiler detection
* limitations in cultural-context interpretation
* contract ambiguity requiring human legal review
* external model/provider availability
* production-scale media processing requirements

---

## 17. Human-in-the-Loop Decisions

The system is designed to assist rather than silently replace human decision-making.

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

## 18. Design Philosophy

The project prioritizes:

1. Story-grounded creative planning
2. Explicit constraint reasoning
3. Independent verification
4. Selective recovery
5. Reproducibility
6. Observability
7. Human control

The core principle is:

> AI proposes; evidence, deterministic checks, tests and human review determine what is accepted.

---

## 19. Scope Tradeoffs

The assignment prioritizes agent decisions and verification over a large user interface or production video-rendering stack.

The current implementation therefore focuses on:

* agentic planning
* structured story representation
* constraint enforcement
* verification
* failure recovery
* machine-readable trailer plans
* reproducible evaluation

A production system could extend this foundation with full video/audio analysis, rendering, distributed processing, richer multimodal models, and production observability.

````

### Then do the final check

Run:

```powershell
python -m pytest -q
````

Then run the actual application:

```powershell
python -m src.pipeline --mode mock
```

We want both:

```text
31 passed
```

and:

```text
FINAL STATUS: PASS
```


