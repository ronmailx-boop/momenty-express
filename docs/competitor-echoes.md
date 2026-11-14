# Echoes (your-echoes.com): competitor research, 13.11.2026

Public sources only: privacy policy and terms (updated 10.11.2026), 56 blog guides, robots.txt, 3 public demo videos.
The dashboard code is behind login and was not inspected. Exact model and prompts are NOT published.

## Confirmed (from their own pages)
- Video providers, one chosen per generation, a second on failure: Runway ML, Atlas Cloud, Higgsfield,
  AIMLAPI / Kling V2, Hailuo 02 (MiniMax), KIE AI (ByteDance Seedance + Seedream, Alibaba Qwen).
- Group photos: AWS Rekognition compares faces in the two photos and produces a text instruction
  ("the person on the left should become the person on the right") that is sent with the photos.
- Moderation: "add simple clothing to a flagged photo" (customer approves the edited photo).
- Prompt per pair is written automatically ("tailored to your photos"); on a retry the customer can pick a
  specific animation from a list, or swap the photo.
- Not zero-retry: every animation is reviewed by the customer; one free retry per animation (a shared bank).
- 13 photos = 12 animations = "1 minute", about 5 s each. Up to 80 photos per upload. Fewer than 3 people per photo.
- Time claim: "most people finish in under 30 minutes"; animations run in the background.
- Customer picks the shape (landscape / portrait / square); the site suggests one.
- Anthropic: support bot + picking frames for a 30 s "Highlights". Stack: Vercel, Supabase, AWS, Freemius, Resend, PostHog.
- Prices: $29.90 (1 min) to $114.90 (6 min).

## Measured on the demo videos
- 720x720 / 720x1280, 24 fps, assembled with ffmpeg (Lavf61.7).
- gallery-babies: 57.8 s, about 22 photos = about 2.6 s per photo (so clips are sped up or trimmed about x2).
- No face crop: the whole photo is kept, with blurred padding to fit the shape.
- Recurring move: arms up / jump with a short light glow at the moment of change; also spin, lunge to camera, run.

## Inferences (not confirmed)
- Qwen (vision) probably describes the photos and writes the prompt; Seedream does the clothing edit.
- The Growing model is one of the first+last-frame models in the list (Kling V2.x, Seedance, Hailuo 02).

## Ideas for Momenty Express
- Test Seedance (first + last frame) on KIE against Kling 3.0 Std: possibly cheaper.
- Second provider on failure is their standard too.
- Clothing edit for photos blocked by moderation.
- Their weak spot = our goal: they rely on customer review and retries; one-click needs an automatic judge.

## Confirmed from the owner's own account traffic (14.11.2026, free trial transition)
Collected by the owner with Claude in Chrome on his own account; only what the site returned to his browser.
- **Model: Kling 3.0 through KIE** - `"provider":"kiekling3"` in the generate response and in the clip record.
  First + last frame (`image_file_path` + `end_image_path`). Same model and provider as ours.
- Time for one clip: 4 min 38 s (queued 06:24:57 -> completed 06:29:34 UTC). Same KIE queue as ours.
- Prompt is NOT returned to the browser. Only `prompt_variation_id: "growing-1789501185776"`,
  `selected_prompt_id` (animation the customer picked) and `morph_instructions` (people instruction; null for 1 face per photo).
- Faces are counted in the browser before upload: `photo_face_counts: [1,1]`.
- Retry: `POST /api/clips/regenerate {clip_id, category: "natural"}`; suggested animation name "Camera dip";
  trial = 2 free retries, daily cap 15 per animation; "stubborn" tip from retry 3.
- Fallback fields: `generation_provider`, `failure_streak`, `failure_code`, `timed_out`.
- Limits: 2-101 photos per Growing video, 100 active clips. Aspect chosen up front (`generated_aspect_ratio: "9:16"`).
- Backend: Supabase (storage + REST) behind api.your-echoes.com; browser polls status every 10-15 s.
- Still unknown: clip duration, std/pro, resolution (need the clip file), the full animation catalog (not shown in trial).
- Reported by the browser extension in its summary (not yet measured by us on the file): clips are 5 s, 720p, 9:16;
  signed links expire after 12 h (`expiresIn: 43200`). 720p fits Kling 3.0 Standard and the public demo videos (720x1280).

## The trial clip itself (measured 14.11.2026; file kept out of the repo)
- Raw Kling output, not re-encoded by Echoes: metadata tag `AIGC: {"ContentProducer":"kling", ...}`,
  encoder `Lavc60.31.102 h264_slapi`. 720x1276, 24 fps, 121 frames = 5.04 s, 7.6 Mbit/s -> **Kling 3.0 Standard, 5 s**.
- Input: two baby photos (3:4), one face each, cropped to 9:16 by the site; no visible face-centred zoom.
- What happens (retry version, category "natural"):
  0-1.5 s  stays on photo 1; the baby kicks, laughs, pushes up (action that fits the pose).
  1.5-2.5 s the baby turns the head away while the camera swings around behind.
  2.5-3.3 s back of the head to the camera: sheet colour, clothes and place change together while the face is hidden.
  3.3-5 s  the baby turns back, already in photo 2 (crib, toys), and settles into the last frame.
- So their method = our "hiding" method (section 3 of transition-guidelines.md): one natural action, face hidden by a
  turn + camera move, everything changes at once, reveal, settle. No flash or glow in this clip.
- **First version** (default, `prompt_variation_id growing-...`; same specs: Kling tag, 720x1276, 5.04 s):
  0-0.5 s on photo 1; 0.5-1.5 s the baby turns the head away; 1.5-2.5 s slides off the bed, back to the camera;
  2.5-3.5 s walks/runs across the room, camera follows, the shirt appears mid-run; 3.5-4.5 s climbs into the crib;
  last 0.5 s turns to the camera = photo 2. This is our "travel" move (guidelines section 3).
  Flaws: a baby of a few months walks and climbs (not believable); the clothes change in plain view, not hidden.
- So the default is a travel move with a following camera, and the retry category "natural" gives a calmer
  in-place head-turn. Two of our three strategies, picked without regard to the child's age.
