# -*- coding: utf-8 -*-
"""
English texts for the knowledge base in rules.py.
Keys match the rule ids. Each entry holds the short card texts
(title / what / if_deleted / how) and the detailed "i" popup texts
(verdict / details / not_affected / after / undo).
"""

SAFETY_LABELS = {
    "safe": "Safe to delete",
    "caution": "Check before deleting",
    "windows": "Only through Windows",
    "keep": "Do not delete",
}

CATEGORIES = {
    "system": "Temporary system files",
    "browser": "Browsers",
    "apps": "Applications",
    "dev": "Developer tools",
    "big": "Large system files",
}

PERSONAL = "Your documents, photos, videos and downloads"
PROGRAMS = "Installed programs. They all keep working exactly as before"

TEXT = {
    # ------------------------------------------------------------------ system
    "user_temp": dict(
        title="User temporary files",
        what="A folder where programs keep temporary files while they work: installers, opened email attachments, "
             "pieces of updates. Most programs never clean up after themselves, so the folder keeps growing.",
        if_deleted="Safe. Programs recreate whatever they need. The tool skips files created in the last 24 hours "
                   "and files that are in use right now, so it will not disturb an open program or a running install.",
        how="Clicking \"Clean\" deletes the contents permanently, without going through the Recycle Bin.",
        verdict="Nothing will break. This is a junk folder meant exactly for this.",
        details="When a program needs to keep something for a moment (opening an email attachment, installing software, "
                "extracting a ZIP), it puts it in the temp folder. It is supposed to delete it afterwards, but most programs forget. "
                "Windows itself treats this folder as junk, and Microsoft's own Disk Cleanup deletes it too.",
        not_affected=[PERSONAL, PROGRAMS, "Windows settings and program settings", "Passwords, browsers and accounts",
                      "Files from the last 24 hours (skipped, in case an install is running now)",
                      "Files a running program is using (Windows does not allow deleting them, so they are skipped)"],
        after=["Nothing noticeable. Programs create new temp files when they need them."],
        undo="No need. If you opened an email attachment and forgot to save it, it is still in the email.",
    ),
    "win_temp": dict(
        title="Windows temporary files",
        what="The system-wide temp folder. Used by Windows, background services and installers.",
        if_deleted="Safe. Same idea as the user temp folder. New and locked files are skipped.",
        how="Requires running the tool as administrator (start-as-admin.bat).",
        verdict="Nothing will break. Same junk, just Windows' own.",
        details="Like the user temp folder, but used by Windows and background services. New and locked files are skipped here too.",
        not_affected=[PERSONAL, PROGRAMS, "Windows itself and installed updates"],
        after=["Nothing noticeable."],
        undo="No need.",
    ),
    "recycle_bin": dict(
        title="Recycle Bin",
        what="Files you deleted. They still take up disk space until the bin is emptied.",
        if_deleted="Safe, as long as there is nothing in the bin you want back. After emptying, the files cannot be restored.",
        how="Open the Recycle Bin, check there is nothing important, then click \"Empty\".",
        verdict="Nothing will break, as long as the bin holds nothing you still want.",
        details="When you delete a file, Windows does not really delete it. It moves it to the Recycle Bin, where it keeps using space. "
                "Emptying the bin removes the files for good.",
        not_affected=["Everything that is not in the Recycle Bin"],
        after=["You will not be able to restore the files that were in the bin."],
        undo="There is no simple way to restore after emptying. Take a quick look inside the bin first.",
    ),
    "wu_download": dict(
        title="Windows Update download files",
        what="Update files Windows downloaded in order to install them. Once the update is installed, they are not needed.",
        if_deleted="Safe. If an update has not been installed yet, Windows simply downloads it again.",
        how="Requires administrator rights. Better not to clean while Windows Update is installing.",
        verdict="Nothing will break. The updates themselves are already installed.",
        details="Windows Update downloads update files here, installs them, and sometimes leaves the downloads behind. "
                "The installed update lives somewhere else entirely. It is like throwing away the box after assembling the furniture.",
        not_affected=[PERSONAL, PROGRAMS, "Updates that are already installed"],
        after=["If an update was downloaded but not installed yet, Windows will download it again (a few minutes in the background)."],
        undo="No need. Windows re-downloads anything that is missing.",
    ),
    "delivery_opt": dict(
        title="Delivery Optimization cache",
        what="Copies of updates Windows keeps in order to share them with other computers on the network.",
        if_deleted="Safe. It is only a cache. The updates themselves are installed.",
        how="Requires administrator rights.",
        verdict="Nothing will break.",
        details="Copies of updates Windows keeps to share with other PCs on your home network. It is a bandwidth-saving feature, not something your PC needs.",
        not_affected=[PERSONAL, PROGRAMS, "Updates that are already installed"],
        after=["Nothing noticeable."],
        undo="No need.",
    ),
    "error_reports": dict(
        title="Error and crash reports",
        what="Reports Windows creates when a program crashes, to send to Microsoft.",
        if_deleted="Safe. The reports were already sent or will not be used. Some paths need administrator rights.",
        how="Click \"Clean\".",
        verdict="Nothing will break.",
        details="When a program crashes, Windows writes a report (what crashed and when) and sends it to Microsoft. "
                "The reports then stay on disk unused.",
        not_affected=[PERSONAL, PROGRAMS, "The Windows event log (stored separately)"],
        after=["Nothing noticeable."],
        undo="No need.",
    ),
    "memory_dumps": dict(
        title="Blue screen memory dumps",
        what="A snapshot of memory saved when the PC crashes with a blue screen. Used by technicians to analyze the crash.",
        if_deleted="Safe, unless you are investigating blue screens with a technician. MEMORY.DMP can be several GB.",
        how="Requires administrator rights.",
        verdict="Nothing will break, unless a technician asked you for these files.",
        details="When the PC crashes with a blue screen, Windows saves an image of memory at that moment. Only a technician with special tools can read it.",
        not_affected=[PERSONAL, PROGRAMS],
        after=["If you contact a technician about blue screens, the old crash files will not be there (new ones are created if it happens again)."],
        undo="No need.",
    ),
    "win_logs": dict(
        title="Windows setup logs (CBS)",
        what="Logs of the Windows component installer. Sometimes they grow to gigabytes because of an update glitch.",
        if_deleted="Safe. These are only text logs. The tool deletes only logs older than a week.",
        how="Requires administrator rights.",
        verdict="Nothing will break.",
        details="Text logs of the Windows setup component. Only logs older than a week are deleted.",
        not_affected=[PERSONAL, PROGRAMS, "The updates themselves"],
        after=["Nothing noticeable."],
        undo="No need.",
    ),
    "thumbcache": dict(
        title="Thumbnail cache",
        what="Small images File Explorer keeps to show previews of photos and videos.",
        if_deleted="Safe. Explorer recreates them. The first time, opening a folder with many photos will be a bit slower. "
                   "Files Explorer currently holds open are skipped.",
        how="Click \"Clean\".",
        verdict="Nothing will break. It rebuilds itself.",
        details="When you open a folder with photos, Explorer shows thumbnails. To avoid computing them every time, it stores them here.",
        not_affected=[PERSONAL + " (the photos themselves are not touched, only their small copies)", PROGRAMS],
        after=["The first time you open a folder with many photos, thumbnails will appear more slowly (a few seconds)."],
        undo="No need. Rebuilt automatically.",
    ),
    "inetcache": dict(
        title="Windows internet cache",
        what="A cache of older Windows internet components and programs that still use them.",
        if_deleted="Safe. It is only a cache.",
        how="Click \"Clean\".",
        verdict="Nothing will break.",
        details="A cache of legacy Windows internet components (from the Internet Explorer era) that some programs still use.",
        not_affected=[PERSONAL, PROGRAMS, "Chrome and Edge (they have their own cache)"],
        after=["Nothing noticeable."],
        undo="No need.",
    ),
    "shader_cache": dict(
        title="Graphics cache (DirectX and NVIDIA)",
        what="Compiled graphics code that games and graphics programs keep so they load faster.",
        if_deleted="Safe. The first time you launch a game after cleaning it will load a bit slower, then the cache is rebuilt.",
        how="Click \"Clean\".",
        verdict="Nothing will break.",
        details="Games and graphics programs translate graphics code into the language of your graphics card, and save the result so they do not have to do it again.",
        not_affected=[PERSONAL, PROGRAMS, "Game saves, graphics settings and the display driver"],
        after=["The first time you launch a game, there may be a few small stutters in the first minute until the cache is rebuilt."],
        undo="No need.",
    ),
    "gpu_installers": dict(
        title="Old display driver installer files",
        what="Files left over after installing NVIDIA or AMD drivers.",
        if_deleted="Safe. The driver is already installed. A future update downloads whatever it needs.",
        how="Requires administrator rights.",
        verdict="Nothing will break. The driver is installed elsewhere.",
        details="When an NVIDIA driver is installed, the installer unpacks into a temporary folder and never deletes it.",
        not_affected=["The installed display driver", "GeForce Experience / NVIDIA App and their settings", PERSONAL],
        after=["Nothing noticeable."],
        undo="No need. The next driver update downloads a fresh installer.",
    ),
    "windows_old": dict(
        title="Previous Windows version (Windows.old)",
        what="A copy of the previous operating system, kept after a major upgrade so you can roll back.",
        if_deleted="After deleting, you cannot go back to the previous version. If the upgrade has been working well for a few days, it is safe. "
                   "Do not delete it by hand: the folder has system permissions and a partial delete leaves junk behind.",
        how="Settings > System > Storage > Temporary files > check \"Previous Windows installation(s)\" > Remove files.",
        verdict="Nothing will break, but you will not be able to go back to the previous Windows version.",
        details="After a major Windows upgrade, the previous copy is kept so you can roll back. Windows deletes it on its own after 10 days.",
        not_affected=[PERSONAL, PROGRAMS, "Your current Windows"],
        after=["The \"Go back\" option in Settings disappears."],
        undo="Cannot be undone.",
    ),
    # ----------------------------------------------------------------- browser
    "chrome_cache": dict(
        title="Google Chrome cache",
        what="Copies of images, scripts and videos from sites you visited, so they load faster.",
        if_deleted="Safe. Passwords, history, bookmarks and cookies (your logins to sites) are not deleted. "
                   "Sites will load a bit slower the first time. Close Chrome before cleaning, otherwise files in use are skipped.",
        how="Close Chrome and click \"Clean\".",
        verdict="Nothing will break. Nothing you see in Chrome will disappear.",
        details="Every time you visit a site, Chrome keeps a copy of its images, code and videos so it loads faster next time. "
                "The cache keeps growing, and if you have several Chrome profiles, each has its own cache. "
                "The tool deletes only the cache folders (Cache, Code Cache, GPUCache and ShaderCache) and does not touch any other file in the profile.",
        not_affected=["Saved passwords", "Bookmarks", "Browsing history",
                      "Logins to sites (cookies). You will not need to sign in again to Gmail, Facebook, etc.",
                      "Extensions and their settings", "Open tabs and profiles", "Autofill and addresses", "Chrome settings"],
        after=["Sites will load slightly slower on the first visit, until the cache is rebuilt (a few seconds).",
               "If Chrome is open, files it is using are skipped. For a full clean, close Chrome first."],
        undo="No need. The cache rebuilds itself as you browse.",
    ),
    "edge_cache": dict(
        title="Microsoft Edge cache",
        what="Copies of files from sites you visited in Edge.",
        if_deleted="Safe. Passwords, favorites, history and logins are not deleted.",
        how="Close Edge and click \"Clean\".",
        verdict="Nothing will break.",
        details="Same as the Chrome cache, but for Edge. Only the cache folders are deleted.",
        not_affected=["Passwords", "Favorites", "History", "Logins to sites", "Extensions and settings"],
        after=["Sites will load slightly slower on the first visit."],
        undo="No need.",
    ),
    "firefox_cache": dict(
        title="Firefox cache",
        what="Copies of files from sites you visited in Firefox.",
        if_deleted="Safe. Passwords, history and bookmarks are not deleted.",
        how="Close Firefox and click \"Clean\".",
        verdict="Nothing will break.",
        details="The Firefox cache. Only the cache2 folder is deleted.",
        not_affected=["Passwords", "Bookmarks", "History", "Logins to sites", "Add-ons"],
        after=["Sites will load slightly slower on the first visit."],
        undo="No need.",
    ),
    "browser_sw": dict(
        title="Offline site data (Service Workers)",
        what="Data that sites and web apps (for example WhatsApp Web, Gmail, Google Docs) keep so they work fast or offline.",
        if_deleted="Nothing important that is not also in the cloud is deleted, but sites like WhatsApp Web may re-sync "
                   "and load slowly next time. Rarely, you may need to sign in to a site again.",
        how="Close the browser and click \"Clean\". Worth it only if the folder is very large (several GB).",
        verdict="Nothing important breaks, but some sites will load slowly the first time.",
        details="Modern sites (WhatsApp Web, Gmail, YouTube, Google Docs) keep a copy of their app on your PC so they open fast, even offline. "
                "This is called a Service Worker. The tool deletes only these copies (CacheStorage). "
                "Your messages, emails and documents live on the sites' servers, not here.",
        not_affected=["Logins to sites (cookies). WhatsApp Web stays signed in", "Passwords, bookmarks and history",
                      "Messages, emails and documents (stored in the cloud)"],
        after=["Sites like WhatsApp Web and Gmail will load slower the first time, then return to normal speed.",
               "A site you used offline will need internet the next time it opens."],
        undo="No need. Sites store the copy again on your next visit.",
    ),
    # -------------------------------------------------------------------- apps
    "capcut_old": dict(
        title="Old CapCut versions",
        what="CapCut updates often and leaves every previous version installed. Each version takes about 1.5 GB.",
        if_deleted="Safe. The newest version stays and is the one that opens. Your projects are not stored in these folders.",
        how="Close CapCut and click \"Clean\".",
        verdict="Nothing will break. CapCut keeps working with the newest version.",
        details="With every update, CapCut installs the new version in a separate folder and leaves the old one. "
                "Many installed versions pile up, but only the latest is used. The tool deletes every version folder except the newest.",
        not_affected=["Your CapCut projects and drafts", "Videos you exported", "Your CapCut login",
                      "The newest CapCut version, which stays installed and working"],
        after=["Nothing noticeable. CapCut opens from the newest version as always."],
        undo="No need. If something does not open, reinstalling CapCut from its site fixes everything, and projects are kept.",
    ),
    "capcut_cache": dict(
        title="CapCut cache",
        what="Effects, music, filters and previews CapCut downloaded or created.",
        if_deleted="Your projects (drafts) are not deleted. Effects and music you used are downloaded again when you open the project, "
                   "so the first opening is slower.",
        how="Close CapCut and click \"Clean\".",
        verdict="Your projects are safe. Effects and music are downloaded again when needed.",
        details="CapCut downloads effects, filters, transitions, music and stickers from the internet and keeps them here. "
                "Your projects (drafts) are stored in a different folder.",
        not_affected=["Your projects and drafts", "Videos you exported", "Clips and photos you imported", "Your CapCut login"],
        after=["When you open a project that uses a CapCut effect or music, they are downloaded again. This needs internet and takes a few seconds."],
        undo="No need.",
    ),
    "chrome_ai_model": dict(
        title="Chrome on-device AI model",
        what="An AI model (Gemini Nano) Chrome downloads to power features like \"Help me write\" without internet.",
        if_deleted="Those features stop working until Chrome downloads the model again (it does so automatically). "
                   "To keep it from coming back: chrome://flags > Enables optimization guide on device > Disabled.",
        how="Close Chrome and click \"Clean\".",
        verdict="Nothing will break. Chrome downloads the model again if it needs it.",
        details="Chrome downloads a small AI model (Gemini Nano) to power features like \"Help me write\" and smart suggestions without sending data to the cloud.",
        not_affected=["Passwords, bookmarks, history and logins", "Normal browsing"],
        after=["Chrome's on-device AI features will not work until Chrome downloads the model again (automatically, in the background)."],
        undo="No need. Chrome downloads it again on its own.",
    ),
    "adobe_cache": dict(
        title="Adobe media cache (Premiere / After Effects)",
        what="Helper files Premiere and After Effects create for every clip you import (decoded audio, waveforms). "
             "Grows without limit and can reach tens of GB.",
        if_deleted="Safe. Your projects and videos are not affected. When you open a project, Premiere rebuilds the cache "
                   "only for the clips in it, which takes a little time at first.",
        how="Close all Adobe programs and click \"Clean\".",
        verdict="Your projects are safe.",
        details="Premiere and After Effects create helper files for each clip (decoded audio and waveforms) so editing stays smooth.",
        not_affected=["Project files (.prproj / .aep)", "Original videos", "Videos you exported"],
        after=["When you first open a project, Premiere re-processes the clips. This can take a few minutes."],
        undo="No need.",
    ),
    "vscode_cache": dict(
        title="VS Code cache",
        what="Cache, logs and old extension installer files of VS Code.",
        if_deleted="Safe. Your settings, installed extensions and code are not affected.",
        how="Close VS Code for a full clean, and click \"Clean\".",
        verdict="Nothing will break.",
        details="VS Code keeps a cache, logs and installer files of previous extension versions.",
        not_affected=["Your code and projects", "Settings (settings.json) and keyboard shortcuts", "Installed extensions",
                      "Recent files and window layout"],
        after=["The first launch of VS Code will be a few seconds slower."],
        undo="No need.",
    ),
    "chat_apps_cache": dict(
        title="Discord / Slack / Zoom cache",
        what="Images and files these apps saved to show chats faster.",
        if_deleted="Safe. Messages are stored on the servers and downloaded again when you need them.",
        how="Close the apps and click \"Clean\".",
        verdict="Nothing will break.",
        details="Discord, Slack and Zoom keep images and files from chats, and logs.",
        not_affected=["Messages (stored on the servers)", "Your logins to the apps", "Zoom recordings (saved in Documents)"],
        after=["Images in old chats load again from the internet."],
        undo="No need.",
    ),
    # --------------------------------------------------------------------- dev
    "npm_cache": dict(
        title="npm cache",
        what="A copy of every npm package you ever downloaded, so the next install is faster.",
        if_deleted="Safe. Projects are not affected. The next npm install downloads packages from the internet, so it will be slower.",
        how="Click \"Clean\" (equivalent to npm cache clean --force).",
        verdict="No project will break.",
        details="npm keeps a copy of every package you ever downloaded here, plus tools you ran with npx. "
                "Projects do not use this folder directly, because each project has its own node_modules.",
        not_affected=["Your projects and their node_modules folders", "Globally installed packages (npm install -g)", "npm settings"],
        after=["The next npm install downloads packages from the internet, so it will be slower.",
               "npx commands download the tool again on first run."],
        undo="No need. Rebuilt automatically.",
    ),
    "yarn_pip_cache": dict(
        title="pip / Yarn / NuGet cache",
        what="Copies of downloaded code packages.",
        if_deleted="Safe. They are downloaded again when needed.",
        how="Click \"Clean\".",
        verdict="No project will break.",
        details="Copies of Python (pip), Yarn and NuGet packages that were downloaded.",
        not_affected=["Installed Python packages", "Your projects", "Virtual environments (venv)"],
        after=["The next install of a package downloads it from the internet."],
        undo="No need.",
    ),
    "gradle_daemon": dict(
        title="Gradle logs and crash files",
        what="A folder where the Android build process (Gradle daemon) writes logs. When it crashes from lack of memory, "
             "Java saves a crash file (core.*.dmp) of 2-3 GB each time. This can add up to hundreds of GB.",
        if_deleted="Completely safe. These are old logs and crash files only. Your code, projects and Gradle cache are not affected. "
                   "Files from the last 24 hours are skipped, so a running build is not disturbed.",
        how="Click \"Clean\".",
        verdict="Nothing will break. These are only old logs and crash files.",
        details="Gradle is the tool that builds Android apps. It runs a background process (daemon) that writes a log to this folder. "
                "When the process crashes from lack of memory, Java saves a \"snapshot\" of its memory (core.*.dmp) of 2 to 3 GB. "
                "For Android developers these files can pile up into dozens. No program reads them after they are created.",
        not_affected=["The source code of your Android apps", "Android Studio and its settings",
                      "Gradle's package cache (in a different folder, caches)", "Emulators and the SDK",
                      "Files from the last 24 hours (in case a build is running now)"],
        after=["Nothing noticeable. The next build creates a new log."],
        undo="No need.",
    ),
    "gradle_cache": dict(
        title="Gradle cache (Android Studio)",
        what="Libraries and Gradle versions downloaded to build Android apps. Tends to collect old versions.",
        if_deleted="No code is deleted. The next build of every Android project downloads everything again, takes a few minutes and needs internet.",
        how="Close Android Studio and click \"Clean\".",
        verdict="No code will break, but the next build will be slow.",
        details="Code libraries and Gradle versions downloaded to build Android apps, including old versions no project uses anymore.",
        not_affected=["Your source code", "Android Studio", "Emulators and the SDK"],
        after=["The first build of every Android project downloads all libraries again. This can take 5 to 15 minutes and needs internet."],
        undo="No need. Gradle downloads whatever is missing.",
    ),
    "pnpm_store": dict(
        title="pnpm package store",
        what="Every package pnpm ever downloaded is kept here, even if no project uses it anymore.",
        if_deleted="The official command pnpm store prune deletes only packages no project uses. Safe. "
                   "Do not delete the folder by hand: existing projects are linked to it.",
        how="Clicking \"Run\" opens a command window that runs pnpm store prune.",
        verdict="No project will break. The command removes only what is unused.",
        details="pnpm keeps each package once in a central store, and projects link to it. The official command pnpm store prune "
                "checks which packages no project links to anymore, and deletes only those.",
        not_affected=["Every existing project and its node_modules folder", "Packages in use"],
        after=["Nothing noticeable."],
        undo="No need.",
    ),
    "automation_browsers": dict(
        title="Browsers of automation and testing tools",
        what="Copies of Chrome and Firefox that Playwright, Puppeteer and testing tools downloaded, and temporary browser profiles created while debugging.",
        if_deleted="No code is deleted. The next time you run a test or automation script, the tool downloads the browser again "
                   "(for example npx playwright install).",
        how="Click \"Clean\".",
        verdict="Your regular Chrome is not affected. This only touches test browsers.",
        details="Tools like Playwright and Puppeteer download a separate copy of Chrome or Firefox to run automated tests. "
                "Chrome debugging also creates temporary profile folders (chrome-debug-...). These are not the browser you browse with.",
        not_affected=["Your regular Chrome, passwords, bookmarks and history", "Your code and tests"],
        after=["The next time you run Playwright or Puppeteer, it asks to download the browser again (for example npx playwright install).",
               "If you signed in to sites inside the test browser, you will need to sign in there again."],
        undo="Run npx playwright install, or run the tool again. It downloads what it needs.",
    ),
    "android_studio_old": dict(
        title="Data of old Android Studio versions",
        what="Every Android Studio version creates its own settings, cache and log folder. After an update, the old versions' folders stay behind.",
        if_deleted="The newest version's folder is kept. Only data of previous versions is deleted, and the new version already copied their settings.",
        how="Close Android Studio and click \"Clean\".",
        verdict="Your current Android Studio is not affected.",
        details="Every Android Studio version creates a folder with settings, cache and logs. When you update, the new version copies the settings "
                "and the old folder stays. The tool keeps the newest version's folder and deletes only the old ones.",
        not_affected=["The current Android Studio version and its settings", "Your projects", "SDK and emulators"],
        after=["If an old Android Studio version is still installed and you open it, it starts with default settings."],
        undo="No need.",
    ),
    "android_avd": dict(
        title="Android emulators",
        what="Virtual Android devices. Each emulator takes several GB.",
        if_deleted="The emulator and the apps installed in it are deleted. You can create a new emulator any time.",
        how="Android Studio > Device Manager > delete emulators you do not use. Do not delete them by hand from the folder.",
        verdict="Deletes the emulator and everything you installed in it.",
        details="Each emulator is a complete virtual phone.",
        not_affected=["Your app code", "Android Studio"],
        after=["You will need to create a new emulator and install your apps in it again."],
        undo="Device Manager > Create Device.",
    ),
    "android_sdk": dict(
        title="Android SDK (system images and versions)",
        what="Emulator system images, NDK versions and build tools. Old versions stay behind after updates.",
        if_deleted="A project that uses a deleted version will not build until you install it again.",
        how="Android Studio > SDK Manager > check \"Show Package Details\" and remove old versions.",
        verdict="No code will break, but a project that needs a deleted version will not build until you install it again.",
        details="Versions of the Android developer tools.",
        not_affected=["Your app code", "Android Studio"],
        after=["Android Studio offers to download a missing version when you open a project that needs it."],
        undo="SDK Manager > check the version > Apply.",
    ),
    "wsl_docker": dict(
        title="Docker / WSL virtual disks",
        what="A single large file that holds an entire Linux system or all of Docker's images.",
        if_deleted="Deleting it by hand deletes all containers, images and files inside Linux. Do not delete.",
        how="To free space: run docker system prune -a, then in Docker Desktop: Troubleshoot > Clean / Purge data. "
            "The file does not shrink automatically even after deleting things inside it.",
    ),
    # ------------------------------------------------------------------- big
    "hiberfil": dict(
        title="Hibernation file (hiberfil.sys)",
        what="A file where Windows saves the contents of memory for Hibernate and Fast Startup. Its size is about 40% of your RAM.",
        if_deleted="If you turn it off: the Hibernate option disappears, and starting the PC from a full shutdown takes a few seconds longer. "
                   "Regular Sleep keeps working. On a laptop that is often carried around it is less recommended. "
                   "Never delete the file by hand. Windows would recreate it.",
        how="Clicking \"Run\" opens an administrator window that runs powercfg /h off. To restore: powercfg /h on.",
        verdict="No programs or files will break. It only changes how the PC shuts down and starts.",
        details="Windows keeps the contents of memory in hiberfil.sys for two modes: Hibernate, where the PC powers off completely "
                "and returns exactly where it was, and Fast Startup, which shortens boot time. "
                "The command powercfg /h off turns both off, and Windows deletes the file itself.",
        not_affected=[PERSONAL, PROGRAMS, "Regular Sleep: closing the lid keeps working as usual",
                      "Normal shut down and restart"],
        after=["Starting the PC from a full shutdown will take a few seconds longer (no Fast Startup). Restart is unchanged.",
               "The \"Hibernate\" option disappears from the power menu.",
               "If the battery drains completely while the PC is asleep, unsaved work is lost (with Hibernate it would be saved). "
               "On a PC that is usually plugged in, this is almost irrelevant."],
        undo="Open a command window as administrator and type powercfg /h on. Everything goes back to how it was.",
    ),
    "pagefile": dict(
        title="Virtual memory file (pagefile.sys)",
        what="When RAM fills up, Windows moves parts of it here. Its size is set automatically based on load.",
        if_deleted="Do not delete or disable it. Without it, programs crash when memory fills up. "
                   "If the file is very large, memory is filling up often (for example many browser tabs). "
                   "The fix is to reduce the load, not to delete the file.",
        how="No action needed. See the \"Why is my PC slow\" report about memory usage.",
        verdict="Do not touch.",
        details="When RAM fills up, Windows moves parts of it here. Without this file, programs crash when memory is full.",
    ),
    "winsxs": dict(
        title="Old Windows components (WinSxS)",
        what="A folder where Windows keeps previous versions of system components after updates, so updates can be uninstalled.",
        if_deleted="Never delete the folder by hand: it breaks Windows. Microsoft's official tool (DISM) safely removes only versions "
                   "that are no longer used. The size shown in Explorer is misleading, because most files are shared with the Windows folder.",
        how="Clicking \"Run\" opens an administrator window that runs DISM. It takes 5 to 20 minutes. Do not close the window midway.",
        verdict="Nothing will break. This is Microsoft's official tool for this cleanup.",
        details="Windows keeps previous versions of system components after each update. The command DISM /StartComponentCleanup deletes only "
                "versions that were replaced by a newer one more than 30 days ago. Windows does exactly this on its own from time to time in a scheduled task.",
        not_affected=[PERSONAL, PROGRAMS, "Windows and installed updates",
                      "The ability to uninstall the latest update (the command does not use /ResetBase)"],
        after=["You cannot roll system components back to versions replaced more than a month ago. You almost never need that."],
        undo="No need.",
    ),
    "restore_points": dict(
        title="System restore points",
        what="Backups of system files Windows creates before installs and updates. Stored in a hidden folder (System Volume Information).",
        if_deleted="Deleting old points is safe. Keep at least the latest, in case an update breaks something.",
        how="In the window that opens: choose drive C > Configure > you can lower \"Max Usage\" to 3%-5%, or click \"Delete\".",
        verdict="Deleting old points does not break anything.",
        details="A restore point is a backup of system files and settings that lets you return Windows to an earlier date after a problem.",
        not_affected=[PERSONAL + " (restore points never backed them up anyway)", PROGRAMS],
        after=["You cannot return the system to the dates of the deleted points."],
        undo="Deleted points cannot be restored. You can create a new point in the same window.",
    ),
    "win_installer": dict(
        title="Windows installer cache (Windows\\Installer)",
        what="Files installed programs need in order to update, repair or uninstall themselves.",
        if_deleted="Do not delete. Afterwards some programs (for example Office) cannot be updated or uninstalled, and fixing it is very hard.",
        how="No action. If the folder is huge, uninstalling programs you do not use will shrink it.",
    ),
}

