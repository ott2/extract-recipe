# Security Considerations

## Threat Model

The primary use case for `extract-recipe` is preparing prompt histories for
public sharing (e.g. on GitHub).  The `--redact` flag and `--audit` feature
help with this, but have important limitations.

## Configuration File Tampering

The user config at `~/.config/extract-recipe/patterns.conf` (or a path
specified with `--config`) controls what gets redacted, stripped, skipped,
and filtered.  If a malicious script modifies this file, several attacks
are possible:

### Silently weakened redaction (high impact)

A tampered config could empty or weaken the `[redact]` section.  The user
runs `extract-recipe -r` believing their home paths and API keys are being
redacted, shares the output publicly, but sensitive content is still present.

This is the most dangerous scenario because:
- The user has an explicit expectation of protection (`--redact`)
- The output looks plausible (it's still valid markdown/JSON)
- The damage (leaked credentials, exposed filesystem paths) happens after
  sharing and may not be noticed immediately

### Content suppression

Adding `.*` to `[skip]` would silently discard all prompts.  Adding broad
`[strip]` patterns could remove content the user intended to keep.  These
are less dangerous (the user is likely to notice empty or truncated output)
but could cause confusion or data loss in the extracted recipe.

### ReDoS (denial of service)

A crafted regex like `(a+)+$` could cause catastrophic backtracking, hanging
the process.  This is a local denial of service only — the attacker already
has write access to user files and could achieve the same effect by modifying
`.bashrc` or similar.

## What is NOT a risk

- **Code execution via regex**: Python's `re` module does not support code
  execution within patterns or replacement strings (unlike Perl).  The config
  is text in, text out.
- **Path traversal**: The config file is read as plain text; no paths within
  it are interpreted as file operations.
- **Injection into output**: Replacement strings in `[redact]` support
  backreferences (`\1`, `\g<name>`) but not arbitrary code.

## Mitigations

### Current

- `--redact` help text and README explicitly state that redaction is
  "not exhaustive" and recommend manual review
- `--audit` is documented as a discovery tool for manual review, not an
  automated guarantee
- `--init-config` refuses to overwrite an existing config file

### Possible future mitigations

- **Always apply package `[redact]` defaults**: The user config could extend
  but never weaken the built-in redaction patterns.  This is the most robust
  defence against tampered configs silently disabling redaction.
- **File permission checks**: Warn if the config file is writable by users
  other than the owner (similar to how `ssh` handles `~/.ssh/config`).
- **Config integrity**: Hash the config file and warn if it has changed
  since `--init-config` was run.  This catches accidental modifications too.

## Redaction Limitations

Even with an untampered config, `--redact` only catches known patterns:

- Home directory paths (`/Users/name/`, `/home/name/`)
- API keys (AWS, GitHub, Anthropic, OpenAI, Google)
- UUIDs and session identifiers
- `/tmp` paths with username components

It does **not** automatically detect or redact:
- Personal names mentioned in prompts
- Project names and details that may be confidential
- URLs that could identify the user (ORCIDs, GitHub profiles)
- Email addresses, phone numbers, or other PII
- Domain-specific sensitive content

Users sharing recipes publicly should use `--audit` to review for proper
nouns, manually inspect the output, and consider additional tools for
thorough anonymisation.
