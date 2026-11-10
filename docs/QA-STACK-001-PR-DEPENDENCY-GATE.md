# QA-STACK-001 — PR dependency gate

Run \`python3 scripts/pr_stack_gate.py --input open-pulls.json\` on a complete
JSON array from GitHub REST \`GET /repos/Davidcarmelalex/MrNothing-OS/pulls?state=open&per_page=100\`.
If there are more than 100 open PRs, concatenate all pages first.

This offline, read-only gate verifies that scoped PR base/head names form a
rooted, acyclic graph and reports a deterministic parent-first inventory.
It fails closed on missing parents, malformed refs, duplicate heads/numbers,
invalid SHAs and cycles. It ignores the phase-one umbrella PR targeting main.

**It cannot prove Git ancestry, successful CI, independent review, or merge
approval.** Before integration, verify actual commit ancestry and exact-head
CI, inspect diffs and require explicit human authorization for merges.
Do not automatically merge, rebase or deploy from this report.

Scope: \`feat/phase1-agentic-phone\`. No Android permissions, agent execution,
MemoryVault activation, flashing or production changes. The project-specific
\`PROJECT-ADAPTER.md\` exists; upstream shared \`SKILL.md\` remains unverified.

