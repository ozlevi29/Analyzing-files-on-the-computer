"use strict";

const TOKEN = new URLSearchParams(location.hash.slice(1)).get("t") || "";
const HASH = new URLSearchParams(location.hash.slice(1));
const $ = (s, el = document) => el.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

let STATE = null;
let pollTimer = null;
let safetyFilter = "all";

// ============================================================== language
// Every UI string exists in Hebrew and English. Texts that come from the scan
// (rules, report) arrive from the server in both languages and are picked here too.
const STR = {
  he: {
    appName: "רופא המחשב", appSub: "אבחון, ניקוי והסבר מסודר לכל פעולה", langBtn: "English", quit: "יציאה",
    introTitle: "למה המחשב איטי?",
    introP1: "הסריקה בודקת את הזיכרון, המעבד, התוכנות שנפתחות עם המחשב, החיבור לאינטרנט ואת כל הקבצים בכונן C. בסוף תקבל הסבר למה המחשב איטי, ורשימת צעדי טיפול. ליד כל צעד יש כפתור טפל.",
    introP2: "שום דבר לא נמחק ולא משתנה בזמן הסריקה. לפני כל פעולה יופיע חלון שמסביר בדיוק מה יקרה, ורק אחרי שתאשר היא תתבצע.",
    deepChk: "סריקה מלאה של כל הכונן (לוקחת כמה דקות, ומוצאת קבצים ותיקיות גדולים)",
    scanBtn: "סרוק את המחשב", skipDeep: "דלג על סריקת הכונן המלאה",
    tabReport: "למה המחשב איטי", tabClean: "מה אפשר למחוק", tabDisk: "קבצים ותיקיות גדולים", tabSystem: "פרטי מערכת", rescan: "סריקה חוזרת",
    sure: "האם אתה בטוח?", whatHappens: "מה יקרה:", yesDo: "כן, בצע", cancel: "ביטול", close: "סגור", moreInfo: "מידע מפורט",
    notMeasured: "לא נמדד", error: "שגיאה",
    diskLabel: "כונן {root}", diskFree: "{free} פנויים מתוך {total} ({pct}% פנוי)",
    admin: "פועל כמנהל", user: "פועל כמשתמש רגיל", adminTip: "חלק מהניקויים דורשים הרשאות מנהל",
    stage: "שלב {n} מתוך 4: {label}",
    stages: ["", "בודק זיכרון, מעבד, תוכנות הפעלה ורשת", "מודד תיקיות זבל ומטמונים מוכרים", "סורק את כל הכונן (זה השלב הארוך)", "מכין דוח"],
    filesScanned: "{n} קבצים, {size}", scanFailed: "הסריקה נכשלה: ",
    sev: { high: "בעיה חמורה", medium: "כדאי לטפל", low: "לתשומת לבך", ok: "תקין" },
    statFree: "מקום פנוי בכונן C", statSafe: "אפשר לפנות בבטחה", statMem: "זיכרון בשימוש", statCpu: "מעבד בזמן הסריקה",
    leadOk: "לא נמצאו בעיות משמעותיות. למטה יש כמה טיפים שיכולים לעזור.",
    leadIssues: "נמצאו {n} סיבות עיקריות לאיטיות. הן מסודרות מהחשובה ביותר. ליד כל צעד יש כפתור \"טפל\", ולפני כל פעולה יופיע הסבר ותתבקש לאשר.",
    stepsTitle: "צעדים לטיפול", again: "שוב", startsNow: "נפתחות עכשיו: ",
    breakQ: "זה יהרוס לי משהו?", secWhat: "מה זה?", secDeleted: "מה בדיוק יימחק, ומאיפה", secThere: "מה נמצא שם עכשיו",
    secHow: "איך זה מתבצע", secNotAffected: "מה לא ייפגע", secAfter: "מה כן ישתנה אחרי", secUndo: "ואם אתחרט?", secWhere: "איפה זה מוגדר",
    howClean: "הקבצים נמחקים לצמיתות, לא דרך סל המחזור, כי הם נבנים מחדש לבד. קבצים שתוכנה פתוחה משתמשת בהם כרגע ידולגו, בלי שום נזק לתוכנה.",
    howAge1: " קבצים שנוצרו או שונו ב-24 השעות האחרונות לא נמחקים.", howAgeN: " קבצים שנוצרו או שונו ב-{n} הימים האחרונים לא נמחקים.",
    howRecycle: "סל המחזור מתרוקן דרך הפונקציה הרשמית של Windows, בדיוק כמו לחיצה ימנית על הסל > \"רוקן את סל המחזור\".",
    howCmd: "ייפתח חלון פקודה{admin} שיריץ את הפקודה הרשמית:\n{cmd}\nהכלי לא מוחק את הקבצים בעצמו: Windows או הכלי הרשמי עושים את זה.",
    howCmdAdmin: " (Windows יבקש אישור מנהל)",
    howOpen: "ייפתח מסך של Windows. שום דבר לא יימחק אוטומטית. אתה מבצע את הפעולה במסך שנפתח.",
    allVerdict: "לא. כל הסוגים ברשימה הם קבצים זמניים, מטמונים וקבצי קריסה. אף אחד מהם לא מכיל מידע אישי, וכל תוכנה יוצרת מחדש את מה שהיא צריכה.",
    allWhat: "מה הפעולה עושה", allWhatText: "הפעולה מנקה {n} סוגים של קבצי פסולת, בסך הכול {size}. לחץ על כל סוג כדי לראות מה הוא, מאילו תיקיות בדיוק הוא נמחק, ומה לא ייפגע.",
    allNever: "מה לא ייפגע בשום מקרה",
    allNeverList: ["המסמכים, התמונות, הסרטונים וההורדות שלך", "התוכנות המותקנות. כולן ממשיכות לעבוד",
      "בדפדפנים: סיסמאות, סימניות, היסטוריה, התחברויות לאתרים ותוספים", "פרויקטים וקוד", "Windows, עדכונים מותקנים והגדרות"],
    allBefore: "לפני שמתחילים", allBeforeText: "כדאי לסגור את הדפדפנים ואת התוכנות הפתוחות. זה לא חובה, אבל כך יימחקו גם הקבצים שהן מחזיקות פתוחים עכשיו.",
    doneFreed: "בוצע. פונו {size}", doneSkipped: " ({n} קבצים בשימוש דולגו)",
    doneRecycled: "הועבר לסל המחזור ({size}). כדי לפנות את המקום בפועל, רוקן את סל המחזור.", done: "בוצע",
    working: "מבצע…", deleting: "מוחק…", failed: "לא הצליח: ",
    act: { clean: "נקה", recycle: "רוקן", command: "הפעל", open: "פתח" },
    chips: { all: "הכל", safe: "בטוח למחוק", caution: "בדוק לפני", windows: "דרך Windows", keep: "לא למחוק" },
    cleanLead: "כל מקום שהכלי מכיר במחשב, מה גודלו, מה זה, והאם בטוח למחוק. ממוין מהגדול לקטן בכל קבוצה.",
    needAdmin: "דורש הרשאות מנהל. לחץ \"הפעל כמנהל\" למעלה.", empty: "ריק, אין מה לנקות", location: "מיקום ({n})",
    dtWhat: "מה זה?", dtSafe: "האם בטוח למחוק?", dtHow: "איך מנקים",
    cfClean: "יימחק לצמיתות (לא דרך סל המחזור) התוכן של:\n{paths}{more}\n\nגודל: {size}\n\nמה המשמעות: {meaning}", cfMore: "\n…ועוד {n}",
    cfRecycle: "כל הפריטים בסל המחזור ({size}) יימחקו לצמיתות, ולא יהיה אפשר לשחזר אותם.\n\nאם אתה לא בטוח מה יש שם, לחץ \"ביטול\" ופתח קודם את סל המחזור.",
    cfCmd: "ייפתח חלון פקודה{admin} שיריץ:\n{cmd}\n\nמה המשמעות: {meaning}", cfCmdAdmin: " עם בקשת הרשאות מנהל",
    cfOpen: "ייפתח מסך של Windows. שום דבר לא יימחק אוטומטית.\n\nמה לעשות שם: {how}",
    dlTitle: "תיקיית ההורדות: קבצים שלא נגעת בהם יותר מחודש", dlSub: "הכלי לא מוחק כאן כלום לבד. בדוק כל קובץ, ואם הוא מיותר העבר אותו לסל המחזור.",
    thFile: "קובץ", thSize: "גודל", thSafe: "האם בטוח למחוק", thProject: "פרויקט", modified: "שונה לאחרונה: ",
    openLoc: "פתח מיקום", toBin: "לסל המחזור", del: "מחק",
    cfOpenLoc: "פתיחת מיקום", cfOpenLocText: "ייפתח סייר הקבצים במיקום:\n{path}\n\nשום דבר לא יימחק.", open: "פתח",
    cfBinTitle: "להעביר לסל המחזור?",
    cfBin: "הקובץ יועבר לסל המחזור:\n{path}\nגודל: {size}\n\nעל הקובץ: {hint}\n\nאפשר לשחזר אותו מסל המחזור עד שתרוקן אותו. המקום בדיסק יתפנה רק אחרי ריקון הסל.\nשים לב: קובץ גדול מהמקום שמוקצה לסל המחזור עלול להימחק לצמיתות.",
    cfBinYes: "כן, העבר לסל המחזור",
    cfNmTitle: "למחוק את node_modules?",
    cfNm: "התיקייה תימחק לצמיתות (לא דרך סל המחזור, כי יש בה עשרות אלפי קבצים):\n{path}\nגודל: {size}\n\nמה המשמעות: הקוד של הפרויקט לא נפגע. כשתחזור לעבוד על הפרויקט, הרץ בתיקייה שלו npm install (או pnpm install / yarn) כדי להוריד את החבילות מחדש. אל תמחק אם הפרויקט רץ עכשיו.",
    cfNmYes: "כן, מחק",
    noDeep: "הסריקה המלאה של הכונן לא הופעלה. לחץ \"סריקה חוזרת\" וסמן \"סריקה מלאה\".",
    whereTitle: "איפה המקום הלך?", whereSub: "תיקיות מעל 200 MB בכונן. לחץ על החץ כדי להיכנס פנימה.", denied: "({n} תיקיות מערכת לא נסרקו בגלל הרשאות.)",
    largeTitle: "קבצים גדולים (מעל 500 MB)", largeSub: "ליד כל קובץ יש הסבר אם בטוח למחוק אותו. הכלי לא מוחק קבצים אישיים לבד: אתה מחליט, והקובץ עובר לסל המחזור.",
    noLarge: "לא נמצאו קבצים מעל 500 MB.", nmTitle: "תיקיות node_modules ({size})",
    nmSub: "חבילות של פרויקטי JavaScript. אפשר למחוק בפרויקטים שאתה לא עובד עליהם, ולשחזר בכל רגע עם npm install.", noneFound: "לא נמצאו.",
    noSub: "אין תת-תיקיות גדולות.", expand: "פתח",
    sysMem: "זיכרון", inUse: "בשימוש", ofTotal: "{used} מתוך {total}", uptime: "זמן מאז הפעלה", days: "{n} ימים", power: "חשמל",
    onBattery: "על סוללה ({n}%)", plugged: "מחובר לחשמל", plan: "תוכנית חשמל", diskNet: "דיסק ורשת", health: "תקינות: ", healthy: "תקין",
    noWifi: "לא מחובר ב-Wi-Fi", latency: "זמן תגובה", latencyVal: "ממוצע {avg}ms, מקסימום {max}ms", noNet: "אין חיבור", av: "אנטי-וירוס", active: " (פעיל)",
    topMem: "מי תופס הכי הרבה זיכרון", thProgram: "תוכנה", thMem: "זיכרון", thProcs: "תהליכים", thCpu: "מעבד",
    startupTitle: "תוכנות שנפתחות עם המחשב", thName: "שם", thState: "מצב", thAdvice: "המלצה", enabled: "פעיל", disabled: "מושבת",
    cfScanTitle: "להתחיל סריקה?", cfScan: "הכלי יבדוק זיכרון, מעבד, תוכנות הפעלה, רשת ותיקיות מוכרות{deep}.\n\nהסריקה רק קוראת מידע. שום דבר לא נמחק ולא משתנה.",
    cfScanDeep: ", ויסרוק את כל הקבצים בכונן C (כמה דקות)", startScan: "התחל סריקה",
    cfSkipTitle: "לדלג על הסריקה המלאה?", cfSkip: "הסריקה המלאה של הכונן תיעצר. הדוח יוצג עם מה שנסרק עד עכשיו. רשימת הקבצים הגדולים תהיה חלקית.", cfSkipYes: "כן, דלג",
    cfQuitTitle: "לצאת מהתוכנה?", cfQuit: "התוכנה תיסגר. אפשר לפתוח אותה שוב עם start.bat.",
    closedTitle: "התוכנה נסגרה", closedText: "אפשר לסגור את החלון.",
    noTokenTitle: "חסר מפתח גישה", noTokenText: "פתח את התוכנה דרך start.bat. הכתובת הנכונה מודפסת בחלון השחור.",
    // undo / quarantine
    undoChk: "לשמור {days} ימים עם אפשרות ביטול",
    undoHint: "הקבצים יועברו לתיקיית הסגר ולא יימחקו. אפשר לשחזר אותם בלשונית \"ביטול פעולות\". המקום בדיסק יתפנה רק כשהם יימחקו סופית, אוטומטית אחרי {days} ימים.",
    undoLowDisk: "הדיסק כמעט מלא, ולכן האפשרות כבויה: כדי לפנות מקום עכשיו, הקבצים צריכים להימחק מיד.",
    doneQuarantined: "הועבר להסגר ({size}). אפשר לשחזר עד {date} בלשונית \"ביטול פעולות\".",
    tabUndo: "ביטול פעולות",
    undoLead: "קבצים שניקית עם אפשרות ביטול. הם נשמרים {days} ימים ואז נמחקים אוטומטית. כרגע הם תופסים {size}.",
    undoEmpty: "אין כרגע פעולות שאפשר לבטל. כשתנקה עם האפשרות \"לשמור {days} ימים\", הקבצים יופיעו כאן.",
    undoItems: "{n} פריטים", undoExpires: "יימחק סופית ב-{date}", undoShow: "מה יש בפנים",
    restore: "שחזר", purgeNow: "מחק עכשיו",
    cfRestoreTitle: "לשחזר את הקבצים?", cfRestore: "כל הקבצים של \"{title}\" ({size}) יחזרו בדיוק למקום שממנו הם הגיעו.\n\nאם תוכנה כבר יצרה קובץ חדש באותו מקום (למשל מטמון שנבנה מחדש), הקובץ החדש נשאר, והישן נשאר בהסגר.",
    cfPurgeTitle: "למחוק סופית?", cfPurge: "כל הקבצים של \"{title}\" ({size}) יימחקו לצמיתות, והמקום בדיסק יתפנה מיד.\n\nאחרי זה אי אפשר לשחזר אותם.",
    doneRestored: "שוחזר ({size}).", doneRestoredSkipped: " {n} פריטים נשארו בהסגר כי המקום המקורי כבר תפוס.",
    // share card
    shareTitle: "שתף את התוצאה", shareSub: "כרטיס עם מה שהשגת, לשיתוף בלינקדאין ובפייסבוק. המספרים נמדדים במחשב שלך.",
    shareNothing: "אחרי שתבצע צעד טיפול אחד לפחות, יופיע כאן כרטיס תוצאה לשיתוף.",
    cardHeadline: "ניקיתי {size} מהמחשב", cardFree: "מקום פנוי בדיסק", cardMem: "זיכרון בשימוש", cardStartup: "תוכנות שכבר לא נפתחות לבד",
    cardFooter: "רופא המחשב · חינמי ובקוד פתוח", saveImg: "שמור תמונה", copyText: "העתק טקסט", shareLi: "שתף בלינקדאין", shareFb: "שתף בפייסבוק",
    copied: "הטקסט הועתק. הדבק אותו בפוסט.", imgSaved: "התמונה נשמרה בתיקיית ההורדות.",
    shareText: "ניקיתי {size} מהמחשב עם רופא המחשב, כלי חינמי בקוד פתוח שמסביר כל פעולה לפני שהוא מבצע אותה.{free}{mem}\n{url}",
    shareTextFree: " המקום הפנוי בדיסק עלה מ-{a} ל-{b}.", shareTextMem: " הזיכרון בשימוש ירד מ-{a}% ל-{b}%.",
    // about
    about: "אודות", aboutTitle: "אודות רופא המחשב",
    aboutText: "כלי חינמי בקוד פתוח ל-Windows, שמסביר למה המחשב איטי ומה אפשר למחוק בבטחה, ומסביר כל פעולה לפני שהוא מבצע אותה.",
    aboutBy: "נוצר על ידי", aboutAuthor: "עוז לוי", aboutLinkedIn: "הפרופיל שלי בלינקדאין", aboutRepo: "קוד המקור ב-GitHub",
    aboutReleases: "גרסאות והורדות", aboutVersion: "גרסה {v}", aboutPrivacy: "התוכנה רצה רק על המחשב שלך ולא שולחת שום מידע.",
    // admin
    runAdmin: "הפעל כמנהל", cfAdminTitle: "להפעיל מחדש כמנהל?",
    cfAdmin: "התוכנה תיסגר ותיפתח מחדש עם הרשאות מנהל. Windows ישאל אם לאשר.\n\nעם הרשאות מנהל אפשר לנקות גם תיקיות מערכת (עדכונים ישנים, קבצים זמניים של Windows) ולבטל הפעלה אוטומטית של תוכנות שמותקנות לכל המשתמשים.\n\nתוצאות הסריקה הנוכחית לא יישמרו, ותצטרך לסרוק שוב.",
  },
  en: {
    appName: "PC Doctor", appSub: "Diagnose, clean up, and understand every action", langBtn: "עברית", quit: "Exit",
    introTitle: "Why is my PC slow?",
    introP1: "The scan checks memory, CPU, programs that start with the PC, the internet connection and every file on drive C. At the end you get an explanation of why the PC is slow and a list of steps to fix it. Every step has a Fix button.",
    introP2: "Nothing is deleted or changed during the scan. Before every action a window explains exactly what will happen, and it runs only after you confirm.",
    deepChk: "Full scan of the whole drive (takes a few minutes, and finds large files and folders)",
    scanBtn: "Scan my PC", skipDeep: "Skip the full drive scan",
    tabReport: "Why is my PC slow", tabClean: "What can I delete", tabDisk: "Large files and folders", tabSystem: "System details", rescan: "Scan again",
    sure: "Are you sure?", whatHappens: "What will happen:", yesDo: "Yes, do it", cancel: "Cancel", close: "Close", moreInfo: "More details",
    notMeasured: "Not measured", error: "Error",
    diskLabel: "Drive {root}", diskFree: "{free} free of {total} ({pct}% free)",
    admin: "Running as administrator", user: "Running as a regular user", adminTip: "Some cleanups require administrator rights",
    stage: "Step {n} of 4: {label}",
    stages: ["", "Checking memory, CPU, startup programs and network", "Measuring known junk and cache folders", "Scanning the whole drive (the long part)", "Preparing the report"],
    filesScanned: "{n} files, {size}", scanFailed: "The scan failed: ",
    sev: { high: "Serious", medium: "Worth fixing", low: "Good to know", ok: "OK" },
    statFree: "Free space on drive C", statSafe: "Can be freed safely", statMem: "Memory in use", statCpu: "CPU during the scan",
    leadOk: "No significant problems were found. Below are a few tips that can help.",
    leadIssues: "Found {n} main reasons for slowness, ordered from most important. Every step has a \"Fix\" button, and before any action you get an explanation and are asked to confirm.",
    stepsTitle: "Steps to fix", again: "Again", startsNow: "Starting now: ",
    breakQ: "Will this break anything?", secWhat: "What is it?", secDeleted: "Exactly what gets deleted, and from where", secThere: "What is there now",
    secHow: "How it is done", secNotAffected: "What is not affected", secAfter: "What does change afterwards", secUndo: "What if I change my mind?", secWhere: "Where it is configured",
    howClean: "The files are deleted permanently, not via the Recycle Bin, because they rebuild themselves. Files a running program is using are skipped, with no harm to the program.",
    howAge1: " Files created or changed in the last 24 hours are not deleted.", howAgeN: " Files created or changed in the last {n} days are not deleted.",
    howRecycle: "The Recycle Bin is emptied through the official Windows function, exactly like right-clicking the bin > \"Empty Recycle Bin\".",
    howCmd: "A command window will open{admin} and run the official command:\n{cmd}\nThe tool does not delete the files itself: Windows or the official tool does.",
    howCmdAdmin: " (Windows will ask for administrator approval)",
    howOpen: "A Windows screen will open. Nothing is deleted automatically. You perform the action on that screen.",
    allVerdict: "No. Everything in this list is temporary files, caches and crash files. None of it holds personal data, and every program recreates what it needs.",
    allWhat: "What this does", allWhatText: "This cleans {n} kinds of junk files, {size} in total. Click each kind to see what it is, exactly which folders are cleaned, and what is not affected.",
    allNever: "What is never affected",
    allNeverList: ["Your documents, photos, videos and downloads", "Installed programs. They all keep working",
      "In browsers: passwords, bookmarks, history, logins to sites and extensions", "Projects and code", "Windows, installed updates and settings"],
    allBefore: "Before you start", allBeforeText: "Close your browsers and open programs. It is not required, but then the files they hold open are cleaned too.",
    doneFreed: "Done. Freed {size}", doneSkipped: " ({n} files in use were skipped)",
    doneRecycled: "Moved to the Recycle Bin ({size}). To actually free the space, empty the Recycle Bin.", done: "Done",
    working: "Working…", deleting: "Deleting…", failed: "Failed: ",
    act: { clean: "Clean", recycle: "Empty", command: "Run", open: "Open" },
    chips: { all: "All", safe: "Safe to delete", caution: "Check first", windows: "Via Windows", keep: "Do not delete" },
    cleanLead: "Every location the tool knows on this PC: its size, what it is, and whether it is safe to delete. Sorted from largest to smallest in each group.",
    needAdmin: "Requires administrator rights. Click \"Run as administrator\" at the top.", empty: "Empty, nothing to clean", location: "Location ({n})",
    dtWhat: "What is it?", dtSafe: "Is it safe to delete?", dtHow: "How to clean",
    cfClean: "The contents of the following will be deleted permanently (not via the Recycle Bin):\n{paths}{more}\n\nSize: {size}\n\nWhat it means: {meaning}", cfMore: "\n…and {n} more",
    cfRecycle: "All items in the Recycle Bin ({size}) will be deleted permanently and cannot be restored.\n\nIf you are not sure what is in there, click \"Cancel\" and open the Recycle Bin first.",
    cfCmd: "A command window will open{admin} and run:\n{cmd}\n\nWhat it means: {meaning}", cfCmdAdmin: " asking for administrator rights",
    cfOpen: "A Windows screen will open. Nothing is deleted automatically.\n\nWhat to do there: {how}",
    dlTitle: "Downloads folder: files you have not touched for over a month", dlSub: "The tool deletes nothing here on its own. Check each file, and if you do not need it, move it to the Recycle Bin.",
    thFile: "File", thSize: "Size", thSafe: "Safe to delete?", thProject: "Project", modified: "Last modified: ",
    openLoc: "Open location", toBin: "To Recycle Bin", del: "Delete",
    cfOpenLoc: "Open location", cfOpenLocText: "File Explorer will open at:\n{path}\n\nNothing will be deleted.", open: "Open",
    cfBinTitle: "Move to the Recycle Bin?",
    cfBin: "The file will be moved to the Recycle Bin:\n{path}\nSize: {size}\n\nAbout this file: {hint}\n\nYou can restore it from the Recycle Bin until you empty it. The disk space is freed only after the bin is emptied.\nNote: a file larger than the space reserved for the Recycle Bin may be deleted permanently.",
    cfBinYes: "Yes, move to Recycle Bin",
    cfNmTitle: "Delete node_modules?",
    cfNm: "The folder will be deleted permanently (not via the Recycle Bin, because it holds tens of thousands of files):\n{path}\nSize: {size}\n\nWhat it means: the project's code is not affected. When you return to the project, run npm install (or pnpm install / yarn) in its folder to download the packages again. Do not delete it while the project is running.",
    cfNmYes: "Yes, delete",
    noDeep: "The full drive scan was not run. Click \"Scan again\" and check \"Full scan\".",
    whereTitle: "Where did the space go?", whereSub: "Folders over 200 MB on the drive. Click the arrow to look inside.", denied: "({n} system folders were not scanned due to permissions.)",
    largeTitle: "Large files (over 500 MB)", largeSub: "Every file has an explanation of whether it is safe to delete. The tool never deletes personal files on its own: you decide, and the file goes to the Recycle Bin.",
    noLarge: "No files over 500 MB were found.", nmTitle: "node_modules folders ({size})",
    nmSub: "Packages of JavaScript projects. You can delete them in projects you are not working on, and restore any time with npm install.", noneFound: "None found.",
    noSub: "No large subfolders.", expand: "Expand",
    sysMem: "Memory", inUse: "In use", ofTotal: "{used} of {total}", uptime: "Time since restart", days: "{n} days", power: "Power",
    onBattery: "On battery ({n}%)", plugged: "Plugged in", plan: "Power plan", diskNet: "Disk and network", health: "health: ", healthy: "healthy",
    noWifi: "Not on Wi-Fi", latency: "Response time", latencyVal: "average {avg}ms, max {max}ms", noNet: "No connection", av: "Antivirus", active: " (active)",
    topMem: "What uses the most memory", thProgram: "Program", thMem: "Memory", thProcs: "Processes", thCpu: "CPU",
    startupTitle: "Programs that start with the PC", thName: "Name", thState: "State", thAdvice: "Recommendation", enabled: "Enabled", disabled: "Disabled",
    cfScanTitle: "Start the scan?", cfScan: "The tool will check memory, CPU, startup programs, network and known folders{deep}.\n\nThe scan only reads information. Nothing is deleted or changed.",
    cfScanDeep: ", and scan every file on drive C (a few minutes)", startScan: "Start scan",
    cfSkipTitle: "Skip the full scan?", cfSkip: "The full drive scan will stop. The report will show what was scanned so far. The large files list will be partial.", cfSkipYes: "Yes, skip",
    cfQuitTitle: "Exit the program?", cfQuit: "The program will close. You can open it again with start.bat.",
    closedTitle: "The program has closed", closedText: "You can close this window.",
    noTokenTitle: "Missing access key", noTokenText: "Open the program through start.bat. The correct address is printed in the console window.",
    // undo / quarantine
    undoChk: "Keep for {days} days so I can undo",
    undoHint: "The files are moved to a quarantine folder instead of being deleted. You can restore them in the \"Undo\" tab. The disk space is freed only when they are deleted for good, automatically after {days} days.",
    undoLowDisk: "Your disk is almost full, so this is off: to free space now, the files need to be deleted right away.",
    doneQuarantined: "Moved to quarantine ({size}). You can restore it until {date} in the \"Undo\" tab.",
    tabUndo: "Undo",
    undoLead: "Files you cleaned with undo enabled. They are kept for {days} days and then deleted automatically. They currently use {size}.",
    undoEmpty: "Nothing to undo right now. When you clean with \"Keep for {days} days\" checked, the files appear here.",
    undoItems: "{n} items", undoExpires: "Deleted for good on {date}", undoShow: "What is inside",
    restore: "Restore", purgeNow: "Delete now",
    cfRestoreTitle: "Restore these files?", cfRestore: "All files of \"{title}\" ({size}) go back exactly where they came from.\n\nIf a program already created a new file in the same place (for example a rebuilt cache), the new file stays and the old one remains in quarantine.",
    cfPurgeTitle: "Delete for good?", cfPurge: "All files of \"{title}\" ({size}) will be deleted permanently, and the disk space is freed right away.\n\nAfter this they cannot be restored.",
    doneRestored: "Restored ({size}).", doneRestoredSkipped: " {n} items stayed in quarantine because their original place is taken.",
    // share card
    shareTitle: "Share your result", shareSub: "A card with what you achieved, for LinkedIn and Facebook. The numbers are measured on your PC.",
    shareNothing: "After you complete at least one fix, a result card to share appears here.",
    cardHeadline: "I cleaned up {size} on my PC", cardFree: "Free disk space", cardMem: "Memory in use", cardStartup: "Programs no longer starting on their own",
    cardFooter: "PC Doctor · free and open source", saveImg: "Save image", copyText: "Copy text", shareLi: "Share on LinkedIn", shareFb: "Share on Facebook",
    copied: "Text copied. Paste it into your post.", imgSaved: "The image was saved to your Downloads folder.",
    shareText: "I cleaned up {size} on my PC with PC Doctor, a free open-source tool that explains every action before it runs.{free}{mem}\n{url}",
    shareTextFree: " Free disk space went from {a} to {b}.", shareTextMem: " Memory in use dropped from {a}% to {b}%.",
    // about
    about: "About", aboutTitle: "About PC Doctor",
    aboutText: "A free, open-source Windows tool that explains why your PC is slow and what you can safely delete, and explains every action before it runs.",
    aboutBy: "Created by", aboutAuthor: "Oz Levi", aboutLinkedIn: "My LinkedIn profile", aboutRepo: "Source code on GitHub",
    aboutReleases: "Releases and downloads", aboutVersion: "Version {v}", aboutPrivacy: "The program runs only on your computer and sends no data.",
    // admin
    runAdmin: "Run as administrator", cfAdminTitle: "Restart as administrator?",
    cfAdmin: "The program will close and reopen with administrator rights. Windows will ask you to approve.\n\nWith administrator rights you can also clean system folders (old updates, Windows temp files) and stop programs installed for all users from starting automatically.\n\nThe current scan results are not kept, so you will need to scan again.",
  },
};

