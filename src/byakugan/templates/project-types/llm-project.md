# LLM Application Project — Working Standards

## What This Project Type Demands
LLM applications are non-deterministic systems built on top of probabilistic models. They hallucinate, misunderstand, and produce plausible-sounding wrong answers. Every design decision must account for this. Validate outputs. Version prompts. Build evaluation infrastructure before building features. Never let an LLM take an irreversible action without a human checkpoint.

## Before Starting Any Feature
- Define what the feature must do and what it must never do. Both sides of this contract matter.
- Define how you will evaluate quality before building. If you cannot measure it, you cannot improve it.
- Identify the failure modes: hallucination, off-topic responses, prompt injection, PII leakage, excessive cost.
- Select the model based on the task requirements (capability, latency, cost, data privacy). Document the choice.
- Identify what human oversight exists. If the LLM output drives an irreversible action, require explicit human confirmation.

## Architecture Standards
- Prompts are versioned artifacts. They live in template files under version control, not inline in code.
- Every LLM call is logged: model, prompt (or hash), response, latency, token counts, cost estimate.
- System boundaries use structured output / tool use / function calling for any LLM output that will be parsed programmatically. Never regex-parse free text in production.
- Input validation and output validation are separate, explicit pipeline stages — not implicit assumptions.
- All LLM integrations are behind an abstraction layer that allows swapping models without changing business logic.

## How to Approach Any Task
1. Write example prompts and test them manually against representative inputs before writing any code.
2. Build the evaluation dataset alongside the feature. At least 20–50 input/expected-output pairs.
3. Implement the feature. Keep the LLM call isolated — one function, one responsibility.
4. Run the evaluation dataset against the implementation. Document the results.
5. Implement output validation (format check, safety check, content check) before the output reaches any downstream system.

## Non-Negotiable Rules
- Prompts are not hardcoded strings in business logic. They are versioned template files.
- Every LLM output that will be used programmatically must use structured output or tool calling. No free-text parsing in production.
- Validate all LLM outputs before use: format validation, safety check, range/type checks on extracted data.
- Never embed user-provided content in a system prompt without sanitizing for prompt injection.
- Never send PII to a third-party LLM API without explicit data processing agreement coverage and user consent.
- Set `max_tokens` on every LLM call. Unbounded token generation is an uncontrolled cost and latency risk.
- Implement retry with exponential backoff for transient API failures. Do not retry on non-retryable errors.
- LLM outputs must never be executed as code without a sandboxed environment and explicit user authorization.

## Evaluation Standards
- Build an evaluation dataset before launch. Add to it continuously from real failures.
- Run evals on every prompt change — before and after. Regressions happen silently.
- Use LLM-as-judge with a rubric for subjective quality metrics. Document the rubric.
- Track: faithfulness (no hallucination), relevance, format compliance, safety.
- Establish a latency budget. Measure p50/p95 LLM call latency in development.

## Observability Standards
- Log every LLM call with: model, prompt hash or template name, response hash, latency, input tokens, output tokens.
- Track cost per request, per user, per day. Alert on anomalies.
- Collect user feedback (thumbs up/down, corrections) and feed it into the evaluation dataset.
- Alert on: error rate spikes, latency degradation, cost anomalies, safety filter triggers.

## Definition of Done
- [ ] Prompts are in versioned template files under version control.
- [ ] Evaluation dataset exists with ≥ 20 input/expected-output pairs.
- [ ] Evaluation run documented showing quality metrics.
- [ ] Structured output / tool calling used for all programmatically consumed LLM output.
- [ ] Output validation implemented (format, safety, content).
- [ ] `max_tokens` set on all LLM calls.
- [ ] Retry with backoff implemented for transient failures.
- [ ] Logging in place: model, template, latency, token counts per call.
- [ ] No user PII sent to third-party API without legal coverage.
- [ ] Prompt injection risk assessed and mitigated for user-provided content in prompts.
