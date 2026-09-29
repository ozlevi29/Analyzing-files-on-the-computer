# -*- coding: utf-8 -*-
"""
רופא המחשב - שרת מקומי שמציג ממשק בדפדפן.

השרת מאזין רק ל-127.0.0.1 (המחשב הזה בלבד) ודורש מפתח אקראי שנוצר בכל הפעלה,
כדי שאתרים אחרים שפתוחים בדפדפן לא יוכלו לשלוח לו פקודות.
פעולות מחיקה מתקבלות רק על נתיבים וצעדים שהסריקה עצמה הציעה.
"""

import json
import mimetypes
import os
import secrets
import shutil
import subprocess
import sys
import threading
import time
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import diagnostics  # noqa: E402
import rules  # noqa: E402
import scanner  # noqa: E402

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
TOKEN = secrets.token_urlsafe(24)
SYSDRIVE = os.environ.get("SystemDrive", "C:") + "\\"


class State:
    lock = threading.Lock()
    scan = dict(status="idle")  # idle / running / done / error
    results = None
    disk_scan = None
    done_steps = {}


# ------------------------------------------------------------------ the scan
def run_scan(deep):
    st = State.scan
    try:
        st.update(status="running", stage=1, stage_label="בודק זיכרון, מעבד, תוכנות הפעלה ורשת", pct=2, started=time.time())
        diag = diagnostics.collect()

        st.update(stage=2, stage_label="מודד תיקיות זבל ומטמונים מוכרים", pct=10)

        def prog(i, n, title):
            st.update(pct=10 + int(i / n * 20), detail=title)
        rule_items = scanner.measure_rules(prog)
        downloads = scanner.old_downloads()

        disk = None
        if deep:
            ds = scanner.DiskScan(SYSDRIVE)
            State.disk_scan = ds
            used = shutil.disk_usage(SYSDRIVE).used
            st.update(stage=3, stage_label="סורק את כל הכונן (זה השלב הארוך)", pct=30)
            t = threading.Thread(target=ds.run, daemon=True)
            t.start()
            while t.is_alive():
                t.join(0.5)
                st.update(pct=30 + int(min(1.0, ds.bytes / max(used, 1)) * 65),
                          detail=ds.current, files=ds.files, scanned=ds.bytes)
            disk = ds.result

        st.update(stage=4, stage_label="מכין דוח", pct=97)
        findings = diagnostics.build_report(diag, rule_items, disk)
        with State.lock:
            State.results = dict(diag=diag, rules=rule_items, downloads=downloads, disk=disk,
                                 findings=findings, finished=time.time(), deep=deep)
            State.done_steps = {}
        st.update(status="done", pct=100, stage_label="הסריקה הסתיימה")
    except Exception as e:  # noqa: BLE001
        traceback.print_exc()
        st.update(status="error", error=str(e))


# ---------------------------------------------------------------- actions
def _chrome_path():
    for base in (os.environ.get("ProgramFiles", ""), os.environ.get("ProgramFiles(x86)", ""),
                 os.environ.get("LOCALAPPDATA", "")):
        p = os.path.join(base, "Google", "Chrome", "Application", "chrome.exe")
        if os.path.exists(p):
            return p
    return None


def run_command(cmd, admin):
    if admin:
        # פותח חלון cmd עם בקשת הרשאות מנהל (UAC). הפקודה קבועה מתוך הקוד, לא מהמשתמש.
        subprocess.Popen(["powershell", "-NoProfile", "-Command",
                          f"Start-Process cmd -ArgumentList '/k {cmd}' -Verb RunAs"],
                         creationflags=diagnostics.NO_WINDOW)
    else:
        subprocess.Popen(["cmd", "/k", cmd], creationflags=subprocess.CREATE_NEW_CONSOLE)