function initialLang() {
  const fromHash = HASH.get("lang");
  if (fromHash === "he" || fromHash === "en") return fromHash;
  try {
    const saved = localStorage.getItem("pcdoctor-lang");
    if (saved === "he" || saved === "en") return saved;
  } catch (e) { /* storage may be unavailable */ }
  return (navigator.language || "").toLowerCase().startsWith("he") ? "he" : "en";
}
let LANG = initialLang();

/** Look up a UI string and fill {placeholders}. */
function L(key, vars) {
  let s = STR[LANG][key];
  if (s === undefined) s = STR.he[key];
  if (vars && typeof s === "string") s = s.replace(/\{(\w+)\}/g, (_, k) => (vars[k] ?? ""));
  return s;
}
/** Rule texts in the current language. */
const rt = (r) => r.text[LANG];
/** Report findings in the current language. */
const findings = () => STATE.results.findings[LANG] || STATE.results.findings.he;
/** A value that may be {he, en} or a plain string. */
const pick = (v) => (v && typeof v === "object" ? v[LANG] : v) || "";

function applyLang() {
  document.documentElement.lang = LANG;
  document.documentElement.dir = LANG === "he" ? "rtl" : "ltr";
  document.title = L("appName");
  document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = L(el.dataset.i18n); });
  try { localStorage.setItem("pcdoctor-lang", LANG); } catch (e) { /* ignore */ }
}