# ---------------------------------------------------------------- file hints
EXT_HINTS = {
    ".iso": ("Disk image, usually for installing an OS or a program. If you already installed it, you can delete it and download again when needed."),
    ".exe": "Installer. If the program is already installed, you can usually delete it and download it again from the vendor's site.",
    ".zip": "Compressed archive. Check whether you already extracted it. If so, the archive is redundant.",
    ".mp4": "Video. Personal content: do not delete without watching or backing it up (for example to the cloud or an external drive).",
    ".vhdx": "Virtual machine disk (Docker / WSL / VirtualBox). Do not delete it by hand if you use it.",
    ".log": "Log file. Almost always safe to delete.",
    ".dmp": "Crash dump. Safe to delete, unless a technician asked for it.",
    ".tmp": "Temporary or backup file. Usually safe to delete, check the name first.",
    ".psd": "Project file of a design or editing program. Personal content.",
    ".apk": "Built Android app. If you have the source code, you can build it again.",
    ".pst": "Outlook mailbox. Do not delete.",
    ".db": "A program's database. Do not delete without knowing which program it belongs to.",
    ".wav": "Audio file. Personal content.",
    ".jpg": "Photo. Personal content.",
}
DOWNLOADS_NOTE = " The file is in your Downloads folder, where files you no longer need usually sit."
SYSTEM_FILE = "System file. Do not delete by hand. The full explanation is in the \"What can I delete\" tab."
PROGRAM_FILE = "A Windows or installed program file. Do not delete by hand. If the program is unused, uninstall it via Settings > Apps."
APPDATA_PREFIX = "A program file, inside AppData. "
APPDATA_UNKNOWN = "Do not delete without knowing which program it belongs to. If the program is unused, uninstall it instead of deleting files."
UNKNOWN_FILE = "Unrecognized file. Open its location and check what it is before deleting."
DOWNLOADS_DIR = "A folder inside Downloads. Check its contents before deleting."

FOLDER_HINTS = {
    "windows": "The operating system. Do not touch.",
    "program files": "Installed programs. To remove: Settings > Apps.",
    "program files (x86)": "Installed programs (32-bit). To remove: Settings > Apps.",
    "programdata": "Shared program data. Do not delete by hand.",
    "users": "User folders: documents, downloads, desktop and program settings.",
    "$recycle.bin": "The Recycle Bin. You can empty it in the \"What can I delete\" tab.",
    "system volume information": "Restore points. Managed via System Protection settings.",
    "xboxgames": "Xbox games. To remove a game: Settings > Apps or the Xbox app.",
    "home": "Your user folder.",
    "appdata": "Program settings and caches. Most caches this tool can clean live here.",
    "downloads": "Downloads. There are usually many files here you can delete.",
    "onedrive": "Files synced to OneDrive. Free up space with right-click > \"Free up space\" (files stay in the cloud).",
    "node_modules": "Packages of a Node.js project. Can be deleted and restored with npm install.",
    ".gradle": "Android build cache.",
    "build": "Build output of a code project. Usually safe to delete and rebuild.",
    "rule": "{title}: {safety}. Details in the \"What can I delete\" tab.",
}
