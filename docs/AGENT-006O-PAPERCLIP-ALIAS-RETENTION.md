# AGENT-006O — PaperClip mutable history alias cleanup

**Scope:** legacy `agents/paperclip/agent.py`, in-memory session retention only. Authorized branch: `feat/phase1-agentic-phone`.

## Finding

Prior `clear_memory` assigned new empty lists to the session dictionary. If an in-process caller retained an alias to the original list or a conversation-entry dictionary, the old mutable containers still held the prior content after `forget`, `memory off`, or normal teardown. Similarly, the bounded-history eviction deleted old list elements without clearing the evicted dictionaries.

## Bounded mitigation

- Clear existing conversation/fact lists **in place**, and clear any plain dictionary entries before releasing the list references.
- Clear evicted conversation dictionaries before removing them from the bounded history list.
- Keep existing opt-in semantics, 100-entry cap, no disk persistence, no legacy `memory.json` access, and no Android executor integration.
- Add three offline regression tests covering aliased list/dictionary cleanup, eviction, and malformed session shape.

## Limitations and review gate

This is **best-effort mutable-reference cleanup**, not secure erasure. Immutable strings, external copies, Python allocator memory, swap, terminal output, subprocess memory and model caches can still contain text. Same-process code can hold independent string references. It does not authorize encrypted persistent memory or device integration.

Independent security review must inspect this exact source head, challenge aliasing and concurrency assumptions, and verify the tests. The upstream shared `SKILL.md` remains unverified; the local `PROJECT-ADAPTER.md` is project-specific. No milestone is independently complete.
