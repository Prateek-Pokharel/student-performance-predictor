from PySide6.QtWidgets import (QWidget, QVBoxLayout, QComboBox, QGroupBox, QTableWidget,
                               QTableWidgetItem, QPushButton, QMessageBox, QLabel, QFrame,
                               QScrollArea, QHeaderView, QHBoxLayout, QAbstractItemView, QSizePolicy)
from PySide6.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import math
import pandas as pd

# --- CUSTOM IMPORTS ---
# Ensure these function names match your database/queries_teacher.py file
from database.queries_teacher import (fetch_grades_for_pareto,
                                      fetch_data_for_teacher_groups,
                                      fetch_exam_details_for_subject)
from services.ml_service import perform_clustering


# ===================================================================
# 1. PAGINATED TABLE WIDGET
# ===================================================================
class PaginatedTable(QWidget):
    """
    Custom widget for paging large tables.
    """

    def __init__(self, dataframe, features):
        super().__init__()
        self.df = dataframe
        self.features = features
        self.items_per_page = 5
        self.current_page = 0
        self.total_pages = math.ceil(len(self.df) / self.items_per_page)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.features) + 1)
        self.table.setHorizontalHeaderLabels(["Name"] + self.features)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)

        self.table.setStyleSheet("""
            QTableWidget { border: none; font-size: 13px; }
            QHeaderView::section { background-color: #f8fafc; color: #64748b; font-weight: bold; border: none; padding: 8px; }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid #f1f5f9; color: #334155; }
        """)
        self.table.setFixedHeight(40 + (self.items_per_page * 40))
        self.layout.addWidget(self.table)

        self.controls = QHBoxLayout()

        self.btn_prev = QPushButton("◀ Prev")
        self.btn_prev.setFixedWidth(80)
        self.btn_prev.setCursor(Qt.PointingHandCursor)
        self.btn_prev.clicked.connect(self.prev_page)

        self.lbl_page = QLabel(f"Page 1 of {self.total_pages}")
        self.lbl_page.setAlignment(Qt.AlignCenter)
        self.lbl_page.setStyleSheet("color: #64748b; font-weight: bold;")

        self.btn_next = QPushButton("Next ▶")
        self.btn_next.setFixedWidth(80)
        self.btn_next.setCursor(Qt.PointingHandCursor)
        self.btn_next.clicked.connect(self.next_page)

        btn_style = """
            QPushButton { background-color: white; border: 1px solid #cbd5e1; border-radius: 4px; color: #334155; }
            QPushButton:hover { background-color: #f1f5f9; }
            QPushButton:disabled { color: #cbd5e1; background-color: #f8fafc; }
        """
        self.btn_prev.setStyleSheet(btn_style)
        self.btn_next.setStyleSheet(btn_style)

        self.controls.addStretch()
        self.controls.addWidget(self.btn_prev)
        self.controls.addWidget(self.lbl_page)
        self.controls.addWidget(self.btn_next)
        self.controls.addStretch()

        self.layout.addLayout(self.controls)

        self.update_table()

    def update_table(self):
        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        subset = self.df.iloc[start:end]

        self.table.setRowCount(len(subset))
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        for i, (idx, row) in enumerate(subset.iterrows()):
            name_item = QTableWidgetItem(str(row['Student_Name']))
            name_item.setTextAlignment(Qt.AlignCenter)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 0, name_item)

            for j, feat in enumerate(self.features):
                val = str(round(row[feat], 2))
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(i, j + 1, item)

        self.lbl_page.setText(f"Page {self.current_page + 1} of {self.total_pages}")
        self.btn_prev.setEnabled(self.current_page > 0)
        self.btn_next.setEnabled(self.current_page < self.total_pages - 1)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_table()

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_table()


