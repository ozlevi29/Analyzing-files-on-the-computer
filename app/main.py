# -*- coding: utf-8 -*-
"""
CleanWhy (רופא המחשב) - a local server that shows its interface in an Edge app window.

The server listens only on 127.0.0.1 (this computer) and requires a random key
created on every start, so other websites open in a browser cannot send it commands.
Delete actions are accepted only for paths and steps that the scan itself produced.
"""

import ctypes
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
from urllib.parse import parse_qs, quote, urlparse
import base64

FROZEN = getattr(sys, "frozen", False)  # running as CleanWhy.exe (PyInstaller)
HERE = sys._MEIPASS if FROZEN else os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# In the windowed exe there is no console: send output and errors to a log file.
DATA_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "CleanWhy")
# Before 1.1.0 the program was called "PC Doctor" and kept its data in ...\PCDoctor.
LEGACY_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "PCDoctor")
os.makedirs(DATA_DIR, exist_ok=True)
if FROZEN or sys.stdout is None or sys.stderr is None:
    _log = open(os.path.join(DATA_DIR, "log.txt"), "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stderr = _log

import diagnostics  # noqa: E402
import quarantine  # noqa: E402
import report  # noqa: E402
import rules  # noqa: E402
import scanner  # noqa: E402
from version import __version__  # noqa: E402

STATIC = os.path.join(HERE, "static")
TOKEN = secrets.token_urlsafe(24)
SYSDRIVE = os.environ.get("SystemDrive", "C:") + "\\"
REPO_URL = "https://github.com/ozlevi29/CleanWhy"
AUTHOR_LINKEDIN = "https://www.linkedin.com/in/ozlevi1/"
# The only external addresses the program ever opens (in the user's regular browser).
LINKS = {
    # Open a normal "new post" window. Sites do not let other programs attach images or text,
    # so the card image is saved to Downloads and the text is copied to the clipboard first.
    "linkedin": "https://www.linkedin.com/feed/?shareActive=true",
    "facebook": "https://www.facebook.com/",
    "author": AUTHOR_LINKEDIN,
    "repo": REPO_URL,
    "releases": REPO_URL + "/releases",
}

MSG = {
    "cmd_opened": ("נפתח חלון פקודה. אם Windows מבקש אישור מנהל, לחץ \"כן\". עקוב אחרי החלון עד שהוא מסיים.",
                   "A command window opened. If Windows asks for administrator approval, click \"Yes\". Follow the window until it finishes."),
    "startup_off": ("בוטל. התוכנה לא תיפתח יותר בהדלקת המחשב.", "Done. The program will no longer open when the PC starts."),
    "opened": ("נפתח.", "Opened."),
    "no_chrome": ("Chrome לא נמצא. פתח את Chrome והקלד בשורת הכתובת: ", "Chrome was not found. Open Chrome and type in the address bar: "),
    "chrome_opened": ("נפתח ב-Chrome.", "Opened in Chrome."),
    "restart": ("המחשב יופעל מחדש בעוד דקה. לביטול: shutdown /a בחלון פקודה.",
                "The PC will restart in one minute. To cancel: shutdown /a in a command window."),
    "no_permission": ("אין הרשאה. נסה להפעיל את הכלי כמנהל.", "Permission denied. Try running the tool as administrator."),
    "scan_running": ("סריקה כבר רצה", "A scan is already running"),
    "no_step": ("הצעד לא נמצא. הרץ סריקה מחדש.", "Step not found. Run the scan again."),
    "no_rule": ("כלל לא מוכר", "Unknown item"),
    "no_action": ("לפריט הזה אין פעולה אוטומטית", "This item has no automatic action"),
    "not_scanned": ("הנתיב לא הופיע בתוצאות הסריקה", "This path was not in the scan results"),
    "recycle_failed": ("לא הצלחתי להעביר לסל המחזור. ייתכן שהקובץ פתוח בתוכנה אחרת.",
                       "Could not move to the Recycle Bin. The file may be open in another program."),
    "admin_cancelled": ("ההפעלה כמנהל בוטלה.", "Running as administrator was cancelled."),
}


def msg(key, lang):
    he, en = MSG[key]
    return he if lang == "he" else en


class State:
    lock = threading.Lock()
    scan = dict(status="idle")  # idle / running / done / error
    results = None
    disk_scan = None
    done_steps = {}
    # for the share card: numbers before the first fix, and what was done since
    stats = dict(baseline=None, freed=0, quarantined=0, startup_disabled=0, actions=0)
    edge_proc = None


def _mem_load():
    return diagnostics.memory()["load"]


# ------------------------------------------------------------------ the scan
def run_scan(deep):
    st = State.scan
    try:
        st.update(status="running", stage=1, pct=2, started=time.time())
        diag = diagnostics.collect()

        st.update(stage=2, pct=10)

        def prog(i, n, title):
            st.update(pct=10 + int(i / n * 20), detail=title)  # title = {"he": ..., "en": ...}
        rule_items = scanner.measure_rules(prog)
        downloads = scanner.old_downloads()

        disk = None
        if deep:
            ds = scanner.DiskScan(SYSDRIVE)
            State.disk_scan = ds
            used = shutil.disk_usage(SYSDRIVE).used
            st.update(stage=3, pct=30)
            t = threading.Thread(target=ds.run, daemon=True)
            t.start()
            while t.is_alive():
                t.join(0.5)
                st.update(pct=30 + int(min(1.0, ds.bytes / max(used, 1)) * 65),
                          detail=ds.current, files=ds.files, scanned=ds.bytes)
            disk = ds.result

        st.update(stage=4, pct=97, detail="")
        findings = report.build_all(diag, rule_items, disk)  # {"he": [...], "en": [...]}
        with State.lock:
            State.results = dict(diag=diag, rules=rule_items, downloads=downloads, disk=disk,
                                 findings=findings, finished=time.time(), deep=deep)
            State.done_steps = {}
            if State.stats["baseline"] is None:  # the "before" numbers for the share card
                State.stats["baseline"] = dict(free=disk_now()["free"], mem=diag["memory"]["load"], time=time.time(),
                                               startup=sum(1 for s in diag["startup"] if s["enabled"]))
        st.update(status="done", pct=100)
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


def open_in_browser(url):
    """Opens a web page in Chrome when it is installed (where people are usually signed in to LinkedIn
    and Facebook), otherwise in the default browser."""
    chrome = _chrome_path()
    if chrome:
        subprocess.Popen([chrome, url])
    else:
        os.startfile(url)


def run_command(cmd, admin):
    if admin:
        # Opens a cmd window with an administrator (UAC) prompt. The command is fixed in the code, never user input.
        subprocess.Popen(["powershell", "-NoProfile", "-Command",
                          f"Start-Process cmd -ArgumentList '/k {cmd}' -Verb RunAs"],
                         creationflags=diagnostics.NO_WINDOW)
    else:
        subprocess.Popen(["cmd", "/k", cmd], creationflags=subprocess.CREATE_NEW_CONSOLE)


def execute(action, lang="he", undo=False, title=None):
    """
    Runs one action. With undo=True, cleaning moves files into the quarantine
    (restorable for 7 days) instead of deleting them.
    """
    t = action["type"]
    if t == "clean_rules":
        batch = quarantine.Batch(title or {"he": "ניקוי", "en": "Cleanup"}) if undo else None
        done = skipped = 0
        for rid in action["rules"]:
            f, s = scanner.clean_rule(rules.rule_by_id(rid), batch)
            done += f
            skipped += s
        if batch is not None:
            info = batch.save() or {}
            State.stats["quarantined"] += done
            return dict(quarantined=done, skipped=skipped, batch=info.get("id"), expires=info.get("expires"))
        State.stats["freed"] += done
        return dict(freed=done, skipped=skipped)
    if t == "empty_recycle":
        freed = scanner.empty_recycle_bin()
        State.stats["freed"] += freed
        return dict(freed=freed)
    if t == "command":
        run_command(action["command"], action.get("admin", True))
        return dict(message=msg("cmd_opened", lang))
    if t == "disable_startup":
        diagnostics.set_startup_enabled(action["hive"], action["sub"], action["name"], False)
        State.stats["startup_disabled"] += 1
        return dict(message=msg("startup_off", lang))
    if t == "open":
        os.startfile(action["target"])
        return dict(message=msg("opened", lang))
    if t == "open_chrome":
        chrome = _chrome_path()
        if not chrome:
            return dict(message=msg("no_chrome", lang) + action["url"])
        subprocess.Popen([chrome, action["url"]])
        return dict(message=msg("chrome_opened", lang))
    if t == "restart":
        subprocess.Popen(["shutdown", "/r", "/t", "60"], creationflags=diagnostics.NO_WINDOW)
        return dict(message=msg("restart", lang))
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


def _step_title(sid):
    out = {}
    for lang in ("he", "en"):
        fs = ((State.results or {}).get("findings") or {}).get(lang, [])
        s = next((s for s in report.all_steps(fs) if s["id"] == sid), None)
        out[lang] = s["title"] if s else sid
    return out


def relaunch_as_admin():
    """Start a new elevated copy of the program, then close this one (and its window)."""
    if FROZEN:
        exe, params = sys.executable, ""
    else:
        exe, params = sys.executable, f'"{os.path.abspath(__file__)}"'
    rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)
    if rc <= 32:  # the user clicked "No" on the UAC prompt
        return False

    def bye():
        time.sleep(0.5)
        if State.edge_proc and State.edge_proc.poll() is None:
            State.edge_proc.terminate()
        os._exit(0)
    threading.Thread(target=bye, daemon=True).start()
    return True


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

    def _lang(self):
        return "en" if (self.headers.get("X-Lang") or "").lower() == "en" else "he"

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
            if res and res.get("disk"):  # the tree is sent separately via /api/tree
                res = dict(res, disk={k: v for k, v in res["disk"].items() if k != "tree"})
            return self._send(200, dict(scan=State.scan, results=res, done_steps=State.done_steps,
                                        disk=disk_now(), admin=scanner.is_admin(), version=__version__,
                                        stats=dict(State.stats, mem_now=_mem_load()),
                                        quarantine=dict(size=quarantine.total_size(), days=quarantine.KEEP_DAYS)))
        if url.path == "/api/tree":
            q = parse_qs(url.query).get("path", [""])[0]
            lang = "en" if parse_qs(url.query).get("lang", ["he"])[0] == "en" else "he"
            disk = (State.results or {}).get("disk") or {}
            children = disk.get("tree", {}).get(q, [])
            return self._send(200, [dict(path=p, size=s, name=os.path.basename(p.rstrip("\\")) or p,
                                         hint=rules.folder_hint(p, lang), has_children=p in disk.get("tree", {}))
                                    for p, s in children])
        if url.path == "/api/quarantine":
            return self._send(200, quarantine.list_batches())
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
            return self._send(400, {"error": msg("no_permission", self._lang()) + " (" + str(e) + ")"})
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            return self._send(400, {"error": str(e)})

    def route(self, path, body):
        lang = self._lang()
        undo = bool(body.get("undo"))
        if path == "/api/scan":
            if State.scan.get("status") == "running":
                return dict(ok=False, error=msg("scan_running", lang))
            State.scan = dict(status="running", pct=0)
            threading.Thread(target=run_scan, args=(bool(body.get("deep", True)),), daemon=True).start()
            return dict(ok=True)
        if path == "/api/cancel":
            if State.disk_scan:
                State.disk_scan.cancel = True
            return dict(ok=True)
        if path == "/api/fix":
            sid = body.get("step")
            findings = ((State.results or {}).get("findings") or {}).get("he", [])  # same ids and actions in both languages
            step = next((s for s in report.all_steps(findings) if s["id"] == sid), None)
            if not step:
                raise ValueError(msg("no_step", lang))
            if step["action"]["type"] == "goto":
                return dict(ok=True)
            res = execute(step["action"], lang, undo=undo, title=_step_title(sid))
            State.done_steps[sid] = res
            State.stats["actions"] += 1
            return dict(ok=True, result=res, disk=disk_now())
        if path == "/api/rule":
            r = rules.rule_by_id(body.get("rule"))
            if not r:
                raise ValueError(msg("no_rule", lang))
            title = {lg: t["title"] for lg, t in rules.rule_text(r).items()}
            if r["action"] == "clean":
                res = execute(dict(type="clean_rules", rules=[r["id"]]), lang, undo=undo, title=title)
            elif r["action"] == "recycle":
                res = execute(dict(type="empty_recycle"), lang)
            elif r["action"] == "command":
                res = execute(dict(type="command", command=r["command"], admin=r.get("admin_cmd", True)), lang)
            elif r["action"] == "open":
                res = execute(dict(type="open", target=r["open_target"]), lang)
            else:
                raise ValueError(msg("no_action", lang))
            State.stats["actions"] += 1
            return dict(ok=True, result=res, disk=disk_now())
        if path == "/api/recycle_file":
            p = body.get("path", "")
            if os.path.normcase(p) not in _known_paths("files"):
                raise ValueError(msg("not_scanned", lang))
            size = scanner.tree_size(p)
            if not scanner.send_to_recycle_bin(p):
                raise ValueError(msg("recycle_failed", lang))
            State.stats["actions"] += 1
            return dict(ok=True, result=dict(recycled=size), disk=disk_now())
        if path == "/api/delete_nm":
            p = body.get("path", "")
            if os.path.normcase(p) not in _known_paths("nm") or os.path.basename(p).lower() != "node_modules":
                raise ValueError(msg("not_scanned", lang))
            State.stats["actions"] += 1
            if undo:
                project = os.path.basename(os.path.dirname(p))
                b = quarantine.Batch({"he": f"node_modules של {project}", "en": f"node_modules of {project}"})
                moved = b.move(p)
                info = b.save() or {}
                if not moved:
                    raise ValueError(msg("recycle_failed", lang))
                State.stats["quarantined"] += moved
                return dict(ok=True, result=dict(quarantined=moved, batch=info.get("id"), expires=info.get("expires")),
                            disk=disk_now())
            freed = scanner.delete_tree(p)
            State.stats["freed"] += freed
            return dict(ok=True, result=dict(freed=freed), disk=disk_now())
        if path == "/api/quarantine/restore":
            res = quarantine.restore(body.get("id"))
            State.stats["quarantined"] = max(0, State.stats["quarantined"] - res["restored"])
            return dict(ok=True, result=res, disk=disk_now())
        if path == "/api/quarantine/purge":
            res = quarantine.purge(body.get("id"))
            return dict(ok=True, result=res, disk=disk_now())
        if path == "/api/open_location":
            p = body.get("path", "")
            if os.path.normcase(p) not in _known_paths("any"):
                raise ValueError(msg("not_scanned", lang))
            if os.path.isdir(p):
                os.startfile(p)
            else:
                subprocess.Popen(["explorer", "/select,", p])
            return dict(ok=True)
        if path == "/api/open_recycle_bin":
            os.startfile("shell:RecycleBinFolder")
            return dict(ok=True)
        if path in ("/api/open_share", "/api/open_link"):
            # Opens a page in the user's regular browser (where they are signed in). Fixed URLs only.
            url = LINKS.get(body.get("site"))
            if not url:
                raise ValueError("unknown site")
            if body.get("site") == "linkedin" and body.get("text"):
                url += "&text=" + quote(str(body["text"])[:2500])  # LinkedIn pre-fills the post with this text
            open_in_browser(url)
            return dict(ok=True)
        if path == "/api/show_card":
            # Opens File Explorer at the saved share card (fixed file name in Downloads).
            out = os.path.join(os.path.expanduser("~"), "Downloads", "cleanwhy-result.png")
            if os.path.exists(out):
                subprocess.Popen(["explorer", "/select,", out])
            else:
                os.startfile(os.path.dirname(out))
            return dict(ok=True)
        if path == "/api/save_card":
            # Saves the share card PNG to the Downloads folder (fixed file name) and shows it in Explorer.
            data = str(body.get("png", ""))
            prefix = "data:image/png;base64,"
            if not data.startswith(prefix):
                raise ValueError("bad image")
            raw = base64.b64decode(data[len(prefix):])
            if raw[1:4] != b"PNG" or len(raw) > 10 * 1024 * 1024:  # PNG signature check
                raise ValueError("bad image")
            folder = os.path.join(os.path.expanduser("~"), "Downloads")
            os.makedirs(folder, exist_ok=True)
            out = os.path.join(folder, "cleanwhy-result.png")
            with open(out, "wb") as f:
                f.write(raw)
            if body.get("show"):
                subprocess.Popen(["explorer", "/select,", out])
            return dict(ok=True, path=out)
        if path == "/api/relaunch_admin":
            if not relaunch_as_admin():
                raise ValueError(msg("admin_cancelled", lang))
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
    Opens the interface as a separate app window (Edge in app mode) with its own profile,
    so cleaning the Chrome/Edge cache never conflicts with the tool's window.
    Closing the window closes the program.
    """
    edge = _edge_path()
    if not edge:
        webbrowser.open(url)
        return
    profile = os.path.join(DATA_DIR, "window-profile")
    # The window's own profile holds nothing of the user's. If Edge grew it anyway, start fresh.
    if os.path.isdir(profile) and scanner.tree_size(profile) > 300 * 1024 ** 2:
        shutil.rmtree(profile, ignore_errors=True)
    started = time.time()
    proc = subprocess.Popen([
        edge, f"--app={url}", f"--user-data-dir={profile}", "--window-size=1280,900",
        "--no-first-run", "--no-default-browser-check",
        # keep the window lightweight: no component downloads, sync, extensions or shopping features
        "--disable-component-update", "--disable-background-networking", "--disable-sync", "--disable-extensions",
        "--disable-features=msEdgeShoppingUI,msWalletCheckout,EdgeCollectionsEnabled,msEdgeSidebarV2",
    ])
    State.edge_proc = proc
    proc.wait()
    if time.time() - started > 5:  # the user closed the window
        os._exit(0)


def main():
    if os.environ.get("CLEANWHY_TEST_STATS"):  # for tests/screenshots only: preload share-card numbers
        State.stats.update(json.loads(os.environ["CLEANWHY_TEST_STATS"]))
    # Clean up what the old "PC Doctor" version left behind: its window profile and log.
    # Its quarantine stays readable (see quarantine.py) until it expires.
    old_running = "pcdoctor.exe" in diagnostics._run(["tasklist", "/fo", "csv", "/nh"]).lower()
    for leftover in (() if old_running else ("window-profile", "log.txt")):  # never while the old version is open
        p = os.path.join(LEGACY_DIR, leftover)
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)
        elif os.path.isfile(p):
            try:
                os.remove(p)
            except OSError:
                pass
    # Delete quarantine batches older than 7 days, in the background.
    threading.Thread(target=quarantine.purge_expired, daemon=True).start()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}/#t={TOKEN}"
    print("=" * 60)
    print(f" CleanWhy {__version__} is running. The window opens automatically.")
    print(" If it does not open, paste this address into a browser:")
    print(" " + url)
    print(" To quit: click 'Exit' in the window, or close this console.")
    print("=" * 60)
    if not os.environ.get("CLEANWHY_NO_WINDOW"):  # for tests: no window
        threading.Thread(target=open_window, args=(url,), daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
