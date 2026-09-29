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

# name (or part of the command) -> why it is safe to turn off, in Hebrew and English.
# Only well-known programs whose startup entry can be disabled without breaking anything.
STARTUP_ADVICE = [
    ("microsoftedgeautolaunch", "Edge נטען ברקע בכל הדלקה, גם אם אתה לא משתמש בו. הוא ייפתח כרגיל כשתלחץ עליו.",
     "Edge preloads in the background at every start, even if you do not use it. It still opens normally when you click it."),
    ("googlechromeautolaunch", "Chrome נטען ברקע עם הדלקת המחשב ותופס זיכרון עוד לפני שפתחת אותו. הוא ייפתח כרגיל כשתלחץ עליו.",
     "Chrome preloads in the background at startup and uses memory before you even open it. It still opens normally when you click it."),
    ("microsoftcopilotautolaunch", "Copilot נטען ברקע בכל הדלקה. אפשר לפתוח אותו ידנית כשצריך.",
     "Copilot loads in the background at every start. You can open it manually when needed."),
    ("teams", "Teams נטען בכל הדלקה ותופס כמה מאות MB של זיכרון. אם אתה לא בפגישות כל יום, עדיף לפתוח אותו ידנית.",
     "Teams loads at every start and uses a few hundred MB of memory. If you are not in meetings every day, open it manually."),
    ("adobeaamupdater", "בודק עדכונים של Adobe ברקע. Adobe יבדוק עדכונים גם כשתפתח את התוכנה.",
     "Checks for Adobe updates in the background. Adobe also checks for updates when you open the program."),
    ("adobe acrobat synchronizer", "מסנכרן קבצי PDF עם הענן של Adobe. אם אתה לא משתמש ב-Adobe Cloud, מיותר.",
     "Syncs PDF files with Adobe's cloud. Unnecessary if you do not use Adobe Cloud."),
    ("adobegcinvoker", "בדיקת רישיון של Adobe. לא נחוץ בהפעלה.", "Adobe license check. Not needed at startup."),
    ("logitech download assistant", "מציע להוריד תוכנות של Logitech. לא נחוץ כדי שהעכבר או המקלדת יעבדו.",
     "Offers to download Logitech software. Not needed for your mouse or keyboard to work."),
    ("logi download assistant", "מציע להוריד תוכנות של Logitech. לא נחוץ כדי שהעכבר או המקלדת יעבדו.",
     "Offers to download Logitech software. Not needed for your mouse or keyboard to work."),
    ("onenote", "כלי \"שלח ל-OneNote\". כמעט אף אחד לא צריך אותו בהפעלה.",
     "The \"Send to OneNote\" tool. Almost nobody needs it at startup."),
    ("nvidia broadcast", "משתמש בכרטיס המסך ובמעבד כל הזמן לסינון רעשים ורקע וירטואלי. אם אתה לא בשיחת וידאו, הוא סתם עובד. תוכל לפתוח אותו ידנית לפני שיחה.",
     "Uses the graphics card and CPU all the time for noise removal and virtual backgrounds. When you are not in a video call it works for nothing. Open it manually before a call."),
    ("spotify", "Spotify נפתח בכל הדלקה. אפשר לפתוח אותו ידנית.", "Spotify opens at every start. You can open it manually."),
    ("discord", "Discord נפתח בכל הדלקה ותופס זיכרון. אפשר לפתוח אותו ידנית.", "Discord opens at every start and uses memory. You can open it manually."),
    ("steam", "Steam נפתח בכל הדלקה ובודק עדכונים ברקע. אפשר לפתוח אותו ידנית כשמשחקים.",
     "Steam opens at every start and checks for updates in the background. Open it manually when you play."),
    ("epicgameslauncher", "Epic Games נפתח בכל הדלקה. אפשר לפתוח אותו ידנית כשמשחקים.",
     "Epic Games opens at every start. Open it manually when you play."),
    ("skype", "Skype נפתח בכל הדלקה.", "Skype opens at every start."),
    ("ccleaner", "CCleaner רץ ברקע. לא נחוץ.", "CCleaner runs in the background. Not needed."),
    ("utorrent", "uTorrent רץ ברקע ומשתמש באינטרנט. זה יכול לגרום לסרטונים להיתקע.",
     "uTorrent runs in the background and uses your internet. This can make videos stutter."),
    ("bittorrent", "BitTorrent רץ ברקע ומשתמש באינטרנט. זה יכול לגרום לסרטונים להיתקע.",
     "BitTorrent runs in the background and uses your internet. This can make videos stutter."),
    ("wondershare helper", "עוזר רקע של Wondershare שבודק עדכונים ופרסומות. התוכנות של Wondershare עובדות גם בלעדיו.",
     "A Wondershare background helper that checks for updates and promotions. Wondershare programs work without it."),
    ("sunjavaupdatesched", "בודק עדכונים ל-Java ברקע. אפשר לעדכן Java ידנית פעם בכמה חודשים.",
     "Checks for Java updates in the background. You can update Java manually every few months."),
]

FRIENDLY = [("microsoftedgeautolaunch", "Microsoft Edge"), ("googlechromeautolaunch", "Google Chrome"),
            ("microsoftcopilotautolaunch", "Microsoft Copilot"), ("sunjavaupdatesched", "Java Update"),
            ("adobeaamupdater", "Adobe Updater")]


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
        it["advice"] = None
        if not any(k in low for k in KEEP_STARTUP):
            for key, he, en in STARTUP_ADVICE:
                if key in low:
                    it["advice"] = {"he": he, "en": en}
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


def gpus():
    return [g.get("Name") for g in _ps_json("Get-CimInstance Win32_VideoController|Select Name|ConvertTo-Json -Compress")
            if g.get("Name") and "basic" not in g.get("Name", "").lower()]


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
                disks=disk_health(), network=network(), gpus=gpus(), admin=scanner.is_admin())
