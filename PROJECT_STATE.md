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
- [ ] Owner uploads ~4 photos in order and writes "העליתי".
- [ ] Verify in KIE docs each model's start/end-frame parameters and price: Kling 3.0 (1080p), Kling 4.0, Kling 4.0 Flash, Kling 2.5 Turbo, Veo 3.1 Fast.
- [ ] Run 3 transitions × 5 models (~950 credits), upload clips to the page, write `results`.
- [ ] Owner rates; summarize per model: clean rate, cost, wait time.
- [ ] Then: measurement experiment plan (25 pairs × 2 attempts) and the KIE privacy email.
