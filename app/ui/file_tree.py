"""Tree view of the files inside an archive (name, size, date, type)."""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTreeWidget, QTreeWidgetItem

from app.engine.models import ArchiveEntry
from app.ui.icons import icon_for, type_label
from app.utils import human_size

COL_NAME, COL_SIZE, COL_MODIFIED, COL_TYPE = range(4)


class EntryItem(QTreeWidgetItem):
    """One row. Folders always sort before files; sizes sort as numbers."""

    def __init__(self, path: str, is_dir: bool, size: int = 0,
                 modified: str = "", encrypted: bool = False) -> None:
        super().__init__()
        self.path = path
        self.is_dir = is_dir
        self.size = size
        name = path.rsplit("/", 1)[-1]
        self.setText(COL_NAME, name)
        self.setIcon(COL_NAME, icon_for(name, is_dir))
        self.setText(COL_MODIFIED, modified)
        kind = type_label(name, is_dir)
        self.setText(COL_TYPE, f"{kind}  🔒" if encrypted else kind)
        self.setTextAlignment(COL_SIZE, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.setToolTip(COL_NAME, path)

    def set_size(self, size: int) -> None:
        self.size = size
        self.setText(COL_SIZE, human_size(size))

    def __lt__(self, other: "EntryItem") -> bool:  # used by Qt when sorting
        tree = self.treeWidget()
        ascending = tree.header().sortIndicatorOrder() == Qt.SortOrder.AscendingOrder
        if self.is_dir != other.is_dir:
            return self.is_dir if ascending else other.is_dir
        column = tree.sortColumn()
        if column == COL_SIZE:
            return self.size < other.size
        return self.text(column).lower() < other.text(column).lower()


class ArchiveTree(QTreeWidget):
    open_requested = Signal(str)   # double-clicked file (path inside archive)

    def __init__(self) -> None:
        super().__init__()
        self.setColumnCount(4)
        self.setHeaderLabels(["Name", "Size", "Modified", "Type"])
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setUniformRowHeights(True)
        self.setIconSize(QSize(22, 22))
        self.setAnimated(True)
        header = self.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(COL_NAME, QHeaderView.ResizeMode.Stretch)
        for col, width in ((COL_SIZE, 90), (COL_MODIFIED, 140), (COL_TYPE, 150)):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
            self.setColumnWidth(col, width)
        self.itemDoubleClicked.connect(self._on_double_click)
        self._items: dict[str, EntryItem] = {}

    # --- filling -------------------------------------------------------------
    def show_entries(self, entries: list[ArchiveEntry]) -> None:
        """Build the folder tree. Missing parent folders are created too."""
        self.setUpdatesEnabled(False)
        self.setSortingEnabled(False)
        self.clear()
        self._items = {}
        for entry in entries:
            item = self._ensure(entry.path, entry.is_dir)
            if not entry.is_dir:
                item.set_size(entry.size)
                item.setText(COL_MODIFIED, entry.modified)
                if entry.encrypted:
                    item.setText(COL_TYPE, f"{type_label(entry.name)}  🔒")
            elif entry.modified:
                item.setText(COL_MODIFIED, entry.modified)
        for index in range(self.topLevelItemCount()):
            self._sum_sizes(self.topLevelItem(index))
        self.setSortingEnabled(True)
        self.sortByColumn(COL_NAME, Qt.SortOrder.AscendingOrder)
        if self.topLevelItemCount() == 1:      # single root folder: open it
            self.topLevelItem(0).setExpanded(True)
        self.setUpdatesEnabled(True)

    def _ensure(self, path: str, is_dir: bool) -> EntryItem:
        if path in self._items:
            return self._items[path]
        parent_path, _, _ = path.rpartition("/")
        item = EntryItem(path, is_dir)
        if parent_path:
            self._ensure(parent_path, True).addChild(item)
        else:
            self.addTopLevelItem(item)
        self._items[path] = item
        return item

    def _sum_sizes(self, item: EntryItem) -> int:
        if not item.is_dir:
            return item.size
        total = sum(self._sum_sizes(item.child(i)) for i in range(item.childCount()))
        item.set_size(total)
        return total

    # --- reading the selection -----------------------------------------------
    def selected_paths(self) -> list[str]:
        """Selected paths; a child is skipped if its folder is selected."""
        chosen = {item.path for item in self.selectedItems()}
        return sorted(p for p in chosen
                      if not any(p.startswith(other + "/") for other in chosen))

    # --- search ----------------------------------------------------------------
    def apply_filter(self, text: str) -> None:
        needle = text.strip().lower()
        for index in range(self.topLevelItemCount()):
            self._filter(self.topLevelItem(index), needle)
        if needle:
            self.expandAll()

    def _filter(self, item: EntryItem, needle: str) -> bool:
        child_match = False
        for i in range(item.childCount()):
            child_match = self._filter(item.child(i), needle) or child_match
        visible = not needle or needle in item.text(COL_NAME).lower() or child_match
        item.setHidden(not visible)
        return visible

    def _on_double_click(self, item: EntryItem, _column: int) -> None:
        if not item.is_dir:
            self.open_requested.emit(item.path)