def execute(action):
    t = action["type"]
    if t == "clean_rules":
        freed = skipped = 0
        details = []
        for rid in action["rules"]:
            r = rules.rule_by_id(rid)
            f, s = scanner.clean_rule(r)
            freed += f
            skipped += s
            details.append(dict(title=r["title"], freed=f, skipped=s))
        return dict(freed=freed, skipped=skipped, details=details)
    if t == "empty_recycle":
        return dict(freed=scanner.empty_recycle_bin())
    if t == "command":
        run_command(action["command"], action.get("admin", True))
        return dict(message="נפתח חלון פקודה. אם Windows מבקש אישור מנהל, לחץ \"כן\". עקוב אחרי החלון עד שהוא מסיים.")
    if t == "disable_startup":
        diagnostics.set_startup_enabled(action["hive"], action["sub"], action["name"], False)
        return dict(message="בוטל. התוכנה לא תיפתח יותר בהדלקת המחשב.")
    if t == "open":
        os.startfile(action["target"])
        return dict(message="נפתח.")
    if t == "open_chrome":
        chrome = _chrome_path()
        if not chrome:
            return dict(message="Chrome לא נמצא. פתח את Chrome והקלד בשורת הכתובת: " + action["url"])
        subprocess.Popen([chrome, action["url"]])
        return dict(message="נפתח ב-Chrome.")
    if t == "restart":
        subprocess.Popen(["shutdown", "/r", "/t", "60"], creationflags=diagnostics.NO_WINDOW)
        return dict(message="המחשב יופעל מחדש בעוד דקה. לביטול: shutdown /a בחלון פקודה.")
    raise ValueError("unknown action")


def _known_paths(kind):
    res = State.results or {}
    disk = res.get("disk") or {}
    if kind == "files":
        return {os.path.normcase(x["path"]) for x in (disk.get("large_files") or []) + (res.get("downloads") or [])}
    if kind == "nm":
        return {os.path.normcase(x["path"]) for x in disk.get("node_modules") or []}
    if kind == "any":
        s = _known_paths("files") | _known_paths("nm")
        for r in res.get("rules") or []:
            s |= {os.path.normcase(p) for p in r.get("paths", [])}
        for v in (disk.get("tree") or {}).values():
            s |= {os.path.normcase(p) for p, _ in v}
        return s
    return set()


def disk_now():
    u = shutil.disk_usage(SYSDRIVE)
    return dict(root=SYSDRIVE, total=u.total, used=u.used, free=u.free)


