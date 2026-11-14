# PROJECT_STATE

## Project
Momenty Express: "One click to generate a growing-up video" — the user picks photos, and the video is ready in a promised time, without per-transition retries.
Built on the experience of Momenty (repo `ronmailx-boop/replica`, site momenty.vplusstudio.app).

## Decisions / notes
- Per-transition clean rate with Kling 3 Pro in Momenty was roughly 70-85% (from its PROJECT_STATE notes) — too low for one click.
  Plan: photo checks at upload + 2-3 candidates per transition + automatic judge (code checks + vision-model judge) + a guaranteed fallback transition (face morph / light flash).
- AI provider for tests: KIE (kie.ai, NEXUSAI SERVICES LLC, Denver). Network secret for `api.kie.ai` saved on the Default environment (key `claude-cloud`, 90 days, all models).
  Pay-as-you-go, credits never expire, failed tasks not charged, media kept 14 days, logs 2 months. Balance 13.11: 1,080 credits (~$5.40).
- KIE is a small reseller; before production ask in writing: no training on photos, deletion, where processed. Atlas Cloud (NY, SOC 2 claimed) is the alternative; fal stays as the automatic fallback.
- Test page (Artifact, private): https://claude.ai/artifact/KopYK45HGjQw4BdNKCEY79 — source `tools/transition-test.html`.
  db: `session/photos` {items:[{id,url,w,h}], status}, `results/*` {from, model, label, url, credits, cost, seconds, res, state, error, order}, `ratings/<resultId>` {rating, issues[], note}. Photos are assets of the artifact (not in the repo).

- **Transition guidelines (read before any run or prompt change): `docs/transition-guidelines.md`** — model, photo prep, strategies,
  variety, timing of the change, people, forbidden wording, assembly, reliability, prompt template; working prompts in `docs/prompts/`.
