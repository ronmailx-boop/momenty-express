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
