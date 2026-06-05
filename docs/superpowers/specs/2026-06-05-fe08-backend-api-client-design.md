# FE-08 — Backend API Client (HTTP + SSE): Design Spec

**Date:** 2026-06-05
**Story:** FE-08 Backend API Client (HTTP + SSE)
**Status:** Approved

---

## Overview

Replace the stub `streamMessage` with a real client that POSTs a question to the backend conversation endpoint and consumes its SSE stream, attaching the Entra access token from FE-07 as a Bearer header. Errors and non-200 responses are surfaced to the UI, differentiating auth failures from everything else.

The frontend remains a pure client of the FastAPI endpoint — no direct Graph or Azure OpenAI calls (NFR-1, NFR-2).

---

## Architecture & File Structure

No new vertical slice. Work lives in the existing `features/chat/api` plus a small shared error type and a config helper.

```
features/chat/
  api/
    streamMessage.ts        — MODIFY: real fetch + SSE parse; new signature (text, sessionId, signal, getToken)
    apiError.ts             — NEW: ApiError class { kind: 'auth' | 'server' | 'network' }
  hooks/
    useChat.ts              — MODIFY: call useToken(), pass getToken into streamMessage; map ApiError.kind → message
  config.ts                 — NEW: API base URL resolver (reads NEXT_PUBLIC_API_URL, defaults http://localhost:8000)

__tests__/
  streamMessage.test.ts     — NEW: parse tokens, [DONE], [ERROR], 401, non-2xx, network fail, stray line, abort
  useChat.test.tsx          — EXTEND: auth vs generic error mapping, getToken passthrough
```

**Responsibility split:**
- `streamMessage` — a pure async generator. Its only new dependency is the injected `getToken: () => Promise<string>`. Owns: building the request, attaching the Bearer header, parsing SSE, yielding tokens, throwing a typed `ApiError`.
- `useChat` — owns calling `useToken()`, threading `getToken` in, and translating a thrown `ApiError` into the right user-facing message.
- `config.ts` — centralises the base URL so it is not duplicated.

---

## Token Threading

`useChat` calls `useToken()` (safe — the chat UI only renders inside the authenticated `AuthGate`) and passes `getToken` as the fourth argument to `streamMessage`. `streamMessage` awaits `getToken()` immediately before the fetch.

Rationale:
- Token is fetched fresh per send, so MSAL silent renewal / expiry is handled per request.
- `streamMessage` stays a plain function — tests inject a fake `getToken`, no MSAL mocking required.
- Preserves the existing async-generator interface (the FE-04 plan anticipated swapping the stub "via the same interface").

`getToken()` reads from the MSAL cache; for a valid token (Entra access tokens last ~60–90 min) it returns with no network call, so this adds negligible latency over resolving the token elsewhere.

---

## Data Flow & SSE Parsing

### Request

`streamMessage` awaits `getToken()`, then issues:

```
POST {API_URL}/chat
Headers:
  Authorization: Bearer <token>
  Content-Type: application/json
  Accept: text/event-stream
Body: { question: text, session_id: sessionId }
Signal: <AbortSignal>          // passed straight to fetch for stop-button support
```

`API_URL` comes from `config.ts` (`NEXT_PUBLIC_API_URL`, default `http://localhost:8000`).

### Reading the stream

`EventSource` cannot do POST or custom headers, so we use `fetch` + `response.body.getReader()`:

