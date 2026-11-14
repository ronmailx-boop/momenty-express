#!/usr/bin/env python3
"""Personal song for a clip: lyrics file -> KIE Suno (2 versions) -> optional transcription -> video with the new song.

Usage:
  python3 tools/make_song.py OUT --lyrics lyrics.txt --title "..." --style "..." [--gender f|m]
                             [--video clip.mp4 | --duration 58] [--model V6] [--shift 0.0] [--no-transcribe]
  python3 tools/make_song.py OUT --mux-only --video clip.mp4 [--shift S]   # re-mux songs already in OUT

OUT gets song1.mp3, song2.mp3, words1.json, words2.json (word timestamps, Hebrew), clip1.mp4, clip2.mp4, task.json.
--shift S: positive = the song starts S seconds later in the video, negative = cut S seconds from the song start
(used to land a lyric on the moment it describes). The video stream is never re-encoded; the song fades out over 2 s.
KIE auth is injected by the session proxy. Cost: 12 credits (~$0.06) per call, 2 versions, ~20-40 s.
"""
import argparse, json, os, subprocess, sys, time, urllib.request

API = "https://api.kie.ai"


def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method,
                               headers={"Content-Type": "application/json", "Authorization": "Bearer x"})
    for i in range(4):
        try:
            with urllib.request.urlopen(r, timeout=60) as f:
                return json.loads(f.read())
        except Exception as e:  # 502s happen; retry
            if i == 3:
                raise
            print("retry:", e, file=sys.stderr)
            time.sleep(3 * (i + 1))


def duration_of(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path])
    return float(out)


def generate(a, out):
    lyrics = open(a.lyrics, encoding="utf-8").read().strip()
    dur = round(duration_of(a.video)) if a.video and not a.duration else a.duration
    body = {"model": "ai-music-api/generate", "input": {
        "custom_mode": True, "instrumental": False, "model": a.model, "title": a.title,
        "lyrics": lyrics, "style": a.style, "vocal_gender": a.gender, "duration": int(dur)}}
    r = req("POST", "/api/v1/jobs/createTask", body)
    tid = (r.get("data") or {}).get("taskId")
    if not tid:
        sys.exit(f"createTask failed: {r}")
    print("task", tid, "duration", dur)
    t0 = time.time()
    while True:
        time.sleep(5)
        d = req("GET", f"/api/v1/jobs/recordInfo?taskId={tid}").get("data") or {}
        st = d.get("state")
        if st == "success":
            break
        if st == "fail":
            sys.exit(f"failed: {d.get('failMsg')}")
        if time.time() - t0 > 600:
            sys.exit("timeout")
    res = d.get("resultJson") or d.get("response")
    if isinstance(res, str):
        res = json.loads(res)
    json.dump({"taskId": tid, "seconds": round(time.time() - t0), "result": res, "body": body},
              open(os.path.join(out, "task.json"), "w"), ensure_ascii=False, indent=1)
    items = (res.get("data") if isinstance(res, dict) else None) or (res.get("resultUrls") if isinstance(res, dict) else None) or []
    for i, it in enumerate(items[:2], 1):
        url = it.get("audio_url") if isinstance(it, dict) else it
        urllib.request.urlretrieve(url, os.path.join(out, f"song{i}.mp3"))
        print(f"song{i}.mp3", round(duration_of(os.path.join(out, f"song{i}.mp3")), 1), "s")
    print("ready in", round(time.time() - t0), "s")


def transcribe(out):
    from faster_whisper import WhisperModel
    m = WhisperModel("small", device="cpu", compute_type="int8")
    for i in (1, 2):
        p = os.path.join(out, f"song{i}.mp3")
        if not os.path.exists(p):
            continue
        segs, _ = m.transcribe(p, language="he", word_timestamps=True, vad_filter=False)
        lines = [{"start": round(s.start, 1), "end": round(s.end, 1), "text": s.text.strip()} for s in segs]
        json.dump(lines, open(os.path.join(out, f"words{i}.json"), "w"), ensure_ascii=False, indent=1)
        print(f"--- song{i}")
        for l in lines:
            print(f"{l['start']:5.1f}-{l['end']:5.1f}  {l['text']}")


def mux(out, video, shift):
    vd = duration_of(video)
    for i in (1, 2):
        p = os.path.join(out, f"song{i}.mp3")
        if not os.path.exists(p):
            continue
        pre = f"adelay={int(shift * 1000)}:all=1," if shift > 0 else (f"atrim=start={-shift},asetpts=PTS-STARTPTS," if shift < 0 else "")
        af = f"{pre}apad,atrim=0:{vd},afade=t=out:st={vd - 2}:d=2"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", p, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-af", af, "-c:a", "aac", "-b:a", "192k", "-shortest", os.path.join(out, f"clip{i}.mp4")], check=True)
        print(f"clip{i}.mp4")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--lyrics"); ap.add_argument("--title", default="Song"); ap.add_argument("--style", default="")
    ap.add_argument("--gender", default="f"); ap.add_argument("--model", default="V6")
    ap.add_argument("--video"); ap.add_argument("--duration", type=int)
    ap.add_argument("--shift", type=float, default=0.0)
    ap.add_argument("--mux-only", action="store_true"); ap.add_argument("--no-transcribe", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if not a.mux_only:
        generate(a, a.out)
        if not a.no_transcribe:
            transcribe(a.out)
    if a.video:
        mux(a.out, a.video, a.shift)
