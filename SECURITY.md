# Security policy

If you discover a security issue (e.g., account takeover, remote code execution, data leakage):
- Please do **not** open a public issue with exploit details.
- Instead, open a draft PR with a minimal reproducer **redacted**, or contact the maintainers
  through a private channel you agree on (e.g., email).

Because this is an early-stage scaffold, the biggest risks are typically:
- WebSocket auth/session handling
- random number generation for dice
- persistence of game logs and private data

We’ll add a formal disclosure process once the project has real users.