# ===================================================================
# 2. PARETO CHART PAGE (UPDATED)
# ===================================================================
class ParetoChartPage(QWidget):
    """
    Displays Pareto Analysis with:
    - Percentage-based bars
    - Fixed 0-100% Scale
    - Horizontal Scrolling for many students
    """

    def __init__(self, subject_id, conn):
        super().__init__()
        self.sid = subject_id
        self.conn = conn

        # Main Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # --- Top Controls ---
        ctrl = QFrame()
        ctrl.setStyleSheet("background-color: white; border-radius: 10px; border: 1px solid #e2e8f0;")
        cl = QHBoxLayout(ctrl)

        lbl = QLabel("Select Exam Term:")
        lbl.setStyleSheet("font-weight: bold; color: #1e293b;")

        self.combo = QComboBox()
        self.combo.addItems(["-- Select --", "Unit Test", "Mid Term", "End Term"])
        self.combo.setFixedWidth(200)
        self.combo.setStyleSheet("""
            QComboBox { padding: 5px; border: 1px solid #cbd5e1; border-radius: 4px; background: #f8fafc; }
            QComboBox::drop-down { border: none; }
        """)
        self.combo.currentTextChanged.connect(self.plot)

        cl.addWidget(lbl)
        cl.addWidget(self.combo)
        cl.addStretch()
        layout.addWidget(ctrl)

        # --- Scrollable Chart Container ---
        chart_card = QFrame()
        chart_card.setStyleSheet("background-color: white; border-radius: 10px; border: 1px solid #e2e8f0;")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(5, 5, 5, 15)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: transparent;")

        # Matplotlib Figure
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.fig.patch.set_facecolor('white')
        self.canvas = FigureCanvas(self.fig)

        # Add Canvas to Scroll Area
        self.scroll.setWidget(self.canvas)
        chart_layout.addWidget(self.scroll)

        layout.addWidget(chart_card)

        # Initial State
        self.plot("-- Select --")

    def plot(self, text):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor('white')

        self.canvas.setMinimumWidth(0)

        if text == "-- Select --":
            ax.text(0.5, 0.5, "Select an exam type to view chart.", ha='center', va='center', color='gray', fontsize=12)
            ax.axis('off')
            self.canvas.draw()
            return

        # Fetch Data
        data = fetch_grades_for_pareto(self.conn, self.sid, text)

        if not data:
            ax.text(0.5, 0.5, f"No data found for '{text}'.\nPlease enter grades first.", ha='center', va='center',
                    color='red', fontsize=12)
            ax.axis('off')
            self.canvas.draw()
            return

        # --- Dynamic Width ---
        # 60px per student bar, min 800px total
        num_students = len(data)
        bar_width_pixels = 60
        total_width = max(800, num_students * bar_width_pixels)

        self.canvas.setMinimumWidth(total_width)
        self.fig.set_figwidth(total_width / 100)

        # --- Get Full Marks for Percentage Calculation ---
        full_marks = 100  # Fallback
        config = fetch_exam_details_for_subject(self.conn, self.sid)
        if config:
            if text == "Unit Test":
                full_marks = int(config.get('Unit_Full', 20))
            elif text == "Mid Term":
                full_marks = int(config.get('Mid_Full', 50))
            elif text == "End Term":
                full_marks = int(config.get('End_Full', 100))

        if full_marks == 0: full_marks = 100

        # --- Calculate Percentages ---
        # Data format: [(Student_ID, Student_Name, Raw_Marks), ...]
        processed_data = []
        for row in data:
            name = row[1]
            raw_mark = row[2]
            percentage = (raw_mark / full_marks) * 100
            processed_data.append((name, percentage))

        # Sort by Percentage High to Low
        processed_data.sort(key=lambda x: x[1], reverse=True)

        names = [x[0] for x in processed_data]
        percentages = [x[1] for x in processed_data]
        x_pos = range(len(names))

        # Draw Bars
        bars = ax.bar(x_pos, percentages, color='#3b82f6', width=0.6, zorder=3)

        # Axis Settings
        ax.set_ylim(0, 105)  # Max 100%
        ax.set_xticks(x_pos)
        ax.set_xticklabels(names, rotation=45, ha='right', fontsize=9)
        ax.set_title(f"Performance Distribution (Percentage) - {text}", fontsize=12, fontweight='bold', pad=15)
        ax.set_ylabel("Percentage (%)", fontsize=10, color='#475569')
        ax.grid(axis='y', linestyle='--', alpha=0.5, zorder=0)

        # Add Value Labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height + 1,
                    f"{int(height)}%", ha='center', va='bottom', fontsize=9, color='#334155')

        # Pareto Line (Cumulative %)
        total_pct_sum = sum(percentages)
        if total_pct_sum > 0:
            cumulative = []
            curr = 0
            for p in percentages:
                curr += p
                cumulative.append((curr / total_pct_sum) * 100)

            ax2 = ax.twinx()
            ax2.plot(x_pos, cumulative, color='#ef4444', marker='o', linewidth=2, markersize=4)
            ax2.set_ylim(0, 105)
            ax2.axis('off')

        self.fig.tight_layout()
        # Adjust margins to ensure labels aren't cut off
        self.fig.subplots_adjust(bottom=0.25)
        self.canvas.draw()

    def load_data(self):
        # Refresh current view if needed
        current = self.combo.currentText()
        if current != "-- Select --":
            self.plot(current)