// ================================================================= utils
function fmt(bytes) {
  if (bytes == null) return L("notMeasured");
  const u = ["B", "KB", "MB", "GB", "TB"];
  let i = 0, n = bytes;
  while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
  // LRI ... PDI isolate direction so Hebrew text shows "12.7 GB", not "GB 12.7"
  const LRI = String.fromCharCode(0x2066), PDI = String.fromCharCode(0x2069);
  return LRI + (i >= 3 ? n.toFixed(1) : Math.round(n)) + " " + u[i] + PDI;
}
const num = (n) => Number(n).toLocaleString(LANG === "he" ? "he-IL" : "en-US");

async function api(path, body) {
  const opts = { headers: { "X-Token": TOKEN, "X-Lang": LANG } };
  if (body !== undefined) {
    opts.method = "POST";
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const r = await fetch(path, opts);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || L("error"));
  return data;
}

function toast(msg, ms = 4000) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.remove("hidden");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => t.classList.add("hidden"), ms);
}

const SAFETY_CLS = { safe: "b-safe", caution: "b-caution", windows: "b-windows", keep: "b-keep" };
const SAFETY_TEXT = {
  he: { safe: "בטוח למחוק", caution: "בדוק לפני שמוחקים", windows: "לפנות רק דרך Windows", keep: "לא למחוק" },
  en: { safe: "Safe to delete", caution: "Check before deleting", windows: "Only through Windows", keep: "Do not delete" },
};
const sbadge = (s) => `<span class="badge ${SAFETY_CLS[s]}">${esc(SAFETY_TEXT[LANG][s])}</span>`;

