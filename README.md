
# Computer-Use Automation System

A focused vertical slice of a computer-use automation system that turns a natural-language goal into a reusable, deterministic automation recipe.

## What This Demonstrates

- Real LLM-driven discovery against a live synthetic web application
- Discovery recording and canonicalization into a structured recipe
- Parameterized deterministic replay without an LLM decision loop
- Typed inputs and outputs
- Explicit success checkpoints
- Business, recoverable, and hard execution outcomes
- Human-in-the-loop takeover and resume on the same live browser session
- Safety checks for allowed hosts and action types
- Redacted evidence logs
- Automated tests covering replay, failure handling, safety, and HITL

The implementation intentionally focuses on one complete workflow rather than broad application coverage.

## Workflow

```text
Natural-language goal
        |
        v
LLM-driven discovery
        |
        v
Discovery history
        |
        v
Canonicalized Recipe
        |
        v
Deterministic Replay
        |
        +---- success ----> typed output
        |
        +---- business outcome
        |
        +---- recoverable failure
        |
        +---- hard failure
        |
        +---- human takeover


Example goal:

Look up a member and return their current savings balance

Example input:

member_id = 12345

Example output:

savings_balance = 4250

Architecture

                    +----------------------+
                    |   Natural-language   |
                    |        Goal          |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |   Discovery Engine   |
                    |  Observe -> Decide   |
                    |       -> Act         |
                    +----------+-----------+
                               |
                         real LLM run
                               |
                               v
                    +----------------------+
                    | Discovery History    |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Canonicalizer        |
                    | History -> Recipe    |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Structured Recipe    |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Deterministic Replay |
                    |  no LLM decisions    |
                    +----------+-----------+
                               |
                 +-------------+-------------+
                 |             |             |
                 v             v             v
             Success     Error handling     HITL
                              |
                              v
                    structured evidence

Core boundary:

Recipe = WHAT should happen
Replay Engine = HOW the recipe is executed
Surface Adapter = HOW logical targets map to the live UI

Main Components

app/
├── artifact/
│   ├── actions.py
│   ├── factory.py
│   └── schema.py
├── discovery/
│   ├── canonicalizer.py
│   ├── engine.py
│   ├── executor.py
│   ├── observation.py
│   └── recorder.py
├── hitl/
│   └── manager.py
├── llm/
│   ├── anthropic_provider.py
│   └── provider.py
├── replay/
│   ├── engine.py
│   ├── result.py
│   ├── session.py
│   └── surface.py
├── safety/
│   └── policy.py
├── session/
│   └── manager.py
└── main.py

target-app/
└── Synthetic Northstar banking application

tests/
├── test_canonicalizer.py
├── test_hitl.py
└── test_replay.py

evidence/
├── saved_recipe.json
├── discovery.jsonl
├── replay.jsonl
└── failure-click_missing_target.png

Prerequisites

    Python 3.11+

    Node.js/npm

    A browser executable available to Playwright

    Anthropic API key for live LLM discovery

The browser executable can be configured through:

PLAYWRIGHT_EXECUTABLE_PATH

Setup

Clone the repository:

git clone git@github.com:Vatsal09-debug/computer-use-automation.git
cd computer-use-automation

Create the Python environment:

python3 -m venv .venv
source .venv/bin/activate

Install dependencies:

pip install -e ".[dev]"

Install target application dependencies:

npm install --prefix target-app

Create the environment file:

cp .env.example .env

Configure .env:

ANTHROPIC_API_KEY=<your Anthropic API key>
NORTHSTAR_URL=http://localhost:5173
PLAYWRIGHT_EXECUTABLE_PATH=

Start the Target Application

In one terminal:

npm run dev --prefix target-app

The target application normally runs at:

http://localhost:5173

If Vite selects another port, update NORTHSTAR_URL in .env.
Start the Backend

In another terminal:

source .venv/bin/activate
uvicorn app.main:app --reload

API:

http://127.0.0.1:8000

Interactive API documentation:

http://127.0.0.1:8000/docs

LLM Discovery

Discovery accepts a natural-language goal and runs against the live synthetic application.

Example:

{
  "goal": "Look up a member and return their current savings balance"
}

The discovery loop:

    Observes the live UI.

    Sends the observation and task context to the LLM.

    Receives a structured action decision.

    Executes the action.

    Records the observation, decision, and result.

    Continues until the goal is completed.

    Canonicalizes the successful history into a reusable recipe.

The discovery path uses a real Anthropic LLM provider.

Evidence:

evidence/discovery.jsonl

Recipe / Artifact

Saved artifact:

evidence/saved_recipe.json

The recipe contains:

    Schema version

    Artifact ID

    Name and version

    Goal

    Target surface

    Typed inputs

    Ordered actions

    Logical targets

    Targeting strategy

    Robustness descriptions

    Typed outputs

    Success checkpoint

The demonstrated recipe performs:

navigate_to_members
fill_member_id
search_member
wait_for_member
verify_member
extract_balance

The member ID is parameterized:

{{member_id}}

Deterministic Replay

Replay consumes:

Recipe + typed inputs

and does not use the LLM to make runtime decisions.

Replay:

    Validates inputs.

    Checks the safety policy.

    Resolves parameterized values.

    Executes ordered actions.

    Verifies checkpoints.

    Extracts typed outputs.

    Returns a structured result.

Example:

member_id = 12345

Result:

status = success
savings_balance = 4250

Error Handling

The replay engine distinguishes different outcomes.
Business Outcome

A nonexistent member such as:

member_id = 99999

produces a structured business outcome rather than a generic execution failure.
Recoverable Condition

A bounded wait timeout is classified as recoverable when the expected UI state is not established within the configured wait.
Hard Failure

Unexpected execution errors are classified as hard failures and include:

    Step ID

    Expected action

    Observed exception

    Captured evidence when available

Replay results use structured status and failure information rather than returning only FAIL.
Human-in-the-Loop

The system supports a handoff from automation to a human on the same live browser session.

The handoff contains:

    Step ID

    Reason

    Current execution state

    Live session

The human can perform the required action, record it, and resume automation.

The HITL test verifies:

    Replay pauses before a selected action.

    A human action is recorded.

    The same browser session is retained.

    Replay resumes.

    The success checkpoint is reached.

    The human action is preserved in the session history.

Safety

Replay uses a configurable SafetyPolicy.

Current checks include:

    Allowed target host

    Allowed action types

Supported action types:

fill
click
press_key
wait
assert
extract

The policy is checked when replay starts and before each action.

The demonstration only reads synthetic member information and does not include irreversible financial actions.

Sensitive values are redacted from discovery observations and evidence where appropriate.
Evidence

The evidence directory contains:

evidence/
├── saved_recipe.json
├── discovery.jsonl
├── replay.jsonl
└── failure-click_missing_target.png

The files demonstrate:

    Saved structured artifact

    Real discovery run

    Deterministic replay

    Structured execution outcomes

    Failure evidence capture

Testing

Run:

pytest -q

The browser-backed integration tests require a browser executable available to Playwright.

Configure it with:

PLAYWRIGHT_EXECUTABLE_PATH

The target application must also be running for the browser-backed tests.

The test suite covers:

    Recipe validation

    Discovery canonicalization

    Successful replay

    Business outcomes

    Recoverable wait failures

    Hard execution failures

    Safety enforcement

    Human takeover and resume

Synthetic Target Application

The included target application is a small synthetic banking-style surface called Northstar.

Workflow:

Member ID -> Search -> Member Dossier -> Savings Balance

Example synthetic records:

12345 -> John Smith -> $4,250
67890 -> Sarah Johnson -> $8,125.50

The target is intentionally local and synthetic so the complete workflow can be demonstrated without external production systems.
Generalization

The implementation demonstrates one concrete web surface.

The main generalization seams are:

Recipe
  |
  +-- logical targets
  |
  +-- action types
  |
  +-- surface adapter
  |
  +-- replay engine

The recipe does not directly depend on Playwright locator implementation.

A future surface adapter could map the same logical action model to another UI automation mechanism.

The current canonicalizer is intentionally specialized to the demonstrated member-balance workflow. Generalizing discovery canonicalization to arbitrary workflows would require a richer mapping from LLM action histories to the full artifact schema.
Deliberate Scope Cuts

The project deliberately does not attempt to implement every enterprise automation capability.

Cuts include:

    One concrete web surface

    One demonstrated workflow

    Focused action vocabulary

    test_id as the concrete targeting strategy

    Specialized canonicalization for the demonstrated goal

    No distributed execution infrastructure

    No multi-tenant control plane

    No desktop automation implementation

    No broad recovery planner

    No unrestricted LLM fallback during deterministic replay

    No persistent production database

    No production authentication/authorization layer

These cuts keep the core vertical slice real and reviewable.

The implementation prioritizes a working core over breadth.
License

This project was created as a take-home engineering exercise.



