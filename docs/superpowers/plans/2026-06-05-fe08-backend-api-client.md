# FE-08 Backend API Client (HTTP + SSE) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the stub `streamMessage` with a real client that POSTs a question to the backend `/chat` endpoint, attaches the Entra Bearer token from FE-07, consumes the SSE stream, and surfaces auth vs. generic errors to the UI.

**Architecture:** `streamMessage` becomes a pure async generator whose only new dependency is an injected `getToken` callback; it builds the request, parses SSE defensively, yields raw tokens, and throws a typed `ApiError`. `useChat` calls `useToken()` and threads `getToken` in via a ref, then maps a thrown `ApiError` to the right message. A `config.ts` helper centralises the base URL.

**Tech Stack:** TypeScript (strict), Next.js App Router, `fetch` + `ReadableStream` (not `EventSource`), `@azure/msal-react` (via FE-07 `useToken`), Jest + Testing Library.

**Spec:** `docs/superpowers/specs/2026-06-05-fe08-backend-api-client-design.md`

**Working directory:** all paths below are relative to `apps/frontend/`. Run all `npx jest` / `npx tsc` commands from `apps/frontend/`.

---

### Task 1: Create the feature branch

**Files:** none (git only)

- [ ] **Step 1: Create and check out the branch**

Run from the repo root:
```bash
git checkout -b feature/FE-08-backend-api-client
```
Expected: `Switched to a new branch 'feature/FE-08-backend-api-client'`

> Note: this branches from the current FE-07 branch HEAD, which is correct — FE-08 builds on FE-07's `useToken`. The FE-08 spec commit already lives here.

---

### Task 2: `ApiError` typed error

**Files:**
- Create: `src/features/chat/api/apiError.ts`
- Test: `src/__tests__/apiError.test.ts`

- [ ] **Step 1: Write the failing test**

Create `src/__tests__/apiError.test.ts`:
```ts
import { ApiError } from '@/features/chat/api/apiError'

describe('ApiError', () => {
  it('is an Error with a kind and message', () => {
    const err = new ApiError('auth', 'Unauthorized')
    expect(err).toBeInstanceOf(Error)
    expect(err.name).toBe('ApiError')
    expect(err.kind).toBe('auth')
    expect(err.message).toBe('Unauthorized')
  })

  it('supports server and network kinds', () => {
    expect(new ApiError('server', 'boom').kind).toBe('server')
    expect(new ApiError('network', 'down').kind).toBe('network')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx jest apiError --no-coverage`
Expected: FAIL — `Cannot find module '@/features/chat/api/apiError'`

- [ ] **Step 3: Write the implementation**

Create `src/features/chat/api/apiError.ts`:
```ts
export type ApiErrorKind = 'auth' | 'server' | 'network'

export class ApiError extends Error {
  constructor(
    public readonly kind: ApiErrorKind,
    message: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx jest apiError --no-coverage`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add src/features/chat/api/apiError.ts src/__tests__/apiError.test.ts
