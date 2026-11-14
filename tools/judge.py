#!/usr/bin/env python3
"""Phase 1, stage B: automatic judge for one transition clip (pass / fail + reasons), with no human in the loop.

Two layers:
  1. code checks (free, ~1 s): hard cut, extra or doubled faces (YuNet), and - when the two photos are given -
     that the clip starts on photo A and ends on photo B.
  2. vision model (KIE chat, same models as auto_plan.py): one 4x3 grid of 12 frames + the clip's prompt, answering a
     fixed checklist (right child grows, real continuous growing, one clear face, other people unchanged, no invented people).

  python3 judge.py clip.mp4 [--prompt-file p.txt] [--a photoA.jpg --b photoB.jpg]        # one clip -> JSON on stdout
  python3 judge.py --calibrate CLIPS_DIR META.json LABELS.json OUT_DIR                 # compare with the owner's verdicts
"""
import argparse, json, os, subprocess, sys
import cv2
import numpy as np
import auto_plan as AP

FACE_MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "yunet.onnx")


def frames(clip, size=None):
    """All frames as BGR arrays (5 s at 24 fps = ~121 frames, small enough to keep in memory)."""
    cap, out = cv2.VideoCapture(clip), []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        out.append(cv2.resize(f, size) if size else f)
    return out


def faces(img, det_cache={}):
    h, w = img.shape[:2]
    if (w, h) not in det_cache:
        det_cache[(w, h)] = cv2.FaceDetectorYN.create(FACE_MODEL, "", (w, h), 0.75, 0.3, 50)
    _, found = det_cache[(w, h)].detect(img)
    return [] if found is None else [f[:4] for f in found if min(f[2], f[3]) > 0.04 * w]


def similarity(a, b):
    """0..1, normalised correlation of small grey images (robust to small colour and compression changes)."""
    g = [cv2.resize(cv2.cvtColor(x, cv2.COLOR_BGR2GRAY), (64, 64)).astype(np.float32).ravel() for x in (a, b)]
    g = [(x - x.mean()) / (x.std() + 1e-6) for x in g]
    return float(max(0.0, (g[0] * g[1]).mean()))


