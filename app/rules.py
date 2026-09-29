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


def file_hint(path):
    """מחזיר (רמת בטיחות, הסבר) עבור קובץ גדול לפי המיקום והסיומת."""
    low = path.lower()
    if os.path.basename(low) in SYSTEM_FILES:
        return "keep", "קובץ מערכת. לא למחוק ידנית. ההסבר המלא בלשונית \"מה אפשר למחוק\"."
    if low.startswith(WIN.lower() + "\\") or "\\program files" in low or low.startswith(PD.lower() + "\\package cache"):
        return "keep", "קובץ של Windows או של תוכנה מותקנת. לא למחוק ידנית. אם התוכנה לא בשימוש, הסר אותה דרך הגדרות > אפליקציות."
    base = "קובץ של תוכנה, בתוך AppData. " if "\\appdata\\" in low else ""
    ext = os.path.splitext(low)[1]
    for exts, safety, text in EXT_HINTS:
        if ext in exts:
            if "\\downloads\\" in low and safety != "keep":
                text += " הקובץ נמצא בתיקיית ההורדות, ושם בדרך כלל יושבים קבצים שכבר לא צריך."
            return safety, base + text
    if base:
        return "caution", base + "לא למחוק בלי לדעת לאיזו תוכנה הוא שייך. אם התוכנה לא בשימוש, הסר אותה במקום למחוק קבצים."
    return "caution", "קובץ לא מזוהה. פתח את המיקום ובדוק מה זה לפני מחיקה."


def folder_hint(path):
    """הסבר קצר לתיקיות מוכרות בעץ הגדלים."""
    low = path.lower().rstrip("\\")
    name = os.path.basename(low)
    table = {
        WIN.lower(): "מערכת ההפעלה. לא לגעת.",
        J(SYS, "program files").lower(): "תוכנות מותקנות. להסרה: הגדרות > אפליקציות.",
        J(SYS, "program files (x86)").lower(): "תוכנות מותקנות (32 ביט). להסרה: הגדרות > אפליקציות.",
        PD.lower(): "נתונים משותפים של תוכנות. לא למחוק ידנית.",
        J(SYS, "users").lower(): "תיקיות המשתמשים: מסמכים, הורדות, שולחן עבודה והגדרות תוכנות.",
        J(SYS, "$recycle.bin").lower(): "סל המחזור. אפשר לרוקן בלשונית \"מה אפשר למחוק\".",
        J(SYS, "system volume information").lower(): "נקודות שחזור. מנהלים דרך הגדרות הגנת מערכת.",
        J(SYS, "xboxgames").lower(): "משחקי Xbox. להסרת משחק: הגדרות > אפליקציות או אפליקציית Xbox.",
        HOME.lower(): "תיקיית המשתמש שלך.",
        J(HOME, "appdata").lower(): "הגדרות ומטמונים של תוכנות. כאן יושבים רוב המטמונים שהכלי יודע לנקות.",
        J(HOME, "downloads").lower(): "הורדות. בדרך כלל יש כאן הרבה קבצים שאפשר למחוק.",
        J(HOME, "onedrive").lower(): "קבצים שמסונכרנים ל-OneDrive. אפשר לפנות מקום עם \"פנה שטח\" בלחיצה ימנית (הקבצים יישארו בענן).",
    }
    if low in table:
        return table[low]
    if name == "node_modules":
        return "חבילות של פרויקט Node.js. אפשר למחוק ולשחזר עם npm install."
    if name in (".gradle",):
        return "מטמון בנייה של Android."
    if name in ("build", "dist", ".next", "out", "target", ".cxx"):
        return "תוצרי בנייה של פרויקט קוד. בדרך כלל אפשר למחוק ולבנות מחדש."
    for r in RULES:
        for p in r.get("paths", []):
            if "*" not in p and p.lower().rstrip("\\") == low:
                return r["title"] + ": " + SAFETY_LABELS[r["safety"]] + ". פרטים בלשונית \"מה אפשר למחוק\"."
    return ""
