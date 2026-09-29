
# AI Collaboration Note

## 1. Purpose

AI coding and reasoning tools were used as development assistants during the implementation of the Autonomous Trailer Director.

The AI tools were used to accelerate:

- architecture design
- implementation of agent interfaces
- Pydantic model design
- test generation
- debugging
- validation logic
- failure-recovery design
- documentation

AI-generated code was treated as a draft and was verified against the repository, tests, and assignment requirements.

---

## 2. How AI Was Used

### Architecture

AI assistance was used to break the system into separate responsibilities:

- Story Agent
- Planner Agent
- Verifier Agent
- Repair Agent
- Constraint Repository
- deterministic validation tools
- model/provider interfaces

The architecture was then implemented and tested locally.

### Implementation

AI assistance was used for implementation patterns and code scaffolding, including:

- Python/Pydantic models
- repository loaders
- planner interfaces
- verifier structure
- repair flow
- mock provider
- CLI integration
- automated tests

Generated code was not accepted solely because an AI model suggested it.

---

## 3. Verification Process

The development workflow followed:

```text
AI suggestion
    ↓
Inspect repository structure
    ↓
Implement / modify code
    ↓
Run automated tests
    ↓
Inspect failure
    ↓
Correct implementation
    ↓
Run tests again
````

The deterministic verifier was deliberately kept independent from the creative planner.

This prevents the same model that proposes a trailer from being the sole authority that approves it.

---

## 4. Debugging Examples

Several implementation issues were discovered through local test execution.

Examples included:

* incorrect constructor arguments
* incorrect model fields
* mismatched validation interfaces
* repair-agent argument mismatches
* incorrect path handling on Windows
* schema mismatches in validation results
* revision-state handling during repair

These failures were fixed based on actual repository errors and repeated test execution rather than assuming that generated code was correct.

---

## 5. Test-Driven Verification

AI assistance was also used to create failure-recovery tests.

The test suite covers scenarios including:

* missing scene
* spoiler-protected scene
* expired music rights
* policy violation
* changed contract
* normal successful planning
* provider behavior
* scene search
* constraint loading
* story-map generation
* planner behavior
* verifier behavior

The recovery tests verify that failures can result in:

```text
Failure
   ↓
Affected segment identification
   ↓
Selective repair
   ↓
Revision increment
   ↓
Re-verification
   ↓
Accepted plan
```

---

## 6. Human Review

Human review remained responsible for:

* deciding the system architecture
* selecting the final implementation approach
* checking whether generated code matched the repository
* interpreting test failures
* deciding which failures required repair
* reviewing generated trailer plans
* reviewing safety, rights and cultural constraints
* deciding what should remain deterministic
* deciding what should remain under human editorial/legal approval

AI assistance did not replace these decisions.

---

## 7. AI Limitations Observed

AI-generated code occasionally made assumptions that did not match the actual repository.

Examples included:

* assuming constructor parameters that did not exist
* assuming fields existed on Pydantic models
* assuming a validation object had a particular schema
* proposing duplicate tests for functionality that was already covered

These were detected through repository inspection and test execution.

This reinforced the development rule:

> Generated code must be checked against the actual implementation and executed tests before being considered correct.

---

## 8. Use of Mock Mode

A deterministic mock provider was retained so the project can be evaluated without requiring a personal model API key.

This also makes the main workflow reproducible.

The mock path is used for:

* local development
* automated testing
* evaluator replay
* deterministic demonstrations

External model providers are treated as replaceable components rather than mandatory dependencies.

---

## 9. Engineering Principle

The central principle followed during development was:

```text
Use AI for reasoning assistance and implementation acceleration,
but use executable code, deterministic checks, tests,
and human review as the final source of truth.
```

The goal was therefore not to build a system that blindly follows model output.

The goal was to build an agentic workflow where AI-assisted planning is combined with explicit grounding, constraints, verification, recovery, and human control.




