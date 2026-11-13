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
- [ ] Owner compares run 3 vs run 4. Next: 8-10 photos months apart; automatic face crop (better detector, e.g. MediaPipe/YuNet); music; subject tap for group photos.
- [ ] Then: measurement experiment plan (25 pairs × 2 attempts) and the KIE privacy email.
