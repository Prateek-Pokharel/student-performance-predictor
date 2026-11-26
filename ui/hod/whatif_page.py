from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                               QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
                               QFrame, QLineEdit, QFormLayout, QGroupBox, QScrollArea, QAbstractItemView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator
from database.queries_hod import fetch_aggregate_data_for_prediction
from services.ml_service import run_prediction


class WhatIfAnalysisPage(QWidget):
    """
    Simulation UI to test "What If" scenarios on student data.
    Instantiated By: HODDashboardUI.
    """

    def __init__(self):
        super().__init__()
        self.data = []
        self.current_student = None
        # Internal Keys
        self.ml_features = ['Unit_Test', 'Mid_Term', 'Pre_Board', 'Class_Attendance', 'Assignment_Submission']

        # Display Labels Map
        self.display_map = {
            'Unit_Test': 'Unit Test %',
            'Mid_Term': 'Mid Term %',
            'Pre_Board': 'Pre Board %',
            'Class_Attendance': 'Attendance %',
            'Assignment_Submission': 'Assignment %'
        }

        self.inputs = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        self.table_card = QFrame()
        self.table_card.setStyleSheet("background-color: white; border-radius: 12px; border: 1px solid #e5e7eb;")
        table_layout = QVBoxLayout(self.table_card)
        table_layout.setContentsMargins(20, 20, 20, 20)

        lbl_list = QLabel("Step 1: Select a Student for Analysis")
        lbl_list.setStyleSheet("font-size: 16px; font-weight: 700; color: #1e293b;")
        table_layout.addWidget(lbl_list)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["No.", "Student ID", "Name", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)

        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { border: none; font-size: 14px; background-color: white; alternate-background-color: #f8fafc; }
            QHeaderView::section { background-color: #f8fafc; color: #64748b; font-weight: 700; border: none; padding: 10px; }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid #f1f5f9; color: #334155; }
        """)
        self.table.setFixedHeight(250)
        table_layout.addWidget(self.table)

        layout.addWidget(self.table_card)

        self.sim_card = QFrame()
        self.sim_card.setVisible(False)
        self.sim_card.setStyleSheet("background-color: white; border-radius: 12px; border: 1px solid #e5e7eb;")
        sim_layout = QVBoxLayout(self.sim_card)
        sim_layout.setContentsMargins(20, 20, 20, 20)
        sim_layout.setSpacing(20)

        self.lbl_sim_title = QLabel("Step 2: What-If Simulation")
        self.lbl_sim_title.setStyleSheet("font-size: 18px; font-weight: 800; color: #3b82f6;")
        sim_layout.addWidget(self.lbl_sim_title)

        form_widget = QWidget()
        form_grid = QHBoxLayout(form_widget)

        for feature in self.ml_features:
            # USE DISPLAY MAP HERE
            display_name = self.display_map.get(feature, feature)
            group = QGroupBox(display_name)
            group.setStyleSheet(
                "font-weight: bold; color: #64748b; border: 1px solid #cbd5e1; border-radius: 8px; margin-top: 5px;")
            g_lay = QVBoxLayout(group)

            inp = QLineEdit()
            inp.setValidator(QDoubleValidator(0.0, 100.0, 2))
            inp.setAlignment(Qt.AlignCenter)
            inp.setStyleSheet(
                "border: none; font-size: 16px; font-weight: bold; color: #1e293b; background: transparent;")

            self.inputs[feature] = inp
            g_lay.addWidget(inp)
            form_grid.addWidget(group)

        sim_layout.addWidget(form_widget)

        result_row = QHBoxLayout()

        self.btn_predict = QPushButton("🔮 Simulate Outcome")
        self.btn_predict.setCursor(Qt.PointingHandCursor)
        self.btn_predict.setFixedSize(200, 45)
        self.btn_predict.setStyleSheet("""
            QPushButton {
                background-color: #8b5cf6; color: white; font-weight: 700; font-size: 14px;
                border-radius: 8px; border: none;
            }
            QPushButton:hover { background-color: #7c3aed; }
        """)
        self.btn_predict.clicked.connect(self.run_simulation)

        self.lbl_result = QLabel("Ready to simulate")
        self.lbl_result.setAlignment(Qt.AlignCenter)
        self.lbl_result.setStyleSheet(
            "font-size: 16px; font-weight: 700; color: #94a3b8; padding: 10px; border: 2px dashed #cbd5e1; border-radius: 8px;")

        result_row.addWidget(self.btn_predict)
        result_row.addSpacing(20)
        result_row.addWidget(self.lbl_result, 1)

        sim_layout.addLayout(result_row)
        layout.addWidget(self.sim_card)
        layout.addStretch()

    # Loads students
    # Called By: HODDashboard (Top Selector)
    def load_data(self, course_id: str):
        self.data = fetch_aggregate_data_for_prediction(course_id)
        self.sim_card.setVisible(False)
        self.table.setRowCount(len(self.data))

        for i, row in enumerate(self.data):
            item_no = QTableWidgetItem(str(i + 1))
            item_no.setTextAlignment(Qt.AlignCenter)
            item_no.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 0, item_no)

            item_id = QTableWidgetItem(str(row['Student_ID']))
            item_id.setTextAlignment(Qt.AlignCenter)
            item_id.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 1, item_id)

            item_name = QTableWidgetItem(str(row['Student_Name']))
            item_name.setTextAlignment(Qt.AlignCenter)
            item_name.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 2, item_name)

            btn = QPushButton("Select")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton { background-color: #e0f2fe; color: #0284c7; border: none; border-radius: 4px; font-weight: bold; }
                QPushButton:hover { background-color: #bae6fd; }
            """)
            btn.clicked.connect(lambda checked, r=row: self.select_student(r))

            container = QWidget()
            lay = QVBoxLayout(container)
            lay.setContentsMargins(5, 2, 5, 2)
            lay.addWidget(btn)
            self.table.setCellWidget(i, 3, container)

    # Pre-fills inputs with real data
    # Called By: 'Select' button
    def select_student(self, student_row):
        self.current_student = student_row
        self.sim_card.setVisible(True)
        self.lbl_sim_title.setText(f"What-If Analysis: {student_row['Student_Name']}")

        self.lbl_result.setText("Adjust values above and click Simulate")
        self.lbl_result.setStyleSheet(
            "font-size: 16px; font-weight: 700; color: #94a3b8; padding: 10px; border: 2px dashed #cbd5e1; border-radius: 8px;")

        for feat in self.ml_features:
            val = student_row.get(feat, 0)
            self.inputs[feat].setText(str(round(val, 2)))

    # Predicts based on MODIFIED inputs
    # Called By: 'Simulate' button
    def run_simulation(self):
        if not self.current_student: return

        simulated_data = self.current_student.copy()

        try:
            for feat in self.ml_features:
                text_val = self.inputs[feat].text()
                val = float(text_val) if text_val else 0.0
                simulated_data[feat] = val
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid numbers for all fields.")
            return

        dataset = [simulated_data]

        results = run_prediction(dataset, self.ml_features)

        sid = simulated_data['Student_ID']
        res = results.get(sid, "Unknown")

        if res == "Pass":
            self.lbl_result.setText(f"✅ Predicted Result: PASS")
            self.lbl_result.setStyleSheet(
                "font-size: 18px; font-weight: 800; color: #059669; background-color: #d1fae5; border: 2px solid #059669; border-radius: 8px; padding: 10px;")
        else:
            self.lbl_result.setText(f"❌ Predicted Result: FAIL")
            self.lbl_result.setStyleSheet(
                "font-size: 18px; font-weight: 800; color: #dc2626; background-color: #fee2e2; border: 2px solid #dc2626; border-radius: 8px; padding: 10px;")