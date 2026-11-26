from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                               QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFrame, QAbstractItemView)
from PySide6.QtCore import Qt
from database.queries_hod import get_all_students, delete_student_record


class DelistStudentPage(QWidget):
    """
    UI for removing students (Cascading Delete).
    Instantiated By: HODDashboardUI (create_menu).
    """
    def __init__(self):
        super().__init__()
        self.current_course_id = ""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.card = QFrame()
        self.card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e5e7eb;
            }
        """)
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(25, 25, 25, 25)

        header_layout = QVBoxLayout()
        lbl_title = QLabel("Delist Students")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: 800; color: #ef4444; border: none;")

        lbl_sub = QLabel(
            "Warning: This action will permanently remove the student and all associated grades/attendance/assignment.")
        lbl_sub.setStyleSheet("font-size: 14px; color: #64748b; border: none; margin-bottom: 15px;")

        header_layout.addWidget(lbl_title)
        header_layout.addWidget(lbl_sub)
        card_layout.addLayout(header_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["No.", "Student ID", "Student Name", "Action"])

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(3, 130)

        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(50)

        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)

        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { border: none; font-size: 14px; background-color: white; alternate-background-color: #f8fafc; }
            QHeaderView::section { background-color: #fef2f2; color: #b91c1c; font-weight: 700; border: none; padding: 12px; }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #f1f5f9; color: #334155; }
        """)
        card_layout.addWidget(self.table)

        layout.addWidget(self.card)

    # Populates table with Delist buttons
    # Called By: HODDashboard (Top Course Selector)
    def load_data(self, course_id: str):
        self.current_course_id = course_id
        students = get_all_students(course_id)
        self.table.setRowCount(len(students))
        for i, s in enumerate(students):
            no_item = QTableWidgetItem(str(i + 1))
            no_item.setTextAlignment(Qt.AlignCenter)
            no_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 0, no_item)

            id_item = QTableWidgetItem(str(s['id']))
            id_item.setTextAlignment(Qt.AlignCenter)
            id_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 1, id_item)

            name_item = QTableWidgetItem(str(s['name']))
            name_item.setTextAlignment(Qt.AlignCenter)
            name_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 2, name_item)

            btn = QPushButton("Delist")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedSize(90, 30)

            btn.setStyleSheet("""
                QPushButton {
                    background-color: #ef4444; 
                    color: black; 
                    font-weight: bold; 
                    font-size: 12px;
                    border-radius: 4px; 
                    border: 1px solid #dc2626;
                }
                QPushButton:hover { background-color: #f87171; }
                QPushButton:pressed { background-color: #b91c1c; }
            """)

            btn.clicked.connect(lambda checked, sid=s['id']: self.delete(sid))

            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setAlignment(Qt.AlignCenter)
            layout.addWidget(btn)

            self.table.setCellWidget(i, 3, widget)

    # Confirms and Deletes
    # Called By: 'Delist' Button
    def delete(self, sid):
        msg = QMessageBox(self)
        msg.setWindowTitle("Confirm Deletion")
        msg.setText(f"Are you sure you want to delete student {sid}?\nThis cannot be undone.")
        msg.setIcon(QMessageBox.Question)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setStyleSheet("QMessageBox { background-color: white; color: black; } QLabel { color: black; }")

        confirm = msg.exec()

        if confirm == QMessageBox.Yes:
            if delete_student_record(sid):
                success_msg = QMessageBox(self)
                success_msg.setWindowTitle("Delisted")
                success_msg.setText(f"Student {sid} has been removed.")
                success_msg.setIcon(QMessageBox.Information)
                success_msg.setStyleSheet(
                    "QMessageBox { background-color: white; color: black; } QLabel { color: black; }")
                success_msg.exec()

                self.load_data(self.current_course_id)