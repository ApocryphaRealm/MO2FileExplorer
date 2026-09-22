# MO2 File Explorer - a Mod Organizer 2 plugin (the owner's name for it, 2026-09-22; developed as MO2 Search Bar) that puts a search box in the gap between the profile selector and the
# tool buttons above the mod list. Typing opens a dropdown of results across MODS, PLUGINS (.esp / .esm / .esl) and
# FILES inside mods; picking one scrolls the mod list to that mod (expanding its separator) and, for a plugin, selects
# it in the plugin list too. Tick boxes at the top of the dropdown narrow the results: which kinds to show, enabled or
# disabled mods, and whether separators are listed.
#
# The owner, 2026-09-22: "make a plugin that adds a search bar to the area inbetween the profile selector and the
# toolbar area and theres a drop down box with search results and some quick filters for different things to exclude
# them or include them like the filters we made earlier so some check boxes in the dropdown to narrow search results".
# Inline, always there, with the filters as tick boxes.
#
# HOW IT SEARCHES. Every word typed must appear (any case, any order) in the mod name, the plugin file name or the
# file's path inside its mod. Mods and plugins are indexed at once (a directory listing per mod); files are indexed by a
# background walk of the mods folder that starts when MO2's window is up and again after every refresh, so the first
# file results arrive a few seconds after start-up - the dropdown says "indexing files..." until then. Results are
# capped at 300, mods first, then plugins, then files, each in load-order position.
#
# Nothing is written anywhere but the plugin's log (plugins\data\mo2-file-explorer.log).
#
# Copyright (C) 2026 ApocryphaRealm. GPL-3.0-or-later - see LICENSE and NOTICE.md.

__version__ = "1.0.0"    # issued by version-gate.ps1; never typed by hand

import os
import threading
import time

try:
    from PyQt6.QtCore import QEvent, QModelIndex, QObject, QPoint, Qt, QTimer, pyqtSignal
    from PyQt6.QtWidgets import (
        QAbstractItemView, QApplication, QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QTreeView,
        QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
    )
    _DISPLAY = Qt.ItemDataRole.DisplayRole
    _USER = Qt.ItemDataRole.UserRole
    _HORIZONTAL = Qt.Orientation.Horizontal
    _KEY_ESC, _KEY_DOWN, _KEY_UP, _KEY_RETURN, _KEY_ENTER = (Qt.Key.Key_Escape, Qt.Key.Key_Down, Qt.Key.Key_Up,
                                                            Qt.Key.Key_Return, Qt.Key.Key_Enter)
    _MOUSE_PRESS, _KEY_PRESS = QEvent.Type.MouseButtonPress, QEvent.Type.KeyPress
    _SINGLE = QAbstractItemView.SelectionMode.SingleSelection
    _ROWS = QAbstractItemView.SelectionBehavior.SelectRows
    _CENTER = QAbstractItemView.ScrollHint.PositionAtCenter
    _STATE_ACTIVE = None
except ImportError:  # MO2 builds that still ship PyQt5
    from PyQt5.QtCore import QEvent, QModelIndex, QObject, QPoint, Qt, QTimer, pyqtSignal
    from PyQt5.QtWidgets import (
        QAbstractItemView, QApplication, QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QTreeView,
        QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
    )
    _DISPLAY = Qt.DisplayRole
    _USER = Qt.UserRole
    _HORIZONTAL = Qt.Horizontal
    _KEY_ESC, _KEY_DOWN, _KEY_UP, _KEY_RETURN, _KEY_ENTER = Qt.Key_Escape, Qt.Key_Down, Qt.Key_Up, Qt.Key_Return, Qt.Key_Enter
    _MOUSE_PRESS, _KEY_PRESS = QEvent.MouseButtonPress, QEvent.KeyPress
    _SINGLE = QAbstractItemView.SingleSelection
    _ROWS = QAbstractItemView.SelectRows
    _CENTER = QAbstractItemView.PositionAtCenter
    _STATE_ACTIVE = None

import mobase

