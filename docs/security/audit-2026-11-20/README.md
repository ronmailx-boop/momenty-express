# Security audit 2026-11-20 (run 1)

Cloudflare `security-audit` skill, quick profile, source-only (no code run), on commit `fe8981e`.
Result: 0 confirmed findings, 2 needs-validation leads, 1 deferred area. Start with `REPORT.md`.

| File | What it is |
|---|---|
| `REPORT.md` | Summary: scope, posture, leads, hardening notes, coverage |
| `NEEDS-VALIDATION.md` | The two open leads with trace, blockers and validation plans |
| `FINDINGS-DETAIL.md` | Confirmed medium+ findings (none) |
| `findings.json`, `coverage-ledger.json`, `run-metadata.json`, `architecture.md` | Machine-readable run files; a later audit run reads them as prior-run input |

## Fixes applied after the audit (same day)

- Lead `tools/db_photos.py:unquoted-db-subject-in-printed-run_set-args`: `db_photos.py` now accepts only numeric
  tap coordinates in 0..1 (stops otherwise) and prints every argument with `shlex.quote`.
- Lead `operator-local-read-via-provider-result-url`: new `kie_compare.download()` accepts only https on a KIE
  result host (`aiquickdraw.com`, `redpandaai.co`, `kie.ai`; more via `KIE_EXTRA_RESULT_HOSTS`) and is used by
  `run_set.py`, `kie_compare.py`, `kie_watch.py` and `make_song.py`. A refused URL marks that clip as failed.
- Deferred area (credit cap): `run_set.py` now counts clips still running (first sends and re-sends) at their
  estimated cost plus vision credits against `--max-credits`.

Still open: the owner checks who has edit access to the test page; `kie_watch.py` re-sends still have no credit cap;
the `.gitignore` / photo-deletion hardening notes in `REPORT.md`. The leads stay `needs_validation` in
`findings.json` until a future audit run re-checks the fixed source.
