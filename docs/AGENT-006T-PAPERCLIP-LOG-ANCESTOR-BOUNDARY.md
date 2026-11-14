# AGENT-006T — PaperClip log ancestor-path boundary

## Finding
AGENT-006S checks the immediate parent of the log home, but opening that
parent with O_NOFOLLOW does not reject symlinks in earlier path components.
A group-writable ancestor could also permit an untrusted user to replace
a later path component before the immediate-parent check.

## Bounded change
Resolve the absolute parent one component at a time using O_DIRECTORY,
O_NOFOLLOW and directory-relative descriptors. Require each opened
component to be owned by root or the effective UID. Reject group/other
writable ancestors except root-owned sticky intermediate directories
(such as /tmp), and never allow a shared-writable immediate parent.
No directory permissions are modified during this traversal.

The log path remains a best-effort local prototype; no Android API,
device permission, executor, network endpoint, memory persistence,
production service or release path changes.

## Adversarial tests
- Symlink in an intermediate ancestor is rejected without creating a log.
- Group-writable non-final ancestor is rejected without creating a log.
- Existing private-path and sticky /tmp test fixtures remain supported.

## Limitations and acceptance
The path walk is not a protection against same-UID or privileged adversaries,
mount-namespace manipulation, kernel compromise or a malicious root.
Android/Termux layouts with system-managed symlink ancestors may now
fail closed; compatibility must be tested separately before release.
The independent security reviewer must assess the root-owned sticky
ancestor exception, path walk and compatibility effects. Hosted CI,
physical Pixel 9 Pro validation, spoken TalkBack and independent approval
are separate gates. Upstream shared SKILL.md remains unverified.