git commit -m "feat(frontend): add ApiError typed error for API client (FE-08)"
```

---

### Task 3: API base URL config helper

**Files:**
- Create: `src/features/chat/config.ts`
- Test: `src/__tests__/config.test.ts`

- [ ] **Step 1: Write the failing test**

Create `src/__tests__/config.test.ts`:
```ts
describe('getApiUrl', () => {
  const original = process.env.NEXT_PUBLIC_API_URL

  afterEach(() => {
    process.env.NEXT_PUBLIC_API_URL = original
    jest.resetModules()
  })

  it('returns NEXT_PUBLIC_API_URL when set', async () => {
    process.env.NEXT_PUBLIC_API_URL = 'https://api.example.com'
    jest.resetModules()
    const { getApiUrl } = await import('@/features/chat/config')
    expect(getApiUrl()).toBe('https://api.example.com')
  })

  it('defaults to http://localhost:8000 when unset', async () => {
    delete process.env.NEXT_PUBLIC_API_URL
    jest.resetModules()
    const { getApiUrl } = await import('@/features/chat/config')
    expect(getApiUrl()).toBe('http://localhost:8000')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx jest config.test --no-coverage`
Expected: FAIL — `Cannot find module '@/features/chat/config'`

- [ ] **Step 3: Write the implementation**

Create `src/features/chat/config.ts`:
```ts
export function getApiUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx jest config.test --no-coverage`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add src/features/chat/config.ts src/__tests__/config.test.ts
git commit -m "feat(frontend): add getApiUrl config helper (FE-08)"
```

---

### Task 4: Real `streamMessage` (fetch + SSE parse)

**Files:**
- Modify: `src/features/chat/api/streamMessage.ts` (full replacement of the stub)
- Test: `src/__tests__/streamMessage.test.ts` (full replacement of the stub tests)

- [ ] **Step 1: Replace the test file with failing tests for the real implementation**

Overwrite `src/__tests__/streamMessage.test.ts` with:
```ts
import { streamMessage } from '@/features/chat/api/streamMessage'
import { ApiError } from '@/features/chat/api/apiError'

const getToken = async () => 'fake-token'

// Builds a fake Response whose body.getReader() yields the given SSE chunks.
function mockResponse(
  chunks: string[],
  { ok = true, status = 200 }: { ok?: boolean; status?: number } = {}
): Response {
  const encoder = new TextEncoder()
  let i = 0
  const body = {
    getReader() {
      return {
        read: async () => {
          if (i < chunks.length) {
            return { done: false, value: encoder.encode(chunks[i++]) }
          }
          return { done: true, value: undefined }
        },
        cancel: async () => {},
        releaseLock: () => {},
      }
    },
  }
  return { ok, status, body } as unknown as Response
}

async function collect(gen: AsyncGenerator<string>): Promise<string[]> {
  const out: string[] = []
  for await (const t of gen) out.push(t)
  return out
}

afterEach(() => { jest.restoreAllMocks() })

describe('streamMessage', () => {
  it('yields tokens in order and stops on [DONE]', async () => {
    global.fetch = jest.fn().mockResolvedValue(
      mockResponse(['data: Hello\n\n', 'data: world\n\n', 'data: [DONE]\n\n', 'data: ignored\n\n'])
    )
    const tokens = await collect(
      streamMessage('q', 'sess', new AbortController().signal, getToken)
    )
    expect(tokens).toEqual(['Hello', 'world'])
  })

  it('attaches the Bearer token, URL and JSON body', async () => {
    const fetchMock = jest.fn().mockResolvedValue(mockResponse(['data: [DONE]\n\n']))
    global.fetch = fetchMock
    await collect(streamMessage('my question', 'sess-1', new AbortController().signal, getToken))

    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('http://localhost:8000/chat')
    expect(init.method).toBe('POST')
    expect(init.headers['Authorization']).toBe('Bearer fake-token')
    expect(init.headers['Content-Type']).toBe('application/json')
    expect(JSON.parse(init.body)).toEqual({ question: 'my question', session_id: 'sess-1' })
  })

  it('preserves a token that has its own leading space', async () => {
    global.fetch = jest.fn().mockResolvedValue(
      mockResponse(['data:  world\n\n', 'data: [DONE]\n\n'])
    )
    const tokens = await collect(
      streamMessage('q', 'sess', new AbortController().signal, getToken)
    )
    expect(tokens).toEqual([' world'])
  })

  it('throws ApiError(server) on the [ERROR] sentinel', async () => {
    global.fetch = jest.fn().mockResolvedValue(
      mockResponse(['data: partial\n\n', 'data: [ERROR] boom\n\n'])
    )
    await expect(
      collect(streamMessage('q', 'sess', new AbortController().signal, getToken))
    ).rejects.toMatchObject({ name: 'ApiError', kind: 'server' })
  })

  it('throws ApiError(auth) on HTTP 401', async () => {
    global.fetch = jest.fn().mockResolvedValue(mockResponse([], { ok: false, status: 401 }))
    await expect(
      collect(streamMessage('q', 'sess', new AbortController().signal, getToken))
    ).rejects.toMatchObject({ name: 'ApiError', kind: 'auth' })
  })

  it('throws ApiError(server) on other non-2xx', async () => {
    global.fetch = jest.fn().mockResolvedValue(mockResponse([], { ok: false, status: 500 }))
    await expect(
      collect(streamMessage('q', 'sess', new AbortController().signal, getToken))
    ).rejects.toMatchObject({ name: 'ApiError', kind: 'server' })
  })

  it('throws ApiError(network) when fetch rejects with a non-abort error', async () => {
    global.fetch = jest.fn().mockRejectedValue(new TypeError('Failed to fetch'))
    await expect(
      collect(streamMessage('q', 'sess', new AbortController().signal, getToken))
    ).rejects.toMatchObject({ name: 'ApiError', kind: 'network' })
  })

  it('propagates AbortError (not ApiError) when fetch is aborted', async () => {
    global.fetch = jest.fn().mockRejectedValue(new DOMException('Aborted', 'AbortError'))
    let caught: Error | null = null
    try {
      await collect(streamMessage('q', 'sess', new AbortController().signal, getToken))
    } catch (e) {
      caught = e as Error
    }
    expect(caught).not.toBeNull()
    expect(caught!.name).toBe('AbortError')
    expect(caught).not.toBeInstanceOf(ApiError)
  })

  it('defensively ignores non-data lines within an event', async () => {
    global.fetch = jest.fn().mockResolvedValue(
      mockResponse(['event: message\ndata: Hi\n\n', 'data: [DONE]\n\n'])
    )
    const tokens = await collect(
      streamMessage('q', 'sess', new AbortController().signal, getToken)
    )
    expect(tokens).toEqual(['Hi'])
  })
})
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `npx jest streamMessage --no-coverage`
Expected: FAIL — the stub yields stub text / wrong signature; assertions like `toEqual(['Hello', 'world'])` and `kind: 'auth'` fail, and `ApiError` import resolves (Task 2) but the stub never throws it.

- [ ] **Step 3: Replace the stub with the real implementation**

Overwrite `src/features/chat/api/streamMessage.ts` with:
```ts
import { ApiError } from './apiError'
import { getApiUrl } from '@/features/chat/config'

export async function* streamMessage(
  text: string,
  sessionId: string,
  signal: AbortSignal,
  getToken: () => Promise<string>
): AsyncGenerator<string> {
  const token = await getToken()

  let response: Response
  try {
    response = await fetch(`${getApiUrl()}/chat`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      },
      body: JSON.stringify({ question: text, session_id: sessionId }),
      signal,
    })
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') throw err
    throw new ApiError('network', 'Network request failed')
  }

  if (!response.ok) {
    if (response.status === 401) throw new ApiError('auth', 'Unauthorized')
    throw new ApiError('server', `Request failed with status ${response.status}`)
  }
  if (!response.body) {
    throw new ApiError('server', 'Empty response body')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      let delimiter: number
      while ((delimiter = buffer.indexOf('\n\n')) !== -1) {
        const rawEvent = buffer.slice(0, delimiter)
        buffer = buffer.slice(delimiter + 2)

        for (const line of rawEvent.split('\n')) {
          if (!line.startsWith('data:')) continue
          // Strip 'data:' and a single SSE delimiter space, preserving the token's own spaces.
          const payload = line.slice(5).replace(/^ /, '')
          if (payload === '[DONE]') return
          if (payload.startsWith('[ERROR]')) throw new ApiError('server', payload)
          yield payload
        }
      }
    }
  } finally {
    reader.cancel().catch(() => {})
  }
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `npx jest streamMessage --no-coverage`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add src/features/chat/api/streamMessage.ts src/__tests__/streamMessage.test.ts
git commit -m "feat(frontend): replace stub streamMessage with real fetch+SSE client (FE-08)"
```

---

### Task 5: Wire `useToken` into `useChat` and map errors

**Files:**
- Modify: `src/features/chat/hooks/useChat.ts`
- Test: `src/__tests__/useChat.test.ts`

- [ ] **Step 1: Add the `useToken` mock and the new failing tests**

Edit `src/__tests__/useChat.test.ts`. Add these imports near the top (after the existing imports on lines 1-3):
```ts
import { ApiError } from '@/features/chat/api/apiError'
```

Add this mock immediately after the existing `jest.mock('@/features/chat/api/streamMessage')` block (after line 6):
```ts
const mockGetToken = jest.fn().mockResolvedValue('fake-token')
jest.mock('@/features/auth/hooks/useToken', () => ({
  useToken: () => ({ getToken: mockGetToken }),
}))
```

Add these three tests inside the `describe('useChat', ...)` block (before its closing `})`):
```ts
  it('shows the session-expired message on an auth ApiError', async () => {
    mockStreamMessage.mockImplementation(async function* () {
      throw new ApiError('auth', 'Unauthorized')
    })
    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('test')
    })

    expect(result.current.streamError).toBe('Session expired — please sign in again')
    expect(result.current.isStreaming).toBe(false)
  })

  it('shows the generic message on a server ApiError', async () => {
    mockStreamMessage.mockImplementation(async function* () {
      throw new ApiError('server', 'boom')
    })
    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('test')
    })

    expect(result.current.streamError).toBe('Something went wrong — please try again')
  })

  it('passes a getToken function as the fourth argument to streamMessage', async () => {
    mockStreamMessage.mockImplementation(() => makeTokenStream(['ok']))
    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('test')
    })

    expect(typeof mockStreamMessage.mock.calls[0][3]).toBe('function')
  })
