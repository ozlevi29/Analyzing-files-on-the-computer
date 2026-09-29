# -*- coding: utf-8 -*-
"""מדידת גדלים, ניקוי, סל מחזור וסריקת דיסק מלאה."""

import ctypes
import glob
import os
import re
import shutil
import stat
import time
from ctypes import wintypes

import rules

HOME = rules.HOME


# ------------------------------------------------------------------ helpers
def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _is_link(entry):
    try:
        if entry.is_symlink():
            return True
        return entry.is_junction()
    except (OSError, AttributeError):
        return False


def tree_size(path):
    """גודל כולל של קובץ או תיקייה. לא עוקב אחרי קיצורי דרך / junctions."""
    try:
        st = os.lstat(path)
    except OSError:
        return 0
    if not stat.S_ISDIR(st.st_mode):
        return st.st_size
    total = 0
    stack = [path]
    while stack:
        cur = stack.pop()
        try:
            with os.scandir(cur) as it:
                for e in it:
                    try:
                        if _is_link(e):
                            continue
                        if e.is_dir(follow_symlinks=False):
                            stack.append(e.path)
                        else:
                            total += e.stat(follow_symlinks=False).st_size
                    except OSError:
                        pass
        except OSError:
            pass
    return total


def resolve(patterns):
    """מרחיב תבניות (עם *) לרשימת נתיבים קיימים, בלי כפילויות."""
    out, seen = [], set()
    for p in patterns:
        matches = glob.glob(p) if any(c in p for c in "*?") else ([p] if os.path.lexists(p) else [])
        for m in matches:
            key = os.path.normcase(os.path.abspath(m))
            if key not in seen:
                seen.add(key)
                out.append(m)
    return out


# ------------------------------------------------------------- recycle bin
class _SHQUERYRBINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("i64Size", ctypes.c_longlong), ("i64NumItems", ctypes.c_longlong)]


def recycle_bin_info():
    info = _SHQUERYRBINFO()
    info.cbSize = ctypes.sizeof(info)
    try:
        if ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(info)) == 0:
            return info.i64Size, info.i64NumItems
    except Exception:
        pass
    return 0, 0


def empty_recycle_bin():
    before, _ = recycle_bin_info()
    # SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND
    ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x1 | 0x2 | 0x4)
    after, _ = recycle_bin_info()
    return max(0, before - after)


class _SHFILEOPSTRUCTW(ctypes.Structure):
    _fields_ = [("hwnd", wintypes.HWND), ("wFunc", wintypes.UINT), ("pFrom", wintypes.LPCWSTR),
                ("pTo", wintypes.LPCWSTR), ("fFlags", ctypes.c_ushort), ("fAnyOperationsAborted", wintypes.BOOL),
                ("hNameMappings", ctypes.c_void_p), ("lpszProgressTitle", wintypes.LPCWSTR)]


def send_to_recycle_bin(path):
    """מעביר קובץ/תיקייה לסל המחזור. מחזיר True בהצלחה."""
    op = _SHFILEOPSTRUCTW()
    op.wFunc = 3  # FO_DELETE
    op.pFrom = os.path.abspath(path) + "\0\0"
    op.fFlags = 0x40 | 0x10 | 0x4 | 0x400  # ALLOWUNDO | NOCONFIRMATION | SILENT | NOERRORUI
    res = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
    return res == 0 and not op.fAnyOperationsAborted and not os.path.lexists(path)


# ------------------------------------------------------------------ cleaning
def _remove_file(path, min_mtime):
    try:
        st = os.lstat(path)
        if min_mtime and st.st_mtime > min_mtime:
            return 0, 1
        size = st.st_size
        try:
            os.remove(path)
        except PermissionError:
            os.chmod(path, stat.S_IWRITE)
            os.remove(path)
        return size, 0
    except OSError:
        return 0, 1


