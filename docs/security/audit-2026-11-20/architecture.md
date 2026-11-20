# Architecture — momenty-express (run 1, quick)

## 1. Product, principals, resources
Phase-1 R&D toolkit for "Momenty Express": turns a family's photos of one child (young → older) into an AI "growing-up" video. There is no deployed server in the repository. Principals:
- **Operator** (the owner, or Claude in a cloud session) runs the Python CLIs in `tools/` locally. Their environment has a network proxy that injects the paid KIE API key into every request to `api.kie.ai` / `kieai.redpandaai.co` (`tools/kie_compare.py:19-27`, `tools/auto_plan.py:46-47`, `tools/make_song.py:19-22`).
- **Photo uploader / rater** uses `tools/transition-test.html`, a claude.ai Artifact page. It stores photos and ratings in the artifact's shared database (`db.doc(...)`, `claude.use("db")`, `tools/transition-test.html:131-148, 297-316`) and the artifact asset store. Who may open/write that artifact is decided by claude.ai sharing, not by source.
- **Third-party AI providers** (KIE: Kling video, vision LLMs, Suno songs) return JSON task results, result URLs and LLM text that the tools trust.
Protected resources: children's photos and generated videos (sensitive personal data of minors), the paid KIE credit balance, the operator's machine/session (files, proxy-injected credentials).

## 2. Comparable baseline
No source-grounded comparable; omitted.

## 3. Stack and deployment
Python 3 scripts using stdlib `urllib`, OpenCV (`cv2`), numpy, and `ffmpeg`/`ffprobe` via `subprocess.run` with argument lists (no shell). One static HTML page with inline JS, run only inside claude.ai (`window.claude`). No package manifest, CI, Dockerfile or deploy config in the repo. Running the tools spends paid credits and contacts provider APIs, so they are prohibited for this audit; no target code is executed.

## 4. Entry surfaces and important paths
1. **Artifact DB → page DOM**: `session/photos`, `results/*`, `ratings/*` docs rendered via the `el()` helper (`setAttribute` + text nodes, no innerHTML) — `tools/transition-test.html:136-145, 162-187, 263-293`. `results` docs (`url`, `label`, `error`, ...) are written by the operator from provider output.
2. **Artifact DB → operator CLI**: `tools/db_photos.py` reads exported `session/photos.json` and `photodata/*.json` chunks, writes `OUT/NN.jpg`, and prints a `run_set.py` argument line containing `subject.x/y` (`tools/db_photos.py:17-31`), which the operator pastes into a shell.
3. **CLI args → files/ffmpeg**: photo paths and `@x,y` taps (`tools/run_set.py:51-57`, `tools/align_faces.py:51-55`); ffmpeg concat list built from local paths with `-safe 0` (`tools/run_set.py:212-216`).
4. **Provider responses → local sinks**: `resultJson.resultUrls[0]` → `urllib.request.urlretrieve(url, file)` (`tools/run_set.py:134-140`, `tools/kie_watch.py:42-44`, `tools/kie_compare.py:122-127`, `tools/make_song.py:63-69`); downloaded media → OpenCV / ffmpeg decode and concat into the customer video (`tools/judge.py:24-33`, `tools/run_set.py:183-219`).
5. **Vision-LLM answers → plan/prompts**: `auto_plan.vision()` parses model JSON (`tools/auto_plan.py:56-76`) and its fields drive strategy choice and prompt text sent to Kling; cached in `vision-cache.json`.
6. **Photo upload to third party**: `kie_compare.upload()` posts children's photos to `kieai.redpandaai.co` (`tools/kie_compare.py:39-53`).
7. **Repository contents**: committed docs/JSON (`docs/judge/*.json`, `docs/prompts/*.json`, PROJECT_STATE.md) and `.gitignore` (`.env`, `output/`, `out/`).

## 5. Trust boundaries and strongest visible control
- DB data → DOM: `el()` uses `setAttribute`/`append` text (no HTML parsing); `on` key only from code.
- DB data → operator shell: none visible (values printed unquoted).
- Provider URL → local fetch: none visible (no scheme/host check before `urlretrieve`).
- Downloaded media → ffmpeg: ffmpeg's own demuxer restrictions only (deployment/toolchain fact).
- LLM answer → prompts: `lint` / fixed template in `auto_plan.py`; prompts only go back to the provider.
- Secrets: KIE key is proxy-injected, code sends placeholder `Bearer proxy-injected`.

## 6. Starting paths
`tools/transition-test.html`, `tools/db_photos.py`, `tools/run_set.py`, `tools/kie_compare.py`, `tools/kie_watch.py`, `tools/make_song.py`, `tools/auto_plan.py`, `tools/judge.py`, `tools/align_faces.py`, `.gitignore`, `docs/`.

## 7. Prior coverage
No prior run or ledger exists for this repository.

## 8. Companion selection
- `CLIENT-SIDE.md` (DOM and object-state): the Artifact page renders shared-DB data into the DOM.
- `AI-AND-LLM.md` (Output and disclosure): LLM output drives local plan/prompt logic.
- Not selected: SUPPLY-CHAIN (no manifest/CI/release), CLOUD (no IaC), WEB-PROTOCOL (no server), PROTOCOLS-RPC, MEMORY-SAFETY (no native code in repo), DESKTOP-MOBILE, DATA-ISOLATION (single-owner tooling, no tenants), RESOURCE-EXHAUSTION (operator-only CLIs; credit caps reviewed under business logic in the tools unit).