- **RE-SEND RULE (mandatory, owner's request 13.11.2026 — learned the hard way, 226.5 credits lost):**
  Re-send a clip to the SAME provider only when that one clip lags far behind the others in the same run:
  at least half of the run's clips have finished AND this clip has waited more than max(5 min, 2 x the median wait of the finished clips).
  If most clips are still running, the provider's whole queue is slow: do NOT re-send (it only doubles the cost); send to the second
  provider (fal) instead, or wait and promise a longer time. At most one re-send per clip and at most 20% of a run's clips.
  KIE charges every accepted task up front and refunds only failed ones, so a duplicate that succeeds is always paid twice.
  Implemented in `tools/kie_watch.py`; the same rule must go into the production server.

- **OTHER PEOPLE RULE (owner's finding 13.11.2026, run 8 T4: the mother got an invented ponytail and a changed face):**
  Every person in a photo, not only the child, must look exactly as in the photo: face, hair and hairstyle, clothes. Say it per person in the
  prompt (e.g. "her mother keeps her loose hair, no ponytail"). Never pick an action that turns an adult's back to the camera or shows a side
  of them the photo does not show (spins, turning away): the model invents it. The big action belongs to the child; adults stay roughly in
  place or leave the frame.

## Current Focus
- [x] New repo attached; test upload page published.
- [x] Owner uploaded 4 photos (toddler at a shop window -> snow with two kids, the RED coat is the subject -> bike -> beach teen).
- [x] Verified KIE params. Kling 4.0 Flash has NO last frame (dropped). Kling 4.0 keyframe = 28.5 cr/s at 720p (not 17). Upload host kieai.redpandaai.co (second network secret), results on tempfile.aiquickdraw.com (allowed host).
- [x] Run 13.11: 13/13 succeeded, 906.6 credits (~$4.53); balance 173.4. Clips + `results` rows on the test page.
  Wait (KIE, per clip): Veo 3.1 Fast ~78 s, Kling 3.0 Std / 2.5 Turbo ~107-116 s, Kling 3.0 Pro ~200-222 s, Kling 4.0 253 s.
  Claude's first look (frames): Veo 3.1 Fast = hard cut at the end + 16:9 output (unusable); Kling 2.5 Turbo = chaotic falls/blends;
  Kling 3.0 Pro = best overall (T3 rides from park to beach); Kling 3.0 Std close to Pro, slight see-through in T2;
  identity: in T1/T2 the Kling 3.0 models made the BLUE-hat child the subject (owner: red coat) — Kling 4.0 picked the red coat (1 sample).
  Lesson: with several people the prompt must name who grows (e.g. user taps the person; competitor uses face matching).
- [x] Run 2 (13.11, T1+T2, Kling 3.0 Pro/Std): prompt names the subject ("the boy in the red coat on the right"; the blue-hat child walks in/out from the side)
  vs the same + a Kling element (2 face/body crops of the subject). 8/8 succeeded, 564.8 credits; balance 608.6.
  Claude's look: NAME ONLY = right child in 4/4 (Pro and Std), clean moves (T2: blue hat walks out left, red coat runs at the camera -> bike).
  NAME + REFERENCE = worse: see-through blends (T1 Pro and Std), and in T2 Pro the blue-hat child is carried into the park scene.
  Decision candidate: Kling 3.0 Std (720p, 60.4 cr ~ $0.30, ~1.5 min) with a prompt that names the subject; no element references.
  Product: for photos with several people the app must know who the child is (tap to confirm a pre-selected face) and describe him in the prompt.
- [x] Owner rated runs 1-2: only T3 (bike -> beach) Kling 3.0 Pro/Std "good"; the rest "no real growing transition, a slideshow".
  Cause: Momenty's prompt HIDES the change (turn away / cover the frame), and the 4 photos were years apart, small full-body subjects.
- [x] Echoes examples (3 videos from the owner): same hiding tricks (hand on lens, tilt to floor, door), BUT ~25 photos/min months apart,
  face-dominant framing, each photo alive 2-3 s; with similar framing the face visibly ages in place (~0.7 s). Growth comes from the sequence.
- [x] Run 3 (13.11): new 4 photos of one boy (~2-5 y), squares cropped around the face by hand (Haar detector failed on a mask),
  new prompt = visible aging in place (face stays, clothes/hair/place change), Kling 3.0 Std, 181.2 credits, 214-274 s per clip; balance ~427.
  Claude's look: real in-place transformation (costume -> shirt -> Superman -> Real Madrid), one face; short see-through moments in the background.
  Full 13 s video on the test page (results rows now carry `run`; the page shows only the latest run; from=0 = full video).
- [x] Owner rated run 3 full video "good, but not much movement" (cause: the prompt asked for stability; 4 s clips; plain concat).
- [x] Run 4 (13.11): same aligned photos, prompt = one big joyful action per clip (jump+clap / wave+lean in / arms up), camera pushes in then
  pulls back while he ages, change happens during the motion; 5 s clips (KIE_SECONDS=5), 75.5 cr each, 226.5 total, 137-148 s; balance 200.9.
  Mean frame difference 10.6-17.4 vs 2.7-7.0 in run 3. Full video sped up x1.15 (14.3 s). Page shows runs 3+ side by side.
  Risks seen: heavy motion blur in T1 claps, wide laughing mouth, T3 background switches late.
- [x] Owner rated runs 3-4: T1 (street Spider-Man -> indoor shirt) failed both; T2 best = run 4 ("excellent, best so far");
  T3 best = run 3 ("5 stars"). 4/6 passed. Full run 4: "better, but he never leaves his spot" -> cause: aligned start/end frames + prompt.
  Decision: two strategies chosen per pair — similar photos = aging in place; very different place/outfit = travel move (runs off, camera follows, place changes).
- [x] Run 5 (T1 travel, 6 s): FIRST attempt blocked by KIE moderation ("sensitive information", not charged) — wording about the child's body.
  Reworded (no body words) -> success, 90.6 cr, 96 s: runs off down the sidewalk, sidewalk turns into the playroom, runs back in the white shirt.
  Flaw: invented a red cape. Best-of full video (T1 run 5 + T2 run 4 + T3 run 3, 15 s) on the test page. Balance 110.3.
  Lesson: moderation false positives on child photos are a failure mode -> pre-tested wording, automatic reworded retry, fallback transition.
- [x] Owner: run 5 full video "very reasonable, passes"; flaw: after the turn the mask/cape stayed ~1 s in the playroom (place and outfit changed at different moments).
- [x] Run 6 (T1 travel v2, 6 s, 90.6 cr, 118 s): prompt orders the change — place, outfit and mask change TOGETHER while his back is to the camera;
  when he turns he is already in the white shirt; "no cape at any time". Claude's look: fixed (no cape, no mask after the turn).
  Full video v2 (T1 run 6 + T2 run 4 + T3 run 3) on the test page. KIE balance 19.7 (top-up needed for more runs).
  Prompt lessons: say WHEN each change happens (all at once, while the face/back hides it); forbid invented items by name.
- [x] Owner rated run 6: "We have a winner. Continuing with this method." (13.11.2026)
  DECISION: Kling 3.0 Standard via KIE (`kling-3.0/video`, mode `std`, sound false, image_urls [first, last], 4-6 s), 15.1 cr/s (~$0.0755/s).
  Method = face-centred square crops + per-pair strategy (similar photos: aging in place with one big joyful action and a camera push-in/pull-back;
  very different photos: travel move, everything changes at once while his back is to the camera) + subject named for group photos.
- [x] Run 7 = measurement experiment (13.11): 12 photos of a baby girl (~2 months -> ~1.5 y); automatic YuNet crops with tapped subject (3 group photos).
  Baby version of the strategies (babies can't run): A = aging in place 4 s (T2,3,9,10), C = camera moves close until the face fills the frame,
  everything changes, pulls back 5 s (T1,4,5,6,7,8,11). One attempt each. Moderation blocks: 0/11. Claude's frame check: 11/11 pass (minor: T4 eyes look enlarged, T9 white blur).
  TIMING: 9 clips 96-170 s; T5 and T8 stuck in KIE "generating" > 20 min (charged up front, 75.5 each). Re-sent at 1,239 s -> back in 97/96 s.
  All 11 ready at 1,336 s (22.3 min). With an automatic re-send at 5 min it would have been ~300 + ~100 = ~400 s (~7 min) + assembly.
  Cost: 770.1 for the 11 used clips + 151 for the stuck duplicates = 921.1 credits (~$4.61). Video 36.9 s (A clips x1.3, C clips x1.5).
  Product rule: re-send any clip still running after ~5 min (or send to fal); promise time = p95 of (slowest clip with re-send) + assembly.
- [x] Owner on run 7: "all fine but very boring": only push-in/pull-back, the baby only smiles. Cause: two templates, all actions were smiles.
- [x] Run 8 (13.11): same 12 photos, one prompt per photo: an action tied to what is in it (crib toy, tickling brother, yellow plush, headband,
  crib rail, car window, orange cup), a different hiding move each time (roll face-down, lifted out of frame, head turned, spin blur, toy peekaboo,
  hands peekaboo, hand over lens, drops below the rail, looks at the window, camera to the floor, cup over face), varied camera and expressions
  ("does not smile the whole time"). All 5 s, 75.5 cr each. Claude's look: 11/11 usable, far more variety; small: invented trees (T2), smear (T8),
  round vignette frame (T11). Video 37.9 s (x1.5).
  TIMING: this time the whole KIE queue was slow: every clip took 585-636 s (9.8-10.6 min) from our submit; all ready at 636 s.
  The 5-min re-send did NOT help (the 3 accepted copies finished later than the originals; 8 more were refused for lack of credits) and cost 226.5.
  => re-sending to the same provider only helps a single stuck clip; a slow queue needs a second provider (fal) or an honest longer promise.
  KIE status checks also returned 502 once: the server must retry. Balance 41.6.
- [x] Owner on run 8: OK except T4 (spin with mother): the mother got an invented ponytail and a changed face -> OTHER PEOPLE RULE added.
  Guidelines consolidated in `docs/transition-guidelines.md` (merged, PR #3). KIE top-ups so far: 4 x $5 = $20 (+80 free credits);
  used ~4,038 credits; balance 41.6 (top up before the next run). Re-send losses: 377.5 credits total, of which 226.5 pure loss (run 8).
- (done above) Measurement experiment (approved 13.11, scaled to 30 s): 12 photos of one child, months apart, Echoes pace (~2.5 s per photo),
  11 transitions, automatic strategy by rules (Claude decides and logs each choice), ONE attempt each (+ automatic reworded retry only on
  moderation blocks), Claude checks frames + owner rates, full 30 s video. Measure first-try pass rate per strategy, block rate, wait p50/p95,
  cost per 30 s. Budget ~755 cr (8 in-place x 60.4 + 3 travel x 90.6); owner tops up $5 (balance ~1,020).
  Test page: "mark the child" tap for group photos (stored as items[].subject {x,y} normalized), folder button accept fix for Galaxy S25 FE.
- Echoes music: own upload (user bears the rights), built-in library (source unstated), AI custom song (provider unstated; KIE sells Suno — unverified). 8-10 photos months apart; automatic face crop (better detector, e.g. MediaPipe/YuNet); music; subject tap for group photos.
- [x] (replaced) measurement plan: done as runs 7-8 at 30 s scale. Open: the KIE privacy email.

## Conversation summary (13.11.2026, before /compact)
- Question that started it: can a "one click, no retries, ready in X minutes" growing-up video site (based on Momenty) work?
  Answer so far: the METHOD works (owner: "we have a winner"), but the one-click AUTOMATION is not built and success is measured on 2 children only.
- Other answers given: Google Play can approve such an app (Play Billing ~15% is mandatory for in-app purchases; AI-content report button;
  photo moderation; account deletion; data safety; biometric/face matching must be disclosed). KIE vs fal vs Atlas: KIE small Colorado LLC
  reseller, privacy policy covers only email; Atlas NY, SOC 2 claimed; fal large. Echoes music: own upload (user bears rights), built-in
  library (source unstated), AI custom song (provider unstated). 60 s at Echoes pace ~24 photos; our measured cost ~$0.30-0.45 per transition,
  ~$4-5 for 12 photos with no retries.
- Launch readiness (owner asked 13.11): NOT ready. Missing: (1) automation of what Claude did by hand — a vision model that describes each photo,
  picks the action/strategy per the guidelines, an automatic judge and a fallback transition; (2) measurement on 5-10 photo sets;
  (3) the site + server (can reuse Momenty: Firebase, render job, Paddle, music picker) with KIE + fal fallback and the re-send rule;
  (4) a reliable time promise (measured 3-33 min); (5) KIE written privacy commitments, privacy policy, terms, accessibility statement.

## Phase 1 plan (approved by the owner 14.11.2026)
Goal: one script, photos folder -> finished video, nobody in the loop. Output numbers: first-pass rate, time to video, cost per video.
Pipeline: (1) photo checks (YuNet: faces, size, sharpness) (2) crop `tools/align_faces.py` (3) vision model describes each photo
(4) code rules pick strategy + hiding move + camera per pair, per `docs/transition-guidelines.md` (5) vision model writes the action
sentences into the fixed template (6) KIE Kling 3.0 Std 5 s with the re-send rule; reworded retry on a moderation block
(7) automatic judge = code checks (first/last frame match, no hard cut, no doubled face / extra person) + vision model on 8-10 frames
(8) one retry with another hiding move, then a local face-morph fallback (9) assembly (guidelines section 8).
Stages, with a stop and a report to the owner between them:
- [x] A: describe + strategy + prompts on the 12 photos of run 8, compared with the hand-written prompts (vision cost only). DONE 14.11.
- [x] B: the judge, calibrated on the clips of runs 1-8 that the owner already rated (vision cost only). First version done 14.11.
- [~] C: first full run, done on 6 photos (run 9, 14.11) after a $5 top-up. Waiting for the owner's ratings.
- [ ] D: 4 more sets of different ages (~830 credits each).
Not in phase 1: site, server, payment, music, legal documents.
Owner still has to supply: KIE top-up before C (about $25-30 for C+D), 4-5 photo sets of 12.

### Stage A status (14.11.2026)
- Script: `tools/auto_plan.py OUT_DIR photo1-sq.jpg ...` -> `plan.json` + `prompts.json`. Answers are cached in OUT_DIR/vision-cache.json
  (a re-run resumes), photos are uploaded as 768 px copies and passed by URL, describe/compare calls run 6 in parallel.
- Vision model (owner approved KIE for the experiment): Gemini 3.8 Flash, `POST https://api.kie.ai/gemini-3-8-flash-openai/v1/chat/completions`
  (OpenAI chat format, image_url by URL or base64 data URL, `stream:false`, answer in choices[0].message.content, cost in `credits_consumed`).
  Measured: 0.06 credits and ~14 s per photo description; the whole stage A is ~2 credits.
  An Anthropic key can NOT be saved as a network secret here (request_credential refuses Anthropic hosts); it would have to be an
  environment variable + a new session. Claude through KIE (`/claude/v1/messages`) works for text but fails on images (500).
- Run on the 12 photos of run 8 stopped at 23 of 34 calls: all Gemini models on KIE started returning "upstream request failed" after 30 s
  (also for plain text). 12 descriptions + 11 comparisons were done; the 11 prompt-writing calls are missing. Cost so far ~1.3 credits.
  The cache was in the session scratchpad and is NOT in the repo (it describes private photos): a new session re-runs it (~2 credits).
  The 12 square photos are also only in the scratchpad; originals are assets of the test artifact (`session/photos` in its db).
- Findings from the automatic strategy choice vs the hand choice of run 7 (fix BEFORE the next run):
  1. T8 and T10 got "travel / run_and_turn" for a baby: the model called her "toddler" because she stands in the crib.
     Rule to add: no travel when the child is strapped in (stroller, car seat, high chair), inside a crib, or held.
  2. "in_place" was never chosen (by hand: T2, T3, T9, T10). The test `same_place_kind and same_pose_kind and similar_framing`
     is too strict: use same_pose_kind and similar_framing only.
  Otherwise fine: age-appropriate hiding moves, no adjacent repeats, no moves that turn the mother.
- Lesson: KIE for both vision and video is a single point of failure. Production needs a separate vision provider.
- KIE balance 14.11: 40.3 credits (~29 after stage A, 7.73 after stage B).

### Stage A result (14.11.2026)
- Vision model switched to **GPT on KIE** (`gpt-6-sol` via `/codex/v1/responses`, OpenAI Responses format; fallbacks gpt-5-6-luna,
  then Gemini). Gemini and Claude-with-images on KIE were down (502/500). Owner's decision: stay with KIE only (cheaper; Echoes uses KIE).
- Full run on the 12 photos of run 8: 34/34 calls, 4.26 credits, 2:42 min (prompt-only re-runs ~1.6 credits, ~1:45 min).
- Automatic prompts: `docs/prompts/run8-auto-stage-a.json` (hand version: `docs/prompts/run8-baby-varied.json`).
- Fixes made after the first look (all in `auto_plan.py`): one pronoun for the whole video (majority gender); no repeated hiding move
  until others are used (9 different moves in 11); no hands/toy/lens moves for a lying baby; writer told to prefer the first
  (object-based) move; "never"/"gone" are item lists and the code writes the sentences (free sentences had reversed meaning).
- Compared with the hand prompts: same move in T1 (roll), T5 (yellow plush), T8 (below the rail), T11 (orange cup); no travel for
  a contained child (fix works); in-place only in T2. Differences: T2/T4 hand used the mother lifting/spinning her (auto never moves
  adults: safer after the ponytail finding); T3 hand used the brother tickling (auto: hands peekaboo); T7 hand reached for the lens
  (auto: head turn); T9 hand looked at the window (auto: face fills frame); T10 hand dropped a thing (auto: head turn again).
- How to rebuild the run 8 inputs in a new session (scratchpad is wiped):
  originals = assets of the test artifact; `Artifact read` with `paths` does NOT work for assets, `read_asset` (claude-artifacts MCP,
  slug 984e01bb-de0a-4c67-99e2-0baa544d86f8) does: it saves each JPEG under the session's tool-results folder.
  Order and taps are in db `session/photos` (photo 2 @0.417,0.437; 3 @0.342,0.532; 4 @0.52,0.339).
  Run 7/8 photo asset ids in order (saved 14.11 because a new upload on the test page replaces `session/photos`):
  1001f6fcc0455a99a2f0117de6317478, f9a8a979da60ff59a182bbbb7fa87e58, 4f290097ae6695ad6cf7397c8df35bdf, 44c57262157c66d63d7c4d624a14a5df,
  00640f874a56f25c9322d7ec9d165bd6, ce9fc88535acea026f5393cf3df1d057, 23130937c15ec429c53ebfed92d491e9, 293663c3e0ae66c79fe3ec988648fb3c,
  cac77f96f749e2d8ccae013440a9872e, 86fac1f4425fe9244b554211d6b53957, e4a4594b871d70edf48b1401bdd88462, 9f61690a535fd4a8d923e1ac2702e333.
  `pip install opencv-python-headless` (cv2 is not preinstalled), then
  `python3 tools/align_faces.py OUT/sq 01.jpg 02.jpg@0.417,0.437 03.jpg@0.342,0.532 04.jpg@0.52,0.339 05.jpg ... 12.jpg`,
  then `python3 tools/auto_plan.py OUT/plan OUT/sq/photo1-sq.jpg ... photo12-sq.jpg` (~5 credits, ~3 min).
- Known gaps: descriptions sometimes wrong in small ways (photo 6 crib called "bed"; photo 5 stroller called "car seat");
  prompts are long (~1,400 chars) with many people lines in group photos; only 2 children tested.

### Stage B result (14.11.2026) - judge v2 (`tools/judge.py`)
- Labels: `docs/judge/labels.json` = owner's verdicts on 48 clips (ratings on the test page + run 7/8 verdicts), 30 pass / 18 fail.
  Clips: KIE `recordInfo?taskId=` gives the result URL (tempfile.aiquickdraw.com, allowed), the prompt and the input photo URLs
  (tempfile.redpandaai.co is NOT reachable from the session; not needed: first/last frames = the photos). Task ids are in the
  test artifact's `results/*` rows. KIE keeps the clips ~14 days (until ~27.11); the clips are also assets of the test artifact.
- Code checks (free, ~1 s/clip): hard cut (jump ratio > 8), extra/doubled face (YuNet: >= 10 of ~24 sampled frames with more faces
  than the first/last frame), almost no motion (< 4 = slideshow); start/end match when the photos are given (untested).
  Alone: never rejected a clip the owner passed; caught r8-t4 (mother changed), Veo's end cut, 2 slideshows.
- Vision check: GPT-6 Sol on KIE, one 4x3 grid = 6 frames spread + 6 dense around the biggest frame change (timed labels),
  prompt explains our method (fast change while the face is hidden is CORRECT). ~0.17 credits per clip.
  v1 (12 even frames, generic checklist) agreed 23/48: it called our half-second change "a cut". v2 agrees 34/48.
- Results v2 (`docs/judge/calibration-v2.json`):
  runs 3-8 (our method, Kling 3.0 Std): 27/30 agree, 0 of 3 bad clips passed, 3 of 27 good clips rejected (r3-t2, r7-t7, r8-t3: "crossfade").
  runs 1-2 (old prompt, other models): 7/18 agree, 11 of 15 bad clips PASSED: wrong child grows (prompt did not name the subject),
  "no real growing transition" (owner's taste), Kling 2.5 Turbo / Veo / Kling 4 quality.
- Gaps: (1) wrong-child detection - add a free face-identity check (OpenCV SFace embeddings: the face that ends as the later child
  must match the subject's face at the start); (2) only 3 bad clips made with our method -> the bad-clip rate is not measured;
  stage C will add owner-rated clips; (3) a rejected good clip costs one retry (~75 credits).
- Credits: stage B used ~20 (calibration v1 11.5 + v2 7.9 + tests). KIE balance 14.11: 7.73.

- Tried 14.11: face-identity tracking (OpenCV SFace) to catch "wrong child grows" - it caught nothing: in our method the face is
  hidden exactly at the change, so the tracks break for good and bad clips alike. Removed. The wrong child is prevented upstream
  instead (subject-centred crop + the prompt names the subject; run 2: name only = right child 4/4).

### Stage C prepared (14.11.2026): `tools/run_set.py` = one command, photos -> video
- Steps: crop (align_faces) -> plan (auto_plan.make_plan) -> all clips in parallel on Kling 3.0 Std via KIE with the RE-SEND RULE
  -> content-filter block = one reworded prompt -> judge (judge.py, with start/end-photo match) -> a rejected clip gets ONE retry
  with another hiding move (auto_plan.write_one(exclude=...)) -> still rejected = local fallback (push-in on the face, white flash,
  pull-out; ffmpeg, free) -> assembly per guidelines section 8 -> OUT/video.mp4 + OUT/report.json
  (first-try passes, retries, fallbacks, minutes to video, credits, USD). State in OUT/state.json: a re-run resumes, never pays twice.
  `--max-credits N` (default 1200) stops sending clips past N Kling credits.
- Dry run 14.11 on run 8's photos with run 8's existing clips (`--use-clips`, no Kling): whole chain works, 3-4 min, 2.6 credits.
  Judge: 9/11 pass; rejected T3 (scene jumps with the face visible) and T4 (the clip the owner rejected: mother changed) -> fallback.
  Start/end match: right photos 1.0/0.98, wrong photos 0.03/0.12 (threshold 0.6). Output video 37 s (local only, not in git).
- Stage C cost estimate: 11 clips x 75.5 = ~830 credits + 2-3 retries (~75 each) + ~5 vision = ~1,000 credits (~$5).
- How to run stage C (new session): attach photos in the session or in a new test artifact; `pip install opencv-python-headless`;
  `python3 tools/run_set.py OUT photo1.jpg photo2.jpg@x,y ... ` (x,y = tapped child in a group photo, 0..1), in the background
  (~10-20 min); then show the owner video.mp4 + report.json and collect ratings per transition (compare with the judge).

### Cost of a 1-minute video (calculated 14.11.2026 from measured numbers; 1 KIE credit = $0.005)
- Pace: a 5 s clip sped x1.5 = ~3.3 s of video per transition -> 60 s = ~18 transitions = ~19 photos (+2 s end hold).
  (Echoes' pace 2.5 s/photo = ~24 photos for the same minute and ~30% more cost.)
- Base: 18 x 75.5 = 1,359 credits = $6.80.
- Judge retries: rejection rate measured 15-20% (calibration on our method 6/30; dry run 2/11) -> ~3.6 retries x 75.5 = ~270 cr ($1.35).
  A second rejection = free local fallback (no extra cost).
- Re-sends (stuck clips): ~1 per video on average (~75 cr, $0.38); the rule caps them at 20% of the clips.
- Content-filter blocks: not charged. Vision (plan + judge): ~10 cr ($0.05).
- EXPECTED: ~1,715 credits = ~$8.60 per minute. Bad day (30% retries + 20% re-sends): ~2,040 cr = ~$10.20.
  Hard ceiling with run_set's rules: ~2,990 cr = ~$15.
- Cheaper option to test: 4 s clips (60.4 cr, x1.3 = 3.1 s) = ~$5.90 base per minute (~$7.50 expected), less room for the action.
- Compared with "2-3 candidates per transition" (the first plan): $13.60-20.40 per minute. One try + judge + one retry + free
  fallback costs ~1.26x the base instead of 2-3x.

- Comparison with Echoes (14.11.2026): same model and provider (Kling 3.0 Std via KIE, `kiekling3`), so the cost per clip is about
  the same (~$0.38) unless they have a KIE volume discount. Echoes' "1 minute" = 13 photos (12 clips, ~$4.53 + customer retries
  they pay for; their demos show ~22 photos/min though). Ours for 13 photos: ~$5.70 expected. Our advantage is not cost but one
  click (no customer review); the judge + retry costs ~20% more. Savings to try: 4 s clips (-20%), ask KIE for a volume discount
  (in the same email as the privacy questions).
- Price and profit at 89 ILS per minute (owner's proposed price, incl. 18% VAT; rate assumed ~3.70 ILS/USD, not checked):
  AI cost per 19-photo minute: expected ~32 ILS, bad day ~38, ceiling ~56; 13-photo minute ~21.
  Web (Paddle 5% + $0.50): 89 - VAT 13.6 - fee 6.3 = 69 left -> profit ~37 ILS (42%); bad day ~31; ceiling ~13.
  App (Google Play 15%): 64 left -> profit ~32 ILS (36%); bad day ~26; ceiling ~8. With a 13-photo minute: ~48 (web) / ~43 (app).
  Not included: advertising (likely the largest cost), server/storage (cents), music (undecided), refunds, support, income tax.
  Echoes charges $29.90 (~110 ILS) for the same minute.

### Photo upload path for stage C (14.11.2026)
- The test page (https://claude.ai/artifact/KopYK45HGjQw4BdNKCEY79, source `tools/transition-test.html`, version 10) now also saves
  each uploaded photo into its database as base64 chunks: `photodata/<assetId>-<k>` {id, k, n, b64} (200,000 chars each); the item
  in `session/photos` carries `chunks`. Reason: the asset store can't be read from every session (read_asset was gone 14.11).
- Run 7/8 photo list archived to `archive/photos-run7-8`; `session/photos` emptied for the new set (assets not deleted).
- To fetch: ArtifactData get `session/photos` and list `photodata` (query.limit 1000) with out_dir = DB, then
  `python3 tools/db_photos.py DB OUT` -> OUT/01.jpg ... + the run_set.py arguments with the taps (tested: byte-identical).
- Upload instructions for the owner: 6 photos of one child (see the chat list 14.11): 1 baby lying alone; 2 baby with people (tap
  the child); 3 seated in a high chair/stroller with an object; 4 seated, framed like 3 (in-place test); 5 toddler outdoors standing;
  6 child indoors. Run with `--max-credits 900` after a $5 top-up (~455-530 credits expected, ceiling ~830).

### Stage C, run 9 (14.11.2026): first fully automatic run, 6 photos of the run 7/8 girl (new photos except photo 1)
- Command: `python3 tools/run_set.py OUT <6 photos, taps on 2 and 6> --max-credits 900` (photos rebuilt with db_photos.py).
- Plan: T1 roll face-down, T2 hands peekaboo, T3 in-place, T4 toy peekaboo (yellow plush), T5 in-place.
- Clips ready 137-169 s after submit (normal queue, no re-sends). Judge: 4/5 pass first try; T4 rejected (stroller shows through
  the later photo, frames 8-10 - Claude's look confirms) -> retry with hand-over-lens, ready in 102 s, passed. No fallback.
- Totals: 7.3 min from start to video, 457.4 credits ($2.29: Kling 453 + vision 4.4), video 18.7 s.
  KIE balance after: 547.7.
- Files: prompts `docs/prompts/run9-stage-c.json`, report `docs/judge/run9-report.json`; clips + full video on the test page
  (`results/r9-*`, run 9; the rejected T4 is shown too, labelled). Video not in git.
- OWNER'S RATINGS (14.11): pass T2 (hands peekaboo, "perfect"), T3 (in-place, "simple, almost no motion"), T5 (in-place, "good aging");
  fail T1 (roll -> "slideshow"), T4 (plush -> "slideshow"), T4-retry (hand over lens -> "almost a slideshow"). Owner pass 3/5 first try.
  Judge v2 agreed 4/6; both misses were "slideshow" clips it passed. Added to `docs/judge/labels.json` (r9-*).
- CAUSE (Claude's frame look): in T2 the hands are still over her face in the NEW place, then come down = one continuous movement.
  In T1 she rolls in the crib, a blur, and the shot opens in a different pose (in her mother's arms) = slide change. Hand over the
  lens = whole frame dark, then a new photo = slide change.
- FIX (14.11, free): BRIDGE RULE. `auto_plan.py` HIDES now carry `finish` for bridge moves (hands/toy/cup peekaboo, head turn and
  back, duck below rail and pop up, run off and come back); `choose` offers only bridge moves when one fits; the writer returns
  `finish` and the template says the movement carries on through the change "never like a cut or a slide change".
  Guidelines section 3 updated. Re-plan of run 9 photos: T1 head turn, T2 hands peekaboo, T3 in-place, T4 head turn, T5 in-place.
- Judge v3 (told to fail "slide changes") was WORSE (3/6: rejected both good in-place clips, still passed both slideshows) -> reverted.
  Slideshow is prevented at the source; the judge can't see it in 12 still frames. Owner ratings stay the measure for it.

### Run 10 (14.11.2026): A/B on run 9's 6 photos with the bridge rule
- Plan (descriptions re-made, so not identical to the dry re-plan): T1 head turn and back, T2 "below the rail" (the bench railing:
  her mother lowers her into the bouncer in one movement), T3 in-place, T4 toy peekaboo, T5 in-place. No slide-change moves.
- Clips 98-116 s; judge 4/5 first try; T5 rejected ("abrupt change with the face visible") -> retry passed. No fallback.
  8.3 min, 458.3 credits ($2.29). KIE balance after: 85.5 (top-up needed for any further run).
- Files: `docs/prompts/run10-bridge.json`, `docs/judge/run10-report.json`; clips on the test page (`results/r10-*`, run 10).
- Open: owner rates run 10 -> is "slideshow" gone? Compare with run 9 (3/5 owner passes).
- Note: photo descriptions differ between runs (vision model is not deterministic) -> the plan for the same photos can change.

## Next step (exact)
1. Owner rates run 10 on the test page. If "slideshow" is gone: stage D (more sets, other ages: an older child for the travel
   move); needs a KIE top-up (balance 85.5; ~460 credits per 6-photo set).
2. In-place clips pass but are "simple, almost no motion": give in-place a bigger action (guidelines section 4) in the next round.

## Competitor research (13.11.2026)
- [x] Echoes deep research from public sources: `docs/competitor-echoes.md`. Providers: Runway, Atlas, Higgsfield, AIMLAPI/Kling V2, Hailuo 02, KIE (Seedance, Seedream, Qwen); Rekognition for group photos; customer reviews each animation (free retry each), so not one-click. Exact model/prompts not public. Idea to test: Seedance first+last frame on KIE.
- [x] 14.11.2026: owner's own Echoes trial traffic confirms **Echoes = Kling 3.0 via KIE** (`provider: kiekling3`), first+last frame, 4:38 min for one clip; prompt stays server-side. Details in `docs/competitor-echoes.md`. Clip measured: raw Kling file (AIGC tag ContentProducer kling), 720x1276, 24 fps, 5.04 s = Kling 3.0 Std 5 s; the transition is a head-turn + camera-swing hiding move, same method as ours.
