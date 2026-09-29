# -*- coding: utf-8 -*-
"""
איסוף מצב המערכת ובניית הדוח "למה המחשב איטי", עם צעדי טיפול.

כל צעד טיפול (step) מכיל:
    id       - מזהה ייחודי. השרת מבצע רק צעדים שהוא עצמו בנה בדוח האחרון.
    title    - מה עושים.
    desc     - הסבר קצר.
    confirm  - מה בדיוק יקרה אם לוחצים "כן", מוצג בחלון האישור.
    action   - מה השרת מבצע: clean_rules / empty_recycle / command / disable_startup /
               open / open_chrome / restart / goto (מעבר ללשונית בממשק, בלי פעולה בשרת).
"""

import ctypes
import json
import os
import re
import socket
import subprocess
import time
import winreg
from ctypes import wintypes

import rules
import scanner

GB = 1024 ** 3
NO_WINDOW = 0x08000000


def _run(cmd, timeout=30):
    try:
        out = subprocess.run(cmd, capture_output=True, timeout=timeout, creationflags=NO_WINDOW)
        for enc in ("utf-8", "mbcs", "cp862"):
            try:
                return out.stdout.decode(enc)
            except (UnicodeDecodeError, LookupError):
                continue
        return out.stdout.decode("utf-8", "replace")
    except Exception:
        return ""


def _ps_json(script, timeout=40):
    txt = _run(["powershell", "-NoProfile", "-NonInteractive", "-Command",
                "[Console]::OutputEncoding=[Text.Encoding]::UTF8;" + script], timeout)
    try:
        data = json.loads(txt) if txt.strip() else []
    except ValueError:
        return []
    return data if isinstance(data, list) else [data]


def gb(n):
    # LRI ... PDI מבודדים את הכיוון, כדי שבטקסט עברי יוצג "12.7 GB" ולא "GB 12.7"
    return chr(0x2066) + f"{n / GB:.1f} GB" + chr(0x2069) if n is not None else "?"


