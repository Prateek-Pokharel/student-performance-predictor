from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                               QPushButton, QHeaderView, QLineEdit, QLabel, QGroupBox,
                               QFormLayout, QMessageBox, QHBoxLayout, QFrame, QFileDialog)
from PySide6.QtGui import QIntValidator
from PySide6.QtCore import Qt
from database.queries_teacher import fetch_exam_details_for_subject, save_exam_details_to_db, \
    fetch_student_grades_for_subject, save_grades_to_db

import os
import pandas as pd
from services.import_service import generate_template, parse_csv_data
from ui.template_preview_dialog import TemplatePreviewDialog


class GradePage(QWidget):
    """
    UI for entering/importing student marks.
    Instantiated By: TeacherDashboardUI (create_menu).
    """
    def __init__(self, students, subject_id, conn):
        super().__init__()
        self.students = students
        self.sid = subject_id
        self.conn = conn
        self.inputs = {}

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)

        config_card = QFrame()
        config_card.setStyleSheet("background-color: white; border-radius: 10px; border: 1px solid #e2e8f0;")
        config_lay = QVBoxLayout(config_card)

        lbl_conf = QLabel("Exam Configuration (Full Marks / Pass Marks)")
        lbl_conf.setStyleSheet("font-size: 15px; font-weight: 700; color: #1e293b; margin-bottom: 10px;")
        config_lay.addWidget(lbl_conf)

        grid = QHBoxLayout()
        for exam in ['Unit', 'Mid', 'End']:
            group = QGroupBox(f"{exam} Term")
            group.setStyleSheet(
                "QGroupBox { font-weight: bold; color: #475569; border: 1px solid #cbd5e1; border-radius: 6px; margin-top: 6px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
            g_lay = QFormLayout(group)

            full = QLineEdit("0")
            full.setValidator(QIntValidator(0, 100))
            full.setAlignment(Qt.AlignCenter)
            full.setStyleSheet("border: 1px solid #cbd5e1; border-radius: 4px; padding: 4px;")

            pas = QLineEdit("0")
            pas.setValidator(QIntValidator(0, 100))
            pas.setAlignment(Qt.AlignCenter)
            pas.setStyleSheet("border: 1px solid #cbd5e1; border-radius: 4px; padding: 4px;")

            self.inputs[f"{exam}_Full"] = full
            self.inputs[f"{exam}_Pass"] = pas

            g_lay.addRow("Full:", full)
            g_lay.addRow("Pass:", pas)
            grid.addWidget(group)

        config_lay.addLayout(grid)
        layout.addWidget(config_card)

        table_card = QFrame()
        table_card.setStyleSheet("background-color: white; border-radius: 10px; border: 1px solid #e2e8f0;")
        table_lay = QVBoxLayout(table_card)

        header_row = QHBoxLayout()
        lbl_tbl = QLabel("Student Grades")
        lbl_tbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #1e293b;")
        header_row.addWidget(lbl_tbl)
        header_row.addStretch()

        btn_template = QPushButton("📥 Template")
        btn_template.setCursor(Qt.PointingHandCursor)
        btn_template.setStyleSheet(
            "background-color: #64748b; color: white; border-radius: 6px; padding: 6px 12px; font-weight: bold; border: none;")
        btn_template.clicked.connect(self.download_template)
        header_row.addWidget(btn_template)

        btn_import = QPushButton("📤 Import CSV")
        btn_import.setCursor(Qt.PointingHandCursor)
        btn_import.setStyleSheet(
            "background-color: #0ea5e9; color: white; border-radius: 6px; padding: 6px 12px; font-weight: bold; border: none;")
        btn_import.clicked.connect(self.import_grades)
        header_row.addWidget(btn_import)

        btn_save = QPushButton("💾 Save All Changes")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton { background-color: #3b82f6; color: white; font-weight: bold; padding: 8px 16px; border-radius: 6px; border: none; }
            QPushButton:hover { background-color: #2563eb; }
        """)
        btn_save.clicked.connect(self.save)
        header_row.addWidget(btn_save)

        table_lay.addLayout(header_row)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["No.", "Student Name", "Unit Test", "Mid Term", "End Term"])
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

        self.setup_table()

    # Creates rows and links validation
    # Called By: __init__
    def setup_table(self):
        self.table.setRowCount(len(self.students))

        config_map = {
            2: self.inputs['Unit_Full'],
            3: self.inputs['Mid_Full'],
            4: self.inputs['End_Full']
        }

        for i, s in enumerate(self.students):
            item_no = QTableWidgetItem(str(i + 1))
            item_no.setTextAlignment(Qt.AlignCenter)
            item_no.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 0, item_no)

            name_item = QTableWidgetItem(s['name'])
            name_item.setTextAlignment(Qt.AlignCenter)
            name_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 1, name_item)
            self.table.item(i, 1).setData(Qt.UserRole, s['id'])

            for j, ex in enumerate(['Unit Test', 'Mid Term', 'End Term']):
                col_index = j + 2
                inp = QLineEdit()
                inp.setValidator(QIntValidator(0, 100))
                inp.setProperty("type", ex)
                inp.setAlignment(Qt.AlignCenter)

                inp.setStyleSheet("""
                    QLineEdit { border: 1px solid transparent; background: transparent; font-weight: bold; }
                    QLineEdit:focus { border: 1px solid #3b82f6; background: white; border-radius: 4px; }
                    QLineEdit:hover { background: #f1f5f9; border-radius: 4px; }
                """)

                inp.textChanged.connect(
                    lambda _, le=inp, max_inp=config_map[col_index]: self.validate_grade(le, max_inp))

                self.table.setCellWidget(i, col_index, inp)

    # Validates input against Max Marks (Red Box)
    # Called By: Signal (textChanged)
    def validate_grade(self, line_edit, max_input_widget):
        try:
            val = int(line_edit.text()) if line_edit.text() else 0
            max_val = int(max_input_widget.text()) if max_input_widget.text() else 0
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
                QLineEdit:focus { border: 1px solid #3b82f6; background: white; border-radius: 4px; }
                QLineEdit:hover { background: #f1f5f9; border-radius: 4px; }
            """)

    # Populates table from DB
    # Called By: Dashboard (Tab Switch)
    def load_data(self):
        conf = fetch_exam_details_for_subject(self.conn, self.sid)
        for k, v in self.inputs.items():
            v.setText(str(conf.get(k, '0')))

        grades = fetch_student_grades_for_subject(self.conn, self.sid)
        for i in range(self.table.rowCount()):
            sid = self.table.item(i, 1).data(Qt.UserRole)
            user_grades = grades.get(sid, {})
            self.table.cellWidget(i, 2).setText(str(user_grades.get('Unit Test', '0')))
            self.table.cellWidget(i, 3).setText(str(user_grades.get('Mid Term', '0')))
            self.table.cellWidget(i, 4).setText(str(user_grades.get('End Term', '0')))

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
        sample_path = os.path.join(os.path.dirname(__file__), "Grade_Templete.csv")

        if not os.path.exists(sample_path):
            self.show_msg("Error", f"Sample file not found: {sample_path}", QMessageBox.Critical)
            return

        try:
            df = pd.read_csv(sample_path)
            cols = df.columns.tolist()
            sample_data = df.astype(str).values.tolist()

            dialog = TemplatePreviewDialog("Grades", cols, sample_data, self)

            if dialog.exec():
                path, _ = QFileDialog.getSaveFileName(self, "Save Template", "grades_template.csv", "CSV Files (*.csv)")
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
    def import_grades(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Grades", "", "CSV Files (*.csv)")
        if not path: return

        cols = ['Unit_Test', 'Mid_Term', 'End_Term']
        df, error = parse_csv_data(path, cols)

        if error:
            self.show_msg("Error", error, QMessageBox.Critical)
            return

        try:
            for i in range(self.table.rowCount()):
                s_id = self.table.item(i, 1).data(Qt.UserRole)
                record = df[df['Student_ID'] == int(s_id)]

                if not record.empty:
                    matches = 1

                    def get_val(col_name):
                        try:
                            val = record.iloc[0][col_name]
                            return str(int(float(val)))
                        except:
                            return "0"

                    if 'Unit_Test' in record:
                        self.table.cellWidget(i, 2).setText(get_val('Unit_Test'))
                    if 'Mid_Term' in record:
                        self.table.cellWidget(i, 3).setText(get_val('Mid_Term'))
                    if 'End_Term' in record:
                        self.table.cellWidget(i, 4).setText(get_val('End_Term'))

            if matches == 0:
                self.show_msg("Warning", "Import successful, but NO matching Student IDs were found.",
                              QMessageBox.Warning)
            else:
                self.show_msg("Success", f"Grades loaded! Click 'Save' to finish.",
                              QMessageBox.Information)

        except Exception as e:
            self.show_msg("Error", f"Error processing data: {e}", QMessageBox.Critical)

    # Commits to DB (Blocks if validation error)
    # Called By: Save Button
    def save(self):
        conf_data = {}
        full_marks_map = {}

        for k, v in self.inputs.items():
            val = v.text()
            if not val: val = '0'
            conf_data[k.lower()] = int(val)

            if "_Full" in k:
                term_key = k.split('_')[0]
                full_marks_map[term_key] = int(val)

        col_to_term = {2: 'Unit', 3: 'Mid', 4: 'End'}

        for i in range(self.table.rowCount()):
            for col_idx, term in col_to_term.items():
                widget = self.table.cellWidget(i, col_idx)
                if widget:
                    txt = widget.text()
                    marks = int(txt) if txt else 0
                    max_marks = full_marks_map.get(term, 0)

                    if marks > max_marks:
                        self.show_msg("Validation Error",
                                      "Cannot save!\n\nMarks exceed the Total Marks limit.\nPlease correct the highlighted values.",
                                      QMessageBox.Critical)
                        return

        if not save_exam_details_to_db(self.conn, self.sid, conf_data):
            self.show_msg("Error", "Failed to save config", QMessageBox.Critical)
            return

        grades_data = []
        cols = {2: 'unit_test', 3: 'mid_term', 4: 'end_term'}
        for i in range(self.table.rowCount()):
            row = {'student_id': self.table.item(i, 1).data(Qt.UserRole), 'subject_id': self.sid}
            for col, key in cols.items():
                val = self.table.cellWidget(i, col).text()
                row[key] = val if val else '0'
            grades_data.append(row)

        if save_grades_to_db(self.conn, grades_data):
            self.show_msg("Success", "Grades Saved Successfully", QMessageBox.Information)
        else:
            self.show_msg("Error", "Database Error", QMessageBox.Critical)