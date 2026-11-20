# Lessons from the birthday video project (19-20.11.2026)

A real end-to-end job for the owner: a 56 s vertical birthday clip for his mother from 9 WhatsApp photos, then voiceover,
a sung song with her name, and an 11 s "envelope" greeting adapted from a Shabbat template video. All through KIE + ElevenLabs,
assembled in HyperFrames + FFmpeg. These are the parts that apply to Momenty Express.

## Costs measured (KIE credits unless stated)
| Step | Model | Cost | Notes |
|---|---|---|---|
| Instrumental music (2 versions) | Suno V5 | 12 | ~1 min to generate |
| Photo sharpening | `kie/image-upscale` | 4 per photo | x1/x2/x4, faces stayed faithful (checked side by side) |
| Photo animation 5 s, no sound | `kling-2.6/image-to-video` | 63 per clip | 5/5 clips kept identity, natural smile |
| Add vocals to our instrumental (2 versions) | Suno `ai-music-api/add-vocals` V6 | 12 | keeps the melody and length (56 s) |
| Re-sing one section | Suno `ai-music-api/replace-section` | 5 per call | min 10 s, max 50% of the song |
| Image edit (swap props, 2K) | `nano-banana-pro` | ~18 | derived from balance change |
| Keyframe animation 8 s 1080p | `kling-4.0/keyframe-to-video` | ~340 | derived from balance; ~5x a Kling 2.6 clip. NOT checked before running |
| Voiceover take (ElevenLabs v4) | ElevenLabs | 262 EL credits per take | each call makes 2 takes; concurrency limit delays the second |

Rule for the product: show the price before any expensive step and keep a per-video cost ceiling.
Kling 4.0 at 1080p must never run without an explicit price check.

## Total cost per deliverable
Conversion: KIE ~$0.005 per credit (1,080 credits ~ $5.40, see PROJECT_STATE), 3.19 ILS per USD.

**56 s clip with the sung song**
| Step | Credits |
|---|---|
| Instrumental music (Suno, 2 versions) | 12 |
| Sharpen 9 photos | 36 |
| Animate 5 photos (Kling 2.6, 5 s) | 315 |
| Add vocals | 12 |
| Vocals re-generated with niqqud (rejected by the owner) | 12 |
| Pronunciation fix, 3 replace-section calls (one wasted, see above) | 15 |
| **Total** | **402 credits ~ $2.01 ~ 6.4 ILS** (390 without the rejected run) |

Animation is ~80% of the clip's cost.

**11 s envelope greeting**
| Step | Credits |
|---|---|
| Upscale the first frame | 4 |
| 2 image edits (Nano Banana Pro) | ~36 |
| Keyframe transition (Kling 4.0, 1080p, 8 s) | ~340 |
| **Total** | **~380 credits ~ $1.90 ~ 6.1 ILS** |

An 11 s greeting cost almost as much as the full minute clip, only because of Kling 4.0 at 1080p.

**Voiceover (ElevenLabs, separate account)**: 3 takes = 786 EL credits; ElevenLabs reported $0.0524 per take = ~$0.16 (~0.5 ILS).
A 4th take was still queued (concurrency limit) at the time of writing.

**Whole project**: KIE 782 credits (982.64 -> 200.64) ~ $3.91 ~ 12.5 ILS, plus ElevenLabs ~0.5 ILS = **~13 ILS**.

## How models were chosen (and what to do instead)
| Step | Model | Basis for the choice |
|---|---|---|
| Upscale | `kie/image-upscale` | Topaz failed first (not charged); kie upscale tested on one face before/after, then run on all. Test-based. |
| Photo animation | Kling 2.6 | General knowledge that Kling keeps faces; one clip tested for quality and price (63) before the other 4. No comparison with other models. |
| Envelope transition | Kling 4.0 keyframe | Needed first + last frame so the final face is the real photo; picked 1080p for quality. **Price not checked first (~340 credits).** |
| Image edit | Nano Banana Pro | Known for local edits that keep the rest of the scene; checked only by looking at the result. |
| Music | Suno V5, then V6 | V5 with no comparison; V6 was the only non-deprecated option for add-vocals / replace-section. |
| Voiceover | ElevenLabs v4 | ElevenLabs' own default, supports emotion tags; voices picked from Hebrew filter by description, not by listening. |

Mistake: PROJECT_STATE was read only at the end. It already says Kling 3.0 Std is close to Pro, ~75 credits per 5 s at 720p,
and supports first + last frame (what Echoes uses). The envelope transition would likely have cost about a quarter.

Rules:
1. Before any run, read PROJECT_STATE and `docs/transition-guidelines.md` and choose from the models already measured there.
2. Check the price of every expensive step first (docs / estimate / one short test) and say it to the owner before running.
3. In the product: model choice comes from a table of measured price + quality, never from general familiarity.

## Photo preparation
- Upscale every photo first (WhatsApp photos arrive ~640x852). Cheap, faithful.
- Other people in a photo: crop to 9:16 around the subject first, blur only what is left (strong Gaussian + slight darkening).
  rembg `u2net_human_seg` failed when people overlap (merged them); a hand polygon worked. Product: the user taps the subject.
- Never AI-animate a photo that still contains blurred people: the video model may re-invent them. Those photos get camera
  motion (Ken Burns / parallax) instead. Same spirit as the OTHER PEOPLE RULE in PROJECT_STATE.

## Keeping the real face
- Image-to-video on solo photos with "very subtle natural motion, keep her face, features and identity exactly the same" worked.
- For an end card: generate the scene with an EMPTY frame (flat grey window), paste the real photo with a perspective warp
  (OpenCV), then animate first frame -> last frame with Kling 4.0 keyframe. The final face is the real photo, never invented.

## Occasion templates
- One base video can serve many occasions: Nano Banana Pro replaced Shabbat candles with roses + balloons and kept the envelope,
  seal, butterfly, table and light. Idea: a small library of base scenes (envelope, book, frame) + per-occasion prop edits.

## Personal song
- Suno add-vocals on our own instrumental + lyrics with the person's name = the most emotional part; a natural premium feature.
- Hebrew names and words get mispronounced ("Silavya", "bariya"). What fixed it:
  1. lyrics with niqqud for the risky words (סִילְבְיָה, בְּרִיאָה);
  2. replace-section on the version the user already liked, not a full re-generation (the user rejected the full re-gen);
  3. the section must cover whole lines: a 20.0-33.5 s cut ending mid-line dropped "בריאה ומאושרת"; 20.0-40.3 s (whole chorus) worked.
- Product: a "this word sounds wrong" button that re-sings only that section.

## What automatic checks cannot see
- Whisper (ivrit-ai) writes the correct spelling even when the singer mispronounces the name, so pronunciation cannot be
  verified by transcription. The user must listen before sending. Transcription is still good for "are all lines there, in time".

## Hebrew text on video
- PIL with raqm already does RTL: pre-reversing the string reversed it twice (owner caught it). Pass logical text with
  `direction="rtl"`, and check by code that the rightmost glyph is the first letter.
- Fontsource Hebrew subsets have no digits or "!": render those runs with the Latin subset.
- HyperFrames: `background-clip: text` on a parent breaks when child letters are transformed (put the gradient on each letter);
  `<video>` elements must be written in the HTML, not created by script, or they render black.

## WhatsApp delivery
- 1080x1920, H.264 CRF 22 + maxrate 6M, AAC, `+faststart`: ~22 MB per 56 s.
- The first frame is the chat thumbnail: put the title on screen at 0 s.

## Iteration
- The owner gave small corrections over several rounds. Keep every version and allow "go back to the previous one".
