# Competitor: Memvivo (memvivo.com)

Checked 27.11.2026 from the public site (home page, /privacy, /terms). Nothing below is a guess unless marked "estimate".

## Who
- Operator: Troiva LLC, Wyoming, USA (registered-agent address in Sheridan, WY). Contact hello@memvivo.com. Source: /terms, /privacy.
- Terms updated 4.11.2026, privacy 6.11.2026 -> a very new site. Payments "not open yet": testers redeem gift codes (home page, pricing note).
- Hebrew first (Israeli-style copy: bar mitzvah, army, wedding hall), plus en, ar, de, es, fr, it, ja, ko, nl, pl, pt-BR, ru.
- Stack seen: Next.js, Firebase / Google Cloud, Resend (email), Freemius (merchant of record). AI: **KIE AI** for video, music and text
  (privacy page: "KIE AI receives the photos and texts needed to create the clips, the opening and the song").

## Product (same idea as Momenty Express)
- Every two adjacent photos -> one 5 s AI clip. 12 photos ~ 1 min film. Output MP4 1080p, 16:9 / 1:1 / 9:16 (fixed at start).
- Personal opening title with the name, closing dedication, caption per clip. Music: library, own file, or an original song written about the person. No voiceover yet.
- Retries: "one retry per two photos" in paid packs; free first clip has one retry. Re-render the film unlimited times.
- Free trial: first clip (2 photos) free, no credit card. 30-day full refund from the account.
- Photos: Google Photos import, phone, computer. Says it does not restore/enhance old photos.
- Privacy claims: KIE gets a private photo link valid 60 min; deleted at the provider within 14 days; never used for training.
- Shows the remaining time per clip; email when ready.
- SEO: occasion landing pages (/bar-mitzvah, /anniversary, /birthday, /wedding, /retirement, /new-baby) and /guides articles.

## Prices (one-time, incl. VAT, home page)
| Film | Photos | Price |
|---|---|---|
| 1 min | 12 | ₪59.90 |
| 2 min | 24 | ₪99.90 |
| 3 min | 36 | ₪139.90 |
| 4 min | 48 | ₪169.90 |
| 5 min ("most popular") | 60 | ₪199.90 |
| 6 min | 72 | ₪229.90 |

## Estimate: their cost per 1-min film (our KIE numbers, model unknown)
- ~11 clips x ~$0.38 (Kling 3.0 Std 5 s on KIE, measured in this repo) = ~$4.2; with all 6 retries used ~$6.5 (~₪21-24), plus song.
- ₪59.90 incl. 18% VAT = ~₪50.8 net, minus Freemius fee. So the entry pack has thin margin; long packs are better for them.

## What it means for Momenty Express
- Same provider (KIE) and same 5 s-per-pair format: no tech moat for either side. Their retries are manual ("didn't like it? retry");
  our plan is automatic candidates + judge + guaranteed fallback = "one click, no retries". That is the main angle to sell.
- Their weak spots (from their own text): no photo enhancement, no voiceover, aspect ratio locked, payments not live yet.
- Copy what is table stakes: free first clip without card, 30-day refund, occasion pages, Google Photos import, per-clip ETA.