def code_checks(clip, photo_a=None, photo_b=None):
    fs = frames(clip)
    small = [cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), (64, 64)).astype(np.float32) for f in fs]
    diff = np.array([np.abs(small[i + 1] - small[i]).mean() for i in range(len(small) - 1)])
    med = float(np.median(diff)) + 0.5
    cut_i = int(diff.argmax())
    out = {"frames": len(fs), "motion": round(float(diff.mean()), 2),
           "max_jump": round(float(diff.max()), 1), "jump_ratio": round(float(diff.max()) / med, 1),
           "jump_at": round(cut_i / max(1, len(diff)), 2)}
    # faces: compare each sampled frame with the faces in the first and last frame
    step = max(1, len(fs) // 24)
    counts = [len(faces(f)) for f in fs[::step]]
    base = max(len(faces(fs[0])), len(faces(fs[-1])))
    out.update({"faces_start_end": base, "faces_max": max(counts), "frames_extra_faces": sum(c > base for c in counts)})
    if photo_a and photo_b:
        a, b = cv2.imread(photo_a), cv2.imread(photo_b)
        out.update({"start_match": round(similarity(fs[0], a), 2), "end_match": round(similarity(fs[-1], b), 2)})
    return out, fs


def code_verdict(c):
    problems = []
    if c["max_jump"] > CUT_JUMP and c["jump_ratio"] > CUT_RATIO and 0.05 < c["jump_at"] < 0.95:
        problems.append(f"hard cut at {int(c['jump_at'] * 100)}% of the clip")
    if c["frames_extra_faces"] >= EXTRA_FACE_FRAMES:
        problems.append(f"extra or doubled face in {c['frames_extra_faces']} sampled frames")
    if c["motion"] < MIN_MOTION:
        problems.append("almost no motion (slideshow)")
    if c.get("start_match", 1) < MATCH or c.get("end_match", 1) < MATCH:
        problems.append("does not start on photo A or end on photo B")
    return problems


# thresholds, set by --calibrate on the owner-rated clips of runs 1-8 (docs/judge/)
# hard cut: only Veo's end cut (ratio 10.9) passes 8; a hand over the lens reaches 6.0. Extra faces: the rejected clip with the
# changed mother has 13 of ~24 sampled frames, approved clips at most 7. Motion under 4: 3 rejected clips (slideshow / nothing
# happens), the lowest approved clip has 4.6.
CUT_JUMP, CUT_RATIO, EXTRA_FACE_FRAMES, MIN_MOTION, MATCH = 25.0, 8.0, 10, 4.0, 0.6


def grid(fs, path, center=None, cols=4, cell=256, fps=24):
    """12 frames: 6 spread over the clip and 6 dense (every 2nd frame) around the moment of change, labelled with the time.
    With 12 even frames (0.45 s apart) the half-second change looked like a cut to the vision model (first calibration)."""
    n = len(fs)
    if center is None:
        center = n // 2
    spread = set(np.linspace(0, n - 1, 6).round().astype(int))
    dense = [min(n - 1, max(0, center + d)) for d in (-5, -3, -1, 1, 3, 5)]
    idx = sorted(set(dense) | spread)
    extra = [int(x) for x in np.linspace(0, n - 1, 24).round() if int(x) not in idx]   # overlap at the edges
    idx = sorted(idx + extra[: max(0, 12 - len(idx))])[:12]
    cells = []
    for k, i in enumerate(idx):
        c = cv2.resize(fs[i], (cell, cell))
        label = f"{k + 1}  {i / fps:.1f}s"
        cv2.putText(c, label, (8, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 5)
        cv2.putText(c, label, (8, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cells.append(c)
    rows = [np.hstack(cells[r * cols:(r + 1) * cols]) for r in range(len(cells) // cols)]
    cv2.imwrite(path, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
    return path


JUDGE = """You check one AI-generated clip for a family's growing-up video. The image is a 4x3 grid of 12 frames in time order,
numbered and timed (6 spread over the clip, 6 close together around the moment of change). Frame 1 is the earlier photo of a
child, frame 12 the later photo of the same child, older, often in another place, other clothes and with other people around.
How these clips are MEANT to work (this is correct, do not count it as a fault): the child does one natural action; while the
face is briefly hidden, turned away, blurred by motion or covered (hand, toy, cup, roll, camera move), age, hair, clothes, people
and place ALL change at once, within about half a second; then the shot settles on the later photo. A fast change at that moment
is the method, not a cut. People and clothes in the later photo are naturally different from the earlier photo.
The instructions the video model got:
---
{prompt}
---
Fail only on real faults you can see. Fields:
"subject_ok": false if the person who turns into the later child is clearly another person than the subject the instructions
     name (e.g. the wrong one of two children),
"real_transition": false only if: nothing moves and the picture just switches (a slideshow), or the two photos are visibly
     blended on top of each other for several frames (a crossfade with ghost images), or the scene jumps with no action, no
     motion and nothing hiding the face at that moment, or the motion is chaotic (people fall, melt, merge),
"face_ok": false if a face that is in clear view (not motion-blurred, not partly covered) is doubled, see-through or deformed,
"others_ok": false if a person changes while in clear view in a way that matches neither photo (invented hair or hairstyle,
     another face), or a person or big object appears that is in neither photo,
"pass": true if all four are true,
"issues": short list of the real faults, with frame numbers."""


def center_of_change(fs):
    small = [cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), (64, 64)).astype(np.float32) for f in fs]
    return int(np.argmax([np.abs(small[i + 1] - small[i]).mean() for i in range(len(small) - 1)]))


def vision_verdict(fs, prompt, work):
    g = grid(fs, os.path.join(work, "grid.jpg"), center_of_change(fs))
    AP.OUT = work
    return AP.vision(JUDGE.format(prompt=prompt or "(not available)"), [g])


def judge(clip, prompt="", photo_a=None, photo_b=None, work=None):
    work = work or os.path.splitext(clip)[0] + "-judge"
    os.makedirs(work, exist_ok=True)
    c, fs = code_checks(clip, photo_a, photo_b)
    problems = code_verdict(c)
    v = vision_verdict(fs, prompt, work)
    return {"pass": not problems and bool(v.get("pass")), "code": c, "code_problems": problems, "vision": v}


def calibrate(clips, meta, labels, out):
    meta, labels = json.load(open(meta)), json.load(open(labels))
    os.makedirs(out, exist_ok=True)
    cache = os.path.join(out, "vision-cache.json")
    if os.path.exists(cache):
        saved = json.load(open(cache)); AP.CACHE.update(saved["cache"]); AP.URLS.update(saved["urls"])
    rows = []
    for k, lab in labels.items():
        work = os.path.join(out, k)
        os.makedirs(work, exist_ok=True)
        c, fs = code_checks(os.path.join(clips, k + ".mp4"))
        g = grid(fs, os.path.join(work, "grid.jpg"), int(c["jump_at"] * (len(fs) - 1)))
        AP.OUT = out
        v = AP.vision(JUDGE.format(prompt=meta[k].get("prompt") or "(not available)"), [g])
        rows.append({"id": k, "owner": lab["pass"], "owner_why": lab["why"], "code": c, "code_problems": code_verdict(c), "vision": v})
        print(k, "owner", lab["pass"], "| vision", int(bool(v.get("pass"))), "| code", code_verdict(c) or "ok", flush=True)
    json.dump(rows, open(os.path.join(out, "calibration.json"), "w"), indent=1)
    for name, f in [("vision only", lambda r: bool(r["vision"].get("pass"))),
                    ("code only", lambda r: not r["code_problems"]),
                    ("code + vision", lambda r: bool(r["vision"].get("pass")) and not r["code_problems"])]:
        tp = sum(f(r) and r["owner"] for r in rows); fp = sum(f(r) and not r["owner"] for r in rows)
        fn = sum(not f(r) and r["owner"] for r in rows); tn = sum(not f(r) and not r["owner"] for r in rows)
        print(f"{name:14s} agree {tp + tn}/{len(rows)}  passed-but-owner-rejected {fp}  rejected-but-owner-passed {fn}")
    print("vision credits:", round(AP.credits, 2), AP.USED)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--calibrate":
        calibrate(*sys.argv[2:6])
    else:
        p = argparse.ArgumentParser()
        p.add_argument("clip"); p.add_argument("--prompt-file"); p.add_argument("--a"); p.add_argument("--b")
        a = p.parse_args()
        print(json.dumps(judge(a.clip, open(a.prompt_file).read() if a.prompt_file else "", a.a, a.b), indent=1))
