# Debugging — Working Standards

## The Core Rule
Debugging is a systematic investigation. Every action is a hypothesis test. Never change code hoping it fixes a bug without first understanding why that change would fix it. Fixing the wrong thing creates the illusion of progress while the real bug remains.

Fix the root cause. Not the symptom. Not the error message.

## The Debugging Procedure

### Step 1: Reproduce It
A bug that cannot be reproduced cannot be fixed confidently. Before writing a single line of code:
- Identify the minimal input or sequence of actions that triggers the bug.
- Confirm the bug is deterministic. If it is intermittent, identify the conditions under which it occurs more reliably.
- Determine the environment: OS, version, configuration, data state.
- Write the reproduction as a failing test case if possible. This test becomes the verification that the fix works.

### Step 2: Understand the Expected vs. Actual Behavior
- State precisely: what should happen? What actually happens?
- Gather evidence: error messages, logs, stack traces, screenshots, HTTP responses. Read them fully.
- Identify where in the execution the divergence begins — not where the error is thrown, but where the data first becomes incorrect.

### Step 3: Form a Hypothesis
- Based on the evidence, propose a specific, testable explanation: "The bug occurs because X, which causes Y, resulting in Z."
- The hypothesis must be falsifiable: you must be able to define an observation that would prove it wrong.
- Hypothesize about root causes, not symptoms.

### Step 4: Test the Hypothesis
- Change exactly one thing. Changing multiple things means you cannot isolate which change mattered.
- Use logs, a debugger, or an intermediate assertion to observe whether the hypothesis holds.
- Read the actual output. Do not assume. Confirm.

### Step 5: Fix the Root Cause
- Fix the cause, not the symptom.
- Symptom fix: catching and suppressing the exception. Root cause fix: ensuring the exceptional condition cannot occur.
- Before committing, explain to yourself (or out loud) why the fix works. If you cannot explain it, you do not understand it yet.

### Step 6: Verify and Prevent Recurrence
- Confirm the failing test from Step 1 now passes.
- Add or update tests to cover this case permanently.
- Scan for the same bug pattern in adjacent code.

## Evidence Gathering Techniques

**Reading the stack trace**: the cause is usually near the bottom (oldest frame). Your code's frame is more useful than the framework's frame. Read the full trace — do not stop at the first unfamiliar line.

**Adding targeted logging**: add logs at decision points with the values that matter: inputs, intermediate results, branch taken, output. Remove them after the fix.

**Using a debugger**: set a breakpoint at or before the point of failure. Step backward through execution. Inspect actual values — do not assume them. Use conditional breakpoints for loops.

**Binary search**: if the failure location is unclear, add a checkpoint in the middle of the execution. If the state is correct there, the bug is in the second half. Repeat.

**Isolating the environment**: can you reproduce in a fresh environment? Can you reproduce with minimal data? The smallest reproducible case is the most informative.

## Debugging Specific Problem Types

**Null / undefined errors**: trace the value backward from where it was used to where it was created. At each step: can this be null? Under what conditions?

**Wrong calculation**: print both the expected and actual value at the earliest point in the computation where they diverge.

**Intermittent failure**: look for timing dependency (race condition), non-deterministic ordering, uninitialized state, or external service variability. Add timestamps to logs. Run under a race detector.

**Performance regression**: use a profiler. Identify which function consumes the most CPU or allocates the most memory. Never optimize without a profile.

**"It works on my machine"**: the environment differs. Check: OS, runtime version, dependency versions, environment variables, data state, configuration files, and any service the code calls.

## What Not to Do
- Do not change multiple things at once and see if the bug goes away.
- Do not add exception handling to silence an error without understanding its cause.
- Do not assume the most recently changed code is where the bug is — it may be triggered by the change but live elsewhere.
- Do not spend more than 30 minutes stuck before asking a colleague. Rubber duck debugging and fresh eyes are efficient.
- Do not fix a bug in a way that would break if the calling code changed — fix the component that has the incorrect assumption.
