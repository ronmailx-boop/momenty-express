#!/usr/bin/env python3
"""Phase 1, stage A: from square photos to one Kling prompt per transition, with no human in the loop.

  describe each photo (vision model) -> compare each pair (vision model) -> pick strategy, hiding move and
  camera move (rules in this file, from docs/transition-guidelines.md) -> write the action sentences
  (vision model) -> assemble the fixed template -> lint.

The vision models are KIE chat models (GPT first, Gemini as fallback) (key injected by the session's network proxy).

  python3 auto_plan.py OUT_DIR photo1-sq.jpg photo2-sq.jpg ...     # writes OUT_DIR/plan.json and prompts.json
"""
import hashlib, json, os, re, subprocess, sys, threading, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
import kie_compare

# Vision models on KIE, tried in order. 14.11.2026: all Gemini and Claude-with-images calls on KIE failed (502/500)
# while the GPT models (Responses API, /codex/v1/responses) worked: gpt-6-sol 0.08 cr, gpt-5-6-luna 0.01 cr per small call.
MODELS = os.environ.get("VISION_MODELS", "gpt-6-sol,gpt-5-6-luna,gemini-3-8-flash-openai").split(",")
credits = 0.0
OUT = "."
LOCK = threading.Lock()


CACHE = {}          # answers already paid for; saved in OUT_DIR/vision-cache.json so a re-run resumes
USED = {}           # model -> answers it gave
URLS = {}           # local photo -> uploaded 768 px copy (a URL is far more reliable here than base64 in the body)


def photo_url(path):
    if path not in URLS:
        small = os.path.join(OUT, "v-" + os.path.basename(path))
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", path, "-vf", "scale=768:-2", "-q:v", "4", small], check=True)
        URLS[path] = kie_compare.upload(small)
    return URLS[path]


def ask(model, prompt, images):
    """One call to one model; returns the answer text and the credits it cost."""
    if model.endswith("-openai"):          # Gemini: OpenAI chat format
        content = [{"type": "text", "text": prompt}] + [{"type": "image_url", "image_url": {"url": photo_url(p)}} for p in images]
        url, body = f"https://api.kie.ai/{model}/v1/chat/completions", {"messages": [{"role": "user", "content": content}], "stream": False}
    else:                                   # GPT: OpenAI Responses format
        content = [{"type": "input_text", "text": prompt}] + [{"type": "input_image", "image_url": photo_url(p)} for p in images]
        url, body = "https://api.kie.ai/codex/v1/responses", {"model": model, "stream": False,
                                                             "input": [{"role": "user", "content": content}]}
    r = urllib.request.Request(url, data=json.dumps(body).encode(), headers={
        "Authorization": "Bearer proxy-injected", "Content-Type": "application/json"})
    out = json.loads(urllib.request.urlopen(r, timeout=120).read())
    if "choices" in out:
        text = out["choices"][0]["message"]["content"]
    else:
        text = "".join(c.get("text", "") for o in out["output"] if o.get("type") == "message" for c in o["content"])
    return text, out.get("credits_consumed") or 0