```

- [ ] **Step 2: Run the tests to verify the new ones fail**

Run: `npx jest useChat --no-coverage`
Expected: FAIL — the auth test gets "Something went wrong — please try again" (no auth mapping yet); the 4th-argument test gets `undefined` (streamMessage called with 3 args).

- [ ] **Step 3: Update `useChat` to inject `getToken` and map `ApiError`**

Edit `src/features/chat/hooks/useChat.ts`.

Add imports after the existing import block (after line 5):
```ts
import { useToken } from '@/features/auth/hooks/useToken'
import { ApiError } from '@/features/chat/api/apiError'
```

Inside `useChat`, after the `sessionIdRef` line (line 13), add the token ref:
```ts
  const { getToken } = useToken()
  const getTokenRef = useRef(getToken)
  getTokenRef.current = getToken
```

Change the `streamMessage` call (line 29) to pass the token getter:
```ts
      for await (const token of streamMessage(text, sessionIdRef.current, controller.signal, getTokenRef.current)) {
```

Replace the `else` branch of the catch block (lines 41-46) with kind-aware mapping:
```ts
      } else {
        if (accumulated) {
          setMessages(prev => [...prev, { role: 'assistant', text: accumulated }])
        }
        if (err instanceof ApiError && err.kind === 'auth') {
          setStreamError('Session expired — please sign in again')
        } else {
          setStreamError('Something went wrong — please try again')
        }
      }
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `npx jest useChat --no-coverage`
Expected: PASS (all existing tests plus the 3 new ones)