def clean_contents(path, min_age_days=0):
    """
    מוחק את התוכן של תיקייה (או קובץ בודד). מדלג על קבצים נעולים, על קבצים חדשים
    מ-min_age_days ועל junctions. התיקייה עצמה נשארת.
    מחזיר (בייטים שפונו, מספר פריטים שדולגו).
    """
    min_mtime = time.time() - min_age_days * 86400 if min_age_days else 0
    freed = skipped = 0
    if not os.path.lexists(path):
        return 0, 0
    if not os.path.isdir(path) or os.path.islink(path):
        return _remove_file(path, min_mtime)
    # מעבר מהעמוק לרדוד כדי שתיקיות ריקות יימחקו אחרי הקבצים שלהן
    for root, dirs, files in os.walk(path, topdown=False, onerror=lambda e: None):
        for f in files:
            fr, sk = _remove_file(os.path.join(root, f), min_mtime)
            freed += fr
            skipped += sk
        for d in dirs:
            dp = os.path.join(root, d)
            try:
                if os.path.islink(dp) or (hasattr(os.path, "isjunction") and os.path.isjunction(dp)):
                    continue
                os.rmdir(dp)
            except OSError:
                pass
    return freed, skipped


def delete_tree(path):
    """מחיקה לצמיתות של תיקייה שלמה (משמש ל-node_modules)."""
    size = tree_size(path)

    def onerr(func, p, exc):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except OSError:
            pass

    shutil.rmtree(path, onexc=onerr)  # Python 3.12+ לא עוקב אחרי junctions
    left = tree_size(path) if os.path.exists(path) else 0
    return size - left


# --------------------------------------------------------------- rule paths
def _version_key(name):
    return tuple(int(x) for x in re.findall(r"\d+", name))


def rule_paths(r):
    """הנתיבים הקיימים בפועל עבור כלל. בכלל של גרסאות ישנות: הכל חוץ מהגרסה החדשה ביותר."""
    found = resolve(r.get("paths", []))
    for base, pattern in r.get("old_versions", []):
        dirs = [d for d in glob.glob(os.path.join(base, pattern))
                if os.path.isdir(d) and not os.path.islink(d) and _version_key(os.path.basename(d))]
        dirs.sort(key=lambda d: _version_key(os.path.basename(d)))
        found.extend(dirs[:-1])  # שומרים את האחרונה
    return found


def clean_rule(r):
    """מנקה את כל הנתיבים של כלל. מחזיר (בייטים שפונו, פריטים שדולגו)."""
    if r["id"] == "recycle_bin":
        return empty_recycle_bin(), 0
    if r.get("action") != "clean":
        raise ValueError("rule is not cleanable")
    freed = skipped = 0
    for p in rule_paths(r):
        f, s = clean_contents(p, r.get("min_age_days", 0))
        freed += f
        skipped += s
        if r.get("remove_root") and os.path.isdir(p):
            try:
                os.rmdir(p)
            except OSError:
                pass
    return freed, skipped


# --------------------------------------------------------------- rule sizes
def measure_rules(progress=None):
    results = []
    admin = is_admin()
    for i, r in enumerate(rules.RULES):
        if progress:
            progress(i, len(rules.RULES), r["title"])
        item = {k: r.get(k) for k in ("id", "title", "category", "safety", "action", "what", "if_deleted", "how",
                                       "command", "open_target")}
        item["admin"] = bool(r.get("admin")) or (r["action"] == "command" and r.get("admin_cmd", True))
        item["needs_admin_now"] = bool(r.get("admin")) and not admin
        item["safety_label"] = rules.SAFETY_LABELS[r["safety"]]
        item["category_label"] = rules.CATEGORIES[r["category"]]
        if r["id"] == "recycle_bin":
            size, count = recycle_bin_info()
            item["size"], item["paths"], item["count"] = size, [], count
        elif r.get("measure") is False:
            item["size"], item["paths"] = None, []
        else:
            found = rule_paths(r)
            item["paths"] = found
            item["size"] = sum(tree_size(p) for p in found)
            if not found:
                continue  # לא קיים במחשב הזה
        results.append(item)
    return results