def vision(prompt, images, tries=8):
    """One question that must be answered with a JSON object. Moves to the next model on errors (KIE often has one
    model down or rate-limited) and on unparsable answers."""
    global credits
    key = hashlib.sha1((prompt + "|".join(images)).encode()).hexdigest()
    if key in CACHE:
        return CACHE[key]
    prompt += "\nAnswer with one JSON object only, no other text."
    last = None
    for attempt in range(tries):
        model = MODELS[attempt % len(MODELS)]
        try:
            text, cost = ask(model, prompt, images)
            text = re.sub(r"\[cite[^\]]*\]", "", text)
            answer = json.loads(text[text.index("{"):text.rindex("}") + 1])
            with LOCK:
                credits += cost
                CACHE[key] = answer
                USED[model] = USED.get(model, 0) + 1
                json.dump({"cache": CACHE, "urls": URLS}, open(os.path.join(OUT, "vision-cache.json"), "w"))
            return answer
        except (urllib.error.URLError, KeyError, ValueError, TimeoutError, OSError) as e:
            last = f"{model}: {e}"
            time.sleep(2 * (attempt // len(MODELS) + 1))
    raise SystemExit(f"vision model failed: {last}")

DESCRIBE = """This is one photo from a family's growing-up video. The main subject is the child whose face is nearest the
centre of the upper part of the frame. Describe only what is visible. Fields:
"subject": short phrase that picks the subject out if other people are in the photo (e.g. "the baby girl in the pink hat"),
"gender_word": "girl" | "boy" | "child",
"stage": "lying_baby" (cannot sit alone) | "sitting_baby" (sits or crawls, does not walk) | "toddler" (walks) |
         "child" (about 3-11) | "teen_adult",
"pose": what the subject is doing and how they are held or seated,
"place": the place, 3-8 words, "indoor": true/false,
"clothes": subject's clothes, "hair": subject's hair,
"objects": list of up to 5 clearly visible things the subject could touch or look at (toy, cup, rail, window, strap...),
"others": list, one item per other person: {"who": "mother"/"man"/"older boy"..., "where": "left"/"behind"/"holding the subject"...,
          "hair": exact hair and hairstyle as seen, "clothes": ..., "face_visible": true/false},
"face_clear": true if the subject's face is sharp and unobstructed,
"contained": true if the subject cannot move away freely: strapped in (stroller, car seat, high chair), inside a crib, cot or
             playpen, or held / carried by someone."""

COMPARE = """Two photos of the same child, the first earlier, the second later. Compare them. Fields:
"same_place_kind": true if both are the same kind of place with a similar background (e.g. both on a sofa indoors),
"same_pose_kind": true if the child's posture and how they are held or seated is similar,
"similar_framing": true if the child's size and position in the frame are similar,
"only_in_first": list of people or big objects that are in the first photo and not in the second,
"only_in_second": list of people or big objects that are in the second photo and not in the first."""

# Hiding moves by developmental stage (guidelines section 3). "needs" = a word that must appear in the photo's objects/pose/place.
HIDES = {
    "roll_face_down": {"stages": ["lying_baby", "sitting_baby"], "text": "rolls over onto the front, face down", "solo": True},
    "hands_peekaboo": {"stages": ["sitting_baby", "toddler"], "text": "covers the face with both hands as in peekaboo"},
    "toy_peekaboo": {"stages": ["sitting_baby", "toddler"], "text": "lifts the toy up in front of the face", "needs": ["toy", "plush", "doll", "teddy", "book", "rattle"]},
    "hand_over_lens": {"stages": ["sitting_baby", "toddler", "child", "teen_adult"], "text": "reaches out and a hand covers the lens"},
    "head_turn_away": {"stages": ["lying_baby", "sitting_baby", "toddler"], "text": "turns the head fully away from the camera to look at something"},
    "face_fills_frame": {"stages": ["lying_baby", "sitting_baby", "toddler"], "text": "the camera moves in until the face is so close that it blurs and fills the frame"},
    "below_rail": {"stages": ["sitting_baby", "toddler"], "text": "ducks down below the rail", "needs": ["rail", "crib", "cot", "bars", "playpen"]},
    "cup_over_face": {"stages": ["sitting_baby", "toddler", "child"], "text": "tips the cup up so that it hides the face", "needs": ["cup", "bottle", "glass", "mug"]},
    "camera_to_floor": {"stages": ["sitting_baby", "toddler", "child", "teen_adult"], "text": "drops something, and the camera follows it down to the floor"},
    "run_and_turn": {"stages": ["toddler", "child"], "text": "runs away from the camera with the back to it, then turns around", "solo": True, "travel": True, "moves": True},
    "jump_spin": {"stages": ["child"], "text": "jumps and spins once, the back passing the camera", "solo": True, "moves": True},
    "run_to_camera": {"stages": ["toddler", "child"], "text": "runs straight at the camera until very close, blurring the frame", "solo": True, "moves": True},
    "walk_past_camera": {"stages": ["teen_adult"], "text": "walks close past the camera, blurring the frame", "solo": True},
}
CAMERAS = ["follows the movement", "rises slowly", "stays still", "slides to the side", "moves slowly closer", "circles a little around"]
CONTAINED = re.compile(r"\b(crib|cot|playpen|stroller|pram|buggy|car ?seat|high ?chair|bouncer|strapped|buckled|held|"
                       r"carried|in (his|her|their|the) arms|on (his|her|their|the) (lap|shoulders|hip))\b", re.I)
BANNED = re.compile(r"\b(body|bodies|naked|nude|bare|skin|chest|belly|tummy|bottom|legs?|thighs?|diaper|nappy|underwear)\b", re.I)


def choose(first, cmp, used, i):
    """Strategy and the hiding / camera moves the writer may pick from (guidelines sections 3, 4 and 6)."""
    stage, others = first["stage"], bool(first["others"])
    # the place may differ (run 7: T2, T3, T9, T10 were in-place by hand with a new background)
    similar = cmp["same_pose_kind"] and cmp["similar_framing"]
    hay = " ".join([first["pose"], first["place"]] + first["objects"]).lower()
    # a child who stands in a crib or sits strapped in is not free to run (run 7 T8, T10 were sent to "travel")
    contained = bool(first.get("contained")) or bool(CONTAINED.search(first["pose"] + " " + first["place"]))
    allowed = [k for k, h in HIDES.items() if stage in h["stages"] and k != (used[-1] if used else None)
               and not (others and h.get("solo"))                       # adults must not be turned or left behind
               and not (contained and h.get("moves"))                   # no running / jumping out of a crib or seat
               and (not h.get("needs") or any(w in hay for w in h["needs"]))]
    if similar:
        return "in_place", [], 5
    runner = stage in ("toddler", "child") and not others and not contained and not cmp["same_place_kind"]
    if runner and "run_and_turn" in allowed:
        return "travel", ["run_and_turn"], 6
    allowed = [k for k in allowed if not HIDES[k].get("travel")] or ["hand_over_lens"]
    # moves not used yet in this video first (run 8 by hand: 11 different moves), then object-based moves (they tie
    # the action to this photo: cup, toy, rail)
    allowed.sort(key=lambda k: (used.count(k), not HIDES[k].get("needs"), (list(HIDES).index(k) + i) % len(HIDES)))
    return "hiding", allowed[:3], 5


WRITE = """You write the middle part of a video-model prompt for one transition of a growing-up video: one continuous shot that
starts exactly on photo 1 and ends exactly on photo 2 (the same child, older).
Photo 1: {a}
Photo 2: {b}
Differences: {cmp}
Strategy: {strategy}. {how}
Camera: the camera {camera}.
Rules:
- The action must use something really visible in photo 1 (one of its objects, or what the child is already doing), and fit
  what a child at stage "{stage}" can physically do. Never use an object that is not in the photo.
- Do not use these words: body, skin, bare, chest, belly, legs, diaper. Describe actions, not the child's physique.
- Other people never turn their back, never spin, never change. The big action belongs to the child.
Fields:
"hide": the id of the hiding move you chose from the list ("" for in-place),
"action": 1-2 sentences in present tense, starting from photo 1's pose: the action, an expression that is not just a smile,
          the camera move, and (unless in-place) the hiding moment. Call the child "{pron}" (never "they" unless {pron} is "they"). Say only the action and hiding;
          do not describe the second photo, the template does that.
"while": a short clause that completes "The change happens all at once while ..." (e.g. "her face is down during the roll"),
"people": one sentence per other person in either photo: that they keep their exact face, hair (quote the hairstyle) and
          clothes; and for a person in only one photo, that they walk in from / step out to the side, whole and solid.
          "" if there are no other people,
"never": list of up to 2 things (1-3 words each) the video model might invent here and must never show (e.g. "cape", "extra hands"),
"gone": list of up to 3 things (1-3 words each) that are in photo 1 and NOT in photo 2, so they must be gone at the end
        (e.g. "orange cup", "car seat")."""

TEMPLATE = ("One continuous shot with no cuts, no flashes, no dissolves and no added effects. Start exactly on the first photo and "
            "end exactly on the second photo. The same {who} is in both photos, a little older in the second.{named} {Poss} expression "
            "changes naturally with what {pron} is doing (curious, focused, surprised, delighted); {pron} does not smile the whole time. "
            "{action} The change happens all at once while {whilst}: {poss} age, hair, clothes and the place all turn into the second "
            "photo's together. Then {pron} is revealed in the second photo's place and pose and eases into it over the last half second, "
            "so the last frame is the second photo. {Poss} face stays one clear face whenever it is visible, never doubled or "
            "see-through. In each photo {pron} looks exactly as in that photo (face, eyes, hair). {people}"
            "No people, objects or text that are not in the photos.{ban}")
IN_PLACE = "the camera moves in and back out during one big action"


def load_cache(out):
    global OUT
    OUT = out
    os.makedirs(out, exist_ok=True)
    if os.path.exists(os.path.join(out, "vision-cache.json")):
        saved = json.load(open(os.path.join(out, "vision-cache.json")))
        CACHE.update(saved["cache"]); URLS.update(saved["urls"])


def write_one(i, photos, desc, cmps, gender, used, prev_cam, exclude=(), note=""):
    """Plan and prompt for transition i (photo i -> i+1, 0-based). `exclude`: hiding moves not to use (a retry after the judge
    rejected one); `note`: extra instruction for the writer (e.g. after a content-filter block)."""
    pron = {"girl": "she", "boy": "he"}.get(gender, "they")
    poss = {"she": "her", "he": "his", "they": "their"}[pron]
    a, b, cmp = desc[i], desc[i + 1], cmps[i]
    strategy, hides, seconds = choose(a, cmp, list(used) + list(exclude), i)
    hides = [h for h in hides if h not in exclude] or [h for h in HIDES if h not in exclude and a["stage"] in HIDES[h]["stages"]
                                                          and not HIDES[h].get("moves")][:3]
    if exclude and strategy == "in_place":        # in-place was rejected: hide the change this time
        strategy, seconds = "hiding", 5
    camera = next(c for c in CAMERAS[i % len(CAMERAS):] + CAMERAS if c != prev_cam)
    how = ("In-place aging: no hiding; one big action that fits the pose while " + IN_PLACE + ", and the child visibly grows during it."
           if strategy == "in_place" else
           "Pick ONE hiding move from (prefer the first): " + "; ".join(f'{k} = the child {HIDES[k]["text"]}' for k in hides) + ".")
    w = vision(WRITE.format(a=json.dumps(a), b=json.dumps(b), cmp=json.dumps(cmp), strategy=strategy, how=how,
                            camera=camera, stage=a["stage"], pron=pron) + (("\n" + note) if note else ""), [photos[i], photos[i + 1]])
    hide = w.get("hide") if w.get("hide") in hides else (hides[0] if hides and strategy != "in_place" else "")
    whilst = w["while"].strip().rstrip(".") if strategy != "in_place" else f"{pron} {'are' if pron == 'they' else 'is'} in the middle of the action"
    who = ("baby " if "baby" in a["stage"] else "") + gender
    named = f" {pron.capitalize()} is {a['subject']}." if a["others"] or b["others"] else ""
    clean = lambda xs: [x.strip().rstrip(".") for x in xs if x.strip() and len(x.split()) <= 4][:3]
    never, gone = clean(w.get("never", [])), clean(w.get("gone", []))
    ban = "".join(f" No {x} at any time." for x in never) + (f" By the end there is no {', no '.join(gone)}." if gone else "")
    people = (w.get("people", "").strip() + " ") if w.get("people") else ""
    prompt = TEMPLATE.format(who=who, named=named, Poss=poss.capitalize(), poss=poss, pron=pron,
                             action=w["action"].strip(), whilst=whilst, people=people, ban=ban)
    problems = [f"banned word: {m}" for m in sorted(set(x.lower() for x in BANNED.findall(prompt)))]
    if (a["others"] or b["others"]) and not people:
        problems.append("other people are in the photos but the prompt does not pin them")
    if not (a["face_clear"] and b["face_clear"]):
        problems.append("a face is not clear")
    step = {"from": i + 1, "strategy": strategy, "hide": hide, "camera": camera, "seconds": seconds,
            "compare": cmp, "problems": problems}
    return step, prompt


def make_plan(out, photos):
    """All photos -> (plan dict, prompts). Writes OUT/plan.json and OUT/prompts.json."""
    load_cache(out)
    for p in photos:
        photo_url(p)
    pairs = list(zip(photos, photos[1:]))
    with ThreadPoolExecutor(6) as pool:          # the photo and pair questions do not depend on each other
        desc = list(pool.map(lambda p: vision(DESCRIBE, [p]), photos))
        cmps = list(pool.map(lambda ab: vision(COMPARE, list(ab)), pairs))
    # one pronoun for the whole video: the model says "child" when unsure in a single photo
    words = [d["gender_word"] for d in desc if d["gender_word"] in ("girl", "boy")]
    gender = max(set(words), key=words.count) if words else "child"
    steps, prompts, used, prev_cam = [], [], [], None
    for i in range(len(photos) - 1):
        step, prompt = write_one(i, photos, desc, cmps, gender, used, prev_cam)
        steps.append(step); prompts.append(prompt)
        used, prev_cam = used + ([step["hide"]] if step["hide"] else []), step["camera"]
        print(i + 1, step["strategy"], step["hide"], "|", step["camera"], "|", "; ".join(step["problems"]) or "ok")
    plan = {"photos": desc, "compares": cmps, "gender": gender, "transitions": steps,
            "vision_credits": round(credits, 2), "vision_models": USED}
    json.dump(plan, open(os.path.join(out, "plan.json"), "w"), indent=1)
    json.dump(prompts, open(os.path.join(out, "prompts.json"), "w"), indent=1)
    print("vision credits:", round(credits, 2), USED)
    return plan, prompts


def main():
    make_plan(sys.argv[1], sys.argv[2:])


if __name__ == "__main__":
    main()