# ------------------------------------------------------------------- http
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _authorized(self):
        host = (self.headers.get("Host") or "").split(":")[0]
        return host in ("127.0.0.1", "localhost") and secrets.compare_digest(self.headers.get("X-Token", ""), TOKEN)

    def do_GET(self):
        url = urlparse(self.path)
        if not url.path.startswith("/api/"):
            name = "index.html" if url.path in ("/", "") else url.path.lstrip("/")
            path = os.path.normpath(os.path.join(STATIC, name))
            if not path.startswith(STATIC) or not os.path.isfile(path):
                return self._send(404, {"error": "not found"})
            with open(path, "rb") as f:
                ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
                if ctype.startswith("text/") or ctype.endswith("javascript"):
                    ctype += "; charset=utf-8"
                return self._send(200, f.read(), ctype)
        if not self._authorized():
            return self._send(403, {"error": "forbidden"})
        if url.path == "/api/state":
            res = State.results
            if res and res.get("disk"):  # העץ נשלח בנפרד דרך /api/tree
                res = dict(res, disk={k: v for k, v in res["disk"].items() if k != "tree"})
            return self._send(200, dict(scan=State.scan, results=res, done_steps=State.done_steps,
                                        disk=disk_now(), admin=scanner.is_admin()))
        if url.path == "/api/tree":
            q = parse_qs(url.query).get("path", [""])[0]
            disk = (State.results or {}).get("disk") or {}
            children = disk.get("tree", {}).get(q, [])
            return self._send(200, [dict(path=p, size=s, name=os.path.basename(p.rstrip("\\")) or p,
                                         hint=rules.folder_hint(p), has_children=p in disk.get("tree", {}))
                                    for p, s in children])
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        if not self._authorized():
            return self._send(403, {"error": "forbidden"})
        url = urlparse(self.path)
        try:
            n = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            return self._send(400, {"error": "bad json"})
        try:
            return self._send(200, self.route(url.path, body))
        except PermissionError as e:
            return self._send(400, {"error": "אין הרשאה. נסה להפעיל את הכלי כמנהל. (" + str(e) + ")"})
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            return self._send(400, {"error": str(e)})

    def route(self, path, body):
        if path == "/api/scan":
            if State.scan.get("status") == "running":
                return dict(ok=False, error="סריקה כבר רצה")
            State.scan = dict(status="running", pct=0)
            threading.Thread(target=run_scan, args=(bool(body.get("deep", True)),), daemon=True).start()
            return dict(ok=True)
        if path == "/api/cancel":
            if State.disk_scan:
                State.disk_scan.cancel = True
            return dict(ok=True)
        if path == "/api/fix":
            sid = body.get("step")
            step = next((s for s in diagnostics.all_steps((State.results or {}).get("findings", [])) if s["id"] == sid), None)
            if not step:
                raise ValueError("הצעד לא נמצא. הרץ סריקה מחדש.")
            if step["action"]["type"] == "goto":
                return dict(ok=True)
            res = execute(step["action"])
            State.done_steps[sid] = res
            return dict(ok=True, result=res, disk=disk_now())
        if path == "/api/rule":
            r = rules.rule_by_id(body.get("rule"))
            if not r:
                raise ValueError("כלל לא מוכר")
            if r["action"] in ("clean", "recycle"):
                res = execute(dict(type="clean_rules", rules=[r["id"]]) if r["action"] == "clean" else dict(type="empty_recycle"))
            elif r["action"] == "command":
                res = execute(dict(type="command", command=r["command"], admin=r.get("admin_cmd", True)))
            elif r["action"] == "open":
                res = execute(dict(type="open", target=r["open_target"]))
            else:
                raise ValueError("לפריט הזה אין פעולה אוטומטית")
            return dict(ok=True, result=res, disk=disk_now())
        if path == "/api/recycle_file":
            p = body.get("path", "")
            if os.path.normcase(p) not in _known_paths("files"):
                raise ValueError("הנתיב לא הופיע בתוצאות הסריקה")
            size = scanner.tree_size(p)
            if not scanner.send_to_recycle_bin(p):
                raise ValueError("לא הצלחתי להעביר לסל המחזור. ייתכן שהקובץ פתוח בתוכנה אחרת.")
            return dict(ok=True, result=dict(recycled=size), disk=disk_now())
        if path == "/api/delete_nm":
            p = body.get("path", "")
            if os.path.normcase(p) not in _known_paths("nm") or os.path.basename(p).lower() != "node_modules":
                raise ValueError("הנתיב לא הופיע בתוצאות הסריקה")
            return dict(ok=True, result=dict(freed=scanner.delete_tree(p)), disk=disk_now())
        if path == "/api/open_location":
            p = body.get("path", "")
            if os.path.normcase(p) not in _known_paths("any"):
                raise ValueError("הנתיב לא הופיע בתוצאות הסריקה")
            if os.path.isdir(p):
                os.startfile(p)
            else:
                subprocess.Popen(["explorer", "/select,", p])
            return dict(ok=True)
        if path == "/api/open_recycle_bin":
            os.startfile("shell:RecycleBinFolder")
            return dict(ok=True)
        if path == "/api/quit":
            threading.Thread(target=lambda: (time.sleep(0.5), os._exit(0)), daemon=True).start()
            return dict(ok=True)
        raise ValueError("unknown endpoint")


def _edge_path():
    for base in (os.environ.get("ProgramFiles(x86)", ""), os.environ.get("ProgramFiles", "")):
        p = os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe")
        if os.path.exists(p):
            return p
    return None


def open_window(url):
    """
    פותח את הממשק כחלון אפליקציה נפרד (Edge במצב app) עם פרופיל משלו,
    כך שניקוי המטמון של Chrome/Edge לא מתנגש בחלון של הכלי. סגירת החלון סוגרת את התוכנה.
    """
    edge = _edge_path()
    if not edge:
        webbrowser.open(url)
        return
    profile = os.path.join(os.environ.get("LOCALAPPDATA", ""), "PCDoctor", "window-profile")
    started = time.time()
    proc = subprocess.Popen([edge, f"--app={url}", f"--user-data-dir={profile}", "--no-first-run",
                             "--no-default-browser-check", "--window-size=1280,900"])
    proc.wait()
    if time.time() - started > 5:  # החלון נסגר על ידי המשתמש
        os._exit(0)


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}/#t={TOKEN}"
    print("=" * 60)
    print(" רופא המחשב פועל. הממשק נפתח בדפדפן.")
    print(" אם הוא לא נפתח, העתק את הכתובת הזו לדפדפן:")
    print(" " + url)
    print(" כדי לסגור את התוכנה: לחץ 'יציאה' בממשק או סגור את החלון הזה.")
    print("=" * 60)
    if not os.environ.get("PCDOCTOR_NO_WINDOW"):  # לבדיקות: בלי לפתוח חלון
        threading.Thread(target=open_window, args=(url,), daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
