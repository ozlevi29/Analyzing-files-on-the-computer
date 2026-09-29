# -*- coding: utf-8 -*-
"""
Quarantine: "delete with undo".

Instead of deleting, files are *moved* (renamed) into a quarantine folder on the
same drive. Renaming on the same drive is instant and needs no extra space.
Each action creates one batch with a manifest of where every item came from.

    restore(batch)  -> moves everything back to its original place
    purge(batch)    -> deletes the batch permanently
    purge_expired() -> deletes batches older than KEEP_DAYS (runs on startup)

Important: files in quarantine still use disk space until the batch is purged.
"""

import json
import os
import shutil
import stat
import threading
import time
import uuid

KEEP_DAYS = 7
_lock = threading.Lock()


def _local_root():
    return os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "PCDoctor", "quarantine")


def root_for(path):
    """Quarantine folder on the same drive as `path`, so moving is a fast rename."""
    local = _local_root()
    drive = os.path.splitdrive(os.path.abspath(path))[0].upper()
    if drive == os.path.splitdrive(local)[0].upper():
        return local
    return os.path.join(drive + "\\", ".pcdoctor-quarantine")


def _all_roots():
    roots = {_local_root()}
    for i in range(26):
        r = f"{chr(65 + i)}:\\.pcdoctor-quarantine"
        if os.path.isdir(r):
            roots.add(r)
    return [r for r in roots if os.path.isdir(r)]


def _is_link(p):
    try:
        return os.path.islink(p) or (hasattr(os.path, "isjunction") and os.path.isjunction(p))
    except OSError:
        return True


def _size(p):
    try:
        st = os.lstat(p)
    except OSError:
        return 0
    if not stat.S_ISDIR(st.st_mode):
        return st.st_size
    total = 0
    for root, dirs, files in os.walk(p, onerror=lambda e: None):
        dirs[:] = [d for d in dirs if not _is_link(os.path.join(root, d))]
        for f in files:
            try:
                total += os.lstat(os.path.join(root, f)).st_size
            except OSError:
                pass
    return total


class Batch:
    """Collects moved items for one action and writes its manifest."""

    def __init__(self, title):
        self.id = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
        self.title = title  # {"he": ..., "en": ...}
        self.created = time.time()
        self.items = []  # dicts: orig, stored, size, is_dir
        self.dirs = {}   # quarantine root -> batch dir

    def _batch_dir(self, orig):
        root = root_for(orig)
        if root not in self.dirs:
            d = os.path.join(root, self.id)
            os.makedirs(os.path.join(d, "items"), exist_ok=True)
            self.dirs[root] = d
        return self.dirs[root]

    def move(self, orig, size=None):
        """Move one file or folder into the batch. Returns bytes moved (0 if it failed, e.g. locked)."""
        bdir = self._batch_dir(orig)
        stored = os.path.join(bdir, "items", str(len(self.items)))
        is_dir = os.path.isdir(orig) and not _is_link(orig)
        if size is None:
            size = _size(orig)
        try:
            os.rename(orig, stored)
        except OSError:
            return 0
        self.items.append(dict(orig=orig, stored=stored, size=size, is_dir=is_dir))
        return size

    def save(self):
        if not self.items:
            for d in self.dirs.values():
                shutil.rmtree(d, ignore_errors=True)
            return None
        total = sum(i["size"] for i in self.items)
        for root, d in self.dirs.items():
            mine = [i for i in self.items if i["stored"].startswith(d)]
            with open(os.path.join(d, "manifest.json"), "w", encoding="utf-8") as f:
                json.dump(dict(id=self.id, title=self.title, created=self.created, total=total,
                               items=mine), f, ensure_ascii=False)
        return dict(id=self.id, size=total, count=len(self.items), expires=self.created + KEEP_DAYS * 86400)


def list_batches():
    """All batches, newest first. A batch may span drives; parts are merged by id."""
    merged = {}
    for root in _all_roots():
        try:
            names = os.listdir(root)
        except OSError:
            continue
        for name in names:
            man = os.path.join(root, name, "manifest.json")
            try:
                with open(man, encoding="utf-8") as f:
                    m = json.load(f)
            except (OSError, ValueError):
                continue
            b = merged.setdefault(m["id"], dict(id=m["id"], title=m["title"], created=m["created"],
                                                 size=0, count=0, dirs=[], sample=[]))
            b["size"] += sum(i["size"] for i in m["items"])
            b["count"] += len(m["items"])
            b["dirs"].append(os.path.join(root, name))
            b["sample"] += [i["orig"] for i in m["items"][:20 - len(b["sample"])]]
    out = sorted(merged.values(), key=lambda b: -b["created"])
    for b in out:
        b["expires"] = b["created"] + KEEP_DAYS * 86400
    return out


def _get(batch_id):
    return next((b for b in list_batches() if b["id"] == batch_id), None)


def restore(batch_id):
    """Move every item back. Items whose original place is taken again (e.g. a rebuilt cache) are kept in quarantine."""
    with _lock:
        b = _get(batch_id)
        if not b:
            raise ValueError("batch not found")
        restored = skipped = 0
        for d in b["dirs"]:
            man_path = os.path.join(d, "manifest.json")
            with open(man_path, encoding="utf-8") as f:
                m = json.load(f)
            left = []
            for it in m["items"]:
                if os.path.lexists(it["orig"]) or not os.path.lexists(it["stored"]):
                    skipped += 1
                    left.append(it)
                    continue
                try:
                    os.makedirs(os.path.dirname(it["orig"]), exist_ok=True)
                    os.rename(it["stored"], it["orig"])
                    restored += it["size"]
                except OSError:
                    skipped += 1
                    left.append(it)
            if left:
                m["items"] = left
                with open(man_path, "w", encoding="utf-8") as f:
                    json.dump(m, f, ensure_ascii=False)
            else:
                shutil.rmtree(d, ignore_errors=True)
        return dict(restored=restored, skipped=skipped)


def _rmtree(p):
    def onerr(func, path, exc):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except OSError:
            pass
    shutil.rmtree(p, onexc=onerr)


def purge(batch_id):
    with _lock:
        b = _get(batch_id)
        if not b:
            raise ValueError("batch not found")
        for d in b["dirs"]:
            _rmtree(d)
        return dict(freed=b["size"])


def purge_expired():
    freed = 0
    for b in list_batches():
        if b["expires"] < time.time():
            try:
                freed += purge(b["id"])["freed"]
            except (OSError, ValueError):
                pass
    return freed


def total_size():
    return sum(b["size"] for b in list_batches())
