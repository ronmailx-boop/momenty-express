#!/usr/bin/env python3
"""Run each transition (photo i -> photo i+1) through several KIE models and record cost and wait time.

The KIE key is injected by the session's network proxy (never stored here). State is kept in a JSON file so a
re-run never submits (and pays for) the same clip twice.

  python3 kie_compare.py prepare STATE.json photo1.jpg photo2.jpg ...   # square crops + upload to KIE
  python3 kie_compare.py submit  STATE.json [--only MODEL] [--transitions 1,2,3]
  python3 kie_compare.py poll    STATE.json                              # until every task ends; downloads clips
"""
import json, os, subprocess, sys, time, urllib.request, uuid

API = "https://api.kie.ai"
UPLOAD = "https://kieai.redpandaai.co"  # KIE file upload host
NEG = ("blur, distort, low quality, camera shake, jittery motion, flicker, morphing face, crossfade, dissolve, "
       "double exposure, transparent overlay")


def req(method, path, body=None, raw=None, headers=None, host=API):
    h = {"Authorization": "Bearer proxy-injected", **(headers or {})}
    data = raw
    if body is not None:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(host + path, data=data, method=method, headers=h)
    with urllib.request.urlopen(r, timeout=120) as resp:
        return json.loads(resp.read())


def square(src, dst, size=1080):
    # centre horizontally, 40% from the top vertically (as Momenty's full-frame crop), then scale
    vf = (f"crop='min(iw,ih)':'min(iw,ih)':'(iw-min(iw,ih))/2':'(ih-min(iw,ih))*0.4',"
          f"scale={size}:{size}")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-vf", vf, "-q:v", "2", dst], check=True)


def upload(path):
    boundary = uuid.uuid4().hex
    name = os.path.basename(path)
    parts = []
    for k, v in (("uploadPath", "momenty-express-test"), ("fileName", name)):
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\n'
                 f'Content-Type: image/jpeg\r\n\r\n'.encode() + open(path, "rb").read() + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    r = req("POST", "/api/file-stream-upload", host=UPLOAD, raw=b"".join(parts),
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    if not r.get("success", r.get("code") == 200):
        raise SystemExit(f"upload failed: {r}")
    return r["data"]["downloadUrl"]


def build(model, prompt, a, b):
    """Request body for one model, with photo a as the first frame and photo b as the last frame."""
    if model == "kling3-pro" or model == "kling3-std":
        return {"model": "kling-3.0/video", "input": {
            "prompt": prompt, "image_urls": [a, b], "sound": False, "duration": os.environ.get("KIE_SECONDS", "4"),
            "mode": "pro" if model == "kling3-pro" else "std", "aspect_ratio": "1:1", "multi_shots": False}}
    if model == "kling25-turbo":
        return {"model": "kling/v2-5-turbo-image-to-video-pro", "input": {
            "prompt": prompt, "image_url": a, "tail_image_url": b, "duration": "5",
            "negative_prompt": NEG, "cfg_scale": 0.5}}
    if model == "veo31-fast":
        return {"model": "veo-3-1", "input": {
            "prompt": prompt, "model": "veo3_fast", "image_urls": [a, b],
            "generation_type": "FIRST_AND_LAST_FRAMES_2_VIDEO", "aspect_ratio": "Auto",
            "resolution": "720p", "duration": 4}}
    if model == "kling4":
        return {"model": "kling-4.0/keyframe-to-video", "input": {
            "prompt": "Start exactly on @first_frame and end exactly on @last_frame. " + prompt,
            "duration": 4, "resolution": "720p", "aspect_ratio": "auto",
            "first_frame_url": a, "last_frame_url": b}}
    raise SystemExit(f"unknown model {model}")


LABELS = {"kling3-pro": "Kling 3.0 Pro (1080p)", "kling3-std": "Kling 3.0 Std (720p)",
          "kling25-turbo": "Kling 2.5 Turbo Pro", "veo31-fast": "Veo 3.1 Fast (720p)", "kling4": "Kling 4.0 (720p)"}


def main():
    cmd, state_path = sys.argv[1], sys.argv[2]
    st = json.load(open(state_path)) if os.path.exists(state_path) else {"photos": [], "tasks": []}
    save = lambda: json.dump(st, open(state_path, "w"), indent=1)
    if cmd == "prepare":
        out = os.path.dirname(os.path.abspath(state_path))
        for i, src in enumerate(sys.argv[3:], 1):
            dst = os.path.join(out, f"photo{i}-sq.jpg")
            square(src, dst)
            st["photos"].append({"n": i, "file": dst, "url": upload(dst)})
            print("uploaded", i)
        save()
    elif cmd == "submit":
        args = sys.argv[3:]
        models = args[args.index("--only") + 1].split(",") if "--only" in args else list(LABELS)
        trs = [int(x) for x in args[args.index("--transitions") + 1].split(",")] if "--transitions" in args \
            else list(range(1, len(st["photos"])))
        prompts = json.load(open(os.path.join(os.path.dirname(os.path.abspath(state_path)), "prompts.json")))
        for t in trs:
            a, b = st["photos"][t - 1]["url"], st["photos"][t]["url"]
            for m in models:
                if any(x["from"] == t and x["model"] == m and x.get("taskId") for x in st["tasks"]):
                    print("skip (already submitted)", t, m); continue
                r = req("POST", "/api/v1/jobs/createTask", build(m, prompts[t - 1], a, b))
                task = {"from": t, "model": m, "label": LABELS[m], "submitted": time.time(),
                        "taskId": (r.get("data") or {}).get("taskId"), "submitResponse": None if r.get("code") == 200 else r}
                st["tasks"] = [x for x in st["tasks"] if not (x["from"] == t and x["model"] == m)] + [task]; save()
                print(t, m, task["taskId"] or r)
                time.sleep(0.6)
    elif cmd == "poll":
        out = os.path.dirname(os.path.abspath(state_path))
        while True:
            pending = 0
            for x in st["tasks"]:
                if not x.get("taskId") or x.get("state") in ("success", "fail"):
                    continue
                d = req("GET", f"/api/v1/jobs/recordInfo?taskId={x['taskId']}").get("data") or {}
                x["state"] = d.get("state")
                if x["state"] in ("success", "fail"):
                    x["done"] = time.time()
                    ct, dt = d.get("createTime"), d.get("completeTime") or d.get("updateTime")
                    # KIE's own timestamps (ms) when given; a late poll would otherwise inflate the wait
                    x["seconds"] = round((dt - ct) / 1000) if ct and dt else round(x["done"] - x["submitted"])
                    x["costTime"] = d.get("costTime")
                    x["credits"] = d.get("creditsConsumed")
                    x["error"] = d.get("failMsg") or d.get("failCode")
                    if x["state"] == "success":
                        res = json.loads(d.get("resultJson") or "{}")
                        x["resultUrl"] = (res.get("resultUrls") or [None])[0]
                        if x["resultUrl"]:
                            x["file"] = os.path.join(out, f"t{x['from']}-{x['model']}.mp4")
                            try:
                                urllib.request.urlretrieve(x["resultUrl"], x["file"])
                            except Exception as e:  # keep polling the rest; re-run to retry the download
                                x["state"], x["downloadError"] = "downloadFailed", str(e)
                    print(x["from"], x["model"], x["state"], x.get("seconds"), "s", x.get("credits"), "cr", x.get("error") or "")
                else:
                    pending += 1
            save()
            if not pending:
                break
            time.sleep(15)


if __name__ == "__main__":
    main()