def old_downloads(days=30, min_size=5 * 1024 * 1024):
    """קבצים בתיקיית ההורדות שלא נגעו בהם יותר מ-X ימים."""
    root = os.path.join(HOME, "Downloads")
    cutoff = time.time() - days * 86400
    out = []
    try:
        entries = list(os.scandir(root))
    except OSError:
        return out
    for e in entries:
        try:
            if _is_link(e):
                continue
            st = e.stat(follow_symlinks=False)
            size = tree_size(e.path) if e.is_dir(follow_symlinks=False) else st.st_size
            if st.st_mtime < cutoff and size >= min_size:
                safety, hint = rules.file_hint(e.path)
                if e.is_dir(follow_symlinks=False):
                    safety, hint = "caution", "תיקייה בתוך ההורדות. בדוק את התוכן לפני מחיקה."
                out.append(dict(path=e.path, size=size, mtime=st.st_mtime, safety=safety, hint=hint,
                                is_dir=e.is_dir(follow_symlinks=False)))
        except OSError:
            pass
    out.sort(key=lambda x: -x["size"])
    return out


# ----------------------------------------------------------------- full scan
class DiskScan:
    """סריקה מלאה של כונן: גדלי תיקיות, קבצים גדולים ותיקיות node_modules."""

    LARGE_FILE = 500 * 1024 ** 2
    TREE_MIN = 200 * 1024 ** 2
    TREE_DEPTH = 6

    def __init__(self, root):
        self.root = root
        self.files = 0
        self.bytes = 0
        self.denied = 0
        self.current = ""
        self.cancel = False

    def run(self):
        paths, parent, depth, own, nm_flag = [], [], [], [], []
        large = []
        stack = [(self.root, -1, 0, False)]
        while stack:
            if self.cancel:
                break
            path, par, d, inside_nm = stack.pop()
            idx = len(paths)
            name = os.path.basename(path.rstrip("\\")).lower()
            is_nm = name == "node_modules" and not inside_nm
            paths.append(path)
            parent.append(par)
            depth.append(d)
            nm_flag.append(is_nm)
            size_here = 0
            self.current = path
            try:
                with os.scandir(path) as it:
                    for e in it:
                        try:
                            if _is_link(e):
                                continue
                            if e.is_dir(follow_symlinks=False):
                                stack.append((e.path, idx, d + 1, inside_nm or is_nm))
                            else:
                                s = e.stat(follow_symlinks=False).st_size
                                size_here += s
                                self.files += 1
                                self.bytes += s
                                if s >= self.LARGE_FILE:
                                    large.append((e.path, s))
                        except OSError:
                            pass
            except OSError:
                self.denied += 1
            own.append(size_here)

        # צבירת גדלים מלמטה למעלה (ילדים תמיד אחרי ההורה ברשימה)
        total = own[:]
        for i in range(len(paths) - 1, 0, -1):
            p = parent[i]
            if p >= 0:
                total[p] += total[i]

        tree = {}
        for i in range(len(paths)):
            if depth[i] <= self.TREE_DEPTH and total[i] >= self.TREE_MIN:
                tree.setdefault(paths[parent[i]] if parent[i] >= 0 else None, []).append((paths[i], total[i]))
        node_modules = [(paths[i], total[i]) for i in range(len(paths)) if nm_flag[i] and total[i] >= 20 * 1024 ** 2]
        node_modules.sort(key=lambda x: -x[1])
        large.sort(key=lambda x: -x[1])

        self.result = dict(
            root=self.root,
            total=total[0] if total else 0,
            tree={k or "": sorted(v, key=lambda x: -x[1]) for k, v in tree.items()},
            large_files=[dict(path=p, size=s, safety=rules.file_hint(p)[0], hint=rules.file_hint(p)[1])
                         for p, s in large[:300]],
            node_modules=[dict(path=p, project=os.path.dirname(p), size=s) for p, s in node_modules],
            denied=self.denied,
            files=self.files,
        )
        return self.result
