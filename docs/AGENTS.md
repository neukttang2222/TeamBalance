# AGENTS.md

## Source of truth
- Follow `docs/final_spec.md` as the source of truth.
- Follow `docs/ai_prompts.md` for all AI prompt and Gemini rules.
- Do not redesign the product.

## Scope rules
- Keep MVP scope minimal.
- Do not add file upload.
- Do not add link analysis.
- Do not add advanced auth or permissions.
- Do not add charts unless explicitly asked.
- Do not expand the question-answer loop beyond 1 question and 1 answer.

## Implementation order
1. Backend skeleton
2. Backend APIs
3. Gemini ai_service integration
4. Frontend Task Workspace
5. Frontend Dashboard
6. Integration test

## Coding rules
- Do not change API contracts unless explicitly asked.
- Preserve status flow and failure policy.
- Keep dependencies minimal.
- Prefer simple, runnable code over abstract architecture.
- When generating code, clearly separate created files and modified files.

## Done criteria
- Code runs locally
- Minimal setup steps are documented
- Minimal test steps are documented
- Core loop works end-to-end