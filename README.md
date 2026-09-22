# MO2 File Explorer

A Mod Organizer 2 plugin that puts a search box in the gap between the profile selector and the
tool buttons above the mod list. Type, and a dropdown lists matches across **mods**, **plugins**
(.esp / .esm / .esl) and **files inside mods**; pick one and the mod list scrolls to that mod,
selected, with its separator expanded - a plugin pick also selects the plugin in the right-hand list.
Tick boxes along the top of the dropdown narrow the results.

## How it searches

* Every word you type must appear - any order, any case - in the mod name, the plugin file name, or
  the file's path inside its mod. Same rule as MO2's own filter box.
* Mods and plugins are indexed at once (one directory listing per mod). Files are indexed by a
  background walk of the mods folder that starts a couple of seconds after MO2's window is up and
  again after every refresh; until it finishes the dropdown says "indexing files...". On a 2,200-mod
  list that is about 210,000 files in two seconds.
* Up to 300 results: mods first, then plugins, then files, each in load-order position.

## The tick boxes

| Box | Meaning |
|---|---|
| Mods / Plugins / Files | which kinds of result to show (all on by default) |
| Enabled / Disabled | which mods count (both on by default) |
| Separators | list separator names as results too (off by default) |

## Keys

Enter jumps to the first result (or the highlighted one). Down moves from the box into the list;
Up from the first row goes back. Escape closes; so does clicking anywhere else.

## Installation

Copy `plugins\MO2FileExplorer.py` into your MO2 instance's `plugins` folder and restart MO2. To
remove it, delete the file. It writes nothing but its log.

## Requirements

Mod Organizer 2 2.5.x (tested on 2.5.2). A PyQt5 fallback for 2.4 exists but is untested.

## Debugging

`<instance>\plugins\data\mo2-file-explorer.log` - the index sizes, every jump and whether the mod
was reachable (a mod hidden by an active filter cannot be scrolled to; the log says so).

## Licence

GPL-3.0-or-later. Copyright (C) 2026 ApocryphaRealm. See `LICENSE` and `NOTICE.md`.