# ===================================================================
# 3. TEACHER GROUP FORMATION PAGE (Updated Widths)
# ===================================================================
class TeacherFormGroupsPage(QWidget):
    """
    AI Group Formation UI.
    """

    def __init__(self, subject_id, conn):
        super().__init__()
        self.sid = subject_id
        self.conn = conn

        self.header_map = {
            'Unit_Test': 'Unit Test %',
            'Mid_Term': 'Mid Term %',
            'End_Term': 'End Term %',
            'Class_Attendance': 'Attendance %',
            'Class_Assignment': 'Assignment %'
        }

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        head = QFrame()
        head.setStyleSheet("background-color: white; border-radius: 10px; border: 1px solid #e2e8f0;")
        hl = QHBoxLayout(head)
        hl.addWidget(QLabel("AI Group Formation"))
        hl.addStretch()
        btn = QPushButton("Generate Groups")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            "background-color: #3b82f6; color: white; padding: 8px 15px; border-radius: 6px; font-weight: bold; border: none;")
        btn.clicked.connect(self.generate)
        hl.addWidget(btn)
        layout.addWidget(head)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: transparent;")

        self.container = QWidget()
        self.tables_layout = QVBoxLayout(self.container)
        self.tables_layout.setSpacing(20)
        self.tables_layout.setContentsMargins(0, 0, 10, 60)
        self.tables_layout.addStretch()

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

    def generate(self):
        data, features = fetch_data_for_teacher_groups(self.conn, self.sid)

        if len(data) < 3:
            QMessageBox.warning(self, "Error", "Not enough data to form groups (Need 3+ students).")
            return

        df = perform_clustering(data, features)
        if df is not None:
            while self.tables_layout.count() > 1:
                child = self.tables_layout.takeAt(0)
                if child.widget(): child.widget().deleteLater()

            for group in ['High Performer', 'Average Performer', 'Low Performer']:
                sub = df[df['Performance_Group'] == group]
                if sub.empty: continue

                self.add_group_table(group, sub, features)

    def add_group_table(self, title, df, features):
        box = QFrame()
        box.setStyleSheet("background-color: white; border-radius: 10px; border: 1px solid #e2e8f0;")
        lay = QVBoxLayout(box)
        lay.setContentsMargins(20, 20, 20, 20)

        color = "#059669" if "High" in title else "#d97706" if "Average" in title else "#dc2626"
        lbl = QLabel(title)
        lbl.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {color}; margin-bottom: 10px;")
        lay.addWidget(lbl)

        tbl = QTableWidget()
        tbl.setColumnCount(len(features) + 2)

        display_headers = [self.header_map.get(f, f) for f in features]
        tbl.setHorizontalHeaderLabels(["No.", "Name"] + display_headers)

        tbl.setRowCount(len(df))

        # --- UPDATED COLUMN WIDTH LOGIC ---
        header = tbl.horizontalHeader()

        # 1. "No." Column: Resize to content (Smallest possible)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)

        # 2. "Name" Column: Resize to content (Prevents it from hogging space)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)

        # 3. Data Columns (Att%, Ass%): Stretch to fill ALL remaining space equally
        for i in range(len(features)):
            header.setSectionResizeMode(i + 2, QHeaderView.Stretch)

        # Disable "Stretch Last Section" since we are manually stretching specific columns
        header.setStretchLastSection(False)

        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(False)
        tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tbl.setSelectionMode(QAbstractItemView.NoSelection)
        tbl.setFocusPolicy(Qt.NoFocus)

        tbl.setStyleSheet("""
            QTableWidget { border: none; font-size: 13px; }
            QHeaderView::section { background-color: #f8fafc; color: #64748b; font-weight: 700; border: none; padding: 8px 5px; }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid #f1f5f9; color: #334155; }
        """)

        for i, (idx, row) in enumerate(df.iterrows()):
            item_no = QTableWidgetItem(str(i + 1))
            item_no.setTextAlignment(Qt.AlignCenter)
            tbl.setItem(i, 0, item_no)

            name_item = QTableWidgetItem(str(row['Student_Name']))
            # Left align name for better readability if it's tight
            name_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            tbl.setItem(i, 1, name_item)

            for j, feat in enumerate(features):
                item = QTableWidgetItem(str(round(row[feat], 2)))
                item.setTextAlignment(Qt.AlignCenter)
                tbl.setItem(i, j + 2, item)

        tbl.setFixedHeight(tbl.horizontalHeader().height() + len(df) * 45)
        lay.addWidget(tbl)

        self.tables_layout.insertWidget(self.tables_layout.count() - 1, box)

    def load_data(self):
        while self.tables_layout.count() > 1:
            child = self.tables_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()