MO2 File Explorer
=================
Version 1.0.0

A Mod Organizer 2 plugin: a search box beside the profile selector that finds mods, plugins and
files inside mods, lists them in a dropdown with tick-box filters, and scrolls the mod list to
whatever you pick.

THIS IS NOT A MOD. Do not install it with the mod manager.

REQUIREMENTS
------------
Mod Organizer 2 2.5.x (tested on 2.5.2).

INSTALLATION
------------
Copy plugins\MO2FileExplorer.py into your MO2 folder's "plugins" folder, next to the other .py
plugins, and restart MO2. The box appears between the profile selector and the tool buttons.
To remove it, delete the file.

USE
---
- Type. Every word must appear (any order, any case) in a mod name, a plugin file name or a file's
  path inside its mod. Results: mods first, then plugins, then files, up to 300.
- Tick boxes at the top of the dropdown: Mods / Plugins / Files (kinds), Enabled / Disabled (which
  mods count), Separators (list them too).
- Click a result, or Enter for the first one, or Down into the list and Enter: the mod list scrolls
  to that mod, selected, with its separator expanded; a plugin pick also selects it on the right.
- Escape or a click elsewhere closes the dropdown.
- Files are indexed in the background a couple of seconds after start-up and after every refresh;
  the dropdown says "indexing files..." until then.

DEBUGGING
---------
<your MO2 folder>\plugins\data\mo2-file-explorer.log - send it with any bug report.

LICENCE
-------
GPL-3.0-or-later. Copyright (C) 2026 ApocryphaRealm. See LICENSE and NOTICE.md.
Source: https://github.com/ApocryphaRealm/MO2FileExplorer
