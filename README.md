# Task API ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â PostgreSQL + Supabase Auth

FastAPI backend with PostgreSQL task CRUD plus Supabase authentication. The auth layer supports sign up, login, logout, JWT verification, reusable protected routes, and Swagger bearer authorization.

## Environment
Copy `.env.example` to `.env`, keep the PostgreSQL values, and set your own `SUPABASE_URL` and public anon `SUPABASE_KEY`. Never use the `service_role` key. `.env` is git-ignored. For this practice project, Supabase **Confirm email** is disabled.

## Run
```powershell
docker compose up --build
```
If Docker Compose Bake fails on Windows, run `$env:COMPOSE_BAKE="false"` first. API: `http://localhost:8000`; Swagger: `http://localhost:8000/docs`.

## Required auth API
| Method | Endpoint | Purpose | Auth | Success |
|---|---|---|---|---|
| POST | `/auth/signup` | Create user | No | 201 |
| POST | `/auth/login` | Return access + refresh tokens | No | 200 |
| POST | `/auth/logout` | End session | Bearer | 204 |
| GET | `/protected/profile` | Verified user metadata | Bearer | 200 |
| GET | `/public/info` | Public information | No | 200 |

`GET /protected/dashboard` is a second protected route using the same reusable FastAPI dependency.

## Error behavior
- Missing signup/login fields: `400` JSON error.
- Invalid login: `401 {"error":"Invalid login credentials"}`.
- Missing/malformed bearer token: `401 {"error":"Access token required"}`.
- Invalid/expired/tampered token: `401 {"error":"Invalid or expired token"}`.

## Auth flow
Supabase stores passwords and issues the JWT. Clients send `Authorization: Bearer <token>`. The dependency verifies the token using `supabase.auth.get_user(token)` before protected route logic runs.

## Swagger UI
FastAPI `HTTPBearer` adds lock icons to `/auth/logout`, `/protected/profile`, and `/protected/dashboard`. Click **Authorize**, paste the login `access_token`, and use **Try it out**.

![Swagger UI bearer authentication](screenshots/swagger-auth.png)

## Existing task routes
The existing PostgreSQL-backed `/tasks` CRUD endpoints remain unchanged in purpose and continue to use Docker Compose and the `taskdata` volume.

## Required stage commits
- Stage 0: setup server and supabase client
- Stage 1: signup and login routes working
- Stage 2: public route and unverified protected route
- Stage 3: profile route token verification
- Stage 4: auth middleware and logout endpoint
- Stage 5: Swagger UI documentation with bearer auth
- Stage 6: publish to GitHub and write README

## Final verification
Run signup ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¾Ãƒâ€šÃ‚Â¢ login ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¾Ãƒâ€šÃ‚Â¢ valid protected call ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¾Ãƒâ€šÃ‚Â¢ tampered token 401 from the terminal, then repeat the protected call through Swagger Authorize/Try it out.

## Week 5 - The polite scraper

The Week 5 assignment is in [`scraper/`](scraper/README.md).

## Week 7 ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â LLM enrichment

Week 7 adds one narrow AI workflow to this existing API: a scraped book record goes in and a schema-controlled enrichment judgement comes out. The provider is not hard-coded: LLM_BASE_URL, LLM_API_KEY, and LLM_MODEL are environment variables, so the same integration can point at another OpenAI-compatible provider without changing route code.

Stage 0 job definition is in [JOB-CARD.md](JOB-CARD.md).


### Stage 1 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â endpoint contract and stub mode

`POST /enrich` validates its input before any model call. Its response is constrained by the Pydantic schema in `src/llm/schema.py`.

For Stage 1, set:

```env
LLM_STUB=1
```

Valid request:

```bash
curl -X POST http://localhost:8000/enrich \
  -H "Content-Type: application/json" \
  -d '{"title":"A Light in the Attic","description":"A collection of poetry and drawings."}'
```

Expected Stage 1 response shape:

```json
{
  "category": "fiction",
  "summary": "A Light in the Attic is a fictional work represented by synthetic Stage 1 enrichment data.",
  "confidence": 0.95,
  "quality_flags": ["none"],
  "needs_review": false
}
```

Deliberately broken request:

```bash
curl -X POST http://localhost:8000/enrich \
  -H "Content-Type: application/json" \
  -d '{"title":"Missing description"}'
```

Expected error:

```json
{
  "error": "Invalid field: description",
  "detail": "Field required"
}
```

The broken request returns HTTP `400` before any LLM call.


### Stage 2 Ã¢â‚¬â€ prompt v1 and real model calls

The prompt is versioned at [`prompts/book-enrich-v1.md`](prompts/book-enrich-v1.md). It contains the model role, exact output shape, closed lists, rules, explicit when-unsure behavior, and three examples.

The route never concatenates scraped content into the system prompt. The book record is JSON-encoded and sent as a separate user message so untrusted scraped text remains data rather than instructions.

For the Stage 2 checkpoint, `LLM_STUB=0` makes three real OpenRouter calls. Stage 2 temporarily exposes each raw answer so it can be inspected. Stage 3 removes raw model output from the public API and replaces it with parsing, Pydantic validation, one repair retry, and quarantine behavior.

Observed during the automated Stage 2 checkpoint: the model was tested with a normal fiction-like description, an ambiguous description, and a prompt-injection attempt.


### Stage 3 â€” parse, validate, repair once, quarantine

The public `/enrich` contract is now the Pydantic `EnrichResponse` schema. Raw model text is never returned to callers.

The reliability flow is:

1. Parse one JSON object from the model answer, tolerating surrounding prose or code fences.
2. Validate every field against `EnrichResponse`, including closed enums and `extra="forbid"`.
3. If parsing or validation fails, make exactly one repair call with the broken answer and exact validation error.
4. If the repaired answer also fails, return HTTP `422`.
5. Append the rejected input, both model outputs, error, timestamp and prompt version to `logs/quarantine.jsonl`.

`logs/quarantine.jsonl` is generated runtime evidence and is git-ignored.


### Stage 4 — production safety

The LLM client has an explicit `30.0` second timeout. The OpenAI SDK's automatic retries are disabled with `max_retries=0`, so there is only one visible retry policy.

Transient failures are retried up to three times:

- timeout
- HTTP `429`
- HTTP `5xx`

Backoff is approximately `1s`, `2s`, `4s` plus random jitter. If a `429` includes `Retry-After`, that value is obeyed. HTTP `400`, `401`, and `403` fail immediately and are never retried.

Every provider attempt writes structured JSON to stdout. Every successful model call logs:

- prompt version
- model
- input tokens
- output tokens
- total tokens
- duration in milliseconds
- repair count
- retries used
- provider cost

The required `openrouter/free` router has a provider charge of `$0` for successful free-router requests, while token counts are still recorded for usage visibility.

Setting `LLM_ENABLED=false` is the kill switch. `/enrich` then returns a deterministic HTTP `503` response without contacting the model.
