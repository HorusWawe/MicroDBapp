"""
Authors : me? Im Alone
"""
import sys
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from microdb import Storage


class MicroDBApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = None
        self.current_collection = None
        self.current_collection_name = None
        self.data_path = "data.json"
        self._row_id_map = []
        self.init_ui()
        self.load_database()

    def init_ui(self):
        self.setWindowTitle("MicroDB Studio")
        self.setGeometry(100, 100, 1200, 700)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
                font-family: 'Segoe UI', sans-serif;
            }
            QTableWidget {
                background-color: #252525;
                border: 1px solid #333333;
                border-radius: 6px;
                gridline-color: #333333;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #ffffff
                color: white;
            }
            QHeaderView::section {
                background-color: #ffffff
                padding: 8px;
                border: none;
                font-weight: 600;
            }
            QLineEdit {
                background-color: #2a2a2a;
                border: 8 solid #ffffff
                border-radius: 4px;
                padding: 6px 10px;
                color: white;
            }
            QLineEdit:focus {
                border-color: #ffffff;
            }
            QPushButton {
                background-color: #2a2a2a;
                border: 1px solid #ffffff
                border-radius: 4px;
                padding: 6px 14px;
                color: white;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton#primary {
                background-color: #4a9eff;
                border: none;
            }
            QPushButton#primary:hover {
                background-color: #3a7ac8;
            }
            QPushButton#danger {
                background-color: #c0392b;
                border: none;
            }
            QPushButton#danger:hover {
                background-color: #a93226;
            }
            QPushButton#success {
                background-color: #27ae60;
                border: none;
            }
            QPushButton#success:hover {
                background-color: #2ecc71;
            }
            QListWidget {
                background-color: #252525;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-radius: 4px;
                border: none;
            }
            QListWidget::item:selected {
                background-color: #3a6ea5;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #2a2a2a;
            }
            QLabel#title {
                font-size: 22px;
                font-weight: bold;
                color: white;
            }
            QLabel#subtitle {
                color: #888888;
                font-size: 13px;
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        sidebar = self.create_sidebar()
        layout.addWidget(sidebar)

        right = self.create_main_area()
        layout.addWidget(right)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.setStyleSheet("background-color: #1a1a1a; color: #888888; padding: 4px;")

    def create_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(260)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title = QLabel("MicroDB")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("Simple JSON Database")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        layout.addSpacing(15)

        self.file_label = QLabel(f"File: {self.data_path}")
        self.file_label.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(self.file_label)

        layout.addSpacing(10)

        coll_layout = QHBoxLayout()
        self.new_coll_input = QLineEdit()
        self.new_coll_input.setPlaceholderText("Collection name")
        coll_layout.addWidget(self.new_coll_input)

        add_btn = QPushButton("+")
        add_btn.setObjectName("primary")
        add_btn.setFixedWidth(36)
        add_btn.clicked.connect(self.create_collection)
        coll_layout.addWidget(add_btn)

        layout.addLayout(coll_layout)

        label = QLabel("Collections")
        label.setStyleSheet("color: #888888; font-size: 12px; margin-top: 8px;")
        layout.addWidget(label)

        self.collections_list = QListWidget()
        self.collections_list.itemClicked.connect(self.load_collection)
        layout.addWidget(self.collections_list)

        layout.addStretch()

        return sidebar

    def create_main_area(self):
        right = QWidget()
        layout = QVBoxLayout(right)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        toolbar = QWidget()
        toolbar.setStyleSheet("background-color: #252525; border-radius: 6px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 8, 12, 8)

        self.collection_title = QLabel("No collection selected")
        self.collection_title.setStyleSheet("font-size: 15px; font-weight: 600;")
        toolbar_layout.addWidget(self.collection_title)

        toolbar_layout.addStretch()

        add_row_btn = QPushButton("Add Row")
        add_row_btn.setObjectName("primary")
        add_row_btn.clicked.connect(self.add_row)
        toolbar_layout.addWidget(add_row_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.setObjectName("primary")
        edit_btn.clicked.connect(self.edit_row)
        toolbar_layout.addWidget(edit_btn)

        delete_row_btn = QPushButton("Delete")
        delete_row_btn.setObjectName("danger")
        delete_row_btn.clicked.connect(self.delete_row)
        toolbar_layout.addWidget(delete_row_btn)

        save_btn = QPushButton("Save")
        save_btn.setObjectName("success")
        save_btn.clicked.connect(self.save_changes)
        toolbar_layout.addWidget(save_btn)

        layout.addWidget(toolbar)

        self.table = QTableWidget()
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        return right

    def load_database(self):
        try:
            self.db = Storage(self.data_path)
            self.refresh_collections()
            self.status_bar.showMessage(f"Loaded: {self.data_path}")
        except Exception as e:
            self.status_bar.showMessage(f"Error loading: {e}")

    def refresh_collections(self):
        self.collections_list.clear()
        if self.db:
            for name in self.db._cache.keys():
                self.collections_list.addItem(name)

    def create_collection(self):
        name = self.new_coll_input.text().strip()
        if not name:
            return

        if self.db and name in self.db._cache:
            self.status_bar.showMessage(f"Collection '{name}' already exists")
            return

        try:
            self.db.create_collection(name)
            self.new_coll_input.clear()
            self.refresh_collections()
            self.status_bar.showMessage(f"Created: {name}")
        except Exception as e:
            self.status_bar.showMessage(f"Error: {e}")

    def load_collection(self, item):
        try:
            name = item.text()
            self.current_collection_name = name
            self.current_collection = getattr(self.db, name)
            self.collection_title.setText(name)
            self._row_id_map = []
            self.refresh_table()
            self.status_bar.showMessage(f"Loaded: {name}")
        except Exception as e:
            self.status_bar.showMessage(f"Error: {e}")

    def refresh_table(self):
        if not self.current_collection:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            self._row_id_map = []
            return

        data = self.current_collection.all()
        if not data:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            self._row_id_map = []
            return

        keys = set()
        for row in data:
            keys.update(row.keys())
        keys = sorted(keys)

        self.table.setColumnCount(len(keys))
        self.table.setHorizontalHeaderLabels(keys)
        self.table.setRowCount(len(data))

        self._row_id_map = []
        for i, row in enumerate(data):
            self._row_id_map.append(row.get("id"))
            for j, key in enumerate(keys):
                value = row.get(key, "")
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(i, j, item)

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

    def add_row(self):
        if not self.current_collection:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Add Row")
        dialog.setModal(True)
        dialog.setStyleSheet("""
            QDialog { background-color: #2a2a2a; }
            QLabel { color: white; }
            QLineEdit {
                background-color: #1a1a1a;
                border: none;
                border-bottom: 1px solid #3a3a3a;
                padding: 6px 10px;
                color: white;
            }
            QLineEdit:focus {
                border-bottom: 1px solid #4a9eff;
            }
            QPushButton {
                background-color: #3a3a3a;
                border-radius: 4px;
                padding: 6px 14px;
                color: white;
            }
            QPushButton:hover { background-color: #4a4a4a; }
            QPushButton#primary { background-color: #4a9eff; }
            QPushButton#primary:hover { background-color: #3a7ac8; }
        """)

        dialog.setLayout(QVBoxLayout())
        dialog.setFixedWidth(380)

        data = self.current_collection.all()
        keys = set()
        for row in data:
            keys.update(row.keys())
        if not keys:
            keys = {"id", "name", "value"}

        fields = {}
        for key in sorted(keys):
            if key == "id":
                continue
            lbl = QLabel(key)
            dialog.layout().addWidget(lbl)
            inp = QLineEdit()
            inp.setPlaceholderText(key)
            dialog.layout().addWidget(inp)
            fields[key] = inp

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Add")
        ok_btn.setObjectName("primary")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        dialog.layout().addLayout(btn_layout)

        def on_add():
            try:
                new_row = {}
                for key, inp in fields.items():
                    val = inp.text().strip()
                    if val:
                        if val.isdigit():
                            new_row[key] = int(val)
                        elif val.lower() in ("true", "false"):
                            new_row[key] = val.lower() == "true"
                        else:
                            new_row[key] = val
                self.current_collection.insert(new_row)
                self.refresh_table()
                self.status_bar.showMessage("Row added")
                dialog.accept()
            except Exception as e:
                self.status_bar.showMessage(f"Error: {e}")

        ok_btn.clicked.connect(on_add)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec()

    def edit_row(self):
        if not self.current_collection:
            return

        row = self.table.currentRow()
        if row < 0 or row >= len(self._row_id_map):
            self.status_bar.showMessage("No row selected")
            return

        row_id = self._row_id_map[row]
        if row_id is None:
            self.status_bar.showMessage("Row has no ID")
            return

        data = self.current_collection.find_one(id=row_id)
        if not data:
            self.status_bar.showMessage("Row not found")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Row")
        dialog.setModal(True)
        dialog.setStyleSheet("""
            QDialog { background-color: #2a2a2a; }
            QLabel { color: white; }
            QLineEdit {
                background-color: #1a1a1a;
                border: none;
                border-bottom: 1px solid #3a3a3a;
                padding: 6px 10px;
                color: white;
            }
            QLineEdit:focus {
                border-bottom: 1px solid #4a9eff;
            }
            QPushButton {
                background-color: #3a3a3a;
                border-radius: 4px;
                padding: 6px 14px;
                color: white;
            }
            QPushButton:hover { background-color: #4a4a4a; }
            QPushButton#primary { background-color: #4a9eff; }
            QPushButton#primary:hover { background-color: #3a7ac8; }
        """)

        dialog.setLayout(QVBoxLayout())
        dialog.setFixedWidth(380)

        fields = {}
        for key, value in data.items():
            lbl = QLabel(key)
            dialog.layout().addWidget(lbl)
            inp = QLineEdit()
            inp.setText(str(value))
            dialog.layout().addWidget(inp)
            fields[key] = inp

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Save")
        ok_btn.setObjectName("primary")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        dialog.layout().addLayout(btn_layout)

        def on_save():
            try:
                new_data = {}
                for key, inp in fields.items():
                    val = inp.text().strip()
                    if key == "id":
                        if val.isdigit():
                            new_data[key] = int(val)
                    else:
                        if val.isdigit():
                            new_data[key] = int(val)
                        elif val.lower() in ("true", "false"):
                            new_data[key] = val.lower() == "true"
                        else:
                            new_data[key] = val
                self.current_collection.update(where={"id": row_id}, set_data=new_data)
                self.refresh_table()
                self.status_bar.showMessage("Row updated")
                dialog.accept()
            except Exception as e:
                self.status_bar.showMessage(f"Error: {e}")

        ok_btn.clicked.connect(on_save)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec()

    def delete_row(self):
        if not self.current_collection:
            return

        row = self.table.currentRow()
        if row < 0 or row >= len(self._row_id_map):
            self.status_bar.showMessage("No row selected")
            return

        row_id = self._row_id_map[row]
        if row_id is None:
            self.status_bar.showMessage("Row has no ID")
            return

        reply = QMessageBox.question(
            self,
            "Delete Row",
            f"Delete row with ID {row_id}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.current_collection.delete(id=row_id)
                self.refresh_table()
                self.status_bar.showMessage(f"Deleted row {row_id}")
            except Exception as e:
                self.status_bar.showMessage(f"Error: {e}")

    def save_changes(self):
        if not self.current_collection:
            return

        try:
            rows = self.table.rowCount()
            cols = self.table.columnCount()
            if cols == 0:
                return

            current_ids = [row.get("id") for row in self.current_collection.all() if row.get("id") is not None]
            updated_ids = []

            for i in range(rows):
                row_data = {}
                for j in range(cols):
                    item = self.table.item(i, j)
                    if item:
                        key = self.table.horizontalHeaderItem(j).text()
                        val = item.text().strip()
                        if key == "id":
                            if val.isdigit():
                                row_data["id"] = int(val)
                            else:
                                row_data["id"] = None
                        else:
                            if val.isdigit():
                                row_data[key] = int(val)
                            elif val.lower() in ("true", "false"):
                                row_data[key] = val.lower() == "true"
                            else:
                                row_data[key] = val

                row_id = row_data.get("id")
                if row_id is not None and row_id in current_ids:
                    self.current_collection.update(where={"id": row_id}, set_data=row_data)
                    updated_ids.append(row_id)
                else:
                    if "id" in row_data:
                        del row_data["id"]
                    self.current_collection.insert(row_data)

            for doc_id in current_ids:
                if doc_id not in updated_ids:
                    self.current_collection.delete(id=doc_id)

            self.refresh_table()
            self.status_bar.showMessage("Saved")
        except Exception as e:
            self.status_bar.showMessage(f"Error saving: {e}")

    def closeEvent(self, event):
        if self.current_collection:
            self.save_changes()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MicroDBApp()
    window.show()
    sys.exit(app.exec())