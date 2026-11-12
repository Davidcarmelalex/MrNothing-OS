# CI-004 — immutable GitHub Actions references

**Status:** Implemented on `feat/phase1-agentic-phone` on 2026-11-05; exact-head CI is the acceptance gate.

## Scope

All repository workflows now pin third-party action references to full commit SHAs resolved from the corresponding official `actions/*` Git tag refs. The action tag is retained in a YAML comment for human traceability; runtime resolution uses only the immutable SHA.

| Action | Official release tag resolved | Pinned commit |
|---|---|---|
| `actions/checkout` | `v7.0.1` | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| `actions/setup-python` | `v7.1.0` | `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0` |
| `actions/setup-java` | `v6.2.0` | `77dd5b2ce225ea11469928ac317850245a74ae78` |
| `actions/upload-artifact` | `v7.0.2` | `cf430e030ddbb5b0abf93d22962f4752f3646cd9` |
| `actions/download-artifact` | `v8.0.2` | `9000827ccba6bdab643e8b6fd33ac0654aef8333` |

The refs were read from the official repositories' Git tag-reference endpoints during this run. The workflow does not depend on a movable major-version tag after this change.

## Additional workflow hardening

- Every `actions/checkout` step sets `persist-credentials: false`; no workflow needs authenticated Git writes.
- All three workflows declare only `contents: read` repository permission.
- Runner labels are explicit `ubuntu-24.04`, not the moving `ubuntu-latest` alias.
- A standard-library unittest guard rejects mutable action tags, unknown actions, unexpected SHAs, credential persistence, write-all permissions and mutable runner labels.

## Acceptance and limitations

The exact-head Phase 1, CI-003 and emulator workflows must pass after this commit. The action pinning test is part of the Python policy suite.

Full-SHA action references prevent an upstream tag move from silently changing the referenced action commit. They do not eliminate vulnerabilities in the pinned action or its transitive dependencies; updates still require review and an intentional SHA change. The `ubuntu-24.04` label is an explicit OS-family/version label, not an immutable runner-image digest. GitHub-hosted runner images can still receive patch updates.

This change does not grant workflow write permissions, create credentials, sign artifacts or deploy software. The CI-003 APK remains unsigned and `release_ready=false`. Independent supervisor review remains a separate gate.
