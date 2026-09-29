# -*- coding: utf-8 -*-
"""
מאגר הידע של הכלי: מיקומים מוכרים ב-Windows שאפשר (או שאסור) לנקות,
עם הסבר מסודר לכל אחד.

רמות בטיחות (safety):
    safe     - בטוח למחוק. המערכת/התוכנה יוצרת מחדש את מה שהיא צריכה.
    caution  - אפשר למחוק, אבל יש מחיר או שצריך לבדוק קודם.
    windows  - אפשר לפנות מקום, אבל רק דרך כלי של Windows (לא מחיקה ידנית).
    keep     - לא למחוק. מוצג כדי להסביר למה התיקייה גדולה.

סוגי פעולה (action):
    clean    - הכלי מוחק את התוכן של הנתיבים (מדלג על קבצים נעולים).
    recycle  - ריקון סל המחזור.
    command  - פותח חלון פקודה עם הרשאות מנהל ומריץ פקודה קבועה של Windows.
    open     - פותח מסך הגדרות / כלי של Windows.
    none     - אין פעולה אוטומטית, רק הסבר.
"""

import os

import rules_en

HOME = os.path.expanduser("~")
SYS = os.environ.get("SystemDrive", "C:") + "\\"
WIN = os.environ.get("WINDIR", r"C:\Windows")
PD = os.environ.get("ProgramData", r"C:\ProgramData")
LAD = os.environ.get("LOCALAPPDATA", os.path.join(HOME, "AppData", "Local"))
AD = os.environ.get("APPDATA", os.path.join(HOME, "AppData", "Roaming"))

J = os.path.join

SAFETY_LABELS = {
    "safe": "בטוח למחוק",
    "caution": "בדוק לפני שמוחקים",
    "windows": "לפנות רק דרך Windows",
    "keep": "לא למחוק",
}

CATEGORIES = {
    "system": "קבצי מערכת זמניים",
    "browser": "דפדפנים",
    "apps": "תוכנות",
    "dev": "כלי פיתוח",
    "big": "קבצי מערכת גדולים",
}


def _chromium(base):
    """נתיבי מטמון של דפדפן מבוסס כרומיום (Chrome / Edge) לכל הפרופילים."""
    ud = J(base, "User Data", "*")
    return [J(ud, "Cache"), J(ud, "Code Cache"), J(ud, "GPUCache"),
            J(base, "User Data", "ShaderCache"), J(base, "User Data", "GrShaderCache")]


