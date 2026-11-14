#!/usr/bin/env python3
"""Phase 1, stage C: one command, photos -> finished growing-up video, nobody in the loop.

  1 crop      square photos centred on the child's face (align_faces.py; photo.jpg@x,y = the child tapped in a group photo)
  2 plan      describe photos, pick strategy / hiding move, write prompts (auto_plan.py, vision model on KIE)
  3 generate  all transitions in parallel on Kling 3.0 Std via KIE; RE-SEND RULE (PROJECT_STATE.md); a content-filter
              block gets one reworded prompt
  4 judge     code checks + vision checklist (judge.py)
  5 retry     a rejected clip gets ONE new clip with another hiding move, judged again
  6 fallback  still rejected (or failed twice): a local transition, push-in on the face, white flash, pull-out (no AI, free)
  7 assemble  guidelines section 8: drop each clip's first frame, speed 4 s x1.3 / 5-6 s x1.5, hold the last photo 1.2 s,
              fade to black 0.8 s -> OUT/video.mp4, and OUT/report.json with the numbers phase 1 measures

State is saved in OUT/state.json after every step, so a re-run resumes and never pays twice for the same clip.

  python3 run_set.py OUT photo1.jpg photo2.jpg@0.42,0.44 ... [--max-credits N]
  python3 run_set.py OUT --use-clips DIR photos...      # dry run: take clips t<n>.mp4 from DIR instead of Kling (no video cost)
"""
import argparse, json, os, re, statistics, subprocess, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_faces, auto_plan as AP, judge as J, kie_compare as K

CREDITS_PER_S = 15.1          # Kling 3.0 Std 720p, no sound (guidelines section 1)
HEDGE_AFTER = 300             # re-send rule: never before 5 minutes
FPS = 24


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


