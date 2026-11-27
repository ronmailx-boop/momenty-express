"""Builds index.html for the Hebrew motivation video from the scene list below.
Times are in seconds and come from the voiceover transcript (see README.md)."""
import html, pathlib, re

DUR = 59.5
# scene: (start, end, mood, [(time, text, style)])  style: "" | "big" | "huge" | "soft"
# *word* = gold highlight, ~word~ = struck-through word
SCENES = [
    (1.2, 8.6, "night", [(2.0, "יום אחד תסתכלו אחורה,", "soft"), (3.6, "ותבינו שהרגע הכי קשה שלכם", ""), (6.7, "היה בעצם *ההתחלה*", "big")]),
    (8.6, 16.5, "night", [(8.9, "כל פעם שנפלתם,", "soft"), (10.4, "חשבתם שזה *הסוף*", ""), (12.15, "שאין לכם כבר כוח,", "soft"), (13.84, "שאולי זה פשוט לא בשבילכם", "soft")]),
    (16.5, 18.3, "rise", [(16.75, "אבל *קמתם*.", "huge")]),
    (18.3, 21.8, "night", [(18.5, "אולי לאט.", "big"), (19.85, "אולי עם דמעות בעיניים,", "")]),
    (21.8, 23.7, "rise", [(21.94, "אבל *קמתם*.", "huge")]),
    (23.7, 29.5, "night", [(23.94, "אף אחד לא ראה את הלילות", ""), (25.6, "שבהם המשכתם *להאמין*,", "big"), (27.3, "כשהכול בפנים אמר לכם לוותר", "soft")]),
    (29.5, 32.8, "night", [(29.77, "כוח אמיתי הוא לא", "soft"), (31.0, "לעולם לא ליפול", "big")]),
    (32.8, 38.2, "rise", [(32.93, "כוח אמיתי הוא *לקום*", "big"), (35.31, "עוד פעם אחת", "big"), (36.5, "יותר ממה שנפלתם", "soft")]),
    (38.2, 41.4, "dawn", [(38.57, "אז אם היום קשה לכם,", ""), (40.3, "*תזכרו:*", "big")]),
    (41.4, 45.5, "dawn", [(41.58, "אתם לא מתחילים ~מאפס~", "big"), (43.46, "אתם מתחילים *מניסיון*", "big")]),
    (45.5, 51.6, "dawn", [(45.81, "וכל צעד קטן שאתם עושים עכשיו", ""), (47.9, "הוא *הסיפור*", "big"), (49.3, "שיום אחד תספרו בגאווה", "soft")]),
    (51.6, DUR, "sun", [(51.97, "*אל* *תוותרו*.", "huge"), (53.58, "הטוב ביותר", "big"), (54.9, "עוד *לפניכם*", "huge")]),
]

def words(text):
    out = []
    for w in text.split(" "):
        cls = "w"
        if m := re.fullmatch(r"\*(.+)\*(.*)", w): w, cls = m[1] + m[2], "w gold"
        elif m := re.fullmatch(r"~(.+)~(.*)", w): w, cls = m[1] + m[2], "w strike"
        out.append(f'<span class="{cls}">{html.escape(w)}</span>')
    return " ".join(out)

clips, tl = [], []
for i, (s, e, mood, lines) in enumerate(SCENES):
    rows = "".join(f'<div class="line {st}" id="l{i}_{j}">{words(t)}</div>' for j, (t, _, st) in enumerate([(x[1], 0, x[2]) for x in lines]))
    clips.append(f'<div id="s{i}" class="scene clip {mood}" data-start="{s}" data-duration="{round(e - s, 2)}" data-track-index="1"><div class="inner" id="in{i}">{rows}</div></div>')
    tl.append(f'tl.fromTo("#s{i}", {{opacity:0}}, {{opacity:1, duration:0.35, ease:"sine.out"}}, {s});')
    for j, (t, _, st) in enumerate(lines):
        sel = f"#l{i}_{j} .w"
        if st == "huge":
            tl.append(f'tl.fromTo("{sel}", {{opacity:0, scale:0.6, y:60, filter:"blur(10px)"}}, {{opacity:1, scale:1, y:0, filter:"blur(0px)", duration:0.45, stagger:0.1, ease:"back.out(1.6)"}}, {t});')
        else:
            tl.append(f'tl.fromTo("{sel}", {{opacity:0, y:40, filter:"blur(12px)"}}, {{opacity:1, y:0, filter:"blur(0px)", duration:0.6, stagger:0.09, ease:"power3.out"}}, {t});')
    if any("strike" in words(x[1]) for x in lines):
        tl.append(f'tl.fromTo("#s{i} .strike", {{"--cut":0}}, {{"--cut":1, duration:0.5, ease:"power2.inOut"}}, {lines[0][0] + 1.2});')
        tl.append(f'tl.to("#l{i}_0", {{opacity:0.35, scale:0.92, duration:0.5}}, {lines[1][0] - 0.2});')
    tl.append(f'tl.to("#s{i}", {{opacity:0, scale:0.97, duration:0.4, ease:"sine.in"}}, {round(e - 0.4, 2)});' if e < DUR else "")
    tl.append(f'tl.fromTo("#in{i}", {{y:24}}, {{y:-24, duration:{round(e - s, 2)}, ease:"none"}}, {s});' if e < DUR else "")

# embers (deterministic pseudo-random)
seed = 7
def rnd():
    global seed
    seed = (seed * 1103515245 + 12345) % 2**31
    return seed / 2**31
embers = []
for k in range(36):
    x, size, d0, sp = rnd() * 1080, 4 + rnd() * 10, rnd() * 10, 9 + rnd() * 10
    embers.append(f'<i class="ember" id="e{k}" style="left:{x:.0f}px;width:{size:.1f}px;height:{size:.1f}px"></i>')
    n = int(DUR // sp) + 2
    for r in range(n):
        st = r * sp - d0
        if st > DUR: break
        tl.append(f'tl.fromTo("#e{k}", {{y:2000, x:0, opacity:0}}, {{y:-120, x:{(rnd() - 0.5) * 220:.0f}, opacity:1, duration:{sp:.2f}, ease:"none", immediateRender:false}}, {max(st, 0):.2f});' if st >= 0 else
                  f'tl.fromTo("#e{k}", {{y:{2000 - 2120 * (-st / sp):.0f}, opacity:1}}, {{y:-120, duration:{sp + st:.2f}, ease:"none"}}, 0);')
stars = "".join(f'<i class="star" style="left:{rnd()*1080:.0f}px;top:{rnd()*1300:.0f}px;width:{1.5+rnd()*3:.1f}px;height:{1.5+rnd()*3:.1f}px;opacity:{0.3+rnd()*0.7:.2f}"></i>' for _ in range(90))

page = pathlib.Path(__file__).with_name("template.html").read_text(encoding="utf-8")
page = page.replace("{{DUR}}", str(DUR)).replace("{{CLIPS}}", "\n      ".join(clips)).replace("{{EMBERS}}", "".join(embers)).replace("{{STARS}}", stars).replace("{{TL}}", "\n      ".join(x for x in tl if x))
pathlib.Path(__file__).parent.parent.joinpath("index.html").write_text(page, encoding="utf-8")
print("ok", len(tl), "tweens")