RULES = [
    # ------------------------------------------------------------------ system
    dict(
        id="user_temp", category="system", safety="safe", action="clean", min_age_days=1,
        title="קבצים זמניים של המשתמש",
        paths=[J(LAD, "Temp")],
        what="תיקייה שבה תוכנות שומרות קבצים זמניים בזמן עבודה: קבצי התקנה, קבצים מצורפים שנפתחו, חלקי עדכונים. "
             "רוב התוכנות לא מנקות אחריהן, ולכן התיקייה מתנפחת עם הזמן.",
        if_deleted="בטוח. תוכנות יוצרות מחדש את מה שהן צריכות. "
                   "הכלי מדלג על קבצים שנוצרו ב-24 השעות האחרונות ועל קבצים שנמצאים כרגע בשימוש, "
                   "כדי לא להפריע לתוכנה פתוחה או להתקנה שרצה עכשיו.",
        how="לחיצה על \"נקה\" מוחקת את התוכן לצמיתות, בלי לעבור דרך סל המחזור.",
    ),
    dict(
        id="win_temp", category="system", safety="safe", action="clean", admin=True, min_age_days=1,
        title="קבצים זמניים של Windows",
        paths=[J(WIN, "Temp")],
        what="הגרסה המערכתית של תיקיית הקבצים הזמניים. משמשת את Windows, שירותי רקע ומתקינים.",
        if_deleted="בטוח. אותו עיקרון כמו התיקייה הזמנית של המשתמש. קבצים נעולים וחדשים מדולגים.",
        how="דורש הפעלה של הכלי כמנהל (start-as-admin.bat).",
    ),
    dict(
        id="recycle_bin", category="system", safety="safe", action="recycle",
        title="סל המחזור",
        paths=[],
        what="קבצים שמחקת. הם עדיין תופסים מקום על הדיסק עד שהסל מתרוקן.",
        if_deleted="בטוח, בתנאי שאין בסל משהו שאתה רוצה לשחזר. אחרי הריקון אי אפשר לשחזר את הקבצים.",
        how="פתח את סל המחזור ובדוק שאין בו משהו חשוב, ואז לחץ \"רוקן\".",
    ),
    dict(
        id="wu_download", category="system", safety="safe", action="clean", admin=True,
        title="קבצי הורדה של Windows Update",
        paths=[J(WIN, "SoftwareDistribution", "Download")],
        what="קבצי עדכונים ש-Windows הוריד כדי להתקין. אחרי שהעדכון הותקן, אין בהם צורך.",
        if_deleted="בטוח. אם יש עדכון שעוד לא הותקן, Windows פשוט יוריד אותו מחדש.",
        how="דורש הרשאות מנהל. עדיף לא לנקות בזמן ש-Windows Update מתקין עדכון.",
    ),
    dict(
        id="delivery_opt", category="system", safety="safe", action="clean", admin=True,
        title="מטמון Delivery Optimization",
        paths=[J(WIN, "ServiceProfiles", "NetworkService", "AppData", "Local", "Microsoft", "Windows",
                 "DeliveryOptimization", "Cache"),
               J(WIN, "SoftwareDistribution", "DeliveryOptimization")],
        what="עותקים של עדכונים ש-Windows שומר כדי לשתף עם מחשבים אחרים ברשת.",
        if_deleted="בטוח. זה רק מטמון. העדכונים עצמם כבר מותקנים.",
        how="דורש הרשאות מנהל.",
    ),
    dict(
        id="error_reports", category="system", safety="safe", action="clean",
        title="דוחות שגיאה וקריסות",
        paths=[J(PD, "Microsoft", "Windows", "WER", "ReportArchive"),
               J(PD, "Microsoft", "Windows", "WER", "ReportQueue"),
               J(PD, "Microsoft", "Windows", "WER", "Temp"),
               J(LAD, "Microsoft", "Windows", "WER"),
               J(LAD, "CrashDumps")],
        what="דוחות ש-Windows יוצר כשתוכנה קורסת, כדי לשלוח למיקרוסופט.",
        if_deleted="בטוח. הדוחות כבר נשלחו או שלא ישמשו יותר. חלק מהנתיבים דורשים הרשאות מנהל.",
        how="לחיצה על \"נקה\".",
    ),
    dict(
        id="memory_dumps", category="system", safety="safe", action="clean", admin=True,
        title="קבצי זיכרון ממסכים כחולים (Dump)",
        paths=[J(WIN, "MEMORY.DMP"), J(WIN, "Minidump"), J(WIN, "LiveKernelReports"), J(SYS, "DUMP*.tmp")],
        what="תמונת זיכרון שנשמרת כשהמחשב קורס (מסך כחול). משמשת טכנאים לניתוח הקריסה.",
        if_deleted="בטוח, אלא אם אתה באמצע בירור של מסכים כחולים עם טכנאי. קובץ MEMORY.DMP יכול להגיע לכמה גיגה.",
        how="דורש הרשאות מנהל.",
    ),
    dict(
        id="win_logs", category="system", safety="safe", action="clean", admin=True, min_age_days=7,
        title="יומני התקנה של Windows (CBS)",
        paths=[J(WIN, "Logs", "CBS")],
        what="יומנים של רכיב ההתקנה של Windows. לפעמים מתנפחים לגיגה-בייטים בגלל תקלה בעדכון.",
        if_deleted="בטוח. אלה רק רישומי טקסט. הכלי מוחק רק יומנים בני יותר משבוע.",
        how="דורש הרשאות מנהל.",
    ),
    dict(
        id="thumbcache", category="system", safety="safe", action="clean",
        title="מטמון תמונות ממוזערות",
        paths=[J(LAD, "Microsoft", "Windows", "Explorer", "thumbcache_*.db"),
               J(LAD, "Microsoft", "Windows", "Explorer", "iconcache_*.db")],
        what="תמונות קטנות שסייר הקבצים שומר כדי להציג תצוגה מקדימה של תמונות וסרטונים.",
        if_deleted="בטוח. הסייר ייצור אותן מחדש. בפעם הראשונה פתיחת תיקייה עם הרבה תמונות תהיה קצת איטית. "
                   "קבצים שהסייר מחזיק פתוחים כרגע ידולגו.",
        how="לחיצה על \"נקה\".",
    ),
    dict(
        id="inetcache", category="system", safety="safe", action="clean",
        title="מטמון אינטרנט של Windows",
        paths=[J(LAD, "Microsoft", "Windows", "INetCache")],
        what="מטמון של רכיבי אינטרנט ישנים של Windows ושל תוכנות שמשתמשות בהם.",
        if_deleted="בטוח. זה מטמון בלבד.",
        how="לחיצה על \"נקה\".",
    ),
    dict(
        id="shader_cache", category="system", safety="safe", action="clean",
        title="מטמון גרפי (DirectX ו-NVIDIA)",
        paths=[J(LAD, "D3DSCache"), J(LAD, "NVIDIA", "DXCache"), J(LAD, "NVIDIA", "GLCache"),
               J(LAD, "NVIDIA Corporation", "NV_Cache"), J(LAD, "AMD", "DxCache"), J(LAD, "AMD", "GLCache")],
        what="קוד גרפי מקומפל ששומרים משחקים ותוכנות גרפיות כדי לעלות מהר יותר.",
        if_deleted="בטוח. בפעם הראשונה שתפעיל משחק אחרי הניקוי הוא ייטען קצת לאט יותר, ואז המטמון ייבנה מחדש.",
        how="לחיצה על \"נקה\".",
    ),
    dict(
        id="gpu_installers", category="system", safety="safe", action="clean", admin=True,
        title="קבצי התקנה ישנים של דרייבר המסך",
        paths=[J(PD, "NVIDIA Corporation", "Downloader"), J(SYS, "NVIDIA"), J(SYS, "AMD")],
        what="קבצים שנשארו אחרי התקנת דרייברים של NVIDIA או AMD.",
        if_deleted="בטוח. הדרייבר כבר מותקן. עדכון עתידי יוריד את מה שצריך.",
        how="דורש הרשאות מנהל.",
    ),
    dict(
        id="windows_old", category="system", safety="windows", action="open", open_target="ms-settings:storagesense",
        title="גרסה קודמת של Windows (Windows.old)",
        paths=[J(SYS, "Windows.old"), J(SYS, "$Windows.~BT"), J(SYS, "$Windows.~WS")],
        what="עותק של מערכת ההפעלה הקודמת שנשמר אחרי שדרוג גדול, כדי לאפשר חזרה אחורה.",
        if_deleted="אחרי המחיקה לא תוכל לחזור לגרסה הקודמת. אם השדרוג עובד טוב כבר כמה ימים, זה בטוח. "
                   "לא למחוק ידנית: יש בתיקייה הרשאות מערכת ומחיקה חלקית משאירה זבל.",
        how="הגדרות > מערכת > אחסון > קבצים זמניים > סמן \"התקנות קודמות של Windows\" > הסר קבצים.",
    ),
    # ----------------------------------------------------------------- browser
    dict(
        id="chrome_cache", category="browser", safety="safe", action="clean",
        title="מטמון של Google Chrome",
        paths=_chromium(J(LAD, "Google", "Chrome")),
        what="עותקים של תמונות, סקריפטים וסרטונים מאתרים שביקרת בהם, כדי שייטענו מהר יותר.",
        if_deleted="בטוח. סיסמאות, היסטוריה, סימניות ועוגיות (ההתחברויות שלך לאתרים) לא נמחקים. "
                   "אתרים ייטענו קצת לאט יותר בפעם הראשונה. "
                   "מומלץ לסגור את Chrome לפני הניקוי, אחרת קבצים שבשימוש ידולגו.",
        how="סגור את Chrome ולחץ \"נקה\".",
    ),
    dict(
        id="edge_cache", category="browser", safety="safe", action="clean",
        title="מטמון של Microsoft Edge",
        paths=_chromium(J(LAD, "Microsoft", "Edge")),
        what="עותקים של קבצים מאתרים שביקרת בהם ב-Edge.",
        if_deleted="בטוח. סיסמאות, היסטוריה, סימניות והתחברויות לא נמחקים.",
        how="סגור את Edge ולחץ \"נקה\".",
    ),
    dict(
        id="firefox_cache", category="browser", safety="safe", action="clean",
        title="מטמון של Firefox",
        paths=[J(LAD, "Mozilla", "Firefox", "Profiles", "*", "cache2")],
        what="עותקים של קבצים מאתרים שביקרת בהם ב-Firefox.",
        if_deleted="בטוח. סיסמאות, היסטוריה וסימניות לא נמחקים.",
        how="סגור את Firefox ולחץ \"נקה\".",
    ),
    dict(
        id="browser_sw", category="browser", safety="caution", action="clean",
        title="נתוני אתרים לא מקוונים (Service Workers)",
        paths=[J(LAD, "Google", "Chrome", "User Data", "*", "Service Worker", "CacheStorage"),
               J(LAD, "Microsoft", "Edge", "User Data", "*", "Service Worker", "CacheStorage")],
        what="נתונים שאתרים ואפליקציות רשת (למשל WhatsApp Web, Gmail, Google Docs) שומרים כדי לעבוד מהר או בלי אינטרנט.",
        if_deleted="לא נמחק שום דבר חשוב שלא נמצא גם בענן, אבל אתרים כמו WhatsApp Web עלולים לסנכרן מחדש "
                   "ולהיטען לאט בפעם הבאה. במקרים נדירים תצטרך להתחבר שוב לאתר.",
        how="סגור את הדפדפן ולחץ \"נקה\". כדאי רק אם התיקייה גדולה מאוד (כמה גיגה).",
    ),
    # -------------------------------------------------------------------- apps
    dict(
        id="adobe_cache", category="apps", safety="safe", action="clean",
        title="מטמון מדיה של Adobe (Premiere / After Effects)",
        paths=[J(AD, "Adobe", "Common", "Media Cache Files"), J(AD, "Adobe", "Common", "Media Cache"),
               J(AD, "Adobe", "Common", "Peak Files"), J(LAD, "Adobe", "Common", "Media Cache Files")],
        what="קבצי עזר ש-Premiere ו-After Effects יוצרים לכל קליפ שייבאת (קבצי שמע מפוענחים, גלי קול). "
             "גדל בלי הגבלה ויכול להגיע לעשרות גיגה.",
        if_deleted="בטוח. הפרויקטים והסרטונים שלך לא נפגעים. כשתפתח פרויקט, Premiere ייצור מחדש את המטמון "
                   "רק לקליפים שבו, ובהתחלה זה ייקח קצת זמן.",
        how="סגור את כל תוכנות Adobe ולחץ \"נקה\".",
    ),
    dict(
        id="capcut_old", category="apps", safety="safe", action="clean", remove_root=True,
        old_versions=[(J(LAD, "CapCut", "Apps"), "[0-9]*.*")],
        title="גרסאות ישנות של CapCut",
        paths=[],
        what="CapCut מתעדכן לעתים קרובות ומשאיר כל גרסה קודמת מותקנת. כל גרסה תופסת כ-1.5 גיגה.",
        if_deleted="בטוח. הגרסה החדשה ביותר נשארת והיא זו שנפתחת. הפרויקטים שלך לא נשמרים בתיקיות האלה.",
        how="סגור את CapCut ולחץ \"נקה\".",
    ),
    dict(
        id="capcut_cache", category="apps", safety="safe", action="clean",
        title="מטמון של CapCut",
        paths=[J(LAD, "CapCut", "User Data", "Cache")],
        what="אפקטים, מוזיקה, פילטרים ותצוגות מקדימות ש-CapCut הוריד או יצר.",
        if_deleted="הפרויקטים (טיוטות) שלך לא נמחקים. אפקטים ומוזיקה שהשתמשת בהם יורדו מחדש כשתפתח את הפרויקט, ולכן הפתיחה הראשונה תהיה איטית יותר.",
        how="סגור את CapCut ולחץ \"נקה\".",
    ),
    dict(
        id="chrome_ai_model", category="browser", safety="caution", action="clean", remove_root=True,
        title="מודל בינה מלאכותית מקומי של Chrome",
        paths=[J(LAD, "Google", "Chrome", "User Data", "OptGuideOnDeviceModel")],
        what="מודל AI (Gemini Nano) ש-Chrome מוריד כדי להפעיל תכונות כמו \"עזור לי לכתוב\" בלי אינטרנט.",
        if_deleted="התכונות האלה יפסיקו לעבוד עד ש-Chrome יוריד את המודל שוב (הוא יעשה זאת אוטומטית). "
                   "כדי שלא יחזור: chrome://flags > Enables optimization guide on device > Disabled.",
        how="סגור את Chrome ולחץ \"נקה\".",
    ),
    dict(
        id="vscode_cache", category="apps", safety="safe", action="clean",
        title="מטמון של VS Code",
        paths=[J(AD, "Code", "Cache"), J(AD, "Code", "CachedData"), J(AD, "Code", "CachedExtensionVSIXs"),
               J(AD, "Code", "Code Cache"), J(AD, "Code", "GPUCache"), J(AD, "Code", "logs"),
               J(AD, "Code", "Service Worker", "CacheStorage")],
        what="מטמון, יומנים וקבצי התקנה של תוספים ישנים של VS Code.",
        if_deleted="בטוח. ההגדרות, התוספים המותקנים והקוד שלך לא נפגעים.",
        how="סגור את VS Code לתוצאה מלאה, ולחץ \"נקה\".",
    ),
    dict(
        id="chat_apps_cache", category="apps", safety="safe", action="clean",
        title="מטמון של Discord / Slack / Zoom",
        paths=[J(AD, "discord", "Cache"), J(AD, "discord", "Code Cache"), J(AD, "discord", "GPUCache"),
               J(AD, "Slack", "Cache"), J(AD, "Slack", "Code Cache"), J(AD, "Slack", "Service Worker", "CacheStorage"),
               J(AD, "Zoom", "logs")],
        what="תמונות וקבצים שהאפליקציות האלה שמרו כדי להציג צ'אטים מהר יותר.",
        if_deleted="בטוח. ההודעות שמורות בשרתים ויורדו מחדש כשתצטרך אותן.",
        how="סגור את האפליקציות ולחץ \"נקה\".",
    ),
    # --------------------------------------------------------------------- dev
    dict(
        id="npm_cache", category="dev", safety="safe", action="clean",
        title="מטמון npm",
        paths=[J(LAD, "npm-cache")],
        what="עותק של כל חבילת npm שהורדת אי פעם, כדי להתקין מהר יותר בפעם הבאה.",
        if_deleted="בטוח. הפרויקטים לא נפגעים. ההתקנה הבאה (npm install) תוריד חבילות מהאינטרנט ולכן תהיה איטית יותר.",
        how="לחיצה על \"נקה\" (שווה ערך ל-npm cache clean --force).",
    ),
    dict(
        id="yarn_pip_cache", category="dev", safety="safe", action="clean",
        title="מטמון של pip / Yarn / NuGet",
        paths=[J(LAD, "pip", "cache"), J(LAD, "Yarn", "Cache"), J(LAD, "NuGet", "v3-cache"),
               J(LAD, "pypoetry", "Cache")],
        what="עותקים של חבילות קוד שהורדו.",
        if_deleted="בטוח. יורדו מחדש כשתצטרך אותן.",
        how="לחיצה על \"נקה\".",
    ),
    dict(
        id="gradle_daemon", category="dev", safety="safe", action="clean", min_age_days=1,
        title="יומנים וקבצי קריסה של Gradle",
        paths=[J(HOME, ".gradle", "daemon")],
        what="תיקייה שבה תהליך הבנייה של Android (Gradle daemon) כותב יומנים. כשהוא קורס מחוסר זיכרון, "
             "Java שומרת כאן קובץ קריסה (core.*.dmp) של 2-3 גיגה כל פעם. זה יכול להצטבר למאות גיגה.",
        if_deleted="בטוח לחלוטין. אלה יומנים וקבצי קריסה ישנים בלבד. הקוד, הפרויקטים והמטמון של Gradle לא נפגעים. "
                   "קבצים מ-24 השעות האחרונות מדולגים, כדי לא להפריע לבנייה שרצה.",
        how="לחיצה על \"נקה\".",
    ),
    dict(
        id="gradle_cache", category="dev", safety="caution", action="clean",
        title="מטמון Gradle (Android Studio)",
        paths=[J(HOME, ".gradle", "caches"), J(HOME, ".gradle", "wrapper", "dists")],
        what="ספריות וגרסאות Gradle שהורדו לבניית אפליקציות Android. נוטה לצבור גרסאות ישנות.",
        if_deleted="לא נמחק קוד. הבנייה הבאה של כל פרויקט Android תוריד הכל מחדש ותיקח כמה דקות, ודורשת אינטרנט.",
        how="סגור את Android Studio ולחץ \"נקה\".",
    ),
    dict(
        id="pnpm_store", category="dev", safety="safe", action="command", admin_cmd=False,
        command="pnpm store prune",
        title="מאגר החבילות של pnpm",
        paths=[J(LAD, "pnpm", "store")],
        what="כל חבילה ש-pnpm הוריד אי פעם נשמרת כאן, גם אם אף פרויקט כבר לא משתמש בה.",
        if_deleted="הפקודה הרשמית pnpm store prune מוחקת רק חבילות שאף פרויקט לא משתמש בהן. בטוח. "
                   "לא למחוק את התיקייה ידנית: פרויקטים קיימים מקושרים אליה.",
        how="לחיצה על \"הפעל\" פותחת חלון פקודה שמריץ pnpm store prune.",
    ),
    dict(
        id="automation_browsers", category="dev", safety="caution", action="clean", remove_root=True,
        title="דפדפנים של כלי אוטומציה ובדיקות",
        paths=[J(LAD, "ms-playwright"), J(HOME, ".cache", "puppeteer"), J(HOME, ".cache", "chrome-devtools-mcp"),
               J(HOME, "chrome-debug-*")],
        what="עותקים של Chrome ו-Firefox ש-Playwright, Puppeteer וכלי בדיקה הורידו, ופרופילי דפדפן זמניים שנוצרו בזמן דיבוג.",
        if_deleted="לא נמחק קוד. בפעם הבאה שתריץ בדיקה או סקריפט אוטומציה, הכלי יוריד את הדפדפן מחדש "
                   "(למשל npx playwright install).",
        how="לחיצה על \"נקה\".",
    ),
    dict(
        id="android_studio_old", category="dev", safety="caution", action="clean", remove_root=True,
        old_versions=[(J(LAD, "Google"), "AndroidStudio*"), (J(AD, "Google"), "AndroidStudio*")],
        title="נתונים של גרסאות ישנות של Android Studio",
        paths=[],
        what="כל גרסה של Android Studio יוצרת תיקיית הגדרות, מטמון ויומנים משלה. אחרי עדכון, התיקיות של הגרסאות הישנות נשארות.",
        if_deleted="התיקייה של הגרסה החדשה ביותר נשמרת. נמחקים רק נתונים של גרסאות קודמות, שהגרסה החדשה כבר העתיקה מהן את ההגדרות.",
        how="סגור את Android Studio ולחץ \"נקה\".",
    ),
    dict(
        id="android_avd", category="dev", safety="caution", action="none",
        title="אמולטורים של Android",
        paths=[J(HOME, ".android", "avd")],
        what="מכשירי Android וירטואליים. כל אמולטור תופס כמה גיגה.",
        if_deleted="האמולטור והאפליקציות שהותקנו בו יימחקו. אפשר ליצור אמולטור חדש בכל רגע.",
        how="Android Studio > Device Manager > מחק אמולטורים שאתה לא משתמש בהם. לא למחוק ידנית מהתיקייה.",
    ),
    dict(
        id="android_sdk", category="dev", safety="caution", action="none",
        title="Android SDK (תמונות מערכת וגרסאות)",
        paths=[J(LAD, "Android", "Sdk", "system-images"), J(LAD, "Android", "Sdk", "ndk"),
               J(LAD, "Android", "Sdk", "build-tools")],
        what="תמונות מערכת לאמולטורים, גרסאות NDK וכלי בנייה. גרסאות ישנות נשארות אחרי עדכונים.",
        if_deleted="פרויקט שמשתמש בגרסה שנמחקה לא ייבנה עד שתתקין אותה מחדש.",
        how="Android Studio > SDK Manager > סמן \"Show Package Details\" והסר גרסאות ישנות.",
    ),
    dict(
        id="wsl_docker", category="dev", safety="keep", action="none",
        title="דיסקים וירטואליים של Docker / WSL",
        paths=[J(LAD, "Docker", "wsl"), J(LAD, "Packages", "*", "LocalState", "ext4.vhdx"),
               J(LAD, "wsl", "*", "ext4.vhdx")],
        what="קובץ אחד גדול שמכיל את כל מערכת הלינוקס או את כל ה-images של Docker.",
        if_deleted="מחיקה ידנית מוחקת את כל הקונטיינרים, ה-images והקבצים בתוך הלינוקס. לא למחוק.",
        how="כדי לפנות מקום: הרץ docker system prune -a, ואז ב-Docker Desktop: Troubleshoot > Clean / Purge data. "
            "הקובץ לא מתכווץ אוטומטית גם אחרי מחיקה בתוכו.",
    ),
    # ------------------------------------------------------------------- big
    dict(
        id="hiberfil", category="big", safety="windows", action="command",
        command="powercfg /h off",
        title="קובץ שינה (hiberfil.sys)",
        paths=[J(SYS, "hiberfil.sys")],
        what="קובץ שבו Windows שומר את תוכן הזיכרון במצב \"שינה עמוקה\" (Hibernate) ובהפעלה מהירה (Fast Startup). "
             "הגודל שלו הוא בערך 40% מה-RAM.",
        if_deleted="אם תכבה אותו: אפשרות Hibernate תיעלם, וההדלקה של המחשב מכבוי מלא תהיה איטית יותר בכמה שניות. "
                   "מצב שינה רגיל (Sleep) ממשיך לעבוד. במחשב נייד שנשאר הרבה בתיק זה פחות מומלץ. "
                   "אסור למחוק את הקובץ ידנית. Windows ייצור אותו מחדש.",
        how="לחיצה על \"הפעל\" פותחת חלון מנהל שמריץ powercfg /h off. להחזרה: powercfg /h on.",
    ),
    dict(
        id="pagefile", category="big", safety="keep", action="none",
        title="קובץ זיכרון וירטואלי (pagefile.sys)",
        paths=[J(SYS, "pagefile.sys"), J(SYS, "swapfile.sys")],
        what="כשה-RAM מתמלא, Windows מעביר לכאן חלקים מהזיכרון. הגודל נקבע אוטומטית לפי העומס.",
        if_deleted="לא למחוק ולא לכבות. בלעדיו תוכנות יקרסו כשהזיכרון יתמלא. "
                   "אם הקובץ גדול מאוד, זה סימן שהזיכרון מתמלא לעתים קרובות (למשל הרבה לשוניות בדפדפן). "
                   "הפתרון הוא להפחית עומס, לא למחוק את הקובץ.",
        how="אין צורך בפעולה. ראה את לשונית \"אבחון מהירות\" לגבי צריכת הזיכרון.",
    ),
    dict(
        id="winsxs", category="big", safety="windows", action="command",
        command="Dism.exe /Online /Cleanup-Image /StartComponentCleanup",
        title="רכיבי Windows ישנים (WinSxS)",
        paths=[], measure=False,
        what="תיקייה שבה Windows שומר גרסאות קודמות של רכיבי מערכת אחרי עדכונים, כדי לאפשר הסרת עדכון.",
        if_deleted="לעולם לא למחוק את התיקייה ידנית: זה משבית את Windows. "
                   "הכלי הרשמי של מיקרוסופט (DISM) מסיר בבטחה רק גרסאות שכבר לא בשימוש. "
                   "הגודל בסייר מטעה, כי רוב הקבצים משותפים עם תיקיית Windows.",
        how="לחיצה על \"הפעל\" פותחת חלון מנהל שמריץ את DISM. זה לוקח 5 עד 20 דקות. אל תסגור את החלון באמצע.",
    ),
    dict(
        id="restore_points", category="big", safety="windows", action="open", open_target="SystemPropertiesProtection.exe",
        title="נקודות שחזור מערכת",
        paths=[], measure=False,
        what="גיבויים של קבצי מערכת ש-Windows יוצר לפני התקנות ועדכונים. נשמרים בתיקייה מוסתרת (System Volume Information).",
        if_deleted="מחיקת נקודות ישנות בטוחה. כדאי להשאיר לפחות את האחרונה, למקרה שעדכון ישבש משהו.",
        how="בחלון שייפתח: בחר את כונן C > הגדר > אפשר להקטין את \"השימוש המרבי\" ל-3% עד 5%, או ללחוץ \"מחק\".",
    ),
    dict(
        id="win_installer", category="big", safety="keep", action="none",
        title="מטמון ההתקנות של Windows (Windows\\Installer)",
        paths=[J(WIN, "Installer")],
        what="קבצים שתוכנות מותקנות צריכות כדי להתעדכן, להתתקן או להסיר את עצמן.",
        if_deleted="לא למחוק. אחרי מחיקה אי אפשר לעדכן או להסיר חלק מהתוכנות (למשל Office), והתיקון מסובך מאוד.",
        how="אין פעולה. אם התיקייה ענקית, הסרה של תוכנות שלא בשימוש תקטין אותה.",
    ),
]