class Run:
    def __init__(self, out, args):
        self.out, self.args = out, args
        self.path = os.path.join(out, "state.json")
        self.st = json.load(open(self.path)) if os.path.exists(self.path) else {"started": time.time(), "clips": {}}

    def save(self):
        json.dump(self.st, open(self.path, "w"), indent=1)

    # 1 -------------------------------------------------------------------------------------------------------------
    def crop(self, photos):
        sq = os.path.join(self.out, "sq")
        os.makedirs(sq, exist_ok=True)
        files, notes = [], []
        for i, arg in enumerate(photos, 1):
            path, _, pt = arg.partition("@")
            dst = os.path.join(sq, f"photo{i}-sq.jpg")
            if not os.path.exists(dst):
                img, note, n = align_faces.crop(path, tuple(float(v) for v in pt.split(",")) if pt else None)
                import cv2
                cv2.imwrite(dst, cv2.resize(img, (align_faces.SIZE, align_faces.SIZE), interpolation=cv2.INTER_LANCZOS4),
                            [cv2.IMWRITE_JPEG_QUALITY, 94])
                notes.append({"photo": i, "faces": n, "note": note, "tapped": bool(pt)})
                if n == 0:
                    log(f"photo {i}: NO FACE FOUND, centre crop")
                elif n > 1 and not pt:
                    log(f"photo {i}: {n} faces and no tap - the largest face was taken")
            files.append(dst)
        self.st.setdefault("photo_checks", notes)
        self.st["photos"] = files
        self.save()
        return files

    # 3 -------------------------------------------------------------------------------------------------------------
    def submit(self, key, t, prompt, seconds):
        """Send one clip. Returns the task id, or None (refused: content filter, no credits...)."""
        if self.args.use_clips:
            return f"local-{key}"
        spent = sum(c.get("credits", 0) for c in self.st["clips"].values())
        if spent + seconds * CREDITS_PER_S > self.args.max_credits:
            log(f"{key}: not sent, the run would pass --max-credits {self.args.max_credits}")
            return None
        urls = self.st.setdefault("urls", {})
        for p in (self.st["photos"][t - 1], self.st["photos"][t]):
            if p not in urls:
                urls[p] = K.upload(p)
        body = {"model": "kling-3.0/video", "input": {
            "prompt": prompt, "image_urls": [urls[self.st["photos"][t - 1]], urls[self.st["photos"][t]]], "sound": False,
            "duration": str(seconds), "mode": "std", "aspect_ratio": "1:1", "multi_shots": False}}
        for attempt in range(4):
            try:
                r = K.req("POST", "/api/v1/jobs/createTask", body)
                break
            except Exception as e:                      # KIE 502s: retry
                log(f"{key}: submit error {e}, retrying"); time.sleep(5 * (attempt + 1))
        else:
            return None
        tid = (r.get("data") or {}).get("taskId")
        if not tid:
            log(f"{key}: refused {r.get('code')} {r.get('msg')}")
        return tid

    def new_clip(self, key, t, prompt, seconds, step):
        c = {"t": t, "prompt": prompt, "seconds": seconds, "step": step, "submitted": time.time(), "copies": []}
        tid = self.submit(key, t, prompt, seconds)
        c["copies"].append({"taskId": tid, "submitted": time.time()}) if tid else c.update(state="refused")
        self.st["clips"][key] = c
        self.save()

    def poll(self, keys):
        """Wait until every clip in `keys` is done (success / fail / refused), applying the re-send rule."""
        while True:
            open_ = []
            for k in keys:
                c = self.st["clips"][k]
                if c.get("state") in ("success", "fail", "refused"):
                    continue
                open_.append(k)
                for cp in c["copies"]:
                    if cp.get("state") in ("success", "fail"):
                        continue
                    if cp["taskId"].startswith("local-"):
                        src = os.path.join(self.args.use_clips, f"t{c['t']}.mp4")
                        cp.update(state="success" if os.path.exists(src) else "fail", file=src, credits=0, wait=0)
                        continue
                    try:
                        d = K.req("GET", f"/api/v1/jobs/recordInfo?taskId={cp['taskId']}").get("data") or {}
                    except Exception as e:
                        log(f"{k}: status error {e}"); continue
                    if d.get("state") in ("success", "fail"):
                        cp.update(state=d["state"], wait=round(time.time() - cp["submitted"]),
                                  credits=d.get("creditsConsumed") or 0, error=d.get("failMsg"))
                        if d["state"] == "success":
                            url = (json.loads(d.get("resultJson") or "{}").get("resultUrls") or [None])[0]
                            cp["file"] = os.path.join(self.out, f"{k}.mp4")
                            try:
                                urllib.request.urlretrieve(url, cp["file"])
                            except Exception as e:
                                cp["state"] = None; log(f"{k}: download error {e}")
                done = [cp for cp in c["copies"] if cp.get("state") == "success"]
                if done:
                    c.update(state="success", file=done[0]["file"], ready=round(time.time() - c["submitted"]))
                elif all(cp.get("state") == "fail" for cp in c["copies"]):
                    c.update(state="fail", error=c["copies"][-1].get("error"))
                c["credits"] = sum(cp.get("credits") or 0 for cp in c["copies"])
                if c.get("state"):
                    log(f"{k}: {c['state']} after {c.get('ready', '-')} s {c.get('error') or ''}")
            self.resend(keys)
            self.save()
            if not open_:
                return
            time.sleep(10)

    def resend(self, keys):
        """RE-SEND RULE: only a clip that lags far behind the others of the same batch; max 1 per clip, 20% of the batch."""
        clips = [self.st["clips"][k] for k in keys]
        finished = [c["ready"] for c in clips if c.get("ready")]
        budget = max(1, int(len(clips) * 0.2)) - sum(len(c["copies"]) - 1 for c in clips)
        for k in keys:
            c = self.st["clips"][k]
            if c.get("state") or len(c["copies"]) > 1 or budget <= 0 or not finished:
                continue
            waited = time.time() - c["submitted"]
            if len(finished) * 2 >= len(clips) and waited > max(HEDGE_AFTER, 2 * statistics.median(finished)):
                tid = self.submit(k, c["t"], c["prompt"], c["seconds"])
                if tid:
                    c["copies"].append({"taskId": tid, "submitted": time.time()}); budget -= 1
                    log(f"{k}: re-sent after {round(waited)} s")

    # 6 -------------------------------------------------------------------------------------------------------------
    def fallback(self, t):
        """Local transition, no AI: slow push-in on photo A's face, white flash, pull-out from photo B (faces are aligned)."""
        a, b = self.st["photos"][t - 1], self.st["photos"][t]
        dst = os.path.join(self.out, f"t{t}-fallback.mp4")
        # one input frame -> zoompan makes d frames itself (a looped input would restart the zoom on every frame)
        z = "zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih*0.38-(ih/zoom*0.38)':d=38:s=960x960:fps=24"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a, "-i", b, "-filter_complex",
                        f"[0]scale=1920:1920,{z.format(z='1+0.35*on/37')},setpts=PTS-STARTPTS[a];"
                        f"[1]scale=1920:1920,{z.format(z='1.35-0.35*on/37')},setpts=PTS-STARTPTS[b];"
                        "[a][b]xfade=transition=fadewhite:duration=0.5:offset=1.0,format=yuv420p",
                        "-r", "24", dst], check=True)
        return dst

    # 7 -------------------------------------------------------------------------------------------------------------
    def assemble(self, parts):
        work = os.path.join(self.out, "parts")
        os.makedirs(work, exist_ok=True)
        files = []
        for n, (f, seconds, kind) in enumerate(parts):
            speed = 1.0 if kind == "fallback" else (1.3 if seconds <= 4 else 1.5)
            trim = "" if n == 0 else "trim=start_frame=1,setpts=PTS-STARTPTS,"
            dst = os.path.join(work, f"{n:02d}.mp4")
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", f, "-an", "-vf",
                            f"{trim}setpts=PTS/{speed},fps={FPS},scale=960:960,format=yuv420p", "-c:v", "libx264", "-crf", "18", dst],
                           check=True)
            files.append(dst)
        hold = os.path.join(work, "hold.mp4")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-loop", "1", "-t", "2.0", "-i", self.st["photos"][-1], "-vf",
                        f"scale=960:960,fps={FPS},fade=t=out:st=1.2:d=0.8,format=yuv420p", "-c:v", "libx264", "-crf", "18", hold],
                       check=True)
        files.append(hold)
        lst = os.path.join(work, "list.txt")
        open(lst, "w").write("".join(f"file '{os.path.abspath(f)}'\n" for f in files))
        video = os.path.join(self.out, "video.mp4")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                        "-movflags", "+faststart", video], check=True)
        return video


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("photos", nargs="+")
    ap.add_argument("--max-credits", type=float, default=1200, help="stop sending clips past this many Kling credits")
    ap.add_argument("--use-clips", help="dry run: clips t<n>.mp4 from this folder instead of Kling")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    run = Run(args.out, args)
    t0 = run.st["started"]

    photos = run.crop(args.photos)
    log(f"cropped {len(photos)} photos")
    plan, prompts = AP.make_plan(os.path.join(args.out, "plan"), photos)
    steps, n = plan["transitions"], len(photos) - 1

    # 3 generate everything in parallel
    first = [f"t{t}" for t in range(1, n + 1)]
    for t in range(1, n + 1):
        if f"t{t}" not in run.st["clips"]:
            run.new_clip(f"t{t}", t, prompts[t - 1], steps[t - 1]["seconds"], steps[t - 1])
    run.poll(first)

    # content-filter blocks: one reworded prompt
    used = [s["hide"] for s in steps if s["hide"]]
    for t in range(1, n + 1):
        c = run.st["clips"][f"t{t}"]
        if c["state"] in ("fail", "refused") and f"t{t}-reword" not in run.st["clips"]:
            step, prompt = AP.write_one(t - 1, photos, plan["photos"], plan["compares"], plan["gender"], used, None,
                                        note="The video service's content filter blocked the last wording. Write it again "
                                             "plainly: only the action, the expression and the camera; no words about the "
                                             "child's appearance.")
            run.new_clip(f"t{t}-reword", t, prompt, step["seconds"], step)
    run.poll([k for k in run.st["clips"] if k.endswith("-reword")])

    # 4 judge, 5 one retry with another hiding move
    def best(t):
        for k in (f"t{t}-retry", f"t{t}-reword", f"t{t}"):
            c = run.st["clips"].get(k)
            if c and c.get("state") == "success":
                return k, c
        return None, None

    def judged(k, c):
        if "verdict" not in c:
            v = J.judge(c["file"], c["prompt"], photos[c["t"] - 1], photos[c["t"]], work=os.path.join(args.out, "judge", k))
            c["verdict"] = {"pass": v["pass"], "code_problems": v["code_problems"], "vision": v["vision"]}
            run.save()
            log(f"{k}: judge {'PASS' if v['pass'] else 'FAIL'} {v['code_problems']} {v['vision'].get('issues', [])}")
        return c["verdict"]["pass"]

    retry = []
    for t in range(1, n + 1):
        k, c = best(t)
        if k and not judged(k, c) and f"t{t}-retry" not in run.st["clips"]:
            step, prompt = AP.write_one(t - 1, photos, plan["photos"], plan["compares"], plan["gender"], used, None,
                                        exclude=[c["step"]["hide"]] if c["step"]["hide"] else ["in_place"])
            run.new_clip(f"t{t}-retry", t, prompt, step["seconds"], step)
            retry.append(f"t{t}-retry")
    run.poll(retry)

    # 6 fallback, 7 assemble
    parts, outcome = [], {}
    for t in range(1, n + 1):
        k, c = best(t)
        if k and judged(k, c):
            parts.append((c["file"], c["seconds"], "clip")); outcome[t] = "first try" if k == f"t{t}" else k.split("-")[1]
        else:
            parts.append((run.fallback(t), 3.2, "fallback")); outcome[t] = "fallback"
            log(f"t{t}: fallback transition used")
    video = run.assemble(parts)

    credits = sum(c.get("credits", 0) for c in run.st["clips"].values()) + AP.credits
    report = {"video": video, "transitions": n,
              "first_try_pass": sum(v == "first try" for v in outcome.values()),
              "after_retry": sum(v in ("retry", "reword") for v in outcome.values()),
              "fallback": sum(v == "fallback" for v in outcome.values()),
              "outcome": outcome, "minutes_to_video": round((time.time() - t0) / 60, 1),
              "kling_credits": round(sum(c.get("credits", 0) for c in run.st["clips"].values()), 1),
              "vision_credits_this_session": round(AP.credits, 2), "total_credits": round(credits, 1),
              "usd": round(credits * 0.005, 2), "photo_checks": run.st.get("photo_checks"),
              "video_seconds": float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                                     "csv=p=0", video], capture_output=True, text=True).stdout or 0)}
    json.dump(report, open(os.path.join(args.out, "report.json"), "w"), indent=1)
    log(json.dumps({k: v for k, v in report.items() if k not in ("photo_checks", "outcome")}))


if __name__ == "__main__":
    main()
