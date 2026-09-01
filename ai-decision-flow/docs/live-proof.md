# A1 Live Execution Proof

Generated: 2026-09-02T04:02:01.4705306+05:00

This proof was produced by a real local end-to-end run through:

1. Next.js API
2. Inngest Dev Server
3. the registered `execute-decision-flow` function
4. the OpenAI SDK decision engine
5. strict YES/NO parsing
6. branch traversal
7. execution-state polling

## Verified result

- `POST /api/execute` returned HTTP `202`.
- Inngest event ID: `01M1FKADJS5AAANP3YFWGB28RK`
- Final status: `completed`
- Execution order: `proof-1 -> proof-2 -> proof-3`
- `proof-1`: `YES`
- `proof-2`: `NO`
- `proof-3`: `YES`
- YES traversal verified: `proof-1 -> proof-2`
- NO traversal verified: `proof-2 -> proof-3`
- Terminal node: `proof-3`
- Model(s): openai/gpt-oss-120b

No API key or environment secret is included in this evidence.