# ------------------------------------------------------------------ probes
class _MEMSTAT(ctypes.Structure):
    _fields_ = [("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


def memory():
    m = _MEMSTAT()
    m.dwLength = ctypes.sizeof(m)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return dict(total=m.ullTotalPhys, avail=m.ullAvailPhys, load=m.dwMemoryLoad,
                commit_total=m.ullTotalPageFile, commit_avail=m.ullAvailPageFile)


def drives():
    out = []
    mask = ctypes.windll.kernel32.GetLogicalDrives()
    for i in range(26):
        if mask & (1 << i):
            root = f"{chr(65 + i)}:\\"
            if ctypes.windll.kernel32.GetDriveTypeW(root) == 3:  # DRIVE_FIXED
                try:
                    import shutil
                    u = shutil.disk_usage(root)
                    out.append(dict(root=root, total=u.total, used=u.used, free=u.free))
                except OSError:
                    pass
    return out


def uptime_hours():
    return ctypes.windll.kernel32.GetTickCount64() / 3600000


class _PWR(ctypes.Structure):
    _fields_ = [("ACLineStatus", ctypes.c_byte), ("BatteryFlag", ctypes.c_byte), ("BatteryLifePercent", ctypes.c_byte),
                ("SystemStatusFlag", ctypes.c_byte), ("BatteryLifeTime", wintypes.DWORD), ("BatteryFullLifeTime", wintypes.DWORD)]


def power():
    p = _PWR()
    ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(p))
    scheme = _run(["powercfg", "/getactivescheme"]).strip()
    saver = "a1841308-3afa-4b6e-9f3a-0fa8e3c4c5b0" in scheme.lower() or "saver" in scheme.lower() or "חיסכון" in scheme
    return dict(on_battery=p.ACLineStatus == 0, battery=p.BatteryLifePercent, battery_saver=bool(p.SystemStatusFlag & 1),
                scheme=scheme, power_saver_plan=saver)


def processes():
    """צריכת זיכרון ומעבד לפי שם תהליך (מקובץ: כל תהליכי chrome ביחד)."""
    script = (
        "$a=@{};Get-Process|%{$a[$_.Id]=$_.CPU};Start-Sleep -Milliseconds 1500;"
        "Get-Process|%{[pscustomobject]@{n=$_.ProcessName;m=$_.WorkingSet64;"
        "c=($(if($a.ContainsKey($_.Id) -and $_.CPU){$_.CPU-$a[$_.Id]}else{0}))}}|ConvertTo-Json -Compress"
    )
    data = _ps_json(script)
    groups = {}
    for p in data:
        name = (p.get("n") or "?")
        g = groups.setdefault(name.lower(), dict(name=name, mem=0, cpu=0.0, count=0))
        g["mem"] += p.get("m") or 0
        g["cpu"] += float(p.get("c") or 0)
        g["count"] += 1
    ncpu = os.cpu_count() or 1
    lst = list(groups.values())
    for g in lst:
        g["cpu_pct"] = round(min(100.0, g["cpu"] / 1.5 / ncpu * 100), 1)
    lst = [g for g in lst if g["name"].lower() not in ("idle", "system idle process")]
    return dict(by_mem=sorted(lst, key=lambda g: -g["mem"])[:12],
                by_cpu=sorted(lst, key=lambda g: -g["cpu"])[:8],
                total_cpu=round(min(100.0, sum(g["cpu"] for g in lst) / 1.5 / ncpu * 100), 1))


# ---------------------------------------------------------------- startup
RUN = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN32 = r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"
APPROVED = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved"

# שם (או חלק מהפקודה) -> הסבר למה אפשר לכבות. רק תוכנות מוכרות שכיבוי שלהן לא פוגע בשום דבר.
STARTUP_ADVICE = [
    ("microsoftedgeautolaunch", "Edge נטען ברקע בכל הדלקה, גם אם אתה לא משתמש בו. הוא ייפתח כרגיל כשתלחץ עליו."),
    ("googlechromeautolaunch", "Chrome נטען ברקע עם הדלקת המחשב ותופס זיכרון עוד לפני שפתחת אותו. הוא ייפתח כרגיל כשתלחץ עליו."),
    ("microsoftcopilotautolaunch", "Copilot נטען ברקע בכל הדלקה. אפשר לפתוח אותו ידנית כשצריך."),
    ("teams", "Teams נטען בכל הדלקה ותופס כמה מאות MB של זיכרון. אם אתה לא בפגישות כל יום, עדיף לפתוח אותו ידנית."),
    ("adobeaamupdater", "בודק עדכונים של Adobe ברקע. Adobe יבדוק עדכונים גם כשתפתח את התוכנה."),
    ("adobe acrobat synchronizer", "מסנכרן קבצי PDF עם הענן של Adobe. אם אתה לא משתמש ב-Adobe Cloud, מיותר."),
    ("adobegcinvoker", "בדיקת רישיון של Adobe. לא נחוץ בהפעלה."),
    ("logitech download assistant", "מציע להוריד תוכנות של Logitech. לא נחוץ כדי שהעכבר או המקלדת יעבדו."),
    ("logi download assistant", "מציע להוריד תוכנות של Logitech. לא נחוץ כדי שהעכבר או המקלדת יעבדו."),
    ("onenote", "כלי \"שלח ל-OneNote\". כמעט אף אחד לא צריך אותו בהפעלה."),
    ("nvidia broadcast", "משתמש בכרטיס המסך ובמעבד כל הזמן לסינון רעשים ורקע וירטואלי. אם אתה לא בשיחת וידאו, הוא סתם עובד. תוכל לפתוח אותו ידנית לפני שיחה."),
    ("spotify", "Spotify נפתח בכל הדלקה. אפשר לפתוח אותו ידנית."),
    ("discord", "Discord נפתח בכל הדלקה ותופס זיכרון. אפשר לפתוח אותו ידנית."),
    ("steam", "Steam נפתח בכל הדלקה ובודק עדכונים ברקע. אפשר לפתוח אותו ידנית כשמשחקים."),
    ("epicgameslauncher", "Epic Games נפתח בכל הדלקה. אפשר לפתוח אותו ידנית כשמשחקים."),
    ("skype", "Skype נפתח בכל הדלקה."),
    ("ccleaner", "CCleaner רץ ברקע. לא נחוץ."),
    ("utorrent", "uTorrent רץ ברקע ומשתמש באינטרנט. זה יכול לגרום לסרטונים להיתקע."),
    ("bittorrent", "BitTorrent רץ ברקע ומשתמש באינטרנט. זה יכול לגרום לסרטונים להיתקע."),
    ("wondershare helper", "עוזר רקע של Wondershare שבודק עדכונים ופרסומות. התוכנות של Wondershare עובדות גם בלעדיו."),
    ("sunjavaupdatesched", "בודק עדכונים ל-Java ברקע. אפשר לעדכן Java ידנית פעם בכמה חודשים."),
]

FRIENDLY = [("microsoftedgeautolaunch", "Microsoft Edge"), ("googlechromeautolaunch", "Google Chrome"),
            ("microsoftcopilotautolaunch", "Microsoft Copilot"), ("sunjavaupdatesched", "Java Update"),
            ("adobeaamupdater", "Adobe Updater"), ("runonstartupschedulechecker", "SendBliss Schedule Checker")]


def friendly_name(name):
    low = name.lower()
    for key, nice in FRIENDLY:
        if low.startswith(key):
            return nice
    name = re.sub(r"_[0-9A-Fa-f]{16,}$", "", name.strip())
    return re.sub(r"\.(lnk|exe)$", "", name, flags=re.I)
KEEP_STARTUP = ("securityhealth", "windows defender", "avast", "realtek", "rtkaud", "igfx", "synaptics", "elan",
                "asus", "armoury", "onedrive")


def _approved_state(hive, sub, name):
    try:
        with winreg.OpenKey(hive, APPROVED + "\\" + sub) as k:
            val, _ = winreg.QueryValueEx(k, name)
            return not (val and val[0] & 1)
    except OSError:
        return True


def startup_items():
    items = []
    sources = [(winreg.HKEY_CURRENT_USER, RUN, "Run", "HKCU"),
               (winreg.HKEY_LOCAL_MACHINE, RUN, "Run", "HKLM"),
               (winreg.HKEY_LOCAL_MACHINE, RUN32, "Run32", "HKLM")]
    for hive, key, sub, hname in sources:
        try:
            with winreg.OpenKey(hive, key) as k:
                i = 0
                while True:
                    try:
                        name, cmd, _ = winreg.EnumValue(k, i)
                    except OSError:
                        break
                    i += 1
                    items.append(dict(name=name, command=str(cmd), hive=hname, sub=sub,
                                      enabled=_approved_state(hive, sub, name)))
        except OSError:
            pass
    folders = [(os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup"), "HKCU"),
               (os.path.join(os.environ.get("ProgramData", ""), r"Microsoft\Windows\Start Menu\Programs\StartUp"), "HKLM")]
    for folder, hname in folders:
        try:
            for f in os.listdir(folder):
                if f.lower() == "desktop.ini":
                    continue
                hive = winreg.HKEY_CURRENT_USER if hname == "HKCU" else winreg.HKEY_LOCAL_MACHINE
                items.append(dict(name=f, command=os.path.join(folder, f), hive=hname, sub="StartupFolder",
                                  enabled=_approved_state(hive, "StartupFolder", f)))
        except OSError:
            pass
    for it in items:
        it["display"] = friendly_name(it["name"])
        low = (it["name"] + " " + it["command"]).lower()
        it["advice"] = ""
        if not any(k in low for k in KEEP_STARTUP):
            for key, text in STARTUP_ADVICE:
                if key in low:
                    it["advice"] = text
                    break
    return items


def set_startup_enabled(hive_name, sub, name, enabled):
    """אותה פעולה כמו ב'מנהל המשימות > אפליקציות הפעלה'. הפיכה מלאה משם."""
    hive = winreg.HKEY_CURRENT_USER if hive_name == "HKCU" else winreg.HKEY_LOCAL_MACHINE
    if enabled:
        data = bytes([2] + [0] * 11)
    else:
        ft = int((time.time() + 11644473600) * 10 ** 7)
        data = bytes([3, 0, 0, 0]) + ft.to_bytes(8, "little")
    with winreg.CreateKeyEx(hive, APPROVED + "\\" + sub, 0, winreg.KEY_SET_VALUE) as k:
        winreg.SetValueEx(k, name, 0, winreg.REG_BINARY, data)


# ------------------------------------------------------------ other probes
def antivirus():
    data = _ps_json("Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntivirusProduct|"
                    "Select displayName,productState|ConvertTo-Json -Compress")
    out = []
    for a in data:
        state = int(a.get("productState") or 0)
        out.append(dict(name=a.get("displayName"), active=((state >> 12) & 0xF) in (1, 3)))
    return out


def disk_health():
    return [dict(name=d.get("FriendlyName"), media=d.get("MediaType"), health=d.get("HealthStatus"))
            for d in _ps_json("Get-PhysicalDisk|Select FriendlyName,MediaType,HealthStatus|ConvertTo-Json -Compress")]


def network():
    lat, fails = [], 0
    for host, port in [("8.8.8.8", 53), ("1.1.1.1", 443)] * 5:
        t = time.perf_counter()
        try:
            with socket.create_connection((host, port), timeout=2):
                lat.append((time.perf_counter() - t) * 1000)
        except OSError:
            fails += 1
    wlan = _run(["netsh", "wlan", "show", "interfaces"])
    m = re.search(r"(\d{1,3})\s*%", wlan)
    band = re.search(r"(2\.4|5|6)\s*GHz", wlan)
    return dict(avg_ms=round(sum(lat) / len(lat), 1) if lat else None,
                max_ms=round(max(lat), 1) if lat else None,
                fails=fails, tries=10, wifi_signal=int(m.group(1)) if m else None,
                wifi_band=band.group(0) if band else None)


def collect():
    return dict(memory=memory(), drives=drives(), uptime_h=uptime_hours(), power=power(),
                processes=processes(), startup=startup_items(), antivirus=antivirus(),
                disks=disk_health(), network=network(), admin=scanner.is_admin())


# ---------------------------------------------------------------- report
def build_report(diag, rule_items, disk):
    """
    בונה רשימת ממצאים ממוינת לפי חומרה. כל ממצא: למה זה מאט, ומה עושים.
    """
    findings = []
    by_id = {r["id"]: r for r in rule_items}
    sysdrive = os.environ.get("SystemDrive", "C:") + "\\"

    def step(sid, title, desc, confirm, action, button="טפל", **kw):
        return dict(id=sid, title=title, desc=desc, confirm=confirm, action=action, button=button, **kw)

    # ---------- disk space
    d = next((x for x in diag["drives"] if x["root"].upper() == sysdrive.upper()), None)
    if d:
        free_pct = d["free"] / d["total"] * 100
        steps = []
        runnable = [r for r in rule_items if r["safety"] == "safe" and r["action"] == "clean"
                    and not r["needs_admin_now"] and (r["size"] or 0) > 50 * 1024 ** 2]
        runnable.sort(key=lambda r: -(r["size"] or 0))
        if runnable:
            total = sum(r["size"] for r in runnable)
            lines = "\n".join(f"• {r['title']} ({gb(r['size'])})" for r in runnable)
            steps.append(step(
                "clean_safe", f"ניקוי כל מה שבטוח למחוק ({gb(total)})",
                "קבצים זמניים, מטמונים וקבצי קריסה שהמערכת והתוכנות יוצרות מחדש לבד.",
                "הפריטים הבאים יימחקו לצמיתות (לא דרך סל המחזור):\n" + lines +
                "\n\nשום קובץ אישי, סיסמה, היסטוריה או פרויקט לא נמחק. קבצים שנמצאים כרגע בשימוש ידולגו. "
                "מומלץ לסגור קודם את Chrome, CapCut ו-VS Code כדי שיימחק כמה שיותר.",
                dict(type="clean_rules", rules=[r["id"] for r in runnable]), size=total,
                info_rules=[r["id"] for r in runnable]))
        rb = by_id.get("recycle_bin")
        if rb and (rb["size"] or 0) > 100 * 1024 ** 2:
            steps.append(step("empty_recycle", f"ריקון סל המחזור ({gb(rb['size'])})",
                              "קבצים שמחקת עדיין תופסים מקום עד שהסל מתרוקן.",
                              f"כל {rb.get('count', 0)} הפריטים בסל המחזור יימחקו לצמיתות ולא יהיה אפשר לשחזר אותם. "
                              "אם אתה לא בטוח, פתח קודם את סל המחזור ובדוק.",
                              dict(type="empty_recycle"), size=rb["size"], info_rules=["recycle_bin"]))
        hib = by_id.get("hiberfil")
        if hib and (hib["size"] or 0) > GB:
            steps.append(step("hibernate_off", f"כיבוי קובץ השינה ({gb(hib['size'])})",
                              "קובץ שנשמר למצב Hibernate. רוב האנשים לא משתמשים במצב הזה.",
                              "ייפתח חלון של Windows שיבקש הרשאות מנהל, ויריץ powercfg /h off.\n\n"
                              "מה ישתנה: אפשרות \"מצב שינה עמוקה\" תיעלם, וההדלקה מכבוי מלא תהיה איטית בכמה שניות. "
                              "מצב שינה רגיל (סגירת מכסה) ממשיך לעבוד כרגיל.\n"
                              "להחזרה בכל רגע: powercfg /h on בחלון מנהל.",
                              dict(type="command", command="powercfg /h off", admin=True), size=hib["size"],
                              info_rules=["hiberfil"]))
        # פריטים גדולים שלא נכללים בניקוי הבטוח: דורשים פקודה, או שיש להם מחיר קטן
        for rid in ("pnpm_store", "gradle_cache", "automation_browsers", "chrome_ai_model", "android_studio_old",
                    "browser_sw"):
            r = by_id.get(rid)
            if r and (r["size"] or 0) > GB:
                if r["action"] == "command":
                    steps.append(step("rule_" + rid, f"{r['title']} ({gb(r['size'])})", r["what"],
                                      r["if_deleted"] + "\n\nייפתח חלון פקודה שיריץ: " + r["command"],
                                      dict(type="command", command=r["command"], admin=r["admin"]), size=r["size"],
                                      info_rules=[rid]))
                else:
                    steps.append(step("rule_" + rid, f"{r['title']} ({gb(r['size'])})", r["what"],
                                      "מה יימחק:\n" + "\n".join("• " + p for p in r["paths"][:12]) +
                                      "\n\nמה המשמעות: " + r["if_deleted"],
                                      dict(type="clean_rules", rules=[rid]), size=r["size"], info_rules=[rid]))
        if disk and disk.get("node_modules"):
            nm_total = sum(x["size"] for x in disk["node_modules"])
            if nm_total > GB:
                steps.append(step("goto_nm", f"תיקיות node_modules בפרויקטים ({gb(nm_total)})",
                                  f"נמצאו {len(disk['node_modules'])} תיקיות node_modules. בפרויקטים שאתה לא עובד עליהם אפשר למחוק ולשחזר עם npm install.",
                                  "", dict(type="goto", tab="disk", anchor="nm"), button="הצג רשימה",
                                  info=dict(
                                      verdict="הכפתור רק מציג רשימה. כל מחיקה שם היא לפרויקט אחד, ורק אחרי אישור.",
                                      details="כל פרויקט JavaScript (React, Node, Next.js וכו') מוריד את החבילות שהוא צריך לתיקייה בשם node_modules "
                                              "בתוך הפרויקט. התיקייה הזו לא מכילה קוד שכתבת, רק עותקים של חבילות מהאינטרנט. "
                                              "הרשימה שבקובץ package.json בפרויקט מאפשרת להוריד את כולן מחדש בפקודה אחת.",
                                      not_affected=["הקוד שכתבת: קבצי המקור, package.json, הגדרות הפרויקט", "Git וההיסטוריה של הפרויקט",
                                                    "פרויקטים אחרים"],
                                      after=["הפרויקט לא ירוץ עד שתריץ בתיקייה שלו npm install (או pnpm install / yarn). זה לוקח דקה-שתיים ודורש אינטרנט.",
                                             "לכן כדאי למחוק רק בפרויקטים ישנים שאתה לא עובד עליהם עכשיו."],
                                      undo="npm install בתיקיית הפרויקט.")))
        if disk and disk.get("large_files"):
            steps.append(step("goto_large", "קבצים גדולים לבדיקה ידנית",
                              "רשימת הקבצים הגדולים בכונן, עם הסבר לכל אחד אם אפשר למחוק.",
                              "", dict(type="goto", tab="disk", anchor="large"), button="הצג רשימה",
                              info=dict(
                                  verdict="הכפתור רק מציג רשימה. הכלי לא מוחק שם שום דבר לבד.",
                                  details="אלה כל הקבצים בכונן שגדולים מ-500 MB. ליד כל קובץ יש הסבר מה הוא לפי הסוג והמיקום שלו "
                                          "(למשל: קובץ התקנה, סרטון, גיבוי דחוס, קובץ מערכת). על קבצי מערכת אין בכלל כפתור מחיקה.",
                                  not_affected=["שום דבר, עד שתבחר קובץ ותאשר"],
                                  after=["קובץ שתבחר עובר לסל המחזור. אפשר לשחזר אותו משם עד שתרוקן את הסל."],
                                  undo="פתח את סל המחזור, לחיצה ימנית על הקובץ > \"שחזר\".")))
        wx = by_id.get("winsxs")
        if wx:
            steps.append(step("dism", "ניקוי רכיבי עדכון ישנים של Windows",
                              "הכלי הרשמי של מיקרוסופט מסיר גרסאות קודמות של רכיבי מערכת. בדרך כלל מפנה 1 עד 5 GB.",
                              "ייפתח חלון של Windows שיבקש הרשאות מנהל, ויריץ:\n"
                              "Dism.exe /Online /Cleanup-Image /StartComponentCleanup\n\n"
                              "זה לוקח 5 עד 20 דקות. אל תסגור את החלון ואל תכבה את המחשב באמצע. "
                              "נמחקות רק גרסאות של רכיבי מערכת שהוחלפו לפני יותר מחודש. העדכונים המותקנים ו-Windows עצמו לא נפגעים.",
                              dict(type="command", command="Dism.exe /Online /Cleanup-Image /StartComponentCleanup", admin=True),
                              info_rules=["winsxs"]))
        if free_pct < 10:
            sev, head = "high", f"הכונן {sysdrive} כמעט מלא: נשארו רק {gb(d['free'])} פנויים ({free_pct:.0f}%)"
        elif free_pct < 20:
            sev, head = "medium", f"מעט מקום פנוי בכונן {sysdrive}: {gb(d['free'])} ({free_pct:.0f}%)"
        else:
            sev, head = "ok", f"יש מספיק מקום פנוי בכונן {sysdrive}: {gb(d['free'])} ({free_pct:.0f}%)"
        findings.append(dict(
            id="disk", severity=sev, title=head,
            why="כונן SSD שכמעט מלא נהיה איטי משמעותית בכתיבה, כי אין לו בלוקים ריקים מוכנים. "
                "בנוסף Windows צריך מקום פנוי כדי להגדיל את הזיכרון הווירטואלי כשה-RAM מתמלא, והדפדפן צריך מקום לשמור "
                "את הווידאו שהוא טוען מראש. כשאין מקום, הכל נתקע לרגע, כולל סרטונים. מומלץ להשאיר לפחות 15% פנוי.",
            steps=steps if sev != "ok" else steps[:1]))

    # ---------- memory
    mem = diag["memory"]
    procs = diag["processes"]["by_mem"]
    top = ", ".join(f"{p['name']} ({gb(p['mem'])}{', ' + str(p['count']) + ' תהליכים' if p['count'] > 1 else ''})"
                    for p in procs[:5])
    chrome = next((p for p in procs if p["name"].lower() == "chrome"), None)
    msteps = []
    if chrome and chrome["mem"] > 3 * GB:
        msteps.append(step("chrome_memsaver", "הפעלת \"חיסכון בזיכרון\" ב-Chrome",
                           f"Chrome תופס כרגע {gb(chrome['mem'])} ב-{chrome['count']} תהליכים. "
                           "חיסכון בזיכרון מקפיא לשוניות שלא השתמשת בהן זמן מה, ומשחרר את הזיכרון שלהן.",
                           "ייפתח Chrome בדף ההגדרות \"ביצועים\". שם הפעל את המתג \"חיסכון בזיכרון\" (Memory Saver).\n\n"
                           "מה ישתנה: לשוניות ישנות ייטענו מחדש כשתחזור אליהן. לשונית שמנגנת מוזיקה או סרטון לא מוקפאת.",
                           dict(type="open_chrome", url="chrome://settings/performance"),
                           info=dict(
                               verdict="לא יהרוס כלום. זו הגדרה רשמית של Chrome שאפשר לכבות בכל רגע.",
                               details="כל לשונית פתוחה ב-Chrome תופסת זיכרון, גם אם לא הסתכלת עליה שעות. \"חיסכון בזיכרון\" "
                                       "(Memory Saver) מקפיא לשוניות שלא השתמשת בהן זמן מה, ומשחרר את הזיכרון שלהן ל-Windows. "
                                       "הלשונית נשארת במקומה עם הכותרת שלה. כשתלחץ עליה, היא נטענת מחדש. הכלי רק פותח את דף ההגדרות, "
                                       "ואתה מפעיל את המתג בעצמך.",
                               not_affected=["הלשוניות עצמן: אף לשונית לא נסגרת", "סיסמאות, סימניות, היסטוריה והתחברויות",
                                             "לשונית שמנגנת מוזיקה או סרטון, או שיש בה שיחת וידאו פעילה (לא מוקפאות)"],
                               after=["כשתחזור ללשונית ישנה, היא תיטען מחדש (שנייה-שתיים).",
                                      "טקסט שהקלדת בטופס בלשונית שהוקפאה עלול להימחק. אפשר להוסיף אתרים לרשימת \"תמיד להשאיר פעיל\" באותו מסך."],
                               undo="באותו דף הגדרות: לכבות את המתג \"חיסכון בזיכרון\".")))
    msteps.append(step("taskmgr", "סגירת תוכנות שלא בשימוש",
                       "במנהל המשימות, מיין לפי \"זיכרון\" וסגור תוכנות פתוחות שאתה לא צריך עכשיו.",
                       "ייפתח מנהל המשימות. הכלי לא סוגר שום תוכנה בעצמו: אתה מחליט מה לסגור. "
                       "שמור עבודה פתוחה לפני שאתה סוגר תוכנה.",
                       dict(type="open", target="taskmgr"), button="פתח",
                       info=dict(
                           verdict="הכלי לא סוגר כלום. רק פותח את מנהל המשימות.",
                           details="מנהל המשימות מראה כל תוכנה פתוחה וכמה זיכרון היא תופסת. לחיצה על הכותרת \"זיכרון\" ממיינת מהגדולה לקטנה. "
                                   "כדי לסגור תוכנה: לחיצה ימנית > \"סיים משימה\". עדיף לסגור תוכנה בדרך הרגילה (האיקס בחלון), כדי שתשמור את העבודה.",
                           not_affected=["שום דבר לא משתנה עד שאתה בוחר לסגור משהו"],
                           after=["תוכנה שתסגור דרך \"סיים משימה\" לא תשמור עבודה פתוחה."],
                           undo="פשוט לפתוח את התוכנה שוב.")))
    load = mem["load"]
    findings.append(dict(
        id="memory", severity="high" if load >= 85 else "medium" if load >= 70 else "ok",
        title=f"זיכרון (RAM) בשימוש: {load}% ({gb(mem['total'] - mem['avail'])} מתוך {gb(mem['total'])})",
        why=f"הצרכנים הגדולים כרגע: {top}. "
            "כשהזיכרון מתמלא, Windows מעביר חלקים ממנו לדיסק (pagefile), שהוא איטי פי אלפים. "
            "במצב כזה סרטון ביוטיוב יכול להיתקע לשנייה בזמן שהמערכת מפנה זיכרון. "
            "32 GB זה הרבה, ולכן שימוש גבוה בדרך כלל אומר הרבה לשוניות פתוחות או תוכנות כבדות ברקע.",
        steps=msteps if load >= 70 else []))

    # ---------- startup
    enabled = [s for s in diag["startup"] if s["enabled"]]
    rec = [s for s in enabled if s["advice"]]
    ssteps = []
    for s in rec:
        admin_needed = s["hive"] == "HKLM" and not diag["admin"]
        ssteps.append(step("startup_" + re.sub(r"\W", "_", s["name"]),
                           f"לבטל הפעלה אוטומטית של {s['display']}", s["advice"],
                           f"{s['display']} לא ייפתח יותר אוטומטית כשהמחשב נדלק.\n\n"
                           "התוכנה עצמה לא נמחקת ותמשיך לעבוד כרגיל כשתפתח אותה. "
                           "זו בדיוק אותה פעולה כמו \"השבת\" במנהל המשימות > אפליקציות הפעלה, ואפשר להפעיל מחדש משם בכל רגע.",
                           dict(type="disable_startup", hive=s["hive"], sub=s["sub"], name=s["name"]),
                           disabled_reason="דורש הפעלת הכלי כמנהל" if admin_needed else "",
                           info=dict(
                               verdict=f"לא יהרוס כלום. {s['display']} נשאר מותקן ועובד, רק לא נפתח לבד.",
                               details=s["advice"] + " "
                                       "כשהמחשב נדלק, Windows מפעיל אוטומטית רשימה של תוכנות. הפעולה הזו מסמנת את התוכנה כ\"מושבתת\" "
                                       "ברשימה, בדיוק כמו הכפתור \"השבת\" במנהל המשימות. לא נמחק שום קובץ.",
                               where=[s["command"], ("HKEY_CURRENT_USER" if s["hive"] == "HKCU" else "HKEY_LOCAL_MACHINE")
                                      + "\\" + APPROVED + "\\" + s["sub"] + " > " + s["name"]],
                               not_affected=[f"התוכנה {s['display']} עצמה, ההגדרות והחשבון שלה",
                                             "האפשרות לפתוח אותה ידנית מתפריט התחל או מקיצור הדרך",
                                             "כל שאר התוכנות"],
                               after=[f"{s['display']} לא ייפתח אוטומטית בהדלקה הבאה. תפתח אותו כשתצטרך.",
                                      "התראות מהתוכנה (אם יש) יופיעו רק אחרי שתפתח אותה.",
                                      "ההשפעה מורגשת מההדלקה הבאה של המחשב."],
                               undo="מנהל המשימות (Ctrl+Shift+Esc) > אפליקציות הפעלה > לחיצה ימנית על התוכנה > \"הפעל\".")))
    findings.append(dict(
        id="startup", severity="medium" if len(rec) >= 3 else "low" if rec else "ok",
        title=f"{len(enabled)} תוכנות נפתחות אוטומטית עם הדלקת המחשב",
        why="כל תוכנה שנפתחת בהפעלה ממשיכה לרוץ ברקע ולתפוס זיכרון ומעבד כל הזמן, גם כשאתה לא משתמש בה. "
            "בהמלצות למטה מופיעות רק תוכנות מוכרות שבטוח לכבות. "
            "תוכנות אבטחה, דרייברים ו-OneDrive לא מופיעות בכוונה.",
        steps=ssteps, extra=[s["display"] for s in enabled]))

    # ---------- antivirus
    third = [a for a in diag["antivirus"] if a["name"] and "defender" not in a["name"].lower()]
    if third:
        names = ", ".join(a["name"] for a in third)
        findings.append(dict(
            id="antivirus", severity="medium",
            title=f"מותקנת תוכנת אנטי-וירוס נוספת: {names}",
            why="אנטי-וירוס סורק כל קובץ שנפתח או נכתב, כולל קבצי המטמון שהדפדפן כותב בזמן צפייה בסרטון. "
                f"{names} נחשבת כבדה יותר מ-Windows Defender המובנה, שמספיק היום לרוב המשתמשים. "
                "אם תסיר אותה, Defender נדלק מחדש אוטומטית, כך שהמחשב לא יישאר בלי הגנה.",
            steps=[step("av_uninstall", f"הסרת {names}",
                        "הסרה דרך הגדרות Windows. זו החלטה שלך: הכלי רק פותח את המסך.",
                        f"ייפתח מסך \"אפליקציות מותקנות\" של Windows. חפש שם {names}, לחץ על שלוש הנקודות ואז \"הסר התקנה\".\n\n"
                        "מה יקרה: Windows Defender יופעל מחדש אוטומטית תוך כמה דקות. "
                        "אם שילמת על מנוי, בדוק קודם שאינך מוותר על משהו שאתה צריך.",
                        dict(type="open", target="ms-settings:appsfeatures"), button="פתח",
                        info=dict(
                            verdict="הכלי לא מסיר כלום. הוא רק פותח את מסך האפליקציות, וההחלטה שלך.",
                            details="כשמותקן אנטי-וירוס נוסף, Windows Defender עובר למצב המתנה, ו-" + names + " סורק כל קובץ. "
                                    "Defender מובנה ב-Windows, חינמי, ומקבל ציונים גבוהים במבחנים עצמאיים. "
                                    "כשמסירים את " + names + ", Windows מזהה שאין הגנה אחרת ומפעיל את Defender אוטומטית.",
                            not_affected=[rules.PERSONAL, "ההגנה על המחשב: Defender נדלק במקום", "שאר התוכנות"],
                            after=["תוכנות נוספות של " + names + " (VPN, ניקוי, מנהל סיסמאות) יוסרו אם הן חלק מאותה התקנה.",
                                   "אם יש לך מנוי בתשלום, הוא לא מתבטל אוטומטית."],
                            undo="אפשר להוריד ולהתקין שוב מהאתר של " + names + "."))]))

    # ---------- disk health
    bad = [x for x in diag["disks"] if x.get("health") and x["health"] != "Healthy"]
    if bad:
        findings.append(dict(
            id="disk_health", severity="high",
            title="Windows מדווח על בעיה בתקינות הדיסק: " + ", ".join(f"{x['name']} ({x['health']})" for x in bad),
            why="דיסק שמתחיל להתקלקל יכול לגרום לתקיעות ולאיבוד מידע. גבה את הקבצים החשובים מיד, ופנה לטכנאי.",
            steps=[]))

    # ---------- power
    pw = diag["power"]
    if pw["on_battery"] or pw["power_saver_plan"] or pw["battery_saver"]:
        why = []
        if pw["on_battery"]:
            why.append(f"המחשב עובד כרגע על סוללה ({pw['battery']}%). מחשבי גיימינג מורידים את מהירות המעבד והמסך בחדות כשהם לא מחוברים לחשמל.")
        if pw["battery_saver"]:
            why.append("\"חיסכון בסוללה\" פעיל ומגביל את הביצועים ופעילות ברקע.")
        if pw["power_saver_plan"]:
            why.append("תוכנית החשמל מוגדרת לחיסכון באנרגיה.")
        findings.append(dict(
            id="power", severity="medium", title="הגדרות חשמל מגבילות ביצועים", why=" ".join(why),
            steps=[step("power_settings", "מעבר למצב ביצועים", "מסך \"חשמל וסוללה\" של Windows.",
                        "ייפתח מסך \"חשמל וסוללה\". תחת \"מצב חשמל\" בחר \"הביצועים הטובים ביותר\", וחבר את המטען.",
                        dict(type="open", target="ms-settings:powersleep"), button="פתח")]))

    # ---------- uptime
    up = diag["uptime_h"]
    if up > 72:
        findings.append(dict(
            id="uptime", severity="low" if up < 24 * 7 else "medium",
            title=f"המחשב לא הופעל מחדש {up / 24:.0f} ימים",
            why="עם הזמן תוכנות צוברות זיכרון שלא משתחרר, ועדכונים ממתינים להפעלה מחדש. "
                "\"כיבוי\" ב-Windows 11 הוא לא כיבוי מלא (בגלל הפעלה מהירה), רק \"הפעלה מחדש\" מנקה הכל.",
            steps=[step("restart", "הפעלה מחדש של המחשב", "הפעלה מחדש בעוד דקה.",
                        "המחשב יופעל מחדש בעוד 60 שניות.\n\nשמור את כל העבודה הפתוחה לפני שאתה ממשיך! "
                        "כל התוכנות ייסגרו. לביטול, בתוך הדקה: פתח חלון פקודה והקלד shutdown /a",
                        dict(type="restart"),
                        info=dict(
                            verdict="לא יהרוס כלום, בתנאי ששמרת את העבודה הפתוחה.",
                            details="הפעלה מחדש סוגרת את כל התוכנות, מנקה את הזיכרון לגמרי ומסיימת התקנה של עדכונים שממתינים.",
                            not_affected=["קבצים שמורים", "תוכנות מותקנות והגדרות"],
                            after=["כל התוכנות ייסגרו. מסמך שלא נשמר עלול ללכת לאיבוד."],
                            undo="לביטול בתוך הדקה: Win+R > shutdown /a > Enter."))]))

    # ---------- network / YouTube
    net = diag["network"]
    net_bad = (net["fails"] > 0 or (net["avg_ms"] or 0) > 80 or (net["max_ms"] or 0) > 300
               or (net["wifi_signal"] is not None and net["wifi_signal"] < 60))
    parts = []
    if net["wifi_signal"] is not None:
        parts.append(f"עוצמת Wi-Fi: {net['wifi_signal']}%" + (f" ({net['wifi_band']})" if net["wifi_band"] else ""))
    if net["avg_ms"] is not None:
        parts.append(f"זמן תגובה ממוצע: {net['avg_ms']:.0f}ms, הכי איטי: {net['max_ms']:.0f}ms")
    if net["fails"]:
        parts.append(f"{net['fails']} מתוך {net['tries']} ניסיונות חיבור נכשלו")
    findings.append(dict(
        id="youtube", severity="medium" if net_bad else "low",
        title="סרטונים ביוטיוב נתקעים: איך לדעת אם זה המחשב או האינטרנט",
        why=("בדיקת רשת: " + ". ".join(parts) + ". " if parts else "") +
            ("נמצאו סימנים לחיבור לא יציב, וזו סיבה נפוצה מאוד לתקיעות ביוטיוב. " if net_bad else "") +
            "יש שני סוגי תקיעה: אם מופיע עיגול טעינה מסתובב, הבעיה היא באינטרנט (Wi-Fi חלש, נתב רחוק, הורדות ברקע). "
            "אם התמונה קופאת בלי עיגול, או שהקול ממשיך והתמונה לא, הבעיה במחשב. "
            "כדי לבדוק: לחיצה ימנית על הסרטון > \"נתונים למתקדמים\" (Stats for nerds). "
            "אם Connection Speed נמוך או Buffer Health יורד לאפס, זה האינטרנט. אם Dropped Frames עולה, זה המחשב.",
        steps=[
            step("chrome_hwaccel", "לוודא שהאצת חומרה פעילה ב-Chrome",
                 "בלי האצת חומרה, המעבד מפענח את הווידאו לבד ותמונות נופלות.",
                 "ייפתח Chrome בדף ההגדרות \"מערכת\". ודא שהמתג \"שימוש בהאצת גרפיקה כשהיא זמינה\" מופעל. "
                 "אם שינית אותו, לחץ \"הפעלה מחדש\" של Chrome.",
                 dict(type="open_chrome", url="chrome://settings/system"), button="פתח",
                 info=dict(verdict="הכלי רק פותח את דף ההגדרות.",
                           details="\"האצת גרפיקה\" נותנת לכרטיס המסך לפענח את הווידאו. בלעדיה, המעבד עושה את כל העבודה לבד, "
                                   "וביוטיוב באיכות גבוהה זה גורם לתמונה לקפוא לרגעים. בדרך כלל ההגדרה פעילה, אבל לפעמים היא כבויה אחרי תקלה.",
                           not_affected=["סיסמאות, סימניות, היסטוריה והתחברויות"],
                           after=["אם תשנה את ההגדרה, Chrome יבקש להפעיל את עצמו מחדש. הלשוניות נפתחות שוב."],
                           undo="להחזיר את המתג למצב הקודם.")),
            step("gpu_pref", "להריץ את Chrome על כרטיס המסך החזק (RTX)",
                 "במחשב שלך יש שני כרטיסי מסך. Windows לפעמים מריץ את הדפדפן על הכרטיס החלש של Intel.",
                 "ייפתח מסך \"גרפיקה\" של Windows. מצא את Google Chrome ברשימה (או הוסף אותו), לחץ עליו ובחר \"ביצועים גבוהים\". "
                 "אחרי זה סגור ופתח את Chrome. החיסרון: צריכת סוללה גבוהה יותר כשלא מחובר לחשמל.",
                 dict(type="open", target="ms-settings:display-advancedgraphics"), button="פתח",
                 info=dict(verdict="הכלי רק פותח את מסך ההגדרות.",
                           details="במחשב שלך יש כרטיס מסך חסכוני של Intel וכרטיס חזק של NVIDIA (RTX 3060). "
                                   "Windows מחליט לבד איזה כרטיס כל תוכנה מקבלת, ולדפדפן הוא בדרך כלל נותן את החסכוני. "
                                   "אפשר לקבוע ל-Chrome את הכרטיס החזק.",
                           not_affected=["שאר התוכנות והמשחקים", "Chrome והנתונים שלו"],
                           after=["צריכת סוללה גבוהה יותר כשהמחשב לא מחובר לחשמל.",
                                  "צריך לסגור ולפתוח את Chrome כדי שזה ייכנס לתוקף."],
                           undo="באותו מסך: לבחור ב-Chrome \"תן ל-Windows להחליט\".")),
        ]))

    order = {"high": 0, "medium": 1, "low": 2, "ok": 3}
    findings.sort(key=lambda f: order[f["severity"]])
    return findings


def all_steps(findings):
    for f in findings:
        for s in f.get("steps", []):
            yield s