# ------------------------------------------------------------ detailed info
# מידע מפורט לחלון ה-i: מה בדיוק קורה, מה לא נפגע, מה משתנה אחרי, ואיך מחזירים.
#   verdict       - תשובה קצרה לשאלה "זה יהרוס לי משהו?"
#   details       - הסבר מורחב בשפה פשוטה
#   not_affected  - רשימה של דברים שבוודאות לא נפגעים
#   after         - מה כן ישתנה אחרי הפעולה (אם בכלל)
#   undo          - איך מחזירים / מה עושים אם מתחרטים

PERSONAL = "המסמכים, התמונות, הסרטונים וההורדות שלך"
PROGRAMS = "התוכנות המותקנות. כולן ממשיכות לעבוד בדיוק כמו קודם"

DETAILS = {
    "user_temp": dict(
        verdict="לא יהרוס כלום. זו תיקיית פסולת שנועדה בדיוק לזה.",
        details="כשתוכנה צריכה לשמור משהו לרגע (למשל כשאתה פותח קובץ מצורף מהמייל, מתקין תוכנה או מחלץ ZIP), "
                "היא שמה אותו בתיקייה הזמנית. התוכנה אמורה למחוק אותו כשהיא מסיימת, אבל רוב התוכנות שוכחות. "
                "Windows עצמו מתייחס לתיקייה הזו כפסולת, וגם כלי \"ניקוי הדיסק\" של מיקרוסופט מוחק אותה.",
        not_affected=[PERSONAL, PROGRAMS, "הגדרות Windows והגדרות התוכנות", "סיסמאות, דפדפנים וחשבונות",
                      "קבצים מ-24 השעות האחרונות (הכלי מדלג עליהם, למקרה שהתקנה רצה עכשיו)",
                      "קבצים שתוכנה פתוחה משתמשת בהם כרגע (Windows לא מאפשר למחוק אותם, והכלי מדלג)"],
        after=["שום דבר מורגש. תוכנות ייצרו קבצים זמניים חדשים כשיצטרכו."],
        undo="אין צורך לשחזר. אם בכל זאת פתחת קובץ מצורף מהמייל ושכחת לשמור אותו, הוא נמצא עדיין במייל עצמו.",
    ),
    "win_temp": dict(
        verdict="לא יהרוס כלום. אותה פסולת, רק של Windows.",
        details="כמו התיקייה הזמנית של המשתמש, אבל משמשת את Windows ושירותי רקע. גם כאן הכלי מדלג על קבצים חדשים ונעולים.",
        not_affected=[PERSONAL, PROGRAMS, "Windows עצמו ועדכונים שכבר הותקנו"],
        after=["שום דבר מורגש."],
        undo="אין צורך.",
    ),
    "recycle_bin": dict(
        verdict="לא יהרוס כלום, בתנאי שאין בסל משהו שאתה עוד רוצה.",
        details="כשאתה מוחק קובץ, Windows לא באמת מוחק אותו אלא מעביר לסל המחזור, והוא ממשיך לתפוס מקום. ריקון הסל מוחק אותם סופית.",
        not_affected=["כל מה שלא נמצא בסל המחזור"],
        after=["לא תוכל לשחזר את הקבצים שהיו בסל."],
        undo="אין דרך פשוטה לשחזר אחרי ריקון. לכן כדאי לפתוח את הסל ולהעיף מבט לפני.",
    ),
    "wu_download": dict(
        verdict="לא יהרוס כלום. העדכונים עצמם כבר מותקנים.",
        details="Windows Update מוריד לכאן קבצי עדכון, מתקין אותם, ולפעמים משאיר את קבצי ההורדה. "
                "העדכון המותקן יושב במקום אחר לגמרי. זה כמו לזרוק את קופסת הקרטון אחרי שהרכבת את הרהיט.",
        not_affected=[PERSONAL, PROGRAMS, "עדכונים שכבר הותקנו"],
        after=["אם יש עדכון שהורד ועוד לא הותקן, Windows יוריד אותו שוב (לוקח כמה דקות ברקע)."],
        undo="אין צורך. Windows מוריד מחדש כל מה שחסר.",
    ),
    "delivery_opt": dict(
        verdict="לא יהרוס כלום.",
        details="עותקים של עדכונים ש-Windows שומר כדי לשתף עם מחשבים אחרים ברשת הביתית. זו תכונה של חיסכון בהורדות, לא משהו שהמחשב שלך צריך.",
        not_affected=[PERSONAL, PROGRAMS, "עדכונים שכבר הותקנו"],
        after=["שום דבר מורגש."],
        undo="אין צורך.",
    ),
    "error_reports": dict(
        verdict="לא יהרוס כלום.",
        details="כשתוכנה קורסת, Windows כותב דוח (מה קרס ומתי) ושולח למיקרוסופט. הדוחות נשארים אחר כך על הדיסק בלי שימוש.",
        not_affected=[PERSONAL, PROGRAMS, "יומן האירועים של Windows (נשמר בנפרד)"],
        after=["שום דבר מורגש."],
        undo="אין צורך.",
    ),
    "memory_dumps": dict(
        verdict="לא יהרוס כלום, אלא אם טכנאי ביקש ממך את הקבצים האלה.",
        details="כשהמחשב קורס עם מסך כחול, Windows שומר תמונה של הזיכרון באותו רגע. רק טכנאי עם כלים מיוחדים יכול לקרוא אותה.",
        not_affected=[PERSONAL, PROGRAMS],
        after=["אם תפנה לטכנאי בגלל מסכים כחולים, לא יהיו לו קבצי הקריסה הישנים (החדשים ייווצרו שוב אם זה יחזור)."],
        undo="אין צורך.",
    ),
    "win_logs": dict(
        verdict="לא יהרוס כלום.",
        details="יומני טקסט של רכיב ההתקנה של Windows. נמחקים רק יומנים בני יותר משבוע.",
        not_affected=[PERSONAL, PROGRAMS, "העדכונים עצמם"],
        after=["שום דבר מורגש."],
        undo="אין צורך.",
    ),
    "thumbcache": dict(
        verdict="לא יהרוס כלום. נבנה מחדש לבד.",
        details="כשאתה פותח תיקייה עם תמונות, הסייר מציג תמונות ממוזערות. כדי לא לחשב אותן כל פעם, הוא שומר אותן כאן.",
        not_affected=[PERSONAL + " (התמונות עצמן לא נוגעים בהן, רק בעותק הממוזער)", PROGRAMS],
        after=["בפעם הראשונה שתפתח תיקייה עם הרבה תמונות, הממוזערות יופיעו לאט יותר (כמה שניות)."],
        undo="אין צורך. נבנה מחדש אוטומטית.",
    ),
    "inetcache": dict(
        verdict="לא יהרוס כלום.",
        details="מטמון של רכיבי אינטרנט ישנים של Windows (מהתקופה של Internet Explorer), שתוכנות מסוימות עדיין משתמשות בהם.",
        not_affected=[PERSONAL, PROGRAMS, "Chrome ו-Edge (יש להם מטמון נפרד)"],
        after=["שום דבר מורגש."],
        undo="אין צורך.",
    ),
    "shader_cache": dict(
        verdict="לא יהרוס כלום.",
        details="משחקים ותוכנות גרפיות מתרגמים קוד גרפי לשפה של כרטיס המסך, ושומרים את התוצאה כדי לא לחשב שוב.",
        not_affected=[PERSONAL, PROGRAMS, "משחקים שמורים, הגדרות גרפיקה ודרייבר המסך"],
        after=["בפעם הראשונה שתפעיל משחק, ייתכנו כמה קפיצות קטנות בדקה הראשונה, עד שהמטמון ייבנה שוב."],
        undo="אין צורך.",
    ),
    "gpu_installers": dict(
        verdict="לא יהרוס כלום. הדרייבר מותקן במקום אחר.",
        details="כשמתקינים דרייבר של NVIDIA, קובץ ההתקנה נפרס לתיקייה זמנית ולא נמחק אחר כך.",
        not_affected=["דרייבר המסך המותקן", "GeForce Experience / NVIDIA App וההגדרות שלהם", PERSONAL],
        after=["שום דבר מורגש."],
        undo="אין צורך. עדכון דרייבר הבא יוריד קובץ התקנה חדש.",
    ),
    "windows_old": dict(
        verdict="לא יהרוס כלום, אבל לא תוכל לחזור לגרסת Windows הקודמת.",
        details="אחרי שדרוג גדול של Windows, העותק הקודם נשמר כדי לאפשר חזרה אחורה. Windows מוחק אותו לבד אחרי 10 ימים.",
        not_affected=[PERSONAL, PROGRAMS, "Windows הנוכחי"],
        after=["אפשרות \"חזור לגרסה הקודמת\" בהגדרות תיעלם."],
        undo="אי אפשר להחזיר.",
    ),
    "chrome_cache": dict(
        verdict="לא יהרוס כלום. שום דבר שאתה רואה ב-Chrome לא ייעלם.",
        details="כל פעם שאתה נכנס לאתר, Chrome שומר עותק של התמונות, הקוד והסרטונים שלו, כדי שבפעם הבאה ייטען מהר יותר. "
                "המטמון גדל כל הזמן, ואם יש לך כמה פרופילים של Chrome, לכל אחד מהם מטמון משלו. "
                "הכלי מוחק רק את תיקיות המטמון (Cache, Code Cache, GPUCache ו-ShaderCache), ולא נוגע בשום קובץ אחר בפרופיל.",
        not_affected=["סיסמאות שמורות", "סימניות (מועדפים)", "היסטוריית גלישה",
                      "התחברויות לאתרים (עוגיות). לא תצטרך להתחבר מחדש ל-Gmail, פייסבוק וכו'",
                      "תוספים והגדרות שלהם", "לשוניות פתוחות ופרופילים", "מילוי אוטומטי וכתובות", "הגדרות Chrome"],
        after=["אתרים ייטענו קצת לאט יותר בכניסה הראשונה, עד שהמטמון ייבנה שוב (שניות בודדות).",
               "אם Chrome פתוח, קבצים שהוא משתמש בהם ידולגו. לניקוי מלא, סגור את Chrome לפני."],
        undo="אין צורך. המטמון נבנה מחדש לבד תוך כדי גלישה.",
    ),
    "edge_cache": dict(
        verdict="לא יהרוס כלום.",
        details="אותו דבר כמו המטמון של Chrome, אבל של Edge. נמחקות רק תיקיות המטמון.",
        not_affected=["סיסמאות", "מועדפים", "היסטוריה", "התחברויות לאתרים", "תוספים והגדרות"],
        after=["אתרים ייטענו מעט לאט יותר בכניסה הראשונה."],
        undo="אין צורך.",
    ),
    "firefox_cache": dict(
        verdict="לא יהרוס כלום.",
        details="המטמון של Firefox. נמחקת רק תיקיית cache2.",
        not_affected=["סיסמאות", "סימניות", "היסטוריה", "התחברויות לאתרים", "תוספים"],
        after=["אתרים ייטענו מעט לאט יותר בכניסה הראשונה."],
        undo="אין צורך.",
    ),
    "browser_sw": dict(
        verdict="לא יהרוס כלום חשוב, אבל חלק מאתרי האינטרנט ייטענו לאט בפעם הראשונה.",
        details="אתרים מודרניים (WhatsApp Web, Gmail, YouTube, Google Docs) שומרים עותק של האפליקציה שלהם במחשב, "
                "כדי להיפתח מהר ואפילו בלי אינטרנט. זה נקרא Service Worker. הכלי מוחק רק את העותקים האלה (CacheStorage). "
                "ההודעות, המיילים והמסמכים עצמם נמצאים בשרתים של האתרים, לא כאן.",
        not_affected=["התחברויות לאתרים (עוגיות). WhatsApp Web נשאר מחובר", "סיסמאות, סימניות והיסטוריה",
                      "הודעות, מיילים ומסמכים (שמורים בענן)"],
        after=["אתרים כמו WhatsApp Web ו-Gmail ייטענו לאט יותר בפעם הראשונה, ואז יחזרו למהירות רגילה.",
               "אתר שהשתמשת בו בלי אינטרנט יצטרך אינטרנט בפתיחה הבאה."],
        undo="אין צורך. האתרים שומרים את העותק מחדש בכניסה הבאה.",
    ),
    "capcut_old": dict(
        verdict="לא יהרוס כלום. CapCut ימשיך לעבוד עם הגרסה החדשה.",
        details="בכל עדכון, CapCut מתקין את הגרסה החדשה בתיקייה נפרדת ומשאיר את הישנה. כך מצטברות הרבה גרסאות מותקנות, "
                "אבל רק האחרונה בשימוש. הכלי מוחק את כל תיקיות הגרסאות מלבד החדשה ביותר.",
        not_affected=["הפרויקטים והטיוטות שלך ב-CapCut", "סרטונים שייצאת", "ההתחברות שלך ל-CapCut",
                      "הגרסה החדשה של CapCut, שנשארת מותקנת ועובדת"],
        after=["שום דבר מורגש. CapCut נפתח מהגרסה החדשה כמו תמיד."],
        undo="אין צורך. אם משהו לא נפתח, התקנה מחדש של CapCut מהאתר מסדרת הכל, והפרויקטים נשמרים.",
    ),
    "capcut_cache": dict(
        verdict="לא יהרוס את הפרויקטים. אפקטים ומוזיקה יורדו מחדש כשצריך.",
        details="CapCut מוריד אפקטים, פילטרים, מעברים, מוזיקה ומדבקות מהאינטרנט ושומר אותם כאן. "
                "הפרויקטים (הטיוטות) שלך נשמרים בתיקייה אחרת.",
        not_affected=["הפרויקטים והטיוטות שלך", "סרטונים שייצאת", "קטעי וידאו ותמונות שייבאת", "ההתחברות ל-CapCut"],
        after=["כשתפתח פרויקט שמשתמש באפקט או במוזיקה של CapCut, הם יורדו שוב. זה דורש אינטרנט ולוקח כמה שניות."],
        undo="אין צורך.",
    ),
    "chrome_ai_model": dict(
        verdict="לא יהרוס כלום. Chrome יוריד את המודל שוב אם יצטרך.",
        details="Chrome מוריד מודל בינה מלאכותית קטן (Gemini Nano) כדי להפעיל תכונות כמו \"עזור לי לכתוב\" והצעות חכמות, בלי לשלוח מידע לענן.",
        not_affected=["סיסמאות, סימניות, היסטוריה והתחברויות", "הגלישה הרגילה"],
        after=["תכונות ה-AI המקומיות של Chrome לא יעבדו עד ש-Chrome יוריד את המודל מחדש (אוטומטית, ברקע)."],
        undo="אין צורך. Chrome מוריד אותו מחדש לבד.",
    ),
    "adobe_cache": dict(
        verdict="לא יהרוס את הפרויקטים.",
        details="Premiere ו-After Effects יוצרים לכל קליפ קבצי עזר (שמע מפוענח וגלי קול) כדי שהעריכה תהיה חלקה.",
        not_affected=["קבצי הפרויקט (.prproj / .aep)", "הסרטונים המקוריים", "סרטונים שייצאת"],
        after=["בפתיחה הראשונה של פרויקט, Premiere יעבד מחדש את הקליפים. זה יכול לקחת כמה דקות."],
        undo="אין צורך.",
    ),
    "vscode_cache": dict(
        verdict="לא יהרוס כלום.",
        details="VS Code שומר מטמון, יומנים וקבצי התקנה של גרסאות קודמות של תוספים.",
        not_affected=["הקוד והפרויקטים שלך", "ההגדרות (settings.json) וקיצורי המקלדת", "התוספים המותקנים",
                      "היסטוריית הקבצים הפתוחים ומצב החלונות"],
        after=["הפתיחה הראשונה של VS Code תהיה איטית בכמה שניות."],
        undo="אין צורך.",
    ),
    "chat_apps_cache": dict(
        verdict="לא יהרוס כלום.",
        details="Discord, Slack ו-Zoom שומרים תמונות וקבצים מהצ'אטים, ויומנים.",
        not_affected=["ההודעות (שמורות בשרתים)", "ההתחברות לאפליקציות", "הקלטות Zoom (נשמרות בתיקיית המסמכים)"],
        after=["תמונות בצ'אטים ישנים ייטענו שוב מהאינטרנט."],
        undo="אין צורך.",
    ),
    "npm_cache": dict(
        verdict="לא יהרוס שום פרויקט.",
        details="npm שומר כאן עותק של כל חבילה שהורדת אי פעם, וגם כלים שהרצת עם npx. הפרויקטים לא משתמשים בתיקייה הזו ישירות, "
                "כי לכל פרויקט יש node_modules משלו.",
        not_affected=["הפרויקטים ותיקיות node_modules שלהם", "חבילות גלובליות מותקנות (npm install -g)", "הגדרות npm"],
        after=["npm install הבא יוריד חבילות מהאינטרנט ולכן יהיה איטי יותר.",
               "פקודות npx יורידו את הכלי מחדש בהרצה הראשונה."],
        undo="אין צורך. נבנה מחדש אוטומטית.",
    ),
    "yarn_pip_cache": dict(
        verdict="לא יהרוס שום פרויקט.",
        details="עותקים של חבילות Python (pip), Yarn ו-NuGet שהורדו.",
        not_affected=["חבילות Python מותקנות", "הפרויקטים שלך", "סביבות וירטואליות (venv)"],
        after=["ההתקנה הבאה של חבילה תוריד אותה מהאינטרנט."],
        undo="אין צורך.",
    ),
    "gradle_daemon": dict(
        verdict="לא יהרוס כלום. אלה יומנים וקבצי קריסה ישנים בלבד.",
        details="Gradle הוא הכלי שבונה אפליקציות Android. הוא מריץ תהליך רקע (daemon) שכותב יומן לתיקייה הזו. "
                "כשהתהליך קורס מחוסר זיכרון, Java שומרת \"צילום\" של הזיכרון שלו (core.*.dmp) בגודל 2 עד 3 GB. "
                "אצל מפתחי Android הקבצים האלה יכולים להצטבר לעשרות. אף תוכנה לא קוראת אותם אחרי שנוצרו.",
        not_affected=["קוד המקור של אפליקציות ה-Android שלך", "Android Studio וההגדרות שלו",
                      "מטמון החבילות של Gradle (בתיקייה אחרת, caches)", "אמולטורים ו-SDK",
                      "קבצים מ-24 השעות האחרונות (למקרה שבנייה רצה עכשיו)"],
        after=["שום דבר מורגש. הבנייה הבאה תיצור יומן חדש."],
        undo="אין צורך.",
    ),
    "gradle_cache": dict(
        verdict="לא יהרוס קוד, אבל הבנייה הבאה תהיה איטית.",
        details="ספריות קוד וגרסאות של Gradle שהורדו לבניית אפליקציות Android. כולל גרסאות ישנות שאף פרויקט כבר לא משתמש בהן.",
        not_affected=["קוד המקור שלך", "Android Studio", "אמולטורים ו-SDK"],
        after=["הבנייה הראשונה של כל פרויקט Android תוריד מחדש את כל הספריות. זה יכול לקחת 5 עד 15 דקות ודורש אינטרנט."],
        undo="אין צורך. Gradle מוריד מחדש את מה שחסר.",
    ),
    "pnpm_store": dict(
        verdict="לא יהרוס שום פרויקט. הפקודה מוחקת רק מה שלא בשימוש.",
        details="pnpm שומר כל חבילה פעם אחת במאגר מרכזי, ופרויקטים מקושרים אליו. הפקודה הרשמית pnpm store prune "
                "בודקת אילו חבילות אף פרויקט כבר לא מקושר אליהן, ומוחקת רק אותן.",
        not_affected=["כל פרויקט קיים ותיקיית node_modules שלו", "חבילות שבשימוש"],
        after=["שום דבר מורגש."],
        undo="אין צורך.",
    ),
    "automation_browsers": dict(
        verdict="לא יהרוס את Chrome הרגיל שלך. זה נוגע רק לדפדפני בדיקה.",
        details="כלים כמו Playwright ו-Puppeteer מורידים עותק נפרד של Chrome או Firefox כדי להריץ בדיקות אוטומטיות. "
                "בנוסף, דיבוג של Chrome יוצר תיקיות פרופיל זמניות (chrome-debug-...). אלה לא הדפדפן שאתה גולש בו.",
        not_affected=["Chrome הרגיל שלך, הסיסמאות, הסימניות וההיסטוריה", "הקוד והבדיקות שלך"],
        after=["בפעם הבאה שתריץ Playwright או Puppeteer, הוא יבקש להוריד את הדפדפן שוב (למשל npx playwright install).",
               "אם התחברת לאתרים בתוך דפדפן הבדיקות, תצטרך להתחבר שם שוב."],
        undo="להריץ npx playwright install או להריץ שוב את הכלי. הוא יוריד את מה שצריך.",
    ),
    "android_studio_old": dict(
        verdict="לא יהרוס את Android Studio הנוכחי.",
        details="כל גרסה של Android Studio יוצרת תיקייה עם הגדרות, מטמון ויומנים. כשמעדכנים, הגרסה החדשה מעתיקה את ההגדרות, "
                "והתיקייה הישנה נשארת. הכלי שומר את התיקייה של הגרסה החדשה ביותר ומוחק רק את הישנות.",
        not_affected=["הגרסה הנוכחית של Android Studio וההגדרות שלה", "הפרויקטים שלך", "SDK ואמולטורים"],
        after=["אם עדיין מותקנת במחשב גרסה ישנה של Android Studio ואתה פותח אותה, היא תתחיל עם הגדרות ברירת מחדל."],
        undo="אין צורך.",
    ),
    "hiberfil": dict(
        verdict="לא יהרוס תוכנות או קבצים. זה משנה רק את אופן הכיבוי וההדלקה.",
        details="Windows שומר בקובץ hiberfil.sys את תוכן הזיכרון בשני מצבים: \"שינה עמוקה\" (Hibernate), שבו המחשב נכבה לגמרי "
                "וחוזר בדיוק למצב שבו היה, ו\"הפעלה מהירה\" (Fast Startup), שמקצרת את ההדלקה. "
                "הפקודה powercfg /h off מכבה את שני המצבים, ו-Windows מוחק את הקובץ בעצמו.",
        not_affected=[PERSONAL, PROGRAMS, "מצב שינה רגיל (Sleep): סגירת המכסה ממשיכה לעבוד כרגיל",
                      "כיבוי והפעלה מחדש רגילים"],
        after=["ההדלקה של המחשב מכבוי מלא תהיה איטית יותר בכמה שניות (בגלל שאין Fast Startup). הפעלה מחדש לא משתנה.",
               "האפשרות \"מצב שינה עמוקה\" תיעלם מתפריט הכיבוי.",
               "אם הסוללה תתרוקן לגמרי כשהמחשב במצב שינה, עבודה שלא נשמרה תאבד (עם Hibernate היא נשמרת). "
               "במחשב שמחובר בדרך כלל לחשמל, זה כמעט לא רלוונטי."],
        undo="פותחים חלון פקודה כמנהל ומקלידים powercfg /h on. הכל חוזר כמו שהיה.",
    ),
    "pagefile": dict(
        verdict="לא לגעת.",
        details="כשה-RAM מתמלא, Windows מעביר חלקים ממנו לכאן. בלי הקובץ, תוכנות יקרסו כשהזיכרון יתמלא.",
        not_affected=[], after=[], undo="",
    ),
    "winsxs": dict(
        verdict="לא יהרוס כלום. זה הכלי הרשמי של מיקרוסופט לניקוי הזה.",
        details="Windows שומר גרסאות קודמות של רכיבי מערכת אחרי כל עדכון. הפקודה DISM /StartComponentCleanup מוחקת רק "
                "גרסאות שהוחלפו בגרסה חדשה לפני יותר מ-30 יום. זה בדיוק מה ש-Windows עושה לבד מדי פעם במשימה מתוזמנת.",
        not_affected=[PERSONAL, PROGRAMS, "Windows ועדכונים מותקנים",
                      "האפשרות להסיר את העדכון האחרון (הפקודה לא משתמשת ב-/ResetBase)"],
        after=["לא יהיה אפשר להחזיר רכיבי מערכת לגרסאות שהוחלפו לפני יותר מחודש. כמעט אף פעם לא צריך את זה."],
        undo="אין צורך.",
    ),
    "restore_points": dict(
        verdict="מחיקה של נקודות ישנות לא הורסת כלום.",
        details="נקודת שחזור היא גיבוי של קבצי מערכת והגדרות, שמאפשר להחזיר את Windows לתאריך קודם אחרי תקלה.",
        not_affected=[PERSONAL + " (נקודות שחזור לא מגבות אותם ממילא)", PROGRAMS],
        after=["לא יהיה אפשר להחזיר את המערכת לתאריכים של הנקודות שנמחקו."],
        undo="אי אפשר להחזיר נקודות שנמחקו. אפשר ליצור נקודה חדשה באותו חלון.",
    ),
    "android_avd": dict(
        verdict="מוחק את האמולטור וכל מה שהתקנת בתוכו.",
        details="כל אמולטור הוא טלפון וירטואלי שלם.",
        not_affected=["קוד האפליקציות שלך", "Android Studio"],
        after=["תצטרך ליצור אמולטור חדש ולהתקין בו את האפליקציות מחדש."],
        undo="Device Manager > Create Device.",
    ),
    "android_sdk": dict(
        verdict="לא יהרוס קוד, אבל פרויקט שצריך גרסה שנמחקה לא ייבנה עד שתתקין אותה שוב.",
        details="גרסאות של כלי פיתוח ל-Android.",
        not_affected=["קוד האפליקציות", "Android Studio"],
        after=["Android Studio יציע להוריד גרסה חסרה כשתפתח פרויקט שצריך אותה."],
        undo="SDK Manager > סמן את הגרסה > Apply.",
    ),
}


