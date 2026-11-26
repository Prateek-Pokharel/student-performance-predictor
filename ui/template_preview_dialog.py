from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                               QPushButton, QHBoxLayout, QLabel, QHeaderView, QAbstractItemView)
from PySide6.QtCore import Qt

class TemplatePreviewDialog(QDialog):
    """
    Modal dialog showing CSV structure before download.
    Instantiated By: All 'Download Template' buttons (Teacher & HOD).
    """
    def __init__(self, title, columns, sample_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Template Preview - {title}")
        self.setFixedSize(600, 400)
        self.setStyleSheet("background-color: white;")

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl_info = QLabel("Please ensure your CSV file matches the format below:")
        lbl_info.setStyleSheet("font-size: 14px; font-weight: bold; color: #1e293b;")
        layout.addWidget(lbl_info)

        self.table = QTableWidget()
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.verticalHeader().setVisible(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setStyleSheet("""
            QTableWidget { border: 1px solid #e2e8f0; gridline-color: #f1f5f9; }
            QHeaderView::section { background-color: #f8fafc; color: #64748b; font-weight: bold; border: none; padding: 8px; }
            QTableWidget::item { padding: 5px; color: #334155; }
        """)

        self.table.setRowCount(len(sample_data))
        for i, row in enumerate(sample_data):
            for j, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, j, item)

        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet(
            "padding: 8px 15px; border-radius: 5px; color: #64748b; font-weight: bold; border: 1px solid #cbd5e1;")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_download = QPushButton("Download .csv File")
        self.btn_download.setCursor(Qt.PointingHandCursor)
        self.btn_download.setStyleSheet(
            "background-color: #3b82f6; color: white; padding: 8px 15px; border-radius: 5px; font-weight: bold; border: none;")
        self.btn_download.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_download)

        layout.addLayout(btn_layout)