// ========================================================= confirm modal
/**
 * Every action goes through here: explain what will happen, run only after "Yes".
 * With opts.undoable, the dialog offers "keep for 7 days so I can undo" and the
 * promise resolves to {undo: true|false} instead of true.
 */
function confirmAction(title, text, yesLabel, danger = false, opts = {}) {
  return new Promise((resolve) => {
    $("#mTitle").textContent = title;
    $("#mText").textContent = text;
    const box = $("#mUndo");
    if (opts.undoable) {
      const days = (STATE && STATE.quarantine && STATE.quarantine.days) || 7;
      const low = STATE && STATE.disk && STATE.disk.free / STATE.disk.total < 0.10;
      $("#mUndoChk").checked = !low;
      $("#mUndoLabel").textContent = L("undoChk", { days });
      $("#mUndoHint").textContent = L("undoHint", { days }) + (low ? " " + L("undoLowDisk") : "");
      box.classList.remove("hidden");
    } else {
      box.classList.add("hidden");
    }
    const yes = $("#mYes"), no = $("#mNo"), modal = $("#modal");
    yes.textContent = yesLabel || L("yesDo");
    yes.className = "btn " + (danger ? "danger" : "primary");
    modal.classList.remove("hidden");
    no.focus();
    const done = (v) => {
      modal.classList.add("hidden");
      yes.onclick = no.onclick = modal.onclick = document.onkeydown = null;
      resolve(v);
    };
    yes.onclick = () => done(opts.undoable ? { undo: $("#mUndoChk").checked } : true);
    no.onclick = () => done(false);
    modal.onclick = (e) => { if (e.target === modal) done(false); };
    document.onkeydown = (e) => { if (e.key === "Escape") done(false); };
  });
}

// ================================================================ header
function renderDisk(d) {
  if (!d) return;
  const pct = d.used / d.total * 100;
  const freePct = 100 - pct;
  const cls = freePct < 10 ? "crit" : freePct < 20 ? "warn" : "";
  $("#diskbox").innerHTML = `
    <div class="disk-row"><b>${esc(L("diskLabel", { root: d.root }))}</b><span class="num">${esc(L("diskFree", { free: fmt(d.free), total: fmt(d.total), pct: freePct.toFixed(0) }))}</span></div>
    <div class="disk-bar ${cls}"><div style="width:${pct.toFixed(1)}%"></div></div>`;
}

function renderAdmin(isAdmin) {
  const b = $("#adminBadge");
  b.className = "badge " + (isAdmin ? "b-safe" : "b-neutral");
  b.textContent = isAdmin ? L("admin") : L("user");
  b.title = isAdmin ? "" : L("adminTip");
  $("#adminBtn").classList.toggle("hidden", !!isAdmin);
  $("#adminBtn").textContent = L("runAdmin");
  if (STATE && STATE.version) $("#ver").textContent = "v" + STATE.version;
}

// =============================================================== polling
async function refresh() {
  try {
    STATE = await api("/api/state");
  } catch (e) {
    schedule(1500);  // server busy or still starting: try again shortly
    return;
  }
  renderDisk(STATE.disk);
  renderAdmin(STATE.admin);
  const s = STATE.scan;
  if (s.status === "running") {
    showOnly("progress");
    const stage = s.stage || 1;
    $("#progLabel").textContent = L("stage", { n: stage, label: L("stages")[stage] });
    $("#progBar").style.width = (s.pct || 0) + "%";
    $("#progPct").textContent = (s.pct || 0) + "%";
    $("#progFiles").textContent = s.files ? L("filesScanned", { n: num(s.files), size: fmt(s.scanned) }) : "";
    $("#progDetail").textContent = pick(s.detail);
    $("#cancelBtn").classList.toggle("hidden", s.stage !== 3);
    schedule(700);
  } else if (s.status === "done" && STATE.results) {
    stopPoll();
    showOnly("results");
    renderAll();
    if (HASH.get("tab")) openTab(HASH.get("tab"));
    if (HASH.get("info")) showStepInfo(HASH.get("info"));
  } else if (s.status === "error") {
    stopPoll();
    showOnly("intro");
    toast(L("scanFailed") + s.error, 8000);
  } else {
    showOnly("intro");
  }
  if (HASH.get("about") && !refresh._about) { refresh._about = 1; showAbout(); }
}
function schedule(ms) { stopPoll(); pollTimer = setTimeout(refresh, ms); }
function stopPoll() { clearTimeout(pollTimer); }
function showOnly(id) {
  for (const x of ["intro", "progress", "results"]) $("#" + x).classList.toggle("hidden", x !== id);
}

// ================================================================== tabs
let currentTab = "report";
document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => openTab(t.dataset.tab)));
function openTab(name, anchor) {
  currentTab = name;
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
  document.querySelectorAll(".tabpane").forEach((p) => p.classList.toggle("hidden", p.id !== "tab-" + name));
  if (anchor) {
    const el = document.getElementById(anchor);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  } else window.scrollTo({ top: 0 });
}

function renderAll() {
  renderReport();
  renderClean();
  renderDiskTab();
  renderSystem();
  renderUndo();
}