- [ ] **Step 5: Commit**

```bash
git add src/features/chat/hooks/useChat.ts src/__tests__/useChat.test.ts
git commit -m "feat(frontend): wire useToken into useChat and map ApiError kinds (FE-08)"
```

---

### Task 6: Keep `page.test.tsx` green (defensive msal mock)

**Files:**
- Modify: `src/__tests__/page.test.tsx`

- [ ] **Step 1: Run the full suite to confirm current state**

Run: `npx jest --no-coverage`
Expected: PASS overall. (`page.test.tsx` should already pass: it mocks `streamMessage`, so `getToken` is never invoked. This task hardens the mock so a future page test that triggers a real `getToken` won't crash on `accounts[0]`.)

- [ ] **Step 2: Add `accounts: []` to the page test's msal mock**

Edit `src/__tests__/page.test.tsx`. Change the `useMsal` mock (line 13) to include `accounts`:
```ts
  useMsal: jest.fn().mockReturnValue({ instance: { loginPopup: jest.fn() }, accounts: [] }),
```

- [ ] **Step 3: Run the full suite again**

Run: `npx jest --no-coverage`
Expected: PASS — all suites green.

- [ ] **Step 4: Type-check the project**

Run: `npx tsc --noEmit`
Expected: no output (clean).

- [ ] **Step 5: Commit**

```bash
git add src/__tests__/page.test.tsx
git commit -m "test(frontend): harden page test msal mock with accounts array (FE-08)"
```

---

### Task 7: Manual integration verification

**Files:** none (manual verification, no commit unless a fix is needed)

This task confirms the real end-to-end path. It requires the backend running and a real Entra login. It is verification, not an automated test.

- [ ] **Step 1: Confirm env config**

Confirm `apps/frontend/.env.local` contains:
```
NEXT_PUBLIC_ENTRA_CLIENT_ID=<frontend app client id>
NEXT_PUBLIC_ENTRA_TENANT_ID=<tenant id>
NEXT_PUBLIC_ENTRA_API_SCOPE=api://<api app client id>/access_as_user
NEXT_PUBLIC_API_URL=http://localhost:8000
```

- [ ] **Step 2: Start the backend** (in a separate terminal, from repo root)

```bash
cd apps/backend && uv run uvicorn app.main:app --app-dir src --reload
```
Expected: backend listening on `http://localhost:8000`.

- [ ] **Step 3: Start the frontend and sign in**

```bash
cd apps/frontend && npm run dev
```
Sign in with Microsoft, then ask a question (e.g., "How many items are in the list?").
Expected: tokens stream into the assistant bubble and render as markdown; no console errors.

- [ ] **Step 4: Verify error path**

Stop the backend, then ask another question.
Expected: the streaming stops and the UI shows "Something went wrong — please try again" (network error → `ApiError('network')` → generic message).

---

### Task 8: Update Obsidian story board and daily note

**Files:** none (Obsidian vault via CLI)

- [ ] **Step 1: Mark FE-08 done in its story note**

```bash
obsidian vault="Group One RTP" property:set name="tag" value="done" file="FE-08 Backend API Client"
```

- [ ] **Step 2: Update the Frontend Story Board**

Open `Story Board - Frontend.md` and set FE-08's status to `done` (match the format used for the other completed stories).

- [ ] **Step 3: Append a daily note**

```bash
obsidian vault="Group One RTP" daily:append content="- Completed FE-08 Backend API Client — replaced stub streamMessage with real fetch+SSE client, Bearer token from useToken, ApiError-based auth/generic error mapping. Note: backend SSE framing (data: {token}) can split markdown paragraph breaks; defensive frontend parse handles it, proper fix deferred to a backend story."
```

---

## Notes for the implementer

- **Do not change the backend.** The SSE framing limitation is handled defensively on the frontend and a proper fix is deferred to a backend story.
- **`streamMessage` keeps the same async-generator interface** — only a fourth `getToken` parameter is added. Consumers that mock it (`page.test.tsx`) are unaffected.
- **No `EventSource`** — POST + `Authorization` header require `fetch` + `ReadableStream`.
- **Reference for the MSAL token flow:** see project memory `reference_msal_v5_popup.md` and `src/features/auth/hooks/useToken.ts`.
