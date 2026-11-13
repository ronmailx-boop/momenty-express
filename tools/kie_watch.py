#!/usr/bin/env python3
"""Poll a kie_compare state file and re-send a clip only when it lags far behind the others (see PROJECT_STATE.md, RE-SEND RULE):
at least half of the clips are done AND this clip waited > max(HEDGE_AFTER, 2 x median wait of the finished ones).
At most one re-send per clip, at most 20% of the run's clips; a failed (e.g. moderation) clip is re-sent once.
The first copy to succeed is kept (downloaded as t<from>-<model>.mp4); timings are real waits from our submit.

  KIE_SECONDS=5 python3 kie_watch.py STATE.json [HEDGE_AFTER=300]
"""
import json, os, statistics, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kie_compare as K

state_path = sys.argv[1]
hedge_after = int(sys.argv[2]) if len(sys.argv) > 2 else 300
out = os.path.dirname(os.path.abspath(state_path))
st = json.load(open(state_path))
prompts = json.load(open(os.path.join(out, "prompts.json")))
t0 = min(x["submitted"] for x in st["tasks"])
save = lambda: json.dump(st, open(state_path, "w"), indent=1)

while True:
    open_slots = 0
    for x in st["tasks"]:
        if x.get("final"):
            continue
        copies = [x] + x.get("hedges", [])
        for c in copies:
            if c.get("state") in ("success", "fail"):
                continue
            try:
                d = K.req("GET", f"/api/v1/jobs/recordInfo?taskId={c['taskId']}").get("data") or {}
            except Exception as e:  # KIE sometimes answers 502; try again next round
                print(f"T{x['from']} status check failed ({e}); retrying", flush=True)
                continue
            c["state"] = d.get("state")
            if c["state"] in ("success", "fail"):
                c["wait"] = round(time.time() - c["submitted"])
                c["credits"] = d.get("creditsConsumed")
                c["error"] = d.get("failMsg")
                if c["state"] == "success" and not x.get("final"):
                    url = (json.loads(d.get("resultJson") or "{}").get("resultUrls") or [None])[0]
                    f = os.path.join(out, f"t{x['from']}-{x['model']}.mp4")
                    urllib.request.urlretrieve(url, f)
                    x["final"] = {"taskId": c["taskId"], "file": f, "ready_at": round(time.time() - t0), "hedged": c is not x}
                    print(f"T{x['from']} ready at {x['final']['ready_at']} s (copy wait {c['wait']} s{', re-sent copy' if c is not x else ''})", flush=True)
        if x.get("final"):
            continue
        open_slots += 1
        waited = time.time() - x["submitted"]
        all_failed = all(c.get("state") == "fail" for c in copies)
        finished = [t["final"]["ready_at"] for t in st["tasks"] if t.get("final")]
        resent = sum(len(t.get("hedges", [])) for t in st["tasks"])
        lagging = (len(finished) * 2 >= len(st["tasks"])
                   and waited > max(hedge_after, 2 * statistics.median(finished)))
        budget_ok = resent < max(1, int(len(st["tasks"]) * 0.2))
        if ((lagging and not x.get("hedges")) or (all_failed and len(x.get("hedges", [])) < 1)) and budget_ok:
            a, b = st["photos"][x["from"] - 1]["url"], st["photos"][x["from"]]["url"]
            try:
                r = K.req("POST", "/api/v1/jobs/createTask", K.build(x["model"], prompts[x["from"] - 1], a, b))
            except Exception as e:
                print(f"T{x['from']} re-send failed ({e}); retrying", flush=True)
                continue
            tid = (r.get("data") or {}).get("taskId")
            if not tid:  # e.g. 402 insufficient credits: report, don't count it as a copy
                print(f"T{x['from']} re-send refused: {r.get('code')} {r.get('msg')}", flush=True)
                continue
            x.setdefault("hedges", []).append({"taskId": tid, "submitted": time.time()})
            why = "failed: " + str(copies[-1].get("error")) if all_failed else f"waiting {round(waited)} s"
            print(f"T{x['from']} re-sent ({why})", flush=True)
    save()
    if not open_slots:
        print("ALL READY at", max(x["final"]["ready_at"] for x in st["tasks"]), "s", flush=True)
        break
    time.sleep(10)
