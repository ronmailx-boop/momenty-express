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

- **RE-SEND RULE (mandatory, owner's request 13.11.2026 — learned the hard way, 226.5 credits lost):**
  Re-send a clip to the SAME provider only when that one clip lags far behind the others in the same run:
  at least half of the run's clips have finished AND this clip has waited more than max(5 min, 2 x the median wait of the finished clips).
  If most clips are still running, the provider's whole queue is slow: do NOT re-send (it only doubles the cost); send to the second
  provider (fal) instead, or wait and promise a longer time. At most one re-send per clip and at most 20% of a run's clips.
  KIE charges every accepted task up front and refunds only failed ones, so a duplicate that succeeds is always paid twice.
  Implemented in `tools/kie_watch.py`; the same rule must go into the production server.

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
- [ ] Owner rates run 8.
- (done above) Measurement experiment (approved 13.11, scaled to 30 s): 12 photos of one child, months apart, Echoes pace (~2.5 s per photo),
  11 transitions, automatic strategy by rules (Claude decides and logs each choice), ONE attempt each (+ automatic reworded retry only on
  moderation blocks), Claude checks frames + owner rates, full 30 s video. Measure first-try pass rate per strategy, block rate, wait p50/p95,
  cost per 30 s. Budget ~755 cr (8 in-place x 60.4 + 3 travel x 90.6); owner tops up $5 (balance ~1,020).
  Test page: "mark the child" tap for group photos (stored as items[].subject {x,y} normalized), folder button accept fix for Galaxy S25 FE.
- Echoes music: own upload (user bears the rights), built-in library (source unstated), AI custom song (provider unstated; KIE sells Suno — unverified). 8-10 photos months apart; automatic face crop (better detector, e.g. MediaPipe/YuNet); music; subject tap for group photos.
- [ ] Then: measurement experiment plan (25 pairs × 2 attempts) and the KIE privacy email.