def rule_by_id(rid):
    for r in RULES:
        if r["id"] == rid:
            return r
    return None


# ---------------------------------------------------------------- file hints
EXT_HINTS = [
    ({".iso", ".img"}, "caution", "קובץ תמונת דיסק, בדרך כלל להתקנת מערכת או תוכנה. אם כבר התקנת, אפשר למחוק ולהוריד שוב כשצריך."),
    ({".exe", ".msi", ".msix", ".appx"}, "caution", "קובץ התקנה. אם התוכנה כבר מותקנת, בדרך כלל אפשר למחוק ולהוריד שוב מהאתר של היצרן."),
    ({".zip", ".rar", ".7z", ".tar", ".gz"}, "caution", "קובץ דחוס. בדוק אם כבר חילצת אותו. אם כן, העותק הדחוס מיותר."),
    ({".mp4", ".mov", ".mkv", ".avi", ".wmv", ".m4v", ".webm", ".mts", ".m2ts"}, "caution", "סרטון. תוכן אישי: אל תמחק בלי לצפות או לגבות (למשל לענן או לדיסק חיצוני)."),
    ({".vhd", ".vhdx", ".vmdk", ".vdi", ".qcow2"}, "keep", "דיסק של מכונה וירטואלית (Docker / WSL / VirtualBox). לא למחוק ידנית אם אתה משתמש בו."),
    ({".log", ".etl"}, "safe", "קובץ יומן. כמעט תמיד בטוח למחוק."),
    ({".dmp", ".mdmp", ".hdmp"}, "safe", "קובץ קריסה. בטוח למחוק, אלא אם טכנאי ביקש אותו."),
    ({".tmp", ".temp", ".old", ".bak"}, "caution", "קובץ זמני או גיבוי. בדרך כלל אפשר למחוק, בדוק את השם לפני."),
    ({".psd", ".prproj", ".aep", ".blend", ".ai"}, "keep", "קובץ פרויקט של תוכנת עיצוב או עריכה. תוכן אישי."),
    ({".apk", ".aab"}, "caution", "אפליקציית Android שנבנתה. אם יש לך את קוד המקור, אפשר לבנות שוב."),
    ({".pst", ".ost"}, "keep", "תיבת דואר של Outlook. לא למחוק."),
    ({".db", ".sqlite", ".mdf", ".ldf"}, "keep", "מסד נתונים של תוכנה. לא למחוק בלי לדעת לאיזו תוכנה הוא שייך."),
    ({".wav", ".mp3", ".flac"}, "caution", "קובץ שמע. תוכן אישי."),
    ({".jpg", ".jpeg", ".png", ".raw", ".cr2", ".nef", ".heic"}, "caution", "תמונה. תוכן אישי."),
]

