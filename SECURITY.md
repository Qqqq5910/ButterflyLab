# Security

This is a local research application without authentication. Bind to loopback;
do not expose the backend or development server publicly.

Only backend process environment may contain API keys. Do not use `VITE_*`
variables for secrets. `.env.example` is a template, not an automatic loader.
Never commit account files, databases, experiment logs or unreviewed exports.
Run `python -m backend.release_scan` and review the generated allowlist before
sharing files. An allowlist scan is not a Git history audit.

Real calls need both explicit UI consent and server enabling, verified
account-effective CNY rates and a valid HTTPS route. All reservations are durable;
125 requests and CNY 10 are software limits, not a provider-enforced invoice cap.
Set a provider-side spending cap yourself when available. No automatic retries.
Cancellation stops new requests; an already in-flight request may run until its
30-second timeout. Recorded Replay makes no external calls.

If a key is exposed, revoke it at the provider and audit every published file,
artifact and Git revision; removing the latest copy is insufficient. Report
vulnerabilities privately to the repository owner rather than posting secrets.