// ================================================================ report
const SEV_CLS = { high: "b-keep", medium: "b-caution", low: "b-windows", ok: "b-safe" };

function renderReport() {
  const R = STATE.results;
  const f = findings();
  const issues = f.filter((x) => x.severity === "high" || x.severity === "medium");
  const mem = R.diag.memory;
  const safeTotal = R.rules.filter((r) => r.safety === "safe" && r.action === "clean").reduce((a, r) => a + (r.size || 0), 0);
  const lead = issues.length ? L("leadIssues", { n: issues.length }) : L("leadOk");

  $("#tab-report").innerHTML = `
    <div class="summary">
      <div class="stat"><div class="k">${esc(L("statFree"))}</div><div class="v num">${fmt(STATE.disk.free)}</div></div>
      <div class="stat"><div class="k">${esc(L("statSafe"))}</div><div class="v num">${fmt(safeTotal)}</div></div>
      <div class="stat"><div class="k">${esc(L("statMem"))}</div><div class="v num">${mem.load}%</div></div>
      <div class="stat"><div class="k">${esc(L("statCpu"))}</div><div class="v num">${R.diag.processes.total_cpu}%</div></div>
    </div>
    ${shareSection()}
    <p class="lead">${esc(lead)}</p>
    ${f.map(renderFinding).join("")}`;
  bindShare();

  $("#tab-report").querySelectorAll("[data-step]").forEach((b) => b.addEventListener("click", () => doStep(b.dataset.step)));
  $("#tab-report").querySelectorAll("[data-info]").forEach((b) => b.addEventListener("click", () => showStepInfo(b.dataset.info)));
}

function renderFinding(f) {
  let n = 0;
  const steps = (f.steps || []).map((s) => {
    n++;
    const done = STATE.done_steps[s.id];
    const res = done ? resultText(done) : "";
    const act = s.disabled_reason
      ? `<span class="note">${esc(s.disabled_reason)}</span>`
      : `<button class="btn ${s.action.type === "goto" ? "ghost" : "primary"} small" data-step="${esc(s.id)}">${done ? esc(L("again")) : esc(s.button)}</button>`;
    const hasInfo = s.info || (s.info_rules && s.info_rules.length);
    const info = hasInfo ? `<button class="i-btn" data-info="${esc(s.id)}" title="${esc(L("moreInfo"))}" aria-label="${esc(L("moreInfo"))}: ${esc(s.title)}">i</button>` : "";
    return `<div class="step ${done ? "done" : ""}">
      <div class="step-n">${done ? "✓" : n}</div>
      <div class="step-body">
        <div class="step-title">${esc(s.title)}</div>
        <div class="step-desc">${esc(s.desc)}</div>
        ${res ? `<div class="step-result">${esc(res)}</div>` : ""}
      </div>
      <div class="step-actions">${info}${act}</div>
    </div>`;
  }).join("");
  const extra = f.extra && f.extra.length ? `<div class="small muted" style="margin-top:6px">${esc(L("startsNow"))}${esc(f.extra.join(", "))}</div>` : "";
  return `<article class="finding sev-${f.severity}">
    <div class="f-head">
      <div style="flex:1">
        <h3>${esc(f.title)}</h3>
        <p class="f-why">${esc(f.why)}</p>
        ${extra}
      </div>
      <span class="badge ${SEV_CLS[f.severity]}">${esc(L("sev")[f.severity])}</span>
    </div>
    ${steps ? `<div class="steps"><div class="steps-title">${esc(L("stepsTitle"))}</div>${steps}</div>` : ""}
  </article>`;
}

function fmtDate(ts) {
  return new Date(ts * 1000).toLocaleDateString(LANG === "he" ? "he-IL" : "en-US", { day: "numeric", month: "long", year: "numeric" });
}

function resultText(r) {
  if (r.quarantined != null) return L("doneQuarantined", { size: fmt(r.quarantined), date: r.expires ? fmtDate(r.expires) : "" }) +
    (r.skipped ? L("doneSkipped", { n: num(r.skipped) }) : "");
  if (r.freed != null) return L("doneFreed", { size: fmt(r.freed) }) + (r.skipped ? L("doneSkipped", { n: num(r.skipped) }) : "");
  if (r.recycled != null) return L("doneRecycled", { size: fmt(r.recycled) });
  return r.message || L("done");
}

function findStep(id) {
  for (const f of findings()) for (const s of f.steps || []) if (s.id === id) return s;
  return null;
}

async function doStep(id) {
  const s = findStep(id);
  if (!s) return;
  if (s.action.type === "goto") return openTab(s.action.tab, s.action.anchor);
  const undoable = s.action.type === "clean_rules";
  const ok = await confirmAction(L("sure") + " " + s.title, s.confirm, L("yesDo"), s.action.type === "restart", { undoable });
  if (!ok) return;
  toast(L("working"), 600000);
  try {
    const r = await api("/api/fix", { step: id, undo: !!(ok && ok.undo) });
    STATE.done_steps[id] = r.result;
    if (r.disk) { STATE.disk = r.disk; renderDisk(r.disk); }
    toast(resultText(r.result), 6000);
    await refreshStats();
    renderReport();
    if (r.result.quarantined != null) renderUndo();
  } catch (e) {
    toast(L("failed") + e.message, 8000);
  }
}

