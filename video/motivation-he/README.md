# סרטון מוטיבציה "אבל קמתם" (עברית, 9:16, 59.5 שניות)

סרטון בקוד: HyperFrames 0.9.26 (HTML + GSAP). לילה שהופך לזריחה, טקסט קינטי בעברית.

- **קריינות:** ElevenLabs, הקול "Nimrod - Warm and Confident" (`ZiofZHcEBTn5sRySe5h8`), מודל `eleven_v4`.
  בין המשפטים נוספו הפסקות נשימה (`vo.py` בסשן; הזמנים בטבלת `SCENES` ב-`tools/build_html.py`).
- **מוזיקה:** Suno V5 (דרך kie.ai), אינסטרומנטלי: emotional cinematic, piano intro, strings, uplifting build. 60 השניות הראשונות, עם ducking מתחת לקול.
- `assets/soundtrack.mp3` (קול + מוזיקה, loudnorm ‎-14 LUFS) לא נשמר ב-git.

## בנייה
```bash
python3 tools/build_html.py                     # tools/template.html + SCENES -> index.html
npx --yes hyperframes@0.9.26 check
npx --yes hyperframes@0.9.26 snapshot --at 7.5,17.4,27,44.5,57
npx --yes hyperframes@0.9.26 render -q delivery -o ../out/motivation-he.mp4
```

## התסריט
יום אחד תסתכלו אחורה, ותבינו שהרגע הכי קשה שלכם… היה בעצם ההתחלה.
כל פעם שנפלתם, חשבתם שזה הסוף. שאין לכם כבר כוח… שאולי זה פשוט לא בשבילכם.
אבל קמתם. אולי לאט. אולי עם דמעות בעיניים. אבל קמתם.
אף אחד לא ראה את הלילות שבהם המשכתם להאמין, כשהכול בפנים אמר לכם לוותר.
כוח אמיתי הוא לא לעולם לא ליפול. כוח אמיתי הוא לקום… עוד פעם אחת יותר ממה שנפלתם.
אז אם היום קשה לכם… תזכרו: אתם לא מתחילים מאפס. אתם מתחילים מניסיון.
וכל צעד קטן שאתם עושים עכשיו… הוא הסיפור שיום אחד תספרו בגאווה.
אל תוותרו. הטוב ביותר… עוד לפניכם.
