# Changelog - MO2 File Explorer

Versions are issued by the project's version gate. Written as the change happens (rule 61).

## 1.0.0 - 2026-09-22 - first release

* A search box in the profile row, between the profile selector and the tool buttons.
* A dropdown of results across mods, plugins (.esp / .esm / .esl) and files inside mods - every typed
  word must appear, any order, any case; up to 300 results, mods first, then plugins, then files,
  in load-order position.
* Tick-box filters at the top of the dropdown: Mods / Plugins / Files, Enabled / Disabled, Separators.
* A pick scrolls the mod list to the mod, selects it and expands its separator; a plugin pick also
  selects the plugin in the plugin list. Enter, Down / Up and Escape work from the box.
* Mods and plugins indexed at once; files indexed by a background walk of the mods folder at start-up
  and after every MO2 refresh.
* Log at `plugins\data\mo2-file-explorer.log`. Developed the same night as "MO2 Search Bar"; renamed
  by the owner before release.