// ==================================================== detailed info popup
const li = (arr, cls) => arr && arr.length ? `<ul class="${cls}">${arr.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : "";
const sec = (title, html) => html ? `<div class="info-sec"><h4>${esc(title)}</h4>${html}</div>` : "";
const para = (t) => t ? `<p>${esc(t)}</p>` : "";

function verdictBox(text, safety) {
  if (!text) return "";
  const warn = safety && safety !== "safe";
  return `<div class="verdict ${warn ? "warn" : ""}"><b>${esc(L("breakQ"))}</b><span>${esc(text)}</span></div>`;
}

function howItRuns(r) {
  if (r.action === "clean") {
    let t = L("howClean");
    if (r.min_age_days) t += r.min_age_days === 1 ? L("howAge1") : L("howAgeN", { n: r.min_age_days });
    return t;
  }
  if (r.action === "recycle") return L("howRecycle");
  if (r.action === "command") return L("howCmd", { admin: r.admin ? L("howCmdAdmin") : "", cmd: r.command });
  if (r.action === "open") return L("howOpen");
  return "";
}

function ruleInfoHtml(r) {
  const d = rt(r);
  const paths = r.path_sizes && r.path_sizes.length
    ? `<div class="path-wrap"><table class="path-tbl">${r.path_sizes.map((p) =>
        `<tr><td class="mono">${esc(p.path)}</td><td class="num">${fmt(p.size)}</td></tr>`).join("")}</table></div>` : "";
  const how = howItRuns(r);
  return verdictBox(d.verdict, r.safety) +
    sec(L("secWhat"), para(d.what) + (d.details ? `<p style="margin-top:6px">${esc(d.details)}</p>` : "")) +
    sec(r.action === "command" || r.action === "open" ? L("secThere") : L("secDeleted"), paths) +
    sec(L("secHow"), how ? `<div class="howbox" style="white-space:pre-wrap">${esc(how)}</div>` : "") +
    sec(L("secNotAffected"), li(d.not_affected, "ok-list")) +
    sec(L("secAfter"), li(d.after, "chg-list")) +
    sec(L("secUndo"), para(d.undo));
}

function openInfo(title, bodyHtml, actLabel, onAct) {
  $("#iTitle").textContent = title;
  $("#iBody").innerHTML = bodyHtml;
  $("#iBody").scrollTop = 0;
  const modal = $("#info"), act = $("#iAct");
  act.classList.toggle("hidden", !actLabel);
  act.textContent = actLabel || "";
  modal.classList.remove("hidden");
  $("#iNo").focus();
  const close = () => {
    modal.classList.add("hidden");
    act.onclick = $("#iNo").onclick = $("#iClose").onclick = modal.onclick = document.onkeydown = null;
  };
  act.onclick = () => { close(); onAct && onAct(); };
  $("#iNo").onclick = $("#iClose").onclick = close;
  modal.onclick = (e) => { if (e.target === modal) close(); };
  document.onkeydown = (e) => { if (e.key === "Escape") close(); };
}

function showStepInfo(id) {
  const s = findStep(id);
  if (!s) return;
  let html = "";
  if (s.info_rules && s.info_rules.length) {
    const rs = s.info_rules.map((rid) => STATE.results.rules.find((r) => r.id === rid)).filter(Boolean);
    if (rs.length === 1) {
      html = ruleInfoHtml(rs[0]);
    } else {
      const total = rs.reduce((a, r) => a + (r.size || 0), 0);
      html = verdictBox(L("allVerdict"), "safe") +
        sec(L("allWhat"), para(L("allWhatText", { n: rs.length, size: fmt(total) }))) +
        sec(L("allNever"), li(L("allNeverList"), "ok-list")) +
        sec(L("allBefore"), para(L("allBeforeText"))) +
        rs.map((r) => `<details class="rule-sec"><summary><span>${esc(rt(r).title)}</span>${sbadge(r.safety)}<span class="sz">${fmt(r.size)}</span></summary>
          <div class="rule-sec-body">${ruleInfoHtml(r)}</div></details>`).join("");
    }
  } else if (s.info) {
    const d = s.info;
    html = verdictBox(d.verdict, "safe") +
      sec(L("secWhat"), para(d.details)) +
      sec(L("secWhere"), d.where ? `<div class="path-wrap"><table class="path-tbl">${d.where.map((w) => `<tr><td class="mono">${esc(w)}</td></tr>`).join("")}</table></div>` : "") +
      sec(L("secNotAffected"), li(d.not_affected, "ok-list")) +
      sec(L("secAfter"), li(d.after, "chg-list")) +
      sec(L("secUndo"), para(d.undo));
  }
  openInfo(s.title, html, s.disabled_reason ? "" : s.button, () => doStep(id));
}

function showRuleInfo(id) {
  const r = STATE.results.rules.find((x) => x.id === id);
  if (!r) return;
  const label = L("act")[r.action];
  const act = label && !r.needs_admin_now && !(r.action === "clean" && !r.size) ? label : "";
  openInfo(rt(r).title, ruleInfoHtml(r), act, () => doRule(id));
}

// =================================================== what can be deleted
const CAT_ORDER = ["system", "browser", "apps", "dev", "big"];

function renderClean() {
  const R = STATE.results;
  const counts = { all: R.rules.length };
  for (const r of R.rules) counts[r.safety] = (counts[r.safety] || 0) + 1;
  const chips = ["all", "safe", "caution", "windows", "keep"]
    .map((k) => `<button class="chip ${safetyFilter === k ? "on" : ""}" data-f="${k}">${esc(L("chips")[k])} (${counts[k] || 0})</button>`).join("");

  let html = `<p class="lead">${esc(L("cleanLead"))}</p><div class="filters">${chips}</div>`;
  for (const cat of CAT_ORDER) {
    const items = R.rules.filter((r) => r.category === cat && (safetyFilter === "all" || r.safety === safetyFilter))
      .sort((a, b) => (b.size || 0) - (a.size || 0));
    if (!items.length) continue;
    html += `<div class="cat-title">${esc(rt(items[0]).category_label)}</div>` + items.map(ruleCard).join("");
  }
  if (safetyFilter === "all" || safetyFilter === "caution") html += downloadsSection(R.downloads);
  $("#tab-clean").innerHTML = html;
  $("#tab-clean").querySelectorAll("[data-f]").forEach((c) => c.addEventListener("click", () => { safetyFilter = c.dataset.f; renderClean(); }));
  $("#tab-clean").querySelectorAll("[data-rule]").forEach((b) => b.addEventListener("click", () => doRule(b.dataset.rule)));
  $("#tab-clean").querySelectorAll("[data-rinfo]").forEach((b) => b.addEventListener("click", () => showRuleInfo(b.dataset.rinfo)));
  bindFileButtons($("#tab-clean"));
}

function ruleCard(r) {
  const t = rt(r);
  const act = L("act")[r.action];
  let btn = "";
  if (act) {
    if (r.needs_admin_now) btn = `<span class="note small muted">${esc(L("needAdmin"))}</span>`;
    else if (r.action === "clean" && !r.size) btn = `<span class="small muted">${esc(L("empty"))}</span>`;
    else btn = `<button class="btn ${r.safety === "safe" ? "primary" : ""} small" data-rule="${esc(r.id)}">${esc(act)}</button>`;
  }
  const paths = r.paths && r.paths.length
    ? `<details class="paths"><summary>${esc(L("location", { n: r.paths.length }))}</summary><ul>${r.paths.map((p) => `<li class="mono">${esc(p)}</li>`).join("")}</ul></details>` : "";
  return `<div class="card">
    <div class="card-head"><h3>${esc(t.title)}</h3>${sbadge(r.safety)}<span class="size">${fmt(r.size)}</span>
      <button class="i-btn" data-rinfo="${esc(r.id)}" title="${esc(L("moreInfo"))}" aria-label="${esc(L("moreInfo"))}: ${esc(t.title)}">i</button></div>
    <dl class="explain">
      <dt>${esc(L("dtWhat"))}</dt><dd>${esc(t.what)}</dd>
      <dt>${esc(L("dtSafe"))}</dt><dd>${esc(t.if_deleted)}</dd>
      <dt>${esc(L("dtHow"))}</dt><dd>${esc(t.how)}</dd>
    </dl>
    ${paths}
    <div class="card-actions">${btn}</div>
  </div>`;
}

async function doRule(id) {
  const r = STATE.results.rules.find((x) => x.id === id);
  const t = rt(r);
  let text;
  if (r.action === "clean") {
    text = L("cfClean", {
      paths: r.paths.slice(0, 15).map((p) => "• " + p).join("\n"),
      more: r.paths.length > 15 ? L("cfMore", { n: r.paths.length - 15 }) : "",
      size: fmt(r.size), meaning: t.if_deleted,
    });
  } else if (r.action === "recycle") {
    text = L("cfRecycle", { size: fmt(r.size) });
  } else if (r.action === "command") {
    text = L("cfCmd", { admin: r.admin ? L("cfCmdAdmin") : "", cmd: r.command, meaning: t.if_deleted });
  } else {
    text = L("cfOpen", { how: t.how });
  }
  const ok = await confirmAction(L("sure") + " " + t.title, text, L("yesDo"), false, { undoable: r.action === "clean" });
  if (!ok) return;
  toast(L("working"), 600000);
  try {
    const res = await api("/api/rule", { rule: id, undo: !!(ok && ok.undo) });
    if (res.disk) { STATE.disk = res.disk; renderDisk(res.disk); }
    if (res.result.freed != null && r.action !== "command") r.size = Math.max(0, (r.size || 0) - res.result.freed);
    toast(resultText(res.result), 6000);
    await refreshStats();
    renderClean();
    renderReport();
    if (res.result.quarantined != null) renderUndo();
  } catch (e) {
    toast(L("failed") + e.message, 8000);
  }
}

function downloadsSection(list) {
  if (!list || !list.length) return "";
  return `<div class="cat-title">${esc(L("dlTitle"))}</div>
    <p class="section-sub">${esc(L("dlSub"))}</p>
    ${fileTable(list, true)}`;
}

// ===================================================== files / folders
function fileTable(list, showDate) {
  return `<table class="tbl"><thead><tr><th>${esc(L("thFile"))}</th><th>${esc(L("thSize"))}</th><th>${esc(L("thSafe"))}</th><th></th></tr></thead><tbody>
    ${list.map((x) => `<tr>
      <td><div class="mono small">${esc(x.path)}</div>${showDate && x.mtime ? `<div class="small muted">${esc(L("modified"))}${new Date(x.mtime * 1000).toLocaleDateString(LANG === "he" ? "he-IL" : "en-US")}</div>` : ""}</td>
      <td class="num">${fmt(x.size)}</td>
      <td>${sbadge(x.safety)}<div class="small">${esc(pick(x.hint))}</div></td>
      <td class="act">
        <button class="btn small ghost" data-open="${esc(x.path)}">${esc(L("openLoc"))}</button>
        ${x.safety === "keep" ? "" : `<button class="btn small" data-recycle="${esc(x.path)}" data-size="${x.size}" data-hint="${esc(pick(x.hint))}">${esc(L("toBin"))}</button>`}
      </td></tr>`).join("")}
  </tbody></table>`;
}

function bindFileButtons(root) {
  root.querySelectorAll("[data-open]").forEach((b) => b.addEventListener("click", async () => {
    const ok = await confirmAction(L("cfOpenLoc"), L("cfOpenLocText", { path: b.dataset.open }), L("open"));
    if (!ok) return;
    api("/api/open_location", { path: b.dataset.open }).catch((e) => toast(e.message));
  }));
  root.querySelectorAll("[data-recycle]").forEach((b) => b.addEventListener("click", async () => {
    const p = b.dataset.recycle;
    const ok = await confirmAction(L("cfBinTitle"), L("cfBin", { path: p, size: fmt(+b.dataset.size), hint: b.dataset.hint }), L("cfBinYes"));
    if (!ok) return;
    try {
      const r = await api("/api/recycle_file", { path: p });
      b.closest("tr").remove();
      if (r.disk) renderDisk(r.disk);
      toast(resultText(r.result), 6000);
    } catch (e) { toast(L("failed") + e.message, 8000); }
  }));
  root.querySelectorAll("[data-nm]").forEach((b) => b.addEventListener("click", async () => {
    const p = b.dataset.nm;
    const ok = await confirmAction(L("cfNmTitle"), L("cfNm", { path: p, size: fmt(+b.dataset.size) }), L("cfNmYes"), true, { undoable: true });
    if (!ok) return;
    toast(L("deleting"), 600000);
    try {
      const r = await api("/api/delete_nm", { path: p, undo: !!ok.undo });
      b.closest("tr").remove();
      if (r.disk) renderDisk(r.disk);
      toast(resultText(r.result), 6000);
      await refreshStats();
      renderReport();
      if (r.result.quarantined != null) renderUndo();
    } catch (e) { toast(L("failed") + e.message, 8000); }
  }));
}

function renderDiskTab() {
  const D = STATE.results.disk;
  const el = $("#tab-disk");
  if (!D) {
    el.innerHTML = `<div class="empty">${esc(L("noDeep"))}</div>`;
    return;
  }
  const nmTotal = D.node_modules.reduce((a, x) => a + x.size, 0);
  el.innerHTML = `
    <h2 class="section-title">${esc(L("whereTitle"))}</h2>
    <p class="section-sub">${esc(L("whereSub"))} ${D.denied ? esc(L("denied", { n: num(D.denied) })) : ""}</p>
    <div class="tree" id="treeRoot"></div>

    <h2 class="section-title" id="large">${esc(L("largeTitle"))}</h2>
    <p class="section-sub">${esc(L("largeSub"))}</p>
    ${D.large_files.length ? fileTable(D.large_files) : `<div class="empty">${esc(L("noLarge"))}</div>`}

    <h2 class="section-title" id="nm">${esc(L("nmTitle", { size: fmt(nmTotal) }))}</h2>
    <p class="section-sub">${esc(L("nmSub"))}</p>
    ${D.node_modules.length ? `<table class="tbl"><thead><tr><th>${esc(L("thProject"))}</th><th>${esc(L("thSize"))}</th><th></th></tr></thead><tbody>
      ${D.node_modules.map((x) => `<tr><td class="mono small">${esc(x.project)}</td><td class="num">${fmt(x.size)}</td>
        <td class="act"><button class="btn small ghost" data-open="${esc(x.path)}">${esc(L("openLoc"))}</button>
        <button class="btn small" data-nm="${esc(x.path)}" data-size="${x.size}">${esc(L("del"))}</button></td></tr>`).join("")}
    </tbody></table>` : `<div class="empty">${esc(L("noneFound"))}</div>`}`;
  bindFileButtons(el);
  loadTree(D.root, $("#treeRoot"), D.total);
}

const ARROW_CLOSED = () => (LANG === "he" ? "◀" : "▶");

async function loadTree(path, container, parentSize) {
  const kids = await api("/api/tree?lang=" + LANG + "&path=" + encodeURIComponent(path));
  if (!kids.length) { container.innerHTML = `<div class="small muted" style="padding:4px 12px">${esc(L("noSub"))}</div>`; return; }
  container.innerHTML = kids.map((k, i) => `
    <div class="node">
      <div class="node-row">
        <button class="twisty" data-i="${i}" ${k.has_children ? "" : "disabled style='visibility:hidden'"} aria-label="${esc(L("expand"))}">${ARROW_CLOSED()}</button>
        <span class="node-name" title="${esc(k.path)}">${esc(k.name)}</span>
        <span class="node-size">${fmt(k.size)}</span>
        <span class="node-bar"><div style="width:${Math.min(100, k.size / parentSize * 100).toFixed(1)}%"></div></span>
        <span class="node-hint">${esc(k.hint)}</span>
      </div>
      <div class="children hidden"></div>
    </div>`).join("");
  container.querySelectorAll(".twisty").forEach((b) => b.addEventListener("click", async () => {
    const k = kids[+b.dataset.i];
    const ch = b.closest(".node").querySelector(".children");
    const open = ch.classList.toggle("hidden") === false;
    b.textContent = open ? "▼" : ARROW_CLOSED();
    if (open && !ch.dataset.loaded) { ch.dataset.loaded = 1; await loadTree(k.path, ch, k.size); }
  }));
}

// ================================================================ system
function renderSystem() {
  const d = STATE.results.diag;
  const p = d.processes;
  const net = d.network;
  $("#tab-system").innerHTML = `<div class="grid2">
    <div class="card"><h3>${esc(L("sysMem"))}</h3><div class="kv" style="margin-top:8px">
      <span class="k">${esc(L("inUse"))}</span><span class="num">${d.memory.load}% (${esc(L("ofTotal", { used: fmt(d.memory.total - d.memory.avail), total: fmt(d.memory.total) }))})</span>
      <span class="k">${esc(L("uptime"))}</span><span class="num">${esc(L("days", { n: (d.uptime_h / 24).toFixed(1) }))}</span>
      <span class="k">${esc(L("power"))}</span><span>${esc(d.power.on_battery ? L("onBattery", { n: d.power.battery }) : L("plugged"))}</span>
      <span class="k">${esc(L("plan"))}</span><span class="small">${esc(d.power.scheme)}</span>
    </div></div>
    <div class="card"><h3>${esc(L("diskNet"))}</h3><div class="kv" style="margin-top:8px">
      ${d.disks.map((x) => `<span class="k">${esc(x.name)}</span><span>${esc(x.media)}, ${esc(L("health"))}${x.health === "Healthy" ? esc(L("healthy")) : esc(x.health)}</span>`).join("")}
      <span class="k">Wi-Fi</span><span>${net.wifi_signal != null ? net.wifi_signal + "% " + esc(net.wifi_band || "") : esc(L("noWifi"))}</span>
      <span class="k">${esc(L("latency"))}</span><span class="num">${esc(net.avg_ms != null ? L("latencyVal", { avg: net.avg_ms, max: net.max_ms }) : L("noNet"))}</span>
      <span class="k">${esc(L("av"))}</span><span>${d.antivirus.map((a) => esc(a.name) + (a.active ? esc(L("active")) : "")).join(", ")}</span>
    </div></div>
  </div>
  <h2 class="section-title">${esc(L("topMem"))}</h2>
  <table class="tbl"><thead><tr><th>${esc(L("thProgram"))}</th><th>${esc(L("thMem"))}</th><th>${esc(L("thProcs"))}</th><th>${esc(L("thCpu"))}</th></tr></thead><tbody>
    ${p.by_mem.map((x) => `<tr><td>${esc(x.name)}</td><td class="num">${fmt(x.mem)}</td><td class="num">${x.count}</td><td class="num">${x.cpu_pct}%</td></tr>`).join("")}
  </tbody></table>
  <h2 class="section-title">${esc(L("startupTitle"))}</h2>
  <table class="tbl"><thead><tr><th>${esc(L("thName"))}</th><th>${esc(L("thState"))}</th><th>${esc(L("thAdvice"))}</th></tr></thead><tbody>
    ${d.startup.map((s) => `<tr><td>${esc(s.display)}<div class="mono small muted">${esc(s.command)}</div></td>
      <td>${esc(s.enabled ? L("enabled") : L("disabled"))}</td><td class="small">${esc(pick(s.advice))}</td></tr>`).join("")}
  </tbody></table>`;
}

// ================================================================== undo
async function renderUndo() {
  const el = $("#tab-undo");
  let batches = [];
  try { batches = await api("/api/quarantine"); } catch (e) { /* ignore */ }
  const days = (STATE.quarantine && STATE.quarantine.days) || 7;
  const total = batches.reduce((a, b) => a + b.size, 0);
  $("#undoCount").textContent = batches.length ? `(${batches.length})` : "";
  if (!batches.length) {
    el.innerHTML = `<div class="empty">${esc(L("undoEmpty", { days }))}</div>`;
    return;
  }
  el.innerHTML = `<p class="lead">${esc(L("undoLead", { days, size: fmt(total) }))}</p>` + batches.map((b) => `
    <div class="card">
      <div class="card-head"><h3>${esc(pick(b.title))}</h3><span class="size">${fmt(b.size)}</span></div>
      <div class="small muted" style="margin-top:4px">${esc(fmtDate(b.created))} · ${esc(L("undoItems", { n: num(b.count) }))} · ${esc(L("undoExpires", { date: fmtDate(b.expires) }))}</div>
      <details class="paths"><summary>${esc(L("undoShow"))}</summary><ul>${b.sample.map((p) => `<li class="mono">${esc(p)}</li>`).join("")}${b.count > b.sample.length ? "<li>…</li>" : ""}</ul></details>
      <div class="card-actions">
        <button class="btn primary small" data-restore="${esc(b.id)}">${esc(L("restore"))}</button>
        <button class="btn small" data-purge="${esc(b.id)}">${esc(L("purgeNow"))}</button>
      </div>
    </div>`).join("");
  const find = (id) => batches.find((b) => b.id === id);
  el.querySelectorAll("[data-restore]").forEach((btn) => btn.addEventListener("click", async () => {
    const b = find(btn.dataset.restore);
    if (!await confirmAction(L("cfRestoreTitle"), L("cfRestore", { title: pick(b.title), size: fmt(b.size) }), L("restore"))) return;
    try {
      const r = await api("/api/quarantine/restore", { id: b.id });
      toast(L("doneRestored", { size: fmt(r.result.restored) }) + (r.result.skipped ? L("doneRestoredSkipped", { n: num(r.result.skipped) }) : ""), 7000);
      if (r.disk) renderDisk(r.disk);
      await refreshStats();
      renderUndo();
      renderReport();
    } catch (e) { toast(L("failed") + e.message, 8000); }
  }));
  el.querySelectorAll("[data-purge]").forEach((btn) => btn.addEventListener("click", async () => {
    const b = find(btn.dataset.purge);
    if (!await confirmAction(L("cfPurgeTitle"), L("cfPurge", { title: pick(b.title), size: fmt(b.size) }), L("purgeNow"), true)) return;
    toast(L("deleting"), 600000);
    try {
      const r = await api("/api/quarantine/purge", { id: b.id });
      toast(L("doneFreed", { size: fmt(r.result.freed) }), 6000);
      if (r.disk) renderDisk(r.disk);
      renderUndo();
    } catch (e) { toast(L("failed") + e.message, 8000); }
  }));
}

// ============================================================ share card
const REPO_URL = "https://github.com/ozlevi29/Analyzing-files-on-the-computer";

async function refreshStats() {
  try {
    const s = await api("/api/state");
    STATE.stats = s.stats;
    STATE.disk = s.disk;
    STATE.quarantine = s.quarantine;
  } catch (e) { /* ignore */ }
}

function cardData() {
  const st = STATE.stats || {};
  const base = st.baseline;
  if (!base || !st.actions) return null;
  const cleaned = (st.freed || 0) + (st.quarantined || 0);
  return {
    cleaned,
    freeBefore: base.free, freeNow: STATE.disk.free,
    memBefore: base.mem, memNow: st.mem_now,
    startup: st.startup_disabled || 0,
  };
}

const plain = (s) => s.replace(/[⁦⁩]/g, "");

function shareSection() {
  const d = cardData();
  if (!d) return "";
  return `<section class="share">
    <div class="share-head">
      <div><h2 class="section-title" style="margin:0">${esc(L("shareTitle"))}</h2>
      <p class="section-sub" style="margin:4px 0 0">${esc(L("shareSub"))}</p></div>
    </div>
    <canvas id="card" width="1200" height="630" aria-label="${esc(L("shareTitle"))}"></canvas>
    <div class="card-actions">
      <button class="btn primary small" id="saveCard">${esc(L("saveImg"))}</button>
      <button class="btn small" id="copyCard">${esc(L("copyText"))}</button>
      <button class="btn small" data-share="linkedin">${esc(L("shareLi"))}</button>
      <button class="btn small" data-share="facebook">${esc(L("shareFb"))}</button>
    </div>
  </section>`;
}

function drawCard(canvas, d) {
  const c = canvas.getContext("2d");
  const W = 1200, H = 630, rtl = LANG === "he";
  const font = (w, px) => `${w} ${px}px "Segoe UI", Arial, sans-serif`;
  /** Shrink the font until the text fits `maxW`. */
  const fit = (text, weight, px, maxW) => {
    c.font = font(weight, px);
    while (px > 14 && c.measureText(text).width > maxW) { px -= 2; c.font = font(weight, px); }
  };
  // background
  const g = c.createLinearGradient(0, 0, W, H);
  g.addColorStop(0, "#0f2a5c");
  g.addColorStop(1, "#1d4ed8");
  c.fillStyle = g;
  c.fillRect(0, 0, W, H);
  c.fillStyle = "rgba(255,255,255,0.06)";
  c.beginPath(); c.arc(rtl ? 120 : W - 120, 90, 260, 0, Math.PI * 2); c.fill();

  c.direction = rtl ? "rtl" : "ltr";
  c.textAlign = rtl ? "right" : "left";
  const x = rtl ? W - 70 : 70;
  // logo + name
  const lx = rtl ? W - 70 - 56 : 70;
  c.fillStyle = "#ffffff";
  roundRect(c, lx, 56, 56, 56, 14); c.fill();
  c.strokeStyle = "#1d4ed8"; c.lineWidth = 5; c.lineJoin = "round";
  c.beginPath();
  [[lx + 10, 86], [lx + 20, 86], [lx + 26, 70], [lx + 33, 100], [lx + 39, 80], [lx + 46, 86]].forEach(([px, py], i) => i ? c.lineTo(px, py) : c.moveTo(px, py));
  c.stroke();
  c.fillStyle = "#ffffff";
  c.font = font(700, 34);
  c.fillText(L("appName"), rtl ? lx - 20 : lx + 76, 96);

  // headline (fmt keeps direction isolates, so Hebrew shows "156.5 GB" in the right order)
  const headline = L("cardHeadline", { size: fmt(d.cleaned) });
  fit(headline, 800, 76, W - 140);
  c.fillText(headline, x, 250);

  // only numbers that actually improved
  const stats = [];
  if (d.freeNow > d.freeBefore) stats.push([L("cardFree"), `${plain(fmt(d.freeBefore))}  →  ${plain(fmt(d.freeNow))}`]);
  if (d.memNow < d.memBefore) stats.push([L("cardMem"), `${d.memBefore}%  →  ${d.memNow}%`]);
  if (d.startup) stats.push([L("cardStartup"), String(d.startup)]);
  if (stats.length) {
    const gap = 40;
    const colW = (W - 140 - gap * (stats.length - 1)) / stats.length;
    stats.forEach(([k, v], i) => {
      const cx = rtl ? W - 70 - i * (colW + gap) : 70 + i * (colW + gap);
      c.fillStyle = "rgba(255,255,255,0.72)";
      fit(k, 600, 26, colW);
      c.fillText(k, cx, 360);
      c.fillStyle = "#ffffff";
      c.save(); c.direction = "ltr";
      c.textAlign = rtl ? "right" : "left";
      fit(v, 700, 44, colW);
      c.fillText(v, cx, 418);
      c.restore();
    });
  }

  // footer
  c.fillStyle = "rgba(255,255,255,0.15)";
  c.fillRect(0, H - 90, W, 90);
  c.fillStyle = "#ffffff";
  c.font = font(600, 26);
  c.fillText(L("cardFooter"), x, H - 36);
  c.save(); c.direction = "ltr"; c.textAlign = rtl ? "left" : "right";
  c.font = font(400, 22);
  c.fillText(REPO_URL.replace("https://", ""), rtl ? 70 : W - 70, H - 38);
  c.restore();
}

function roundRect(c, x, y, w, h, r) {
  c.beginPath();
  c.moveTo(x + r, y); c.arcTo(x + w, y, x + w, y + h, r); c.arcTo(x + w, y + h, x, y + h, r);
  c.arcTo(x, y + h, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath();
}

function shareText(d) {
  const free = d.freeNow > d.freeBefore ? L("shareTextFree", { a: plain(fmt(d.freeBefore)), b: plain(fmt(d.freeNow)) }) : "";
  const mem = d.memNow < d.memBefore ? L("shareTextMem", { a: d.memBefore, b: d.memNow }) : "";
  return L("shareText", { size: plain(fmt(d.cleaned)), free, mem, url: REPO_URL });
}

function bindShare() {
  const canvas = $("#card");
  if (!canvas) return;
  const d = cardData();
  drawCard(canvas, d);
  $("#saveCard").onclick = () => {
    const a = document.createElement("a");
    a.href = canvas.toDataURL("image/png");
    a.download = "pc-doctor-result.png";
    a.click();
    toast(L("imgSaved"));
  };
  $("#copyCard").onclick = async () => {
    try { await navigator.clipboard.writeText(shareText(d)); toast(L("copied")); }
    catch (e) { toast(L("failed") + e.message); }
  };
  document.querySelectorAll("[data-share]").forEach((b) => (b.onclick = () => {
    navigator.clipboard.writeText(shareText(d)).catch(() => {});
    api("/api/open_share", { site: b.dataset.share }).then(() => toast(L("copied"), 6000)).catch((e) => toast(e.message));
  }));
}

// ================================================================= about
function showAbout() {
  const v = (STATE && STATE.version) || "";
  const link = (site, label) => `<button class="link-btn" data-link="${site}">${esc(label)}</button>`;
  const html = `
    <div class="about-hero">
      <div class="logo big-logo" aria-hidden="true"><svg viewBox="0 0 24 24" width="30" height="30"><path fill="currentColor" d="M3 4h18v12H3zM1 18h22v2H1z" opacity=".25"/><path fill="none" stroke="currentColor" stroke-width="2" d="M5 11h3l2-4 3 7 2-3h4"/></svg></div>
      <div><div class="about-name">${esc(L("appName"))}</div><div class="small muted">${esc(L("aboutVersion", { v }))}</div></div>
    </div>
    <p>${esc(L("aboutText"))}</p>
    <div class="info-sec"><h4>${esc(L("aboutBy"))}</h4>
      <p class="about-author">${esc(L("aboutAuthor"))}</p>
      ${link("author", L("aboutLinkedIn"))}
    </div>
    <div class="info-sec"><h4>GitHub</h4>
      ${link("repo", L("aboutRepo"))}<br>${link("releases", L("aboutReleases"))}
    </div>
    <p class="small muted">${esc(L("aboutPrivacy"))}</p>`;
  openInfo(L("aboutTitle"), html, "", null);
  document.querySelectorAll("#iBody [data-link]").forEach((b) => (b.onclick = () =>
    api("/api/open_link", { site: b.dataset.link }).catch((e) => toast(e.message))));
}
$("#aboutBtn").addEventListener("click", showAbout);

// =============================================================== buttons
$("#adminBtn").addEventListener("click", async () => {
  if (!await confirmAction(L("cfAdminTitle"), L("cfAdmin"), L("runAdmin"))) return;
  try { await api("/api/relaunch_admin", {}); } catch (e) { toast(e.message, 6000); }
});

async function startScan(deep) {
  const ok = await confirmAction(L("cfScanTitle"), L("cfScan", { deep: deep ? L("cfScanDeep") : "" }), L("startScan"));
  if (!ok) return;
  try {
    await api("/api/scan", { deep });
    showOnly("progress");
    refresh();
  } catch (e) { toast(e.message); }
}
$("#scanBtn").addEventListener("click", () => startScan($("#deepChk").checked));
$("#rescanBtn").addEventListener("click", () => { showOnly("intro"); });
$("#cancelBtn").addEventListener("click", async () => {
  const ok = await confirmAction(L("cfSkipTitle"), L("cfSkip"), L("cfSkipYes"));
  if (ok) api("/api/cancel", {});
});
$("#quitBtn").addEventListener("click", async () => {
  const ok = await confirmAction(L("cfQuitTitle"), L("cfQuit"), L("quit"));
  if (!ok) return;
  await api("/api/quit", {}).catch(() => {});
  document.body.innerHTML = `<main><div class="panel intro"><h2>${esc(L("closedTitle"))}</h2><p>${esc(L("closedText"))}</p></div></main>`;
});
$("#langBtn").addEventListener("click", () => {
  LANG = LANG === "he" ? "en" : "he";
  applyLang();
  if (STATE) {
    renderDisk(STATE.disk);
    renderAdmin(STATE.admin);
    if (STATE.results && STATE.scan.status === "done") {
      renderAll();
      openTab(currentTab);
    }
  }
});

applyLang();
if (!TOKEN) {
  document.body.innerHTML = `<main><div class="panel intro"><h2>${esc(L("noTokenTitle"))}</h2><p>${esc(L("noTokenText"))}</p></div></main>`;
} else {
  refresh();
}
