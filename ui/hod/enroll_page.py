from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
                               QFrame, QComboBox, QFileDialog, QAbstractItemView)
from PySide6.QtCore import Qt
from database.queries_hod import get_all_students, insert_new_student, generate_next_student_id, get_all_courses

import os
import pandas as pd
from services.import_service import generate_blank_template, parse_csv_data
from ui.template_preview_dialog import TemplatePreviewDialog


class EnrollStudentPage(QWidget):
    """
    UI for enrolling new students (Manual + Bulk).
    Instantiated By: HODDashboardUI (create_menu).
    """

    def __init__(self):
        super().__init__()
        self.current_course_id = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        self.form_card = QFrame()
        self.form_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e5e7eb;
            }
        """)
        form_layout = QHBoxLayout(self.form_card)
        form_layout.setContentsMargins(25, 25, 25, 25)
        form_layout.setSpacing(20)

        title_layout = QVBoxLayout()
        lbl_title = QLabel("Enroll New Student")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #1e293b; border: none;")
        title_layout.addWidget(lbl_title)

        id_layout = QVBoxLayout()
        lbl_id = QLabel("Student ID")
        lbl_id.setStyleSheet("font-size: 12px; font-weight: bold; color: #64748b; border: none;")
        self.id_input = QLineEdit()
        self.id_input.setReadOnly(True)
        self.id_input.setFixedHeight(38)
        self.id_input.setStyleSheet("""
            background-color: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; 
            border-radius: 6px; padding: 0 10px; font-weight: bold;
        """)
        id_layout.addWidget(lbl_id)
        id_layout.addWidget(self.id_input)

        name_layout = QVBoxLayout()
        lbl_name = QLabel("Full Name")
        lbl_name.setStyleSheet("font-size: 12px; font-weight: bold; color: #64748b; border: none;")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter student name...")
        self.name_input.setFixedHeight(38)
        self.name_input.setStyleSheet("""
            QLineEdit { border: 1px solid #cbd5e1; border-radius: 6px; padding: 0 10px; font-size: 14px; }
            QLineEdit:focus { border: 2px solid #3b82f6; }
        """)
        name_layout.addWidget(lbl_name)
        name_layout.addWidget(self.name_input)

        self.course_combo = QComboBox()
        self.course_combo.setVisible(False)

        # --- BUTTON LAYOUT SETUP ---
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(10)  # Increased spacing slightly for better look

        # 1. Prepare Bulk Import Row (Template & Import Buttons)
        bulk_row = QHBoxLayout()

        btn_temp = QPushButton("📥 Template")
        btn_temp.setCursor(Qt.PointingHandCursor)
        btn_temp.setStyleSheet(
            "background: #64748b; color: white; border-radius: 4px; padding: 5px; font-weight: bold;")
        btn_temp.clicked.connect(self.download_template)

        btn_import = QPushButton("📤 Import CSV")
        btn_import.setCursor(Qt.PointingHandCursor)
        btn_import.setStyleSheet(
            "background: #0ea5e9; color: white; border-radius: 4px; padding: 5px; font-weight: bold;")
        btn_import.clicked.connect(self.import_csv)

        bulk_row.addWidget(btn_temp)
        bulk_row.addWidget(btn_import)

        # 2. Prepare Enroll Button
        self.btn_enroll = QPushButton("Enroll Student")
        self.btn_enroll.setCursor(Qt.PointingHandCursor)
        self.btn_enroll.setFixedHeight(38)
        self.btn_enroll.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6; color: white; font-weight: 700; 
                border-radius: 6px; padding: 0 20px; border: none; font-size: 14px;
            }
            QPushButton:hover { background-color: #2563eb; }
        """)
        self.btn_enroll.clicked.connect(self.enroll)

        # --- FIX: SWAPPED ORDER HERE ---
        # First: Add the Bulk Row (Top)
        btn_layout.addLayout(bulk_row)

        # Second: Add the Enroll Button (Bottom)
        btn_layout.addWidget(self.btn_enroll)

        form_layout.addLayout(id_layout, 1)
        form_layout.addLayout(name_layout, 3)
        form_layout.addLayout(btn_layout, 1)

        layout.addWidget(self.form_card)

        self.table_card = QFrame()
        self.table_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e5e7eb;
            }
        """)
        table_layout = QVBoxLayout(self.table_card)
        table_layout.setContentsMargins(25, 25, 25, 25)

        self.subtitle = QLabel("Currently Enrolled Students")
        self.subtitle.setStyleSheet(
            "font-size: 18px; font-weight: 700; color: #1e293b; border: none; margin-bottom: 15px;")
        table_layout.addWidget(self.subtitle)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["No.", "Student ID", "Student Name"])

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)

        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)

        self.table.setStyleSheet("""
            QTableWidget { border: none; font-size: 14px; background-color: white; alternate-background-color: #f8fafc; }
            QHeaderView::section { background-color: #f1f5f9; color: #475569; font-weight: 700; border: none; padding: 12px; }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #f1f5f9; color: #334155; }
        """)
        table_layout.addWidget(self.table)

        layout.addWidget(self.table_card)

        self.load_courses()

    # Prepares internal course data
    # Called By: __init__
    def load_courses(self):
        self.course_combo.clear()
        for cid, cname in get_all_courses():
            self.course_combo.addItem(cname, cid)

    # Refreshes student list and next ID
    # Called By: HODDashboard (Top Course Selector)
    def load_data(self, course_id: str):
        self.current_course_id = course_id

        idx = self.course_combo.findData(course_id)
        if idx >= 0: self.course_combo.setCurrentIndex(idx)

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

        self.id_input.setText(generate_next_student_id())
        self.subtitle.setText(f"Enrolled Students in {course_id}")

    def show_msg(self, title, text, icon):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(icon)
        msg.setStyleSheet("QMessageBox { background-color: white; color: black; } QLabel { color: black; }")
        msg.exec()

    # Inserts single student
    # Called By: 'Enroll Student' button
    def enroll(self):
        name = self.name_input.text().strip()
        sid = self.id_input.text()
        cid = self.current_course_id

        if not name or not cid:
            self.show_msg("Error", "Please enter a name and ensure a course is selected.", QMessageBox.Warning)
            return

        if insert_new_student(sid, name, cid):
            self.show_msg("Success", "Student Enrolled Successfully.", QMessageBox.Information)
            self.name_input.clear()
            self.load_data(self.current_course_id)

    # Creates blank CSV
    # Called By: 'Template' button
    def download_template(self):
        sample_path = os.path.join(os.path.dirname(__file__), "Enrollment_Templete.csv")

        if not os.path.exists(sample_path):
            self.show_msg("Error", f"Sample file not found: {sample_path}", QMessageBox.Critical)
            return

        try:
            df = pd.read_csv(sample_path)
            cols = df.columns.tolist()
            sample_data = df.astype(str).values.tolist()

            dialog = TemplatePreviewDialog("Enrollment", cols, sample_data, self)

            if dialog.exec():
                path, _ = QFileDialog.getSaveFileName(self, "Save Template", "enrollment_template.csv",
                                                      "CSV Files (*.csv)")
                if path:
                    success, msg = generate_blank_template(path, cols)
                    if success:
                        self.show_msg("Success", f"Template saved to {path}", QMessageBox.Information)
                    else:
                        self.show_msg("Error", msg, QMessageBox.Critical)
        except Exception as e:
            self.show_msg("Error", f"Failed to load sample: {e}", QMessageBox.Critical)

    # Bulk import via CSV
    # Called By: 'Import CSV' button
    def import_csv(self):
        if not self.current_course_id:
            self.show_msg("Error", "Please select a course first.", QMessageBox.Warning)
            return

        path, _ = QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV Files (*.csv)")
        if not path: return

        df, error = parse_csv_data(path, ['Student_ID', 'Student_Name'])
        if error:
            self.show_msg("Error", error, QMessageBox.Critical)
            return

        success_count = 0
        fail_count = 0

        try:
            for index, row in df.iterrows():
                sid = str(row['Student_ID'])
                name = str(row['Student_Name'])

                if not sid or not name or sid == 'nan' or name == 'nan':
                    fail_count += 1
                    continue

                if insert_new_student(sid, name, self.current_course_id):
                    success_count += 1
                else:
                    fail_count += 1

            self.show_msg("Import Complete",
                          f"Successfully enrolled: {success_count}\nFailed (Duplicates/Errors): {fail_count}",
                          QMessageBox.Information)
            self.load_data(self.current_course_id)

        except Exception as e:
            self.show_msg("Critical Error", f"Import failed: {str(e)}", QMessageBox.Critical)