SYSTEM_FILES = {"pagefile.sys", "hiberfil.sys", "swapfile.sys"}
LANGS = ("he", "en")


def _both(he, en):
    return {"he": he, "en": en}


def rule_text(r):
    """כל הטקסטים של כלל, בשתי השפות: {"he": {...}, "en": {...}}."""
    he = {k: r.get(k) for k in ("title", "what", "if_deleted", "how")}
    he.update(DETAILS.get(r["id"], {}))
    he["safety_label"] = SAFETY_LABELS[r["safety"]]
    he["category_label"] = CATEGORIES[r["category"]]
    en = dict(rules_en.TEXT.get(r["id"], {}))
    for k, v in he.items():  # אם חסר תרגום, נופלים לעברית ולא לריק
        en.setdefault(k, v)
    en["safety_label"] = rules_en.SAFETY_LABELS[r["safety"]]
    en["category_label"] = rules_en.CATEGORIES[r["category"]]
    return _both(he, en)


def file_hint(path):
    """מחזיר (רמת בטיחות, {"he": הסבר, "en": explanation}) עבור קובץ לפי המיקום והסיומת."""
    E = rules_en
    low = path.lower()
    if os.path.basename(low) in SYSTEM_FILES:
        return "keep", _both("קובץ מערכת. לא למחוק ידנית. ההסבר המלא בלשונית \"מה אפשר למחוק\".", E.SYSTEM_FILE)
    if low.startswith(WIN.lower() + "\\") or "\\program files" in low or low.startswith(PD.lower() + "\\package cache"):
        return "keep", _both("קובץ של Windows או של תוכנה מותקנת. לא למחוק ידנית. אם התוכנה לא בשימוש, "
                             "הסר אותה דרך הגדרות > אפליקציות.", E.PROGRAM_FILE)
    in_appdata = "\\appdata\\" in low
    base_he = "קובץ של תוכנה, בתוך AppData. " if in_appdata else ""
    base_en = E.APPDATA_PREFIX if in_appdata else ""
    ext = os.path.splitext(low)[1]
    en_texts = list(E.EXT_HINTS.values())
    for i, (exts, safety, text) in enumerate(EXT_HINTS):
        if ext in exts:
            en = en_texts[i]
            if "\\downloads\\" in low and safety != "keep":
                text += " הקובץ נמצא בתיקיית ההורדות, ושם בדרך כלל יושבים קבצים שכבר לא צריך."
                en += E.DOWNLOADS_NOTE
            return safety, _both(base_he + text, base_en + en)
    if in_appdata:
        return "caution", _both(base_he + "לא למחוק בלי לדעת לאיזו תוכנה הוא שייך. אם התוכנה לא בשימוש, "
                                "הסר אותה במקום למחוק קבצים.", base_en + E.APPDATA_UNKNOWN)
    return "caution", _both("קובץ לא מזוהה. פתח את המיקום ובדוק מה זה לפני מחיקה.", E.UNKNOWN_FILE)


