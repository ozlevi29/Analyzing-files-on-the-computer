# -*- coding: utf-8 -*-
"""
Builds dist/<version>/CleanWhy.exe: a single file that runs without Python installed.
Each version gets its own folder, so a copy that is currently running never blocks a new build.

    python -m pip install pyinstaller pillow
    python tools/build_exe.py

Also writes CleanWhy.exe.sha256 next to it (needed for the winget manifest and for users who
want to verify the download).
"""

import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "app")
DIST = os.path.join(ROOT, "dist")
WORK = os.path.join(ROOT, "build")


def version():
    with open(os.path.join(APP, "version.py"), encoding="utf-8") as f:
        return re.search(r'__version__\s*=\s*"([^"]+)"', f.read()).group(1)


def version_file(ver):
    """Windows file properties (Details tab). Also helps antivirus software trust the file."""
    nums = (ver.split(".") + ["0", "0", "0", "0"])[:4]
    tup = ", ".join(nums)
    path = os.path.join(WORK, "version_info.txt")
    os.makedirs(WORK, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers=({tup}), prodvers=({tup}), mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'CleanWhy (open source)'),
      StringStruct('FileDescription', 'CleanWhy - explains why your PC is slow and what you can safely delete'),
      StringStruct('FileVersion', '{ver}'),
      StringStruct('InternalName', 'CleanWhy'),
      StringStruct('OriginalFilename', 'CleanWhy.exe'),
      StringStruct('ProductName', 'CleanWhy'),
      StringStruct('ProductVersion', '{ver}'),
      StringStruct('Comments', 'https://github.com/ozlevi29/CleanWhy')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
""")
    return path


def main():
    ver = version()
    out = os.path.join(DIST, ver)
    icon = os.path.join(ROOT, "assets", "icon.ico")
    if not os.path.exists(icon):
        subprocess.check_call([sys.executable, os.path.join(ROOT, "tools", "make_icon.py")])
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onefile",
        "--windowed",                       # no console window: the UI opens in its own window
        "--name", "CleanWhy",
        "--icon", icon,
        "--version-file", version_file(ver),
        "--add-data", os.path.join(APP, "static") + os.pathsep + "static",
        "--paths", APP,
        "--distpath", out, "--workpath", WORK, "--specpath", WORK,
        os.path.join(APP, "main.py"),
    ]
    print(" ".join(cmd))
    subprocess.check_call(cmd, cwd=ROOT)
    exe = os.path.join(out, "CleanWhy.exe")
    digest = hashlib.sha256(open(exe, "rb").read()).hexdigest().upper()
    with open(exe + ".sha256", "w") as f:
        f.write(f"{digest}  CleanWhy.exe\n")
    print(f"\nBuilt {exe} (version {ver})\nSHA256 {digest}")


if __name__ == "__main__":
    main()
