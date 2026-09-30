# Engineering Report

## 1. Approach & Architecture

The implementation focuses on one complete vertical slice: a natural-language member lookup goal is discovered by a real LLM against a live synthetic web application, converted into a structured recipe, and then replayed deterministically without an LLM decision loop.

The main architectural boundary is:

```text
Recipe = WHAT should happen
Replay Engine = HOW the recipe is executed
Surface Adapter = HOW logical targets map to the live application

Discovery follows an observe → decide → act loop. The LLM receives the current UI observation and returns a structured action decision. Discovery history is recorded and then canonicalized into a reusable recipe.

The replay engine consumes the saved recipe plus typed inputs. It resolves parameters, checks safety policy, executes ordered actions, verifies checkpoints, extracts typed outputs, and returns a structured result.

The concrete demonstration uses a synthetic banking-style web application called Northstar. Logical targets are separated from the Playwright implementation through a surface adapter. The current concrete targeting strategy is test_id, providing stable selectors for the demonstration surface.
2. Artifact Schema & Replay Contract

The recipe is the central contract between discovery and replay.

It contains:

    Schema version

    Artifact ID

    Name and version

    Goal

    Target surface

    Typed inputs

    Ordered actions

    Logical target specifications

    Targeting strategy and robustness information

    Typed outputs

    Success checkpoint

The demonstrated recipe accepts:

member_id: string

and produces:

savings_balance: money

The member identifier is parameterized using:

{{member_id}}

The action sequence is:

navigate_to_members
fill_member_id
search_member
wait_for_member
verify_member
extract_balance

Replay intentionally does not ask the LLM what to do next. This makes the saved artifact executable, reviewable, and deterministic.

A successful replay returns the extracted typed output. A failed replay returns structured status information including the relevant step, expected condition, observed condition, and optional evidence.
3. Error Handling

Replay distinguishes between different classes of failure rather than treating every problem as a generic failure.
Business outcome

A member that does not exist is an expected application-level outcome. For example, an unknown member ID produces a business_outcome result rather than being treated as an automation crash.
Recoverable condition

A bounded synchronization failure, such as a required UI element not becoming visible within the configured wait, is represented as a recoverable condition.
Hard failure

Unexpected execution exceptions are treated as hard failures. The result contains:

    Step ID

    Expected action

    Observed exception

    Evidence path when available

The replay engine also contains a bounded synchronization check around the member-search error state. This handles the target application's short asynchronous search delay without turning the workflow into an unbounded wait.
4. HITL

Human takeover is implemented on the same live browser session used by replay.

A replay session can pause before a selected action and return a structured needs_human result containing the current step and reason for escalation.

The human can then perform an action against the same session. That action is recorded in the handoff state before replay resumes.

The HITL flow therefore preserves:

automation session
        ↓
pause / handoff
        ↓
human action
        ↓
record action
        ↓
resume same session
        ↓
continue replay

The HITL test verifies that the human action is recorded, the browser session is retained, replay resumes successfully, and the final output is still produced.
5. Safety

Safety is enforced through a configurable SafetyPolicy.

The current policy checks:

    The current target host

    The action type being executed

Allowed actions in the demonstrated system are:

fill
click
press_key
wait
assert
extract

The safety policy is checked when replay starts and again before each action.

The demonstration intentionally operates only on synthetic banking data and does not include irreversible financial operations.

Discovery evidence also applies redaction to sensitive-looking values such as email addresses, currency values, long numeric identifiers, and input values before they are written to evidence.
6. Generalization

The implementation deliberately demonstrates one concrete web surface rather than attempting to support every computer-use environment.

The primary extension points are:

logical recipe
      ↓
action model
      ↓
surface adapter
      ↓
concrete automation technology

Because recipe actions operate on logical targets, the artifact does not directly encode Playwright locator implementation details.

A future surface adapter could map the same action model to another browser automation mechanism or another supported application surface.

The current canonicalizer is intentionally specialized to the demonstrated member-balance workflow. Generalizing this component to arbitrary workflows would require a more general mapping from discovery histories into the full recipe schema.
7. Trade-offs / Deliberate Cuts

The project prioritizes a real end-to-end vertical slice over breadth.

Deliberate cuts include:

    One concrete web surface

    One demonstrated workflow

    Focused action vocabulary

    test_id as the concrete targeting strategy

    Specialized canonicalization for the demonstrated goal

    No distributed execution infrastructure

    No multi-tenant control plane

    No desktop automation implementation

    No unrestricted LLM fallback during deterministic replay

    No broad recovery planner

    No production database

    No production authentication/authorization layer

These choices keep the core artifact and replay contract small enough to inspect and reason about while still demonstrating the major runtime boundaries.
8. Testing & Evidence

The repository includes tests covering:

    Recipe validation

    Discovery canonicalization

    Successful replay

    Business outcomes

    Recoverable failures

    Hard execution failures

    Safety enforcement

    Human takeover and resume

The evidence/ directory contains the saved recipe and execution evidence, including discovery and replay logs and captured failure evidence.

The discovery evidence represents a genuine LLM-driven run against the live synthetic application. The discovery run also demonstrates recovery from an initial unsuccessful extraction attempt before reaching the final success state.

The saved recipe is then used independently by deterministic replay.

This separation provides evidence for both sides of the system:

LLM discovery → reusable artifact

reusable artifact → deterministic replay

9. Next Steps

If this were extended beyond the take-home scope, the next areas would be:

    Generalize canonicalization beyond the single demonstrated workflow.

    Add additional surface adapters and targeting strategies.

    Introduce stronger locator fallback and drift handling.

    Expand recovery policies for more transient UI conditions.

    Add artifact review, approval, and version-management workflows.

    Add broader confidence and validation mechanisms around discovered recipes.

    Add richer operational observability for long-running automation.

The current implementation intentionally stops before these areas in order to keep the demonstrated vertical slice focused, deterministic, and reviewable.
