# Security audit report — momenty-express (run 1)

## 1. Run scope and limits

- **Profile:** `quick` (one hunter wave, one coverage critic, one fresh verifier per candidate). **This is a partial pass, not complete coverage.**
- **Source ref:** `fe8981e15f9f1f589f925275b7e8ec1abac381c5` (clean worktree), repository `ronmailx-boop/momenty-express`.
- **Scope:** `tools/` (Python CLIs + `transition-test.html`), `docs/`, `.gitignore`, `README.md`, `PROJECT_STATE.md`, `CLAUDE.md`. Out of scope: `.claude/skills/security-audit/` (the audit skill itself) and `tools/models/yunet.onnx` (binary model weights).
- **Budget:** none set. Agents spent: 2 hunters, 1 coverage critic, 2 verifiers (5 total).
- **Execution:** sandboxed-source-and-local-only policy. No OS sandbox with read-only mounts and resource limits was established in this container, so **no target code was run**. All evidence is source-only. No provider API (KIE), claude.ai artifact or other live service was contacted.
- **Deviation from the skill workflow:** reconnaissance was done by the parent agent directly (the repository is ~1,600 source lines), not by four reconnaissance agents.
- **Prior runs:** none. This is the first ledger for this repository.
- **Deferred coverage:** 1 unit. The critic found that the paid-credit controls (`--max-credits` cap, re-send budget, `state.json` / `vision-cache.json` resume) had no dedicated business-logic unit. The quick profile allows no second wave, so it is `deferred` (`quick_profile_final_critic`).

## 2. Security posture

This is an operator-run R&D toolkit, not a deployed service. There are no committed secrets: the KIE key is injected by the network proxy and the code sends only placeholders. The claude.ai upload page renders shared data safely (text nodes only, no `innerHTML`). The two leads below are both about trusting data that crosses into the operator's machine: values from the shared artifact database, and URLs returned by the AI provider. Neither could be confirmed without facts outside the source.

## 3. Confirmed findings

None. No candidate met the `confirmed` bar (complete source trace plus a bounded local observed result).

## 4. Confirmed finding details

Not applicable.

## 5. NEEDS VALIDATION (leads, no severity)

| Lead | Trace | Exact blocker | Local next step | Owner-observed check |
|---|---|---|---|---|
| Shared-DB tap coordinates printed unquoted into the shell argument line (`tools/db_photos.py:unquoted-db-subject-in-printed-run_set-args`) | `tools/transition-test.html:177` → `tools/db_photos.py:14,28,29,32` → `PROJECT_STATE.md:327` (`run_set.py OUT <args>`) | Whether anyone besides the owner can write the artifact's database, and whether the printed line is pasted literally into the shell | Sandboxed run of `db_photos.py` on a fixture whose `subject.x` holds `;`, `#` and `--max-credits 1e9`; check the printed line (do not run it) | Check the test page's sharing settings for edit access; confirm how the printed line is used |
| Provider result URLs fetched with `urlretrieve` without a scheme/host check (`operator-local-read-via-provider-result-url`) | `tools/run_set.py:119,126,129,259` → `tools/judge.py:23,143` → `tools/auto_plan.py:33`; same sink in `kie_compare.py:132`, `kie_watch.py:43`, `make_song.py:69` | Needs a malicious, compromised or spoofed KIE response; no sandbox to run the mocked harness | Mock `kie_compare.req` to return a `file:///` result URL and check whether the file is copied and its frames uploaded | List the result hosts in past `state.json` / `task.json` files so an allowlist can be pinned |

Smallest fixes (recommended regardless of validation):
- `tools/db_photos.py`: `float()` both coordinates, require `0 <= v <= 1`, and print each argument with `shlex.quote` (or have `run_set.py` read the taps from the JSON directly).
- One shared download helper used by all four `urlretrieve` call sites that requires `urlparse(url).scheme == "https"` and a host on a pinned KIE result-host allowlist.

## 6. Hardening notes and positive patterns

Hardening (not findings):
- `tools/run_set.py:71-72`: `--max-credits` counts only finished copies. Clips in flight, re-sends and vision credits (`AP.credits`) are not counted, so a run can pass the cap by the cost of in-flight clips. `kie_watch.py` re-sends without any credit cap. (This area is the deferred unit.)
- `tools/kie_watch.py:43`: `urlretrieve(None, ...)` when `resultUrls` is empty crashes the watcher; guard it as `kie_compare.py` does.
- `.gitignore` covers only `output/` and `out/`. Children's photos, clips, `state.json` and `vision-cache.json` go to an operator-chosen OUT directory, so a run into another folder inside the repo could be committed by accident. Add media/state patterns or enforce `out/`.
- `kie_compare.upload` sends children's photos to the third-party upload host under a fixed `uploadPath` with no deletion step. Document retention in the privacy policy and delete uploads after use if the API allows.
- `tools/transition-test.html:289`: a `results` doc with `from: "__proto__"` makes rendering throw for every viewer; use a `Map` and `Number(r.from)`.
- `tools/transition-test.html:186,293-294,311`: `img`/`video` `src` accept any URL from the database, so a database writer could make viewers' browsers fetch an external URL (unless the claude.ai artifact CSP blocks it). Restrict to the asset-store origin.
- `tools/db_photos.py:22-27`: chunk `n`/`k` are unchecked and malformed values crash the script; validate `k in range(n)` and a consistent `n`.
- `tools/transition-test.html:3`: the Google Fonts stylesheet tells a third party when the page holding children's photos is opened.

Positive patterns:
- All `subprocess.run` calls use argument lists; no `shell=True`, `eval` or `exec`.
- No API keys in source or git history; credentials are proxy-injected.
- The upload page builds the DOM with `createElement`/`setAttribute`/text nodes only.
- Vision-LLM answers are parsed as JSON and only steer prompt text sent back to the same provider; the `hide` field is checked against a code-built allowlist.
- Output file names in `db_photos.py` come from the loop index, not from database values (no path traversal).

## 7. Coverage summary

| Status | Units |
|---|---|
| covered | 3 (upload page DOM rendering; vision-LLM output handling; secrets / committed data) |
| candidate | 2 (both resolved as `needs_validation`) |
| blocked | 0 |
| deferred | 1 (paid-credit cap / re-send / resume business logic) |

Excluded companion domains (no source-visible boundary): supply chain (no manifest/CI), cloud, web protocol/auth (no server), RPC, memory safety, desktop/mobile, data isolation (single-owner tooling).

Final critic result: one missing unit accepted and deferred, no reassignments. Because of the quick profile and the deferred unit, **this run makes no clean-coverage claim.**
