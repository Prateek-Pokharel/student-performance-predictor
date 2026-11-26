from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                               QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
                               QFrame, QAbstractItemView, QScrollArea)
from PySide6.QtCore import Qt, QTimer
from database.queries_hod import fetch_aggregate_data_for_prediction
from services.ml_service import run_prediction, perform_clustering
import pandas as pd


class PredictStudentPerformancePage(QWidget):
    """
    Pass/Fail Prediction UI.
    Instantiated By: HODDashboardUI.
    """

    def __init__(self):
        super().__init__()
        self.data = []
        # Internal keys match database/ML keys
        self.ml_features = ['Unit_Test', 'Mid_Term', 'Pre_Board', 'Class_Attendance', 'Assignment_Submission']

        # Display Headers (Human Readable with %)
        self.display_headers = ["Unit Test %", "Mid Term %", "Pre Board %", "Attendance %", "Assignment %"]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        control_card = QFrame()
        control_card.setStyleSheet("background-color: white; border-radius: 12px; border: 1px solid #e5e7eb;")
        control_layout = QHBoxLayout(control_card)
        control_layout.setContentsMargins(20, 15, 20, 15)

        lbl_desc = QLabel("Performance Prediction")
        lbl_desc.setStyleSheet("font-size: 16px; font-weight: 700; color: #1e293b; border: none;")

        self.predict_btn = QPushButton("🚀 Run Prediction Model")
        self.predict_btn.setCursor(Qt.PointingHandCursor)
        self.predict_btn.setStyleSheet(
            "background-color: #8b5cf6; color: white; font-weight: bold; padding: 10px 20px; border-radius: 8px;")
        self.predict_btn.clicked.connect(self.run_predict)

        self.export_btn = QPushButton("💾 Export CSV")
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setStyleSheet(
            "background-color: #10b981; color: white; font-weight: bold; padding: 10px 20px; border-radius: 8px;")
        self.export_btn.clicked.connect(self.export)

        control_layout.addWidget(lbl_desc)
        control_layout.addStretch()
        control_layout.addWidget(self.predict_btn)
        control_layout.addWidget(self.export_btn)
        layout.addWidget(control_card)

        # SCROLL AREA FOR TABLE
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background: transparent;")

        self.table_container = QWidget()
        self.table_layout = QVBoxLayout(self.table_container)
        self.table_layout.setContentsMargins(0, 0, 0, 0)

        table_card = QFrame()
        table_card.setStyleSheet("background-color: white; border-radius: 12px; border: 1px solid #e5e7eb;")
        card_layout = QVBoxLayout(table_card)
        card_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        # UPDATED HEADERS HERE
        self.table.setHorizontalHeaderLabels(["No.", "Student Name"] + self.display_headers + ["Predicted Result"])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        for i in [0, 2, 3, 4, 5, 6, 7]:
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { border: none; font-size: 14px; background-color: white; alternate-background-color: #f8fafc; }
            QHeaderView::section { background-color: #f1f5f9; color: #475569; font-weight: 700; border: none; padding: 12px; }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #f1f5f9; color: #334155; }
            QTableWidget::item:hover { background-color: transparent; } 
        """)

        card_layout.addWidget(self.table)
        self.table_layout.addWidget(table_card)

        self.scroll_area.setWidget(self.table_container)
        layout.addWidget(self.scroll_area)

    def adjust_table_height(self):
        # Calculate height based on rows
        if self.table.rowCount() == 0: return
        header_height = self.table.horizontalHeader().height()
        rows_height = sum([self.table.rowHeight(i) for i in range(self.table.rowCount())])
        total_height = header_height + rows_height + 20  # +20 buffer

        # Enforce minimum height so it doesn't collapse
        self.table.setMinimumHeight(max(300, total_height))
        self.table.repaint()

    def delayed_adjust_height(self):
        QTimer.singleShot(10, self.adjust_table_height)

    # Loads aggregated data
    # Called By: HODDashboard (Top Selector)
    def load_data(self, course_id: str):
        self.data = fetch_aggregate_data_for_prediction(course_id)
        self.table.setRowCount(len(self.data))
        for i, row in enumerate(self.data):
            flags = Qt.ItemIsEnabled

            item_no = QTableWidgetItem(str(i + 1))
            item_no.setTextAlignment(Qt.AlignCenter)
            item_no.setFlags(flags)
            self.table.setItem(i, 0, item_no)

            name_item = QTableWidgetItem(str(row['Student_Name']))
            name_item.setTextAlignment(Qt.AlignCenter)
            name_item.setFlags(flags)
            self.table.setItem(i, 1, name_item)

            for j, feat in enumerate(self.ml_features):
                item = QTableWidgetItem(str(round(row[feat], 2)))
                item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(flags)
                self.table.setItem(i, j + 2, item)

            dash = QTableWidgetItem("-")
            dash.setTextAlignment(Qt.AlignCenter)
            dash.setFlags(flags)
            self.table.setItem(i, 7, dash)

        self.table.resizeColumnsToContents()
        self.delayed_adjust_height()

    # Runs Model -> Updates Table Column 7
    # Called By: 'Run Prediction' button
    def run_predict(self):
        if not self.data: return
        results = run_prediction(self.data, self.ml_features)

        for i in range(self.table.rowCount()):
            sid = self.data[i]['Student_ID']
            res = results.get(sid, "N/A")
            item = QTableWidgetItem(res)
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(Qt.ItemIsEnabled)

            if res == "Fail":
                item.setBackground(Qt.darkRed);
                item.setForeground(Qt.white)
            elif res == "Pass":
                item.setBackground(Qt.darkGreen);
                item.setForeground(Qt.white)
            else:
                item.setForeground(Qt.black)

            self.table.setItem(i, 7, item)

        self.table.resizeColumnsToContents()
        self.delayed_adjust_height()

    def export(self):
        if not self.data: return
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "prediction.csv", "CSV Files (*.csv)")
        if path:
            headers = ["No.", "Student Name"] + self.display_headers + ["Result"]
            rows = [[self.table.item(i, c).text() for c in range(8)] for i in range(self.table.rowCount())]
            pd.DataFrame(rows, columns=headers).to_csv(path, index=False)
            QMessageBox.information(self, "Success", "Exported.")


class FormGroupsPage(QWidget):
    """
    HOD Group Formation (Clustering).
    Instantiated By: HODDashboardUI.
    """

    def __init__(self):
        super().__init__()
        self.data = []
        self.ml_features = ['Unit_Test', 'Mid_Term', 'Pre_Board', 'Class_Attendance', 'Assignment_Submission']

        # Display Headers
        self.display_headers = ["Unit Test %", "Mid Term %", "Pre Board %", "Attendance %", "Assignment %"]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        control_card = QFrame()
        control_card.setFixedHeight(80)
        control_card.setStyleSheet("background-color: white; border-radius: 12px; border: 1px solid #e5e7eb;")
        ctrl_layout = QHBoxLayout(control_card)
        ctrl_layout.setContentsMargins(20, 15, 20, 15)

        lbl_title = QLabel("Automated Group Formation")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #1e293b; border: none;")

        btn_gen = QPushButton("Generate Groups")
        btn_gen.setCursor(Qt.PointingHandCursor)
        btn_gen.setStyleSheet(
            "background-color: #3b82f6; color: white; font-weight: bold; padding: 10px 20px; border-radius: 8px;")
        btn_gen.clicked.connect(self.generate)

        ctrl_layout.addWidget(lbl_title)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(btn_gen)
        layout.addWidget(control_card)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background: transparent;")

        self.tables_container = QWidget()
        self.tables_container.setStyleSheet("background-color: transparent;")
        self.tables_layout = QVBoxLayout(self.tables_container)
        self.tables_layout.setSpacing(20)
        self.tables_layout.setContentsMargins(0, 0, 10, 20)
        self.tables_layout.addStretch()

        self.scroll_area.setWidget(self.tables_container)
        layout.addWidget(self.scroll_area)

    def load_data(self, course_id: str):
        self.data = fetch_aggregate_data_for_prediction(course_id)
        while self.tables_layout.count() > 1:
            item = self.tables_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    # Runs Clustering
    # Called By: Generate Button
    def generate(self):
        if len(self.data) < 3:
            QMessageBox.warning(self, "Error", "Need at least 3 students.")
            return

        df = perform_clustering(self.data, self.ml_features)
        if df is not None:
            while self.tables_layout.count() > 1:
                item = self.tables_layout.takeAt(0)
                if item.widget(): item.widget().deleteLater()

            for group in ['High Performer', 'Average Performer', 'Low Performer']:
                sub_df = df[df['Performance_Group'] == group]
                if not sub_df.empty: self.add_group_table(group, sub_df)

    def add_group_table(self, title, df):
        box = QFrame()
        box.setStyleSheet("background-color: white; border-radius: 12px; border: 1px solid #e5e7eb;")
        lay = QVBoxLayout(box)
        lay.setContentsMargins(20, 20, 20, 20)

        color = "#059669" if "High" in title else "#dc2626" if "Low" in title else "#d97706"
        lbl = QLabel(title)
        lbl.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {color}; border: none; margin-bottom: 10px;")
        lay.addWidget(lbl)

        tbl = QTableWidget()
        tbl.setColumnCount(len(self.ml_features) + 2)
        # UPDATED HEADERS HERE
        tbl.setHorizontalHeaderLabels(["No.", "Name"] + self.display_headers)
        tbl.setRowCount(len(df))

        header = tbl.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for i in range(2, tbl.columnCount()): header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        tbl.setAlternatingRowColors(True)
        tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tbl.setFocusPolicy(Qt.NoFocus)
        tbl.setSelectionMode(QAbstractItemView.NoSelection)

        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(False)
        tbl.setStyleSheet("""
            QTableWidget { border: none; font-size: 13px; background-color: white; alternate-background-color: #f8fafc; }
            QHeaderView::section { background-color: #f8fafc; font-weight: bold; padding: 8px; }
            QTableWidget::item:hover { background-color: transparent; }
        """)

        for i, (idx, row) in enumerate(df.iterrows()):
            flags = Qt.ItemIsEnabled

            item_no = QTableWidgetItem(str(i + 1))
            item_no.setTextAlignment(Qt.AlignCenter)
            item_no.setFlags(flags)
            tbl.setItem(i, 0, item_no)

            name_item = QTableWidgetItem(str(row['Student_Name']))
            name_item.setTextAlignment(Qt.AlignCenter)
            name_item.setFlags(flags)
            tbl.setItem(i, 1, name_item)

            for j, feat in enumerate(self.ml_features):
                item = QTableWidgetItem(str(round(row[feat], 2)))
                item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(flags)
                tbl.setItem(i, j + 2, item)

        tbl.setFixedHeight(40 + len(df) * 40)
        lay.addWidget(tbl)
        self.tables_layout.insertWidget(self.tables_layout.count() - 1, box)