def downloads_dir_hint():
    return _both("תיקייה בתוך ההורדות. בדוק את התוכן לפני מחיקה.", rules_en.DOWNLOADS_DIR)


def folder_hint(path, lang="he"):
    """הסבר קצר לתיקיות מוכרות בעץ הגדלים."""
    E = rules_en.FOLDER_HINTS
    low = path.lower().rstrip("\\")
    name = os.path.basename(low)
    table = {
        WIN.lower(): ("מערכת ההפעלה. לא לגעת.", E["windows"]),
        J(SYS, "program files").lower(): ("תוכנות מותקנות. להסרה: הגדרות > אפליקציות.", E["program files"]),
        J(SYS, "program files (x86)").lower(): ("תוכנות מותקנות (32 ביט). להסרה: הגדרות > אפליקציות.", E["program files (x86)"]),
        PD.lower(): ("נתונים משותפים של תוכנות. לא למחוק ידנית.", E["programdata"]),
        J(SYS, "users").lower(): ("תיקיות המשתמשים: מסמכים, הורדות, שולחן עבודה והגדרות תוכנות.", E["users"]),
        J(SYS, "$recycle.bin").lower(): ("סל המחזור. אפשר לרוקן בלשונית \"מה אפשר למחוק\".", E["$recycle.bin"]),
        J(SYS, "system volume information").lower(): ("נקודות שחזור. מנהלים דרך הגדרות הגנת מערכת.", E["system volume information"]),
        J(SYS, "xboxgames").lower(): ("משחקי Xbox. להסרת משחק: הגדרות > אפליקציות או אפליקציית Xbox.", E["xboxgames"]),
        HOME.lower(): ("תיקיית המשתמש שלך.", E["home"]),
        J(HOME, "appdata").lower(): ("הגדרות ומטמונים של תוכנות. כאן יושבים רוב המטמונים שהכלי יודע לנקות.", E["appdata"]),
        J(HOME, "downloads").lower(): ("הורדות. בדרך כלל יש כאן הרבה קבצים שאפשר למחוק.", E["downloads"]),
        J(HOME, "onedrive").lower(): ("קבצים שמסונכרנים ל-OneDrive. אפשר לפנות מקום עם \"פנה שטח\" בלחיצה ימנית "
                                      "(הקבצים יישארו בענן).", E["onedrive"]),
    }
    pick = (lambda pair: pair[0] if lang == "he" else pair[1])
    if low in table:
        return pick(table[low])
    if name == "node_modules":
        return pick(("חבילות של פרויקט Node.js. אפשר למחוק ולשחזר עם npm install.", E["node_modules"]))
    if name == ".gradle":
        return pick(("מטמון בנייה של Android.", E[".gradle"]))
    if name in ("build", "dist", ".next", "out", "target", ".cxx"):
        return pick(("תוצרי בנייה של פרויקט קוד. בדרך כלל אפשר למחוק ולבנות מחדש.", E["build"]))
    for r in RULES:
        for p in r.get("paths", []):
            if "*" not in p and p.lower().rstrip("\\") == low:
                t = rule_text(r)[lang]
                if lang == "he":
                    return t["title"] + ": " + t["safety_label"] + ". פרטים בלשונית \"מה אפשר למחוק\"."
                return E["rule"].format(title=t["title"], safety=t["safety_label"])
    return ""

