# -*- coding: utf-8 -*-
"""
Builds the "Why is my PC slow?" report, in Hebrew or English.

Each finding explains why something slows the PC down and lists treatment steps.
Each step holds:
    id        - unique id. The server only executes steps it built itself in the last report.
    title     - what to do.
    desc      - a short explanation.
    confirm   - exactly what happens on "Yes", shown in the confirmation dialog.
    action    - what the server does: clean_rules / empty_recycle / command / disable_startup /
                open / open_chrome / restart / goto (switch tab in the UI, no server action).
    info / info_rules - detailed content for the "i" popup.

The action and id of a step are identical in both languages, only the texts differ.
"""

import os
import re

from diagnostics import APPROVED, GB, gb

PERSONAL = {"he": "המסמכים, התמונות, הסרטונים וההורדות שלך", "en": "Your documents, photos, videos and downloads"}


def build_report(diag, rule_items, disk, lang="he"):
    def t(he, en):
        return he if lang == "he" else en

    findings = []
    by_id = {r["id"]: r for r in rule_items}
    sysdrive = os.environ.get("SystemDrive", "C:") + "\\"
    treat, open_ = t("טפל", "Fix"), t("פתח", "Open")

    def txt(r):
        return r["text"][lang]

    def step(sid, title, desc, confirm, action, button=None, **kw):
        return dict(id=sid, title=title, desc=desc, confirm=confirm, action=action, button=button or treat, **kw)

    # ------------------------------------------------------------ disk space
    d = next((x for x in diag["drives"] if x["root"].upper() == sysdrive.upper()), None)
    if d:
        free_pct = d["free"] / d["total"] * 100
        steps = []
        runnable = [r for r in rule_items if r["safety"] == "safe" and r["action"] == "clean"
                    and not r["needs_admin_now"] and (r["size"] or 0) > 50 * 1024 ** 2]
        runnable.sort(key=lambda r: -(r["size"] or 0))
        if runnable:
            total = sum(r["size"] for r in runnable)
            lines = "\n".join(f"• {txt(r)['title']} ({gb(r['size'])})" for r in runnable)
            steps.append(step(
                "clean_safe", t(f"ניקוי כל מה שבטוח למחוק ({gb(total)})", f"Clean everything that is safe to delete ({gb(total)})"),
                t("קבצים זמניים, מטמונים וקבצי קריסה שהמערכת והתוכנות יוצרות מחדש לבד.",
                  "Temporary files, caches and crash files that Windows and programs recreate on their own."),
                t("הפריטים הבאים יימחקו לצמיתות (לא דרך סל המחזור):\n", "The following will be deleted permanently (not via the Recycle Bin):\n") + lines +
                t("\n\nשום קובץ אישי, סיסמה, היסטוריה או פרויקט לא נמחק. קבצים שנמצאים כרגע בשימוש ידולגו. "
                  "מומלץ לסגור קודם את הדפדפנים ותוכנות פתוחות כדי שיימחק כמה שיותר.",
                  "\n\nNo personal file, password, history or project is deleted. Files currently in use are skipped. "
                  "Close your browsers and open programs first so as much as possible is cleaned."),
                dict(type="clean_rules", rules=[r["id"] for r in runnable]), size=total,
                info_rules=[r["id"] for r in runnable]))
        rb = by_id.get("recycle_bin")
        if rb and (rb["size"] or 0) > 100 * 1024 ** 2:
            n = rb.get("count", 0)
            steps.append(step("empty_recycle", t(f"ריקון סל המחזור ({gb(rb['size'])})", f"Empty the Recycle Bin ({gb(rb['size'])})"),
                              t("קבצים שמחקת עדיין תופסים מקום עד שהסל מתרוקן.", "Files you deleted still use space until the bin is emptied."),
                              t(f"כל {n} הפריטים בסל המחזור יימחקו לצמיתות ולא יהיה אפשר לשחזר אותם. "
                                "אם אתה לא בטוח, פתח קודם את סל המחזור ובדוק.",
                                f"All {n} items in the Recycle Bin will be deleted permanently and cannot be restored. "
                                "If you are not sure, open the Recycle Bin and check first."),
                              dict(type="empty_recycle"), size=rb["size"], info_rules=["recycle_bin"]))
        hib = by_id.get("hiberfil")
        if hib and (hib["size"] or 0) > GB:
            steps.append(step("hibernate_off", t(f"כיבוי קובץ השינה ({gb(hib['size'])})", f"Turn off the hibernation file ({gb(hib['size'])})"),
                              t("קובץ שנשמר למצב Hibernate. רוב האנשים לא משתמשים במצב הזה.",
                                "A file kept for Hibernate mode. Most people never use this mode."),
                              t("ייפתח חלון של Windows שיבקש הרשאות מנהל, ויריץ powercfg /h off.\n\n"
                                "מה ישתנה: אפשרות \"מצב שינה עמוקה\" תיעלם, וההדלקה מכבוי מלא תהיה איטית בכמה שניות. "
                                "מצב שינה רגיל (סגירת מכסה) ממשיך לעבוד כרגיל.\n"
                                "להחזרה בכל רגע: powercfg /h on בחלון מנהל.",
                                "A Windows window will open, ask for administrator rights and run powercfg /h off.\n\n"
                                "What changes: the \"Hibernate\" option disappears, and starting from a full shutdown takes a few seconds longer. "
                                "Regular Sleep (closing the lid) keeps working.\n"
                                "To undo at any time: powercfg /h on in an administrator window."),
                              dict(type="command", command="powercfg /h off", admin=True), size=hib["size"],
                              info_rules=["hiberfil"]))
        # large items not included in the safe clean: they need a command, or have a small cost
        for rid in ("pnpm_store", "gradle_cache", "automation_browsers", "chrome_ai_model", "android_studio_old", "browser_sw"):
            r = by_id.get(rid)
            if r and (r["size"] or 0) > GB:
                tx = txt(r)
                if r["action"] == "command":
                    steps.append(step("rule_" + rid, f"{tx['title']} ({gb(r['size'])})", tx["what"],
                                      tx["if_deleted"] + t("\n\nייפתח חלון פקודה שיריץ: ", "\n\nA command window will open and run: ") + r["command"],
                                      dict(type="command", command=r["command"], admin=r["admin"]), size=r["size"], info_rules=[rid]))
                else:
                    steps.append(step("rule_" + rid, f"{tx['title']} ({gb(r['size'])})", tx["what"],
                                      t("מה יימחק:\n", "What will be deleted:\n") + "\n".join("• " + p for p in r["paths"][:12]) +
                                      t("\n\nמה המשמעות: ", "\n\nWhat it means: ") + tx["if_deleted"],
                                      dict(type="clean_rules", rules=[rid]), size=r["size"], info_rules=[rid]))
        if disk and disk.get("node_modules"):
            nm_total = sum(x["size"] for x in disk["node_modules"])
            if nm_total > GB:
                n = len(disk["node_modules"])
                steps.append(step(
                    "goto_nm", t(f"תיקיות node_modules בפרויקטים ({gb(nm_total)})", f"node_modules folders in projects ({gb(nm_total)})"),
                    t(f"נמצאו {n} תיקיות node_modules. בפרויקטים שאתה לא עובד עליהם אפשר למחוק ולשחזר עם npm install.",
                      f"Found {n} node_modules folders. In projects you are not working on, you can delete them and restore with npm install."),
                    "", dict(type="goto", tab="disk", anchor="nm"), button=t("הצג רשימה", "Show list"),
                    info=dict(
                        verdict=t("הכפתור רק מציג רשימה. כל מחיקה שם היא לפרויקט אחד, ורק אחרי אישור.",
                                  "The button only shows a list. Each deletion there is for one project, and only after you confirm."),
                        details=t("כל פרויקט JavaScript (React, Node, Next.js וכו') מוריד את החבילות שהוא צריך לתיקייה בשם node_modules "
                                  "בתוך הפרויקט. התיקייה הזו לא מכילה קוד שכתבת, רק עותקים של חבילות מהאינטרנט. "
                                  "הרשימה שבקובץ package.json בפרויקט מאפשרת להוריד את כולן מחדש בפקודה אחת.",
                                  "Every JavaScript project (React, Node, Next.js, etc.) downloads the packages it needs into a folder called "
                                  "node_modules inside the project. This folder holds no code you wrote, only copies of packages from the internet. "
                                  "The list in the project's package.json lets you download them all again with one command."),
                        not_affected=[t("הקוד שכתבת: קבצי המקור, package.json, הגדרות הפרויקט", "The code you wrote: source files, package.json, project settings"),
                                      t("Git וההיסטוריה של הפרויקט", "Git and the project history"), t("פרויקטים אחרים", "Other projects")],
                        after=[t("הפרויקט לא ירוץ עד שתריץ בתיקייה שלו npm install (או pnpm install / yarn). זה לוקח דקה-שתיים ודורש אינטרנט.",
                                 "The project will not run until you run npm install (or pnpm install / yarn) in its folder. It takes a minute or two and needs internet."),
                               t("לכן כדאי למחוק רק בפרויקטים ישנים שאתה לא עובד עליהם עכשיו.",
                                 "So delete only in old projects you are not working on now.")],
                        undo=t("npm install בתיקיית הפרויקט.", "npm install in the project folder."))))
        if disk and disk.get("large_files"):
            steps.append(step(
                "goto_large", t("קבצים גדולים לבדיקה ידנית", "Large files to review yourself"),
                t("רשימת הקבצים הגדולים בכונן, עם הסבר לכל אחד אם אפשר למחוק.",
                  "The list of large files on the drive, with an explanation for each one of whether it can be deleted."),
                "", dict(type="goto", tab="disk", anchor="large"), button=t("הצג רשימה", "Show list"),
                info=dict(
                    verdict=t("הכפתור רק מציג רשימה. הכלי לא מוחק שם שום דבר לבד.",
                              "The button only shows a list. The tool never deletes anything there on its own."),
                    details=t("אלה כל הקבצים בכונן שגדולים מ-500 MB. ליד כל קובץ יש הסבר מה הוא לפי הסוג והמיקום שלו "
                              "(למשל: קובץ התקנה, סרטון, גיבוי דחוס, קובץ מערכת). על קבצי מערכת אין בכלל כפתור מחיקה.",
                              "These are all the files on the drive larger than 500 MB. Each has an explanation based on its type and location "
                              "(for example: installer, video, compressed backup, system file). System files have no delete button at all."),
                    not_affected=[t("שום דבר, עד שתבחר קובץ ותאשר", "Nothing, until you pick a file and confirm")],
                    after=[t("קובץ שתבחר עובר לסל המחזור. אפשר לשחזר אותו משם עד שתרוקן את הסל.",
                             "A file you pick moves to the Recycle Bin. You can restore it from there until you empty the bin.")],
                    undo=t("פתח את סל המחזור, לחיצה ימנית על הקובץ > \"שחזר\".", "Open the Recycle Bin, right-click the file > \"Restore\"."))))
        if by_id.get("winsxs"):
            cmd = "Dism.exe /Online /Cleanup-Image /StartComponentCleanup"
            steps.append(step(
                "dism", t("ניקוי רכיבי עדכון ישנים של Windows", "Clean up old Windows update components"),
                t("הכלי הרשמי של מיקרוסופט מסיר גרסאות קודמות של רכיבי מערכת. בדרך כלל מפנה 1 עד 5 GB.",
                  "Microsoft's official tool removes previous versions of system components. Usually frees 1 to 5 GB."),
                t("ייפתח חלון של Windows שיבקש הרשאות מנהל, ויריץ:\n" + cmd + "\n\n"
                  "זה לוקח 5 עד 20 דקות. אל תסגור את החלון ואל תכבה את המחשב באמצע. "
                  "נמחקות רק גרסאות של רכיבי מערכת שהוחלפו לפני יותר מחודש. העדכונים המותקנים ו-Windows עצמו לא נפגעים.",
                  "A Windows window will open, ask for administrator rights and run:\n" + cmd + "\n\n"
                  "It takes 5 to 20 minutes. Do not close the window or shut down the PC midway. "
                  "Only system component versions replaced more than a month ago are removed. Installed updates and Windows itself are not affected."),
                dict(type="command", command=cmd, admin=True), info_rules=["winsxs"]))
        free = gb(d["free"])
        if free_pct < 10:
            sev, head = "high", t(f"הכונן {sysdrive} כמעט מלא: נשארו רק {free} פנויים ({free_pct:.0f}%)",
                                  f"Drive {sysdrive} is almost full: only {free} free ({free_pct:.0f}%)")
        elif free_pct < 20:
            sev, head = "medium", t(f"מעט מקום פנוי בכונן {sysdrive}: {free} ({free_pct:.0f}%)",
                                    f"Low free space on drive {sysdrive}: {free} ({free_pct:.0f}%)")
        else:
            sev, head = "ok", t(f"יש מספיק מקום פנוי בכונן {sysdrive}: {free} ({free_pct:.0f}%)",
                                f"Enough free space on drive {sysdrive}: {free} ({free_pct:.0f}%)")
        findings.append(dict(
            id="disk", severity=sev, title=head,
            why=t("כונן SSD שכמעט מלא נהיה איטי משמעותית בכתיבה, כי אין לו בלוקים ריקים מוכנים. "
                  "בנוסף Windows צריך מקום פנוי כדי להגדיל את הזיכרון הווירטואלי כשה-RAM מתמלא, והדפדפן צריך מקום לשמור "
                  "את הווידאו שהוא טוען מראש. כשאין מקום, הכל נתקע לרגע, כולל סרטונים. מומלץ להשאיר לפחות 15% פנוי.",
                  "An SSD that is almost full becomes much slower at writing, because it has no empty blocks ready. "
                  "Windows also needs free space to grow virtual memory when RAM fills up, and the browser needs room to buffer "
                  "the video it preloads. Without space, everything freezes for a moment, videos included. Keep at least 15% free."),
            steps=steps if sev != "ok" else steps[:1]))

    # ---------------------------------------------------------------- memory
    mem = diag["memory"]
    procs = diag["processes"]["by_mem"]
    top = ", ".join(f"{p['name']} ({gb(p['mem'])}" + (t(f", {p['count']} תהליכים", f", {p['count']} processes") if p["count"] > 1 else "") + ")"
                    for p in procs[:5])
    chrome = next((p for p in procs if p["name"].lower() == "chrome"), None)
    msteps = []
    if chrome and chrome["mem"] > 3 * GB:
        msteps.append(step(
            "chrome_memsaver", t("הפעלת \"חיסכון בזיכרון\" ב-Chrome", "Turn on Chrome \"Memory Saver\""),
            t(f"Chrome תופס כרגע {gb(chrome['mem'])} ב-{chrome['count']} תהליכים. "
              "חיסכון בזיכרון מקפיא לשוניות שלא השתמשת בהן זמן מה, ומשחרר את הזיכרון שלהן.",
              f"Chrome is using {gb(chrome['mem'])} in {chrome['count']} processes right now. "
              "Memory Saver freezes tabs you have not used for a while and frees their memory."),
            t("ייפתח Chrome בדף ההגדרות \"ביצועים\". שם הפעל את המתג \"חיסכון בזיכרון\" (Memory Saver).\n\n"
              "מה ישתנה: לשוניות ישנות ייטענו מחדש כשתחזור אליהן. לשונית שמנגנת מוזיקה או סרטון לא מוקפאת.",
              "Chrome will open on the \"Performance\" settings page. Turn on the \"Memory Saver\" switch there.\n\n"
              "What changes: old tabs reload when you return to them. A tab playing music or video is never frozen."),
            dict(type="open_chrome", url="chrome://settings/performance"), button=open_,
            info=dict(
                verdict=t("לא יהרוס כלום. זו הגדרה רשמית של Chrome שאפשר לכבות בכל רגע.",
                          "Nothing will break. It is an official Chrome setting you can turn off at any time."),
                details=t("כל לשונית פתוחה ב-Chrome תופסת זיכרון, גם אם לא הסתכלת עליה שעות. \"חיסכון בזיכרון\" (Memory Saver) "
                          "מקפיא לשוניות שלא השתמשת בהן זמן מה, ומשחרר את הזיכרון שלהן ל-Windows. הלשונית נשארת במקומה עם הכותרת שלה. "
                          "כשתלחץ עליה, היא נטענת מחדש. הכלי רק פותח את דף ההגדרות, ואתה מפעיל את המתג בעצמך.",
                          "Every open Chrome tab uses memory, even if you have not looked at it for hours. Memory Saver freezes tabs you "
                          "have not used for a while and gives their memory back to Windows. The tab stays in place with its title. "
                          "When you click it, it reloads. The tool only opens the settings page, and you flip the switch yourself."),
                not_affected=[t("הלשוניות עצמן: אף לשונית לא נסגרת", "The tabs themselves: no tab is closed"),
                              t("סיסמאות, סימניות, היסטוריה והתחברויות", "Passwords, bookmarks, history and logins"),
                              t("לשונית שמנגנת מוזיקה או סרטון, או שיש בה שיחת וידאו פעילה (לא מוקפאות)",
                                "Tabs playing music or video, or with an active video call (never frozen)")],
                after=[t("כשתחזור ללשונית ישנה, היא תיטען מחדש (שנייה-שתיים).", "When you return to an old tab, it reloads (a second or two)."),
                       t("טקסט שהקלדת בטופס בלשונית שהוקפאה עלול להימחק. אפשר להוסיף אתרים לרשימת \"תמיד להשאיר פעיל\" באותו מסך.",
                         "Text you typed into a form in a frozen tab may be lost. You can add sites to the \"Always keep active\" list on the same page.")],
                undo=t("באותו דף הגדרות: לכבות את המתג \"חיסכון בזיכרון\".", "On the same settings page: turn off the \"Memory Saver\" switch."))))
    msteps.append(step(
        "taskmgr", t("סגירת תוכנות שלא בשימוש", "Close programs you are not using"),
        t("במנהל המשימות, מיין לפי \"זיכרון\" וסגור תוכנות פתוחות שאתה לא צריך עכשיו.",
          "In Task Manager, sort by \"Memory\" and close open programs you do not need right now."),
        t("ייפתח מנהל המשימות. הכלי לא סוגר שום תוכנה בעצמו: אתה מחליט מה לסגור. שמור עבודה פתוחה לפני שאתה סוגר תוכנה.",
          "Task Manager will open. The tool does not close any program itself: you decide what to close. Save open work before closing a program."),
        dict(type="open", target="taskmgr"), button=open_,
        info=dict(
            verdict=t("הכלי לא סוגר כלום. רק פותח את מנהל המשימות.", "The tool closes nothing. It only opens Task Manager."),
            details=t("מנהל המשימות מראה כל תוכנה פתוחה וכמה זיכרון היא תופסת. לחיצה על הכותרת \"זיכרון\" ממיינת מהגדולה לקטנה. "
                      "כדי לסגור תוכנה: לחיצה ימנית > \"סיים משימה\". עדיף לסגור תוכנה בדרך הרגילה (האיקס בחלון), כדי שתשמור את העבודה.",
                      "Task Manager shows every open program and how much memory it uses. Clicking the \"Memory\" header sorts from largest to smallest. "
                      "To close a program: right-click > \"End task\". It is better to close a program the normal way (the X in its window) so it saves your work."),
            not_affected=[t("שום דבר לא משתנה עד שאתה בוחר לסגור משהו", "Nothing changes until you choose to close something")],
            after=[t("תוכנה שתסגור דרך \"סיים משימה\" לא תשמור עבודה פתוחה.", "A program closed with \"End task\" will not save open work.")],
            undo=t("פשוט לפתוח את התוכנה שוב.", "Just open the program again."))))
    load = mem["load"]
    ram_gb = round(mem["total"] / GB)
    findings.append(dict(
        id="memory", severity="high" if load >= 85 else "medium" if load >= 70 else "ok",
        title=t(f"זיכרון (RAM) בשימוש: {load}% ({gb(mem['total'] - mem['avail'])} מתוך {gb(mem['total'])})",
                f"Memory (RAM) in use: {load}% ({gb(mem['total'] - mem['avail'])} of {gb(mem['total'])})"),
        why=t(f"הצרכנים הגדולים כרגע: {top}. "
              "כשהזיכרון מתמלא, Windows מעביר חלקים ממנו לדיסק (pagefile), שהוא איטי פי אלפים. "
              "במצב כזה סרטון ביוטיוב יכול להיתקע לשנייה בזמן שהמערכת מפנה זיכרון. "
              + (f"{ram_gb} GB זה הרבה, ולכן שימוש גבוה בדרך כלל אומר הרבה לשוניות פתוחות או תוכנות כבדות ברקע."
                 if ram_gb >= 16 else f"{ram_gb} GB זה לא הרבה למחשב של היום, ולכן כדאי במיוחד להקפיד על מספר הלשוניות והתוכנות הפתוחות."),
              f"The biggest consumers right now: {top}. "
              "When memory fills up, Windows moves parts of it to disk (the page file), which is thousands of times slower. "
              "In that state a YouTube video can freeze for a second while the system frees memory. "
              + (f"{ram_gb} GB is a lot, so high usage usually means many open tabs or heavy programs in the background."
                 if ram_gb >= 16 else f"{ram_gb} GB is not much for a modern PC, so it is especially worth keeping open tabs and programs in check.")),
        steps=msteps if load >= 70 else []))

    # --------------------------------------------------------------- startup
    enabled = [s for s in diag["startup"] if s["enabled"]]
    rec = [s for s in enabled if s["advice"]]
    ssteps = []
    for s in rec:
        admin_needed = s["hive"] == "HKLM" and not diag["admin"]
        name = s["display"]
        advice = s["advice"][lang]
        ssteps.append(step(
            "startup_" + re.sub(r"\W", "_", s["name"]),
            t(f"לבטל הפעלה אוטומטית של {name}", f"Stop {name} from starting automatically"), advice,
            t(f"{name} לא ייפתח יותר אוטומטית כשהמחשב נדלק.\n\n"
              "התוכנה עצמה לא נמחקת ותמשיך לעבוד כרגיל כשתפתח אותה. "
              "זו בדיוק אותה פעולה כמו \"השבת\" במנהל המשימות > אפליקציות הפעלה, ואפשר להפעיל מחדש משם בכל רגע.",
              f"{name} will no longer open automatically when the PC starts.\n\n"
              "The program itself is not deleted and keeps working normally when you open it. "
              "This is exactly the same as \"Disable\" in Task Manager > Startup apps, and you can re-enable it there at any time."),
            dict(type="disable_startup", hive=s["hive"], sub=s["sub"], name=s["name"]),
            disabled_reason=t("דורש הפעלת הכלי כמנהל", "Requires running the tool as administrator") if admin_needed else "",
            info=dict(
                verdict=t(f"לא יהרוס כלום. {name} נשאר מותקן ועובד, רק לא נפתח לבד.",
                          f"Nothing will break. {name} stays installed and working, it just does not open on its own."),
                details=advice + " " + t("כשהמחשב נדלק, Windows מפעיל אוטומטית רשימה של תוכנות. הפעולה הזו מסמנת את התוכנה כ\"מושבתת\" "
                                         "ברשימה, בדיוק כמו הכפתור \"השבת\" במנהל המשימות. לא נמחק שום קובץ.",
                                         "When the PC starts, Windows automatically launches a list of programs. This action marks the program as "
                                         "\"disabled\" in that list, exactly like the \"Disable\" button in Task Manager. No file is deleted."),
                where=[s["command"], ("HKEY_CURRENT_USER" if s["hive"] == "HKCU" else "HKEY_LOCAL_MACHINE")
                       + "\\" + APPROVED + "\\" + s["sub"] + " > " + s["name"]],
                not_affected=[t(f"התוכנה {name} עצמה, ההגדרות והחשבון שלה", f"{name} itself, its settings and account"),
                              t("האפשרות לפתוח אותה ידנית מתפריט התחל או מקיצור הדרך", "Opening it manually from the Start menu or a shortcut"),
                              t("כל שאר התוכנות", "All other programs")],
                after=[t(f"{name} לא ייפתח אוטומטית בהדלקה הבאה. תפתח אותו כשתצטרך.",
                         f"{name} will not open automatically at the next start. Open it when you need it."),
                       t("התראות מהתוכנה (אם יש) יופיעו רק אחרי שתפתח אותה.", "Notifications from the program (if any) appear only after you open it."),
                       t("ההשפעה מורגשת מההדלקה הבאה של המחשב.", "The effect is felt from the next time the PC starts.")],
                undo=t("מנהל המשימות (Ctrl+Shift+Esc) > אפליקציות הפעלה > לחיצה ימנית על התוכנה > \"הפעל\".",
                       "Task Manager (Ctrl+Shift+Esc) > Startup apps > right-click the program > \"Enable\"."))))
    findings.append(dict(
        id="startup", severity="medium" if len(rec) >= 3 else "low" if rec else "ok",
        title=t(f"{len(enabled)} תוכנות נפתחות אוטומטית עם הדלקת המחשב", f"{len(enabled)} programs start automatically with the PC"),
        why=t("כל תוכנה שנפתחת בהפעלה ממשיכה לרוץ ברקע ולתפוס זיכרון ומעבד כל הזמן, גם כשאתה לא משתמש בה. "
              "בהמלצות למטה מופיעות רק תוכנות מוכרות שבטוח לכבות. תוכנות אבטחה, דרייברים ו-OneDrive לא מופיעות בכוונה.",
              "Every program that starts with the PC keeps running in the background, using memory and CPU all the time, even when you are not using it. "
              "The recommendations below list only well-known programs that are safe to turn off. Security software, drivers and OneDrive are left out on purpose."),
        steps=ssteps, extra=[s["display"] for s in enabled]))

    # ------------------------------------------------------------- antivirus
    third = [a for a in diag["antivirus"] if a["name"] and "defender" not in a["name"].lower()]
    if third:
        names = ", ".join(a["name"] for a in third)
        findings.append(dict(
            id="antivirus", severity="medium",
            title=t(f"מותקנת תוכנת אנטי-וירוס נוספת: {names}", f"An additional antivirus is installed: {names}"),
            why=t("אנטי-וירוס סורק כל קובץ שנפתח או נכתב, כולל קבצי המטמון שהדפדפן כותב בזמן צפייה בסרטון. "
                  f"{names} נחשבת כבדה יותר מ-Windows Defender המובנה, שמספיק היום לרוב המשתמשים. "
                  "אם תסיר אותה, Defender נדלק מחדש אוטומטית, כך שהמחשב לא יישאר בלי הגנה.",
                  "An antivirus scans every file that is opened or written, including the cache files the browser writes while you watch a video. "
                  f"{names} is generally heavier than the built-in Windows Defender, which is enough for most users today. "
                  "If you uninstall it, Defender turns back on automatically, so the PC is never left unprotected."),
            steps=[step(
                "av_uninstall", t(f"הסרת {names}", f"Uninstall {names}"),
                t("הסרה דרך הגדרות Windows. זו החלטה שלך: הכלי רק פותח את המסך.",
                  "Uninstall through Windows Settings. It is your decision: the tool only opens the screen."),
                t(f"ייפתח מסך \"אפליקציות מותקנות\" של Windows. חפש שם {names}, לחץ על שלוש הנקודות ואז \"הסר התקנה\".\n\n"
                  "מה יקרה: Windows Defender יופעל מחדש אוטומטית תוך כמה דקות. אם שילמת על מנוי, בדוק קודם שאינך מוותר על משהו שאתה צריך.",
                  f"The Windows \"Installed apps\" screen will open. Find {names}, click the three dots, then \"Uninstall\".\n\n"
                  "What happens: Windows Defender turns back on automatically within a few minutes. If you pay for a subscription, first check you are not giving up something you need."),
                dict(type="open", target="ms-settings:appsfeatures"), button=open_,
                info=dict(
                    verdict=t("הכלי לא מסיר כלום. הוא רק פותח את מסך האפליקציות, וההחלטה שלך.",
                              "The tool uninstalls nothing. It only opens the apps screen, and the decision is yours."),
                    details=t(f"כשמותקן אנטי-וירוס נוסף, Windows Defender עובר למצב המתנה, ו-{names} סורק כל קובץ. "
                              "Defender מובנה ב-Windows, חינמי, ומקבל ציונים גבוהים במבחנים עצמאיים. "
                              f"כשמסירים את {names}, Windows מזהה שאין הגנה אחרת ומפעיל את Defender אוטומטית.",
                              f"When another antivirus is installed, Windows Defender goes into standby and {names} scans every file. "
                              "Defender is built into Windows, free, and scores well in independent tests. "
                              f"When you uninstall {names}, Windows detects there is no other protection and turns Defender on automatically."),
                    not_affected=[PERSONAL[lang], t("ההגנה על המחשב: Defender נדלק במקום", "Your protection: Defender takes over"),
                                  t("שאר התוכנות", "Other programs")],
                    after=[t(f"תוכנות נוספות של {names} (VPN, ניקוי, מנהל סיסמאות) יוסרו אם הן חלק מאותה התקנה.",
                             f"Other {names} tools (VPN, cleanup, password manager) are removed if they are part of the same install."),
                           t("אם יש לך מנוי בתשלום, הוא לא מתבטל אוטומטית.", "A paid subscription is not cancelled automatically.")],
                    undo=t(f"אפשר להוריד ולהתקין שוב מהאתר של {names}.", f"You can download and install it again from the {names} website.")))]))

    # ----------------------------------------------------------- disk health
    bad = [x for x in diag["disks"] if x.get("health") and x["health"] != "Healthy"]
    if bad:
        lst = ", ".join(f"{x['name']} ({x['health']})" for x in bad)
        findings.append(dict(
            id="disk_health", severity="high",
            title=t("Windows מדווח על בעיה בתקינות הדיסק: " + lst, "Windows reports a disk health problem: " + lst),
            why=t("דיסק שמתחיל להתקלקל יכול לגרום לתקיעות ולאיבוד מידע. גבה את הקבצים החשובים מיד, ופנה לטכנאי.",
                  "A disk that is starting to fail can cause freezes and data loss. Back up your important files right away and contact a technician."),
            steps=[]))

    # ----------------------------------------------------------------- power
    pw = diag["power"]
    if pw["on_battery"] or pw["power_saver_plan"] or pw["battery_saver"]:
        why = []
        if pw["on_battery"]:
            why.append(t(f"המחשב עובד כרגע על סוללה ({pw['battery']}%). מחשבים ניידים רבים מורידים את מהירות המעבד והמסך בחדות כשהם לא מחוברים לחשמל.",
                         f"The PC is running on battery ({pw['battery']}%). Many laptops sharply reduce CPU and graphics speed when unplugged."))
        if pw["battery_saver"]:
            why.append(t("\"חיסכון בסוללה\" פעיל ומגביל את הביצועים ופעילות ברקע.", "\"Battery saver\" is on and limits performance and background activity."))
        if pw["power_saver_plan"]:
            why.append(t("תוכנית החשמל מוגדרת לחיסכון באנרגיה.", "The power plan is set to power saving."))
        findings.append(dict(
            id="power", severity="medium", title=t("הגדרות חשמל מגבילות ביצועים", "Power settings limit performance"), why=" ".join(why),
            steps=[step("power_settings", t("מעבר למצב ביצועים", "Switch to performance mode"),
                        t("מסך \"חשמל וסוללה\" של Windows.", "The Windows \"Power & battery\" screen."),
                        t("ייפתח מסך \"חשמל וסוללה\". תחת \"מצב חשמל\" בחר \"הביצועים הטובים ביותר\", וחבר את המטען.",
                          "The \"Power & battery\" screen will open. Under \"Power mode\" choose \"Best performance\", and plug in the charger."),
                        dict(type="open", target="ms-settings:powersleep"), button=open_,
                        info=dict(verdict=t("הכלי רק פותח את מסך ההגדרות.", "The tool only opens the settings screen."),
                                  details=t("מצב החשמל קובע כמה מהר המעבד וכרטיס המסך מורשים לעבוד. במצב חיסכון הם מאטים כדי לחסוך בסוללה.",
                                            "The power mode decides how fast the CPU and graphics card are allowed to run. In saving mode they slow down to save battery."),
                                  not_affected=[PERSONAL[lang], t("התוכנות וההגדרות", "Programs and settings")],
                                  after=[t("הסוללה תתרוקן מהר יותר כשהמחשב לא מחובר לחשמל.", "The battery drains faster when unplugged.")],
                                  undo=t("באותו מסך: לבחור שוב את המצב הקודם.", "On the same screen: pick the previous mode again.")))]))

    # ---------------------------------------------------------------- uptime
    up = diag["uptime_h"]
    if up > 72:
        days = f"{up / 24:.0f}"
        findings.append(dict(
            id="uptime", severity="low" if up < 24 * 7 else "medium",
            title=t(f"המחשב לא הופעל מחדש {days} ימים", f"The PC has not been restarted for {days} days"),
            why=t("עם הזמן תוכנות צוברות זיכרון שלא משתחרר, ועדכונים ממתינים להפעלה מחדש. "
                  "\"כיבוי\" ב-Windows 11 הוא לא כיבוי מלא (בגלל הפעלה מהירה), רק \"הפעלה מחדש\" מנקה הכל.",
                  "Over time programs accumulate memory that is never released, and updates wait for a restart. "
                  "\"Shut down\" in Windows 11 is not a full shutdown (because of Fast Startup). Only \"Restart\" clears everything."),
            steps=[step("restart", t("הפעלה מחדש של המחשב", "Restart the PC"), t("הפעלה מחדש בעוד דקה.", "Restart in one minute."),
                        t("המחשב יופעל מחדש בעוד 60 שניות.\n\nשמור את כל העבודה הפתוחה לפני שאתה ממשיך! "
                          "כל התוכנות ייסגרו. לביטול, בתוך הדקה: פתח חלון פקודה והקלד shutdown /a",
                          "The PC will restart in 60 seconds.\n\nSave all open work before you continue! "
                          "All programs will close. To cancel within the minute: open a command window and type shutdown /a"),
                        dict(type="restart"),
                        info=dict(
                            verdict=t("לא יהרוס כלום, בתנאי ששמרת את העבודה הפתוחה.", "Nothing will break, as long as you saved your open work."),
                            details=t("הפעלה מחדש סוגרת את כל התוכנות, מנקה את הזיכרון לגמרי ומסיימת התקנה של עדכונים שממתינים.",
                                      "A restart closes all programs, clears memory completely and finishes installing pending updates."),
                            not_affected=[t("קבצים שמורים", "Saved files"), t("תוכנות מותקנות והגדרות", "Installed programs and settings")],
                            after=[t("כל התוכנות ייסגרו. מסמך שלא נשמר עלול ללכת לאיבוד.", "All programs close. An unsaved document may be lost.")],
                            undo=t("לביטול בתוך הדקה: Win+R > shutdown /a > Enter.", "To cancel within the minute: Win+R > shutdown /a > Enter.")))]))

    # -------------------------------------------------------- network / video
    net = diag["network"]
    net_bad = (net["fails"] > 0 or (net["avg_ms"] or 0) > 80 or (net["max_ms"] or 0) > 300
               or (net["wifi_signal"] is not None and net["wifi_signal"] < 60))
    parts = []
    if net["wifi_signal"] is not None:
        parts.append(t("עוצמת Wi-Fi: ", "Wi-Fi signal: ") + f"{net['wifi_signal']}%" + (f" ({net['wifi_band']})" if net["wifi_band"] else ""))
    if net["avg_ms"] is not None:
        parts.append(t(f"זמן תגובה ממוצע: {net['avg_ms']:.0f}ms, הכי איטי: {net['max_ms']:.0f}ms",
                       f"average response time: {net['avg_ms']:.0f}ms, slowest: {net['max_ms']:.0f}ms"))
    if net["fails"]:
        parts.append(t(f"{net['fails']} מתוך {net['tries']} ניסיונות חיבור נכשלו", f"{net['fails']} of {net['tries']} connection attempts failed"))
    vsteps = [step(
        "chrome_hwaccel", t("לוודא שהאצת חומרה פעילה ב-Chrome", "Make sure hardware acceleration is on in Chrome"),
        t("בלי האצת חומרה, המעבד מפענח את הווידאו לבד ותמונות נופלות.", "Without hardware acceleration, the CPU decodes video alone and frames are dropped."),
        t("ייפתח Chrome בדף ההגדרות \"מערכת\". ודא שהמתג \"שימוש בהאצת גרפיקה כשהיא זמינה\" מופעל. אם שינית אותו, לחץ \"הפעלה מחדש\" של Chrome.",
          "Chrome will open on the \"System\" settings page. Make sure \"Use graphics acceleration when available\" is on. If you changed it, click \"Relaunch\"."),
        dict(type="open_chrome", url="chrome://settings/system"), button=open_,
        info=dict(verdict=t("הכלי רק פותח את דף ההגדרות.", "The tool only opens the settings page."),
                  details=t("\"האצת גרפיקה\" נותנת לכרטיס המסך לפענח את הווידאו. בלעדיה, המעבד עושה את כל העבודה לבד, "
                            "וביוטיוב באיכות גבוהה זה גורם לתמונה לקפוא לרגעים. בדרך כלל ההגדרה פעילה, אבל לפעמים היא כבויה אחרי תקלה.",
                            "\"Graphics acceleration\" lets the graphics card decode video. Without it, the CPU does all the work, "
                            "and high-quality YouTube freezes for moments. The setting is usually on, but sometimes it is off after a glitch."),
                  not_affected=[t("סיסמאות, סימניות, היסטוריה והתחברויות", "Passwords, bookmarks, history and logins")],
                  after=[t("אם תשנה את ההגדרה, Chrome יבקש להפעיל את עצמו מחדש. הלשוניות נפתחות שוב.",
                           "If you change the setting, Chrome asks to relaunch. Your tabs reopen.")],
                  undo=t("להחזיר את המתג למצב הקודם.", "Flip the switch back.")))]
    gpus = diag.get("gpus") or []
    if len(gpus) >= 2:
        strong = next((g for g in gpus if any(k in g.lower() for k in ("nvidia", "radeon rx", "geforce", "arc a"))), gpus[-1])
        weak = next((g for g in gpus if g != strong), gpus[0])
        vsteps.append(step(
            "gpu_pref", t(f"להריץ את Chrome על כרטיס המסך החזק ({strong})", f"Run Chrome on the stronger graphics card ({strong})"),
            t(f"במחשב יש שני כרטיסי מסך. Windows לפעמים מריץ את הדפדפן על החסכוני ({weak}).",
              f"This PC has two graphics cards. Windows sometimes runs the browser on the power-saving one ({weak})."),
            t("ייפתח מסך \"גרפיקה\" של Windows. מצא את Google Chrome ברשימה (או הוסף אותו), לחץ עליו ובחר \"ביצועים גבוהים\". "
              "אחרי זה סגור ופתח את Chrome. החיסרון: צריכת סוללה גבוהה יותר כשלא מחובר לחשמל.",
              "The Windows \"Graphics\" screen will open. Find Google Chrome in the list (or add it), click it and choose \"High performance\". "
              "Then close and reopen Chrome. The downside: higher battery use when unplugged."),
            dict(type="open", target="ms-settings:display-advancedgraphics"), button=open_,
            info=dict(verdict=t("הכלי רק פותח את מסך ההגדרות.", "The tool only opens the settings screen."),
                      details=t(f"במחשב הזה יש כרטיס מסך חסכוני ({weak}) וכרטיס חזק ({strong}). "
                                "Windows מחליט לבד איזה כרטיס כל תוכנה מקבלת, ולדפדפן הוא בדרך כלל נותן את החסכוני. אפשר לקבוע ל-Chrome את הכרטיס החזק.",
                                f"This PC has a power-saving graphics card ({weak}) and a strong one ({strong}). "
                                "Windows decides which card each program gets, and usually gives the browser the power-saving one. You can assign Chrome the strong card."),
                      not_affected=[t("שאר התוכנות והמשחקים", "Other programs and games"), t("Chrome והנתונים שלו", "Chrome and its data")],
                      after=[t("צריכת סוללה גבוהה יותר כשהמחשב לא מחובר לחשמל.", "Higher battery use when the PC is unplugged."),
                             t("צריך לסגור ולפתוח את Chrome כדי שזה ייכנס לתוקף.", "Close and reopen Chrome for it to take effect.")],
                      undo=t("באותו מסך: לבחור ב-Chrome \"תן ל-Windows להחליט\".", "On the same screen: set Chrome to \"Let Windows decide\"."))))
    findings.append(dict(
        id="youtube", severity="medium" if net_bad else "low",
        title=t("סרטונים ביוטיוב נתקעים: איך לדעת אם זה המחשב או האינטרנט", "Videos stutter on YouTube: how to tell if it is the PC or the internet"),
        why=(t("בדיקת רשת: ", "Network check: ") + ". ".join(parts) + ". " if parts else "") +
            (t("נמצאו סימנים לחיבור לא יציב, וזו סיבה נפוצה מאוד לתקיעות ביוטיוב. ",
               "Signs of an unstable connection were found, a very common cause of YouTube stutter. ") if net_bad else "") +
            t("יש שני סוגי תקיעה: אם מופיע עיגול טעינה מסתובב, הבעיה היא באינטרנט (Wi-Fi חלש, נתב רחוק, הורדות ברקע). "
              "אם התמונה קופאת בלי עיגול, או שהקול ממשיך והתמונה לא, הבעיה במחשב. "
              "כדי לבדוק: לחיצה ימנית על הסרטון > \"נתונים למתקדמים\" (Stats for nerds). "
              "אם Connection Speed נמוך או Buffer Health יורד לאפס, זה האינטרנט. אם Dropped Frames עולה, זה המחשב.",
              "There are two kinds of stutter: if a spinning loading circle appears, the problem is the internet (weak Wi-Fi, distant router, background downloads). "
              "If the picture freezes without a circle, or the sound continues but the picture does not, the problem is the PC. "
              "To check: right-click the video > \"Stats for nerds\". "
              "If Connection Speed is low or Buffer Health drops to zero, it is the internet. If Dropped Frames climbs, it is the PC."),
        steps=vsteps))

    order = {"high": 0, "medium": 1, "low": 2, "ok": 3}
    findings.sort(key=lambda f: order[f["severity"]])
    return findings


def build_all(diag, rule_items, disk):
    return {lang: build_report(diag, rule_items, disk, lang) for lang in ("he", "en")}


def all_steps(findings):
    for f in findings:
        for s in f.get("steps", []):
            yield s
