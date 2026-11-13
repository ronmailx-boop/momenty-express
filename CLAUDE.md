# Project Instructions for Claude Code

אנחנו עובדים דרך Claude Code. כל השינויים נכתבים ונשמרים ישירות ב-Repository.

## חוקי זיכרון והמשכיות בין שיחות (חובה)

- ניהול הזיכרון מתבצע דרך קובץ בשם `PROJECT_STATE.md` בשורש ה-Repository.
- בתחילת כל שיחה חדשה, קרא את `PROJECT_STATE.md` כדי לדעת איפה הפסקנו ומה הסטטוס הנוכחי.
- עדכון בזמן אמת: בכל פעם שאתה משלים משימה או כותב קוד, עדכן מיד את `PROJECT_STATE.md` וסמן `[x]` על המשימה שהושלמה.
- סיום שיחה: אם אגיד "ביי", "נמשיך מחר" או "תסכם" — עדכן את הסעיף "Current Focus" בקובץ עם הנקודה המדויקת שבה הפסקנו והצעד הבא לביצוע.
- ניהול Context: בסיום שלב/פיצ'ר משמעותי (ולא רק כשה-context מתמלא אוטומטית), עדכן קודם את `PROJECT_STATE.md` ואז הצע להריץ `/compact` עם הנחיה ממוקדת (למשל: שמור על רשימת הקבצים ששונו, המשימות הפתוחות וההחלטות האחרונות). אל תמתין ל-compact האוטומטי (95%) כברירת מחדל.

## כללי פיתוח, עיצוב וביצועים

- כל הקוד חייב להיות מותאם לנייד (Mobile-First).
- תמיכה מלאה בעברית ו-RTL.
- כשמבקשים ממך ליצור תוכנית עבודה (Plan), הצג רק תוכנית מפורטת ואל תבצע שינויי קוד גדולים עד לקבלת אישור מפורש.
- **עיצוב וקוד נקי:** שמור על HTML נקי וקריא. אל תוסיף ARIA attributes "כברירת מחדל" או בלי סיבה פונקציונלית ברורה — אבל כן הוסף אותם במקומות שבהם הם נדרשים בפועל לנגישות אמיתית (טפסים, כפתורי אייקון ללא טקסט, הודעות שגיאה דינמיות, מודלים, ניווט מקלדת). המטרה היא לא "לנפח" קוד סתם — לא להתעלם מנגישות אמיתית, במיוחד לאור דרישת ה-IS 5568 למטה.
- **ביצועים וניהול שגיאות:** שמור על קוד קל משקל, ותפוס שגיאות רשת/שרת עם הודעה ברורה למשתמש בעברית.
- **הודעות Commit:** תאר הודעות Commit קצרות באנגלית (למשל `feat:...`, `fix:...`).

## כללי אבטחה וסודות (Security Rules)

**חשוב: ההתייחסות שונה בין Backend לבין אפליקציות סטטיות — אל תערבב בין השניים.**

### Backend / GitHub Actions (Render, סקרייפרים, פונקציות שרת)
- לעולם אל תשתול מפתחות אבטחה, סיסמאות או API Keys בקוד הגלוי.
- השתמש במשתני סביבה: `.env` מקומי (עם `.env` ב-`.gitignore`) ו-GitHub Secrets / Render Environment Variables בפריסה.
- צור קובץ `.env.example` שמעלים ל-GitHub עם שמות המשתנים בלבד, ללא ערכים אמיתיים (למשל `FIREBASE_API_KEY=your_key_here`).

### אפליקציות סטטיות בצד-לקוח (GitHub Pages + Firebase Web SDK)
- מפתחות ה-Firebase Web SDK (`apiKey`, `authDomain` וכו') **חשופים מטבעם** בקוד הצד-לקוח — זו התנהגות תקנית של Firebase ולא פגם אבטחה.
- ההגנה האמיתית היא **Firestore/Storage Security Rules**, לא הסתרת המפתחות. אל תציע להעביר אותם ל-`.env` או ל-build step בפרויקט סטטי — זה לא רלוונטי ל-GitHub Pages.
- אם משהו כן צריך להישאר סודי אמת (מפתח API של שירות צד-שלישי בתשלום, טוקן עם הרשאות כתיבה רחבות) — הוא לא שייך לקוד קליינט בכלל, גם לא ב-`.env`; הוא צריך לעבור דרך Cloud Function / Backend.

### סניטציה ואבטחת קלט
- בצע ניקוי וסניטציה לכל קלט שמגיע מהמשתמש לפני שמירתו ב-Firebase / LocalStorage או הצגתו במסך (מניעת XSS).

## Legal & Compliance Documents

- **Location:** All legal documents must be stored in `docs/legal/`.
- **Required Files:**
  - `docs/legal/privacy-policy.md` (Privacy Policy - Israeli Law & GDPR compliant)
  - `docs/legal/terms-of-service.md` (Terms of Use)
  - `docs/legal/cookie-policy.md` (Cookie Policy)
  - `docs/legal/accessibility-statement.md` (Accessibility Statement - IS 5568 / WCAG 2.1 AA)
- **Language & Formatting:** Written in formal Hebrew, formatted in clean Markdown with placeholders like `[PLACEHOLDER]` where specific dynamic context is needed.

## פריסה ל-Cloudflare ודומיין

- פריסה ל-Cloudflare Workers, חיבור `*.vplusstudio.app`, כתובת ה-workers.dev ותיקוני Service Worker / PWA —
  דרך ה-Skill `vplus-deploy` (נטען אוטומטית בכל סשן מחשבון claude.ai; ההוראות המלאות, הלקחים והתבניות בתוכו).
- עובדות קבועות: Account ID ‏`1c9c1dd0e8a1d80f324b974ae6a617fb`; פריסה רק דרך GitHub Actions + wrangler 4 + ה-Secret
  `CLOUDFLARE_API_TOKEN` (רק המשתמש יוצר ומוסיף אותו — לא לבקש אותו בצ'אט); לא Cloudflare Pages ולא "Connect GitHub".
- המקור של ה-Skill: הריפו `ronmailx-boop/vplus-skills`, תיקייה `skills/vplus-deploy/`.

## Google Play, YouTube וסרטוני פרומו

- כל העבודה מול Play Console (העלאת AAB, דף החנות, צילומי מסך, סרטון בדף החנות) ומול YouTube, וגם הכנת סרטון פרומו —
  דרך ה-Skill `vplus-publishing` (נטען אוטומטית בכל סשן מחשבון claude.ai; ההוראות המלאות נטענות רק כשמשתמשים בו).
- המקור של ה-Skill: הריפו `ronmailx-boop/vplus-skills`, תיקייה `skills/vplus-publishing/`.
- החלופה (fastlane / GitHub Actions עם Secrets לכל ריפו) נמצאת בתוך ה-Skill: `references/fallback-*.md`.
- לפני כל שינוי ב-Play או ב-YouTube: להראות לבעלים בדיוק מה ישתנה ולחכות לאישור.
