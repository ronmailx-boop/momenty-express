# Needs validation — momenty-express (run 1)

Prioritized leads. No severity is assigned; none is a confirmed vulnerability.

## 1. Shared-DB tap coordinates printed unquoted into the shell argument line

Fingerprint: `tools/db_photos.py:unquoted-db-subject-in-printed-run_set-args`

**Boundary:** a principal who can write the test page's shared artifact database → the operator's shell session (which holds proxy-injected KIE credentials and the `--max-credits` cap).

**Trace**
1. `tools/transition-test.html:177` (`savePhotos`): `session/photos` is stored with `subject` as given; no schema. The page itself writes only rounded numbers (`:219`).
2. `tools/db_photos.py:14`: the exported `session/photos.json` is loaded with no type checks.
3. `tools/db_photos.py:28-29`: `f"@{s['x']},{s['y']}"` interpolates the raw values.
4. `tools/db_photos.py:32`: `print(" ".join(args))` prints the line unquoted.
5. `PROJECT_STATE.md:327`, `:489-490`: the printed line is used as `<args>` in `python3 tools/run_set.py OUT <args> --max-credits <balance-10>` in the operator's Bash session. `run_set.py:209-212` (argparse) accepts injected `--max-credits` / `--use-clips` / extra photo paths; the tap is `float()`-parsed only afterwards (`run_set.py:54`).

**Blockers**
- Who can write the artifact database is set by claude.ai sharing, not by source. If only the owner can write it, this is self-injection and not a vulnerability.
- Whether the printed line is pasted literally (command execution) or via `$(...)` (argument injection only) is an operational fact.
- No sandbox was available to run `db_photos.py` on a malicious fixture.

**Local plan:** in an offline sandbox with a scratch-only writable directory, create `DB/session/photos.json` with `subject.x = "0.5,0.5 --max-credits 1e9 ;touch SCRATCH/pwned;#"` and a one-chunk `DB/photodata/a-0.json`; run `python3 tools/db_photos.py DB SCRATCH/out > SCRATCH/line` (10 s limit); confirm the unquoted `;`, `#` and `--max-credits 1e9`; show word splitting with `printf '%s\n' $(cat SCRATCH/line)`. Do not run `run_set.py` or evaluate the line.

**Owner check:** open the test page artifact's sharing settings and note whether anyone besides the owner has edit access; confirm how the printed line is used.

**Fix:** convert `subject.x/y` with `float()` and require `0 <= v <= 1`; print each argument with `shlex.quote`; or have `run_set.py` read the taps from the JSON directly.

## 2. Provider result URLs fetched without a scheme/host check

Fingerprint: `operator-local-read-via-provider-result-url`

**Boundary:** the AI provider's task-status response (KIE, over HTTPS with a proxy-injected key) → files on the operator's machine.

**Trace**
1. `tools/run_set.py:119`: `recordInfo` JSON from `https://api.kie.ai`.
2. `tools/run_set.py:126`: `resultUrls[0]` taken with no validation.
3. `tools/run_set.py:129`: `urllib.request.urlretrieve(url, cp["file"])`. The default opener accepts `file:`, `ftp:`, `data:` and any http(s) host; a `file:` URL copies a local file into `OUT/<k>.mp4`.
4. `tools/run_set.py:259` → `tools/judge.py:23`: the file is decoded by OpenCV (only decodable media gives frames).
5. `tools/judge.py:143`: frames go into `grid.jpg`.
6. `tools/auto_plan.py:33`: the grid is uploaded to `kieai.redpandaai.co` and sent to the vision model; the clip is also concatenated into `OUT/video.mp4` (`run_set.py:202`).
Same sink: `tools/kie_compare.py:132`, `tools/kie_watch.py:43`, `tools/make_song.py:69`.

**Blockers**
- Requires a malicious, compromised or spoofed response from the credentialed HTTPS provider; whether KIE can return attacker-influenced `resultUrls` is not visible in source.
- No sandbox to run the mocked harness.

**Local plan:** offline sandbox; monkeypatch `kie_compare.req` to return `resultUrls: ["file:///<scratch>/dummy.mp4"]`; stub `kie_compare.upload` and `auto_plan.vision`; run `Run.poll` on one clip; check that `OUT/<k>.mp4` is a byte copy and that the stubbed upload receives frames of the dummy file; repeat with a non-media file (copied but not uploaded). Regression: after the fix, both mocks are refused before any file is written.

**Owner check:** list the result hosts in past `state.json` / `task.json` files to pin an allowlist; confirm no request field can influence `resultUrls`. Send no audit traffic to KIE.

**Fix:** one download helper for all four call sites that requires `scheme == "https"` and a host on a pinned KIE result-host allowlist.