try:
    _STATE_ACTIVE = int(mobase.ModState.ACTIVE)
except Exception:  # noqa: BLE001 - IModList::ModStates: ACTIVE = 2
    _STATE_ACTIVE = 2

PLUGIN_NAME = "MO2 File Explorer"
PLUGIN_EXT = (".esp", ".esm", ".esl")
MAX_RESULTS = 300
KIND_MOD, KIND_PLUGIN, KIND_FILE, KIND_SEP = "Mod", "Plugin", "File", "Separator"


def _words(text):
    return [w for w in text.lower().split() if w]


def _matches(hay, words):
    return all(w in hay for w in words)


class _FileIndexer(QObject):
    """Walks the mods folder on a worker thread; hands back {mod: [relative path, ...]} when done."""
    done = pyqtSignal(object)

    def __init__(self, mods_dir):
        super().__init__()
        self._mods_dir = mods_dir
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        out = {}
        try:
            for mod in os.listdir(self._mods_dir):
                if self._stop:
                    return
                root = os.path.join(self._mods_dir, mod)
                if not os.path.isdir(root) or mod.endswith("_separator"):
                    continue
                files = []
                for dirpath, _dirs, names in os.walk(root):
                    rel_dir = os.path.relpath(dirpath, root)
                    rel_dir = "" if rel_dir == "." else rel_dir + os.sep
                    for n in names:
                        if n.lower() == "meta.ini" and not rel_dir:
                            continue
                        files.append(rel_dir + n)
                out[mod] = files
        except Exception:  # noqa: BLE001
            pass
        if not self._stop:
            self.done.emit(out)


class MO2FileExplorer(mobase.IPlugin):
    def __init__(self):
        super().__init__()
        self._organizer = None
        self._bar = None

    # ---- IPlugin ------------------------------------------------------------------------------
    def init(self, organizer):
        self._organizer = organizer
        try:
            organizer.onUserInterfaceInitialized(self._on_ui)
        except Exception as exc:  # noqa: BLE001
            self._log(f"could not subscribe to the window being built: {exc!r}")
        return True

    def name(self):
        return PLUGIN_NAME

    def author(self):
        return "ApocryphaRealm"

    def description(self):
        return ("A search box beside the profile selector: mods, plugins and files inside mods, with a results dropdown "
                "and tick-box filters; a pick scrolls the mod list to the mod.")

    def version(self):
        major, minor, patch = (int(x) for x in __version__.split("."))
        return mobase.VersionInfo(major, minor, patch, mobase.ReleaseType.FINAL)

    def requirements(self):
        return []

    def settings(self):
        return []

    def _on_ui(self, window):
        try:
            self._bar = _SearchBar(self, window)
            self._log("search bar added beside the profile selector")
        except Exception as exc:  # noqa: BLE001
            self._log(f"search bar NOT added: {exc!r}")

    def _log(self, msg):
        try:
            path = os.path.join(self._organizer.basePath(), "plugins", "data", "mo2-file-explorer.log")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")
        except Exception:  # noqa: BLE001
            pass


