from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                               QPushButton, QHeaderView, QLineEdit, QLabel, QHBoxLayout,
                               QMessageBox, QFrame, QFileDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIntValidator
from database.queries_teacher import fetch_subject_config, save_subject_config, fetch_student_records, \
    save_assignment_data

import os
import pandas as pd
from services.import_service import generate_template, parse_csv_data
from ui.template_preview_dialog import TemplatePreviewDialog


class BaseAssignmentPage(QWidget):
    """
    Base Logic for Assignments (Class/Lab).
    Instantiated By: Subclasses (ClassAssignmentPage, LabAssignmentPage).
    """
    def __init__(self, students, subject_id, conn, sub_type):
        super().__init__()
        self.students = students
        self.sid = subject_id
        self.conn = conn
        self.type = sub_type

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)

        config_card = QFrame()
        config_card.setStyleSheet("background-color: white; border-radius: 10px; border: 1px solid #e2e8f0;")
        config_lay = QHBoxLayout(config_card)
        config_lay.setContentsMargins(20, 20, 20, 20)

        lbl_title = QLabel(f"Total {sub_type} Assignments:")
        lbl_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #1e293b;")

        self.max_input = QLineEdit()
        self.max_input.setFixedWidth(100)
        self.max_input.setAlignment(Qt.AlignCenter)
        self.max_input.setValidator(QIntValidator(0, 100))
        self.max_input.setStyleSheet("""
            QLineEdit { border: 2px solid #cbd5e1; border-radius: 6px; padding: 5px; font-weight: bold; font-size: 14px; }
            QLineEdit:focus { border: 2px solid #8b5cf6; }
        """)

        config_lay.addWidget(lbl_title)
        config_lay.addWidget(self.max_input)
        config_lay.addStretch()
        layout.addWidget(config_card)

        table_card = QFrame()
        table_card.setStyleSheet("background-color: white; border-radius: 10px; border: 1px solid #e2e8f0;")
        table_lay = QVBoxLayout(table_card)

        h_lay = QHBoxLayout()
        h_lay.addWidget(
            QLabel("Assignment Submissions", styleSheet="font-size: 15px; font-weight: 700; color: #1e293b;"))
        h_lay.addStretch()

        btn_template = QPushButton("📥 Template")
        btn_template.setCursor(Qt.PointingHandCursor)
        btn_template.setStyleSheet(
            "background-color: #64748b; color: white; border-radius: 6px; padding: 6px 12px; font-weight: bold; border: none;")
        btn_template.clicked.connect(self.download_template)
        h_lay.addWidget(btn_template)

        btn_import = QPushButton("📤 Import CSV")
        btn_import.setCursor(Qt.PointingHandCursor)
        btn_import.setStyleSheet(
            "background-color: #0ea5e9; color: white; border-radius: 6px; padding: 6px 12px; font-weight: bold; border: none;")
        btn_import.clicked.connect(self.import_assignments)
        h_lay.addWidget(btn_import)

        btn_save = QPushButton("💾 Save Assignments")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton { background-color: #8b5cf6; color: white; font-weight: bold; padding: 8px 16px; border-radius: 6px; border: none; }
            QPushButton:hover { background-color: #7c3aed; }
        """)
        btn_save.clicked.connect(self.save)
        h_lay.addWidget(btn_save)
        table_lay.addLayout(h_lay)

        self.table = QTableWidget(len(students), 3)
        self.table.setHorizontalHeaderLabels(["No.", "Student Name", "No. Submitted"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)

        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)

        self.table.setStyleSheet("""
            QTableWidget { border: none; gridline-color: #f1f5f9; font-size: 14px; }
            QHeaderView::section { background-color: #f8fafc; color: #64748b; font-weight: bold; border: none; padding: 10px; }
            QTableWidget::item { padding: 5px; color: #334155; border-bottom: 1px solid #f1f5f9; }
        """)
        table_lay.addWidget(self.table)
        layout.addWidget(table_card)

        for i, s in enumerate(students):
            item_no = QTableWidgetItem(str(i + 1))
            item_no.setTextAlignment(Qt.AlignCenter)
            item_no.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 0, item_no)

            name_item = QTableWidgetItem(s['name'])
            name_item.setTextAlignment(Qt.AlignCenter)
            name_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 1, name_item)
            self.table.item(i, 1).setData(Qt.UserRole, s['id'])

            inp = QLineEdit()
            inp.setValidator(QIntValidator(0, 100))
            inp.setAlignment(Qt.AlignCenter)
            inp.setStyleSheet("""
                QLineEdit { border: 1px solid transparent; background: transparent; font-weight: bold; }
                QLineEdit:focus { border: 1px solid #8b5cf6; background: white; border-radius: 4px; }
                QLineEdit:hover { background: #f1f5f9; border-radius: 4px; }
            """)

            inp.textChanged.connect(lambda _, le=inp: self.validate_assignment(le))

            self.table.setCellWidget(i, 2, inp)

    # Validates input against Total Assignments (Red Box)
    # Called By: Signal (textChanged)
    def validate_assignment(self, line_edit):
        try:
            val = int(line_edit.text()) if line_edit.text() else 0
            max_val = int(self.max_input.text()) if self.max_input.text() else 0
        except ValueError:
            val = 0
            max_val = 0

        if val > max_val:
            line_edit.setStyleSheet("""
                QLineEdit { 
                    border: 2px solid #ef4444; 
                    background-color: #fecaca; 
                    color: #b91c1c; 
                    font-weight: bold; 
                    border-radius: 4px;
                }
            """)
        else:
            line_edit.setStyleSheet("""
                QLineEdit { border: 1px solid transparent; background: transparent; font-weight: bold; color: black; }
                QLineEdit:focus { border: 1px solid #8b5cf6; background: white; border-radius: 4px; }
                QLineEdit:hover { background: #f1f5f9; border-radius: 4px; }
            """)

    def show_msg(self, title, text, icon):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(icon)
        msg.setStyleSheet("QMessageBox { background-color: white; color: black; } QLabel { color: black; }")
        msg.exec()

    # Generates filled CSV
    # Called By: Template Button
    def download_template(self):
        sample_path = os.path.join(os.path.dirname(__file__), "Assignment_Templete.csv")

        if not os.path.exists(sample_path):
            self.show_msg("Error", f"Sample file not found: {sample_path}", QMessageBox.Critical)
            return

        try:
            df = pd.read_csv(sample_path)
            cols = df.columns.tolist()
            sample_data = df.astype(str).values.tolist()

            dialog = TemplatePreviewDialog("Assignments", cols, sample_data, self)

            if dialog.exec():
                path, _ = QFileDialog.getSaveFileName(self, "Save Template", "Assignment_Templete.csv",
                                                      "CSV Files (*.csv)")
                if path:
                    data_cols = [c for c in cols if c not in ['Student_ID', 'Student_Name']]
                    success, msg = generate_template(path, self.students, data_cols)
                    if success:
                        self.show_msg("Success", f"Template saved to {path}", QMessageBox.Information)
                    else:
                        self.show_msg("Error", msg, QMessageBox.Critical)

        except Exception as e:
            self.show_msg("Error", f"Failed to load sample: {e}", QMessageBox.Critical)

    # Reads CSV and fills UI
    # Called By: Import Button
    def import_assignments(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV Files (*.csv)")
        if not path: return

        cols = ['No_Submitted']
        df, error = parse_csv_data(path, cols)

        if error:
            self.show_msg("Error", error, QMessageBox.Critical)
            return

        try:
            for i in range(self.table.rowCount()):
                s_id = self.table.item(i, 1).data(Qt.UserRole)
                record = df[df['Student_ID'] == int(s_id)]

                if not record.empty and 'No_Submitted' in record:
                    self.table.cellWidget(i, 2).setText(str(record.iloc[0]['No_Submitted']))

            self.show_msg("Success", "Assignments loaded! Click 'Save' to finish.", QMessageBox.Information)
        except Exception as e:
            self.show_msg("Error", f"Error processing data: {e}", QMessageBox.Critical)

    # Loads data from DB
    # Called By: Dashboard (Tab Switch)
    def load_data(self):
        col = "Class_Assignment_Assigned" if self.type == "Class" else "Lab_Assignment_Assigned"
        self.max_input.setText(str(fetch_subject_config(self.conn, self.sid, "Subject", col) or 0))

        recs = fetch_student_records(self.conn, self.sid, "Assignment", "Submission_Type", self.type,
                                     "Number_Of_Assignment")
        for i in range(self.table.rowCount()):
            sid = self.table.item(i, 1).data(Qt.UserRole)
            self.table.cellWidget(i, 2).setText(str(recs.get(sid, '0')))

    # Commits to DB (Blocks if validation error)
    # Called By: Save Button
    def save(self):
        try:
            max_assign = int(self.max_input.text()) if self.max_input.text() else 0
        except ValueError:
            max_assign = 0

        for i in range(self.table.rowCount()):
            widget = self.table.cellWidget(i, 2)
            if widget:
                txt = widget.text()
                val = int(txt) if txt else 0

                if val > max_assign:
                    self.show_msg("Validation Error",
                                  "Cannot save!\n\nAssignments Submitted exceed the Total Assignments limit.\nPlease correct the highlighted values.",
                                  QMessageBox.Critical)
                    return

        col = "Class_Assignment_Assigned" if self.type == "Class" else "Lab_Assignment_Assigned"
        if not save_subject_config(self.conn, self.sid, "Subject", col, self.max_input.text()): return

        data = []
        for i in range(self.table.rowCount()):
            val = self.table.cellWidget(i, 2).text()
            data.append({
                'student_id': self.table.item(i, 1).data(Qt.UserRole),
                'number_of_assignment': val if val else '0'
            })

        if save_assignment_data(self.conn, data, self.type, self.sid):
            self.show_msg("Success", "Saved Successfully.", QMessageBox.Information)
        else:
            self.show_msg("Error", "Failed to save.", QMessageBox.Critical)


class ClassAssignmentPage(BaseAssignmentPage):
    def __init__(self, s, sid, c): super().__init__(s, sid, c, "Class")


class LabAssignmentPage(BaseAssignmentPage):
    def __init__(self, s, sid, c): super().__init__(s, sid, c, "Lab")