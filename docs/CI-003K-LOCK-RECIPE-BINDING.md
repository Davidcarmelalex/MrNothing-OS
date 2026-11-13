# CI-003K — Offline builder lock-to-recipe declaration binding

**Status:** candidate-only, unapproved; stacked on CI-003J / PR #73. This work does not change `.github/workflows`, build or run an image, install SDK packages, sign an APK, or authorize a device operation.

## Finding and bounded correction

CI-003J verified the two offline archives against `toolchain-candidate.lock.json` but its executable CLI did not verify that the candidate Dockerfile still used the same base digests, archive checksums, or non-root runtime. The previous Dockerfile checks were test-only and used substring matching. Standard JSON parsing also silently accepted duplicate object keys.

CI-003K adds fail-closed lock parsing and a declaration-level Dockerfile binding check to the actual offline input CLI, before any archive read. It rejects duplicate lock keys (including nested archive entries), changed or additional FROM/COPY/RUN/USER/WORKDIR declarations, missing strict archive SHA-256 checks, mutable base references, extra ADD/ARG/ENTRYPOINT/CMD/ONBUILD/SHELL/VOLUME/EXPOSE instructions, and case/tab variants of these instructions. Existing candidate Dockerfile and workflow remain unchanged.

## Evidence and limitations

Focused tests cover valid lock/recipe and adversarial mutations; the full Python regression and Android source gates must pass on the exact pushed SHA. This is a **syntactic declaration guard**, not a complete Dockerfile interpreter, signed OCI attestation, immutable filesystem snapshot, independent SBOM audit, secure archive extraction proof, or assurance against malicious edits to embedded heredoc scripts. Both the lock and Dockerfile are still editable in a PR and require independent review. File-path replacement between preflight and build remains a TOCTOU risk; the build must independently verify archives and use isolated immutable inputs.

The project-specific `PROJECT-ADAPTER.md` exists. The upstream shared `SKILL.md` remains absent/unverified and was not installed. M1–M8 independent acceptance remains 0/8. CI-003 issue #66 remains open pending approved SDK 35/build-tools 35.0.0 inputs, image provenance, actual isolated builds and independent dual-builder evidence.