1. If `!response.ok` → throw `ApiError` (`kind: 'auth'` for 401, else `'server'`).
2. Read chunks; decode with a streaming `TextDecoder` (`{ stream: true }`); append to a string buffer.
3. Split the buffer on `\n\n` (SSE event delimiter); keep the trailing partial segment in the buffer for the next read.
4. For each complete event — **defensive parse**: take the lines beginning with `data:`, strip the `data:` prefix (and a single leading space if present), and use them. Non-`data:` lines (which can appear when a markdown paragraph break splits a token across the backend's framing) are ignored.
5. Sentinel handling on each `data:` payload:
   - `[DONE]` → stop and return cleanly.
   - `[ERROR]` (payload starts with `[ERROR]`) → throw `ApiError('server', ...)`.
   - otherwise → `yield` the raw payload unchanged (no added spaces; `useChat` concatenates as-is).

### Abort

`fetch` rejects with `AbortError` when the signal fires; `streamMessage` lets it propagate. `useChat`'s existing catch treats `AbortError` as a normal stop — keeps partial text, shows no error banner. Unchanged.

### Defensive-parse caveat

If a streamed token legitimately contains `\n\n`, the backend's `data: {token}\n\n` framing splits it across events. We reassemble by yielding consecutive `data:` payloads in order, so rendered text stays correct even though event boundaries are imperfect. The proper fix (multi-line `data:` framing or JSON-encoding tokens) is a backend concern noted for a future BE story; it is out of scope for FE-08.

---

## Error Handling

### `ApiError`

```ts
type ApiErrorKind = 'auth' | 'server' | 'network'

class ApiError extends Error {
  constructor(public kind: ApiErrorKind, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}
```

### Thrown by `streamMessage`

| Situation | Thrown |
|---|---|
| Response status 401 | `ApiError('auth', ...)` |
| Any other non-2xx | `ApiError('server', ...)` |
| `[ERROR]` sentinel in stream | `ApiError('server', ...)` |
| `fetch` throws, not AbortError (network down, DNS, CORS) | `ApiError('network', ...)` |
| Signal aborted | `AbortError` propagates (not an `ApiError`) |

### Mapping in `useChat` catch (extends existing logic)

- `AbortError` → keep partial text, no banner (unchanged).
- `ApiError` with `kind === 'auth'` → `setStreamError('Session expired — please sign in again')`.
- Everything else (`server`, `network`, unknown) → `setStreamError('Something went wrong — please try again')`.
- In all error cases, any `accumulated` partial text is still committed as an assistant message (unchanged behaviour).

Auth errors show the distinct message but do **not** auto-trigger a popup: `getToken()` already attempted silent→popup before the request, so a backend 401 indicates a config/clock/audience issue a further popup would not resolve. The user can send a new message (re-running `getToken`) or refresh.

---

## Testing

All tests mock the network and token — no real backend or Entra calls. TDD: failing test first, confirm red, implement, confirm green.

### `streamMessage.test.ts` (NEW)

Inject a fake `getToken: async () => 'fake-token'`; mock global `fetch` to return a `Response` whose body is a `ReadableStream` of encoded SSE text.

| Test | Setup | Assert |
|---|---|---|
| Yields tokens in order | `data: Hello\n\n` `data: world\n\n` `data: [DONE]\n\n` | yields `['Hello', 'world']` |
| Attaches Bearer token + body | capture fetch args | URL `{API_URL}/chat`; header `Authorization: Bearer fake-token`; body `{ question, session_id }` |
| Stops on `[DONE]` | `[DONE]` mid-stream | generator completes; ignores anything after |
| `[ERROR]` sentinel throws | `data: [ERROR] boom\n\n` | throws `ApiError`, `kind: 'server'` |
| 401 throws auth | fetch resolves `{ ok: false, status: 401 }` | throws `ApiError`, `kind: 'auth'` |
| Other non-2xx throws server | status 500 | throws `ApiError`, `kind: 'server'` |
| Network failure throws network | fetch rejects (non-abort) | throws `ApiError`, `kind: 'network'` |
| Defensive parse tolerates stray lines | event containing a non-`data:` line | stray line ignored; `data:` payload still yielded |
| Abort propagates | abort the signal | rejects with `AbortError` (not `ApiError`) |

### `useChat.test.tsx` (EXTEND existing)

Mock `streamMessage` and `useToken`.

| Test | Assert |
|---|---|
| Auth error → session message | `streamMessage` throws `ApiError('auth')` → `streamError` = "Session expired — please sign in again" |
| Server error → generic message | throws `ApiError('server')` → `streamError` = "Something went wrong — please try again" |
| Token passthrough | `useChat` calls `streamMessage` with the `getToken` returned by `useToken` |

Existing `useChat` and `page` tests keep passing: they mock `streamMessage`, so the added fourth argument is transparent.

---

## Constraints

- **Frontend-only** — no backend changes in this story. The SSE framing fix is deferred to a future backend story.
- **No direct Graph/Azure OpenAI calls** — the only backend is the FastAPI `/chat` endpoint (NFR-1, NFR-2).
- **Base URL from env** — `NEXT_PUBLIC_API_URL`, already present in `.env.local.example`.
- **Same async-generator interface** — `streamMessage` keeps yielding string tokens; only a `getToken` parameter is added.
- **fetch + ReadableStream**, not `EventSource` — required for POST + Authorization header.
