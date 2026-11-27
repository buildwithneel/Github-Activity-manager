# Security & Privacy

- **Credential Storage**: Uses OS Keyring when available, with a `0600` encrypted local fallback (`.credentials`). Tokens are never written to `config.json` or `app.log`.
- **Log Redaction**: `TokenRedactingFilter` automatically redacts GitHub tokens and `Bearer` headers from log output.
- **SSL/TLS**: Certificate verification is always enabled.
- **Git Safety**: Never force-pushes, never rewrites history, refuses to commit unrelated staged files, and warns on uncommitted changes.