class _SearchBar(QObject):
    """The box in the profile row, its dropdown, the index and the jump."""

    def __init__(self, plugin, window):
        super().__init__()
        self._p = plugin
        self._org = plugin._organizer
        self._window = window
        self._mod_view = window.findChild(QTreeView, "modList")
        self._esp_view = window.findChild(QTreeView, "espList")
        profile_box = window.findChild(QComboBox, "profileBox")
        if profile_box is None or self._mod_view is None:
            raise RuntimeError("profile selector or mod list not found - a different MO2 version?")
        row = self._holding_layout(profile_box.parentWidget().layout() if profile_box.parentWidget() else None, profile_box)
        if row is None:
            raise RuntimeError("the profile row's layout was not found")

        # the box, right after the profile selector, taking the empty space that was there
        self._edit = QLineEdit()
        self._edit.setObjectName("mo2FileExplorerEdit")
        self._edit.setPlaceholderText("Search mods, plugins, files...")
        self._edit.setClearButtonEnabled(True)
        self._edit.setToolTip("Every word must appear in the name (any order). Enter jumps to the first result, "
                              "Down moves into the list, Escape closes.")
        row.insertWidget(row.indexOf(profile_box) + 1, self._edit, 2)

        # the dropdown: a child of the main window, laid over whatever is below the box
        self._popup = QFrame(window)
        self._popup.setObjectName("mo2FileExplorerPopup")
        self._popup.setFrameShape(QFrame.Shape.StyledPanel if hasattr(QFrame, "Shape") else QFrame.StyledPanel)
        self._popup.setAutoFillBackground(True)
        self._popup.hide()
        lay = QVBoxLayout(self._popup)
        lay.setContentsMargins(8, 6, 8, 8)
        filters = QHBoxLayout()
        self._boxes = {}
        for key, label, on in (("mods", "Mods", True), ("plugins", "Plugins", True), ("files", "Files", True),
                               ("enabled", "Enabled", True), ("disabled", "Disabled", True), ("seps", "Separators", False)):
            cb = QCheckBox(label)
            cb.setChecked(on)
            cb.toggled.connect(lambda _on: self._schedule())
            self._boxes[key] = cb
            filters.addWidget(cb)
            if key == "files":
                gap = QLabel("|")
                gap.setStyleSheet("opacity: 0.5")
                filters.addWidget(gap)
        filters.addStretch(1)
        self._status = QLabel("")
        filters.addWidget(self._status)
        lay.addLayout(filters)
        self._tree = QTreeWidget()
        self._tree.setColumnCount(4)
        self._tree.setHeaderLabels(["Kind", "Match", "In mod", "Separator"])
        self._tree.setRootIsDecorated(False)
        self._tree.setUniformRowHeights(True)
        self._tree.setAlternatingRowColors(True)
        self._tree.setSelectionMode(_SINGLE)
        self._tree.setSelectionBehavior(_ROWS)
        self._tree.header().resizeSection(0, 80)
        self._tree.header().resizeSection(1, 420)
        self._tree.header().resizeSection(2, 300)
        self._tree.itemClicked.connect(lambda it, _c: self._jump(it))
        self._tree.itemActivated.connect(lambda it, _c: self._jump(it))
        lay.addWidget(self._tree, 1)

        # timers, keys, clicks outside
        self._timer = QTimer(self._popup)
        self._timer.setSingleShot(True)
        self._timer.setInterval(150)
        self._timer.timeout.connect(self._search)
        self._edit.textChanged.connect(lambda _t: self._schedule())
        self._edit.installEventFilter(self)
        self._tree.installEventFilter(self)
        QApplication.instance().installEventFilter(self)

        # the index
        self._mods = []            # (name, enabled, separator, is_separator)
        self._plugins = []         # (plugin file, mod, separator, enabled)
        self._files = {}           # mod -> [relative path]
        self._files_ready = False
        self._indexer = None
        self._indexer_thread = None
        self._build_index()
        QTimer.singleShot(2500, self._start_file_index)
        try:
            self._org.pluginList().onRefreshed(lambda *a: self._on_refreshed())
        except Exception as exc:  # noqa: BLE001
            self._p._log(f"refresh hook not available: {exc!r}")

    # ---- layout helpers -----------------------------------------------------------------------
    @staticmethod
    def _holding_layout(lay, w):
        if lay is None:
            return None
        if lay.indexOf(w) != -1:
            return lay
        for i in range(lay.count()):
            found = _SearchBar._holding_layout(lay.itemAt(i).layout(), w)
            if found is not None:
                return found
        return None

    # ---- index --------------------------------------------------------------------------------
    def _build_index(self):
        t0 = time.time()
        ml = self._org.modList()
        mods, plugins = [], []
        current_sep = ""
        for n in ml.allModsByProfilePriority():
            if n.endswith("_separator"):
                current_sep = n[: -len("_separator")]
                mods.append((current_sep, True, "", True))
                continue
            try:
                enabled = bool(int(ml.state(n)) & _STATE_ACTIVE)
            except Exception:  # noqa: BLE001
                enabled = False
            mods.append((n, enabled, current_sep, False))
            mod = ml.getMod(n)
            if mod is None:
                continue
            try:
                root = mod.absolutePath()
                for f in os.listdir(root):
                    if f.lower().endswith(PLUGIN_EXT) and os.path.isfile(os.path.join(root, f)):
                        plugins.append((f, n, current_sep, enabled))
            except OSError:
                pass
        self._mods, self._plugins = mods, plugins
        self._mod_meta = {m[0]: m for m in mods}
        self._p._log(f"index: {len(mods)} entries, {len(plugins)} plugins in {time.time() - t0:.2f}s")

    def _start_file_index(self):
        if self._indexer is not None:
            self._indexer.stop()
        self._files_ready = False
        self._indexer = _FileIndexer(self._org.modsPath())
        self._indexer.done.connect(self._files_done)
        t = threading.Thread(target=self._indexer.run, daemon=True, name="MO2FileExplorer-files")
        self._indexer_thread = t
        t.start()
        if self._popup.isVisible():
            self._status.setText("indexing files...")

    def _files_done(self, files):
        self._files = files
        self._files_ready = True
        self._p._log(f"file index: {sum(len(v) for v in files.values())} files in {len(files)} mods")
        if self._popup.isVisible():
            self._schedule()

    def _on_refreshed(self):
        try:
            self._build_index()
            self._start_file_index()
            if self._popup.isVisible():
                self._schedule()
        except Exception as exc:  # noqa: BLE001
            self._p._log(f"re-index after refresh failed: {exc!r}")

    # ---- searching ----------------------------------------------------------------------------
    def _schedule(self):
        self._timer.start()

    def _on(self, key):
        return self._boxes[key].isChecked()

    def _state_ok(self, enabled, is_sep):
        if is_sep:
            return self._on("seps")
        return (enabled and self._on("enabled")) or ((not enabled) and self._on("disabled"))

    def _search(self):
        words = _words(self._edit.text())
        if not words:
            self._hide()
            return
        results = []
        if self._on("mods") or self._on("seps"):
            for name, enabled, sep, is_sep in self._mods:
                if is_sep and not self._on("seps"):
                    continue
                if not is_sep and not self._on("mods"):
                    continue
                if self._state_ok(enabled, is_sep) and _matches(name.lower(), words):
                    results.append((KIND_SEP if is_sep else KIND_MOD, name, "" if is_sep else name, sep, name))
                    if len(results) >= MAX_RESULTS:
                        break
        if self._on("plugins") and len(results) < MAX_RESULTS:
            for f, mod, sep, enabled in self._plugins:
                if self._state_ok(enabled, False) and _matches(f.lower(), words):
                    results.append((KIND_PLUGIN, f, mod, sep, mod))
                    if len(results) >= MAX_RESULTS:
                        break
        if self._on("files") and len(results) < MAX_RESULTS:
            if self._files_ready:
                for mod, files in self._files.items():
                    meta = self._mod_meta.get(mod)
                    if meta is None or not self._state_ok(meta[1], False):
                        continue
                    for rel in files:
                        if _matches(rel.lower(), words):
                            results.append((KIND_FILE, rel, mod, meta[2], mod))
                            if len(results) >= MAX_RESULTS:
                                break
                    if len(results) >= MAX_RESULTS:
                        break
        self._tree.clear()
        for kind, match, mod, sep, target in results:
            it = QTreeWidgetItem([kind, match, mod, sep])
            it.setData(0, _USER, (kind, match, target))
            it.setToolTip(1, match)
            self._tree.addTopLevelItem(it)
        note = "" if self._files_ready or not self._on("files") else "  (indexing files...)"
        capped = "+" if len(results) >= MAX_RESULTS else ""
        self._status.setText(f"{len(results)}{capped} result(s){note}")
        self._show()

    # ---- showing / hiding ---------------------------------------------------------------------
    def _show(self):
        top_left = self._edit.mapTo(self._window, QPoint(0, self._edit.height()))
        width = max(self._edit.width(), 900)
        width = min(width, self._window.width() - top_left.x() - 12)
        height = min(560, self._window.height() - top_left.y() - 12)
        self._popup.setGeometry(top_left.x(), top_left.y() + 2, width, height)
        self._popup.raise_()
        self._popup.show()

    def _hide(self):
        self._popup.hide()

    # ---- the jump -----------------------------------------------------------------------------
    def _jump(self, it):
        data = it.data(0, _USER)
        if not data:
            return
        kind, match, target = data
        found = self._select_mod(target)
        if kind == KIND_PLUGIN:
            self._select_plugin(match)
        self._p._log(f"jump: {kind} {match!r} -> mod {target!r} {'found' if found else 'NOT visible in the list'}")
        self._hide()
        self._edit.setFocus()

    def _name_column(self, model):
        for c in range(model.columnCount()):
            h = model.headerData(c, _HORIZONTAL, _DISPLAY)
            if h and str(h).strip().lower() in ("mod name", "name"):
                return c
        return 0

    def _find_row(self, view, text, col):
        model = view.model()
        if model is None:
            return None
        want = text.lower()

        def walk(parent):
            for r in range(model.rowCount(parent)):
                idx = model.index(r, col, parent)
                if str(idx.data(_DISPLAY) or "").strip().lower() == want:
                    return idx
                idx0 = model.index(r, 0, parent)
                if model.hasChildren(idx0):
                    hit = walk(idx0)
                    if hit is not None:
                        return hit
            return None
        return walk(QModelIndex())

    def _select_mod(self, name):
        view = self._mod_view
        idx = self._find_row(view, name, self._name_column(view.model()))
        if idx is None:
            return False
        parent = idx.parent()
        if parent.isValid():
            view.expand(parent)
        view.scrollTo(idx, _CENTER)
        view.setCurrentIndex(idx)
        try:
            view.selectionModel().select(idx, view.selectionModel().SelectionFlag.ClearAndSelect | view.selectionModel().SelectionFlag.Rows)
        except Exception:  # noqa: BLE001
            pass
        return True

    def _select_plugin(self, plugin):
        view = self._esp_view
        if view is None or view.model() is None:
            return False
        idx = self._find_row(view, plugin, self._name_column(view.model()))
        if idx is None:
            return False
        view.scrollTo(idx, _CENTER)
        view.setCurrentIndex(idx)
        return True

    # ---- keys and clicks ----------------------------------------------------------------------
    def eventFilter(self, obj, ev):
        try:
            et = ev.type()
            if et == _KEY_PRESS and obj is self._edit:
                k = ev.key()
                if k == _KEY_ESC:
                    self._hide()
                    return True
                if k == _KEY_DOWN and self._popup.isVisible() and self._tree.topLevelItemCount():
                    self._tree.setFocus()
                    self._tree.setCurrentItem(self._tree.topLevelItem(0))
                    return True
                if k in (_KEY_RETURN, _KEY_ENTER):
                    if not self._popup.isVisible():
                        self._search()
                    if self._tree.topLevelItemCount():
                        self._jump(self._tree.currentItem() or self._tree.topLevelItem(0))
                    return True
            elif et == _KEY_PRESS and obj is self._tree:
                k = ev.key()
                if k == _KEY_ESC:
                    self._hide()
                    self._edit.setFocus()
                    return True
                if k in (_KEY_RETURN, _KEY_ENTER) and self._tree.currentItem() is not None:
                    self._jump(self._tree.currentItem())
                    return True
                if k == _KEY_UP and self._tree.currentIndex().row() == 0:
                    self._edit.setFocus()
                    return True
            elif et == _MOUSE_PRESS and self._popup.isVisible() and isinstance(obj, QWidget):
                w = obj
                inside = False
                while w is not None:
                    if w is self._popup or w is self._edit:
                        inside = True
                        break
                    w = w.parentWidget()
                if not inside:
                    self._hide()
        except Exception:  # noqa: BLE001
            pass
        return False


def createPlugin():
    return MO2FileExplorer()
