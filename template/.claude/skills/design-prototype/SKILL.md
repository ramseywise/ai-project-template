---
name: design-prototype
description: "Designer role — spike/explore before committing. Use when the question is feasibility, not implementation: 'does this work?'. Fast validation mode: state the question, write minimum code, observe, decide (adopt/adapt/discard). Triggers on: 'prototype this', 'spike on X', 'try this approach', 'explore this API', 'validate this idea', 'feasibility check'."
disable-model-invocation: true
allowed-tools: Read Bash Grep Glob Write WebSearch WebFetch
---

Prototype or explore $ARGUMENTS. Apply all rules below strictly.

## Purpose
- Goal is fast learning and validation, not production-ready code
- Answer a specific question: "Does this work?", "How does this API behave?", "Is this approach feasible?"
- State the question being answered before writing code

## Rules
- No TDD — tests are optional during prototyping
- BCE layering and strict architecture rules are relaxed
- Shortcuts are allowed (hardcoded values, minimal error handling, skipped validation)
- Do not refactor or clean up existing production code as part of prototyping
- Keep prototype code clearly separated — use a `prototype/` directory or clearly mark files as experimental

## Workflow
1. Clarify the question or hypothesis being tested
2. Write the minimum code needed to answer it
3. Run it and observe the result
4. Document findings: what worked, what didn't, what was surprising
5. Decide together with the user: adopt (rewrite properly), adapt (refactor into production), or discard

## Output
- After prototyping, summarize findings as a comment in ROADMAP.md or as an ADR if the finding influences architecture
- If the prototype code is to be adopted, switch back to the `/backend` or `/frontend` skill and rewrite with full rules (TDD, BCE, validation, etc.)
- Never merge prototype code directly into production paths
