# PC Doctor

**English** | [עברית](README.he.md)

A free, open-source Windows tool that explains **why your PC is slow** and shows **what you can safely delete**, with a clear explanation before every action.

![The "Why is my PC slow" report](docs/images/report-en.png)

## What it does

- **Finds why the PC is slow.** It checks disk space, memory, startup programs, antivirus, power settings and your internet connection. Then it lists the causes, most important first.
- **Gives you steps to fix it.** Every step has a **Fix** button, and an **i** button that explains in detail what will happen.
- **Shows what you can delete.** It lists every known junk and cache folder on your PC, with its size and a clear safety label.
- **Finds large files and folders.** A full scan of drive C shows where the space went, which files are over 500 MB, and which `node_modules` folders you can remove.
- **Lets you undo.** Cleanups can be kept in a quarantine for 7 days, and restored with one click from the **Undo** tab.
- **Shows what you achieved.** After fixing, a result card shows how much you cleaned, ready to save and share.
- **Works in English and Hebrew.** Switch with one click in the top bar.

## Why it is safe

- **Nothing happens without your approval.** Before every action, a window explains exactly what will happen. It runs only after you click "Yes".
- **The scan only reads.** Scanning never deletes or changes anything.
- **You can undo.** With "Keep for 7 days so I can undo" checked, files are moved aside instead of deleted, and the **Undo** tab restores them exactly where they were.
- **Your personal files are never deleted automatically.** Documents, photos and videos can only be moved to the Recycle Bin, one at a time, by you.
- **Caches are cleaned carefully.** Files a program is using right now are skipped. Temporary files from the last 24 hours are skipped too.
- **System changes go through Windows' own tools.** Turning off hibernation or cleaning old updates runs the official Windows commands, in a visible window.
- **It stays on your computer.** The tool runs locally and uploads nothing. The only network activity is a short connection test to 8.8.8.8 and 1.1.1.1, to measure your internet speed.
- **The code is open.** Every rule and every explanation is in [app/rules.py](app/rules.py) and [app/rules_en.py](app/rules_en.py).

## Quick start

### 1. Download

Download **PCDoctor.exe** from the [latest release](https://github.com/ozlevi29/Analyzing-files-on-the-computer/releases/latest). It is a single file. Nothing to install, and no Python needed.

### 2. Run it

Double-click **PCDoctor.exe**. A window opens with the program.

Windows may show **"Windows protected your PC"**. This appears for every new program that is not signed with a paid certificate. Click **More info**, then **Run anyway**. You can check that the file is the official one: its SHA-256 fingerprint is published next to it in the release.

Some cleanups, such as old Windows update files, need administrator rights. Click **Run as administrator** at the top of the window when you need them.

### 3. Scan

Click **Scan my PC**. The full scan takes a few minutes.

### Run from source (optional)

If you prefer to run the Python code directly: install [Python 3.12 or newer](https://www.python.org/downloads/), download the code with the green **Code** button, and double-click **`start.bat`**. To build the exe yourself, run `python tools/build_exe.py` (needs `pip install pyinstaller pillow`).

## How to use the results

The results have four tabs.

| Tab | What you will find |
|---|---|
| **Why is my PC slow** | The causes of slowness, most important first, each with steps to fix. |
| **What can I delete** | Every known junk and cache folder, with its size and a safety label. |
| **Large files and folders** | Where the space went, files over 500 MB, and `node_modules` folders. |
| **System details** | Memory, top programs, startup programs, disk health and network. |
| **Undo** | Everything you cleaned with undo on, with **Restore** and **Delete now** buttons. |

**Keep "undo" on when you can.** The confirmation window offers **"Keep for 7 days so I can undo"**. The files are moved to a quarantine folder instead of being deleted, and the **Undo** tab restores them. The catch: the space is freed only when the quarantine is emptied, automatically after 7 days, or right away with **Delete now**. When your disk is almost full, the option starts unchecked, so the space is freed immediately.

**Before you click Fix, click the i button.** It shows exactly which folders will be deleted and how big each one is. It also lists what will not be affected, what does change afterwards, and how to undo it.

![Detailed explanation window](docs/images/details-en.png)

Every item has one of four safety labels.

| Label | Meaning |
|---|---|
| **Safe to delete** | Windows or the program recreates it automatically. |
| **Check before deleting** | You can delete it, but there is a small cost. The explanation says what it is. |
| **Only through Windows** | Do not delete it by hand. The tool opens the official Windows tool for it. |
| **Do not delete** | Shown only to explain why the folder is large. |

![What can I delete](docs/images/what-can-i-delete-en.png)

## FAQ

**Does it work on Windows 10?**
It should. It was built and tested on Windows 11, and it uses only Windows features that also exist on Windows 10.

**Why does it open in an Edge window?**
The interface is a small local web page. It opens in a separate Edge app window with its own profile, so it never touches your browser data. Closing the window closes the program.

**How do I uninstall it?**
Delete PCDoctor.exe. The program also keeps its quarantine and window settings in `%LOCALAPPDATA%\PCDoctor`. Restore or delete anything in the Undo tab first, then delete that folder too.

**Why does my antivirus warn about it?**
Programs packed into a single exe with PyInstaller are sometimes flagged by mistake. The full source code is in this repository, and you can build the exe yourself with `python tools/build_exe.py`.

**Can I add more folders to clean?**
Yes. Each location is one entry in the `RULES` list in [app/rules.py](app/rules.py), with its English text in [app/rules_en.py](app/rules_en.py).

## Project structure

| File | Purpose |
|---|---|
| `app/rules.py` | The knowledge base: known locations, safety levels and Hebrew explanations. |
| `app/rules_en.py` | English texts for the knowledge base. |
| `app/scanner.py` | Measuring sizes, cleaning, Recycle Bin and the full drive scan. |
| `app/diagnostics.py` | System checks: memory, processes, startup, antivirus, disk, network. |
| `app/quarantine.py` | Undo: moves cleaned files aside for 7 days, restores them, or deletes them for good. |
| `app/report.py` | Builds the "Why is my PC slow" report and its steps, in both languages. |
| `app/main.py` | The local server that connects the interface to the actions. |
| `app/static/` | The interface (HTML, CSS, JavaScript). |
| `tools/build_exe.py` | Builds `dist/PCDoctor.exe`. |
| `winget/` | The manifest for Windows Package Manager (winget). |

The local server listens only on `127.0.0.1` and requires a random key that is created on every start. Delete actions accept only paths and steps that the scan itself produced.
